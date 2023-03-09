import pprint

import requests
import time
from threading import Lock
from urllib.parse import urlencode

import source.creds as creds
import source.utils.Utils as Utils

from source.BitrixFieldsAliases import *
from source.BitrixFieldMappings import *
from source.config import *
from typing import List, Dict
from source.DealData import DealData

logger = logging.getLogger(__name__)

SESSION = requests.session()
REQUESTS_TIMEOUT = 10  # seconds
REQUESTS_MAX_ATTEMPTS = 3

# global bitrix worker error code
BW_OK = 0
BW_NO_SUCH_DEAL = -1
BW_WRONG_STAGE = -2
BW_INTERNAL_ERROR = -3

# bitrix dicts
PAYMENT_TYPES = {}
PAYMENT_TYPES_LOCK = Lock()
PAYMENT_METHODS = {}
PAYMENT_METHODS_LOCK = Lock()
FLORISTS = {}
FLORISTS_LOCK = Lock()
COURIERS = {}
COURIERS_LOCK = Lock()
ORDERS_TYPES = {}
ORDERS_TYPES_LOCK = Lock()
DEAL_TIMES = {}
DEAL_TIMES_LOCK = Lock()
SUBDIVISIONS = {}
SUBDIVISIONS_LOCK = Lock()
DISTRICTS = {}
DISTRICTS_LOCK = Lock()
SOURCES = {}
SOURCES_LOCK = Lock()
STAGES = {}
STAGES_LOCK = Lock()
BITRIX_USERS = {}  # phone -> id mapping
# TODO: users mappings refactoring
BITRIX_IDS_USERS = {}  # id -> name + last name, auxiliary mapping
BITRIX_USERS_LOCK = Lock()
FESTIVE_DATES = []
FESTIVE_DATES_LOCK = Lock()

# Bitrix OAuth keys
# store in Telegram bot persistence to serialize automatically
OAUTH_LOCK = Lock()

SLEEP_INTERVAL = 0.5
QUERY_LIMIT_EXCEEDED = 'QUERY_LIMIT_EXCEEDED'


# if getter_method is True -> then result absence mead there is no such entity
def send_request(method, params=None, handle_next=False, getter_method=False, obtain_total=False):
    if params is None:
        params = {}

    for a in range(REQUESTS_MAX_ATTEMPTS):
        try:
            response = SESSION.post(url=creds.BITRIX_API_URL + method,
                                    json=params, timeout=REQUESTS_TIMEOUT)

            # code 400 in response to getter method means object not found
            if getter_method and response.status_code == 400:
                return None

            if response and response.ok:
                json = response.json()
                error = json.get('error')

                # TODO: handle QUERY_LIMIT_EXCEEDED properly
                if error == QUERY_LIMIT_EXCEEDED:
                    time.sleep(SLEEP_INTERVAL)
                    continue

                if obtain_total:
                    return json.get('total')

                next_counter = json.get('next')
                result = json.get('result')

                # handling List[]
                if result is not None and handle_next and next_counter:
                    time.sleep(SLEEP_INTERVAL)
                    params['start'] = next_counter
                    result.extend(send_request(method, params, True))
                    return result

                if result is not None:
                    return result
                else:
                    error = 'Bitrix bad response: %s\n Attempt: %s\n Request params: %s\n Error:%s' \
                            % (json, a, params, json.get('error_description'))
                    logger.error(error)
            else:
                error = 'Bitrix request failed - %s : Attempt: %s : Request params: %s' \
                        % (response.text, a, params)
                logger.error(error)

        except Exception as e:
            error = 'Sending Bitrix api request error %s' % e
            logger.error(error)

    raise Exception(f'B24 request failed: {method} using {params}')


# TODO: finish batch queries implementation!
# queries: {1: {'method': 'crm.deals.get', params:{...}}, 2: ... }
def send_batch(queries, halt=False):
    params = {}
    for k, v in queries.items():
        method = v['method']
        params[k] = method + '?' + urlencode(params)

    params = {
        'halt': 1 if halt else 0,
        'cmd': params
    }

    return send_request('batch', params)


def get_deal(deal_id):
    result = send_request('crm.deal.get', {'id': deal_id}, getter_method=True)
    return result


def update_deal(deal_id, fields):
    send_request('crm.deal.update', {'id': deal_id,
                                     'fields': fields})


# load B24 userfield
def _load_userfield_dict(field_id):
    result = {}

    try:
        userfield = send_request('crm.deal.userfield.get', {'id': field_id})
        userfield_list = userfield['LIST']
        result = {el['ID']: el['VALUE'] for el in userfield_list}
    except Exception as e:
        logger.error("Exception getting userfield dict: %s", e)

    return result


# load B24 standard references
def _load_reference(ref_id):
    result = {}

    try:
        reference_list = send_request('crm.status.list',
                                      {
                                          'order': {'SORT': 'ASC'},
                                          'filter': {'ENTITY_ID': ref_id}
                                      },
                                      handle_next=True)
        result = {el['STATUS_ID']: el['NAME'] for el in reference_list}
    except Exception as e:
        logger.error("Exception getting reference dict: %s", e)

    return result


def _load_payment_types():
    global PAYMENT_TYPES
    result = _load_userfield_dict(PAYMENT_TYPE_FIELD_ID)

    if result:
        with PAYMENT_TYPES_LOCK:
            PAYMENT_TYPES = result


def _load_payment_methods():
    global PAYMENT_METHODS
    result = _load_userfield_dict(PAYMENT_METHOD_FIELD_ID)

    if result:
        with PAYMENT_METHODS_LOCK:
            PAYMENT_METHODS = result


def _load_orders_types():
    global ORDERS_TYPES
    result = _load_userfield_dict(ORDER_TYPE_FIELD_ID)

    if result:
        with ORDERS_TYPES_LOCK:
            ORDERS_TYPES = result


def _load_deal_times():
    global DEAL_TIMES
    result = _load_userfield_dict(DEAL_TIME_FIELD_ID)

    if result:
        with DEAL_TIMES_LOCK:
            DEAL_TIMES = result


def _load_couriers():
    result = {}
    params = {
        'sort': 'LAST_NAME',
        'order': 'ASC',
        'FILTER': {USER_POSITION_ALIAS: COURIER_POSITION_ID, 'ACTIVE': 'True'}
    }

    try:
        couriers = send_request('user.get', params, handle_next=True)

        result = {c['ID']: Utils.prepare_external_field(c, 'LAST_NAME') + ' ' + Utils.prepare_external_field(c, 'NAME')
                  for c in couriers}

    except Exception as e:
        logging.error("Exception getting florists, %s", e)

    global COURIERS
    if result:
        with COURIERS_LOCK:
            COURIERS = result


def _load_florists():
    result = {}
    params = {
        'sort': 'LAST_NAME',
        'order': 'ASC',
        'FILTER': {USER_POSITION_ALIAS: FLORIST_POSITION_ID, 'ACTIVE': 'True'}
    }

    try:
        florists = send_request('user.get', params, handle_next=True)

        result = {f['ID']: Utils.prepare_external_field(f, 'LAST_NAME') + ' ' + Utils.prepare_external_field(f, 'NAME')
                  for f in florists}

    except Exception as e:
        logging.error("Exception getting florists, %s", e)

    global FLORISTS
    if result:
        with FLORISTS_LOCK:
            FLORISTS = result


def load_active_users():
    result = {}
    params = {'filter': {'ACTIVE': 'True'}}

    try:
        # can't select particular fields due to Bitrix API restrictions
        # load all fields for now
        # TODO: possible performance tests needed
        result = send_request('user.get', params, handle_next=True)

        users_dict = {}
        users_ids_dict = {}

        for u in result:
            try:
                users_dict[Utils.prepare_phone_number(u[USER_MAIN_PHONE_ALIAS])] = u[USER_ID_ALIAS]
                users_ids_dict[u[USER_ID_ALIAS]] = (Utils.prepare_external_field(u, 'LAST_NAME') if u.get(
                    'LAST_NAME') else '') + ' ' + \
                                      Utils.prepare_external_field(u, 'NAME') if u.get('NAME') else ''
            except Exception as err:
                logger.error(f"Ошибка при получении данных пользователей: \nData: {u}\nERR: {err}")
                continue

        global BITRIX_USERS
        global BITRIX_IDS_USERS
        if result:
            with BITRIX_USERS_LOCK:
                BITRIX_USERS = users_dict
                BITRIX_IDS_USERS = users_ids_dict

    except Exception as e:
        logging.error("Exception getting bitrix users, %s", e, exc_info=True)


def update_user_from_phonenumber(number):
    """
    :param number: +79964316090
    """
    params = {'filter': {'ACTIVE': 'True', USER_MAIN_PHONE_ALIAS: number}}
    result: List[dict] = send_request('user.get', params)

    if result:
        user = result[0]
        global BITRIX_USERS
        global BITRIX_IDS_USERS
        with BITRIX_USERS_LOCK:
            BITRIX_USERS[Utils.prepare_phone_number(user[USER_MAIN_PHONE_ALIAS])] = user[USER_ID_ALIAS]
            BITRIX_IDS_USERS[user[USER_ID_ALIAS]] = Utils.prepare_external_field(user, 'LAST_NAME') if user.get(
                'LAST_NAME') else '' + ' ' + \
                                  Utils.prepare_external_field(user, 'NAME') if user.get('NAME') else ''


def _load_subdivisions():
    global SUBDIVISIONS
    result = _load_userfield_dict(DEAL_SUBDIVISION_FIELD_ID)

    if result:
        with SUBDIVISIONS_LOCK:
            SUBDIVISIONS = result


def _load_districts():
    global DISTRICTS
    result = _load_userfield_dict(DEAL_DISTRICT_FIELD_ID)

    if result:
        with DISTRICTS_LOCK:
            DISTRICTS = result


def _load_sources():
    global SOURCES
    result = _load_reference(DEAL_SOURCE_REFERENCE_ID)

    if result:
        with SOURCES_LOCK:
            SOURCES = result


def _load_stages():
    global STAGES
    result = _load_reference(DEAL_STAGE_LIST_REFERENCE_ID)

    if result:
        with STAGES_LOCK:
            STAGES = result


# праздничные даты из списка
def _load_festive_dates():
    result = {}
    params = {
        'IBLOCK_TYPE_ID': 'lists',
        'IBLOCK_ID': FESTIVE_LIST_IBLOCK_ID,
    }

    try:
        result = list(send_request('lists.element.get', params)[0][FESTIVE_LIST_PROPERTY_NAME].values())

    except Exception as e:
        logging.error("Exception getting florists, %s", e)

    global FESTIVE_DATES
    if result:
        with FESTIVE_DATES_LOCK:
            FESTIVE_DATES = result


def load_dicts():
    # TODO: batch load instead of sleep intervals workaround
    sleep_interval = 1
    _load_couriers()
    time.sleep(sleep_interval)
    _load_florists()
    time.sleep(sleep_interval)
    _load_payment_methods()
    time.sleep(sleep_interval)
    _load_payment_types()
    time.sleep(sleep_interval)
    _load_orders_types()
    time.sleep(sleep_interval)
    _load_deal_times()
    time.sleep(sleep_interval)
    _load_subdivisions()
    time.sleep(sleep_interval)
    _load_districts()
    time.sleep(sleep_interval)
    _load_sources()
    time.sleep(sleep_interval)
    _load_stages()
    time.sleep(sleep_interval)
    _load_festive_dates()


def refresh_oauth(refresh_token):
    for a in range(REQUESTS_MAX_ATTEMPTS):
        try:
            response = SESSION.get(
                url=creds.BITRIX_OAUTH_REFRESH_URL.format(refresh_token),
                timeout=REQUESTS_TIMEOUT)

            if response and response.ok:
                json = response.json()

                access_token = json.get('access_token')
                refresh_token = json.get('refresh_token')

                logger.info('OAuth refreshed')
                return access_token, refresh_token
            else:
                logger.error("Error OAuth refreshing: %s", response)

        except Exception as e:
            error = 'Bitrix OAuth refresh exception %s' % e
            logger.error(error)

    return None, None


def get_user_position(user_id):
    # user.get isn't a getter method, but a list method. Yep, B24 API is irrational
    users = send_request('user.get',
                         {'ID': user_id})
    if users and len(users) > 0:
        return users[0][USER_POSITION_ALIAS]
    else:
        return None


def get_user_name(user_id):
    if not user_id:
        return None

    users = send_request('user.get',
                         {'ID': user_id})

    if users and len(users) > 0:
        user = users[0]
        return user[USER_NAME_ALIAS] + ' ' + user[USER_SURNAME_ALIAS]
    else:
        return None


def get_contact_data(contact_id):
    if not contact_id:
        return None

    contact_data = send_request('crm.contact.get',
                                {'id': contact_id}, getter_method=True)

    contact_phone = ''

    if contact_data and contact_data.get(CONTACT_HAS_PHONE_ALIAS) == CONTACT_HAS_PHONE:
        contact_phone = Utils.prepare_external_field(contact_data[CONTACT_PHONE_ALIAS][0], 'VALUE')

    contact_name = Utils.prepare_external_field(contact_data, CONTACT_USER_NAME_ALIAS)

    return {
        CONTACT_USER_NAME_ALIAS: contact_name,
        CONTACT_PHONE_ALIAS: contact_phone
    }


def get_deal_stage(deal_id):
    deal = send_request('crm.deal.get',
                        {'ID': deal_id}, getter_method=True)

    return deal[DEAL_STAGE_ALIAS]  # throws exception in case of problems


def generate_photo_link(obj, access_token):
    path = obj['downloadUrl'].replace('auth=', 'auth=' + access_token)
    return creds.BITRIX_MAIN_PAGE + path


def process_deal_photo_dl_urls(deal, access_token, field_aliases=()):
    photos_list = []

    for fa in field_aliases:
        if fa in deal:
            data = deal[fa]
            if isinstance(data, list):
                for photo in data:
                    photos_list.append(generate_photo_link(photo, access_token))
            else:
                photos_list.append(generate_photo_link(data, access_token))

    return photos_list


def get_deal_photo_dl_urls(deal_id, access_token, field_aliases=()):
    deal = get_deal(deal_id)
    return process_deal_photo_dl_urls(deal, access_token, field_aliases)
