import sqlite3
import os
import logging
from threading import local

import source.config as cfg

ORDERS_DIR = os.path.join(cfg.DATA_DIR_NAME, cfg.ORDERS_DIR_NAME)


logger = logging.getLogger(__name__)
ORDERS_DB = local()


def get_deal_id(digest):
    try:
        if not hasattr(ORDERS_DB, 'conn'):
            ORDERS_DB.conn = sqlite3.connect(os.path.join(ORDERS_DIR, cfg.ORDERS_DATABASE))
            pass

        cursor = ORDERS_DB.conn.cursor()
        cursor.execute('select * from orders where digest=?', (digest,))
        data = cursor.fetchall()

        if len(data) == 0:
            return None
        else:
            return data[0][1]
    except Exception as e:
        logger.error('Error getting deal id by digest: %s', e)
        return None


def get_deal_photos_path(digest):
    photos_path_list = []

    try:
        for photo_entry in os.scandir(os.path.join(ORDERS_DIR, digest)):
            photos_path_list.append('/' + digest + '/' + photo_entry.name)

    except Exception as e:
        logging.error('Error traversing deal photos to return: %s', e)
        return []

    return photos_path_list
