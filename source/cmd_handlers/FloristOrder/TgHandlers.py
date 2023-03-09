import logging

from telegram.ext import MessageHandler, Filters, CallbackContext, \
    ConversationHandler, CommandHandler, CallbackQueryHandler
from telegram import Update, InlineKeyboardButton, InputMediaPhoto

from source.User import Operator
from source.State import State
import source.Commands as Cmd
import source.config as cfg
import source.TelegramCommons as TgCommons
import source.TextSnippets as GlobalTxt
import source.BitrixWorker as BW
import source.creds as creds

from . import TextSnippets as Txt
from . import BitrixHandlers as BH

import source.cmd_handlers.Equip.TgHandlers as EquipHandlers

logger = logging.getLogger(__name__)


@TgCommons.tg_callback
def get_deals(update: Update, context: CallbackContext, user: Operator):
    BH.process_deals(user)
    render_cur_deal(update, user)

    return State.FLORIST_VIEWS_ORDER


def render_cur_deal(update: Update, user: Operator):
    cur_deal_index = user.florist_order.cur_deal_index
    deals = user.florist_order.deals_list

    if not deals:
        TgCommons.send_mdv2(update.effective_user, Txt.NO_ORDERS)
        return None

    d = deals[cur_deal_index]
    keyboard = []

    if d.order_reserve:
        keyboard.append([InlineKeyboardButton(text=Txt.VIEW_RESERVE_PHOTO_BUTTON_TEXT,
                                              callback_data=Txt.VIEW_RESERVE_PHOTO_BUTTON_CB)])

    keyboard.append([InlineKeyboardButton(text=Txt.EQUIP_BUTTON_TEXT,
                                          callback_data=Txt.EQUIP_BUTTON_CB)])

    if cur_deal_index > 0:
        keyboard.append([InlineKeyboardButton(text=Txt.PREV_ORDER_BUTTON_TEXT, callback_data=Txt.PREV_ORDER_BUTTON_CB)])

    if cur_deal_index < len(deals) - 1:
        if cur_deal_index > 0:  # if prev page button has been added
            keyboard[-1].append(InlineKeyboardButton(text=Txt.NEXT_ORDER_BUTTON_TEXT,
                                                     callback_data=Txt.NEXT_ORDER_BUTTON_CB))
        else:
            keyboard.append([InlineKeyboardButton(text=Txt.NEXT_ORDER_BUTTON_TEXT,
                                                  callback_data=Txt.NEXT_ORDER_BUTTON_CB)])

    postcard_elt = Txt.POSTCARD_ELT.format(d.postcard_text) if d.postcard_text else ''
    deal_text = Txt.ORDER_TEMPLATE.format(cur_deal_index + 1, len(deals), d.deal_id, d.supply_type, d.order,
                                          d.order_comment, postcard_elt,
                                          d.sum, d.date, d.time)

    TgCommons.send_mdv2(update.effective_user, deal_text, keyboard)


@TgCommons.tg_callback
def view_reserve_photo(update: Update, context: CallbackContext, user: Operator):
    cur_deal_index = user.florist_order.cur_deal_index
    deals = user.florist_order.deals_list

    d = deals[cur_deal_index]

    with BW.OAUTH_LOCK:
        access_token = context.bot_data[cfg.BOT_ACCESS_TOKEN_PERSISTENT_KEY]

        deal_photos_links = [creds.BITRIX_MAIN_PAGE + el.replace('auth=', 'auth=' + access_token)
                             for el in d.order_reserve]

        msg_text = Txt.RESERVE_VIEWER_TEXT
        if d.reserve_desc:
            msg_text += d.reserve_desc + '\n'

        media_list = [InputMediaPhoto(media=el) for el in deal_photos_links]
        keyboard = [[InlineKeyboardButton(text=Txt.EQUIP_BUTTON_TEXT,
                                          callback_data=Txt.EQUIP_BUTTON_CB)],
                    [InlineKeyboardButton(text=Txt.BACK_TO_ORDER_BUTTON_TEXT,
                                          callback_data=Txt.BACK_TO_ORDER_BUTTON_CB)]]

        TgCommons.send_media_group(update.effective_user, media_list)
        TgCommons.send_mdv2(update.effective_user, msg_text, keyboard)


@TgCommons.tg_callback
def back_to_deals(update: Update, context: CallbackContext, user: Operator):
    render_cur_deal(update, user)
    return State.FLORIST_VIEWS_ORDER


@TgCommons.tg_callback
def prev_deal(update: Update, context: CallbackContext, user: Operator):
    deals_size = len(user.florist_order.deals_list)

    if user.florist_order.cur_deal_index == 0:
        user.florist.cur_deal_index = deals_size - 1
    else:
        user.florist_order.cur_deal_index -= 1

    render_cur_deal(update, user)


@TgCommons.tg_callback
def next_deal(update: Update, context: CallbackContext, user: Operator):
    deals_size = len(user.florist_order.deals_list)

    user.florist_order.cur_deal_index = (user.florist_order.cur_deal_index + 1) % deals_size
    render_cur_deal(update, user)


@TgCommons.tg_callback
def equip_deal(update: Update, context, user: Operator):
    cur_deal = user.florist_order.deals_list[user.florist_order.cur_deal_index]
    update.effective_message.text = cur_deal.deal_id

    # use unwrapped function to answer CBQ only once
    return EquipHandlers.set_deal_number.__wrapped__(update, context, user)


cv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(callback=get_deals,
                                       pattern=GlobalTxt.MENU_DEAL_FLORIST_ORDERS_BUTTON_CB)],
    states={
        State.FLORIST_VIEWS_ORDER: [CallbackQueryHandler(callback=view_reserve_photo,
                                                         pattern=Txt.VIEW_RESERVE_PHOTO_BUTTON_CB),
                                    CallbackQueryHandler(callback=equip_deal,
                                                         pattern=Txt.EQUIP_BUTTON_CB),
                                    CallbackQueryHandler(callback=prev_deal,
                                                         pattern=Txt.PREV_ORDER_BUTTON_CB),
                                    CallbackQueryHandler(callback=next_deal,
                                                         pattern=Txt.NEXT_ORDER_BUTTON_CB),
                                    CallbackQueryHandler(callback=back_to_deals,
                                                        pattern=Txt.BACK_TO_ORDER_BUTTON_CB)
                                    ],
        State.FLORIST_VIEWS_RESERVE_PHOTO: [CallbackQueryHandler(callback=equip_deal,
                                                                 pattern=Txt.EQUIP_BUTTON_CB),
                                            CallbackQueryHandler(callback=back_to_deals,
                                                                 pattern=Txt.BACK_TO_ORDER_BUTTON_CB)
                                            ],
        **EquipHandlers.cv_handler.states
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
