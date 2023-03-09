import copy
import threading
import uuid
from typing import List, Dict
import requests
import time
from threading import Lock
import source.secret as creds
import source.utils.Utils as Utils

from urllib.parse import urlencode
from source.bitrix.BitrixFieldsAliases import *
from source.bitrix.BitrixFieldMappings import *
from source.config import *

logger = logging.getLogger(__name__)


class Field:
    def __init__(self, id_entry, field: dict):
        if field.get('formLabel'):
            self.name = field['formLabel']
        elif field.get('title'):
            self.name = field['title']
        else:
            self.name = None

        self.id = id_entry
        self.type = field['type']
        # EXAMPLE items: [{'ID': '2293', 'VALUE': 'Басово'}, {'ID': '2295', 'VALUE': 'Стадион'}]
        self.items: list = field.get('items') if field.get('items') else []

    def __repr__(self):
        return str(self.__dict__)

    def get_name_item(self, value):
        for item in self.items:
            if value == item['ID']:
                return item['VALUE']


class _Throttling:
    """ Механиз тротлинга, используется как часть запросов для контроля"""
    def __init__(self, limit_request: int = 2, limit_time: int = 1):
        self._times = []
        self._limit_request = limit_request
        self._limit_time = limit_time
        self._lock = threading.Lock()
        self._time_method = time.time
        self._sleep_method = time.sleep

    def acquire(self, block=False):
        if block:
            self.wait()
        with self._lock:
            if self._times and self._time_method() - self._times[0] >= self._limit_time:
                self._times.pop(0)

            if len(self._times) == self._limit_request:
                return False
            else:
                self._times.append(self._time_method())
                return True

    def wait(self):
        sleep = False
        with self._lock:
            if len(self._times) == self._limit_request:
                sleep = True
        if sleep:
            rate = self._limit_time - (self._time_method() - self._times[0])
            self._sleep_method(float(0 if rate < 0 else rate))

    def get_rate(self):
        with self._lock:
            if len(self._times) == self._limit_request:
                rate = self._time_method() - self._times[0]
                return 0 if rate < 0 else rate
            else:
                return 0


# Базовый, использовать в крайнем случае
class Request:
    SESSION = requests.session()
    SLEEP_INTERVAL = 0.5  # seconds
    QUERY_LIMIT_EXCEEDED = 'QUERY_LIMIT_EXCEEDED'
    REQUESTS_TIMEOUT = 15  # seconds
    REQUESTS_MAX_ATTEMPTS = 3
    throttling = _Throttling()

    @staticmethod
    def _error_handler(func):
        def wrapp(*arg, **kwargs):
            for a in range(Request.REQUESTS_MAX_ATTEMPTS):
                try:
                    ok, result = func(*arg, **kwargs)

                    if ok and (isinstance(result, dict) and result.get("result_error")):
                        # handling error
                        for key, error in result.get("result_error").items():
                            logger.error(f'Batch Error:\n    Key: {key}\n    Bitrix bad response: {error}\n'
                                         f'Request params: {arg}, {kwargs}')
                        return result
                    if ok:
                        return result
                    elif result == Request.QUERY_LIMIT_EXCEEDED:
                        logger.warning("Превышен лимит запросов к API Bitrix24")
                        time.sleep(Request.SLEEP_INTERVAL)
                    else:
                        error = f'Bitrix request failed: Attempt: {a}  Request params: {arg};;{kwargs}  '
                        logger.error(error + result)
                except Exception as e:
                    error = 'Sending Bitrix sourse request error %s' % e
                    logger.error(error, exc_info=True)

            raise Exception(f'B24 request failed: {arg}, {kwargs}')

        return wrapp

    @classmethod
    @_error_handler
    def send(cls, method, params=None, handle_next=False, getter_method=False, obtain_total=False, throttling=False):
        if params is None:
            params = {}

        if throttling:
            cls.throttling.acquire(block=True)
        # Запрос может отправляться как методом GET, так и POST.
        response = cls.SESSION.post(url=creds.BITRIX_API_URL + method,
                                    json=params, timeout=cls.REQUESTS_TIMEOUT)
        logger.debug(f"Send request bitrix \nurl: {response.url}\njson: {params}")
        # code 400 in response to getter method means object not found
        if (getter_method or "get" in method) and response.status_code == 400:
            return True, None

        if response and response.ok:
            json = response.json()
            error = json.get('error')
            logger.debug(f"Bitrix recv: {json}")
            if error == cls.QUERY_LIMIT_EXCEEDED:
                return response.ok, cls.QUERY_LIMIT_EXCEEDED

            if obtain_total:
                return response.ok, json.get('total')

            next_counter = json.get('next')
            result: list = json.get('result')

            # handling List[]
            if result is not None and handle_next and next_counter:
                params['start'] = next_counter
                next_result = cls.send(method, params, True, throttling=True)
                result.extend(next_result)
                return True, result

            return response.ok, result
        return response.ok, response.text

    @classmethod
    @_error_handler
    def batch(cls, params, handle_next=False, halt=False, orig_params=None, throttling=False):
        """
        :param throttling:
        :param halt:
        :param handle_next:
        :param orig_params: link params
        :param params: {'halt': 0, 'cmd': {'test': ...}}
        :return:
        """
        if params is None:
            params = {}
        if orig_params is None:
            orig_params = params
        if throttling:
            cls.throttling.acquire(block=True)

        # Запрос может отправляться как методом GET, так и POST.
        response = cls.SESSION.post(url=creds.BITRIX_API_URL + 'batch',
                                    json=params, timeout=cls.REQUESTS_TIMEOUT)
        logger.debug(f"Send request bitrix \nurl: {response.url}\njson: {params}")
        if response and response.ok:
            result = response.json()
            error = result.get('error')
            logger.debug(f"Bitrix recv: {result}")
            if error == cls.QUERY_LIMIT_EXCEEDED:
                return True, cls.QUERY_LIMIT_EXCEEDED

            result_batch = result.get('result')

            result_cmd: dict = result_batch.get('result')
            next_counter: dict = result_batch.get('result_next')

            # handling List[]
            if result_cmd is not None and handle_next and next_counter:
                next_cmd = {}
                for key, next_count in next_counter.items():
                    next_cmd[key] = orig_params["cmd"].get(key) + f"&start={next_count}"
                new_params = {'halt': 1 if halt else 0, 'cmd': next_cmd}

                result_next: dict = cls.batch(new_params, handle_next, halt, orig_params, throttling=True)

                for k, v in result_next["result"].items():
                    result_cmd[k].extend(v)
                return response.ok, result_batch

            return response.ok, result_batch

        return response.ok, response.text


class Batch:
    REQUESTS_MAX_ATTEMPTS = 5

    def __init__(self, halt=False, handle_next=False):
        self.halt = halt
        self.handle_next = handle_next
        self._cmd = {}
        self._response = {}
        self._response_ok = {}
        self.response_err = {}
        self._params = {}
        self._lock = threading.Lock()
        self._lock_result = threading.Lock()
        self.done = False

    @property
    def full(self):
        if len(self._cmd) == 50:
            return True
        return False

    @property
    def count_cmd(self):
        return len(self._cmd)

    def _build_params(self, key, value, in_key=None):
        def result_handle(data, result):
            for el in result:
                if isinstance(el, list):
                    result_handle(data, el)
                elif isinstance(el, str):
                    url_params.append(el)

        url_params = []

        if isinstance(value, dict):
            values = list(value.values())
            in_keys = list(value.keys())
            new_keys = [key] * len(in_keys)
            result_handle(url_params, list(map(self._build_params, new_keys, values, in_keys)))

        elif isinstance(value, list):
            if in_key:
                new_key = f"{key}[{in_key}]"
            else:
                new_key = key

            new_key = [f"{new_key}[]"] * len(value)
            result_handle(url_params, list(map(self._build_params, new_key, value)))

        elif isinstance(value, str) or value is None:
            if in_key:
                new_key = f"{key}[{in_key}]"
            else:
                new_key = key
            value = "null" if value is None else value
            # url_params.append(f"{new_key}={value}")  # DEBUG
            url_params.append(urlencode({new_key: value}))
        else:
            raise TypeError("Неизвестный параметр")

        return url_params

    def _build_cmd(self, method, params):
        """
        :return: Example url array 'crm.deal.list?filter[UF_CRM_1614264167]=41305
        &filter[!STAGE][]=C17:NEW&filter[!STAGE][]=C17:17&select[]=ID&select[]=UF_CRM_1572513138'
        """
        url = method + '?'
        url_params = []

        for k, v in params.items():
            url_params.extend(self._build_params(k, v))
        return url + "&".join(url_params)

    def add_request(self, key: str, method: str, params: dict = None):
        if len(self._cmd) == 50:
            raise IndexError("Достигнуто максимальное количество запросов")
        if params is None:
            self._cmd.update({key: method})
        else:
            self._cmd.update({key: self._build_cmd(method, params)})

    def send(self, throttling=True):
        if throttling:
            Request.throttling.acquire(block=True)
        with self._lock:
            if self.done:
                return False
            if self._cmd:
                self.done = True
                self._params = {'halt': 1 if self.halt else 0, 'cmd': self._cmd}
                result = Request.batch(self._params, self.handle_next, self.halt)
                self._response = result
                if result.get("result"):
                    self._response_ok = result.get("result")
                if result.get("result_error"):
                    self.response_err = result.get("result_error")
                return True
            else:
                raise BufferError("Нет ни одного запроса")

    @property
    def response(self):
        with self._lock:
            return self._response

    def get_result(self, key, getter_method=False, return_any_result=True):
        with self._lock:
            if key in self._response_ok:
                return self._response_ok.get(key)
            if key in self.response_err and return_any_result:
                if ("get" in self._params["cmd"][key] or getter_method) and \
                        self.response_err[key].get("error_description") == "Not found":
                    return None
                return self.response_err.get(key)


# Основной тип запроса
class ThrottlingRequest:
    _lock = threading.Lock()
    _curr_batch = None

    @classmethod
    def send(cls, method, params=None, handle_next=False, getter_method=False):
        batch = None
        with cls._lock:
            if not Request.throttling.acquire():
                logger.info("THROTTLING ACTIVE!")
                if not cls._curr_batch:
                    cls._curr_batch = Batch(handle_next=True)
                if cls._curr_batch.full:
                    cls._curr_batch = Batch(handle_next=True)
                batch = cls._curr_batch
                key = uuid.uuid4().hex
                batch.add_request(key, method, params)
                if not batch.handle_next and handle_next:
                    batch.handle_next = True

        if batch:
            Request.throttling.wait()
            with cls._lock:
                cls._curr_batch = None
                batch.send(throttling=False)
            return batch.get_result(key, getter_method=getter_method)
        else:
            return Request.send(method, params, handle_next=handle_next, getter_method=getter_method)


class BitrixUsers:
    _users_ids = {}  # id -> response bitrix dict
    _users_phone = {}  # phone -> response bitrix dict
    _lock = threading.Lock()

    class ConstFields:
        ID = 'ID'
        ROLE = 'UF_USR_1614265033324'  # Роль
        NAME = 'NAME'
        SURNAME = 'LAST_NAME'
        MAIN_PHONE = 'PERSONAL_MOBILE'

    class ConstRoleId:
        # user role
        FLORIST_ID = '2343'  # Флорист
        COURIER_ID = '2347'  # Курьер

    @classmethod
    def user_by_phone(cls, phone_number):
        with cls._lock:
            return cls._users_phone.get(phone_number)

    @classmethod
    def user_by_bitrix_id(cls, bitrix_id):
        with cls._lock:
            return cls._users_ids.get(bitrix_id)

    @classmethod
    def get_users_by_role(cls, role_id, search_surname: str = ''):
        result = {}
        search_surname = search_surname.upper()
        with cls._lock:
            for bitrix_id, user in cls._users_ids.items():
                if user[cls.ConstFields.ROLE] == role_id:
                    if search_surname:
                        surname = user[cls.ConstFields.SURNAME].upper()
                        if surname.startswith(search_surname):
                            result[bitrix_id] = user
                    else:
                        result[bitrix_id] = user
        return result

    @classmethod
    def get_florists(cls, search_surname: str = ''):
        return cls.get_users_by_role(cls.ConstRoleId.FLORIST_ID, search_surname)

    @classmethod
    def get_couriers(cls, search_surname: str = ''):
        return cls.get_users_by_role(cls.ConstRoleId.COURIER_ID, search_surname)

    @classmethod
    def fullname_by_bitrix_id(cls, bitrix_id):
        user = cls.user_by_bitrix_id(bitrix_id)
        if user:
            return f"{user[cls.ConstFields.SURNAME]} {user[cls.ConstFields.NAME]}"
        else:
            return "Отсутствует"

    @classmethod
    def update_user_by_phone(cls, phone_number):
        params = {'filter': {'ACTIVE': 'True', USER_MAIN_PHONE_ALIAS: phone_number}}
        try:
            result: List[dict] = ThrottlingRequest.send('user.get', params)

            if result:
                user = result[0]

                with cls._lock:
                    cls._users_phone[Utils.prepare_phone_number(user[USER_MAIN_PHONE_ALIAS])] = user
                    cls._users_ids[user[USER_ID_ALIAS]] = user
        except Exception as e:
            logging.error(f"Exception getting bitrix user({phone_number}), %s", e)

    @classmethod
    def update(cls):
        params = {'filter': {'ACTIVE': 'True'}}

        try:
            # can't select particular fields due to Bitrix API restrictions
            # load all fields for now
            result = ThrottlingRequest.send('user.get', params, handle_next=True)

            users_phone_dict = {}
            users_ids_dict = {}

            for u in result:
                # Записываем данные о пользователе
                users_phone_dict[Utils.prepare_phone_number(u[USER_MAIN_PHONE_ALIAS])] = u
                users_ids_dict[u[USER_ID_ALIAS]] = u

            if result:
                with cls._lock:
                    cls._users_phone = users_phone_dict
                    cls._users_ids = users_ids_dict

        except Exception as e:
            logging.error("Exception getting bitrix users, %s", e)


class Bitrix:
    class FieldsID:
        # deal field ID's
        COURIER_FIELD_ID = '1009'  # Курьер
        PAYMENT_TYPE = '835'  # Тип оплаты
        PAYMENT_METHOD = '1389'  # Способ оплаты
        ORDER_TYPE = '1679'  # Тип заказа
        DEAL_TIME = '771'  # Время
        DEAL_SUBDIVISION = '1683'  # Подразделение, принявшее заказ
        DEAL_DISTRICT = '743'  # Район доставки

        # actual dates dict {some_id: date}
        FESTIVE_LIST_PROPERTY_NAME = 'PROPERTY_225'
        # festive dates list
        FESTIVE_LIST_IBLOCK_ID = '75'

    class EntityID:
        SOURCE = 'SOURCE'  # Источник сделки (все источники)
        STAGE = 'DEAL_STAGE_17'  # этапы сделки (клумба)
        CONTACT_TYPE = 'CONTACT_TYPE'  # тип контакта

    class Festive:
        # festive Approvement
        APPROVEMENT_YES = '2891'
        APPROVEMENT_NO = '2893'
        APPROVEMENT_NOT_SELECTED = '3003'
        # festive dates list
        LIST_IBLOCK_ID = '75'
        # actual dates dict {some_id: date}
        LIST_PROPERTY_NAME = 'PROPERTY_225'

    class _Data:
        _lock = Lock()

        def __init__(self):
            self.orders_types = {}
            self.deal_times = {}
            self.subdivisions = {}
            self.districts = {}
            self.sources = {}
            self.stages = {}
            self.festive_dates = []
            self.payment_types = {}
            self.payment_methods = {}
            self.fields: Dict[str: Field] = {}
            self.contact_type_id = {}

        def __getattribute__(self, item):
            if item in object.__getattribute__(self, '__dict__'):
                with object.__getattribute__(self, '_lock'):
                    return copy.deepcopy(object.__getattribute__(self, item))
            else:
                object.__getattribute__(self, item)

        def __setattr__(self, key, value):
            with object.__getattribute__(self, '_lock'):
                object.__setattr__(self, key, value)

    data = _Data()
    users = BitrixUsers

    @classmethod
    def update(cls):
        batch = Batch(handle_next=True)

        # Готовим параметры
        method_userfield = 'crm.deal.userfield.get'
        method_reference = 'crm.status.list'

        key_orders = "orders"
        batch.add_request(key_orders, method_userfield, {'id': cls.FieldsID.ORDER_TYPE})

        key_payment_type = "payment_type"
        batch.add_request(key_payment_type, method_userfield, {'id': cls.FieldsID.PAYMENT_TYPE})

        key_payment_method = "payment_method"
        batch.add_request(key_payment_method, method_userfield, {'id': cls.FieldsID.PAYMENT_METHOD})

        key_deal_time = "deal_time"
        batch.add_request(key_deal_time, method_userfield, {'id': cls.FieldsID.DEAL_TIME})

        key_subdivision = "subdivision"
        batch.add_request(key_subdivision, method_userfield, {'id': cls.FieldsID.DEAL_SUBDIVISION})

        key_deal_district = "deal_district"
        batch.add_request(key_deal_district, method_userfield, {'id': cls.FieldsID.DEAL_DISTRICT})

        key_sources = "sources"
        batch.add_request(key_sources, method_reference, {'order': {'SORT': 'ASC'},
                                                          'filter': {'ENTITY_ID': cls.EntityID.SOURCE}})

        key_stages = "stages"
        batch.add_request(key_stages, method_reference, {'order': {'SORT': 'ASC'},
                                                         'filter': {'ENTITY_ID': cls.EntityID.STAGE}})

        key_fistive = "festive"
        batch.add_request(key_fistive, 'lists.element.get', {'IBLOCK_TYPE_ID': 'lists',
                                                             'IBLOCK_ID': cls.Festive.LIST_IBLOCK_ID})

        key_fields_name = "fields_name"
        batch.add_request(key_fields_name, 'crm.deal.fields')

        key_contact_type_id = "contact_type_id"
        batch.add_request(key_stages, method_reference, {'order': {'SORT': 'ASC'},
                                                         'filter': {'ENTITY_ID': cls.EntityID.CONTACT_TYPE}})

        # Отправляем запрос
        try:
            batch.send()
        except Exception as e:
            logger.error("Exception getting reference dict: %s", e, exc_info=True)
        else:
            # Парсим результат
            if batch.get_result(key_orders, return_any_result=False):
                cls.data.orders_types = {el['ID']: el['VALUE'] for el in batch.get_result(key_orders)['LIST']}
            if batch.get_result(key_payment_type, return_any_result=False):
                cls.data.payment_types = {el['ID']: el['VALUE'] for el in batch.get_result(key_payment_type)['LIST']}
            if batch.get_result(key_payment_method, return_any_result=False):
                cls.data.payment_methods = {el['ID']: el['VALUE'] for el in
                                            batch.get_result(key_payment_method)['LIST']}
            if batch.get_result(key_deal_time, return_any_result=False):
                cls.data.deal_times = {el['ID']: el['VALUE'] for el in batch.get_result(key_deal_time)['LIST']}
            if batch.get_result(key_subdivision, return_any_result=False):
                cls.data.subdivisions = {el['ID']: el['VALUE'] for el in batch.get_result(key_subdivision)['LIST']}
            if batch.get_result(key_deal_district, return_any_result=False):
                cls.data.districts = {el['ID']: el['VALUE'] for el in batch.get_result(key_deal_district)['LIST']}

            if batch.get_result(key_sources, return_any_result=False):
                cls.data.sources = {el['STATUS_ID']: el['NAME'] for el in batch.get_result(key_sources)}
            if batch.get_result(key_stages, return_any_result=False):
                cls.data.stages = {el['STATUS_ID']: el['NAME'] for el in batch.get_result(key_stages)}

            if batch.get_result(key_fistive, return_any_result=False):
                cls.data.festive_dates = list(batch.get_result(key_fistive)[0][cls.Festive.LIST_PROPERTY_NAME].values())

            if batch.get_result(key_fields_name, return_any_result=False):
                data = {}
                for k, v in batch.get_result(key_fields_name).items():
                    data[k] = Field(k, v)
                cls.data.fields = data

            if batch.get_result(key_contact_type_id, return_any_result=False):
                cls.data.contact_type_id = {el['STATUS_ID']: el['NAME'] for el in batch.get_result(key_contact_type_id)}


class BitrixOAUTH:
    OAUTH_LOCK = Lock()

    @staticmethod
    def refresh_oauth(refresh_token):
        for a in range(Request.REQUESTS_MAX_ATTEMPTS):
            try:
                response = Request.SESSION.get(
                    url=creds.BITRIX_OAUTH_REFRESH_URL.format(refresh_token),
                    timeout=Request.REQUESTS_TIMEOUT)

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


def get_deal(deal_id):
    result = ThrottlingRequest.send('crm.deal.get', {'id': deal_id}, getter_method=True)
    return result


def update_deal(deal_id, fields):
    ThrottlingRequest.send('crm.deal.update', {'id': deal_id,
                                               'fields': fields})


def get_contact_data(contact_id):
    if not contact_id:
        return None

    contact_data = ThrottlingRequest.send('crm.contact.get',
                                          {'id': contact_id}, getter_method=True)

    contact_phone = ''

    if contact_data and contact_data.get(CONTACT_HAS_PHONE_ALIAS) == CONTACT_HAS_PHONE:
        contact_phone = Utils.prepare_external_field(contact_data[CONTACT_PHONE_ALIAS][0], 'VALUE')

    contact_name = Utils.prepare_external_field(contact_data, CONTACT_USER_NAME_ALIAS)

    return {
        CONTACT_USER_NAME_ALIAS: contact_name,
        CONTACT_PHONE_ALIAS: contact_phone
    }


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
