import logging
import threading

import source.secret as secret
from telegram import Bot, ParseMode
from telegram.ext import Dispatcher, Updater

from source.config import USER_PERSISTENT_KEY
from source.Users import BaseUser
from source.web_app.Tasks import TaskEventUser

logger = logging.getLogger(__name__)


class EventUser:
    def __init__(self, main_dispatcher: Dispatcher, bot_event: Bot):
        self.main_dispatcher = main_dispatcher
        self.bot_event = bot_event

    def send_message(self, task: TaskEventUser):
        for _, user_data in self.main_dispatcher.user_data.items():
            user: BaseUser = user_data.get(USER_PERSISTENT_KEY)
            if user.bitrix_user_id == task.bitrix_id:
                try:
                    self.bot_event.send_message(user.tg_user.id, task.text, parse_mode=ParseMode.HTML)
                    return task
                except Exception as err:
                    logger.warning(f"Не удалось отправить уведомление пользователю ({user.tg_user.full_name}): {err}")
        logger.warning(f"Пользователь (b24 id {task.bitrix_id}) не авторизирован")


def run(updater):
    updater.start_polling()


def build():
    updater = Updater(secret.TG_BOT_EVENT_TOKEN, workers=2)
    threading.Thread(name='bot_event', daemon=True, target=run, args=(updater,)).start()
    return updater
