import os
from typing import List
import logging
import datetime

from telegram.ext import MessageHandler, Filters, CallbackContext, \
    ConversationHandler, CallbackQueryHandler
from telegram import PhotoSize, InlineKeyboardButton, InlineKeyboardMarkup, Update, InputMediaAnimation, \
    InputMediaPhoto, ParseMode

from source.Users import Operator
import source.config as cfg
import source.TelegramCommons as TgCommons
from source.utils.TelegramCalendar import TgCalendar
from source.handlers.WorkingDeal.SetFlorist.TgHandlers import SetFlorist
from source.handlers.WorkingDeal.Reserve.Photo import Photo
import source.handlers.WorkingDeal.Reserve.BitrixHandlers as BH

logger = logging.getLogger(__name__)


class Reserve:
    class _State:
        WILL_YOU_RESERVE = 70
        LOADING_PHOTOS = 71
        SUPPLY_CALENDAR = 72
        APPROVE_RESERVE_NOT_NEEDED = 73
        DESCRIPTION = 74

        def __init__(self, finish):
            self.FINISH = finish

    class Buttons:
        ENTRY = InlineKeyboardButton("Обработать заказ 👌", callback_data="deal_process")

        RESERVE_YES = InlineKeyboardButton(text='Отложить товар сейчас', callback_data="reserve_yes")
        WAITING_SUPPLY = InlineKeyboardButton(text='Ждет поставки', callback_data='reserve_waiting_for_supply')
        RESERVE_NO = InlineKeyboardButton(text='Резерв не нужен', callback_data='reserve_not_needed')
        CB_PATTERN = f"^{RESERVE_YES.callback_data}$|^{WAITING_SUPPLY.callback_data}$|^{RESERVE_NO.callback_data}$"

        FINISH_PHOTO_LOADING = InlineKeyboardButton('Завершить', callback_data='finish_photo_loading')

        TWIX_APPROVE = InlineKeyboardButton('Подтверждаю', callback_data='bt_approve')

        def __init__(self, cancel_prev: InlineKeyboardButton, cancel_general: InlineKeyboardButton,
                     set_florist: SetFlorist):
            self.SET_FLORIST = set_florist.Buttons.ENTRY
            self.CANCEL_PREV = cancel_prev
            self.CANCEL_GENERAL = cancel_general

    class _Text:
        _CURR = "▶"
        _WAIT = "☑"
        _DONE = "✅"
        _YES_PHOTO_CURR = "Загрузите одно или несколько фото резерва."
        _YES_PHOTO_DONE = "Фото успешно загружено."
        _YES_PHOTO_CURR2 = "Загрузите другие фото, или завершите загрузку."

        _YES_DESCRIPTION_WAIT = "<tg-spoiler>Описание отложенного.</tg-spoiler>"
        _YES_DESCRIPTION_CURR = "Введите текстовое описание отложенного."

        HEADER = "📌 Обрабатываем сделку {}\n\n"

        START_LOAD_PHOTO = f"{_CURR} {_YES_PHOTO_CURR}\n{_WAIT} {_YES_DESCRIPTION_WAIT}"
        LOAD_PHOTO = f"{_CURR} {_YES_PHOTO_DONE} {_YES_PHOTO_CURR2}\n{_WAIT} {_YES_DESCRIPTION_WAIT}"
        START_LOAD_DESCRIPTION = f"{_DONE} {_YES_PHOTO_DONE}\n{_CURR} {_YES_DESCRIPTION_CURR}"

    def __init__(self, fallbacks: list, map_to_parent: dict, state_finish: int,
                 button_cancel_prev: InlineKeyboardButton, button_cancel_general: InlineKeyboardButton,
                 set_florist: SetFlorist, timeout: int):
        self._buttons = self.Buttons(button_cancel_prev, button_cancel_general, set_florist)
        self._calendar = TgCalendar(other_keyboard=[[self._buttons.CANCEL_PREV]])
        self._state = self._State(state_finish)

        self.cv_handler = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(callback=self.entry, pattern=self._buttons.ENTRY.callback_data)],
            states={
                self._state.WILL_YOU_RESERVE: [CallbackQueryHandler(callback=self.reserve_choice,
                                                                    pattern=self._buttons.CB_PATTERN, )],
                self._state.LOADING_PHOTOS: [CallbackQueryHandler(callback=self.request_description,
                                                                  pattern=self._buttons.FINISH_PHOTO_LOADING.callback_data),
                                             MessageHandler(Filters.photo, self.append_photo)],
                self._state.DESCRIPTION: [MessageHandler(Filters.text, self.response_description)],
                self._state.APPROVE_RESERVE_NOT_NEEDED: [CallbackQueryHandler(callback=self.no_reserve_approve,
                                                                              pattern=self._buttons.TWIX_APPROVE.callback_data),
                                                         CallbackQueryHandler(callback=SetFlorist._check_florist,
                                                                              pattern=self._buttons.SET_FLORIST.callback_data)
                                                         ],
                self._state.SUPPLY_CALENDAR: [CallbackQueryHandler(callback=self.calendar_selection,
                                                                   pattern=TgCalendar.CB_PATTERN)],
                **set_florist.cv_handler.states
            },
            fallbacks=fallbacks,
            map_to_parent=map_to_parent,
            conversation_timeout=timeout
        )

    @TgCommons.pre_handler(access_user=Operator)
    def entry(self, update: Update, context: CallbackContext, user: Operator):
        if user.deal.stage_name != user.deal.FilMapStage.PAID_PREPAID:
            text = 'Заказ должен находиться в стадии "Оплачен\Предоплачен".\nИзмените стадию заказа и попробуйте снова.'
            update.callback_query.answer(text, show_alert=True)
            return None
        user.reserve.clear()
        text = f'Резервируем товар для заказа {user.deal.deal_id}?'
        keyboard = [[self._buttons.RESERVE_YES], [self._buttons.WAITING_SUPPLY], [self._buttons.RESERVE_NO],
                    [self._buttons.CANCEL_PREV]]
        update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        return self._state.WILL_YOU_RESERVE

    @TgCommons.pre_handler(access_user=Operator)
    def reserve_choice(self, update: Update, context: CallbackContext, user: Operator):
        action = update.callback_query.data
        user.mes_media = None
        user.mes_main = update.callback_query.message
        text_header = self._Text.HEADER.format(user.deal.deal_id)
        keyboard = [[self._buttons.CANCEL_PREV]]

        if action == self._buttons.RESERVE_YES.callback_data:
            text = text_header + self._Text.START_LOAD_PHOTO
            path_img = os.path.join(os.getcwd(), os.path.abspath("source/data/load.gif"))
            with open(path_img, "rb") as file:
                img = file.read()
            update.callback_query.message.delete()
            user.mes_main = update.callback_query.from_user.send_animation(img, caption=text,
                                                                           reply_markup=InlineKeyboardMarkup(keyboard),
                                                                           parse_mode=ParseMode.HTML)
            return self._state.LOADING_PHOTOS
        elif action == self._buttons.WAITING_SUPPLY.callback_data:
            calendar_markup = self._calendar.create_calendar()
            text = text_header + 'Выберите дату, затем время поставки:\n'
            update.callback_query.edit_message_text(text, reply_markup=calendar_markup)
            return self._state.SUPPLY_CALENDAR
        elif action == self._buttons.RESERVE_NO.callback_data:
            text = 'Подтверждаю, что резерв не нужен \\- будет горький твикс, если это не так\\.\n' \
                   'Резерв товара нужно делать *ТОЛЬКО через телеграм\\-бота*,\n' \
                   'НО если заказ изготавливается прямо сейчас \\- переведи на стадию *У Флориста*'
            text = text_header + text
            keyboard = [[self._buttons.TWIX_APPROVE], [self._buttons.SET_FLORIST], *keyboard]
            update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard),
                                                    parse_mode=ParseMode.MARKDOWN_V2)
            return self._state.APPROVE_RESERVE_NOT_NEEDED

    @TgCommons.pre_handler(access_user=Operator)
    def append_photo(self, update: Update, context: CallbackContext, user: Operator):
        photos: List[PhotoSize] = update.message.photo
        photo_big = photos[-1]

        unique_id_big = photo_big.file_unique_id
        photo_content_big = photo_big.get_file().download_as_bytearray()
        update.message.delete()
        file_extension_big = photo_big.get_file().file_path.split('.')[-1]

        if photo_content_big:
            user.reserve.add_deal_photo(Photo(unique_id_big + '_B.' + file_extension_big, photo_content_big))
            text = self._Text.HEADER.format(user.deal.deal_id) + self._Text.LOAD_PHOTO
            keyboard = InlineKeyboardMarkup([[self._buttons.FINISH_PHOTO_LOADING], [self._buttons.CANCEL_PREV]])
            if len(user.reserve.photos) == 1:
                img_tg = InputMediaPhoto(bytes(photo_content_big), caption=text, parse_mode=ParseMode.HTML)
                user.mes_main.edit_media(media=img_tg, reply_markup=keyboard)
            elif len(user.reserve.photos) > 1:
                media = []
                for img in user.reserve.photos:
                    media.append(InputMediaPhoto(bytes(img.data_big)))

                # delete old album
                if user.mes_media:
                    for mes in user.mes_media:
                        mes.delete()

                user.del_mes_main()
                user.mes_media = update.effective_user.send_media_group(media)
                user.mes_main = update.effective_user.send_message(text, reply_markup=keyboard,
                                                                   parse_mode=ParseMode.HTML)

    @TgCommons.pre_handler(access_user=Operator)
    def request_description(self, update: Update, context: CallbackContext, user: Operator):
        if not user.reserve.photos:
            update.callback_query.answer(text="Вы не загрузили фото резерва.", show_alert=True)
            return None
        else:
            text = self._Text.HEADER.format(user.deal.deal_id) + self._Text.START_LOAD_DESCRIPTION
            keyboard = InlineKeyboardMarkup([[self._buttons.CANCEL_PREV]])

            if update.callback_query.message.photo:
                user.mes_main = update.callback_query.edit_message_caption(text, reply_markup=keyboard)
            else:
                user.mes_main = update.callback_query.edit_message_text(text, reply_markup=keyboard)
            return self._state.DESCRIPTION

    @TgCommons.pre_handler(access_user=Operator)
    def response_description(self, update: Update, context: CallbackContext, user: Operator):
        user.deal.reserve_desc = update.message.text
        update.message.delete()
        BH.update_deal_reserve(user)

        if user.mes_media:
            mes_finish = user.mes_media[0]
        else:
            mes_finish = user.mes_main
        text = f'✅ Заказ {user.deal.deal_id} успешно обновлен!\n #резерв #сделка_{user.deal.deal_id}'
        mes_finish.edit_caption(text)

        return self.finish(update, context)

    @TgCommons.pre_handler(access_user=Operator)
    def no_reserve_approve(self, update: Update, context: CallbackContext, user: Operator):
        img_name = "no_reserve_needed.png"
        img_path = os.path.join(os.getcwd(), os.path.abspath(f"source/data/{img_name}"))

        with open(img_path, 'rb') as f:
            stub_bytes = f.read()
            user.reserve.add_deal_photo(Photo(img_name, stub_bytes))

        BH.update_deal_no_reserve(user)
        text = f'✅ Заказ {user.deal.deal_id} успешно обновлен!\n #резерв_не_нужен #сделка_{user.deal.deal_id}'
        update.callback_query.edit_message_text(text)

        return self.finish(update, context)

    @TgCommons.pre_handler(access_user=Operator)
    def calendar_selection(self, update, context: CallbackContext, user: Operator):
        query = update.callback_query

        result, dt = self._calendar.process_selection(update, context)

        if result:
            if dt < datetime.datetime.now(tz=cfg.TIMEZONE):
                keyboard = self._calendar.create_calendar()
                query.answer(text='Дата поставки должна быть позже текущей!\nПопробуйте снова.')
                context.bot.edit_message_text(text=query.message.text,
                                              chat_id=query.message.chat_id,
                                              message_id=query.message.message_id,
                                              reply_markup=keyboard)

                return None

            user.deal.supply_datetime = dt.isoformat()

            BH.update_deal_waiting_for_supply(user)

            text = f'✅ Заказ {user.deal.deal_id} успешно обновлен!\n #ждет_поставки #сделка_{user.deal.deal_id}'
            update.callback_query.edit_message_text(text)
            return self.finish(update, context)

    @TgCommons.pre_handler(access_user=Operator)
    def finish(self, update, context, user: Operator):
        user.mes_media = None
        text = "Что будем делать дальше?"
        keyboard = InlineKeyboardMarkup([[self._buttons.CANCEL_PREV], [self._buttons.CANCEL_GENERAL]])
        user.mes_main = update.callback_query.from_user.send_message(text, reply_markup=keyboard)
        user.reserve.clear()
        return self._state.FINISH
