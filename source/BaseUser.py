from source.DealData import DealData
from source.State import State
from source.festive_approvement.UserData import UserData as FestiveData


class BaseUser:
    def __init__(self):
        self.phone_number = None
        self.bitrix_user_id = None
        self.state = State.LOGIN_REQUESTED
        self.tg_user = None

        # any deal description
        self.deal_data = DealData()

        # data of festive approvement
        self.festive_data = FestiveData()

    def __getstate__(self):
        return {
            'phone_number': self.phone_number,
            'bitrix_user_id': self.bitrix_user_id
        }

    def __setstate__(self, pickled):
        self.__init__()

        self.phone_number = pickled['phone_number']
        self.bitrix_user_id = pickled['bitrix_user_id']

    def _clear_data(self):
        self.deal_data = DealData()

    def restart(self, update, context):
        return State.LOGIN_REQUESTED
