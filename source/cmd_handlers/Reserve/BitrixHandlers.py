import logging

import source.BitrixWorker as BW
import source.cmd_handlers.Reserve.TextSnippets as Txt
from source.User import Operator

from source.BitrixFieldsAliases import *
from source.BitrixFieldMappings import *

logger = logging.getLogger(__name__)


def set_deal_number(user: Operator, deal_id):
    deal = BW.get_deal(deal_id)

    if not deal:
        return BW.BW_NO_SUCH_DEAL

    user.deal_data.deal_id = deal_id
    user.deal_data.stage = deal.get(DEAL_STAGE_ALIAS)

    if user.deal_data.stage != DEAL_PAID_PREPAID_STATUS_ID:
        return BW.BW_WRONG_STAGE

    return BW.BW_OK


def update_deal_reserve(user: Operator):
    deal_id = user.deal_data.deal_id
    photos_list = user.reserve.encode_deal_photos()

    update_obj = {DEAL_ORDER_RESERVE_ALIAS: [],
                  DEAL_STAGE_ALIAS: DEAL_PROCESSED_ON_HOLD_STATUS_ID,
                  DEAL_ORDER_RESERVE_DESC_ALIAS: user.deal_data.reserve_desc,
                  DEAL_ORDER_HAS_RESERVE_ALIAS: DEAL_HAS_RESERVE_YES,
                  DEAL_RESERVE_HANDLER_ID_ALIAS: user.bitrix_user_id,
                  DEAL_ORDER_RESERVE_NOT_NEEDED_APPROVE: DEAL_ORDER_RESERVE_NOT_NEEDED_APPROVE}

    for photo in photos_list:
        update_obj[DEAL_ORDER_RESERVE_ALIAS].append({'fileData': [photo.name_big,
                                                                  photo.data_big]})

    BW.update_deal(deal_id, update_obj)


def update_deal_no_reserve(user: Operator):
    deal_id = user.deal_data.deal_id
    photos_list = user.reserve.encode_deal_photos()

    update_obj = {DEAL_ORDER_RESERVE_ALIAS: [{'fileData': [photos_list[0].name_big,
                                                           photos_list[0].data_big]}],
                  DEAL_STAGE_ALIAS: DEAL_PROCESSED_ON_HOLD_STATUS_ID,
                  DEAL_ORDER_RESERVE_DESC_ALIAS: Txt.NO_RESERVE_NEEDED_STUB,
                  DEAL_ORDER_HAS_RESERVE_ALIAS: DEAL_HAS_RESERVE_NO,
                  DEAL_RESERVE_HANDLER_ID_ALIAS: user.bitrix_user_id,
                  DEAL_ORDER_RESERVE_NOT_NEEDED_APPROVE: DEAL_ORDER_RESERVE_NOT_NEEDED_APPROVE}

    BW.update_deal(deal_id, update_obj)


def update_deal_waiting_for_supply(user: Operator):
    deal_id = user.deal_data.deal_id

    update_obj = {DEAL_ORDER_RESERVE_ALIAS: [],
                  DEAL_STAGE_ALIAS: DEAL_PROCESSED_WAITING_FOR_SUPPLY_STATUS_ID,
                  DEAL_ORDER_RESERVE_DESC_ALIAS: None,
                  DEAL_ORDER_HAS_RESERVE_ALIAS: DEAL_HAS_RESERVE_NO,
                  DEAL_SUPPLY_DATETIME_ALIAS: user.deal_data.supply_datetime,
                  DEAL_RESERVE_HANDLER_ID_ALIAS: user.bitrix_user_id}

    BW.update_deal(deal_id, update_obj)
