import logging

from source.utils import Utils
import source.BitrixWorker as BW
from source.BitrixFieldsAliases import *
from source.BitrixFieldMappings import *
from source.User import Operator
from source.DealData import DealData

logger = logging.getLogger(__name__)


def process_deals(user: Operator):
    params = {
        'filter': {DEAL_FLORIST_NEW_ALIAS: user.bitrix_user_id,
                   DEAL_STAGE_ALIAS: DEAL_FLORIST_STATUS_ID},
        'select': [DEAL_ID_ALIAS, DEAL_SUPPLY_METHOD_ALIAS, DEAL_ORDER_ALIAS, DEAL_ORDER_COMMENT_ALIAS,
                   DEAL_POSTCARD_TEXT_ALIAS, DEAL_TOTAL_SUM_ALIAS, DEAL_DATE_ALIAS, DEAL_TIME_ALIAS,
                   DEAL_ORDER_RESERVE_ALIAS, DEAL_ORDER_RESERVE_DESC_ALIAS, DEAL_HAS_POSTCARD_ALIAS]
    }

    deals = BW.send_request('crm.deal.list', params, handle_next=True)

    for d in deals:
        deal = DealData()
        deal.deal_id = Utils.prepare_external_field(d, DEAL_ID_ALIAS)
        deal.supply_type = Utils.prepare_deal_supply_method(d, DEAL_SUPPLY_METHOD_ALIAS)
        deal.order = Utils.prepare_external_field(d, DEAL_ORDER_ALIAS)
        deal.order_comment = Utils.prepare_external_field(d, DEAL_ORDER_COMMENT_ALIAS)
        has_postcard = Utils.prepare_external_field(d, DEAL_HAS_POSTCARD_ALIAS)

        if has_postcard == DEAL_HAS_POSTCARD_YES:
            deal.has_postcard = True
            deal.postcard_text = Utils.prepare_external_field(d, DEAL_POSTCARD_TEXT_ALIAS)

        deal.sum = Utils.prepare_external_field(d, DEAL_TOTAL_SUM_ALIAS)
        deal.date = Utils.prepare_deal_date(d, DEAL_DATE_ALIAS)
        deal.time = Utils.prepare_deal_time(d, DEAL_TIME_ALIAS)
        deal.order_reserve = [el['downloadUrl'] for el in d.get(DEAL_ORDER_RESERVE_ALIAS)]  # only links list for now
        deal.reserve_desc = Utils.prepare_external_field(d, DEAL_ORDER_RESERVE_DESC_ALIAS)

        user.florist_order.add_deal(deal)



