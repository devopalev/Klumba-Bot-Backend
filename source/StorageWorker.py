import os
import schedule
from threading import Thread, local
import time
import random
import logging
import sqlite3

import source.handlers.WorkingDeal.Equip.StorageHandlers as Photos1
import source.bitrix.BitrixWorker as BW
import source.config as cfg

random.seed()

SCHEDULING_SLEEP_INTERVAL = 60  # 1 min

logger = logging.getLogger(__name__)
BITRIX_DICTS_DB = local()


# general purpose databases
def init_bitrix_dicts_db():
    if not hasattr(BITRIX_DICTS_DB, 'conn'):
        BITRIX_DICTS_DB.conn = sqlite3.connect(os.path.join(cfg.DATA_DIR_NAME, cfg.BITRIX_DICTS_DATABASE))

    cursor = BITRIX_DICTS_DB.conn.cursor()

    cursor.execute('create table if not exists deal_times (id text, val text)')
    BITRIX_DICTS_DB.conn.commit()


def load_bitrix_dicts():
    BW.Bitrix.update()

    # separate thread connection
    if not hasattr(BITRIX_DICTS_DB, 'conn'):
        BITRIX_DICTS_DB.conn = sqlite3.connect(os.path.join(cfg.DATA_DIR_NAME, cfg.BITRIX_DICTS_DATABASE))

    cursor = BITRIX_DICTS_DB.conn.cursor()

    # some dicts need to be saved to use in Client backend process
    cursor.execute('delete from deal_times')
    cursor.executemany('insert into deal_times values (?,?)', BW.Bitrix.data.deal_times.items())
    BITRIX_DICTS_DB.conn.commit()


def maintain_storage():
    try:
        init_bitrix_dicts_db()
        Photos1.init_db()
        BW.BitrixUsers.update()
        load_bitrix_dicts()

        schedule.every().day.at(Photos1.ORDERS_CLEANUP_TIME).do(Photos1.orders_cleanup_job)
        schedule.every(15).minutes.do(BW.BitrixUsers.update)
        schedule.every().hour.do(load_bitrix_dicts)

        def thread_fun():
            while True:
                try:
                    schedule.run_pending()
                    time.sleep(SCHEDULING_SLEEP_INTERVAL)
                except Exception as e:
                    logger.error("Scheduler thread error: %s", e)

        thread = Thread(target=thread_fun, daemon=True)
        thread.start()
    except Exception as e:
        logger.critical("Scheduler thread error: %s", e)
