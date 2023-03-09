import logging
from typing import List
from abc import ABC, abstractmethod

import telegram
from telegram import *

from source.bitrix.BitrixWorker import BitrixUsers
from source.handlers.WorkingDeal.Equip.UserData import UserData as EquipUserData
from source.handlers.WorkingDeal.Reserve.UserData import UserData as Reserve
from source.handlers.WorkingDeal.SetFlorist.UserData import UserData as FloristData
from source.handlers.WebCourier.Courier.UserData import UserData as CourierData
from source.handlers.WorkingDeal.SetCourier.UserData import UserData as SendData
from source.utils import Utils

from source.handlers.Approvement.UserData import UserData as FestiveData
from source.handlers.SearchDeals.UserData import Templates
from source.handlers.SearchDeals.UserData import ResultSearch
from source.handlers.ContactHandler.UserData import CreateContact
from source.handlers.CreateDeal.UserData import CreateDeal
from source.bitrix.Deal import Deal

logger = logging.getLogger(__name__)


class BaseUser(ABC):
    @abstractmethod
    def __init__(self):
        # Bitrix data
        self.phone_number = None
        self.bitrix_user_id = None

        # Telegram object
        self.tg_user: telegram.User = None
        self.mes_main: Message = None
        self.mes_media: List[Message] = []
        self.main_menu = None

        # any deal description
        self.deal = Deal({})

        # data of festive Approvement
        self.festive_data = FestiveData()

    def __str__(self):
        return str(self.__dict__)

    @abstractmethod
    def __getstate__(self):
        #TODO: сохранить фильтры
        return {
            'phone_number': self.phone_number,
            'bitrix_user_id': self.bitrix_user_id,
            'mes_main': self.mes_main,
            'mes_media': self.mes_media,
            'tg_user': self.tg_user,
        }

    @abstractmethod
    def __setstate__(self, pickled):
        # TODO: сохранить фильтры
        self.__init__()
        self.phone_number = pickled['phone_number']
        self.bitrix_user_id = pickled['bitrix_user_id']
        self.mes_main = pickled['mes_main']
        self.mes_media = pickled['mes_media']
        self.tg_user = pickled['tg_user']

    def send_message(self, text: str, reply_markup: InlineKeyboardMarkup = None, parse_mode=None):
        parse_mode = parse_mode if parse_mode else ParseMode.HTML
        self.tg_user.send_message(text, reply_markup=reply_markup, parse_mode=parse_mode)

    def del_mes_media(self):
        if self.mes_media:
            try:
                for mes in self.mes_media:
                    mes.delete()
            except Exception as err:
                logger.error(f"Message media not delete: {err}")
        self.mes_media = []

    def del_mes_main(self):
        if self.mes_main:
            try:
                self.mes_main.delete()
            except Exception as err:
                logger.error(f"Message main not delete: {err}")
        self.mes_main = None

    @abstractmethod
    def _clear_data(self):
        self.deal = None
        self.mes_main = None
        self.mes_media = None

    def restart(self, update, context):
        self._clear_data()
        return self.main_menu(update, context)

    @classmethod
    def build(cls, user_bitrix: dict, tg_user: telegram.User, main_menu):
        # Bitrix data
        new = cls()
        new.phone_number = Utils.prepare_phone_number(user_bitrix[BitrixUsers.ConstFields.MAIN_PHONE])
        new.bitrix_user_id = user_bitrix[BitrixUsers.ConstFields.ID]
        new.tg_user = tg_user
        new.main_menu = main_menu
        return new


class Operator(BaseUser):
    def __init__(self):
        super().__init__()

        # deal equipment (укомплектовать заказ)
        self.equip = EquipUserData()
        # deal send data (назначение курьера, перевод в доставке)
        self.send = SendData()
        # reserve (Обработать заказ)
        self.reserve = Reserve()
        # florist (Назначить флориста)
        self.florist = FloristData()
        # Templates filters
        self.templates = Templates()
        # Result SearchDeals
        self.search_deals = ResultSearch()

        self.create_contact = CreateContact()
        self.create_deal = CreateDeal()

    def __getstate__(self):
        return super().__getstate__()

    def __setstate__(self, pickled):
        self.__init__()
        super().__setstate__(pickled)

    def _clear_data(self):
        super()._clear_data()
        self.equip.clear()
        self.send.clear()
        self.reserve.clear()
        self.florist.clear()
        self.search_deals.clear()
        self.create_contact.clear()


class Florist(Operator):
    def __init__(self):
        super().__init__()

        # Set default template
        self.templates.selected.name = "Сделки на мне (Флорист)"
        self.templates.selected.filter_roles.append(Deal.Fields.FLORIST_NEW)
        self.templates.selected.filter_stage.extend([Deal.FilMapStage.IS_EQUIPPED, Deal.FilMapStage.FLORIST,
                                                    Deal.FilMapStage.PROCESSED_1C])

    def __getstate__(self):
        return super().__getstate__()

    def __setstate__(self, pickled):
        self.__init__()
        super().__setstate__(pickled)

    def _clear_data(self):
        super()._clear_data()
        self.florist_order.clear()


class Courier(BaseUser):
    def __init__(self):
        super().__init__()
        self.data = CourierData()

    def __getstate__(self):
        return super().__getstate__()

    def __setstate__(self, pickled):
        self.__init__()
        super().__setstate__(pickled)

    def _clear_data(self):
        super()._clear_data()
        self.data.clear()


class IntranetUser:
    pass