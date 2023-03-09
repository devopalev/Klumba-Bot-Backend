import os
import hashlib
import time
import random
import logging
import sqlite3
import shutil
from threading import local

from source import config as cfg


logger = logging.getLogger(__name__)

ORDERS_DIR = os.path.join(cfg.DATA_DIR_NAME, cfg.ORDERS_DIR_NAME)
os.makedirs(ORDERS_DIR, exist_ok=True)

ORDER_DIGEST_LIMIT = 8
ORDER_EXPIRED_TIME_LIMIT = 30 * 24 * 60 * 60  # days to seconds to order expiration
ORDERS_CLEANUP_TIME = '03:00'

ORDERS_DB = local()


def init_db():
    if not hasattr(ORDERS_DB, 'conn'):
        ORDERS_DB.conn = sqlite3.connect(os.path.join(ORDERS_DIR, cfg.ORDERS_DATABASE))

    cursor = ORDERS_DB.conn.cursor()

    cursor.execute('create table if not exists orders (digest text, id text)')
    ORDERS_DB.conn.commit()


def save_deal(user, deal_id):
    photos = user.equip.photos
    logger.info(f'Saving {len(photos)} photos now')

    order_digest = ''
    all_is_on_disk = True
    for p in photos:
        logger.info(f'Photo file {p.name_big} has state {p.state}')
        order_digest += p.name_big
        if not p.has_been_saved():
            all_is_on_disk = False

    if all_is_on_disk:
        logger.info("Order # %s: all photos are on disk, using previous digest!")
        return

    order_digest += (str(time.time()) + str(random.random()))
    order_digest = hashlib.sha256(order_digest.encode()).hexdigest()[:ORDER_DIGEST_LIMIT]

    while os.path.isdir(os.path.join(ORDERS_DIR, order_digest)):
        order_digest += str(random.random())
        order_digest = hashlib.sha256(order_digest.encode()).hexdigest()[:ORDER_DIGEST_LIMIT]

    order_dir_path = os.path.join(ORDERS_DIR, order_digest)

    os.mkdir(order_dir_path)

    for p in photos:
        with open(os.path.join(ORDERS_DIR, *(order_digest, p.name_big)), 'wb') as f:
            p.save_big(f)

    if not hasattr(ORDERS_DB, 'conn'):
        ORDERS_DB.conn = sqlite3.connect(os.path.join(ORDERS_DIR, cfg.ORDERS_DATABASE))

    cursor = ORDERS_DB.conn.cursor()
    cursor.execute('insert into orders values(?,?)', (order_digest, deal_id))
    ORDERS_DB.conn.commit()

    user.equip.digest = order_digest


def orders_cleanup_job():
    try:
        logger.info("Running orders dir maintenance now!")
        cur_time = time.time()

        if not hasattr(ORDERS_DB, 'conn'):
            ORDERS_DB.conn = sqlite3.connect(os.path.join(ORDERS_DIR, cfg.ORDERS_DATABASE))

        cursor = ORDERS_DB.conn.cursor()

        for entry in os.scandir(ORDERS_DIR):
            delta_time = cur_time - entry.stat().st_mtime

            order_digest = ''
            try:
                if entry.is_dir() and delta_time >= ORDER_EXPIRED_TIME_LIMIT:  # expired
                    order_digest = entry.name
                    cursor.execute('delete from orders where digest=?', (order_digest,))
                    shutil.rmtree(entry.path)
            except Exception as e:
                logger.error("Maintenance entry {} error: {}".format(order_digest, e))

        ORDERS_DB.conn.commit()
    except Exception as e:
        logger.error("Maintenance service job error: %s", e)
