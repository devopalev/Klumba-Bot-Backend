import logging

import source.bitrix.BitrixWorker as BW
from source.Users import Courier
from source.bitrix.Deal import Deal

logger = logging.getLogger(__name__)


def get_deals(user: Courier, date):
    method = "crm.deal.list"
    select = [Deal.Fields.ID, Deal.Fields.DATE, Deal.Fields.TIME, Deal.Fields.ADDRESS, Deal.Fields.FLAT,
              Deal.Fields.RECIPIENT_NAME, Deal.Fields.RECIPIENT_PHONE, Deal.Fields.DISTRICT,
              Deal.Fields.DELIVERY_COMMENT, Deal.Fields.INCOGNITO, Deal.Fields.TERMINAL_CHANGE,
              Deal.Fields.CHANGE_SUM, Deal.Fields.TO_PAY, Deal.Fields.BIG_PHOTO, Deal.Fields.SUBDIVISION,
              Deal.Fields.SENDER_ID, Deal.Fields.SOURCE_ID, Deal.Fields.ORDER, Deal.Fields.CONTACT]

    flt = {Deal.Fields.COURIER_NEW: user.bitrix_user_id, Deal.Fields.CLOSED: Deal.FilMap.CLOSED_NO}

    if date:
        flt.update({Deal.Fields.STAGE: Deal.FilMapStage.IS_IN_DELIVERY})
        flt.update({Deal.Fields.DATE: date})
    else:
        flt.update({"!"+Deal.Fields.STAGE: Deal.FilMapStage.IS_IN_DELIVERY})

    params = {"filter": flt, "select": select}
    result = BW.ThrottlingRequest.send(method, params=params, handle_next=True)
    return result
