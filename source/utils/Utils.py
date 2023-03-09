import re
import os
import sqlite3
import telegram.utils.helpers as tg_helpers
from threading import local

import source.BitrixFieldMappings as BitrixFieldMappings
import source.config as cfg
import source.TextSnippets as Txt

ADDRESS_LINK_RESOLVING_SPECIAL_CHARS_PATTERN = re.compile('["]')
BITRIX_ADDRESS_PATTERN = re.compile('(.+)\\|(\\d+\\.\\d+;\\d+\\.\\d+)')
BITRIX_DATE_PATTERN = re.compile('(\\d{4})-(\\d{2})-(\\d{2}).*')
PHONE_INVALID_SYMBOLS_LIST_PATTERN = re.compile('[^\\d]')

BITRIX_DICTS_DB = local()

# using only last PHONE_SIGNIFICANT_PART digits handling phone numbers
PHONE_SIGNIFICANT_PART_SIZE = 10


# remove all except digits to properly display in Tg clients
# remove country code (one-char only)!
def prepare_phone_number(phone):
    if phone:
        return re.sub(PHONE_INVALID_SYMBOLS_LIST_PATTERN, '', phone)[-PHONE_SIGNIFICANT_PART_SIZE:]

    return ''


# fully escape Markdownv2 string
def escape_mdv2(string):
    return tg_helpers.escape_markdown(text=string, version=2)


# escape '()' part of markdown link definition
def escape_mdv2_textlink(string):
    return tg_helpers.escape_markdown(text=string, version=2, entity_type='text_link')


def _stringify_field(field):
    if not bool(field):
        return Txt.FIELD_IS_EMPTY_PLACEHOLDER
    else:
        return str(field)


def prepare_str(field, escape_md=True):
    stringified = _stringify_field(field)

    return escape_mdv2(stringified) if escape_md else stringified


def prepare_external_field(obj, key, lock=None, escape_md=True):
    if not obj:
        return Txt.FIELD_IS_EMPTY_PLACEHOLDER

    if lock:
        lock.acquire()

    val = obj.get(key)

    if lock:
        lock.release()

    if type(val) is list:
        val = ', '.join(val)

    return prepare_str(val, escape_md)


def prepare_deal_address(obj, addrkey, escape_md=True):
    val = prepare_external_field(obj, addrkey, escape_md=escape_md)

    val = re.sub(ADDRESS_LINK_RESOLVING_SPECIAL_CHARS_PATTERN, '', val)

    location_check = BITRIX_ADDRESS_PATTERN.search(val)

    if location_check:
        return location_check[1], location_check[2]

    # address, location
    return val, None


def prepare_deal_date(obj, datekey, escape_md=True):
    val = _stringify_field(obj.get(datekey))

    date_check = BITRIX_DATE_PATTERN.search(val)

    if date_check:
        date_str = date_check[3] + '.' + date_check[2] + '.' + date_check[1]
        return escape_mdv2(date_str) if escape_md else date_str

    return val


def prepare_deal_time(obj, timekey, escape_md=True):
    deal_time_id = prepare_external_field(obj, timekey)

    if not hasattr(BITRIX_DICTS_DB, 'conn'):
        BITRIX_DICTS_DB.conn = sqlite3.connect(os.path.join(cfg.DATA_DIR_NAME, cfg.BITRIX_DICTS_DATABASE))

    cursor = BITRIX_DICTS_DB.conn.cursor()
    cursor.execute('select * from deal_times where id=?', (deal_time_id,))
    data = cursor.fetchall()

    if len(data) == 0:
        return Txt.FIELD_IS_EMPTY_PLACEHOLDER
    else:
        time_str = data[0][1]
        return escape_mdv2(time_str) if escape_md else time_str


def prepare_deal_incognito_client_view(obj, inckey):
    val = prepare_external_field(obj, inckey)

    if val in BitrixFieldMappings.DEAL_INCOGNITO_MAPPING_CLIENT:
        return BitrixFieldMappings.DEAL_INCOGNITO_MAPPING_CLIENT[val]
    else:
        return False


def prepare_deal_incognito_bot_view(obj, inckey):
    val = prepare_external_field(obj, inckey)

    if val in BitrixFieldMappings.DEAL_INCOGNITO_MAPPING_OPERATOR:
        return BitrixFieldMappings.DEAL_INCOGNITO_MAPPING_OPERATOR[val]
    else:
        return Txt.FIELD_IS_EMPTY_PLACEHOLDER


def prepare_deal_supply_method(obj, key):
    val = obj.get(key)
    return prepare_external_field(BitrixFieldMappings.DEAL_SUPPLY_METHOD_MAPPING, val)
