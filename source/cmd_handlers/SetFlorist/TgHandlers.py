import logging
import math

from telegram.ext import MessageHandler, Filters, CallbackContext, \
    ConversationHandler, CommandHandler, CallbackQueryHandler

from telegram import InlineKeyboardButton

from source.User import Operator
from source.State import State
import source.Commands as Cmd
import source.utils.Utils as Utils
import source.TelegramCommons as TgCommons
import source.TextSnippets as GlobalTxt
import source.BitrixWorker as BW

from . import TextSnippets as Txt
from . import BitrixHandlers as BH
from . import UserData

logger = logging.getLogger(__name__)


@TgCommons.tg_callback
def request_deal_number(update, context: CallbackContext, user):
    TgCommons.send_mdv2(update.effective_user, Txt.ASK_FOR_DEAL_NUMBER)
    return State.SETTING_FLORIST_DEAL_NUMBER


def send_florists_header(update, context, user):
    deal_info = Txt.DEAL_INFO_TEMPLATE.format(user.deal_data.deal_id,
                                              user.deal_data.order,
                                              user.deal_data.contact,
                                              user.deal_data.florist,
                                              user.deal_data.order_received_by,
                                              user.deal_data.incognito,
                                              user.deal_data.order_comment,
                                              user.deal_data.delivery_comment,
                                              user.deal_data.total_sum,
                                              user.deal_data.payment_type,
                                              user.deal_data.payment_method,
                                              user.deal_data.payment_status,
                                              user.deal_data.prepaid,
                                              user.deal_data.to_pay,
                                              user.deal_data.courier,
                                              user.deal_data.order_type)

    keyboard = [[InlineKeyboardButton(text=Txt.SHOW_ALL_FLORISTS_BUTTON_TEXT,
                                      callback_data=Txt.SHOW_ALL_FLORISTS_BUTTON_CB)]]
    TgCommons.send_mdv2(update.effective_user, deal_info + '\n\n' + Txt.CHOOSE_FLORIST_HEADER, keyboard)


@TgCommons.tg_callback
def set_deal_number(update, context: CallbackContext, user: Operator):
    deal_id = update.effective_message.text

    result = BH.set_deal_number(user, deal_id)

    if result == BW.BW_NO_SUCH_DEAL:
        TgCommons.send_mdv2(update.effective_user, GlobalTxt.NO_SUCH_DEAL.format(deal_id))
        return None
    elif result == BH.BH_ALREADY_HAS_FLORIST:
        with BW.FLORISTS_LOCK:
            florist = Utils.prepare_external_field(BW.FLORISTS, user.deal_data.florist_id).upper()

        keyboard = [[InlineKeyboardButton(text=Txt.CHANGE_FLORIST_BUTTON_TEXT,
                                          callback_data=Txt.CHANGE_FLORIST_BUTTON_CB)],
                    [InlineKeyboardButton(text=Txt.LEAVE_FLORIST_BUTTON_TEXT.format(florist),
                                          callback_data=Txt.LEAVE_FLORIST_BUTTON_CB)]]
        TgCommons.send_mdv2(update.effective_user, Txt.FLORIST_ALREADY_SET_HEADER.format(florist,
                                                                                         deal_id),
                            keyboard)
        return State.SETTING_FLORIST_CHANGE_FLORIST
    elif result == BW.BW_WRONG_STAGE:
        TgCommons.send_mdv2(update.effective_user, Txt.WRONG_DEAL_STAGE)
        return None

    send_florists_header(update, context, user)
    return State.SETTING_FLORIST_SET_FLORIST


@TgCommons.tg_callback
def leave_florist(update, context: CallbackContext, user: Operator):
    message = Txt.DEAL_UPDATED.format(user.deal_data.deal_id, user.deal_data.florist)
    TgCommons.send_mdv2(update.effective_user, message)
    return TgCommons.restart(update, context)


def render_cur_page(update, context, user: Operator, edit_message=False):
    florists_num = len(user.florist.florists)
    page_number = user.florist.page_number
    user.florist.total_pages = math.ceil(florists_num / UserData.FLORISTS_PER_PAGE)

    florist_surname_starts_with_elt = Txt.FLORISTS_LIST_SURNAME_STARTS_ELT \
        .format(user.florist.florist_surname_starts_with) if user.florist.florist_surname_starts_with else ''

    message = Txt.FLORISTS_LIST_HEADER.format(florist_surname_starts_with_elt)

    if user.florist.total_pages > 1:
        message += Txt.FLORISTS_PAGE_HEADER.format(page_number + 1, user.florist.total_pages)

    florists_tuples = list(user.florist.florists.items())
    page = florists_tuples[page_number * UserData.FLORISTS_PER_PAGE:
                           (page_number + 1) * UserData.FLORISTS_PER_PAGE]

    keyboard = []

    for bitrix_id, p_data in page:
        keyboard.append([InlineKeyboardButton(p_data, callback_data=bitrix_id)])

    if page_number > 0:
        keyboard.append([InlineKeyboardButton(Txt.PREV_PAGE_TEXT, callback_data=Txt.PREV_PAGE_CB)])

    if page_number < user.florist.total_pages - 1:
        if page_number > 0:  # if prev page button has been added
            keyboard[-1].append(InlineKeyboardButton(Txt.NEXT_PAGE_TEXT, callback_data=Txt.NEXT_PAGE_CB))
        else:
            keyboard.append([InlineKeyboardButton(Txt.NEXT_PAGE_TEXT, callback_data=Txt.NEXT_PAGE_CB)])

    if edit_message:
        TgCommons.edit_mdv2(update.effective_message, message, keyboard)
    else:
        TgCommons.send_mdv2(update.effective_user, message, keyboard)


def cache_florists(user: Operator, surname_starts_with=None):
    with BW.FLORISTS_LOCK:
        result = {}

        if surname_starts_with:
            for bitrix_id, p_data in BW.FLORISTS.items():
                surname = p_data.upper()
                if surname.startswith(surname_starts_with.upper()):
                    result[bitrix_id] = p_data
        else:
            result = BW.FLORISTS.copy()

        user.florist.page_number = 0
        user.florist.florists = result


@TgCommons.tg_callback
def get_florists_by_surname(update, context, user: Operator):
    user.florist.florist_surname_starts_with = Utils.prepare_str(update.message.text)
    cache_florists(user, update.message.text)
    render_cur_page(update, context, user)
    return State.SETTING_FLORIST_CHOOSE_FLORIST


@TgCommons.tg_callback
def show_all_florists(update, context, user):
    cache_florists(user)
    render_cur_page(update, context, user)
    return State.SETTING_FLORIST_CHOOSE_FLORIST


@TgCommons.tg_callback
def next_page(update, context, user: Operator):
    page_number = user.florist.page_number

    if page_number < user.florist.total_pages - 1:
        user.florist.page_number += 1
        render_cur_page(update, context, user, True)

    return State.SETTING_FLORIST_CHOOSE_FLORIST


@TgCommons.tg_callback
def prev_page(update, context, user: Operator):
    page_number = user.florist.page_number

    if page_number > 0:
        user.florist.page_number -= 1
        render_cur_page(update, context, user, True)

    return State.SETTING_FLORIST_CHOOSE_FLORIST


@TgCommons.tg_callback
def change_florist(update, context: CallbackContext, user: Operator):
    send_florists_header(update, context, user)
    return State.SETTING_FLORIST_SET_FLORIST


@TgCommons.tg_callback
def choose_florist(update, context, user: Operator):
    florist_id = context.match.group(1)
    user.deal_data.florist_id = florist_id

    BH.update_deal_florist(user)

    with BW.FLORISTS_LOCK:
        florist = Utils.prepare_external_field(BW.FLORISTS, user.deal_data.florist_id).upper()

    message = Txt.DEAL_UPDATED.format(user.deal_data.deal_id, florist)
    TgCommons.send_mdv2(update.effective_user, message)
    return TgCommons.restart(update, context)


cv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(callback=request_deal_number,
                                       pattern=GlobalTxt.MENU_DEAL_SET_FLORIST_BUTTON_CB)],
    states={
        State.SETTING_FLORIST_DEAL_NUMBER: [MessageHandler(Filters.regex(GlobalTxt.BITRIX_DEAL_NUMBER_PATTERN),
                                                           set_deal_number)],
        State.SETTING_FLORIST_SET_FLORIST: [MessageHandler(Filters.text, get_florists_by_surname),
                                            CallbackQueryHandler(callback=show_all_florists,
                                                                 pattern=Txt.SHOW_ALL_FLORISTS_BUTTON_CB)],
        State.SETTING_FLORIST_CHOOSE_FLORIST: [CallbackQueryHandler(callback=choose_florist,
                                                                    pattern=Txt.FLORIST_CHOOSE_BUTTON_PATTERN),
                                               CallbackQueryHandler(callback=next_page,
                                                                    pattern=Txt.NEXT_PAGE_CB),
                                               CallbackQueryHandler(callback=prev_page,
                                                                    pattern=Txt.PREV_PAGE_CB),
                                               MessageHandler(Filters.text, get_florists_by_surname)
                                               ],

        State.SETTING_FLORIST_CHANGE_FLORIST: [CallbackQueryHandler(callback=change_florist,
                                                                    pattern=Txt.CHANGE_FLORIST_BUTTON_CB),
                                               CallbackQueryHandler(callback=leave_florist,
                                                                    pattern=Txt.LEAVE_FLORIST_BUTTON_CB)]
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
