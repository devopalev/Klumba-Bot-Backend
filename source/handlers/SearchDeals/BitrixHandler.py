import source.bitrix.BitrixWorker as BW
from source.Users import Operator
from source.bitrix.Deal import Deal


def get_deals(user: Operator) -> list:
    template = user.templates.selected
    filter_ = {}

    if not template.filter_date.empty:
        if template.filter_date.start:
            filter_[">" + Deal.Fields.DATE_CREATE] = template.filter_date.start.strftime("%Y-%m-%d %H:%M")
        if template.filter_date.end:
            filter_["<" + Deal.Fields.DATE_CREATE] = template.filter_date.end.strftime("%Y-%m-%d %H:%M")

    if template.filter_stage:
        filter_[Deal.Fields.STAGE] = template.filter_stage

    if template.filter_subdivisions:
        filter_[Deal.Fields.SUBDIVISION] = template.filter_subdivisions

    if template.filter_districts:
        filter_[Deal.Fields.DISTRICT] = template.filter_districts

    if template.filter_payment_type:
        filter_[Deal.Fields.PAYMENT_TYPE] = template.filter_payment_type

    if template.filter_payment_method:
        filter_[Deal.Fields.PAYMENT_METHOD] = template.filter_payment_method

    if template.filter_roles:
        for field in template.filter_roles:
            filter_[field] = user.bitrix_user_id

    params = {"filter": filter_, "select": ["ID"], "order": {Deal.Fields.DATE_CREATE: "ASC"}}
    result = BW.ThrottlingRequest.send("crm.deal.list", params=params)
    return result if result else []
