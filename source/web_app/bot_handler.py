import logging
import threading

from telegram import Bot
from telegram.ext import Dispatcher

from source.web_app import bot_socket
from source.handlers.WebCourier.WebHandler import WebHandlerCourier, TaskCourier
from source.event_bot.bot import EventUser
from source.web_app.Tasks import TaskEventUser

logger = logging.getLogger(__name__)


class ApiHandler:
    def __init__(self, dispatcher: Dispatcher, event_bot: Bot):
        self.event_user = EventUser(dispatcher, event_bot)
        self.dispatcher = dispatcher
        self.courier = WebHandlerCourier(dispatcher)
        self.api = bot_socket.ApiConnector()
        threading.Thread(target=self._core, daemon=True).start()

    def _handler(self, task):
        if isinstance(task, TaskEventUser):
            self.event_user.send_message(task)
        elif isinstance(task, TaskCourier):
            task = self.courier.handler(task)
            if task:
                self.api.send(task)

        # if action == "testing":
        #     result.update({"result": "Ok"})
        #     self.api.send(result)
        # if action == "event_user":
        #     pass
        # elif action == "approve":
        #     pass
        # else:
        #     pass

        # res_courier = self.courier.handler(task)
        # if res_courier is not False:
        #     result.update({"result": res_courier})
        #     self.api.send(result)

    def _core(self):
        while True:
            try:
                task = self.api.recv()
                self._handler(task)
            except Exception as err:
                logger.error(f"Проблемное задание от API: {err}", exc_info=True)
