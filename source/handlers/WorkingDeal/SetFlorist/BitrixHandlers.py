import source.bitrix.BitrixWorker as BW
from source.Users import Operator
from source.bitrix.Deal import Deal


def update_deal_florist(user: Operator):
    update_obj = {Deal.Fields.STAGE: Deal.FilMapStage.FLORIST,
                  Deal.Fields.FLORIST_NEW: user.deal.florist_id,
                  Deal.Fields.FLORIST_SETTER_ID: user.bitrix_user_id}

    BW.update_deal(user.deal.deal_id, update_obj)
