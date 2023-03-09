import logging

import source.BitrixWorker as BW
import source.utils.Utils as Utils
from source.BitrixFieldsAliases import *
import source.BitrixFieldMappings as BFM
from source.User import Operator

BH_ALREADY_HAS_FLORIST = 1

logger = logging.getLogger(__name__)


def set_deal_number(user: Operator, deal_id):
    deal = BW.get_deal(deal_id)

    if not deal:
        return BW.BW_NO_SUCH_DEAL

    user.deal_data.deal_id = deal_id
    user.deal_data.stage = deal.get(DEAL_STAGE_ALIAS)

    if user.deal_data.stage not in (BFM.DEAL_PROCESSED_WAITING_FOR_SUPPLY_STATUS_ID, BFM.DEAL_PRINTED_STATUS_ID,
                                    BFM.DEAL_PROCESSED_ON_HOLD_STATUS_ID, BFM.DEAL_PAID_PREPAID_STATUS_ID):
        return BW.BW_WRONG_STAGE

    user.deal_data.florist_id = deal.get(DEAL_FLORIST_NEW_ALIAS)

    user.deal_data.order = Utils.prepare_external_field(deal, DEAL_ORDER_ALIAS)
    contact_id = deal.get(DEAL_CONTACT_ALIAS)

    contact_data = BW.get_contact_data(contact_id)
    contact_name = contact_data.get(CONTACT_USER_NAME_ALIAS)
    contact_phone = contact_data.get(CONTACT_PHONE_ALIAS)

    user.deal_data.contact = contact_name + ' ' + contact_phone
    user.deal_data.florist = Utils.prepare_external_field(BW.FLORISTS, user.deal_data.florist_id, BW.FLORISTS_LOCK)

    order_received_by_id = deal.get(DEAL_ORDER_RECEIVED_BY_ALIAS)
    user.deal_data.order_received_by = Utils.prepare_external_field(BW.BITRIX_IDS_USERS, order_received_by_id,
                                                                    BW.BITRIX_USERS_LOCK)

    user.deal_data.total_sum = Utils.prepare_external_field(deal, DEAL_TOTAL_SUM_ALIAS)

    payment_type_id = Utils.prepare_external_field(deal, DEAL_PAYMENT_TYPE_ALIAS)
    user.deal_data.payment_type = Utils.prepare_external_field(BW.PAYMENT_TYPES, payment_type_id, BW.PAYMENT_TYPES_LOCK)

    payment_method_id = Utils.prepare_external_field(deal, DEAL_PAYMENT_METHOD_ALIAS)
    user.deal_data.payment_method = Utils.prepare_external_field(BW.PAYMENT_METHODS, payment_method_id,
                                                                 BW.PAYMENT_METHODS_LOCK)

    user.deal_data.payment_status = Utils.prepare_external_field(deal, DEAL_PAYMENT_STATUS_ALIAS)

    user.deal_data.prepaid = Utils.prepare_external_field(deal, DEAL_PREPAID_ALIAS)
    user.deal_data.to_pay = Utils.prepare_external_field(deal, DEAL_TO_PAY_ALIAS)

    courier_id = Utils.prepare_external_field(deal, DEAL_COURIER_NEW_ALIAS)
    user.deal_data.courier = Utils.prepare_external_field(BW.COURIERS, courier_id, BW.COURIERS_LOCK)

    order_type_id = Utils.prepare_external_field(deal, DEAL_ORDER_TYPE_ALIAS)
    user.deal_data.order_type = Utils.prepare_external_field(BW.ORDERS_TYPES, order_type_id,
                                                             BW.ORDERS_TYPES_LOCK)

    user.deal_data.order_comment = Utils.prepare_external_field(deal, DEAL_ORDER_COMMENT_ALIAS)
    user.deal_data.delivery_comment = Utils.prepare_external_field(deal, DEAL_DELIVERY_COMMENT_ALIAS)
    user.deal_data.incognito = Utils.prepare_deal_incognito_bot_view(deal, DEAL_INCOGNITO_ALIAS)

    if user.deal_data.florist_id:
        return BH_ALREADY_HAS_FLORIST

    return BW.BW_OK


def update_deal_florist(user: Operator):
    update_obj = {DEAL_STAGE_ALIAS: BFM.DEAL_FLORIST_STATUS_ID,
                  DEAL_FLORIST_NEW_ALIAS: user.deal_data.florist_id,
                  DEAL_FLORIST_SETTER_ID_ALIAS: user.bitrix_user_id}

    BW.update_deal(user.deal_data.deal_id, update_obj)
