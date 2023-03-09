from source.bitrix.Contact import Contact

class CreateDeal:
    def __init__(self):
        self.contact: Contact = None
        self.source = None
        self.order_or_form = None
        self.urgent_or_advance = None
        self.sales_department = None
        self.order_received_by = None
        self.order_contents = None

