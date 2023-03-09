from functools import wraps, partial

from telegram.ext import CallbackContext
from telegram import ParseMode, InlineKeyboardButton, InlineKeyboardMarkup, User as TelegramUser, \
    Message as TelegramMessage, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, Chat as TelegramChat

import source.TextSnippets as GlobalTxt
import source.config as cfg
from source.State import State
from source.BaseUser import BaseUser
import source.StorageWorker as StorageWorker

CANCEL_BUTTON = InlineKeyboardButton(text=GlobalTxt.CANCEL_BUTTON_TEXT,
                                     callback_data=GlobalTxt.CANCEL_BUTTON_CB_DATA)


# decorator for PTB callbacks (update, context: CallbackContext)
# - exposes user variable for fast cached user access from context
# - changes user state to callback result
def tg_callback(func=None, change_user_state=True):
    if callable(func):
        @wraps(func)
        def wrapper(update, context):
            user = context.user_data.get(cfg.USER_PERSISTENT_KEY)

            if update.callback_query:
                update.callback_query.answer()

            state = func(update, context, user)

            if user and change_user_state:
                user.state = state

            return state

        return wrapper
    else:
        return partial(tg_callback, change_user_state=change_user_state)


def send_mdv2_reply_keyboard(tg_user: TelegramUser, msg_text, reply_keyboard, one_time_keyboard):
    tg_user.send_message(text=msg_text, parse_mode=ParseMode.MARKDOWN_V2,
                         reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=one_time_keyboard))


def send_reply_keyboard_remove(tg_user: TelegramUser, msg_text):
    tg_user.send_message(text=msg_text, parse_mode=ParseMode.MARKDOWN_V2,
                         reply_markup=ReplyKeyboardRemove())


# send message to user with MarkdownV2 formatting and keyboard with cancel/menu button
def send_mdv2(tg_user: TelegramUser, msg_text, inline_keyboard=None):
    # using green mark
    msg_text = '\U0001F7E2 \n\n' + msg_text

    if inline_keyboard:
        inline_keyboard.append([CANCEL_BUTTON])
    else:
        inline_keyboard = [[CANCEL_BUTTON]]

    tg_user.send_message(text=msg_text, parse_mode=ParseMode.MARKDOWN_V2,
                         reply_markup=InlineKeyboardMarkup(inline_keyboard), disable_web_page_preview=True)


# send message to specific char with MarkdownV2 formatting and keyboard
def send_mdv2_chat(chat: TelegramChat, msg_text, inline_keyboard=None, reply_id=None, need_cancel=False):
    if need_cancel:
        if inline_keyboard:
            inline_keyboard.append([CANCEL_BUTTON])
        else:
            inline_keyboard = [[CANCEL_BUTTON]]

    chat.send_message(text=msg_text, parse_mode=ParseMode.MARKDOWN_V2,
                      reply_markup=InlineKeyboardMarkup(inline_keyboard) if inline_keyboard else None,
                      disable_web_page_preview=True,
                      reply_to_message_id=reply_id)


# send message to user with MarkdownV2 formatting and keyboard with cancel/menu button
def edit_mdv2(tg_msg: TelegramMessage, msg_text, keyboard=None, need_cancel=True):
    cancel_button = InlineKeyboardButton(text=GlobalTxt.CANCEL_BUTTON_TEXT,
                                         callback_data=GlobalTxt.CANCEL_BUTTON_CB_DATA)
    if need_cancel:
        if keyboard:
            keyboard.append([cancel_button])
        else:
            keyboard = [[cancel_button]]

    tg_msg.edit_text(text=msg_text, parse_mode=ParseMode.MARKDOWN_V2,
                     reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None,
                     disable_web_page_preview=True)


def send_media_group(tg_user: TelegramUser, media_list):
    tg_user.send_media_group(media_list)


@tg_callback
def restart(update, context: CallbackContext, user):
    auth_button = KeyboardButton(text=GlobalTxt.SEND_CONTACT_BUTTON_TEXT, request_contact=True)

    # has user been already cached?
    if user:
        if StorageWorker.check_authorization(user) and not type(user) is BaseUser:
            return user.restart(update, context)
        else:  # authorization isn't valid now
            send_mdv2_reply_keyboard(update.effective_user, GlobalTxt.AUTHORIZATION_FAILED, [[auth_button]], True)
            return State.LOGIN_REQUESTED

    else:
        send_mdv2_reply_keyboard(update.effective_user, GlobalTxt.REQUEST_LOGIN_MESSAGE, [[auth_button]], True)
        context.user_data[cfg.USER_PERSISTENT_KEY] = BaseUser()
        return State.LOGIN_REQUESTED


@tg_callback
def logout(update, context: CallbackContext, user):
    if cfg.USER_PERSISTENT_KEY in context.user_data:
        del context.user_data[cfg.USER_PERSISTENT_KEY]

    return restart(update, context)


@tg_callback
def global_fallback(update, context: CallbackContext, user):
    send_mdv2(update.effective_user, GlobalTxt.UNKNOWN_COMMAND)
    return user.state if user else None  # don't change actual conversation state
