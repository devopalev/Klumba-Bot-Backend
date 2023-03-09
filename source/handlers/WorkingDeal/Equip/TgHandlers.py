import os
from typing import List
import logging
import base64

from telegram.ext import MessageHandler, Filters, CallbackContext, \
    ConversationHandler, CallbackQueryHandler

from telegram import PhotoSize, InlineKeyboardButton, Update, ParseMode, InlineKeyboardMarkup, InputMediaPhoto

from source.Users import Operator
import source.TelegramCommons as TgCommons

from .Photo import Photo as Photo
import source.handlers.WorkingDeal.Equip.BitrixHandlers as BH
import source.handlers.WorkingDeal.Equip.StorageHandlers as StorageHandlers
from source.bitrix.Deal import Deal

logger = logging.getLogger(__name__)


class Equip:
    class Buttons:
        ENTRY = InlineKeyboardButton("Укомплектовать заказ 💐", callback_data="deal_equip")

        REPEATEDLY = InlineKeyboardButton('Да 😎', callback_data='equip_repeatedly')

        DELETE_DEAL_PHOTO = InlineKeyboardButton("Удалить последнее фото заказа ❌", callback_data=f"delete:deal_photo")

        CB_CHANGE = "change:"
        CHANGE_DEAL_PHOTO = InlineKeyboardButton("Изменить фото заказа 🥀", callback_data=f"{CB_CHANGE}deal_photo")
        CHANGE_POSTCARD_FRONT = InlineKeyboardButton("Изменить лицевое фото открытки 💌",
                                                     callback_data=f"{CB_CHANGE}postcard_front")
        CHANGE_POSTCARD_REVERSE = InlineKeyboardButton("Изменить фото текста в открытке 📝",
                                                       callback_data=f"{CB_CHANGE}postcard_reverse")

        FINISH_PHOTO_LOADING = InlineKeyboardButton('Завершить загрузку ✅', callback_data='finish_loading')

        def __init__(self, cancel_prev: InlineKeyboardButton, cancel_general: InlineKeyboardButton):
            self.CANCEL_PREV = cancel_prev
            self.CANCEL_GENERAL = cancel_general

    class _State:
        REPEATEDLY_APPROVE = 81  # Подтверждаем, что хотим повторно укомплектовать заказ
        SET_PHOTOS = 82  # Загружаем фото заказа
        SET_POSTCARD_FRONT = 83  # Загружаем лицевую сторону открытки
        SET_POSTCARD_REVERSE = 84  # Загружаем сторону с текстом открытки
        SET_CHECKLIST = 85  # Запрошено фото бумажного чек-листа

        def __init__(self, finish):
            self.FINISH = finish

    class _Text:
        _CURR = "▶"
        _WAIT = "☑"
        _DONE = "✅"

        def __init__(self):
            self.__temp = ""

        def header(self, id_):
            self.__temp += f"📌 Обрабатываем сделку {id_}"
            return self

        def bad_stage(self):
            self.__temp += 'Заказ должен находиться в одной из стадий: ' \
                           '"Обработан в 1С", "У Флориста", "Согласовано", "Несогласовано"\n' \
                           'Измените стадию заказа и попробуйте снова.'
            return self

        def repeatedly(self, deal_id):
            self.__temp += f'Заказ {deal_id} уже укомплектован.\nУкомплектовать повторно?'
            return self

        def deal_photo_curr(self):
            self.__temp += f"\n\n{self._CURR} Загрузите одно или несколько фото заказа.\n"
            return self

        def deal_photo_curr2(self):
            self.__temp += f"\n\n{self._CURR} Фото успешно загружено. Загрузите другие фото, или " \
                           f"нажмите <b>Завершить загрузку</b>.\n"
            return self

        def deal_photo_done(self):
            self.__temp += f"\n\n{self._DONE} Фото успешно загружено.\n"
            return self

        def postcard_front_wait(self):
            self.__temp += f'{self._WAIT} <tg-spoiler>Загрузка лицевой стороны открытки.</tg-spoiler>\n'
            return self

        def postcard_front_curr(self):
            self.__temp += f'{self._CURR} Загрузите фото <b>лицевой стороны</b> открытки.\n'
            return self

        def postcard_front_done(self):
            self.__temp += f'{self._DONE} Фото лицевой стороны открытки загружено.\n'
            return self

        def postcard_reverse_wait(self):
            self.__temp += f'{self._WAIT} <tg-spoiler>Загрузка стороны открытки где виден текст.</tg-spoiler>\n'
            return self

        def postcard_reverse_curr(self, text):
            self.__temp += f'{self._CURR} Загрузите фото стороны открытки, <b>где виден текст</b>: {text}.\n'
            return self

        def postcard_reverse_done(self):
            self.__temp += f'{self._DONE} Фото стороны где виден текст открытки загружено.\n'
            return self

        def checklist_wait(self):
            self.__temp += f'{self._WAIT} <tg-spoiler>Загрузка фото чек-листа.</tg-spoiler>'
            return self

        def checklist_curr(self):
            self.__temp += f'{self._CURR} Загрузите <b>ФОТО БУМАЖНОГО ЧЕК-ЛИСТА</b>.'
            return self

        def build_by_user(self, user: Operator, stage):
            if stage == Equip._State.SET_PHOTOS:
                if user.equip.photos:
                    self.deal_photo_curr2()
                else:
                    self.deal_photo_curr()
            else:
                self.deal_photo_done()

            if user.deal.has_postcard:
                if stage == Equip._State.SET_POSTCARD_FRONT:
                    self.postcard_front_curr()
                else:
                    if user.equip.postcard_front:
                        self.postcard_front_done()
                    else:
                        self.postcard_front_wait()

                if stage == Equip._State.SET_POSTCARD_REVERSE:
                    self.postcard_reverse_curr(user.deal.postcard_text)
                else:
                    if user.equip.postcard_reverse:
                        self.postcard_reverse_done()
                    else:
                        self.postcard_reverse_wait()

            if stage == Equip._State.SET_CHECKLIST:
                self.checklist_curr()
            else:
                self.checklist_wait()
            return self.build()

        def build(self):
            return self.__temp

    def __init__(self, fallbacks: list, map_to_parent: dict, state_finish: int,
                 button_cancel_prev: InlineKeyboardButton, button_cancel_general: InlineKeyboardButton,
                 timeout: int
                 ):
        self._buttons = self.Buttons(button_cancel_prev, button_cancel_general)
        self._state = self._State(state_finish)

        equip_fallbacks = [CallbackQueryHandler(self.change_photo, pattern=self._buttons.CB_CHANGE)]
        equip_fallbacks.extend(fallbacks)

        self.cv_handler = ConversationHandler(
            name="EquipMenu",
            entry_points=[
                CallbackQueryHandler(callback=self.check_equip, pattern=self._buttons.ENTRY.callback_data)],
            states={
                self._state.REPEATEDLY_APPROVE: [CallbackQueryHandler(callback=self.dialog_handler,
                                                                      pattern=self._buttons.REPEATEDLY.callback_data)],
                self._state.SET_PHOTOS: [MessageHandler(Filters.photo, self.append_deal_photo),
                                         CallbackQueryHandler(callback=self.dialog_handler,
                                                              pattern=self._buttons.FINISH_PHOTO_LOADING.callback_data),
                                         CallbackQueryHandler(self.delete_photo,
                                                              pattern=self._buttons.DELETE_DEAL_PHOTO.callback_data)],
                self._state.SET_POSTCARD_FRONT: [MessageHandler(Filters.photo, self.append_postcard)],
                self._state.SET_POSTCARD_REVERSE: [MessageHandler(Filters.photo, self.append_postcard)],
                self._state.SET_CHECKLIST: [MessageHandler(Filters.photo, self.load_checklist_photo),
                                            ]
            },
            fallbacks=equip_fallbacks,
            map_to_parent=map_to_parent,
            conversation_timeout=timeout
        )

    @TgCommons.pre_handler(access_user=Operator)
    def check_equip(self, update: Update, context: CallbackContext, user: Operator):
        user.equip.clear()
        keyboard = InlineKeyboardMarkup([[self._buttons.CANCEL_PREV]])

        # Проверяем этап сделки
        if user.deal.stage_name not in (Deal.FilMapStage.PROCESSED_1C, Deal.FilMapStage.UNAPPROVED,
                                        Deal.FilMapStage.IS_EQUIPPED, Deal.FilMapStage.FLORIST):
            text = self._Text().bad_stage().build()
            update.callback_query.answer(text, show_alert=True)
            return None

        # Сделка уже укомплектована?
        elif user.deal.stage_name == Deal.FilMapStage.IS_EQUIPPED:
            user.equip.repeating = True
            text = self._Text().repeatedly(user.deal.deal_id).build()
            keyboard.inline_keyboard.insert(0, [self._buttons.REPEATEDLY])
            update.callback_query.edit_message_text(text, reply_markup=keyboard)
            return self._state.REPEATEDLY_APPROVE
        user.mes_media = None
        user.mes_main = update.callback_query.message
        return self.dialog_handler(update, context)

    @TgCommons.pre_handler(access_user=Operator)
    def append_deal_photo(self, update: Update, context: CallbackContext, user: Operator):
        if update.message:
            photos: List[PhotoSize] = update.message.photo
            photo_big = photos[-1]

            if len(photos) > 1:
                photo_small = photos[1]
            else:
                photo_small = photos[0]

            unique_id_big = photo_big.file_unique_id
            photo_content_big = photo_big.get_file().download_as_bytearray()
            file_extension_big = photo_big.get_file().file_path.split('.')[-1]

            file_extension_small = photo_small.get_file().file_path.split('.')[-1]
            unique_id_small = photo_small.file_unique_id
            photo_content_small = photo_small.get_file().download_as_bytearray()

            update.message.delete()

            if photo_content_big and photo_content_small:
                logger.info(f'Appending photo: big photo content size: {len(photo_content_big)}')
                # store raw photo data to save it on disk later
                user.equip.add_deal_photo(Photo(unique_id_small + '_S.' + file_extension_small,
                                                unique_id_big + '_B.' + file_extension_big,
                                                photo_content_small,
                                                photo_content_big))
                logger.info(
                    f'User bitrix id {user.bitrix_user_id} uploaded photo {unique_id_small}.{file_extension_small}')
            else:
                logger.error('No photo content big/small from user %s', update.message.from_user.id)

        keyboard = InlineKeyboardMarkup([[self._buttons.DELETE_DEAL_PHOTO], [self._buttons.FINISH_PHOTO_LOADING],
                                         [self._buttons.CANCEL_PREV]])

        text = self._Text().header(user.deal.deal_id).build_by_user(user, self._state.SET_PHOTOS)
        self.send_message(update, context, user, text, keyboard)
        return self._state.SET_PHOTOS

    @TgCommons.pre_handler(access_user=Operator)
    def append_postcard(self, update, context: CallbackContext, user: Operator):
        photos: List[PhotoSize] = update.message.photo
        photo_big = photos[-1]

        unique_id_big = photo_big.file_unique_id
        photo_content_big = photo_big.get_file().download_as_bytearray()
        file_extension_big = photo_big.get_file().file_path.split('.')[-1]

        update.message.delete()

        if photo_content_big:
            photo = Photo(name_big=unique_id_big + '_B.' + file_extension_big, data_big=photo_content_big)
            # store raw photo data to save it on disk later
            if not user.equip.postcard_front:
                user.equip.postcard_front = photo
            else:
                user.equip.postcard_reverse = photo

        else:
            logger.error('No photo content big/small from user %s', update.message.from_user.id)
        return self.dialog_handler(update, context)

    @TgCommons.pre_handler(access_user=Operator)
    def load_checklist_photo(self, update: Update, context, user: Operator):
        photos: List[PhotoSize] = update.message.photo

        photo = photos[-1]
        unique_id = photo.file_unique_id
        photo_content = photo.get_file().download_as_bytearray()
        file_extension = photo.get_file().file_path.split('.')[-1]

        media = [InputMediaPhoto(bytes(p.data_big)) for p in user.equip.photos]
        media.append(InputMediaPhoto(bytes(user.equip.postcard_front.data_big)))
        media.append(InputMediaPhoto(bytes(user.equip.postcard_reverse.data_big)))
        media.append(InputMediaPhoto(bytes(photo_content)))

        update.message.delete()

        encoded_data = base64.b64encode(photo_content).decode('ascii')
        user.deal.photo_data = encoded_data
        user.deal.photo_name = unique_id + '.' + file_extension

        StorageHandlers.save_deal(user, user.deal.deal_id)
        BH.update_deal_image(user)

        user.del_mes_main()
        user.del_mes_media()

        text = f'✅ Заказ {user.deal.deal_id} успешно обновлен!\n #укомплектован #сделка_{user.deal.deal_id}'
        media[0].caption = text
        update.effective_user.send_media_group(media)

        text = "Что будем делать дальше?"
        keyboard = InlineKeyboardMarkup([[self._buttons.CANCEL_PREV], [self._buttons.CANCEL_GENERAL]])
        user.mes_main = update.effective_user.send_message(text, reply_markup=keyboard)
        return self._state.FINISH

    @TgCommons.pre_handler(access_user=Operator)
    def delete_photo(self, update: Update, context, user: Operator):
        user.equip.photos.pop()
        if not user.equip.photos:
            return self.dialog_handler(update, context)
        else:
            return self.append_deal_photo(update, context)

    @TgCommons.pre_handler(access_user=Operator)
    def change_photo(self, update: Update, context, user: Operator):
        query = update.callback_query.data
        if query == self._buttons.CHANGE_DEAL_PHOTO.callback_data:
            return self.append_deal_photo(update, context)
        elif query == self._buttons.CHANGE_POSTCARD_FRONT.callback_data:
            user.equip.postcard_front = None
            return self.dialog_handler(update, context)
        elif query == self._buttons.CHANGE_POSTCARD_REVERSE.callback_data:
            user.equip.postcard_reverse = None
            return self.dialog_handler(update, context)

    @TgCommons.pre_handler(access_user=Operator)
    def dialog_handler(self, update: Update, context: CallbackContext, user: Operator):
        # Запрос загрузки фото заказа
        if not user.equip.photos:
            keyboard = InlineKeyboardMarkup([[self._buttons.CANCEL_PREV]])
            text = self._Text().header(user.deal.deal_id).build_by_user(user, self._state.SET_PHOTOS)
            self.send_message(update, context, user, text, keyboard)
            return self._state.SET_PHOTOS

        # Открытика есть в сделке?
        if user.deal.has_postcard:
            # Запрос отправки фото лицевой стороны открытки
            if not user.equip.postcard_front:
                keyboard = InlineKeyboardMarkup([[self._buttons.CHANGE_DEAL_PHOTO], [self._buttons.CANCEL_PREV]])
                text = self._Text().header(user.deal.deal_id).build_by_user(user, self._state.SET_POSTCARD_FRONT)
                self.send_message(update, context, user, text, keyboard)
                return self._state.SET_POSTCARD_FRONT

            # Запрос отправки фото стороны открытки с текстом
            elif not user.equip.postcard_reverse:
                keyboard = InlineKeyboardMarkup(
                    [[self._buttons.CHANGE_DEAL_PHOTO], [self._buttons.CHANGE_POSTCARD_FRONT],
                     [self._buttons.CANCEL_PREV]])
                text = self._Text().header(user.deal.deal_id).build_by_user(user, self._state.SET_POSTCARD_REVERSE)
                self.send_message(update, context, user, text, keyboard)
                return self._state.SET_POSTCARD_REVERSE
            else:
                keyboard = InlineKeyboardMarkup(
                    [[self._buttons.CHANGE_DEAL_PHOTO], [self._buttons.CHANGE_POSTCARD_FRONT],
                     [self._buttons.CHANGE_POSTCARD_REVERSE], [self._buttons.CANCEL_PREV]])
        else:
            keyboard = InlineKeyboardMarkup([[self._buttons.CHANGE_DEAL_PHOTO], [self._buttons.CANCEL_PREV]])

        # Запрос отправки чек-листа
        text = self._Text().header(user.deal.deal_id).build_by_user(user, self._state.SET_CHECKLIST)
        self.send_message(update, context, user, text, keyboard)
        return self._state.SET_CHECKLIST

    @staticmethod
    def send_message(update: Update, context: CallbackContext, user: Operator,
                     text: str, keyboard: InlineKeyboardMarkup):

        # формируем список фото или одно фото
        media = [InputMediaPhoto(bytes(p.data_big)) for p in user.equip.photos]
        if user.equip.postcard_front:
            media.append(InputMediaPhoto(bytes(user.equip.postcard_front.data_big)))
        if user.equip.postcard_reverse:
            media.append(InputMediaPhoto(bytes(user.equip.postcard_reverse.data_big)))

        from_user = update.callback_query.from_user if update.callback_query else update.effective_user

        if len(media) == 0:
            user.del_mes_media()

            path_img = os.path.join(os.getcwd(), os.path.abspath("source/data/load.gif"))
            with open(path_img, "rb") as file:
                img = file.read()
            if user.mes_main.photo:
                img = InputMediaPhoto(img, caption=text, parse_mode=ParseMode.HTML)
                user.mes_main = user.mes_main.edit_media(img, reply_markup=keyboard)
            else:
                user.mes_main.delete()
                user.mes_main = from_user.send_animation(img, caption=text, reply_markup=keyboard,
                                                         parse_mode=ParseMode.HTML)

        elif len(media) == 1:
            user.del_mes_media()
            img = media[0]

            if user.mes_main.photo:
                img.caption = text
                img.parse_mode = ParseMode.HTML
                user.mes_main = user.mes_main.edit_media(img, reply_markup=keyboard)
            else:
                user.mes_main.delete()
                user.mes_main = from_user.send_photo(img.media, caption=text, reply_markup=keyboard,
                                                     parse_mode=ParseMode.HTML)

        else:
            user.del_mes_main()
            user.del_mes_media()

            user.mes_media = from_user.send_media_group(media)
            user.mes_main = from_user.send_message(text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
