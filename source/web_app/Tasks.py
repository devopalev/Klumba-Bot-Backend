import pickle


class Task:
    action_ping = "ping"
    action_pong = "pong"

    def __init__(self, action, params=None, task_id=None):
        self.id = task_id
        self.action = action
        self.params = params
        self.result = None

    def __repr__(self):
        return str(self.__dict__)

    def dumps(self):
        return pickle.dumps(self)

    @property
    def this_ping(self):
        return self.action == self.action_ping

    @property
    def this_pong(self):
        return self.action == self.action_pong


class TaskEventUser(Task):
    def __init__(self, bitrix_id, text):
        self.action = "event_user"
        self.bitrix_id = bitrix_id
        self.text = text
        super().__init__(self.action)


class TaskCourier(Task):
    pass


class TaskCourierDealsToday(TaskCourier):
    def __init__(self, telegram_id):
        self.action = "courier_deals_today"
        self.telegram_id = telegram_id
        super().__init__(self.action)


class TaskCourierDealsTomorrow(TaskCourier):
    def __init__(self, telegram_id):
        self.action = "courier_deals_tomorrow"
        self.telegram_id = telegram_id
        super().__init__(self.action)


class TaskCourierDealsEarly(TaskCourier):
    def __init__(self, telegram_id):
        self.action = "courier_deals_early"
        self.telegram_id = telegram_id
        super().__init__(self.action)


class TaskCourierDealDone(TaskCourier):
    def __init__(self, telegram_id, deal_id):
        self.action = "deal_done"
        self.deal_id = deal_id
        self.telegram_id = telegram_id
        super().__init__(self.action)


class TaskCourierDealReturn(TaskCourier):
    def __init__(self, telegram_id, deal_id, comment):
        self.action = "deal_done"
        self.deal_id = deal_id
        self.comment = comment
        self.telegram_id = telegram_id
        super().__init__(self.action)