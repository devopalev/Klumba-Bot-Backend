from telegram.ext import CallbackContext
from telegram import InlineKeyboardButton

import source.TextSnippets as GlobalTxt
import source.TelegramCommons as TgCommons
import source.cmd_handlers.Courier.TgHandlers as CourierHandlers
from source.State import State


@TgCommons.tg_callback
def restart_operator(update, context: CallbackContext, user):
    message = GlobalTxt.MENU_TEXT
    keyboard = [
        [InlineKeyboardButton(text=GlobalTxt.MENU_DEAL_PROCESS_BUTTON_TEXT,
                              callback_data=GlobalTxt.MENU_DEAL_PROCESS_BUTTON_CB)],
        [InlineKeyboardButton(text=GlobalTxt.MENU_DEAL_SET_FLORIST_BUTTON_TEXT,
                              callback_data=GlobalTxt.MENU_DEAL_SET_FLORIST_BUTTON_CB)],
        [InlineKeyboardButton(text=GlobalTxt.MENU_DEAL_EQUIP_BUTTON_TEXT,
                              callback_data=GlobalTxt.MENU_DEAL_EQUIP_BUTTON_CB)],
        [InlineKeyboardButton(text=GlobalTxt.MENU_DEAL_SEND_BUTTON_TEXT,
                              callback_data=GlobalTxt.MENU_DEAL_SEND_BUTTON_CB)],
        [InlineKeyboardButton(text=GlobalTxt.MENU_DEAL_COURIER_BUTTON_TEXT,
                              callback_data=GlobalTxt.MENU_DEAL_COURIER_BUTTON_CB)],
        [InlineKeyboardButton(text=GlobalTxt.MENU_DEAL_FLORIST_ORDERS_BUTTON_TEXT,
                              callback_data=GlobalTxt.MENU_DEAL_FLORIST_ORDERS_BUTTON_CB)]
    ]

    TgCommons.send_mdv2(update.effective_user, message, keyboard)
    return State.IN_OPERATOR_MENU


@TgCommons.tg_callback
def restart_courier(update, context: CallbackContext, user):
    return CourierHandlers.delivers_today(update, context)
