import datetime

from telegram.ext import Dispatcher
from source.config import USER_PERSISTENT_KEY
from source.handlers.WebCourier import BitrixHandler as BH
from source.bitrix.Deal import Deal
from source.web_app.Tasks import TaskCourierDealsToday, TaskCourierDealsTomorrow, TaskCourier, TaskCourierDealsEarly, \
    TaskCourierDealDone, TaskCourierDealReturn
import logging

logger = logging.getLogger(__name__)


class WebHandlerCourier:
    def __init__(self, dispatcher: Dispatcher):
        self.dispatcher = dispatcher

    def search_user(self, telegram_id):
        user_data = self.dispatcher.user_data.get(int(telegram_id))
        if user_data:
            return user_data.get(USER_PERSISTENT_KEY)

    def get_deals(self, task, date):
        if task.telegram_id:
            user = self.search_user(task.telegram_id)
            if user:
                task.result = transform_deals(BH.get_deals(user, date))
                return task
            else:
                logger.warning(f"Курьер не найден, API: {task}")

    def handler(self, task: TaskCourier):
        if isinstance(task, TaskCourierDealsToday):
            return self.get_deals(task, datetime.datetime.now().strftime('%Y-%m-%d'))
        elif isinstance(task, TaskCourierDealsTomorrow):
            return self.get_deals(task, (datetime.datetime.now() + datetime.timedelta(days=1)).strftime('%Y-%m-%d'))
        elif isinstance(task, TaskCourierDealsEarly):
            return self.get_deals(task, None)
        elif isinstance(task, TaskCourierDealDone):
            pass  #TODO
        elif isinstance(task, TaskCourierDealReturn):
            pass  #TODO
        else:
            task.result = {"error": "action unavailable"}
            logger.warning(f"Неизвестное задание курьера от API: {task}")
            return task


def transform_deals(deals):
    new_deals = []
    for deal in deals:
        deal = Deal(deal)
        new_deal = {Deal.Fields.ID: deal.deal_id}
        terminal = 'Терминал: НУЖЕН\n' if deal.terminal_needed else ""
        change_sum = f"Сдача с: {deal.change_sum}\n" if deal.change_sum else ""
        description = f"№ заказа: {deal.deal_id}\n" \
                      f"Время: {deal.time}\n" \
                      f"Дата: {deal.date}\n" \
                      f"Адрес: {deal.address}\n" \
                      f"Квартира: {deal.flat}\n" \
                      f"Имя получателя: {deal.recipient_name}\n" \
                      f"Телефон получателя: {deal.recipient_phone}\n" \
                      f"Район: {deal.district}\n" \
                      f"Комментарий по доставке: {deal.delivery_comment}\n\n" \
                      f"Инкогнито: {deal.incognito}\n\n" \
                      + terminal \
                      + change_sum \
                      + f"К оплате: {deal.to_pay}\n" \
                        f"Подразделение: {deal.subdivision}\n" \
                        f"Кто отправил заказ: {deal.sender}\n" \
                        f"Телефон заказчика (если получатель не отвечает): {deal.contact_phone}"

        new_deal['text'] = description
        new_deals.append(new_deal)
    return new_deals
