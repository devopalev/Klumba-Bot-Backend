import logging

import source.bitrix.BitrixWorker as BW
from source.Users import Operator
from source.bitrix.Deal import Deal

logger = logging.getLogger(__name__)


def update_deal_reserve(user: Operator):
    deal_id = user.deal.deal_id
    photos_list = user.reserve.encode_deal_photos()

    update_obj = {Deal.Fields.ORDER_RESERVE: [],
                  Deal.Fields.STAGE: Deal.FilMapStage.PROCESSED_ON_HOLD,
                  Deal.Fields.ORDER_RESERVE_DESC: user.deal.reserve_desc,
                  Deal.Fields.ORDER_HAS_RESERVE: Deal.FilMapReserve.RESERVE_YES,
                  Deal.Fields.RESERVE_HANDLER_ID: user.bitrix_user_id,
                  Deal.Fields.ORDER_RESERVE_NOT_NEEDED_APPROVE: Deal.Fields.ORDER_RESERVE_NOT_NEEDED_APPROVE}

    for photo in photos_list:
        update_obj[Deal.Fields.ORDER_RESERVE].append({'fileData': [photo.name_big,
                                                                   photo.data_big]})
    BW.update_deal(deal_id, update_obj)


def update_deal_no_reserve(user: Operator):
    deal_id = user.deal.deal_id
    photos_list = user.reserve.encode_deal_photos()

    update_obj = {Deal.Fields.ORDER_RESERVE: [{'fileData': [photos_list[0].name_big,
                                                           photos_list[0].data_big]}],
                  Deal.Fields.STAGE: Deal.FilMapStage.PROCESSED_ON_HOLD,
                  Deal.Fields.ORDER_RESERVE_DESC: "Резерв не нужен",
                  Deal.Fields.ORDER_HAS_RESERVE: Deal.FilMapReserve.DEAL_HAS_RESERVE_NO,
                  Deal.Fields.RESERVE_HANDLER_ID: user.bitrix_user_id,
                  Deal.Fields.ORDER_RESERVE_NOT_NEEDED_APPROVE: Deal.Fields.ORDER_RESERVE_NOT_NEEDED_APPROVE}

    BW.update_deal(deal_id, update_obj)


def update_deal_waiting_for_supply(user: Operator):
    deal_id = user.deal.deal_id

    update_obj = {Deal.Fields.ORDER_RESERVE: [],
                  Deal.Fields.STAGE: Deal.FilMapStage.PROCESSED_WAITING_FOR_SUPPLY,
                  Deal.Fields.ORDER_RESERVE_DESC: None,
                  Deal.Fields.ORDER_HAS_RESERVE: Deal.FilMapReserve.DEAL_HAS_RESERVE_NO,
                  Deal.Fields.SUPPLY_DATETIME: user.deal.supply_datetime,
                  Deal.Fields.RESERVE_HANDLER_ID: user.bitrix_user_id}

    BW.update_deal(deal_id, update_obj)
