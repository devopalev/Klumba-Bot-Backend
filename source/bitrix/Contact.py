from source.bitrix import BitrixWorker


class PhoneContact:
    def __init__(self, data: dict):
        self.id = data.get("ID")
        self.value = data.get("VALUE")
        self.value_type = data.get("VALUE_TYPE")
        self.type_id = data.get("TYPE_ID")

    def __repr__(self):
        return f"{self.__dict__}"

    @property
    def params(self):
        return {"VALUE": self.value, "VALUE_TYPE": self.value_type, "TYPE_ID": self.type_id}


class Contact:
    def __init__(self, data=None):
        if data is None:
            self.new = True
            self.data = {}
        else:
            self.new = False
            self.data = data
        self.id = self.data.get("ID")
        self.last_name = self.data.get("LAST_NAME")
        self.name = self.data.get("NAME")
        self.type_id = self.data.get("TYPE_ID")
        self.phone = [PhoneContact(ph) for ph in self.data.get("PHONE")] if self.data.get("PHONE") else []

    def __repr__(self):
        return f"{self.__dict__}"

    @property
    def fullname(self):
        return (self.last_name if self.last_name else '') + " " + (self.name if self.name else '')

    @classmethod
    def build(cls, contact_id):
        result = BitrixWorker.ThrottlingRequest.send('crm.contact.get', params={'id': contact_id})
        if result:
            return cls(result)

    def add_phone(self, phone: str):
        self.phone.append(PhoneContact({"VALUE": phone}))

    def create_by_bitrix(self):
        if not self.new:
            raise ValueError("Contact already exists")
        if self.name and self.phone:
            fields = {"NAME": self.name, "PHONE": [ph.params for ph in self.phone]}
            if self.last_name:
                fields.update({"LAST_NAME": self.last_name})

            type_id = self.type_id if self.type_id else "CLIENT"
            fields.update({"TYPE_ID": type_id})

            return BitrixWorker.ThrottlingRequest.send("crm.contact.add", params={"fields": fields})


def get_contact(contact_id):
    return BitrixWorker.ThrottlingRequest.send("crm.contact.get", params={"ID": contact_id})


# import pprint
# contact = get_contact("158615")
# pprint.pprint(contact)
# print(len(contact))
# pprint.pprint(get_contact("168029"))


# contact = Contact()
# contact.name = "Опалев тестирование"
# contact.add_phone("89175156289")
# res = contact.create_by_bitrix()
# print(res)
