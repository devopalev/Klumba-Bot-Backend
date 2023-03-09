import logging
import pickle
import os
import threading

from telegram.ext import Updater, Dispatcher
from telegram import Update, Bot, ParseMode

from source import creds
from source.BaseUser import BaseUser
from source.config import USER_PERSISTENT_KEY

logger = logging.getLogger(__name__)


bot = None


# class EventUser:
#     def __init__(self, main_dispatcher: Dispatcher, bot_event: Bot):
#         self.main_dispatcher = main_dispatcher
#         self.bot_event = bot_event
#
#     def send_message(self, bitrix_id, text):
#         for _, user_data in self.main_dispatcher.user_data.items():
#             user: BaseUser = user_data.get(USER_PERSISTENT_KEY)
#             if user.bitrix_user_id == bitrix_id:
#                 try:
#                     self.bot_event.send_message(user.tg_user.id, text, parse_mode=ParseMode.HTML)
#                 except Exception as err:
#                     logger.warning(f"Не удалось отправить уведомление пользователю ({user.tg_user.full_name}): {err}")
#         logger.warning(f"Пользователь (b24 id {task.bitrix_id}) не авторизирован")


def run(updater):
    updater.start_polling()


def build():
    updater = Updater(creds.TG_BOT_EVENT_TOKEN, workers=2)
    threading.Thread(name='bot_event', daemon=True, target=run, args=(updater,)).start()
    global bot
    bot = updater.bot
