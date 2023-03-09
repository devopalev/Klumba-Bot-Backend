import logging
from datetime import datetime, timedelta

import source.BitrixWorker as BW
import source.BitrixFieldMappings as BFM
from source.BitrixFieldsAliases import *
from source.cmd_handlers.Courier.UserData import *
from source.utils import Utils

logger = logging.getLogger(__name__)


def process_deals(user):
    user.data.clear_deals()

    deals_type = user.data.deals_type
    stages = None
    dt = None
    is_late = None

    if deals_type == DealsType.DELIVERS_TODAY:
        stages = [BFM.DEAL_IS_IN_DELIVERY_STATUS_ID]
        dt = datetime.now(tz=cfg.TIMEZONE).strftime('%Y-%m-%d')
    elif deals_type == DealsType.DELIVERS_TOMORROW:
        stages = [BFM.DEAL_IS_IN_DELIVERY_STATUS_ID]
        dt = (datetime.now(tz=cfg.TIMEZONE) + timedelta(days=1)).strftime('%Y-%m-%d')
    elif deals_type == DealsType.IN_ADVANCE:
        stages = [BFM.DEAL_NEW_STATUS_ID, BFM.DEAL_IN_PROCESS_STATUS_ID, BFM.DEAL_PAID_PREPAID_STATUS_ID,
                  BFM.DEAL_PROCESSED_WAITING_FOR_SUPPLY_STATUS_ID, BFM.DEAL_PROCESSED_ON_HOLD_STATUS_ID,
                  BFM.DEAL_PRINTED_STATUS_ID, BFM.DEAL_FLORIST_STATUS_ID, BFM.DEAL_PROCESSED_1C_STATUS_ID,
                  BFM.DEAL_IS_EQUIPPED_STATUS_ID, BFM.DEAL_UNAPPROVED_STATUS_ID, BFM.DEAL_APPROVED_STATUS_ID]
    elif deals_type == DealsType.FINISHED_IN_TIME:
        stages = [BFM.DEAL_SUCCESSFUL_STATUS_ID, BFM.DEAL_LOSE_STATUS_ID]
        dt = user.data.deals_date.isoformat()
        is_late = False
    elif deals_type == DealsType.FINISHED_LATE:
        stages = [BFM.DEAL_SUCCESSFUL_STATUS_ID, BFM.DEAL_LOSE_STATUS_ID]
        dt = user.data.deals_date.isoformat()
        is_late = True

    flt = {
        DEAL_COURIER_NEW_ALIAS: user.bitrix_user_id,
        DEAL_STAGE_ALIAS: stages
    }

    if dt:
        flt[DEAL_DATE_ALIAS] = dt

    if is_late is not None:
        flt[DEAL_IS_LATE_ALIAS] = BFM.DEAL_IS_LATE_YES if is_late else BFM.DEAL_IS_LATE_NO

    params = {
        'filter': flt,
        'select': [DEAL_ID_ALIAS, DEAL_DATE_ALIAS, DEAL_TIME_ALIAS, DEAL_ADDRESS_ALIAS, DEAL_FLAT_ALIAS,
                   DEAL_RECIPIENT_NAME_ALIAS, DEAL_RECIPIENT_PHONE_ALIAS, DEAL_DISTRICT_ALIAS,
                   DEAL_DELIVERY_COMMENT_ALIAS, DEAL_INCOGNITO_ALIAS, DEAL_TERMINAL_CHANGE_ALIAS,
                   DEAL_CHANGE_SUM_ALIAS, DEAL_TO_PAY_ALIAS, DEAL_BIG_PHOTO_ALIAS, DEAL_SUBDIVISION_ALIAS,
                   DEAL_SENDER_ID_ALIAS, DEAL_SOURCE_ID_ALIAS, DEAL_ORDER_ALIAS, DEAL_CONTACT_ALIAS],
        'order': {DEAL_TIME_ALIAS: 'ASC'}
    }

    deals = BW.send_request('crm.deal.list', params, handle_next=True)

    for d in deals:
        deal = DealData()
        deal.deal_id = Utils.prepare_external_field(d, DEAL_ID_ALIAS)
        deal.date = Utils.prepare_deal_date(d, DEAL_DATE_ALIAS)
        deal.time = Utils.prepare_deal_time(d, DEAL_TIME_ALIAS)

        address, location = Utils.prepare_deal_address(d, DEAL_ADDRESS_ALIAS)
        deal.address = address
        deal.flat = Utils.prepare_external_field(d, DEAL_FLAT_ALIAS)

        deal.recipient_name = Utils.prepare_external_field(d, DEAL_RECIPIENT_NAME_ALIAS)
        deal.recipient_phone = Utils.prepare_external_field(d, DEAL_RECIPIENT_PHONE_ALIAS)

        district_id = Utils.prepare_external_field(d, DEAL_DISTRICT_ALIAS)
        deal.district = Utils.prepare_external_field(BW.DISTRICTS, district_id, BW.DISTRICTS_LOCK)

        deal.delivery_comment = Utils.prepare_external_field(d, DEAL_DELIVERY_COMMENT_ALIAS)
        deal.incognito = Utils.prepare_deal_incognito_bot_view(d, DEAL_INCOGNITO_ALIAS)

        terminal_change = Utils.prepare_external_field(d, DEAL_TERMINAL_CHANGE_ALIAS)

        if terminal_change == BFM.DEAL_NEED_TERMINAL:
            deal.terminal_needed = True
        elif terminal_change == BFM.DEAL_NEED_CHANGE:
            deal.change_sum = Utils.prepare_external_field(d, DEAL_CHANGE_SUM_ALIAS)

        to_pay = Utils.prepare_external_field(d, DEAL_TO_PAY_ALIAS)

        if to_pay != '0':
            deal.to_pay = to_pay

        # only URLs for now
        deal.order_big_photos = [el['downloadUrl'] for el in d.get(DEAL_BIG_PHOTO_ALIAS)]

        subdivision_id = Utils.prepare_external_field(d, DEAL_SUBDIVISION_ALIAS)
        deal.subdivision = Utils.prepare_external_field(BW.SUBDIVISIONS, subdivision_id, BW.SUBDIVISIONS_LOCK)

        sender_id = Utils.prepare_external_field(d, DEAL_SENDER_ID_ALIAS)
        deal.sender = Utils.prepare_str(BW.get_user_name(sender_id))

        source_id = Utils.prepare_external_field(d, DEAL_SOURCE_ID_ALIAS)
        deal.source = Utils.prepare_external_field(BW.SOURCES, source_id, BW.SOURCES_LOCK)

        deal.order = Utils.prepare_external_field(d, DEAL_ORDER_ALIAS)

        contact_id = Utils.prepare_external_field(d, DEAL_CONTACT_ALIAS)
        contact_data = BW.get_contact_data(contact_id)
        deal.contact_phone = contact_data.get(CONTACT_PHONE_ALIAS)

        user.data.add_deal(deal)


def finish_deal(user):
    deal_id = user.deal_data.deal_id

    # get stage, check it's actual
    actual_stage = BW.get_deal_stage(deal_id)

    if actual_stage != BFM.DEAL_IS_IN_DELIVERY_STATUS_ID:
        return BW.BW_WRONG_STAGE

    fields = {
        DEAL_STAGE_ALIAS: BFM.DEAL_SUCCESSFUL_STATUS_ID,
        DEAL_WAREHOUSE_RETURNED: BFM.DEAL_IS_RETURNED_TO_WAREHOUSE_NO
    }

    if user.data.late_reason is None:
        fields[DEAL_IS_LATE_ALIAS] = BFM.DEAL_IS_LATE_NO
    else:
        fields[DEAL_IS_LATE_ALIAS] = BFM.DEAL_IS_LATE_YES
        fields[DEAL_IS_LATE_REASON_ALIAS] = user.data.late_reason

    BW.update_deal(deal_id, fields)
    return BW.BW_OK


def return_to_warehouse(user):
    deal_id = user.deal_data.deal_id

    # get stage, check it's actual
    actual_stage = BW.get_deal_stage(deal_id)

    if actual_stage != BFM.DEAL_IS_IN_DELIVERY_STATUS_ID:
        return BW.BW_WRONG_STAGE

    fields = {
        DEAL_STAGE_ALIAS: BFM.DEAL_APPROVED_STATUS_ID,
        DEAL_WAREHOUSE_RETURNED: BFM.DEAL_IS_RETURNED_TO_WAREHOUSE_YES,
        DEAL_WAREHOUSE_RETURN_REASON: user.data.warehouse_return_reason
    }

    BW.update_deal(deal_id, fields)
    return BW.BW_OK
