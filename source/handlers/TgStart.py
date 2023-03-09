from telegram.ext import *
from telegram import *

from source import secret
from source.Users import Operator, Courier
import source.TelegramCommons as TgCommons
from source.handlers.WorkingDeal.Start.TgHandler import WorkingDeal
from source.handlers.SearchDeals.TgHandlers import TemplateHandler


class OperatorMenu:
    NAME = "Основное меню"

    class Buttons:
        CREATE_DEAL = InlineKeyboardButton(text="Создать сделку 🐣", callback_data="create_deal")
        SEARCH_DEAL = TemplateHandler.Buttons.ENTRY
        WORKING_DEAL = WorkingDeal.Buttons.ENTRY
        CURR_CANCEL = InlineKeyboardButton("Вернуться в главное меню 🏠", callback_data="back_general_operator_menu")

    @classmethod
    @TgCommons.pre_handler(access_user=Operator)
    def send(cls, update: Update, context: CallbackContext, user, new=False):
        keyboard = InlineKeyboardMarkup([
            [cls.Buttons.CREATE_DEAL],
            [cls.Buttons.WORKING_DEAL],
            [cls.Buttons.SEARCH_DEAL]
        ])

        if update.message or new:
            update.effective_user.send_message(text=cls.NAME, reply_markup=keyboard)
        elif update.callback_query:
            update.callback_query.edit_message_text(text=cls.NAME, reply_markup=keyboard)
        return ConversationHandler.END

    @classmethod
    def add_handler(cls, ds: Dispatcher):
        WorkingDeal.build_request(cls.Buttons.CURR_CANCEL, cls.send, ds)
        TemplateHandler(cls.Buttons.CURR_CANCEL, ds)
        ds.add_handler(CallbackQueryHandler(cls.send, pattern=cls.Buttons.CURR_CANCEL.callback_data))


class CourierMenu:
    BUTTON_ENTRY = InlineKeyboardButton(text="Доставка",
                                        web_app=WebAppInfo(url=secret.WEB_URL + secret.WEB_COURIER_URL))

    @classmethod
    @TgCommons.pre_handler(access_user=Courier, user_data=False)
    def send(cls, update: Update, context: CallbackContext):
        web_app = cls.BUTTON_ENTRY.web_app
        web_app.url += str(update.effective_user.id) + "?token=" + secret.WEB_TOKENS[0]
        web_button = InlineKeyboardButton(cls.BUTTON_ENTRY.text, web_app=web_app)
        keyboard = InlineKeyboardMarkup([[web_button]])
        update.effective_user.send_message("Для работы со сделками (доставкой) открой приложение по кнопке ниже.",
                                           reply_markup=keyboard)


# Для тестирования
class DevMenu:
    @classmethod
    @TgCommons.pre_handler(access_user=Operator)
    def send(cls, update: Update, context: CallbackContext, user, new=False):
        keyboard = InlineKeyboardMarkup([
            [cls.Buttons.CREATE_DEAL],
            [cls.Buttons.WORKING_DEAL],
            [cls.Buttons.SEARCH_DEAL]
        ])

        if update.message or new:
            update.effective_user.send_message(text=cls.NAME, reply_markup=keyboard)
        elif update.callback_query:
            update.callback_query.edit_message_text(text=cls.NAME, reply_markup=keyboard)
        return ConversationHandler.END