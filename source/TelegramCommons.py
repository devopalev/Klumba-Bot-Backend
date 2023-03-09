import logging
import threading
import time
from functools import wraps

from telegram.ext import CallbackContext
from telegram import Update

import source.config as cfg
from source import Users


logger = logging.getLogger(__name__)


# decorator for PTB callbacks (update, context: CallbackContext)
# - exposes user variable for fast cached user access from context
# - changes user state to callback result
def pre_handler(access_user=Users.BaseUser, user_data=True):
    """
    :param access_user: class or List[class]
    :param user_data: user_data arg
    :return: func()
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            update = None
            user = None
            for arg in args:
                if isinstance(arg, Update):
                    update = arg
                if isinstance(arg, CallbackContext):
                    user = arg.user_data.get(cfg.USER_PERSISTENT_KEY)

            logger.debug(f"Use (update_id:{update.update_id}) func {func.__name__}: user {user}, update: {update}")

            if access_user is False or isinstance(user, access_user) or \
                    (isinstance(access_user, list) and any([isinstance(user, el) for el in access_user])):
                if user_data:
                    result = func(*args, user, **kwargs)
                else:
                    result = func(*args, **kwargs)
            elif user:
                if update.callback_query:
                    update.callback_query.answer("У вас нет прав для этого действия!")
                return update.effective_user.send_message("У вас нет прав для этого действия!")
            else:
                if update.callback_query:
                    update.callback_query.answer("Вы не авторизированы!")
                try:
                    return update.effective_user.send_message("Вы не авторизированы!")
                except Exception as err:
                    logger.warning(f"Не удалось отправить сообщение о неавторизированном пользователе: {err}")

            if update.callback_query:
                update.callback_query.answer()
            logger.debug(f"Result (update_id:{update.update_id}) func {func.__name__}: {result}")
            return result
        return wrapper
    return decorator


def send_temp_message(update: Update, text, timer=5, th=False):
    if not th:
        threading.Thread(target=send_temp_message, args=(update, text, timer, True)).start()
    else:
        if update.callback_query:
            message = update.callback_query.from_user.send_message(text)
        else:
            message = update.effective_user.send_message(text)
        time.sleep(timer)
        message.delete()


@pre_handler()
def global_fallback(update: Update, context: CallbackContext, user):
    if update.callback_query:
        update.callback_query.answer("Не знаю что делать с этой кнопкой, попробуй снова.")
        user.restart(update, context)
    elif update.message:
        update.message.delete()
        send_temp_message(update, "Не знаю зачем ты мне это написал.")
    logger.warning(f"Неизвестное действие пользователя: {update}")