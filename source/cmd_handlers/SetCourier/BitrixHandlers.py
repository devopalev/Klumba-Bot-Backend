import logging

import source.BitrixWorker as BW
import source.utils.Utils as Utils
from source.BitrixFieldsAliases import *
import source.BitrixFieldMappings as BFM
import source.cmd_handlers.Send.BitrixHandlers as SendBH
from source.User import Operator

logger = logging.getLogger(__name__)


def set_deal_number(user: Operator, deal_id):
    deal = BW.get_deal(deal_id)

    if not deal:
        return BW.BW_NO_SUCH_DEAL

    user.deal_data.deal_id = deal_id
    user.deal_data.stage = deal.get(DEAL_STAGE_ALIAS)
    user.deal_data.courier_id = deal.get(DEAL_COURIER_NEW_ALIAS)
    payment_type_id = Utils.prepare_external_field(deal, DEAL_PAYMENT_TYPE_ALIAS)
    user.deal_data.payment_type = Utils.prepare_external_field(BW.PAYMENT_TYPES, payment_type_id, BW.PAYMENT_TYPES_LOCK)

    terminal_change = Utils.prepare_external_field(deal, DEAL_TERMINAL_CHANGE_ALIAS)

    if terminal_change == BFM.DEAL_NEED_TERMINAL:
        user.deal_data.terminal_needed = True
    elif terminal_change == BFM.DEAL_NEED_CHANGE:
        user.deal_data.change_sum = Utils.prepare_external_field(deal, DEAL_CHANGE_SUM_ALIAS)

    user.deal_data.to_pay = Utils.prepare_external_field(deal, DEAL_TO_PAY_ALIAS)

    if user.deal_data.courier_id:
        return SendBH.BH_ALREADY_HAS_COURIER

    return BW.BW_OK


def update_deal_courier(user: Operator):
    update_obj = {DEAL_COURIER_NEW_ALIAS: user.deal_data.courier_id}

    BW.update_deal(user.deal_data.deal_id, update_obj)
