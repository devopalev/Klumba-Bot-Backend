from typing import List

from telegram import *
from telegram.ext import *
import source.TelegramCommons as TgCommons

from source.Users import BaseUser
from source.bitrix.Contact import Contact


# Запросить контакт
# Искать
# Выдать результат
# Создать: Имя + Телефон + Тип
#TODO: сделать поиск контакта, а из него создание. Возможность встраивать поиск в разные меню


class CreateContact:
    class Keyboard:
        ENTRY = InlineKeyboardButton("Создать контакт", callback_data="ContactHandler")

        def __init__(self, cancel):
            self.CANCEL = InlineKeyboardButton("Вернуться назад")

    def __init__(self):
        pass


    def type_contact(self):
        pass

    def source_contact(self):
        pass

    def name_contact(self):
        pass


class ContactHandler:
    access = BaseUser

    class Keyboard:
        CREATE_CONTACT = InlineKeyboardButton("Найти контакт", callback_data="ContactHandler")

        def __init__(self, cancel):
            self.CANCEL = InlineKeyboardButton("Вернуться назад")

    def __init__(self, base_cb, contact_cb, other_buttons=None, exit_func=None, only_search=False):
        self.state_waiting_contact = 823
        self.handler_dialog = ConversationHandler(entry_points=[],
                                                  states={},
                                                  fallbacks=[])
        self.other_buttons = other_buttons
        self.exit_func = exit_func
        self.base_cb = f"{base_cb}:SearchContactMenu:"
        self.btn_create_contact = self.Keyboard.CREATE_CONTACT



    def create_keyboard(self, contacts: List[Contact] = None, create_contact=False):
        keyboard = []
        if contacts:
            keyboard = [[InlineKeyboardButton(cnt.fullname, callback_data=self.base_cb + cnt.id)]
                        for cnt in contacts]
        if create_contact:
            keyboard.append([self.btn_create_contact])
        keyboard.extend([[btn] for btn in self.other_buttons])
        return InlineKeyboardMarkup(keyboard)

    @TgCommons.pre_handler(access_user=access)
    def request_contact(self, update: Update, context: CallbackContext, user: BaseUser):
        text = "Давайте поищем контакт клиента в базе." \
               "\nНапишите номер в формате\"89998887766\""
        keyboard = self.create_keyboard()
        update.callback_query.edit_message_text(text, reply_markup=keyboard)
        user.mes_main = update.callback_query.message
        return self.state_waiting_contact

    @TgCommons.pre_handler(access_user=access)
    def search(self, update: Update, context: CallbackContext, user: access):
        phone = update.message.text
        update.message.delete()
        check_phone = bool(re.match(r'^(\+7|7|8)?\d{10}$', phone))
        if check_phone:
            contacts = BH.search_contacts(phone)
            if contacts:
                text = render_text(user)
                keyboard = self.create_keyboard(contacts)
                update.effective_chat.send_message(text, reply_markup=keyboard)
            else:
                text = "Контакт не найден, создать?"
                keyboard = self.create_keyboard(create_contact=True)
                update.effective_chat.send_message(text, reply_markup=keyboard)
        else:
            TgCommons.send_temp_message(update, f"Некорректный формат номера ({phone}). Попробуйте ещё раз!")
        return ConversationHandler.END

    @TgCommons.pre_handler(access_user=access)
    def select_contact(self, update: Update, context: CallbackContext, user: access):
        contact = update.callback_query.data.split(":")[2]
        user.create_deal.contact = contact
        if self.exit_func:
            self.exit_func(update, context)




