import logging

import source.bitrix.BitrixWorker as BW
from source.Users import Operator
from source.bitrix.Deal import Deal


logger = logging.getLogger(__name__)


def send_deal(user: Operator):
    update_obj = {Deal.Fields.STAGE: Deal.FilMapStage.IS_IN_DELIVERY,
                  Deal.Fields.COURIER_NEW: user.deal.courier_id,
                  Deal.Fields.SENDER_ID: user.bitrix_user_id}

    BW.update_deal(user.deal.deal_id, update_obj)


def update_deal_courier(user: Operator):
    update_obj = {Deal.Fields.COURIER_NEW: user.deal.courier_id}
    BW.update_deal(user.deal.deal_id, update_obj)