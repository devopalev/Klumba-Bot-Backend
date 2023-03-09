import source.bitrix.BitrixWorker as BW
from source.bitrix.Contact import Contact

source = BW.Bitrix.data.sources


def search_contact(phone):
    phone_raw = str(phone)[-10:]
    phone_7 = f"+7{phone}"
    phone_8 = f"8{phone_raw}"
    select = ["ID", "NAME", "LAST_NAME", "PHONE", "TYPE_ID"]

    batch = BW.Batch()

    batch.add_request(phone_raw, 'crm.contact.list', params={'filter': {'PHONE': phone_raw}, 'select': select})
    batch.add_request(phone_7, 'crm.contact.list', params={'filter': {'PHONE': phone_7}, 'select': select})
    batch.add_request(phone_8, 'crm.contact.list', params={'filter': {'PHONE': phone_8}, 'select': select})
    batch.send()

    result = []
    if isinstance(batch.get_result(phone_raw), list):
        result.extend(batch.get_result(phone_raw))
    if isinstance(batch.get_result(phone_7), list):
        result.extend(batch.get_result(phone_7))
    if isinstance(batch.get_result(phone_8), list):
        result.extend(batch.get_result(phone_8))
    return [Contact(val) for val in result]

