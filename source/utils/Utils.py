import re
import os
import sqlite3
import telegram.utils.helpers as tg_helpers
from threading import local

import source.bitrix.BitrixFieldMappings as BitrixFieldMappings
import source.config as cfg

import cv2
import numpy as np

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
        return 'нет'
    else:
        return str(field)


def prepare_str(field, escape_md=True):
    stringified = _stringify_field(field)

    return escape_mdv2(stringified) if escape_md else stringified


def prepare_external_field(obj, key, lock=None, escape_md=True):
    if not obj:
        return 'нет'

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
        return 'нет'
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
        return 'нет'


def prepare_deal_supply_method(obj, key):
    val = obj.get(key)
    return prepare_external_field(BitrixFieldMappings.DEAL_SUPPLY_METHOD_MAPPING, val)


def qr_analise(image: bytes):
    """
    Анализирует фото на наличие qr-кода.
    :param image: QR photo
    :return: если qr найден возвращает его содержимое в виде str, если нет возвращает False.
    """
    def qr_reader(img):
        detector = cv2.QRCodeDetector()
        data, bbox, _ = detector.detectAndDecode(img)
        if data:
            return data
        else:
            return False

    image_np = np.frombuffer(image, np.uint8)
    img_np = cv2.imdecode(image_np, cv2.IMREAD_COLOR)

    result = qr_reader(img_np)

    if result:
        return result
    else:
        # Load imgae, grayscale, Gaussian blur, Otsu's threshold
        original = img_np.copy()
        gray = cv2.cvtColor(img_np, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (9, 9), 0)
        thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

        # Morph close
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        close = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)

        # Find contours and filter for QR code
        cnts = cv2.findContours(close, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = cnts[0] if len(cnts) == 2 else cnts[1]
        for c in cnts:
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.04 * peri, True)
            x, y, w, h = cv2.boundingRect(approx)
            area = cv2.contourArea(c)
            ar = w / float(h)
            if len(approx) == 4 and area > 1000 and (ar > .85 and ar < 1.3):
                cv2.rectangle(img_np, (x, y), (x + w, y + h), (36, 255, 12), 3)
                ROI = original[y - 10:y + h + 10, x - 10:x + w + 10]
                gray_ROI = cv2.cvtColor(ROI, cv2.COLOR_BGR2GRAY)
                ret, threshold_ROI = cv2.threshold(gray_ROI, 127, 255, 0)

        try:
            for roi in (ROI, gray_ROI, threshold_ROI):
                result = qr_reader(roi)
                if result:
                    return result
            else:
                return False
        except UnboundLocalError:
            return False
        except Exception:
            return False


