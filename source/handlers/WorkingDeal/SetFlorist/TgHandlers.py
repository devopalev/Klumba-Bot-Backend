import logging
import math
from typing import Tuple

from telegram.ext import MessageHandler, Filters, CallbackContext, \
    ConversationHandler, CallbackQueryHandler
from telegram import InlineKeyboardButton, Update, ParseMode, InlineKeyboardMarkup

from source.Users import Operator, Florist
import source.utils.Utils as Utils
import source.TelegramCommons as TgCommons
import source.bitrix.BitrixWorker as BW
import source.handlers.WorkingDeal.SetFlorist.BitrixHandlers as BH

logger = logging.getLogger(__name__)


class SetFlorist:
    class Buttons:
        ENTRY = InlineKeyboardButton("Назначить флориста 👩‍🌾", callback_data="deal_set_florist")

        CHANGE_FLORIST = InlineKeyboardButton("Изменить", callback_data="change_florist")
        ASSIGN_ME_TEXT = "Назначить флористом меня 🫵🏼"
        SHOW_ALL = InlineKeyboardButton("Показать весь список", callback_data="show_all")

        PREV = InlineKeyboardButton("<", callback_data="prev_page")
        NEXT = InlineKeyboardButton(">", callback_data="next_page")

        PATTERN_FLORIST_CHOOSE = r'^(\d+)$'

        def __init__(self, cancel_prev: InlineKeyboardButton, cancel_general: InlineKeyboardButton):
            self.CANCEL_PREV = cancel_prev
            self.CANCEL_GENERAL = cancel_general

    class _State:
        SEARCH_FLORIST = 60
        CHANGE_FLORIST = 62

        def __init__(self, finish):
            self.FINISH = finish

    def __init__(self, fallbacks: list, map_to_parent: dict, state_finish: int,
                 button_cancel_prev: InlineKeyboardButton, button_cancel_general: InlineKeyboardButton, timeout: int):
        self._buttons = self.Buttons(button_cancel_prev, button_cancel_general)
        self._state = self._State(state_finish)

        self.cv_handler = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(callback=self._check_florist, pattern=self._buttons.ENTRY.callback_data)],
            states={
                self._state.CHANGE_FLORIST: [CallbackQueryHandler(self._send_florists_header,
                                                                  pattern=self._buttons.CHANGE_FLORIST.callback_data)],
                self._state.SEARCH_FLORIST: [MessageHandler(Filters.text, self.search_florists_by_surname),
                                             CallbackQueryHandler(callback=self.show_all_florists,
                                                                  pattern=self._buttons.SHOW_ALL.callback_data),
                                             CallbackQueryHandler(callback=self.choose_florist,
                                                                  pattern=self._buttons.PATTERN_FLORIST_CHOOSE),
                                             CallbackQueryHandler(callback=self.next_page,
                                                                  pattern=self._buttons.NEXT.callback_data),
                                             CallbackQueryHandler(callback=self.prev_page,
                                                                  pattern=self._buttons.PREV.callback_data)
                                             ]
            },
            fallbacks=fallbacks,
            map_to_parent=map_to_parent,
            conversation_timeout=timeout)

    @TgCommons.pre_handler(access_user=Operator)
    def _check_florist(self, update: Update, context: CallbackContext, user: Operator):
        if user.deal.florist_id:
            florist = BW.BitrixUsers.fullname_by_bitrix_id(user.deal.florist_id)
            text = f"Флорист *{florist}* уже назначен на заказ *{user.deal.deal_id}*\\."

            keyboard = InlineKeyboardMarkup([[self._buttons.CHANGE_FLORIST], [self._buttons.CANCEL_PREV]])
            update.callback_query.edit_message_text(text, ParseMode.MARKDOWN_V2, reply_markup=keyboard,
                                                    disable_web_page_preview=True)
            return self._state.CHANGE_FLORIST
        else:
            return self._send_florists_header(update, context)

    @TgCommons.pre_handler(access_user=Operator)
    def _send_florists_header(self, update: Update, context: CallbackContext, user: Operator):

        user.mes_main = update.callback_query.message
        deal_info = f'*Заказ №*: {user.deal.deal_id}\n' \
                    f'*Что заказано*: {user.deal.order}\n' \
                    f'*Контакт*: {user.deal.contact}\n' \
                    f'*Флорист*: {user.deal.florist}\n' \
                    f'*Кто принял заказ*: {user.deal.order_received_by}\n' \
                    f'*Инкогнито*: {user.deal.incognito}\n' \
                    f'*Комментарий к товару*: {user.deal.order_comment}\n' \
                    f'*Комментарий по доставке*: {user.deal.delivery_comment}\n' \
                    f'*Сумма заказа общая\\(итоговая\\):* {user.deal.total_sum}\n\n' \
                    f'*Тип оплаты*: {user.deal.payment_type}\n' \
                    f'*Способ оплаты*: {user.deal.payment_method}\n' \
                    f'*Статус оплаты*: {user.deal.payment_status}\n' \
                    f'*Предоплата*: {user.deal.prepaid}\n' \
                    f'*К оплате*: {user.deal.to_pay}\n' \
                    f'*Курьер*: {user.deal.courier}\n' \
                    f'*Тип заказа*: {user.deal.order_type}'

        text = f"{deal_info}\n\n <b>ВВЕДИТЕ НАЧАЛО ФАМИЛИИ ФЛОРИСТА:</b>"

        keyboard = InlineKeyboardMarkup([[self._buttons.SHOW_ALL], [self._buttons.CANCEL_PREV]])
        if isinstance(user, Florist):
            keyboard.inline_keyboard.insert(0, [InlineKeyboardButton(self._buttons.ASSIGN_ME_TEXT,
                                                                     callback_data=user.bitrix_user_id)])
        update.callback_query.edit_message_text(text, ParseMode.HTML, reply_markup=keyboard)
        return self._state.SEARCH_FLORIST

    @TgCommons.pre_handler(access_user=Operator)
    def search_florists_by_surname(self, update: Update, context: CallbackContext, user: Operator):
        search_surname = update.message.text
        update.message.delete()
        user.florist.florist_search_surname = Utils.prepare_str(search_surname)

        result = BW.BitrixUsers.get_florists(search_surname=search_surname)
        if result:
            user.florist.page_number = 0
            user.florist.florists = result

            text, keyboard = self.render_cur_page(user)
            user.mes_main.edit_text(text, ParseMode.MARKDOWN_V2, reply_markup=keyboard)
            return self._state.SEARCH_FLORIST
        else:
            text = f"Не нашел флористов фамилия которых начинается на \"{search_surname}\". Попробуй ещё раз или " \
                   f"вернись в предыдущее меню."
            keyboard = InlineKeyboardMarkup([[self._buttons.SHOW_ALL], [self._buttons.CANCEL_PREV]])
            user.mes_main.edit_text(text, reply_markup=keyboard)

    def render_cur_page(self, user: Operator) -> Tuple[str, InlineKeyboardMarkup]:
        florists_num = len(user.florist.florists)
        page_number = user.florist.page_number
        user.florist.total_pages = math.ceil(florists_num / user.florist.FLORISTS_PER_PAGE)

        if user.florist.florist_search_surname:
            message = f'Флористы  с фамилией на *{user.florist.florist_search_surname}*:\n'
        else:
            message = '📌 Флористы\n'

        if user.florist.total_pages > 1:
            message += f'Страница {page_number + 1} из {user.florist.total_pages}\n\n'

        florists_tuples = list(user.florist.florists.items())
        page = florists_tuples[page_number * user.florist.FLORISTS_PER_PAGE:
                               (page_number + 1) * user.florist.FLORISTS_PER_PAGE]

        keyboard = []

        for bitrix_id, p_data in page:
            fullname = f"{p_data[BW.BitrixUsers.ConstFields.SURNAME]} {p_data[BW.BitrixUsers.ConstFields.NAME]}"
            keyboard.append([InlineKeyboardButton(fullname, callback_data=bitrix_id)])

        if page_number > 0:
            keyboard.append([self._buttons.PREV])

        if page_number < user.florist.total_pages - 1:
            if page_number > 0:  # if prev page button has been added
                keyboard[-1].append(self._buttons.NEXT)
            else:
                keyboard.append([self._buttons.NEXT])
        keyboard.append([self._buttons.CANCEL_PREV])
        return message, InlineKeyboardMarkup(keyboard)

    @TgCommons.pre_handler(access_user=Operator)
    def show_all_florists(self, update: Update, context: CallbackContext, user: Operator):
        result = BW.BitrixUsers.get_florists()
        user.florist.page_number = 0
        user.florist.florists = result
        text, keyboard = self.render_cur_page(user)
        update.callback_query.edit_message_text(text, ParseMode.MARKDOWN_V2, reply_markup=keyboard)
        return self._state.SEARCH_FLORIST

    @TgCommons.pre_handler(access_user=Operator)
    def next_page(self, update: Update, context: CallbackContext, user: Operator):
        page_number = user.florist.page_number

        if page_number < user.florist.total_pages - 1:
            user.florist.page_number += 1
            text, keyboard = self.render_cur_page(user)
            update.callback_query.edit_message_text(text, ParseMode.MARKDOWN_V2, reply_markup=keyboard)

        return self._state.SEARCH_FLORIST

    @TgCommons.pre_handler(access_user=Operator)
    def prev_page(self, update: Update, context: CallbackContext, user: Operator):
        page_number = user.florist.page_number

        if page_number > 0:
            user.florist.page_number -= 1
            text, keyboard = self.render_cur_page(user)
            update.callback_query.edit_message_text(text, ParseMode.MARKDOWN_V2, reply_markup=keyboard)

        return self._state.SEARCH_FLORIST

    @TgCommons.pre_handler(access_user=Operator)
    def choose_florist(self, update: Update, context: CallbackContext, user: Operator):
        florist: Operator

        florist_id = context.match.group(1)
        user.deal.florist_id = florist_id

        BH.update_deal_florist(user)

        florist = BW.BitrixUsers.fullname_by_bitrix_id(florist_id)
        deal_id = user.deal.deal_id
        message = f'✅ На заказ {deal_id} назначен флорист {florist}!\n#назначен_флорист #сделка_{deal_id}'
        update.callback_query.edit_message_text(message)

        text = "Что будем делать дальше?"
        keyboard = InlineKeyboardMarkup([[self._buttons.CANCEL_PREV], [self._buttons.CANCEL_GENERAL]])
        update.callback_query.from_user.send_message(text, reply_markup=keyboard)
        return self._state.FINISH
