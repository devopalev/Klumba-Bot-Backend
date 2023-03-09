# storing deal data while processing intermediate steps
class DealData:
    def __init__(self):
        self.photo_data = None
        self.photo_name = None

        self.courier_id = None

        self.deal_id = None
        self.stage = None
        self.order = None
        self.contact = None
        self.contact_phone = None
        self.order_received_by = None
        self.total_sum = None
        self.sum = None
        self.payment_type = None
        self.payment_method = None
        self.payment_status = None
        self.prepaid = None
        self.to_pay = None
        self.incognito = None
        self.order_comment = None
        self.delivery_comment = None
        self.order_type_id = None
        self.order_type = None
        self.supply_type = None
        self.has_postcard = None
        self.postcard_text = None
        self.time = None
        self.date = None
        self.order_reserve = []
        self.florist_id = None
        self.has_reserve = None
        self.reserve_desc = None
        self.supply_datetime = None
        self.recipient_name = None
        self.recipient_phone = None
        self.address = None
        self.flat = None
        self.subdivision = None
        self.district = None
        self.order_big_photos = []
        # Нужен терминал
        self.terminal_needed = None
        # Сдача С
        self.change_sum = None
        # Тот, кто отправил заказ
        self.sender = None
        # Источник
        self.source = None



