import logging
import math
from datetime import datetime, timedelta

from telegram.ext import MessageHandler, Filters, \
    ConversationHandler, CommandHandler, CallbackQueryHandler

from telegram import InlineKeyboardButton, InputMediaPhoto

import source.BitrixWorker as BW
from source.State import State
import source.Commands as Cmd
import source.utils.Utils as Utils
import source.utils.TelegramCalendar as TgCalendar
import source.TelegramCommons as TgCommons
import source.TextSnippets as GlobalTxt
import source.creds as creds
import source.config as cfg

from . import TextSnippets as Txt
from . import BitrixHandlers as BitrixHandlers
from . import UserData as UserData

logger = logging.getLogger(__name__)


def render_cur_page(update, context, user, edit_message=False):
    deals_num = len(user.data.deals_dict)
    page_number = user.data.page_number
    user.data.total_pages = math.ceil(deals_num / UserData.DEALS_PER_PAGE)

    deals_type_elt = Txt.DEALS_TYPE_STR_MAPPING[user.data.deals_type]
    if user.data.deals_type in [UserData.DealsType.FINISHED_IN_TIME, UserData.DealsType.FINISHED_LATE]:
        formatted_date = Utils.prepare_str(user.data.deals_date.strftime('%d.%m.%Y'))
        deals_date_elt = Txt.DEALS_DATE_ELT.format(formatted_date)
        deals_type_elt = deals_type_elt.format(deals_date_elt)

    message = Txt.DEAL_TOTAL_ORDERS_HEADER.format(deals_type_elt,
                                                  deals_num)

    if user.data.total_pages > 1:
        message += Txt.DEAL_PAGE_HEADER.format(page_number + 1, user.data.total_pages)

    deals_list = user.data.get_deals_list()
    deals_page = deals_list[page_number * UserData.DEALS_PER_PAGE:
                            (page_number + 1) * UserData.DEALS_PER_PAGE]

    for d in deals_page:
        deal_view_cmd = Cmd.CMD_PREFIX + Txt.VIEW_DEAL_PREFIX + Cmd.CMD_DELIMETER + d.deal_id
        deal_terminal = Txt.DEAL_TERMINAL_ELT if d.terminal_needed else ''
        deal_change_sum = Txt.DEAL_CHANGE_ELT.format(d.change_sum) if d.change_sum is not None else ''
        deal_to_pay = Txt.DEAL_TO_PAY_ELT.format(d.to_pay) if d.to_pay is not None else ''

        message += Txt.DEAL_PREVIEW_TEMPLATE.format(Utils.escape_mdv2(deal_view_cmd), d.time, d.date,
                                                    d.address,
                                                    Txt.ADDRESS_RESOLUTION_LINK + Utils.escape_mdv2_textlink(d.address),
                                                    d.flat,
                                                    d.recipient_name, d.recipient_phone,
                                                    Utils.escape_mdv2_textlink(d.recipient_phone),
                                                    d.district, d.delivery_comment, d.incognito,
                                                    deal_terminal, deal_change_sum, deal_to_pay)

        message += '\n\n' + Txt.DEAL_DELIMETER + '\n\n'

    keyboard = []
    if page_number > 0:
        keyboard.append([InlineKeyboardButton(Txt.PREV_PAGE_TEXT, callback_data=Txt.PREV_PAGE_CB)])

    if page_number < user.data.total_pages - 1:
        if page_number > 0:  # if prev page button has been added
            keyboard[0].append(InlineKeyboardButton(Txt.NEXT_PAGE_TEXT, callback_data=Txt.NEXT_PAGE_CB))
        else:
            keyboard.append([InlineKeyboardButton(Txt.NEXT_PAGE_TEXT, callback_data=Txt.NEXT_PAGE_CB)])

    keyboard.extend([
        [InlineKeyboardButton(Txt.DELIVERS_TODAY_BUTTON_TEXT, callback_data=Txt.DELIVERS_TODAY_BUTTON_CB)],
        [InlineKeyboardButton(Txt.DELIVERS_TOMORROW_BUTTON_TEXT, callback_data=Txt.DELIVERS_TOMORROW_BUTTON_CB)],
        [InlineKeyboardButton(Txt.ADVANCE_BUTTON_TEXT, callback_data=Txt.ADVANCE_BUTTON_CB)],
        [InlineKeyboardButton(Txt.FINISHED_BUTTON_TEXT, callback_data=Txt.FINISHED_BUTTON_CB)],
    ])

    if edit_message:
        TgCommons.edit_mdv2(update.effective_message, message, keyboard)
    else:
        TgCommons.send_mdv2(update.effective_user, message, keyboard)


@TgCommons.tg_callback
def delivers_tomorrow(update, context, user):
    user.data.deals_type = UserData.DealsType.DELIVERS_TOMORROW
    user.data.page_number = 0

    BitrixHandlers.process_deals(user)

    render_cur_page(update, context, user)
    return State.IN_COURIER_MENU


@TgCommons.tg_callback
def in_advance(update, context, user):
    user.data.deals_type = UserData.DealsType.IN_ADVANCE
    user.data.page_number = 0

    BitrixHandlers.process_deals(user)

    render_cur_page(update, context, user)
    return State.IN_COURIER_MENU


@TgCommons.tg_callback
def finished(update, context, user):
    cal_keyboard = TgCalendar.create_calendar()

    TgCommons.send_mdv2(update.effective_user, Txt.FINISHED_CHOOSE_DATE_TXT, cal_keyboard)
    return State.COURIER_CHOOSING_FINISHED_DATE


@TgCommons.tg_callback
def calendar_finished(update, context, user):
    result, dt = TgCalendar.process_calendar_selection(update, context, with_hours=False)

    # not empty button clicked
    if result:
        user.data.deals_date = dt
        keyboard = [[InlineKeyboardButton(Txt.LATE_BUTTON_TEXT, callback_data=Txt.LATE_BUTTON_CB)],
                    [InlineKeyboardButton(Txt.IN_TIME_BUTTON_TEXT, callback_data=Txt.IN_TIME_BUTTON_CB)]]

        TgCommons.send_mdv2(update.effective_user, Txt.FINISHED_CHOOSE_TYPE_TXT, keyboard)
        return State.COURIER_CHOOSING_FINISHED_TYPE

    return user.state


def type_finished(update, context, user):
    user.data.page_number = 0

    BitrixHandlers.process_deals(user)

    render_cur_page(update, context, user)

    return State.IN_COURIER_MENU


@TgCommons.tg_callback
def type_finished_late(update, context, user):
    user.data.deals_type = UserData.DealsType.FINISHED_LATE
    return type_finished(update, context, user)


@TgCommons.tg_callback
def type_finished_in_time(update, context, user):
    user.data.deals_type = UserData.DealsType.FINISHED_IN_TIME
    return type_finished(update, context, user)


@TgCommons.tg_callback
def prev_page(update, context, user):
    if user.data.page_number > 0:
        user.data.page_number -= 1
        render_cur_page(update, context, user, edit_message=True)

    return user.state


@TgCommons.tg_callback
def next_page(update, context, user):
    if user.data.page_number < user.data.total_pages - 1:
        user.data.page_number += 1
        render_cur_page(update, context, user, edit_message=True)

    return user.state


def render_cur_deal(update, context, user):
    deal_id = user.deal_data.deal_id
    d = user.data.get_deal(deal_id)

    deal_terminal = Txt.DEAL_TERMINAL_ELT if d.terminal_needed else ''
    deal_change_sum = Txt.DEAL_CHANGE_ELT.format(d.change_sum) if d.change_sum is not None else ''
    deal_to_pay = Txt.DEAL_TO_PAY_ELT.format(d.to_pay) if d.to_pay is not None else ''

    message = Txt.DEAL_VIEW_TEMPLATE.format(deal_id, d.time, d.date, d.address,
                                            Txt.ADDRESS_RESOLUTION_LINK + Utils.escape_mdv2_textlink(d.address),
                                            d.flat,
                                            d.recipient_name, d.recipient_phone, d.recipient_phone,
                                            d.district, d.delivery_comment,
                                            d.incognito, deal_terminal, deal_change_sum, deal_to_pay,
                                            d.subdivision, d.sender, d.source, d.contact_phone, d.contact_phone)

    keyboard = [[InlineKeyboardButton(Txt.ORDER_CONTENT_BUTTON_TEXT, callback_data=Txt.ORDER_CONTENT_BUTTON_CB)]]

    if user.data.deals_type == UserData.DealsType.DELIVERS_TODAY:
        keyboard.extend([[InlineKeyboardButton(Txt.FINISH_DEAL_BUTTON_TEXT, callback_data=Txt.FINISH_DEAL_BUTTON_CB)],
                         [InlineKeyboardButton(Txt.WAREHOUSE_RETURN_DEAL_BUTTON_TEXT,
                                               callback_data=Txt.WAREHOUSE_RETURN_DEAL_BUTTON_CB)]])

    keyboard.append([InlineKeyboardButton(Txt.BACK_TO_CUR_DEALS_LIST_BUTTON_TEXT,
                                          callback_data=Txt.BACK_TO_CUR_DEALS_LIST_BUTTON_CB)])

    with BW.OAUTH_LOCK:
        access_token = context.bot_data[cfg.BOT_ACCESS_TOKEN_PERSISTENT_KEY]

        deal_photos_links = [creds.BITRIX_MAIN_PAGE + el.replace('auth=', 'auth=' + access_token)
                             for el in d.order_big_photos]

        media_list = [InputMediaPhoto(media=el) for el in deal_photos_links]

        if media_list:
            TgCommons.send_media_group(update.effective_user, media_list)

        TgCommons.send_mdv2(update.effective_user, message, keyboard)


@TgCommons.tg_callback
def view_deal(update, context, user):
    deal_id = context.match.group(1)

    # TODO: !!!
    if not user.data.deals_dict:
        BitrixHandlers.process_deals(user)

    logger.info(f'Courier {user.bitrix_user_id} viewing deal {deal_id} when deals type is {user.data.deals_type}, deals dict is {list(user.data.deals_dict.keys())}')
    user.deal_data.deal_id = deal_id  # save for future use commands based on deal view

    render_cur_deal(update, context, user)
    return State.COURIER_VIEWS_DEAL


@TgCommons.tg_callback
def view_order_content(update, context, user):
    d = user.data.get_deal(user.deal_data.deal_id)

    message = d.order
    keyboard = [[InlineKeyboardButton(Txt.BACK_TO_CUR_DEAL_BUTTON_TEXT,
                                      callback_data=Txt.BACK_TO_CUR_DEAL_BUTTON_CB)]]

    TgCommons.send_mdv2(update.effective_user, message, keyboard)
    return State.COURIER_VIEWS_DEAL_ORDER


@TgCommons.tg_callback
def back_to_cur_deal(update, context, user):
    render_cur_deal(update, context, user)  # deal id has been already set
    return State.COURIER_VIEWS_DEAL


@TgCommons.tg_callback
def finish_deal(update, context, user):
    message = Txt.APPROVE_DEAL_FINISH_TEXT.format(user.deal_data.deal_id)
    keyboard = [[InlineKeyboardButton(Txt.APPROVE_DEAL_FINISH_BUTTON_TEXT,
                                      callback_data=Txt.APPROVE_DEAL_FINISH_BUTTON_CB)]]
    TgCommons.send_mdv2(update.effective_user, message, keyboard)
    return State.COURIER_FINISHES_DEAL


def finish_deal_helper(update, context, user):
    deal_id = user.deal_data.deal_id

    result = BitrixHandlers.finish_deal(user)

    if result == BW.BW_WRONG_STAGE:
        TgCommons.send_mdv2(update.effective_user, Txt.DEAL_IS_IN_WRONG_STAGE_TXT.format(deal_id))
        return user.state

    TgCommons.send_mdv2(update.effective_user, Txt.DEAL_FINISHED.format(deal_id))
    return TgCommons.restart(update, context)


@TgCommons.tg_callback
def approve_finish_deal(update, context, user):
    deal_id = user.deal_data.deal_id
    d = user.data.get_deal(deal_id)
    deadline_time = d.time.split(Txt.DEAL_TIME_DELIMETER)[-1].strip()
    hm_list = deadline_time.split(Txt.DEAL_HOURS_MINUTES_DELIMETER)
    deadline_hour = int(hm_list[0])
    deadline_minutes = int(hm_list[1])

    now = datetime.now(tz=cfg.TIMEZONE)
    deadline_dt = now.replace(hour=deadline_hour, minute=deadline_minutes, second=0)

    # if delivery deadline is 00 hours -> then it's until tomorrow's midnight
    if deadline_hour == 0:
        deadline_dt += timedelta(days=1)

    if now > deadline_dt:
        TgCommons.send_mdv2(update.effective_user, Txt.DEAL_IS_TOO_LATE_TEXT.format(deal_id, deadline_time))
        return State.COURIER_WRITING_LATE_REASON

    return finish_deal_helper(update, context, user)


@TgCommons.tg_callback
def set_deal_late_reason(update, context, user):
    user.data.late_reason = update.message.text
    return finish_deal_helper(update, context, user)


@TgCommons.tg_callback
def warehouse_return_deal(update, context, user):
    message = Txt.APPROVE_WAREHOUSE_RETURN_TEXT.format(user.deal_data.deal_id)
    keyboard = [[InlineKeyboardButton(Txt.APPROVE_WAREHOUSE_RETURN_BUTTON_TEXT,
                                      callback_data=Txt.APPROVE_WAREHOUSE_RETURN_BUTTON_CB)]]
    TgCommons.send_mdv2(update.effective_user, message, keyboard)
    return State.COURIER_RETURNS_DEAL_TO_WAREHOUSE


@TgCommons.tg_callback
def approve_warehouse_return_deal(update, context, user):
    message = Txt.WAREHOUSE_RETURN_TEXT.format(user.deal_data.deal_id)
    TgCommons.send_mdv2(update.effective_user, message)
    return State.COURIER_WRITING_WAREHOUSE_RETURN_REASON


@TgCommons.tg_callback
def set_warehouse_return_reason(update, context, user):
    deal_id = user.deal_data.deal_id
    user.data.warehouse_return_reason = update.message.text

    result = BitrixHandlers.return_to_warehouse(user)

    if result == BW.BW_WRONG_STAGE:
        TgCommons.send_mdv2(update.effective_user, Txt.DEAL_IS_IN_WRONG_STAGE_TXT.format(deal_id))
        return user.state

    TgCommons.send_mdv2(update.effective_user, Txt.DEAL_RETURNED_TO_WAREHOUSE.format(deal_id))
    return TgCommons.restart(update, context)


@TgCommons.tg_callback
def back_to_cur_deals_list(update, context, user):
    render_cur_page(update, context, user)
    return State.IN_COURIER_MENU


# viewing deals list, switching pages...
@TgCommons.tg_callback
def delivers_today(update, context, user):
    user.data.deals_type = UserData.DealsType.DELIVERS_TODAY
    user.data.page_number = 0

    BitrixHandlers.process_deals(user)

    render_cur_page(update, context, user)
    return State.IN_COURIER_MENU


MENU_HANDLERS = [CallbackQueryHandler(callback=delivers_today, pattern=Txt.DELIVERS_TODAY_BUTTON_CB),
                 CallbackQueryHandler(callback=delivers_tomorrow, pattern=Txt.DELIVERS_TOMORROW_BUTTON_CB),
                 CallbackQueryHandler(callback=in_advance, pattern=Txt.ADVANCE_BUTTON_CB),
                 CallbackQueryHandler(callback=finished, pattern=Txt.FINISHED_BUTTON_CB),
                 CallbackQueryHandler(callback=prev_page, pattern=Txt.PREV_PAGE_CB),
                 CallbackQueryHandler(callback=next_page, pattern=Txt.NEXT_PAGE_CB),
                 MessageHandler(Filters.chat_type.private & Filters.regex(Txt.VIEW_DEAL_PATTERN), view_deal)]

cv_handler = ConversationHandler(
    entry_points=MENU_HANDLERS,
    states={
        State.IN_COURIER_MENU: MENU_HANDLERS,
        State.COURIER_CHOOSING_FINISHED_DATE: [CallbackQueryHandler(callback=calendar_finished,
                                                                    pattern=TgCalendar.PATTERN)],
        State.COURIER_CHOOSING_FINISHED_TYPE: [CallbackQueryHandler(callback=type_finished_late,
                                                                    pattern=Txt.LATE_BUTTON_CB),
                                               CallbackQueryHandler(callback=type_finished_in_time,
                                                                    pattern=Txt.IN_TIME_BUTTON_CB)],
        State.COURIER_VIEWS_DEAL: [CallbackQueryHandler(callback=view_order_content,
                                                        pattern=Txt.ORDER_CONTENT_BUTTON_CB),
                                   CallbackQueryHandler(callback=finish_deal,
                                                        pattern=Txt.FINISH_DEAL_BUTTON_CB),
                                   CallbackQueryHandler(callback=warehouse_return_deal,
                                                        pattern=Txt.WAREHOUSE_RETURN_DEAL_BUTTON_CB),
                                   CallbackQueryHandler(callback=back_to_cur_deals_list,
                                                        pattern=Txt.BACK_TO_CUR_DEALS_LIST_BUTTON_CB)],
        State.COURIER_VIEWS_DEAL_ORDER: [CallbackQueryHandler(callback=back_to_cur_deal,
                                                              pattern=Txt.BACK_TO_CUR_DEAL_BUTTON_CB)],
        State.COURIER_FINISHES_DEAL: [CallbackQueryHandler(callback=approve_finish_deal,
                                                           pattern=Txt.APPROVE_DEAL_FINISH_BUTTON_CB)],
        State.COURIER_WRITING_LATE_REASON: [MessageHandler(Filters.text, set_deal_late_reason)],
        State.COURIER_RETURNS_DEAL_TO_WAREHOUSE: [CallbackQueryHandler(callback=approve_warehouse_return_deal,
                                                                       pattern=Txt.APPROVE_WAREHOUSE_RETURN_BUTTON_CB)],
        State.COURIER_WRITING_WAREHOUSE_RETURN_REASON: [MessageHandler(Filters.text, set_warehouse_return_reason)]
    },
    fallbacks=[CommandHandler([Cmd.START, Cmd.CANCEL], TgCommons.restart),
               CommandHandler([Cmd.LOGOUT], TgCommons.logout),
               CallbackQueryHandler(callback=TgCommons.restart, pattern=GlobalTxt.CANCEL_BUTTON_CB_DATA),
               MessageHandler(Filters.all, TgCommons.global_fallback),
               CallbackQueryHandler(callback=TgCommons.global_fallback, pattern=GlobalTxt.ANY_STRING_PATTERN)],
    map_to_parent={
        State.LOGIN_REQUESTED: State.LOGIN_REQUESTED
    }
)
