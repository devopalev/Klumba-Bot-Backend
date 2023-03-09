from telegram.ext import CallbackContext
from telegram import InputMediaPhoto, Chat, InlineKeyboardButton

import source.utils.Utils as Utils
import source.bitrix.BitrixWorker as BW
import source.config as cfg
import source.secret as creds
import source.http_server.TextSnippets as Txt
import source.bitrix.BitrixFieldsAliases as BFA
import source.bitrix.BitrixFieldMappings as BFM
import source.TelegramCommons as TgCommons


def send_festive_deal_message(bot, deal_id, deal_stage, deal_order, deal_date, deal_time, deal_sum, deal_accepted,
                              deal_source, deal_contact, deal_subdivision, deal_reserve_desc,
                              deal_delivery_type, deal_district, deal_address, deal_delivery_comment,
                              deal_pay_method, deal_pay_type, deal_prepaid, deal_terminal, deal_change,
                              deal_to_pay, deal_pay_status,
                              photo_urls):

    reserve_desc = Txt.DEAL_RESERVE_DESC_ELT.format(deal_reserve_desc) \
        if deal_reserve_desc != GlobalTxt.FIELD_IS_EMPTY_PLACEHOLDER else ''
    prepaid = Txt.DEAL_PREPAID_ELT.format(deal_prepaid) if deal_pay_type == BFM.DEAL_PAY_PREPAID_FRIENDLY else ''
    terminal = Txt.DEAL_TERMINAL_ELT.format(deal_terminal) if deal_pay_type == BFM.DEAL_PAY_PERSONAL_FRIENDLY else ''
    change = Txt.DEAL_CHANGE_ELT.format(deal_change) if deal_terminal != BFM.DEAL_PAY_TERMINAL_FRIENDLY else ''

    deal_message = Txt.DEAL_FESTIVE_PROCESSED_TEMPLATE.format(deal_id, deal_stage, deal_order,
                                                              deal_date, deal_time, deal_sum, deal_accepted,
                                                              deal_source, deal_contact, deal_subdivision,
                                                              reserve_desc, deal_delivery_type, deal_district,
                                                              deal_address, deal_delivery_comment, deal_pay_method,
                                                              deal_pay_type, prepaid, terminal, change, deal_to_pay,
                                                              deal_pay_status)

    keyboard = [[InlineKeyboardButton(text=Txt.FESTIVE_APPROVE_BUTTON_TEXT,
                                      callback_data=Txt.FESTIVE_APPROVE_BUTTON_KEY
                                                    + Cmd.CMD_DELIMETER + deal_id)],
                [InlineKeyboardButton(text=Txt.FESTIVE_DECLINE_BUTTON_TEXT,
                                      callback_data=Txt.FESTIVE_DECLINE_BUTTON_KEY
                                                    + Cmd.CMD_DELIMETER + deal_id)]]

    chat = Chat(bot=bot, id=creds.FESTIVE_APPROVAL_CHAT_ID, type=Chat.SUPERGROUP)

    # 1024 symbols of caption only, if more -> need a message
    if photo_urls:
        media_list = [InputMediaPhoto(media=el) for el in photo_urls]
        bot.send_media_group(chat_id=creds.FESTIVE_APPROVAL_CHAT_ID, media=media_list)

    TgCommons.send_mdv2_chat(chat, deal_message, keyboard)


def festive_deal_processed(context: CallbackContext):
    query_components = context.job.context
    bot = context.bot

    with BW.OAUTH_LOCK:
        access_token = context.bot_data[cfg.BOT_ACCESS_TOKEN_PERSISTENT_KEY]

        deal_id = Utils.prepare_external_field(query_components, BFA.WEBHOOK_DEAL_ID_ALIAS)
        deal_stage = Utils.prepare_external_field(query_components, BFA.WEBHOOK_STAGE_ALIAS)
        deal_order = Utils.prepare_external_field(query_components, BFA.WEBHOOK_DEAL_ORDER_ALIAS)
        deal_date = Utils.prepare_external_field(query_components, BFA.WEBHOOK_DATE_ALIAS)
        deal_time = Utils.prepare_external_field(query_components, BFA.WEBHOOK_TIME_ALIAS)
        deal_sum = Utils.prepare_external_field(query_components, BFA.WEBHOOK_SUM_ALIAS)
        deal_accepted = Utils.prepare_external_field(query_components, BFA.WEBHOOK_ACCEPTED_ALIAS)
        deal_source = Utils.prepare_external_field(query_components, BFA.WEBHOOK_SOURCE_ALIAS)
        deal_contact = Utils.prepare_external_field(query_components, BFA.WEBHOOK_CONTACT_ALIAS)
        deal_subdivision = Utils.prepare_external_field(query_components, BFA.WEBHOOK_SUBDIVISION_ALIAS)
        deal_has_reserve = Utils.prepare_external_field(query_components, BFA.WEBHOOK_HAS_RESERVE_ALIAS)
        deal_reserve_desc = Utils.prepare_external_field(query_components, BFA.WEBHOOK_RESERVE_DESC_ALIAS)
        deal_delivery_type = Utils.prepare_external_field(query_components, BFA.WEBHOOK_DELIVERY_TYPE_ALIAS)
        deal_district = Utils.prepare_external_field(query_components, BFA.WEBHOOK_DISTRICT_ALIAS)
        deal_address = Utils.prepare_external_field(query_components, BFA.WEBHOOK_ADDRESS_ALIAS)
        deal_delivery_comment = Utils.prepare_external_field(query_components, BFA.WEBHOOK_DELIVERY_COMMENT_ALIAS)
        deal_pay_method = Utils.prepare_external_field(query_components, BFA.WEBHOOK_PAY_METHOD_ALIAS)
        deal_pay_type = Utils.prepare_external_field(query_components, BFA.WEBHOOK_PAY_TYPE_ALIAS)
        deal_prepaid = Utils.prepare_external_field(query_components, BFA.WEBHOOK_PREPAID_ALIAS)
        deal_terminal = Utils.prepare_external_field(query_components, BFA.WEBHOOK_TERMINAL_ALIAS)
        deal_change = Utils.prepare_external_field(query_components, BFA.WEBHOOK_CHANGE_ALIAS)
        deal_to_pay = Utils.prepare_external_field(query_components, BFA.WEBHOOK_TO_PAY_ALIAS)
        deal_pay_status = Utils.prepare_external_field(query_components, BFA.WEBHOOK_PAY_STATUS_ALIAS)

        if deal_id != GlobalTxt.FIELD_IS_EMPTY_PLACEHOLDER:
            if deal_has_reserve == BFM.DEAL_HAS_RESERVE_YES_FRIENDLY:
                photo_urls = BW.get_deal_photo_dl_urls(deal_id, access_token, (BFA.DEAL_ORDER_RESERVE_ALIAS,))
            else:
                photo_urls = None

            send_festive_deal_message(bot, deal_id, deal_stage, deal_order,
                                      deal_date, deal_time, deal_sum, deal_accepted,
                                      deal_source, deal_contact, deal_subdivision, deal_reserve_desc,
                                      deal_delivery_type, deal_district, deal_address, deal_delivery_comment,
                                      deal_pay_method, deal_pay_type, deal_prepaid, deal_terminal, deal_change,
                                      deal_to_pay, deal_pay_status,
                                      photo_urls)
