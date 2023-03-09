import time

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ParseMode, ReplyKeyboardRemove, BotCommand
from telegram.ext import CallbackContext, ConversationHandler, Dispatcher, CommandHandler, MessageHandler, Filters

import source.config as cfg
import source.bitrix.BitrixWorker as BW
import source.utils.Utils as Utils
from source import Users
from source.handlers import TgStart

import logging

logger = logging.getLogger(__name__)


class AuthHandler:
    """
    Обработчик авторизации.
    """

    class Commands:
        START = BotCommand('start', 'Старт или возврат в меню')
        LOGOUT = BotCommand('logout', 'Сменить пользователя (выход из системы)')

        ALL_LIST = [START, LOGOUT]

    # PARAMETERS AUTH
    LIMIT_TIME_AUTH = 5

    # STATE Dialog
    STATE_LOGIN_REQUESTED = 1

    # TEXT
    TEXT_SEND_CONTACT_BUTTON = 'ВОЙТИ ПО НОМЕРУ ТЕЛЕФОНА'

    TEXT_REQUEST_LOGIN_MESSAGE = f"Добро пожаловать в *Клумба: общий интерфейс*\\!\n" \
                                 f"Нажмите *' {TEXT_SEND_CONTACT_BUTTON} '* для входа\\.\n" \
                                 f"КНОПКА НАХОДИТСЯ ПОД ИЛИ НАД КЛАВИАТУРОЙ\\. \n" \
                                 f"ЕСЛИ ОНА СКРЫТА \\- НУЖНО НАЖАТЬ НА КНОПКУ " \
                                 f"\U0001F39B РЯДОМ С КЛАВИАТУРОЙ\\."

    TEXT_AUTHORIZATION_SUCCESSFUL = 'Авторизация пройдена\\!\n' \
                                    'Теперь вы можете использовать возможности бота\\.'

    TEXT_AUTHORIZATION_FAILED = '❗ Авторизация не пройдена\\.\n' \
                                'Проверьте настройки мобильного номера в ' \
                                '[профиле битрикс](https://klumba.bitrix24.ru/company/personal/user/) и ' \
                                'совпадает ли он с номером в Вашей учетной записи telegram\\. ' \
                                '\nПосле проверки попробуйте снова\\.\n\n'
    TEXT_LIMIT_TIME_AUTH = f"Не так часто\\! Авторизация возможна не чаще одного раза в {LIMIT_TIME_AUTH} секунд\\."

    @classmethod
    def send_authorized_message(cls, update: Update, text: str):
        send_message = update.effective_user.send_message
        keyboard = ReplyKeyboardMarkup([[KeyboardButton(text=cls.TEXT_SEND_CONTACT_BUTTON, request_contact=True)]],
                                       one_time_keyboard=True)
        send_message(text=text, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=keyboard)

    @classmethod
    def _restart(cls, update, context: CallbackContext):
        user: Users.BaseUser = context.user_data.get(cfg.USER_PERSISTENT_KEY)
        # has user been already cached?

        if user:
            user.restart(update, context)
            return ConversationHandler.END
        else:
            cls.send_authorized_message(update, cls.TEXT_REQUEST_LOGIN_MESSAGE)
            return cls.STATE_LOGIN_REQUESTED

    @classmethod
    def _handle_login(cls, update: Update, context: CallbackContext):
        contact = update.message.contact

        # Контроль спама авторизации
        key_try_last_time = "try_last_time"
        curr_time = time.time()
        last_try = context.user_data.pop(key_try_last_time, None)

        if last_try and curr_time - last_try < cls.LIMIT_TIME_AUTH:
            cls.send_authorized_message(update, cls.TEXT_LIMIT_TIME_AUTH)
            context.user_data[key_try_last_time] = last_try
            logger.info(f"Spam authorization user: {contact.phone_number}")
            return
        elif last_try:
            BW.BitrixUsers.update_user_by_phone(contact.phone_number)

        # check that sent contact is user's own contact
        if not contact or contact.user_id != update.effective_user.id:
            cls.send_authorized_message(update, cls.TEXT_AUTHORIZATION_FAILED)
            context.user_data[key_try_last_time] = curr_time
            return

        phone_number = Utils.prepare_phone_number(contact.phone_number)

        # Есть ли пользователь в Битрикс?
        user_bitrix = BW.BitrixUsers.user_by_phone(phone_number)

        if contact.user_id == update.effective_user.id and user_bitrix:
            logger.info(f"Good authorization user [login: {update.effective_user.username}], [phone: {phone_number}]")
            role = user_bitrix[BW.BitrixUsers.ConstFields.ROLE]

            if role == BW.BitrixUsers.ConstRoleId.COURIER_ID:
                authorized_user = Users.Courier.build(user_bitrix, update.effective_user, TgStart.CourierMenu.send)
            elif role == BW.BitrixUsers.ConstRoleId.FLORIST_ID:
                authorized_user = Users.Florist.build(user_bitrix, update.effective_user, TgStart.OperatorMenu.send)
            else:
                authorized_user = Users.Operator.build(user_bitrix, update.effective_user, TgStart.OperatorMenu.send)
            logger.debug(f"Create user [role: {authorized_user.__class__}], [data: {authorized_user.__dict__}]")
            update.effective_user.send_message(text=cls.TEXT_AUTHORIZATION_SUCCESSFUL, parse_mode=ParseMode.MARKDOWN_V2,
                                               reply_markup=ReplyKeyboardRemove())

            context.user_data[cfg.USER_PERSISTENT_KEY] = authorized_user

            cls._restart(update, context)
            return ConversationHandler.END
        else:
            logger.info(f"Bad authorization user [login: {update.effective_user.username}], [phone: {phone_number}]")
            context.user_data[key_try_last_time] = curr_time
            cls.send_authorized_message(update, cls.TEXT_AUTHORIZATION_FAILED)
            return cls.STATE_LOGIN_REQUESTED

    @classmethod
    def _logout(cls, update: Update, context: CallbackContext):
        if cfg.USER_PERSISTENT_KEY in context.user_data:
            del context.user_data[cfg.USER_PERSISTENT_KEY]
        return cls._restart(update, context)

    @classmethod
    def add_handler(cls, dispatcher: Dispatcher):
        handlers = [CommandHandler(cls.Commands.START.command, cls._restart, Filters.chat_type.private),
                    CommandHandler(cls.Commands.LOGOUT.command, cls._logout, Filters.chat_type.private)]
        dispatcher.add_handler(ConversationHandler(entry_points=handlers,
                                                   states={cls.STATE_LOGIN_REQUESTED: [
                                                       MessageHandler(Filters.contact, cls._handle_login)]},
                                                   fallbacks=handlers))

