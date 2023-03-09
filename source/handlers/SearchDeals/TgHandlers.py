import datetime
import math

from telegram import *
from telegram.ext import *
import source.TelegramCommons as TgCommons

from source.bitrix.Deal import Deal
from source.Users import Operator
import source.bitrix.BitrixWorker as BW
from source.handlers.SearchDeals import BitrixHandler as BH
from source.utils.TelegramCalendar import TgCalendar
from source import config as cfg
from source.handlers.WorkingDeal.Start.TgHandler import WorkingDeal


class FiltersHandler:
    class Buttons:
        KEY_CATEGORY_ENTRY = "search_category_filter="
        KEY_FILTER = "search_filter="
        KEY_VALUE = "value="
        key_selected = "selected="
        CB_SPLITTER = "&&"

        cb_selected, text_selected = f"{key_selected}1", "🟢"
        cb_not_selected, text_not_selected = f"{key_selected}0", "🔘"

        SELECT_PATTERN = f"{KEY_FILTER}\\w+{CB_SPLITTER}{KEY_VALUE}.+{CB_SPLITTER}{key_selected}\\d"

        CB_STAGES = "stages"
        STAGE = InlineKeyboardButton("Фильтр по стадиям сделки", callback_data=f"{KEY_CATEGORY_ENTRY}{CB_STAGES}")
        CB_SUBDIVISIONS = "subdivisions"
        SUBDIVISION = InlineKeyboardButton("Фильтр по магазинам", callback_data=f"{KEY_CATEGORY_ENTRY}{CB_SUBDIVISIONS}")
        CB_DISTRICTS = "districts"
        DISTRICTS = InlineKeyboardButton("Фильтр по районам доставки", callback_data=f"{KEY_CATEGORY_ENTRY}{CB_DISTRICTS}")
        CB_PAYMENT_TYPE = "payment_type"
        PAYMENT_TYPE = InlineKeyboardButton("Фильтр по типу оплаты", callback_data=f"{KEY_CATEGORY_ENTRY}{CB_PAYMENT_TYPE}")
        CB_PAYMENT_METHOD = "payment_method"
        PAYMENT_METHOD = InlineKeyboardButton("Фильтр по методу оплаты", callback_data=f"{KEY_CATEGORY_ENTRY}{CB_PAYMENT_METHOD}")
        CB_ROLES = "roles"
        ROLES = InlineKeyboardButton("Фильтр по ролям", callback_data=f"{KEY_CATEGORY_ENTRY}{CB_ROLES}")

        CLEAR_PATTERN = f"{KEY_FILTER}\\w+{CB_SPLITTER}action=clear"
        CLEAR = InlineKeyboardButton("🔪 Очистить", callback_data=f"{KEY_FILTER}" + "{}" + CB_SPLITTER + "action=clear")

        PATTERN_ENTRY = f"{KEY_CATEGORY_ENTRY}({CB_STAGES}|{CB_SUBDIVISIONS}|{CB_DISTRICTS}|{CB_PAYMENT_TYPE}|" \
                        f"{CB_PAYMENT_METHOD}|{CB_ROLES})"

        def __init__(self, cancel_prev: InlineKeyboardButton):
            self.CANCEL_PREV = cancel_prev

        def generate_keyboard(self, filter_name, bitrix_filter, user_data):
            cb_filter = f"{self.KEY_FILTER}{filter_name}{self.CB_SPLITTER}"

            keyboard = InlineKeyboardMarkup([])
            for cb, name in bitrix_filter.items():
                if cb in user_data:
                    text = f"{self.text_selected} {name}"
                    cb_data = f"{cb_filter}{self.KEY_VALUE}{cb}{self.CB_SPLITTER}{self.cb_selected}"
                else:
                    text = f"{self.text_not_selected} {name}"
                    cb_data = f"{cb_filter}{self.KEY_VALUE}{cb}{self.CB_SPLITTER}{self.cb_not_selected}"
                keyboard.inline_keyboard.append([InlineKeyboardButton(text, callback_data=cb_data)])
            clear = InlineKeyboardButton(self.CLEAR.text, callback_data=self.CLEAR.callback_data.format(filter_name))
            if user_data:
                keyboard.inline_keyboard.append([clear])
            keyboard.inline_keyboard.append([self.CANCEL_PREV])
            return keyboard

    def __init__(self, cancel_prev: InlineKeyboardButton, dispatcher: Dispatcher):
        self.buttons = self.Buttons(cancel_prev)
        dispatcher.add_handler(CallbackQueryHandler(self.entry, pattern=self.buttons.PATTERN_ENTRY))
        dispatcher.add_handler(CallbackQueryHandler(self.handler_selected, pattern=self.buttons.SELECT_PATTERN))
        dispatcher.add_handler(CallbackQueryHandler(self.handler_action, pattern=self.buttons.CLEAR_PATTERN))

    def get_data_filter(self, name, user: Operator):
        bitrix_data, user_data = None, None
        if name == self.buttons.CB_STAGES:
            bitrix_data = BW.Bitrix.data.stages
            user_data = user.templates.selected.filter_stage
        elif name == self.buttons.CB_SUBDIVISIONS:
            bitrix_data = BW.Bitrix.data.subdivisions
            user_data = user.templates.selected.filter_subdivisions
        elif name == self.buttons.CB_DISTRICTS:
            bitrix_data = BW.Bitrix.data.districts
            user_data = user.templates.selected.filter_districts
        elif name == self.buttons.CB_PAYMENT_TYPE:
            bitrix_data = BW.Bitrix.data.payment_types
            user_data = user.templates.selected.filter_payment_type
        elif name == self.buttons.CB_PAYMENT_METHOD:
            bitrix_data = BW.Bitrix.data.payment_methods
            user_data = user.templates.selected.filter_payment_method
        elif name == self.buttons.CB_ROLES:
            bitrix_data = {Deal.Fields.ASSIGNED: "Я - Ответственный", Deal.Fields.FLORIST_NEW: "Я - Флорист",
                           Deal.Fields.RESERVE_HANDLER_ID: "Я - Обработал(-а) резерв/поставку",
                           Deal.Fields.EQUIPER_HANDLER_ID: "Я - Укомплектовал(-а) заказ",
                           Deal.Fields.SENDER_ID: "Я - Отправил(-а) заказ"}
            user_data = user.templates.selected.filter_roles
        return bitrix_data, user_data

    @TgCommons.pre_handler(access_user=Operator)
    def entry(self, update: Update, context, user: Operator):
        data = update.callback_query.data
        filter_name = data.split("=")[1]
        bitrix_data, user_data = self.get_data_filter(filter_name, user)
        text = "Выбирите необходимые фильтры."
        keyboard = self.buttons.generate_keyboard(filter_name, bitrix_data, user_data)
        update.callback_query.edit_message_text(text, reply_markup=keyboard)

    @TgCommons.pre_handler(access_user=Operator)
    def handler_selected(self, update: Update, context, user: Operator):
        data = update.callback_query.data
        filter_name, value, selected = data.split(self.buttons.CB_SPLITTER)
        filter_name = filter_name.split("=")[1]
        value = value.split("=")[1]

        bitrix_data, user_data = self.get_data_filter(filter_name, user)

        if selected == self.buttons.cb_selected:
            user_data.remove(value)
        else:
            user_data.append(value)

        text = update.callback_query.message.text
        keyboard = self.buttons.generate_keyboard(filter_name, bitrix_data, user_data)
        update.callback_query.edit_message_text(text, reply_markup=keyboard)

    @TgCommons.pre_handler(access_user=Operator)
    def handler_action(self, update, context, user):
        data = update.callback_query.data
        filter_name, action = data.split(self.buttons.CB_SPLITTER)
        value_filter_name = filter_name.split("=")[1]

        bitrix_data, user_data = self.get_data_filter(value_filter_name, user)

        if action in self.buttons.CLEAR.callback_data:
            user_data.clear()

        text = update.callback_query.message.text
        keyboard = self.buttons.generate_keyboard(value_filter_name, bitrix_data, user_data)
        update.callback_query.edit_message_text(text, reply_markup=keyboard)


class FilterDate:
    class Buttons:
        ENTRY = InlineKeyboardButton("Фильтр по дате создания", callback_data="filter_by_date")

        PATTERN_CALENDAR = "fil_create_date_cal_"
        PATTERN_CALENDAR_START = f"{PATTERN_CALENDAR}start"
        PATTERN_CALENDAR_END = f"{PATTERN_CALENDAR}end"
        PATTERN_CHANGE = "fil_change_create_date_"
        PATTERN_DEL = "fil_delete_create_date_"

        CHANGE_START = InlineKeyboardButton("✏ Изменить \"Дата от\"", callback_data=f"{PATTERN_CHANGE}start")
        DEL_START = InlineKeyboardButton("❌ Удалить \"Дата от\"", callback_data=f"{PATTERN_DEL}start")

        CHANGE_END = InlineKeyboardButton("✏ Изменить \"Дата до\"", callback_data=f"{PATTERN_CHANGE}end")
        DEL_END = InlineKeyboardButton("❌ Удалить \"Дата до\"", callback_data=f"{PATTERN_DEL}end")

        CANCEL_CURR = InlineKeyboardButton("Вернуться назад", callback_data="back_filter_date_menu")

        def __init__(self, cancel_prev: InlineKeyboardButton):
            self.CANCEL_PREV = cancel_prev

    def __init__(self, cancel_prev: InlineKeyboardButton, dispatcher: Dispatcher):
        self.buttons = self.Buttons(cancel_prev)

        other_keyboard = [[self.buttons.CANCEL_CURR]]
        self._calendar_start = TgCalendar(cb_prefix=self.buttons.PATTERN_CALENDAR_START, no_more_now=True,
                                          other_keyboard=other_keyboard)
        self._calendar_end = TgCalendar(cb_prefix=self.buttons.PATTERN_CALENDAR_END, no_more_now=True,
                                        other_keyboard=other_keyboard)

        dispatcher.add_handler(CallbackQueryHandler(self.entry, pattern=self.buttons.ENTRY.callback_data))
        dispatcher.add_handler(CallbackQueryHandler(self.calendar, pattern=self.buttons.PATTERN_CHANGE))
        dispatcher.add_handler(CallbackQueryHandler(self.handler_calendar, pattern=self.buttons.PATTERN_CALENDAR))
        dispatcher.add_handler(CallbackQueryHandler(self.delete, pattern=self.buttons.PATTERN_DEL))
        dispatcher.add_handler(CallbackQueryHandler(self.entry, pattern=self.buttons.CANCEL_CURR.callback_data))

    @TgCommons.pre_handler(access_user=Operator)
    def entry(self, update, context, user: Operator):
        date_start = user.templates.selected.filter_date.start
        date_end = user.templates.selected.filter_date.end
        text_empty = "🚫"

        keyboard = [[self.buttons.CHANGE_START], [self.buttons.CHANGE_END], [self.buttons.CANCEL_PREV]]

        if date_start:
            start_text = date_start.strftime('%Y-%m-%d %H:%M')
            keyboard[0].append(self.buttons.DEL_START)
        else:
            start_text = text_empty

        if date_end:
            end_text = date_end.strftime('%Y-%m-%d %H:%M')
            keyboard[1].append(self.buttons.DEL_END)
        else:
            end_text = text_empty

        text = f"📅 Фильтр по дате создания сделки\n\nДата от: {start_text}\nДата до: {end_text}"
        update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    @TgCommons.pre_handler(access_user=Operator)
    def calendar(self, update, context, user):
        data = update.callback_query.data
        text = "Выберите дату и время"

        if data == self.buttons.CHANGE_START.callback_data:
            keyboard = self._calendar_start.create_calendar()
        else:
            keyboard = self._calendar_end.create_calendar()

        update.callback_query.edit_message_text(text, reply_markup=keyboard)

    @TgCommons.pre_handler(access_user=Operator)
    def handler_calendar(self, update, context, user):
        data = update.callback_query.data

        if self.buttons.PATTERN_CALENDAR_START in data:
            cal = self._calendar_start
        else:
            cal = self._calendar_end

        result, dt = cal.process_selection(update, context)
        query = update.callback_query

        if result:
            if dt > datetime.datetime.now(tz=cfg.TIMEZONE):
                query.answer("Дата не может быть позднее чем сейчас")
                return
            elif self.buttons.PATTERN_CALENDAR_END in data:
                if user.templates.selected.filter_date.start and dt < user.templates.selected.filter_date.start:
                    query.answer("\"Дата до\" не может быть раньше чем \"Дата от\"")
                    return

            if self.buttons.PATTERN_CALENDAR_START in data:
                user.templates.selected.filter_date.start = dt
            else:
                user.templates.selected.filter_date.end = dt
            self.entry(update, context)
            return ConversationHandler.END

    @TgCommons.pre_handler(access_user=Operator)
    def delete(self, update, context, user: Operator):
        data = update.callback_query.data

        if data == self.buttons.DEL_START.callback_data:
            del user.templates.selected.filter_date.start
        else:
            del user.templates.selected.filter_date.end
        self.entry(update, context)


class SearchRender:
    class Buttons:
        SEARCH = InlineKeyboardButton("Поиск сделок 🔍", callback_data="search_deals_request")
        NEXT = InlineKeyboardButton("➡", callback_data="search_deals_result:next")
        BACK = InlineKeyboardButton("⬅", callback_data="search_deals_result:back")

        CB_DEAL = "search_deals_result:"
        PATTERN_DEAL = f"{CB_DEAL}\d+"

        CB_INFO = f"search_deals_result_info:"
        PATTERN_INFO = f"{CB_INFO}\d+"

        def __init__(self, cancel_prev):
            self.CANCEL_PREV = cancel_prev

    def __init__(self, cancel_prev: InlineKeyboardButton, cancel_func, dispatcher):
        self.buttons = self.Buttons(cancel_prev)
        dispatcher.add_handler(CallbackQueryHandler(self.search, pattern=self.buttons.SEARCH.callback_data))
        WorkingDeal.build_search_deals(self.buttons.PATTERN_DEAL, self.buttons.CANCEL_PREV, cancel_func, dispatcher)

    @TgCommons.pre_handler(access_user=Operator)
    def render(self, update: Update, context: CallbackContext, user: Operator):
        action = update.callback_query.data
        limit = 8
        total_pages = math.ceil(len(user.search_deals.deals) / limit)

        if action == self.buttons.NEXT.callback_data:
            user.search_deals.page += 1
        elif action == self.buttons.BACK.callback_data:
            user.search_deals.page += 1
        page = user.search_deals.page

        text = "Нажмите на номер сделки что бы начать с ней работу или " \
               f"нажмите на ℹ что бы посмотреть краткую информацию о сделке.\nСтраница {page+1} из {total_pages}"

        keyboard = []

        for deal in user.search_deals.deals[page*limit:(page+1)*limit]:
            keyboard.append([InlineKeyboardButton(deal.deal_id, callback_data=self.buttons.CB_DEAL + deal.deal_id),
                             InlineKeyboardButton("ℹ", callback_data=self.buttons.CB_INFO + deal.deal_id)])

        row = []
        if page > 0:
            row.append(self.buttons.BACK)
        if page < total_pages-1:
            row.append(self.buttons.NEXT)
        keyboard.append(row)
        keyboard.append([self.buttons.CANCEL_PREV])
        update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    @TgCommons.pre_handler(access_user=Operator)
    def search(self, update: Update, context: CallbackContext, user: Operator):
        deals = BH.get_deals(user)
        if not deals:
            update.callback_query.answer("Сделки не найдены!", show_alert=True)
            return

        if len(deals) == 50:
            update.callback_query.answer("Внимание! Найдено более 50 сделок, возможно стоит уточнить фильтры?",
                                         show_alert=True)

        user.search_deals.deals = [Deal(deal) for deal in deals]
        self.render(update, context)

    def deal_handler(self, update: Update, context: CallbackContext):
        pass


class TemplateHandler:
    class Buttons:
        ENTRY = InlineKeyboardButton("Найти сделки 🔍", callback_data="search_deals_by_filters")

        DATE = FilterDate.Buttons.ENTRY
        STAGE = FiltersHandler.Buttons.STAGE
        SUBDIVISION = FiltersHandler.Buttons.SUBDIVISION
        DISTRICTS = FiltersHandler.Buttons.DISTRICTS
        PAYMENT_TYPE = FiltersHandler.Buttons.PAYMENT_TYPE
        PAYMENT_METHOD = FiltersHandler.Buttons.PAYMENT_METHOD
        ROLES = FiltersHandler.Buttons.ROLES

        CREATE_TEMPLATE = InlineKeyboardButton("Создать 🧱", callback_data="create_template")
        RENAME_TEMPLATE = InlineKeyboardButton("Переименовать 🖋", callback_data="rename_template")

        CLEAR_TEMPLATE = InlineKeyboardButton("Очистить 🗑", callback_data="clear_template")
        DEL_TEMPLATE = InlineKeyboardButton("Удалить ☠", callback_data="delete_template")
        MY_TEMPLATES = InlineKeyboardButton("Мои шаблоны 📦", callback_data="my_templates")
        CANCEL_CURR = InlineKeyboardButton("Вернуться назад", callback_data="cancel_templates")

        CB_SEL_TEMPLATE = "select_template="
        CB_ENTRY = f"{ENTRY.callback_data}|{CANCEL_CURR.callback_data}"
        CB_NAME = f"{CREATE_TEMPLATE.callback_data}|{RENAME_TEMPLATE.callback_data}"

        def __init__(self, cancel_prev):
            self.CANCEL_PREV = cancel_prev

    class State:
        CREATE = 131
        RENAME = 132

    def __init__(self, cancel_prev: InlineKeyboardButton, dispatcher: Dispatcher):
        self.buttons = self.Buttons(cancel_prev)

        FiltersHandler(self.buttons.CANCEL_CURR, dispatcher)
        FilterDate(self.buttons.CANCEL_CURR, dispatcher)
        self.search = SearchRender(self.buttons.CANCEL_CURR, self.render_selected_template, dispatcher)

        dispatcher.add_handler(CallbackQueryHandler(self.render_selected_template, pattern=self.buttons.CB_ENTRY))
        dispatcher.add_handler(CallbackQueryHandler(self.my_templates, pattern=self.buttons.MY_TEMPLATES.callback_data))
        dispatcher.add_handler(CallbackQueryHandler(self.select_template, pattern=self.buttons.CB_SEL_TEMPLATE))
        dispatcher.add_handler(CallbackQueryHandler(self.delete_template,
                                                    pattern=self.buttons.DEL_TEMPLATE.callback_data))
        dispatcher.add_handler(CallbackQueryHandler(self.clear_template,
                                                    pattern=self.buttons.CLEAR_TEMPLATE.callback_data))
        dispatcher.add_handler(ConversationHandler(entry_points=[CallbackQueryHandler(self.request_name_template,
                                                                                      pattern=self.buttons.CB_NAME)],
                                                   states={self.State.CREATE: [MessageHandler(Filters.text,
                                                                                              self.create_template)],
                                                           self.State.RENAME: [MessageHandler(Filters.text,
                                                                                              self.rename_template)],
                                                           ConversationHandler.TIMEOUT:
                                                               [CallbackQueryHandler(self.render_selected_template)]},
                                                   fallbacks=[CallbackQueryHandler(self.render_selected_template,
                                                                                   pattern=self.buttons.CB_ENTRY)],
                                                   conversation_timeout=60)
                               )

    @TgCommons.pre_handler(access_user=Operator)
    def render_selected_template(self, update: Update, context: CallbackContext, user: Operator):
        curr = user.templates.selected
        keyboard = []
        text = f'Сейчас настроен ваш последний выбранный шаблон "{curr.name}".'

        text_state = "🟢 " if not curr.filter_date.empty else "🔘 "
        button_text = text_state + self.buttons.DATE.text
        keyboard.append([InlineKeyboardButton(button_text, callback_data=self.buttons.DATE.callback_data)])

        text_state = "🟢 " if curr.filter_stage else "🔘 "
        button_text = text_state + self.buttons.STAGE.text
        keyboard.append([InlineKeyboardButton(button_text, callback_data=self.buttons.STAGE.callback_data)])

        text_state = "🟢 " if curr.filter_subdivisions else "🔘 "
        button_text = text_state + self.buttons.SUBDIVISION.text
        keyboard.append([InlineKeyboardButton(button_text, callback_data=self.buttons.SUBDIVISION.callback_data)])

        text_state = "🟢 " if curr.filter_districts else "🔘 "
        button_text = text_state + self.buttons.DISTRICTS.text
        keyboard.append([InlineKeyboardButton(button_text, callback_data=self.buttons.DISTRICTS.callback_data)])

        text_state = "🟢 " if curr.filter_payment_type else "🔘 "
        button_text = text_state + self.buttons.PAYMENT_TYPE.text
        keyboard.append([InlineKeyboardButton(button_text, callback_data=self.buttons.PAYMENT_TYPE.callback_data)])

        text_state = "🟢 " if curr.filter_payment_method else "🔘 "
        button_text = text_state + self.buttons.PAYMENT_METHOD.text
        keyboard.append([InlineKeyboardButton(button_text, callback_data=self.buttons.PAYMENT_METHOD.callback_data)])

        text_state = "🟢 " if curr.filter_roles else "🔘 "
        button_text = text_state + self.buttons.ROLES.text
        keyboard.append([InlineKeyboardButton(button_text, callback_data=self.buttons.ROLES.callback_data)])

        my_template = InlineKeyboardButton(self.buttons.MY_TEMPLATES.text + str(len(user.templates.storage)),
                                           callback_data=self.buttons.MY_TEMPLATES.callback_data)

        keyboard.append([self.buttons.CLEAR_TEMPLATE, self.buttons.DEL_TEMPLATE])
        keyboard.append([self.buttons.RENAME_TEMPLATE, my_template])
        keyboard.append([self.search.buttons.SEARCH])
        keyboard.append([self.buttons.CANCEL_PREV])
        if update.callback_query:
            update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            user.mes_main.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    @TgCommons.pre_handler(access_user=Operator)
    def my_templates(self, update: Update, context: CallbackContext, user: Operator):
        keyboard = []
        storage = user.templates.storage
        for cb, fil in storage.items():
            keyboard.append([InlineKeyboardButton(fil.name, callback_data=self.buttons.CB_SEL_TEMPLATE + cb)])
        keyboard.append([self.buttons.CREATE_TEMPLATE])
        keyboard.append([self.buttons.CANCEL_CURR])
        update.callback_query.edit_message_text("Мои шаблоны", reply_markup=InlineKeyboardMarkup(keyboard))

    @TgCommons.pre_handler(access_user=Operator)
    def select_template(self, update: Update, context: CallbackContext, user: Operator):
        data = update.callback_query.data
        template_id = data.split("=")[1]
        user.templates.select(template_id)
        self.render_selected_template(update, context)

    @TgCommons.pre_handler(access_user=Operator)
    def clear_template(self, update: Update, context: CallbackContext, user: Operator):
        if not user.templates.selected.empty:
            user.templates.reset_selected()
            self.render_selected_template(update, context)
        else:
            update.callback_query.answer("У вас не выбраны фильтры, выбирите минимум один фильтр.", show_alert=True)

    @TgCommons.pre_handler(access_user=Operator)
    def delete_template(self, update: Update, context: CallbackContext, user: Operator):
        if len(user.templates) > 1:
            user.templates.delete()
            self.my_templates(update, context)
        else:
            update.callback_query.answer("Что бы удалить шаблон, у вас должно быть больше 1 шаблона.", show_alert=True)

    @TgCommons.pre_handler(access_user=Operator)
    def request_name_template(self, update: Update, context: CallbackContext, user: Operator):
        if len(user.templates) < 16:
            text = "Введите название шаблона (будет отображен на кнопке). Не более 30 символов."
            keyboard = InlineKeyboardMarkup([[self.buttons.CANCEL_CURR]])
            user.mes_main = update.callback_query.edit_message_text(text, reply_markup=keyboard)
            if update.callback_query.data == self.buttons.CREATE_TEMPLATE.callback_data:
                return self.State.CREATE
            else:
                return self.State.RENAME
        else:
            update.callback_query.answer("У вас слишком много шаблонов. Максимум - 15.", show_alert=True)

    @TgCommons.pre_handler(access_user=Operator)
    def rename_template(self, update: Update, context: CallbackContext, user: Operator):
        return self.handler_name(update, context, user, user.templates.rename)

    @TgCommons.pre_handler(access_user=Operator)
    def create_template(self, update: Update, context: CallbackContext, user: Operator):
        return self.handler_name(update, context, user, user.templates.create)

    @TgCommons.pre_handler(access_user=Operator, user_data=False)
    def handler_name(self, update: Update, context: CallbackContext, user: Operator, func):
        name = update.message.text
        update.message.delete()
        if len(name) < 31:
            func(name)
            self.render_selected_template(update, context)
            user.mes_main = None
            return ConversationHandler.END
        else:
            TgCommons.send_temp_message(update, "❗ Введено более 30 символов")



