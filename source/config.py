import logging
import datetime

# dirs
DATA_DIR_NAME = '/home/.klumba_bot'
# DATA_DIR_NAME = '/home/.klumba_bot_test'  # test env
ORDERS_DIR_NAME = 'orders_data'

# Telegram bot persistent storage
TG_STORAGE_NAME = 'bot_storage.pickle'
USER_PERSISTENT_KEY = 'USER_DATA'
BOT_REFRESH_TOKEN_PERSISTENT_KEY = 'BITRIX_REFRESH_TOKEN'
BOT_ACCESS_TOKEN_PERSISTENT_KEY = 'BITRIX_ACCESS_TOKEN'

# logging
LOG_FORMAT = '%(asctime)s :: %(levelname)-6s :: %(name)s :: func:%(funcName)s :: line:%(lineno)-5d => %(message)s'
LOG_TG_FORMAT = '<b>Date:</b> %(asctime)s\n<b>Level:</b> %(levelname)s\n<b>Logger:</b> %(name)s\n' \
                '<b>Func:</b> %(funcName)s\n<b>Line:</b> %(lineno)d\n\n<code>%(message)s</code>'
LOG_FILE_SIZE = 5242880  # 5242880 Bytes/5MB

# databases
ORDERS_DATABASE = 'orders.db'
BITRIX_DICTS_DATABASE = 'bitrix_dicts.db'

# times
BITRIX_OAUTH_UPDATE_INTERVAL = 45 * 60  # seconds

# use UTC+3 timezone in all datetime-related features
TIMEZONE = datetime.timezone(datetime.timedelta(hours=3))


HTTP_SERVER_PORT = 8082
HTTP_SERVER_ADDRESS = '0.0.0.0'
