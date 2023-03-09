import logging

from telegram.ext import MessageHandler, Filters, CallbackContext, \
    ConversationHandler, CommandHandler, CallbackQueryHandler

from telegram import InlineKeyboardButton

from source.User import Operator
from source.State import State
import source.Commands as Cmd
import source.BitrixWorker as BW
import source.utils.Utils as Utils
import source.TelegramCommons as TgCommons
import source.TextSnippets as GlobalTxt
import source.cmd_handlers.Send.TgHandlers as CLHandlers
import source.cmd_handlers.SetCourier.BitrixHandlers as BH
import source.cmd_handlers.Send.BitrixHandlers as SendBH
import source.cmd_handlers.Send.TextSnippets as SendTxt
import source.cmd_handlers.SetCourier.TextSnippets as Txt
import source.cmd_handlers.Send.TgHandlers as SendHandlers

logger = logging.getLogger(__name__)


@TgCommons.tg_callback
def set_deal_number(update, context: CallbackContext, user: Operator):
    deal_id = update.message.text

    result = BH.set_deal_number(user, deal_id)

    if result == BW.BW_NO_SUCH_DEAL:
        TgCommons.send_mdv2(update.effective_user, GlobalTxt.NO_SUCH_DEAL.format(deal_id))
        return None
    elif result == SendBH.BH_ALREADY_HAS_COURIER:
        with BW.COURIERS_LOCK:
            courier = Utils.prepare_external_field(BW.COURIERS, user.deal_data.courier_id)

        keyboard = [[InlineKeyboardButton(text=SendTxt.CHANGE_COURIER_BUTTON_TEXT,
                                          callback_data=SendTxt.CHANGE_COURIER_BUTTON_CB)],
                    [InlineKeyboardButton(text=Txt.LEAVE_COURIER_BUTTON_TEXT.format(courier.upper()),
                                          callback_data=SendTxt.LEAVE_COURIER_BUTTON_CB)]]
        TgCommons.send_mdv2(update.effective_user, SendTxt.COURIER_ALREADY_SET_HEADER.format(courier.upper(),
                                                                                             deal_id),
                            keyboard)
        return State.SEND_CHANGE_COURIER

    SendHandlers.send_couriers_header(update, context, user)
    return State.SEND_SET_COURIER


@TgCommons.tg_callback
def choose_courier(update, context, user: Operator):
    courier_id = context.match.group(1)
    user.deal_data.courier_id = courier_id

    BH.update_deal_courier(user)

    courier = Utils.prepare_external_field(BW.COURIERS, user.deal_data.courier_id, BW.COURIERS_LOCK)
    message = Txt.DEAL_UPDATED.format(user.deal_data.deal_id, courier)
    TgCommons.send_mdv2(update.effective_user, message)
    return TgCommons.restart(update, context)


@TgCommons.tg_callback
def leave_courier(update, context: CallbackContext, user: Operator):
    courier = Utils.prepare_external_field(BW.COURIERS, user.deal_data.courier_id, BW.COURIERS_LOCK)
    message = Txt.COURIER_LEFT.format(user.deal_data.deal_id, courier)
    TgCommons.send_mdv2(update.effective_user, message)
    return TgCommons.restart(update, context)


cv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(callback=CLHandlers.request_deal_number,
                                       pattern=GlobalTxt.MENU_DEAL_COURIER_BUTTON_CB)],
    states={
        State.SEND_SET_DEAL_NUMBER: [MessageHandler(Filters.regex(GlobalTxt.BITRIX_DEAL_NUMBER_PATTERN),
                                                    set_deal_number)],
        State.SEND_SET_COURIER: [MessageHandler(Filters.text, SendHandlers.get_couriers_by_surname),
                                 CallbackQueryHandler(callback=SendHandlers.show_all_couriers,
                                                      pattern=SendTxt.SHOW_ALL_COURIERS_BUTTON_CB)],
        State.SEND_CHOOSE_COURIER: [CallbackQueryHandler(callback=choose_courier,
                                                         pattern=SendTxt.COURIER_CHOOSE_BUTTON_PATTERN),
                                    CallbackQueryHandler(callback=SendHandlers.next_page,
                                                         pattern=SendTxt.NEXT_PAGE_CB),
                                    CallbackQueryHandler(callback=SendHandlers.prev_page,
                                                         pattern=SendTxt.PREV_PAGE_CB)
                                    ],
        State.SEND_CHANGE_COURIER: [CallbackQueryHandler(callback=SendHandlers.change_courier,
                                                         pattern=SendTxt.CHANGE_COURIER_BUTTON_CB),
                                    CallbackQueryHandler(callback=leave_courier,
                                                         pattern=SendTxt.LEAVE_COURIER_BUTTON_CB)],

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
