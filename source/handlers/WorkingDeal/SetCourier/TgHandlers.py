import logging
import math
from typing import Tuple

from telegram.ext import MessageHandler, Filters, CallbackContext, \
    ConversationHandler, CallbackQueryHandler

from telegram import InlineKeyboardButton, Update, InlineKeyboardMarkup, ParseMode

from source.Users import Operator
import source.utils.Utils as Utils
import source.bitrix.BitrixWorker as BW
import source.TelegramCommons as TgCommons
import source.handlers.WorkingDeal.SetCourier.BitrixHandlers as BH

logger = logging.getLogger(__name__)


class AssignCourier:
    class _State:
        CHANGE = 140
        SEARCH = 141

        def __init__(self, finish):
            self.FINISH = finish

    class Buttons:
        ENTRY = InlineKeyboardButton("Назначить курьера (заранее) 👨‍🦼", callback_data="deal_courier")

        CHANGE_COURIER = InlineKeyboardButton("Изменить", callback_data="change_courier")
        SHOW_ALL = InlineKeyboardButton('Показать весь список', callback_data='show_all')

        PREV = InlineKeyboardButton("<", callback_data="prev_page")
        NEXT = InlineKeyboardButton(">", callback_data="next_page")

        PATTERN_CHOOSE = r'^(\d+)$'

        def __init__(self, cancel_prev: InlineKeyboardButton, cancel_general: InlineKeyboardButton):
            self.CANCEL_PREV = cancel_prev
            self.CANCEL_GENERAL = cancel_general

    def __init__(self, fallbacks: list, map_to_parent: dict, state_finish: int,
                 button_cancel_prev: InlineKeyboardButton, button_cancel_general: InlineKeyboardButton,
                 timeout: int):
        self._buttons = self.Buttons(button_cancel_prev, button_cancel_general)
        self._state = self._State(state_finish)

        self.cv_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.check_courier, pattern=self._buttons.ENTRY.callback_data)],
            states={self._state.CHANGE: [CallbackQueryHandler(self.send_couriers_header,
                                                              pattern=self._buttons.CHANGE_COURIER.callback_data)],
                    self._state.SEARCH: [MessageHandler(Filters.text, self.search_courier_by_surname),
                                         CallbackQueryHandler(self.show_all,
                                                              pattern=self._buttons.SHOW_ALL.callback_data),
                                         CallbackQueryHandler(callback=self.choose_courier,
                                                              pattern=self._buttons.PATTERN_CHOOSE),
                                         CallbackQueryHandler(self.next_page,
                                                              pattern=self._buttons.NEXT.callback_data),
                                         CallbackQueryHandler(self.prev_page,
                                                              pattern=self._buttons.PREV.callback_data)
                                         ]},
            fallbacks=fallbacks,
            map_to_parent=map_to_parent,
            conversation_timeout=timeout)

    @TgCommons.pre_handler(access_user=Operator)
    def check_courier(self, update: Update, context, user: Operator):
        if user.deal.stage_name != user.deal.FilMapStage.APPROVED:
            text = 'Заказ должен находиться в стадии "Согласовано".\nИзмените стадию заказа и попробуйте снова.'
            update.callback_query.answer(text, show_alert=True)
            return None

        if user.deal.courier_id:
            name = BW.BitrixUsers.fullname_by_bitrix_id(user.deal.courier_id)
            text = f"Курьер <b>{name}</b> уже назначен на заказ <b>{user.deal.deal_id}</b>."

            keyboard = InlineKeyboardMarkup([[self._buttons.CHANGE_COURIER],
                                             [self._buttons.CANCEL_PREV]])
            update.callback_query.edit_message_text(text, ParseMode.HTML, reply_markup=keyboard,
                                                    disable_web_page_preview=True)
            return self._state.CHANGE
        else:
            return self.send_couriers_header(update, context)

    @TgCommons.pre_handler(access_user=Operator)
    def send_couriers_header(self, update: Update, context, user):
        user.mes_main = update.callback_query.message
        text = f'Заказ *{user.deal.deal_id}*\n' \
               f'Выбран курьер: *{BW.BitrixUsers.fullname_by_bitrix_id(user.deal.courier_id)}*\n' \
               f'Тип оплаты: {user.deal.payment_type}\n' \
               "<b>Терминал:</b> НУЖЕН" if user.deal.terminal_needed else '' \
               f"<b>Сдача с:</b> {user.deal.change_sum}" if user.deal.change_sum else '' \
               f'К оплате: {user.deal.to_pay}\n\n' \
               '<b>ВВЕДИТЕ НАЧАЛО ФАМИЛИИ КУРЬЕРА:</b>'

        keyboard = InlineKeyboardMarkup([[self._buttons.SHOW_ALL], [self._buttons.CANCEL_PREV]])
        update.callback_query.edit_message_text(text, ParseMode.HTML, reply_markup=keyboard)
        return self._state.SEARCH

    def render_cur_page(self, user: Operator) -> Tuple[str, InlineKeyboardMarkup]:
        couriers_num = len(user.send.couriers)
        page_number = user.send.page_number
        user.send.total_pages = math.ceil(couriers_num / user.send.COURIERS_PER_PAGE)

        if user.send.courier_search_surname:
            text = f"Курьеры с фамилией на <b>{user.send.courier_search_surname}</b>"
        else:
            text = "📌 Курьеры\n\n"

        if user.send.total_pages > 1:
            text += f'Страница {page_number + 1} из {user.send.total_pages}\n\n'

        couriers_tuples = list(user.send.couriers.items())
        page = couriers_tuples[page_number * user.send.COURIERS_PER_PAGE:
                               (page_number + 1) * user.send.COURIERS_PER_PAGE]

        keyboard = []

        for bitrix_id, p_data in page:
            fullname = f"{p_data[BW.BitrixUsers.ConstFields.SURNAME]} {p_data[BW.BitrixUsers.ConstFields.NAME]}"
            keyboard.append([InlineKeyboardButton(fullname, callback_data=bitrix_id)])

        if page_number > 0:
            keyboard.append([self._buttons.PREV])

        if page_number < user.send.total_pages - 1:
            if page_number > 0:  # if prev page button has been added
                keyboard[-1].append(self._buttons.NEXT)
            else:
                keyboard.append([self._buttons.NEXT])

        keyboard.append([self._buttons.CANCEL_PREV])
        return text, InlineKeyboardMarkup(keyboard)

    @TgCommons.pre_handler(access_user=Operator)
    def show_all(self, update: Update, context: CallbackContext, user: Operator):
        result = BW.BitrixUsers.get_couriers()
        user.send.page_number = 0
        user.send.couriers = result
        text, keyboard = self.render_cur_page(user)
        update.callback_query.edit_message_text(text, ParseMode.HTML, reply_markup=keyboard)
        return self._state.SEARCH

    @TgCommons.pre_handler(access_user=Operator)
    def search_courier_by_surname(self, update: Update, context: CallbackContext, user: Operator):
        search_surname = update.message.text
        update.message.delete()
        user.send.courier_search_surname = Utils.prepare_str(search_surname)

        result = BW.BitrixUsers.get_couriers(search_surname=search_surname)
        if result:
            user.send.page_number = 0
            user.send.couriers = result

            text, keyboard = self.render_cur_page(user)
            user.mes_main.edit_text(text, ParseMode.HTML, reply_markup=keyboard)
            return self._state.SEARCH
        else:
            text = f"Не нашел курьеров фамилия которых начинается на \"{search_surname}\". Попробуй ещё раз или " \
                   f"вернись в предыдущее меню."
            keyboard = InlineKeyboardMarkup([[self._buttons.SHOW_ALL], [self._buttons.CANCEL_PREV]])
            user.mes_main.edit_text(text, reply_markup=keyboard)

    @TgCommons.pre_handler(access_user=Operator)
    def next_page(self, update: Update, context: CallbackContext, user: Operator):
        page_number = user.send.page_number

        if page_number < user.send.total_pages - 1:
            user.send.page_number += 1
            text, keyboard = self.render_cur_page(user)
            update.callback_query.edit_message_text(text, ParseMode.HTML, reply_markup=keyboard)
        return self._state.SEARCH

    @TgCommons.pre_handler(access_user=Operator)
    def prev_page(self, update: Update, context: CallbackContext, user: Operator):
        page_number = user.send.page_number

        if page_number > 0:
            user.send.page_number -= 1
            text, keyboard = self.render_cur_page(user)
            update.callback_query.edit_message_text(text, ParseMode.HTML, reply_markup=keyboard)

        return self._state.SEARCH

    @TgCommons.pre_handler(access_user=Operator)
    def choose_courier(self, update, context, user: Operator):
        user.deal.courier_id = context.match.group(1)

        BH.update_deal_courier(user)

        deal_id = user.deal.deal_id
        courier = BW.BitrixUsers.fullname_by_bitrix_id(user.deal.courier_id)
        message = f'✅ На заказ {deal_id} назначен курьер {courier}!\n#назначен_курьер #сделка_{deal_id}'
        update.callback_query.edit_message_text(message)

        text = "Что будем делать дальше?"
        keyboard = InlineKeyboardMarkup([[self._buttons.CANCEL_PREV], [self._buttons.CANCEL_GENERAL]])
        update.callback_query.from_user.send_message(text, reply_markup=keyboard)
        return self._state.FINISH


class SendCourier(AssignCourier):
    class Buttons(AssignCourier.Buttons):
        ENTRY = InlineKeyboardButton("Отправить заказ (курьером) 🚚", callback_data="deal_send")
        LEAVE_COURIER = InlineKeyboardButton("Отправить с курьером {}", callback_data="leave_courier")

    def __init__(self, fallbacks: list, map_to_parent: dict, state_finish: int,
                 button_cancel_prev: InlineKeyboardButton, button_cancel_general: InlineKeyboardButton,
                 timeout: int):
        super().__init__(fallbacks, map_to_parent, state_finish, button_cancel_prev, button_cancel_general, timeout)
        self._buttons = self.Buttons(button_cancel_prev, button_cancel_general)
        self.cv_handler.states[self._state.CHANGE].append(CallbackQueryHandler(self.choose_courier,
                                                              pattern=self._buttons.LEAVE_COURIER.callback_data))

    @TgCommons.pre_handler(access_user=Operator)
    def check_courier(self, update: Update, context, user: Operator):
        if user.deal.stage_name != user.deal.FilMapStage.APPROVED:
            text = 'Заказ должен находиться в стадии "Согласовано".\nИзмените стадию заказа и попробуйте снова.'
            update.callback_query.answer(text, show_alert=True)
            return None

        if user.deal.courier_id:
            name = BW.BitrixUsers.fullname_by_bitrix_id(user.deal.courier_id)
            text = f"Курьер <b>{name}</b> уже назначен на заказ <b>{user.deal.deal_id}</b>."

            send_curr = InlineKeyboardButton(self._buttons.LEAVE_COURIER.text.format(name),
                                             callback_data=self._buttons.LEAVE_COURIER.callback_data)
            keyboard = InlineKeyboardMarkup([[self._buttons.CHANGE_COURIER], [send_curr],
                                             [self._buttons.CANCEL_PREV]])
            update.callback_query.edit_message_text(text, ParseMode.HTML, reply_markup=keyboard,
                                                    disable_web_page_preview=True)
            return self._state.CHANGE
        else:
            return self.send_couriers_header(update, context)

    @TgCommons.pre_handler(access_user=Operator)
    def choose_courier(self, update, context, user: Operator):
        if update.callback_query.data != self._buttons.LEAVE_COURIER.callback_data:
            user.deal.courier_id = context.match.group(1)

        BH.send_deal(user)

        deal_id = user.deal.deal_id
        courier = BW.BitrixUsers.fullname_by_bitrix_id(user.deal.courier_id)
        message = f'✅ Заказ {deal_id} отправлен с курьером {courier}!\n#отправлен_с_курьером #сделка_{deal_id}'
        update.callback_query.edit_message_text(message)

        text = "Что будем делать дальше?"
        keyboard = InlineKeyboardMarkup([[self._buttons.CANCEL_PREV], [self._buttons.CANCEL_GENERAL]])
        update.callback_query.from_user.send_message(text, reply_markup=keyboard)
        return self._state.FINISH

