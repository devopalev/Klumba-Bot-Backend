import logging
import re

from telegram import InlineKeyboardButton

import source.bitrix.BitrixWorker as BW

logger = logging.getLogger(__name__)


class Deal:
    # deal stages
    class FilMapStage:
        NEW = 'C17:2'  # Новый заказ
        IN_PROCESS = 'C17:4'  # В обработке \ Надо проверить
        PAID_PREPAID = 'C17:UC_J0R30S'  # Оплачен \ Предоплачен
        PROCESSED_WAITING_FOR_SUPPLY = 'C17:13'  # Обработан, но ждет поставки
        PROCESSED_ON_HOLD = 'C17:6'  # Обработан,тов.отлож/не треб.
        PRINTED = 'C17:UC_EQMV7Y'  # Распечатан
        FLORIST = 'C17:7'  # У Флориста (Изготавливается)
        PROCESSED_1C = 'C17:8'  # Обработан в 1С
        IS_EQUIPPED = 'C17:NEW'  # Заказ укомплектован
        UNAPPROVED = 'C17:9'  # Несогласовано
        APPROVED = 'C17:10'  # Согласовано
        IS_IN_DELIVERY = 'C17:FINAL_INVOICE'  # В доставке
        SUCCESSFUL = 'C17:WON'  # Сделка успешна
        LOSE = 'C17:LOSE'  # Удален \ Провален
        LIST_REFERENCE_ID = 'DEAL_STAGE_17'  # Стадии по Базе Заказов (направление 17)

    class FilMapPostcardStage:
        DEAL_HAS_POSTCARD_YES = '2543'  # Есть открытка

    class FilMapPay:
        # Оплата
        PAY_PREPAID_FRIENDLY = 'Предоплата'
        PAY_PERSONAL_FRIENDLY = 'При получении'
        PAY_TERMINAL_FRIENDLY = 'Терминал'
        PAY_CHANGE_FRIENDLY = 'Сдача с:'
        NEED_TERMINAL = '2331'
        NEED_CHANGE = '2333'

    class FilMapReserve:
        # Есть резерв
        RESERVE_YES = '2551'
        DEAL_HAS_RESERVE_YES_FRIENDLY = 'Да'
        DEAL_HAS_RESERVE_NO = '2553'

    class FilMapFestive:
        APPROVEMENT_YES = '2891'
        APPROVEMENT_NO = '2893'
        APPROVEMENT_NOT_SELECTED = '3003'

    class FilMap:
        CLOSED_YES = "Y"
        CLOSED_NO = "N"

    class Fields:
        # deal fields
        ID = 'ID'  # Номер заказа
        CLOSED = 'CLOSED'  # Закрыта?
        DATE_CREATE = 'DATE_CREATE'  # Дата создания
        SMALL_PHOTO = 'UF_CRM_1583265060'  # Фото букета
        BIG_PHOTO = 'UF_CRM_1583348851496'  # Фото букета большое
        SUPPLY_METHOD = 'UF_CRM_1572419729488'  # Доставка \ Самовывоз
        CHECKLIST = 'UF_CRM_1587838059218'  # Фото чеклиста
        STAGE = 'STAGE_ID'  # Стадия сделки
        ORDER = 'UF_CRM_1572513138'  # Что заказано
        CONTACT = 'CONTACT_ID'  # Контактное лицо (клиент)
        ORDER_RECEIVED_BY = 'UF_CRM_1625240260'  # Кто принял заказ (привязка к сотруднику)
        TOTAL_SUM = 'OPPORTUNITY'  # Сумма сделки
        ORDER_OR_FORM = 'UF_CRM_1630074895761'  # Заказ или заявка(школа, горшечка, фитодиз, свадебное оформ)?
        PAYMENT_TYPE = 'UF_CRM_1572521912939'  # Тип оплаты
        PAYMENT_METHOD = 'UF_CRM_1581955203244'  # Способ оплаты
        PAYMENT_STATUS = 'UF_CRM_1582364078288'  # Статус оплаты
        PREPAID = 'UF_CRM_1581381796094'  # Предоплата
        TO_PAY = 'UF_CRM_1572874675779'  # К оплате
        COURIER = 'UF_CRM_1577117931'  # Курьер (старый, список строк)
        CLIENT_URL = 'UF_CRM_1592498133598'  # Ссылка клиента
        CLIENT_COMMENT = 'UF_CRM_1593363999625'  # Комментарий клиента
        CLIENT_CALLMEBACK = 'UF_CRM_1593364122228'  # Перезвонить клиенту
        COMMENT_APPROVED = 'UF_CRM_1594140784155'  # Комментарий - согласовано
        DATE = 'UF_CRM_1572436074496'  # Дата
        TIME = 'UF_CRM_1572436244600'  # Время
        ADDRESS = 'UF_CRM_1572422724116'  # Адрес
        INCOGNITO = 'UF_CRM_5DAF18DCC292F'  # Инкогнито
        ORDER_COMMENT = 'UF_CRM_1572864792721'  # Комментарий к товару
        DELIVERY_COMMENT = 'UF_CRM_1573049555741'  # Комментарий по доставке
        FLAT = 'UF_CRM_1572422787172'  # Квартира
        FLORIST_NEW = 'UF_CRM_1614264167'  # Флорист новый
        ORDER_TYPE = 'UF_CRM_1610634201578'  # Тип заказа
        POSTCARD_TEXT = 'UF_CRM_1573050122374'  # Текст открытки
        HAS_POSTCARD = 'UF_CRM_1625059428684'  # Есть ли открытка?
        POSTCARD_PHOTO = 'UF_CRM_1640434640'  # Фото открытки
        ORDER_RESERVE = 'UF_CRM_1620936565099'  # Резерв товара
        ORDER_RESERVE_NOT_NEEDED_APPROVE = 'UF_CRM_1638622666871'  # Подтверждаю, что резерв не нужен (горький твикс иначе)
        ORDER_RESERVE_DESC = 'UF_CRM_1625410694838'  # Что отложено
        ORDER_HAS_RESERVE = 'UF_CRM_1625834851636'  # Есть резерв?
        SUPPLY_DATETIME = 'UF_CRM_1628348038537'  # Дата поставки
        COURIER_NEW = 'UF_CRM_1632075413'  # Курьер (привязка к сотруднику)
        RECIPIENT_NAME = 'UF_CRM_5DAF18DD1755D'  # Имя получателя
        RECIPIENT_PHONE = 'UF_CRM_1572421180924'  # Телефон получателя
        SUBDIVISION = 'UF_CRM_1612453867429'  # Подразделение, ответственное за заказ
        DISTRICT = 'UF_CRM_1572422285260'  # Район доставки
        TERMINAL_CHANGE = 'UF_CRM_1613572957078'  # Терминал \ Сдача с
        CHANGE_SUM = 'UF_CRM_1613572999144'  # Сдача с (сумма)
        SENDER_ID = 'UF_CRM_1636976353'  # Кто отправил заказ? (привязка к сотруднику)
        EQUIPER_HANDLER_ID = 'UF_CRM_1636976653'  # Кто укомплектовал заказ? (привязка к сотруднику)
        RESERVE_HANDLER_ID = 'UF_CRM_1640625045'  # Кто обработал резерв/поставку заказ? (привязка к сотруднику)
        FLORIST_SETTER_ID = 'UF_CRM_1644678959'  # Кто назначил флориста?
        SOURCE_ID = 'SOURCE_ID'  # Источник
        IS_LATE = 'UF_CRM_1631979755121'  # Заказ опоздал
        IS_LATE_REASON = 'UF_CRM_1631979785526'  # Причина опоздания заказа
        WAREHOUSE_RETURN_REASON = 'UF_CRM_1613565471434'  # Причина возврата на склад, кому и куда отдан
        WAREHOUSE_RETURNED = 'UF_CRM_1640240629788'  # Заказ вернулся на склад (да \ нет)
        LINK = 'UF_CRM_1581375809'  # Ссылка на заказ
        ASSIGNED = 'ASSIGNED_BY_ID'  # Ответственный

        URGENT_OR_ADVANCE = 'UF_CRM_1655464829758'  # Срочный/Заблаговременный
        SALES_DEPARTAMENT = 'UF_CRM_1655465426062'  # Отдел продаж (Подразделение - продавец)

        # festive Approvement
        FESTIVE_APPROVEMENT = 'UF_CRM_1646001150'  # Праздничное согласование (список)
        FESTIVE_DECLINE_COMMENT = 'UF_CRM_1646163933'  # Комментарий по отклонению
        FESTIVE_DECLINE_USER = 'UF_CRM_1646208854'  # Кто отклонил
        FESTIVE_BOOL = "UF_CRM_1661526547"  # Что бы сменить стадию заказа необходимо согласование Вероники Егоровой!

    class ConstContact:
        # contact
        USER_NAME = 'NAME'
        CONTACT_PHONE = 'PHONE'
        CONTACT_HAS_PHONE = 'HAS_PHONE'

    class Buttons:
        PROCESS = InlineKeyboardButton("Обработать заказ 👌", callback_data="deal_process")
        SET_FLORIST = InlineKeyboardButton("Назначить флориста 👩‍🌾", callback_data="deal_set_florist")
        EQUIP_BUTTON = InlineKeyboardButton("Укомплектовать заказ 💐", callback_data="deal_equip")
        SEND = InlineKeyboardButton("Отправить заказ (назначить курьера) 🚚", callback_data="deal_send")
        COURIER = InlineKeyboardButton("Назначить курьера (заранее) 👨‍🦼", callback_data="deal_courier")

    def __init__(self, deal: dict):
        self.photo_data = None
        self.photo_name = None

        self.florist_id = deal.get(self.Fields.FLORIST_NEW)
        self.florist = BW.BitrixUsers.fullname_by_bitrix_id(self.florist_id)

        self.courier_id = deal.get(self.Fields.COURIER_NEW)
        self.courier = BW.BitrixUsers.fullname_by_bitrix_id(self.courier_id)

        self.deal_id = deal.get(self.Fields.ID)  # Номер заказа
        self.stage_id = deal.get(self.Fields.STAGE)
        self.stage_name = BW.Bitrix.data.stages.get(deal.get(self.Fields.STAGE))

        order = deal.get(self.Fields.ORDER)
        self.order = ", ".join(order) if order else None  # Что заказано

        contact_id = deal.get(self.Fields.CONTACT)  # Контактное лицо (клиент)
        if contact_id:
            contact_data = BW.get_contact_data(contact_id)
            self.contact = contact_data.get(self.ConstContact.USER_NAME)
            self.contact_phone = contact_data.get(self.ConstContact.CONTACT_PHONE)
        else:
            self.contact, self.contact_phone = None, None

        order_received_by_id = deal.get(self.Fields.ORDER_RECEIVED_BY)
        # Кто принял заказ (привязка к сотруднику)
        self.order_received_by = BW.BitrixUsers.fullname_by_bitrix_id(order_received_by_id)

        self.total_sum = deal.get(self.Fields.TOTAL_SUM)  # Сумма сделки

        # Тип оплаты
        payment_type_id = deal.get(self.Fields.PAYMENT_TYPE)
        field = BW.Bitrix.data.fields.get(self.Fields.PAYMENT_TYPE)
        self.payment_type = field.get_name_item(payment_type_id) if field else None

        payment_method_id = deal.get(self.Fields.PAYMENT_METHOD)
        field = BW.Bitrix.data.fields.get(self.Fields.PAYMENT_METHOD)
        self.payment_method = field.get_name_item(payment_method_id) if field else None

        self.payment_status = deal.get(self.Fields.PAYMENT_STATUS)  # Статус оплаты
        self.prepaid = deal.get(self.Fields.PREPAID)  # Предоплата
        self.to_pay = deal.get(self.Fields.TO_PAY)  # К оплате

        if deal.get(self.Fields.INCOGNITO) == '0':
            self.incognito = 'нет'
        elif deal.get(self.Fields.INCOGNITO) == '1':
            self.incognito = 'ВНИМАНИЕ - ДА!'
        else:
            self.incognito = None
        self.order_comment = deal.get(self.Fields.ORDER_COMMENT)
        self.delivery_comment = deal.get(self.Fields.DELIVERY_COMMENT)

        self.order_type_id = deal.get(self.Fields.ORDER_TYPE)
        self.order_type = deal.get(self.order_type_id)

        field = BW.Bitrix.data.fields.get(self.Fields.SUPPLY_METHOD)
        self.supply_type = field.get_name_item(deal.get(self.Fields.SUPPLY_METHOD)) if field else None
        supply_datetime = deal.get(self.Fields.SUPPLY_DATETIME)
        self.supply_datetime = supply_datetime.replace("T", " ").replace("+03:00", "") if supply_datetime else None

        # Открытка
        has_postcard = deal.get(self.Fields.HAS_POSTCARD)
        if has_postcard == self.FilMapPostcardStage.DEAL_HAS_POSTCARD_YES:
            self.has_postcard = True
            self.postcard_text = deal.get(self.Fields.POSTCARD_TEXT)
        else:
            self.has_postcard = None
            self.postcard_text = None

        field = BW.Bitrix.data.fields.get(self.Fields.TIME)
        self.time = field.get_name_item(deal.get(self.Fields.TIME)) if field else None
        date = deal.get(self.Fields.DATE)
        self.date = re.match(r"\d{4}-\d{2}-\d{2}", date)[0] if date else date
        if deal.get(self.Fields.ORDER_RESERVE):
            self.order_reserve = [el['downloadUrl'] for el in deal.get(self.Fields.ORDER_RESERVE)]
        else:
            self.order_reserve = None
        self.reserve_desc = deal.get(self.Fields.ORDER_RESERVE_DESC)
        self.has_reserve = deal.get(self.Fields.ORDER_HAS_RESERVE) == self.FilMapReserve.RESERVE_YES

        self.recipient_name = deal.get(self.Fields.RECIPIENT_NAME)
        self.recipient_phone = deal.get(self.Fields.RECIPIENT_PHONE)
        address = deal.get(self.Fields.ADDRESS)
        self.address = re.match(r"([^|]+)|", address)[0] if address else None
        self.flat = deal.get(self.Fields.FLAT)
        field = BW.Bitrix.data.fields.get(self.Fields.SUBDIVISION)
        self.subdivision = field.get_name_item(deal.get(self.Fields.SUBDIVISION)) if field else None
        field = BW.Bitrix.data.fields.get(self.Fields.DISTRICT)
        self.district = field.get_name_item(deal.get(self.Fields.DISTRICT)) if field else None
        self.order_big_photos = []

        terminal_change = deal.get(self.Fields.TERMINAL_CHANGE)
        # Нужен терминал
        if terminal_change == self.FilMapPay.NEED_TERMINAL:
            self.terminal_needed = True
        else:
            self.terminal_needed = False

        # Нужна сдача
        if terminal_change == self.FilMapPay.NEED_CHANGE:
            self.change_sum = deal.get(self.Fields.CHANGE_SUM)
        else:
            self.change_sum = None

        # Тот, кто отправил заказ
        self.sender_id = deal.get(self.Fields.SENDER_ID)
        self.sender = BW.BitrixUsers.fullname_by_bitrix_id(self.sender_id)

        # Источник
        self.source_id = deal.get(self.Fields.SOURCE_ID)
        self.order_or_form = deal.get(self.Fields.ORDER_OR_FORM)
        self.urgent_or_advance = deal.get(self.Fields.URGENT_OR_ADVANCE)
        self.sales_department = deal.get(self.Fields.SALES_DEPARTAMENT)

    @staticmethod
    def str_value(key, value):
        field: BW.Field = BW.Bitrix.data.fields.get(key)
        if field:
            for item in field.items:
                if item['ID'] == value:
                    return item['VALUE']

    def __repr__(self):
        text = ""
        for k, v in self.__dict__.items():
            text += f"{k}: {v}\n"
        return text

    @classmethod
    def build(cls, deal_id):
        result = BW.get_deal(deal_id)
        if result:
            return cls(result)

    def update(self):
        result = BW.get_deal(self.deal_id)
        self.__init__(result)
