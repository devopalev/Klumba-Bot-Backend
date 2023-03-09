from typing import List
import logging
import pathlib
import datetime
from undecorated import undecorated

from telegram.ext import MessageHandler, Filters, CallbackContext, \
    ConversationHandler, CommandHandler, CallbackQueryHandler

from telegram import PhotoSize, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode

from source.User import Operator
from source.State import State
import source.Commands as Cmd
import source.config as cfg
import source.TelegramCommons as TgCommons
import source.TextSnippets as GlobalTxt
import source.BitrixWorker as BW
import source.utils.TelegramCalendar as TgCalendar
import source.cmd_handlers.SetFlorist.TgHandlers as FloristHandlers

from . import TextSnippets as Txt
from .Photo import Photo as Photo
from . import BitrixHandlers as BH

logger = logging.getLogger(__name__)


@TgCommons.tg_callback
def request_deal_number(update, context: CallbackContext, user: Operator):
    TgCommons.send_mdv2(update.effective_user, Txt.ASK_FOR_DEAL_NUMBER)
    return State.PROCESS_SETTING_DEAL_NUMBER


@TgCommons.tg_callback
def set_deal_number(update, context: CallbackContext, user: Operator):
    deal_id = update.message.text
    result = BH.set_deal_number(user, deal_id)

    if result == BW.BW_NO_SUCH_DEAL:
        TgCommons.send_mdv2(update.effective_user, GlobalTxt.NO_SUCH_DEAL.format(deal_id))
        return None

    if result == BW.BW_WRONG_STAGE:
        TgCommons.send_mdv2(update.effective_user, Txt.WRONG_DEAL_STAGE)
        return None

    keyboard = [[InlineKeyboardButton(text=Txt.RESERVE_YES_TXT, callback_data=Txt.RESERVE_YES_KEY)],
                [InlineKeyboardButton(text=Txt.SWITCH_STAGE_WAITING_FOR_SUPPLY_TXT,
                                      callback_data=Txt.SWITCH_STAGE_WAITING_FOR_SUPPLY_KEY)],
                [InlineKeyboardButton(text=Txt.SWITCH_STAGE_PROCESSED_TXT,
                                      callback_data=Txt.SWITCH_STAGE_PROCESSED_KEY)]
                ]

    TgCommons.send_mdv2(update.effective_user, Txt.WILL_YOU_RESERVE.format(deal_id), keyboard)
    return State.PROCESS_WILL_YOU_RESERVE


@TgCommons.tg_callback
def reserve_choice(update, context: CallbackContext, user: Operator):
    action = update.callback_query.data

    if action == Txt.RESERVE_YES_KEY:
        TgCommons.send_mdv2(update.effective_user, Txt.ASK_FOR_PHOTO_TEXT)
        return State.PROCESS_LOADING_PHOTOS
    elif action == Txt.SWITCH_STAGE_WAITING_FOR_SUPPLY_KEY:
        calendar_markup = TgCalendar.create_calendar()
        TgCommons.send_mdv2(update.effective_user, Txt.CALENDAR_DESCRIPTION, calendar_markup)
        return State.PROCESS_SUPPLY_CALENDAR
    elif action == Txt.SWITCH_STAGE_PROCESSED_KEY:
        keyboard = [[InlineKeyboardButton(text=Txt.BITTER_TWIX_APPROVE_TXT, callback_data=Txt.BITTER_TWIX_APPROVE_KEY)],
                    [InlineKeyboardButton(text=Txt.BITTER_TWIX_SET_FLORIST_TXT,
                                          callback_data=Txt.BITTER_TWIX_SET_FLORIST_KEY)]]
        TgCommons.send_mdv2(update.effective_user, Txt.BITTER_TWIX_WARNING, keyboard)
        return State.PROCESS_APPROVE_RESERVE_NOT_NEEDED


@TgCommons.tg_callback
def append_photo(update, context: CallbackContext, user: Operator):
    photos: List[PhotoSize] = update.message.photo

    photo_big = photos[-1]

    unique_id_big = photo_big.file_unique_id
    photo_content_big = photo_big.get_file().download_as_bytearray()
    file_extension_big = photo_big.get_file().file_path.split('.')[-1]

    if photo_content_big:
        user.reserve.add_deal_photo(Photo(unique_id_big + '_B.' + file_extension_big,
                                          photo_content_big))

        keyboard = [[InlineKeyboardButton(text=Txt.FINISH_PHOTO_LOADING_TXT,
                                          callback_data=Txt.FINISH_PHOTO_LOADING_KEY)]]
        TgCommons.send_mdv2(update.effective_user, Txt.PHOTO_LOADED_TEXT, keyboard)

    return None


@TgCommons.tg_callback
def request_description(update, context: CallbackContext, user: Operator):
    if not user.reserve.photos:
        TgCommons.send_mdv2(update.effective_user, Txt.NO_PHOTOS_TEXT)
        return None

    TgCommons.send_mdv2(update.effective_user, Txt.REQUEST_DESCRIPTION)
    return State.PROCESS_DESCRIPTION


@TgCommons.tg_callback
def set_description(update, context: CallbackContext, user: Operator):
    user.deal_data.reserve_desc = update.message.text
    BH.update_deal_reserve(user)

    TgCommons.send_mdv2(update.effective_user, GlobalTxt.DEAL_UPDATED.format(user.deal_data.deal_id))
    return TgCommons.restart(update, context)


@TgCommons.tg_callback
def no_reserve_approve(update, context: CallbackContext, user: Operator):
    photo_stub_name = 'no_reserve_needed.png'
    photo_stub_path = pathlib.Path(__file__).parent.resolve() / 'data' / photo_stub_name

    with open(photo_stub_path, 'rb') as f:
        stub_bytes = f.read()
        user.reserve.add_deal_photo(Photo(photo_stub_name,
                                          stub_bytes))

    BH.update_deal_no_reserve(user)

    TgCommons.send_mdv2(update.effective_user, GlobalTxt.DEAL_UPDATED.format(user.deal_data.deal_id))
    return TgCommons.restart(update, context)


@TgCommons.tg_callback
def set_florist(update, context: CallbackContext, user: Operator):
    update.effective_message.text = user.deal_data.deal_id  # set deal id as message to handle in SetFlorist
    # using unwrapped function to answer CBQ only once
    return FloristHandlers.set_deal_number.__wrapped__(update, context, user)


@TgCommons.tg_callback
def calendar_selection(update, context: CallbackContext, user: Operator):
    query = update.callback_query

    result, dt = TgCalendar.process_calendar_selection(update, context)

    if result:
        if dt < datetime.datetime.now(tz=cfg.TIMEZONE):
            query.answer(text=Txt.DATE_TOO_EARLY)
            context.bot.edit_message_text(text=query.message.text,
                                          chat_id=query.message.chat_id,
                                          message_id=query.message.message_id,
                                          reply_markup=InlineKeyboardMarkup(TgCalendar.create_calendar()))

            return None

        user.deal_data.supply_datetime = dt.isoformat()

        BH.update_deal_waiting_for_supply(user)
        TgCommons.send_mdv2(update.effective_user, GlobalTxt.DEAL_UPDATED.format(user.deal_data.deal_id))
        TgCommons.restart(update, context)


cv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(callback=request_deal_number, pattern=GlobalTxt.MENU_DEAL_PROCESS_BUTTON_CB)],
    states={
        State.PROCESS_SETTING_DEAL_NUMBER: [MessageHandler(Filters.regex(GlobalTxt.BITRIX_DEAL_NUMBER_PATTERN),
                                                           set_deal_number)],
        State.PROCESS_WILL_YOU_RESERVE: [CallbackQueryHandler(callback=reserve_choice,
                                                              pattern=Txt.RESERVE_CB_PATTERN)],
        State.PROCESS_LOADING_PHOTOS: [CallbackQueryHandler(callback=request_description,
                                                            pattern=Txt.FINISH_PHOTO_LOADING_KEY),
                                       MessageHandler(Filters.photo, append_photo)],
        State.PROCESS_DESCRIPTION: [MessageHandler(Filters.text, set_description)],
        State.PROCESS_APPROVE_RESERVE_NOT_NEEDED: [CallbackQueryHandler(callback=no_reserve_approve,
                                                                        pattern=Txt.BITTER_TWIX_APPROVE_KEY),
                                                   CallbackQueryHandler(callback=set_florist,
                                                                        pattern=Txt.BITTER_TWIX_SET_FLORIST_KEY)
                                                   ],
        State.PROCESS_SUPPLY_CALENDAR: [CallbackQueryHandler(callback=calendar_selection,
                                                             pattern=TgCalendar.PATTERN)],
        **FloristHandlers.cv_handler.states
    },
    fallbacks=[CommandHandler([Cmd.START, Cmd.CANCEL], TgCommons.restart),
               CommandHandler([Cmd.LOGOUT], TgCommons.logout),
               CallbackQueryHandler(callback=TgCommons.restart, pattern=GlobalTxt.CANCEL_BUTTON_CB_DATA),
               MessageHandler(Filters.all, TgCommons.global_fallback),
               CallbackQueryHandler(callback=TgCommons.global_fallback, pattern=GlobalTxt.ANY_STRING_PATTERN)],
    map_to_parent={
        State.IN_OPERATOR_MENU: State.IN_OPERATOR_MENU,
        State.LOGIN_REQUESTED: State.LOGIN_REQUESTED
    }
)
