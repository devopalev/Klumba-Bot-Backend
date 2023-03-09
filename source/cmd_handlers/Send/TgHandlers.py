import logging
import math

from telegram.ext import MessageHandler, Filters, CallbackContext, \
    ConversationHandler, CommandHandler, CallbackQueryHandler

from telegram import InlineKeyboardButton

from source.User import Operator
from source.State import State
import source.Commands as Cmd
import source.utils.Utils as Utils
import source.TextSnippets as GlobalTxt
import source.BitrixWorker as BW
import source.TelegramCommons as TgCommons

import source.cmd_handlers.Send.UserData as UserData
import source.cmd_handlers.Send.TextSnippets as Txt
import source.cmd_handlers.Send.BitrixHandlers as BH

logger = logging.getLogger(__name__)


@TgCommons.tg_callback
def request_deal_number(update, context: CallbackContext, user):
    TgCommons.send_mdv2(update.effective_user, Txt.ASK_FOR_DEAL_NUMBER)
    return State.SEND_SET_DEAL_NUMBER


def render_order_data(update, context: CallbackContext, user: Operator):
    terminal_elt = Txt.DEAL_TERMINAL_ELT if user.deal_data.terminal_needed else ''
    change_elt = Txt.DEAL_CHANGE_ELT.format(user.deal_data.change_sum) if user.deal_data.change_sum else ''

    courier = Utils.prepare_external_field(BW.COURIERS, user.deal_data.courier_id, BW.COURIERS_LOCK)

    return Txt.DEAL_TEMPLATE.format(user.deal_data.deal_id, courier, user.deal_data.payment_type,
                                    terminal_elt, change_elt, user.deal_data.to_pay)


def send_couriers_header(update, context, user):
    order_preview = render_order_data(update, context, user)
    keyboard = [[InlineKeyboardButton(text=Txt.SHOW_ALL_COURIERS_BUTTON_TEXT,
                                      callback_data=Txt.SHOW_ALL_COURIERS_BUTTON_CB)]]
    TgCommons.send_mdv2(update.effective_user, order_preview + Txt.CHOOSE_COURIER_HEADER, keyboard)


@TgCommons.tg_callback
def set_deal_number(update, context: CallbackContext, user: Operator):
    deal_id = update.message.text

    result = BH.set_deal_number(user, deal_id)

    if result == BW.BW_NO_SUCH_DEAL:
        TgCommons.send_mdv2(update.effective_user, GlobalTxt.NO_SUCH_DEAL.format(deal_id))
        return None
    elif result == BW.BW_WRONG_STAGE:
        TgCommons.send_mdv2(update.effective_user, Txt.WRONG_DEAL_STAGE)
        return None
    elif result == BH.BH_ALREADY_HAS_COURIER:
        courier = Utils.prepare_external_field(BW.COURIERS, user.deal_data.courier_id, BW.COURIERS_LOCK)

        keyboard = [[InlineKeyboardButton(text=Txt.CHANGE_COURIER_BUTTON_TEXT,
                                          callback_data=Txt.CHANGE_COURIER_BUTTON_CB)],
                    [InlineKeyboardButton(text=Txt.LEAVE_COURIER_BUTTON_TEXT.format(courier),
                                          callback_data=Txt.LEAVE_COURIER_BUTTON_CB)]]
        TgCommons.send_mdv2(update.effective_user, Txt.COURIER_ALREADY_SET_HEADER.format(courier.upper(), deal_id),
                            keyboard)
        return State.SEND_CHANGE_COURIER

    send_couriers_header(update, context, user)
    return State.SEND_SET_COURIER


@TgCommons.tg_callback
def change_courier(update, context: CallbackContext, user: Operator):
    send_couriers_header(update, context, user)
    return State.SEND_SET_COURIER


@TgCommons.tg_callback
def leave_courier(update, context: CallbackContext, user: Operator):
    courier = Utils.prepare_external_field(BW.COURIERS, user.deal_data.courier_id, BW.COURIERS_LOCK)
    message = Txt.DEAL_UPDATED.format(user.deal_data.deal_id, courier)

    BH.send_deal(user)

    TgCommons.send_mdv2(update.effective_user, message)
    return TgCommons.restart(update, context)


def render_cur_page(update, context, user: Operator, edit_message=False):
    couriers_num = len(user.send.couriers)
    page_number = user.send.page_number
    user.send.total_pages = math.ceil(couriers_num / UserData.COURIERS_PER_PAGE)

    courier_surname_starts_with_elt = Txt.COURIERS_LIST_SURNAME_STARTS_ELT \
        .format(user.send.courier_surname_starts_with) if user.send.courier_surname_starts_with else ''

    message = Txt.COURIERS_LIST_HEADER.format(courier_surname_starts_with_elt)

    if user.send.total_pages > 1:
        message += Txt.COURIERS_PAGE_HEADER.format(page_number + 1, user.send.total_pages)

    couriers_tuples = list(user.send.couriers.items())
    page = couriers_tuples[page_number * UserData.COURIERS_PER_PAGE:
                           (page_number + 1) * UserData.COURIERS_PER_PAGE]

    keyboard = []

    for bitrix_id, p_data in page:
        keyboard.append([InlineKeyboardButton(p_data, callback_data=bitrix_id)])

    if page_number > 0:
        keyboard.append([InlineKeyboardButton(Txt.PREV_PAGE_TEXT, callback_data=Txt.PREV_PAGE_CB)])

    if page_number < user.send.total_pages - 1:
        if page_number > 0:  # if prev page button has been added
            keyboard[-1].append(InlineKeyboardButton(Txt.NEXT_PAGE_TEXT, callback_data=Txt.NEXT_PAGE_CB))
        else:
            keyboard.append([InlineKeyboardButton(Txt.NEXT_PAGE_TEXT, callback_data=Txt.NEXT_PAGE_CB)])

    if edit_message:
        TgCommons.edit_mdv2(update.effective_message, message, keyboard)
    else:
        TgCommons.send_mdv2(update.effective_user, message, keyboard)


def cache_couriers(user: Operator, surname_starts_with=None):
    with BW.COURIERS_LOCK:
        result = {}

        if surname_starts_with:
            for bitrix_id, p_data in BW.COURIERS.items():
                surname = p_data.upper()
                if surname.startswith(surname_starts_with.upper()):
                    result[bitrix_id] = p_data
        else:
            result = BW.COURIERS.copy()

        user.send.page_number = 0
        user.send.couriers = result


@TgCommons.tg_callback
def get_couriers_by_surname(update, context, user):
    user.send.courier_surname_starts_with = Utils.prepare_str(update.message.text)
    cache_couriers(user, update.message.text)
    render_cur_page(update, context, user)
    return State.SEND_CHOOSE_COURIER


@TgCommons.tg_callback
def show_all_couriers(update, context, user):
    cache_couriers(user)
    render_cur_page(update, context, user)
    return State.SEND_CHOOSE_COURIER


@TgCommons.tg_callback
def choose_courier(update, context, user: Operator):
    courier_id = context.match.group(1)
    user.deal_data.courier_id = courier_id

    BH.send_deal(user)

    courier = Utils.prepare_external_field(BW.COURIERS, courier_id, BW.COURIERS_LOCK)
    message = Txt.DEAL_UPDATED.format(user.deal_data.deal_id, courier)
    TgCommons.send_mdv2(update.effective_user, message)
    return TgCommons.restart(update, context)


@TgCommons.tg_callback
def next_page(update, context, user: Operator):
    page_number = user.send.page_number

    if page_number < user.send.total_pages - 1:
        user.send.page_number += 1
        render_cur_page(update, context, user, True)

    return State.SEND_CHOOSE_COURIER


@TgCommons.tg_callback
def prev_page(update, context, user: Operator):
    page_number = user.send.page_number

    if page_number > 0:
        user.send.page_number -= 1
        render_cur_page(update, context, user, True)

    return State.SEND_CHOOSE_COURIER


cv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(callback=request_deal_number, pattern=GlobalTxt.MENU_DEAL_SEND_BUTTON_CB)],
    states={
        State.SEND_SET_DEAL_NUMBER: [MessageHandler(Filters.regex(GlobalTxt.BITRIX_DEAL_NUMBER_PATTERN),
                                                    set_deal_number)],
        State.SEND_SET_COURIER: [MessageHandler(Filters.text, get_couriers_by_surname),
                                 CallbackQueryHandler(callback=show_all_couriers,
                                                      pattern=Txt.SHOW_ALL_COURIERS_BUTTON_CB)],
        State.SEND_CHOOSE_COURIER: [CallbackQueryHandler(callback=choose_courier,
                                                         pattern=Txt.COURIER_CHOOSE_BUTTON_PATTERN),
                                    CallbackQueryHandler(callback=next_page,
                                                         pattern=Txt.NEXT_PAGE_CB),
                                    CallbackQueryHandler(callback=prev_page,
                                                         pattern=Txt.PREV_PAGE_CB)
                                    ],
        State.SEND_CHANGE_COURIER: [CallbackQueryHandler(callback=change_courier,
                                                         pattern=Txt.CHANGE_COURIER_BUTTON_CB),
                                    CallbackQueryHandler(callback=leave_courier,
                                                         pattern=Txt.LEAVE_COURIER_BUTTON_CB)]
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
