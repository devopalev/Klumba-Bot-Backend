import re

import source.bitrix.BitrixWorker as BW
from source.bitrix.Contact import Contact


def generator():
    phone = ["9964316090"]


def search_contacts(phone):
    valid_pattern = re.compile(r"^((8|\+7|7)[\- ]?)?(\(?\d{3}\)?[\- ]?)?[\d\- ]{7,10}$")
    if not valid_pattern.match(phone):
        raise ValueError
    phone_raw = re.sub(r"\D", "", phone)[-10:]
    phone_blocks = [phone_raw[:3], phone_raw[3:6], phone_raw[6:8], phone_raw[8:10]]

    formats = ["", "+7", "7", "8"]
    numbers = [f + phone_raw for f in formats]

    select = ["ID", "NAME", "LAST_NAME", "PHONE", "TYPE_ID"]

    batch = BW.Batch()
    for num in numbers:
        batch.add_request(num, 'crm.contact.list', params={'filter': {'PHONE': num}, 'select': select})
    batch.send()

    result = {}
    for num in numbers:
        if isinstance(batch.get_result(num), list):
            for raw_contact in batch.get_result(num):
                result[raw_contact["ID"]] = raw_contact

    return [Contact(val) for val in result.values()]


def valid(phone):
    pattern = re.compile(r"^((8|\+7|7)[\- ]?)?(\(?\d{3}\)?[\- ]?)?[\d\- ]{7,10}$")
    psub = re.compile(r"[^\d]")
    phone_raw = re.sub(r"\D", "", phone)[-10:]
    print(phone_raw)
    # pattern = re.template(r"^(\+7|7|8)?\d{10}$")
    print(psub.sub("", phone))
    print(pattern.match(phone))


# valid("(996) 431 60-90")
#
#
# # cons = search_contacts("79964316090")
# #
# # for c in cons:
# #     print(c.id)