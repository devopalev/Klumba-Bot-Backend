import re
from abc import ABC, abstractmethod
from typing import List

from telegram import *
from telegram.ext import *
import source.TelegramCommons as TgCommons

from source.Users import BaseUser, Operator
from source.handlers.CreateDeal import BitrixHandler as BH
from source.bitrix import BitrixWorker as BW
from source.bitrix.Deal import Deal
from source.bitrix.Contact import Contact
# from source.handlers.ContactHandler.TgHandlers import CreateContact


# TODO: Что нужно для создания сделки
# 1. Контакт клиента (найти или создать)
# 2. Источник (выбрать из текущих)
# 3. ОК Заказ или заявка(школа, горшечка, фитодиз, свадебное оформ)?
# 4. ОК Срочный/Заблаговременный
# 5. ОК Отдел продаж (Подразделение - продавец)
# 6. Кто принял заказ? (человек, НЕ учетка магазина)
# 7. Что заказано


def render_text(user: Operator):
    emj_curr = "▶"
    emj_wait = "☑"
    emj_done = "✅"
    curr = True
    text = "Этапы создания сделки:"
    if user.create_deal.contact:
        text += f"\n{emj_done} <b>Контакт:</b> {user.create_deal.contact.fullname}"
    else:
        text += f"\n{emj_curr} <b>Контакт:</b> Выберите контакт сделки на клавиатуре."
        curr = False

    if user.create_deal.source:
        text += f"\n{emj_done} <b>Источник:</b> {user.create_deal.contact.source}."
    else:
        if curr:
            text += f"\n{emj_curr} <b>Источник:</b> Выбирите источник сделки."
            curr = False
        else:
            text += f"\n{emj_wait} <b>Источник:</b> 🧸"

    if user.create_deal.order_or_form:
        text += f"\n{emj_done} <b>Заказ или заявка:</b> {user.create_deal.contact.order_or_form}."
    else:
        if curr:
            text += f"\n{emj_curr} <b>Заказ или заявка:</b> Выбирите тип сделки."
            curr = False
        else:
            text += f"\n{emj_wait} <b>Заказ или заявка:</b> 🧸"

    if user.create_deal.urgent_or_advance:
        text += f"\n{emj_done} <b>Срочный/Заблаговременный:</b> {user.create_deal.contact.urgent_or_advance}."
    else:
        if curr:
            text += f"\n{emj_curr} <b>Срочный/Заблаговременный:</b> Выбирите срочность сделки."
            curr = False
        else:
            text += f"\n{emj_wait} <b>Срочный/Заблаговременный:</b> 🧸"

    if user.create_deal.sales_department:
        text += f"\n{emj_done} <b>Отдел продаж:</b> {user.create_deal.contact.sales_department}."
    else:
        if curr:
            text += f"\n{emj_curr} <b>Отдел продаж:</b> Выбирите отдел продаж"
            curr = False
        else:
            text += f"\n{emj_wait} <b>Отдел продаж:</b> 🧸"

    if user.create_deal.order_contents:
        text += f"\n{emj_done} <b>Что заказано:</b> {user.create_deal.contact.order_contents}."
    else:
        if curr:
            text += f"\n{emj_curr} <b>Что заказано:</b> Напишите что заказано"
        else:
            text += f"\n{emj_wait} <b>Что заказано:</b> 🧸"
    return text


class Source:
    access = BaseUser

    def __init__(self):
        self.base_cb = "CreateDeal:Source:"
        self.handler = CallbackQueryHandler(self.processing, pattern=self.base_cb)

    @TgCommons.pre_handler(access_user=access)
    def create_keyboard(self):
        example = {'79066213885': '[РОЗНИЦА] (пришли в магазин ногами)', 'CALL': '[ЗВОНОК]',
                   'STORE': '[САЙТ KLUMBA71.ru] Интернет-магазин (не проставлять)',
                   '79066213913': '[ЮЛЯ] - с ее инсты, обращений. Сервис клауд, ост',
                   '79066213908': '[КОРПЫ] - Тендеры, Дума, Правительство, Госуха',
                   'SELF': '[ОБРАТИЛИСЬ ЛИЧНО К СОТРУДНИКУ КЛУМБЫ]',
                   '9606198454': '[KLUMBA] 9606198454 (моб тел клумба)',
                   'EMPLOYEE': '[СОТРУДНИК КЛУМБЫ] - является покупателем', '79066213900': '[Партнеры] - Флоувоу',
                   '9674317205': '9674317205', '79674317205': '79674317205',
                   '79066213899': '[Партнеры] - Русский букет', '79636236615': '79636236615',
                   '79674317266': '79674317266',
                   '39|TELEGRAM_UNLIM': 'Telegram - [KLUMBA] - Telegram',
                   '39|TELEGRAM': 'Telegram - [KLUMBA] - Telegram',
                   '3|OLCHAT_WA_CONNECTOR_2': '[OLChat] WhatsApp - АРХИВНАЯ (Открытая линия доставки)',
                   '37|OLCHAT_WA_CONNECTOR_2': '[OLChat] WhatsApp - [KLUMBA] - WHATSAPP ОБЩИЙ +79051129113',
                   '79652420419': '79652420419', '9674317233': '9674317233',
                   '37|WAAPP_REDHAM': 'WhatsApp - [KLUMBA] - WHATSAPP ОБЩИЙ +79051129113',
                   '79066213901': '[Партнеры] - Киберфлорист', '37|WAAPP': 'waApp - Открытая линия 19',
                   '79066213898': '[Партнеры] - Эдельвейс', '79066213904': '[Партнеры] - Интерфлора',
                   '79066213902': '[Партнеры] - Флора-экспресс', '79066213905': '[Партнеры] - Киберфлора',
                   '79066213906': '[Партнеры] - Грандфлора', '79066213912': '[Партнеры] - UFL',
                   '2|TELEGRAM': 'Telegram - Ландшафт(отк.линия)', 'CALLBACK': '[KLUMBA] - Обратный звонок',
                   '79066213891': '[KLUMBA] - insta klumba_delivery',
                   '79066213887': '[KLUMBA] - Whatsapp (ПЕРВЫЙ) +7(960)-619-84-54',
                   '79066213893': '[KLUMBA] - Whatsapp (ВТОРОЙ) +7(961)-145-01-66', '79066213890': '[KLUMBA] - vk',
                   '79066213896': '[KLUMBA] - чат на сайте klumba71.ru',
                   '35|NOTIFICATIONS': '[KLUMBA] - sms/wa (by b24)-  Битрикс24 СМС и WhatsApp',
                   '29|NOTIFICATIONS': '[KLUMBA] Битрикс24 СМС и WhatsApp', 'WEBFORM': '[KLUMBA] CRM-форма(с сайта?)',
                   '79066213881': 'Виджет сайта klumba71.ru', '79066213909': '[CVETYVTULE] - avito',
                   '9611450166': '[tel] 9611450166  (моб тел цв.в туле)', '79066213897': '[WORKSHOP] - inst 1.0',
                   '79066213910': '[WORKSHOP] - Inst 2.0',
                   '79066213911': '[WORKSHOP] WA [9056263396] - Вероника Шавохина',
                   '9056263396': '[tel] 9056263396 (моб тел. WORKSHOP)',
                   '79066213914': '[9622769990] - Илья - Ландшафт WA',
                   '79066213883': '[OPT-CVETY.RU] ФОРМА Оптовый Лендинг',
                   '9|OPENLINE': '[OPT-CVETY.RU] -Онлайн-чат - Открытая линия для', 'RC_GENERATOR': 'Генератор продаж',
                   '74991105735': '74991105735', '79066213907': 'корпы архив', '9066213879': '[tel] - Тургеневская',
                   '3|PACT_WHATSAPP_CONNECTOR_40723': 'pact_whatsapp_connector_40723 - АРХИВНАЯ (Открытая линия доставки)',
                   'UC_OVUYJJ': 'Рекламация', '79652420420': '[ЗВОНОК/Клумба/717266(2gis)]',
                   '9622787828': '[МОРЕ ЦВЕТОВ] +7(962)278-78-28',
                   '9674317206': '[МОРЕ ЦВЕТОВ] +7(967)431-72-06(71-72-06)', '49|VK': '[МОРЕ ЦВЕТОВ] - VK',
                   '45|AVITO': '[МОРЕ ЦВЕТОВ] - AVITO', '79066213892': '[МОРЕ ЦВЕТОВ] - Инстаграм-Директ',
                   '79066213915': '[МОРЕ ЦВЕТОВ] Whatsapp +7962-278-78-28',
                   '79652420421': '[МОРЕ ЦВЕТОВ] WA +7(905)112-91-54',
                   'UC_WXZAOE': '[МОРЕ ЦВЕТОВ] Розница (пришли в магазин ногами)',
                   'UC_Q1XYM0': '[МОРЕ ЦВЕТОВ] Интернет-магазин', 'UC_YT0KP4': 'Соня',
                   'UC_5MH4OE': 'CRM-форма Анкета соискателя (HR)', '79652420422': 'Sberlead',
                   '79674317267': 'WhatsApp - [KLUMBA] - WHATSAPP Рассылка'}

        keyboard = InlineKeyboardMarkup([x for x in BH.source])

    def processing(self):
        pass


class OrderOrForm:
    access = BaseUser

    def __init__(self, base_cb, other_buttons=None, exit_func=None):
        if other_buttons is None:
            other_buttons = []
        self.base_cb = f"{base_cb}:OrderOrForm:"
        self.handler = CallbackQueryHandler(self.processing, pattern=self.base_cb)
        self.other_buttons = other_buttons
        self.exit_func = exit_func

    def create_keyboard(self):
        field: BW.Field = BW.Bitrix.data.fields.get(Deal.Fields.ORDER_OR_FORM)
        if field:
            keyboard = [[InlineKeyboardButton(item['VALUE'], callback_data=self.base_cb + item['ID'])]
                        for item in field.items]
            keyboard.extend([[btn] for btn in self.other_buttons])
            return InlineKeyboardMarkup(keyboard)

    @TgCommons.pre_handler(access_user=access)
    def entry(self, update: Update, context: CallbackContext, user: BaseUser):
        keyboard = self.create_keyboard()
        text = "Заказ или заявка?"
        update.callback_query.message.edit_text(text, reply_markup=keyboard)

    @TgCommons.pre_handler(access_user=access)
    def processing(self, update: Update, context: CallbackContext, user: BaseUser):
        selected = update.callback_query.data.split(':')[2]
        user.deal.order_or_form = selected

        if self.exit_func:
            self.exit_func(update, context)


class UrgentOrAdvance:
    access = BaseUser

    def __init__(self, base_cb, other_buttons=None, exit_func=None):
        if other_buttons is None:
            other_buttons = []
        self.base_cb = f"{base_cb}:UrgentOrAdvance:"
        self.handler = CallbackQueryHandler(self.processing, pattern=self.base_cb)
        self.other_buttons = other_buttons
        self.exit_func = exit_func

    def create_keyboard(self):
        field: BW.Field = BW.Bitrix.data.fields.get(Deal.Fields.URGENT_OR_ADVANCE)
        if field:
            keyboard = [[InlineKeyboardButton(item['VALUE'], callback_data=self.base_cb + item['ID'])]
                        for item in field.items]
            keyboard.extend([[btn] for btn in self.other_buttons])
            return InlineKeyboardMarkup(keyboard)

    @TgCommons.pre_handler(access_user=access)
    def entry(self, update: Update, context: CallbackContext, user: BaseUser):
        keyboard = self.create_keyboard()
        text = "Срочный или заблаговременный?"
        update.callback_query.message.edit_text(text, reply_markup=keyboard)

    @TgCommons.pre_handler(access_user=access)
    def processing(self, update: Update, context: CallbackContext, user: BaseUser):
        selected = update.callback_query.data.split(':')[2]
        user.deal.urgent_or_advance = selected

        if self.exit_func:
            self.exit_func(update, context)


class SalesDepartament:
    access = BaseUser

    def __init__(self, base_cb, other_buttons=None, exit_func=None):
        if other_buttons is None:
            other_buttons = []
        self.base_cb = f"{base_cb}:SalesDepartament:"
        self.handler = CallbackQueryHandler(self.processing, pattern=self.base_cb)
        self.other_buttons = other_buttons
        self.exit_func = exit_func

    def create_keyboard(self):
        field: BW.Field = BW.Bitrix.data.fields.get(Deal.Fields.SALES_DEPARTAMENT)
        if field:
            keyboard = [[InlineKeyboardButton(item['VALUE'], callback_data=self.base_cb + item['ID'])]
                        for item in field.items]
            keyboard.extend([[btn] for btn in self.other_buttons])
            return InlineKeyboardMarkup(keyboard)

    @TgCommons.pre_handler(access_user=access)
    def entry(self, update: Update, context: CallbackContext, user: BaseUser):
        keyboard = self.create_keyboard()
        text = "Выбирите отдел продаж"
        update.callback_query.message.edit_text(text, reply_markup=keyboard)

    @TgCommons.pre_handler(access_user=access)
    def processing(self, update: Update, context: CallbackContext, user: BaseUser):
        selected = update.callback_query.data.split(':')[2]
        user.deal.sales_department = selected

        if self.exit_func:
            self.exit_func(update, context)


# TODO: Доделать логику создания сделок
class CreateDeal:
    class Buttons:
        ENTRY = InlineKeyboardButton("Создать сделку 🐣", callback_data="create_deal")
        CHANGE_SOURCE = InlineKeyboardButton("Изменить источник")
        CB_CONTACT = "bitrix_contact:"
        CB_SOURCE = "CreateDeal:Source:"

        def __init__(self, cancel):
            self.CANCEL = InlineKeyboardButton("Вернуться назад")

    class State:
        WAITING_CONTACT = 410

    access = BaseUser

    def __init__(self, cancel):
        self.buttons = self.Buttons(cancel)
        self.base_cb = "CreateDeal"
        # Отрабатывают снизу -> вверх из за exit function
        sales_departament = SalesDepartament(self.base_cb, exit_func=None)
        urgent_or_advance = UrgentOrAdvance(self.base_cb, exit_func=sales_departament.entry)
        order_or_form = OrderOrForm(self.base_cb, exit_func=urgent_or_advance.entry)

        self.cv_handler = ConversationHandler(entry_points=[],
                                              states={},
                                              fallbacks=[])

    @TgCommons.pre_handler(access_user=access)
    def source(self):
        source = BH.source

    @TgCommons.pre_handler(access_user=access)
    def type_deal(self):
        pass

    @TgCommons.pre_handler(access_user=access)
    def emergency(self):
        pass

    @TgCommons.pre_handler(access_user=access)
    def sales_department(self):
        pass

    @TgCommons.pre_handler(access_user=access)
    def order_received_by(self):
        pass

    @TgCommons.pre_handler(access_user=access)
    def order_contents(self):
        pass

    @TgCommons.pre_handler(access_user=access)
    def callback_handler(self):
        pass

    @TgCommons.pre_handler(access_user=access)
    def handler(self, update: Update, context: CallbackContext, user):
        pass
