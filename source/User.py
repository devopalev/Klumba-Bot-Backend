import logging

import source.Restarter as Restarter
import source.StorageWorker as StorageWorker
from source.BaseUser import BaseUser
from source.State import State
from source.cmd_handlers.Equip.UserData import UserData as EquipUserData
from source.cmd_handlers.FloristOrder.UserData import UserData as FloristOrder
from source.cmd_handlers.Reserve.UserData import UserData as Reserve
from source.cmd_handlers.SetFlorist.UserData import UserData as Florist
from source.cmd_handlers.Courier.UserData import UserData as CourierData
from source.cmd_handlers.Send.UserData import UserData as SendData

logger = logging.getLogger(__name__)


class Operator(BaseUser):
    def __init__(self):
        super().__init__()

        # deal equipment (укомплектовать заказ)
        self.equip = EquipUserData()
        # deal send data (назначение курьера, перевод в доставке)
        self.send = SendData()
        # step 5(florist orders listing)
        self.florist_order = FloristOrder()
        # reserve (Обработать заказ)
        self.reserve = Reserve()
        # florist (Назначить флориста)
        self.florist = Florist()

    def __getstate__(self):
        return super().__getstate__()

    def __setstate__(self, pickled):
        self.__init__()
        super().__setstate__(pickled)

        authorized = StorageWorker.check_authorization(self)
        self.state = State.IN_OPERATOR_MENU if authorized else State.LOGIN_REQUESTED

    @classmethod
    def from_base(cls, baseuser: BaseUser, tg_user):
        new = cls()
        new.phone_number = baseuser.phone_number
        new.bitrix_user_id = baseuser.bitrix_user_id
        new.state = baseuser.state
        new.tg_user = tg_user

        return new

    def _clear_data(self):
        super()._clear_data()
        self.equip.clear()
        self.send.clear()
        self.florist_order.clear()
        self.reserve.clear()
        self.florist.clear()

    def restart(self, update, context):
        self._clear_data()
        return Restarter.restart_operator(update, context)


class Courier(BaseUser):
    def __init__(self):
        super().__init__()
        self.data = CourierData()

    def __getstate__(self):
        return super().__getstate__()

    def __setstate__(self, pickled):
        self.__init__()
        super().__setstate__(pickled)

        authorized = StorageWorker.check_authorization(self)
        self.state = State.IN_COURIER_MENU if authorized else State.LOGIN_REQUESTED

    @classmethod
    def from_base(cls, baseuser: BaseUser, tg_user):
        new = cls()
        new.phone_number = baseuser.phone_number
        new.bitrix_user_id = baseuser.bitrix_user_id
        new.state = baseuser.state
        new.tg_user = tg_user

        return new

    def _clear_data(self):
        super()._clear_data()
        self.data.clear()

    def restart(self, update, context):
        self._clear_data()
        return Restarter.restart_courier(update, context)





