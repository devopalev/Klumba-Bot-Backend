from typing import List
import logging
import base64

from telegram.ext import MessageHandler, Filters, CallbackContext, \
    ConversationHandler, CommandHandler, CallbackQueryHandler

from telegram import PhotoSize, InlineKeyboardButton, Update

from source.User import Operator
from source.State import State
import source.Commands as Cmd
import source.TelegramCommons as TgCommons
import source.TextSnippets as GlobalTxt
import source.BitrixWorker as BW
import source.BitrixFieldMappings as BFM
import source.utils.Utils as Utils

import source.cmd_handlers.Equip.TextSnippets as Txt
from .Photo import Photo as Photo
import source.cmd_handlers.Equip.BitrixHandlers as BH
import source.cmd_handlers.Equip.StorageHandlers as StorageHandlers

logger = logging.getLogger(__name__)


@TgCommons.tg_callback
def request_deal_number(update, context: CallbackContext, user: Operator):
    TgCommons.send_mdv2(update.effective_user, Txt.ASK_FOR_DEAL_NUMBER)
    return State.EQUIP_SET_DEAL_NUMBER


@TgCommons.tg_callback
def set_deal_number(update, context: CallbackContext, user: Operator):
    deal_id = update.effective_message.text

    result = BH.set_deal_number(user, deal_id)

    if result == BW.BW_NO_SUCH_DEAL:
        TgCommons.send_mdv2(update.effective_user, GlobalTxt.NO_SUCH_DEAL.format(deal_id))
        return None

    if result == BW.BW_WRONG_STAGE:
        TgCommons.send_mdv2(update.effective_user, Txt.WRONG_DEAL_STAGE)
        return None

    # deal has been already equipped
    if user.deal_data.stage == BFM.DEAL_IS_EQUIPPED_STATUS_ID:
        user.equip.repeating = True
        keyboard = [[InlineKeyboardButton(text=Txt.EQUIP_REPEATEDLY_BUTTON_TEXT,
                                          callback_data=Txt.EQUIP_REPEATEDLY_BUTTON_CB)]]
        TgCommons.send_mdv2(update.effective_user, Txt.APPROVE_ALREADY_EQUIPPED_DEAL_TXT.format(deal_id), keyboard)
        return State.EQUIP_REPEATEDLY_APPROVE

    TgCommons.send_mdv2(update.effective_user, Txt.ASK_FOR_PHOTO_TEXT)
    return State.EQUIP_SET_PHOTOS


@TgCommons.tg_callback
def equip_repeatedly_approve(update, context, user: Operator):
    TgCommons.send_mdv2(update.effective_user, Txt.ASK_FOR_PHOTO_TEXT)
    return State.EQUIP_SET_PHOTOS


@TgCommons.tg_callback
def append_photo(update, context: CallbackContext, user: Operator):
    photos: List[PhotoSize] = update.message.photo

    photo_big = photos[-1]

    if len(photos) > 1:
        photo_small = photos[1]
    else:
        photo_small = photos[0]

    unique_id_big = photo_big.file_unique_id
    photo_content_big = photo_big.get_file().download_as_bytearray()
    file_extension_big = photo_big.get_file().file_path.split('.')[-1]

    file_extension_small = photo_small.get_file().file_path.split('.')[-1]
    unique_id_small = photo_small.file_unique_id
    photo_content_small = photo_small.get_file().download_as_bytearray()

    if photo_content_big and photo_content_small:
        logger.info(f'Appending photo: big photo content size: {len(photo_content_big)}')
        # store raw photo data to save it on disk later
        user.equip.add_deal_photo(Photo(unique_id_small + '_S.' + file_extension_small,
                                        unique_id_big + '_B.' + file_extension_big,
                                        photo_content_small,
                                        photo_content_big))

        keyboard = [[InlineKeyboardButton(text=Txt.FINISH_PHOTO_LOADING,
                                          callback_data=Txt.FINISH_PHOTO_LOADING_CB)]]
        TgCommons.send_mdv2(update.effective_user, Txt.PHOTO_LOADED_TEXT, keyboard)

        logger.info(f'User bitrix id {user.bitrix_user_id} uploaded photo {unique_id_small}.{file_extension_small}')
    else:
        logger.error('No photo content big/small from user %s', update.message.from_user.id)

    return None


def request_checklist(update, context, user: Operator):
    terminal_elt = Txt.DEAL_TERMINAL_ELT if user.deal_data.terminal_needed else ''
    change_elt = Txt.DEAL_CHANGE_ELT.format(user.deal_data.change_sum) if user.deal_data.change_sum else ''

    courier = Utils.prepare_external_field(BW.COURIERS, user.deal_data.courier_id, BW.COURIERS_LOCK)

    message = Txt.CHECKLIST_REQUEST.format(user.deal_data.deal_id, courier, user.deal_data.payment_type,
                                           terminal_elt, change_elt, user.deal_data.to_pay)

    TgCommons.send_mdv2(update.effective_user, message)


@TgCommons.tg_callback
def finish_photo_loading(update: Update, context: CallbackContext, user: Operator):
    if not user.equip.photos:
        keyboard = [[InlineKeyboardButton(text=Txt.FINISH_PHOTO_LOADING,
                                          callback_data=Txt.FINISH_PHOTO_LOADING_CB)]]
        TgCommons.send_mdv2(update.effective_user, Txt.NO_PHOTOS_TEXT, keyboard)
        return None

    if user.deal_data.has_postcard:
        TgCommons.send_mdv2(update.effective_user, Txt.DEAL_HAS_POSTCARD.format(user.deal_data.postcard_text))
        return State.EQUIP_SET_POSTCARD_FACIAL
    else:
        request_checklist(update, context, user)
        return State.EQUIP_SET_CHECKLIST


@TgCommons.tg_callback
def append_postcard(update, context: CallbackContext, user: Operator):
    photos: List[PhotoSize] = update.message.photo

    photo_big = photos[-1]

    unique_id_big = photo_big.file_unique_id
    photo_content_big = photo_big.get_file().download_as_bytearray()
    file_extension_big = photo_big.get_file().file_path.split('.')[-1]

    if photo_content_big:
        # store raw photo data to save it on disk later
        user.equip.add_deal_postcard(Photo(name_big=unique_id_big + '_B.' + file_extension_big,
                                           data_big=photo_content_big))
    else:
        logger.error('No photo content big/small from user %s', update.message.from_user.id)

    if user.state == State.EQUIP_SET_POSTCARD_FACIAL:
        TgCommons.send_mdv2(update.effective_user, Txt.DEAL_REQUEST_POSTCARD_REVERSE_SIDE)
        return State.EQUIP_SET_POSTCARD_REVERSE
    else:  # reverse loaded
        request_checklist(update, context, user)
        return State.EQUIP_SET_CHECKLIST


@TgCommons.tg_callback
def load_checklist_photo(update, context, user: Operator):
    if not user.equip.photos:
        keyboard = [[InlineKeyboardButton(text=Txt.FINISH_PHOTO_LOADING,
                                          callback_data=Txt.FINISH_PHOTO_LOADING_CB)]]
        TgCommons.send_mdv2(update.effective_user, Txt.NO_PHOTOS_TEXT, keyboard)
        return State.EQUIP_SET_PHOTOS

    photos: List[PhotoSize] = update.message.photo

    photo = photos[-1]
    unique_id = photo.file_unique_id
    photo_content = photo.get_file().download_as_bytearray()
    file_extension = photo.get_file().file_path.split('.')[-1]

    encoded_data = base64.b64encode(photo_content).decode('ascii')
    user.deal_data.photo_data = encoded_data
    user.deal_data.photo_name = unique_id + '.' + file_extension

    StorageHandlers.save_deal(user, user.deal_data.deal_id)
    BH.update_deal_image(user)

    TgCommons.send_mdv2(update.effective_user, GlobalTxt.DEAL_UPDATED.format(user.deal_data.deal_id))
    return TgCommons.restart(update, context)


cv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(callback=request_deal_number, pattern=GlobalTxt.MENU_DEAL_EQUIP_BUTTON_CB)],
    states={
        State.EQUIP_SET_DEAL_NUMBER: [MessageHandler(Filters.regex(GlobalTxt.BITRIX_DEAL_NUMBER_PATTERN),
                                                     set_deal_number)],
        State.EQUIP_REPEATEDLY_APPROVE: [CallbackQueryHandler(callback=equip_repeatedly_approve,
                                                              pattern=Txt.EQUIP_REPEATEDLY_BUTTON_CB)],
        State.EQUIP_SET_PHOTOS: [MessageHandler(Filters.photo, append_photo),
                                 CallbackQueryHandler(callback=finish_photo_loading,
                                                      pattern=Txt.FINISH_PHOTO_LOADING_CB)],
        State.EQUIP_SET_POSTCARD_FACIAL: [MessageHandler(Filters.photo, append_postcard)],
        State.EQUIP_SET_POSTCARD_REVERSE: [MessageHandler(Filters.photo, append_postcard)],
        State.EQUIP_SET_CHECKLIST: [MessageHandler(Filters.photo, load_checklist_photo)]
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
