import logging
import os

from telegram import Update
from telegram.ext import CallbackContext, Dispatcher, MessageHandler, Filters, PicklePersistence, Updater, \
    CallbackQueryHandler

from source.web_app.bot_handler import ApiHandler
import source.secret as creds
import source.config as cfg
import source.bitrix.BitrixWorker as BW


import source.TelegramCommons as TgCommons

import source.TelegramAuthorization as Authorization
from source.handlers.TgStart import OperatorMenu
from source.event_bot import bot as event_bot

logger = logging.getLogger(__name__)
JOB_QUEUE = None


def error_handler(update, context: CallbackContext):
    try:
        logger.error(msg="Exception while handling Telegram update:", exc_info=context.error)

        # don't confuse user with particular error data
        # if update:
        #     if update.effective_chat.type == Chat.PRIVATE:
        #         # don't confuse user with particular errors data
        #         TgCommons.send_mdv2(update.effective_user, GlobalTxt.UNKNOWN_ERROR)
        #     elif update.effective_chat.type in (Chat.GROUP, Chat.SUPERGROUP):
        #         TgCommons.send_mdv2_chat(update.effective_chat, GlobalTxt.UNKNOWN_ERROR)
    except Exception as e:
        logger.error(msg="Exception while handling lower-level exception:", exc_info=e)


def add_handlers(dispatcher: Dispatcher):
    """
    Handlers:
        - Authorization
        - TgStart
        - WorkingDeal:
            - SetFlorist
            - Reverse
            - Equip

    """
    Authorization.AuthHandler.add_handler(dispatcher)
    OperatorMenu.add_handler(dispatcher)

    # other
    dispatcher.add_handler(MessageHandler(Filters.all, callback=TgCommons.global_fallback))
    dispatcher.add_handler(CallbackQueryHandler(TgCommons.global_fallback))


def bitrix_oauth_update_job(context: CallbackContext):
    with BW.BitrixOAUTH.OAUTH_LOCK:
        refresh_token = context.bot_data[cfg.BOT_REFRESH_TOKEN_PERSISTENT_KEY]
        a_token, r_token = BW.BitrixOAUTH.refresh_oauth(refresh_token)

        if a_token:
            context.bot_data[cfg.BOT_ACCESS_TOKEN_PERSISTENT_KEY] = a_token
            context.bot_data[cfg.BOT_REFRESH_TOKEN_PERSISTENT_KEY] = r_token


# entry point
def run():
    os.makedirs(cfg.DATA_DIR_NAME, exist_ok=True)
    storage = PicklePersistence(filename=os.path.join(os.getcwd(), os.path.abspath('bot_storage.pickle')))
    # storage = PicklePersistence(filename=os.path.join(cfg.DATA_DIR_NAME, cfg.TG_STORAGE_NAME))
    updater = Updater(creds.TG_BOT_TOKEN, workers=10)#, persistence=storage)
    dispatcher: Dispatcher = updater.dispatcher
    # updater.logger.setLevel(logging.INFO)

    # handle Bitrix OAuth keys update here in job queue
    bot_data = dispatcher.bot_data

    if cfg.BOT_ACCESS_TOKEN_PERSISTENT_KEY not in bot_data:
        bot_data[cfg.BOT_ACCESS_TOKEN_PERSISTENT_KEY] = creds.BITRIX_APP_ACCESS_TOKEN
        bot_data[cfg.BOT_REFRESH_TOKEN_PERSISTENT_KEY] = creds.BITRIX_APP_REFRESH_TOKEN

    jq = updater.job_queue
    global JOB_QUEUE
    JOB_QUEUE = jq

    # refresh oauth
    jq.run_repeating(bitrix_oauth_update_job, interval=cfg.BITRIX_OAUTH_UPDATE_INTERVAL, first=1)

    # start festive statistics jobs
    # FestiveStats.jq_add_festive_stats(jq)

    # cv_handler = main_handler()
    #
    # dispatcher.add_handler(FestiveApprovement.FESTIVE_CV_HANDLER)
    # dispatcher.add_handler(FestiveApprovement.FESTIVE_REAPPROVE_HANDLER)
    # dispatcher.add_handler(cv_handler)
    # for fb in cv_handler.fallbacks:
    #     dispatcher.add_handler(fb)

    updater.bot.set_my_commands(Authorization.AuthHandler.Commands.ALL_LIST)
    add_handlers(dispatcher)
    dispatcher.add_error_handler(error_handler)

    updater_event_bot = event_bot.build()

    # Запуск обработчика api (в отдельном потоке)
    ApiHandler(dispatcher, updater_event_bot.bot)

    updater.start_polling(allowed_updates=Update.ALL_TYPES)
    updater.idle()
