from telegram import *
from telegram.ext import *

import source.TelegramCommons as TgCommons
import source.Users as User
import logging
import source.utils.Utils as Utils
import source.bitrix.Deal as DealData
from source.handlers.WorkingDeal.SetFlorist.TgHandlers import SetFlorist
from source.handlers.WorkingDeal.Reserve.TgHandlers import Reserve
from source.handlers.WorkingDeal.Equip.TgHandlers import Equip
from source.handlers.WorkingDeal.SetCourier.TgHandlers import SendCourier, AssignCourier

logger = logging.getLogger(__name__)


class WorkingDeal:
    TEXT_ASK_FOR_DEAL_NUMBER = 'Введите номер заказа или сфотографируйте qr код сделки'

    class State:
        ASK = 50
        MENU = 51
        END = 53

    class Buttons:
        ENTRY = InlineKeyboardButton(text="Работа с заказом ⚙", callback_data="working_deal")
        PROCESS = Reserve.Buttons.ENTRY
        SET_FLORIST = SetFlorist.Buttons.ENTRY
        EQUIP_BUTTON = Equip.Buttons.ENTRY
        SEND = SendCourier.Buttons.ENTRY
        COURIER = AssignCourier.Buttons.ENTRY

        SHOW_ALL = InlineKeyboardButton("Показать все действия ⚠", callback_data="deal_show_all")

        CANCEL_CURR = InlineKeyboardButton("Вернуться в меню заказа ↩", callback_data="back_workdeal")

        def __init__(self, cancel_prev_button: InlineKeyboardButton):
            self.CANCEL_PREV_MENU = cancel_prev_button

    def __init__(self, cancel_prev_button: InlineKeyboardButton, cancel_prev_func):
        self.buttons = self.Buttons(cancel_prev_button)
        self.cancel_prev_func = cancel_prev_func

        self.timeout = 600

        self.fallbacks = [CallbackQueryHandler(self.cancel_curr_menu, pattern=self.buttons.CANCEL_CURR.callback_data),
                          CallbackQueryHandler(self.cancel_prev_menu,
                                               pattern=self.buttons.CANCEL_PREV_MENU.callback_data)]
        self.map_to_parent = {self.State.MENU: self.State.MENU, ConversationHandler.END: ConversationHandler.END}

        set_florist = SetFlorist(self.fallbacks, self.map_to_parent, self.State.MENU, self.buttons.CANCEL_CURR,
                                 self.buttons.CANCEL_PREV_MENU, timeout=self.timeout)

        assign_courier = AssignCourier(self.fallbacks, self.map_to_parent, self.State.MENU, self.buttons.CANCEL_CURR,
                                       self.buttons.CANCEL_PREV_MENU, timeout=self.timeout)

        send = SendCourier(self.fallbacks, self.map_to_parent, self.State.MENU, self.buttons.CANCEL_CURR,
                           self.buttons.CANCEL_PREV_MENU, timeout=self.timeout)

        reverse = Reserve(self.fallbacks, self.map_to_parent, self.State.MENU, self.buttons.CANCEL_CURR,
                          self.buttons.CANCEL_PREV_MENU, set_florist, timeout=self.timeout)

        equip = Equip(self.fallbacks, self.map_to_parent, self.State.MENU, self.buttons.CANCEL_CURR,
                      self.buttons.CANCEL_PREV_MENU, timeout=self.timeout)

        self.handler_menu = [set_florist.cv_handler, reverse.cv_handler, equip.cv_handler, send.cv_handler,
                             assign_courier.cv_handler,
                             CallbackQueryHandler(self.deal_menu, pattern=self.Buttons.SHOW_ALL.callback_data)]

    @TgCommons.pre_handler(access_user=User.Operator)
    def request(self, update: Update, context: CallbackContext, user: User.Operator):

        user.mes_main = update.callback_query.message
        keyboard = InlineKeyboardMarkup([[self.buttons.CANCEL_PREV_MENU]])
        update.callback_query.edit_message_text(self.TEXT_ASK_FOR_DEAL_NUMBER, reply_markup=keyboard)
        return self.State.ASK

    @TgCommons.pre_handler(access_user=User.Operator, user_data=False)
    def response_deal_text(self, update, context):
        deal_id = update.effective_message.text
        update.message.delete()
        return self.deal_menu(update, context, deal_id=deal_id)

    @TgCommons.pre_handler(access_user=User.Operator, user_data=False)
    def response_deal_photo(self, update: Update, context):
        image: bytes = update.message.photo[-1].get_file().download_as_bytearray()
        update.message.delete()
        dial_id = Utils.qr_analise(image)

        if dial_id:
            return self.deal_menu(update, context, deal_id=dial_id)
        else:
            keyboard = InlineKeyboardMarkup([[self.buttons.CANCEL_PREV_MENU]])
            update.callback_query.edit_message_text("Не распознал QR код на фото, "
                                                    "попробуйте ещё раз или пришлите номер заказа.",
                                                    reply_markup=keyboard)

    def _generate_keyboard(self, deal: DealData.Deal, show_all=False):
        """
        Логика:
            Оплачен/предоплачен:
                - Обработать заказ
                - Назначить флориста

            Обработан, но ждет поставки + Обработан, товар отложен\Не треб:
                - Назначить флориста

            Обработан в 1С + У Флориста (Изготавливается) + Согласовано + Несогласовано:
                - Укомплектовать заказ

            Согласовано:
                - Отправить заказ (назначить курьера)
                - Назначить курьера (заранее)
        """

        keyboard = []
        if not show_all:
            if deal.stage_name == deal.FilMapStage.PAID_PREPAID:
                keyboard.append([self.buttons.PROCESS])
                keyboard.append([self.buttons.SET_FLORIST])
            elif deal.stage_name in (deal.FilMapStage.PROCESSED_WAITING_FOR_SUPPLY, deal.FilMapStage.PROCESSED_ON_HOLD):
                keyboard.append([self.buttons.SET_FLORIST])
            elif deal.stage_name in (deal.FilMapStage.PROCESSED_1C, deal.FilMapStage.FLORIST, deal.FilMapStage.UNAPPROVED):
                keyboard.append([self.buttons.EQUIP_BUTTON])
            elif deal.stage_name == deal.FilMapStage.APPROVED:
                keyboard.append([self.buttons.SEND])
                keyboard.append([self.buttons.COURIER])
            elif deal.stage_name == deal.FilMapStage.IS_EQUIPPED:
                keyboard.append([self.buttons.EQUIP_BUTTON])
            else:
                show_all = True
                logger.warning(f"Unknown stage deal: {deal.__dict__}")

            if not show_all:
                keyboard.append([self.buttons.SHOW_ALL])

        if show_all:
            keyboard.extend([[self.buttons.PROCESS], [self.buttons.SET_FLORIST], [self.buttons.EQUIP_BUTTON],
                             [self.buttons.SEND], [self.buttons.COURIER]])

        keyboard.append([self.buttons.CANCEL_PREV_MENU])
        return InlineKeyboardMarkup(keyboard)

    def _generate_text(self, deal: DealData.Deal):
        text = f"Сделка {deal.deal_id}\n" \
               f"Этап/стадия: {deal.stage_name}"
        return text

    @TgCommons.pre_handler(access_user=User.Operator, user_data=False)
    def search_deals_handler(self, update: Update, context: CallbackContext):
        deal_id = update.callback_query.data.split(":")[1]
        return self.deal_menu(update, context, deal_id=deal_id)

    @TgCommons.pre_handler(access_user=User.Operator)
    def deal_menu(self, update: Update, context, user: User.BaseUser, deal_id="", new=False):
        if deal_id:
            deal = DealData.Deal.build(deal_id)
        else:
            deal = DealData.Deal.build(user.deal.deal_id)

        if deal:
            user.deal = deal
            text = self._generate_text(deal)
            reply_markup = self._generate_keyboard(deal)
            if new:
                if update.callback_query:
                    user.mes_main = update.callback_query.from_user.send_message(text, reply_markup=reply_markup)
                else:
                    update.effective_user.send_message(text, reply_markup=reply_markup)
            elif update.callback_query:
                show_all = update.callback_query.data == self.buttons.SHOW_ALL.callback_data
                reply_markup = self._generate_keyboard(deal, show_all=True) if show_all else reply_markup
                update.callback_query.edit_message_text(text, reply_markup=reply_markup)
            else:
                user.mes_main.edit_text(text=text, reply_markup=reply_markup)
            return self.State.MENU
        else:
            keyboard = InlineKeyboardMarkup([[self.buttons.CANCEL_PREV_MENU]])
            if update.callback_query:
                update.callback_query.edit_message_text(text=f"Заказ {deal_id} не существует. Попробуйте снова.",
                                                        reply_markup=keyboard)
            else:
                user.mes_main.edit_text(text=f"Заказ {deal_id} не существует. Попробуйте снова.", reply_markup=keyboard)

    @TgCommons.pre_handler(access_user=User.Operator)
    def cancel_curr_menu(self, update: Update, context: CallbackContext, user: User.BaseUser):
        logger.debug("use back working deal menu")

        user.del_mes_media()

        if update.callback_query:
            media = any((update.callback_query.message.document, update.callback_query.message.photo))
            if media:
                update.callback_query.message.delete()
                self.deal_menu(update, context, new=True)
                return self.State.MENU

        self.deal_menu(update, context)
        return self.State.MENU

    def event_handler(self, update: Update, context: CallbackContext):
        deal_id = update.callback_query.data.split(":")[1]
        return self.deal_menu(update, context, deal_id=deal_id)

    @TgCommons.pre_handler(access_user=User.Operator)
    def timeout_handler(self, update: Update, context: CallbackContext, user: User.Operator):
        user.del_mes_main()
        user.del_mes_media()
        user.deal = DealData.Deal
        self.cancel_prev_func(update, context)
        logger.info(f"Timeout WorkingDealMenu {user.phone_number}")

    @TgCommons.pre_handler(access_user=User.Operator, user_data=False)
    def cancel_prev_menu(self, update, context):
        self.cancel_prev_func(update, context)
        return ConversationHandler.END

    @classmethod
    def build_request(cls, cancel_prev_button: InlineKeyboardButton, cancel_prev_func, dispatcher: Dispatcher):
        self = cls(cancel_prev_button, cancel_prev_func)
        handler = ConversationHandler(
            name="WorkingDealMenu(Request)",
            entry_points=[CallbackQueryHandler(self.request, pattern=self.buttons.ENTRY.callback_data)],
            states={self.State.ASK: [MessageHandler(Filters.text, self.response_deal_text),
                                     MessageHandler(Filters.photo, self.response_deal_photo)],
                    self.State.MENU: self.handler_menu,
                    ConversationHandler.TIMEOUT: [CallbackQueryHandler(self.timeout_handler),
                                                  MessageHandler(Filters.all, self.timeout_handler)]},
            fallbacks=self.fallbacks,
            # persistent=True,
            conversation_timeout=self.timeout
        )
        dispatcher.add_handler(handler)
        return self

    @classmethod
    def build_search_deals(cls, pattern_entry: str, cancel_prev_button: InlineKeyboardButton, cancel_prev_func,
                           dispatcher: Dispatcher):
        self = cls(cancel_prev_button, cancel_prev_func)
        handler = ConversationHandler(
            name="WorkingDealMenu(Search)",
            entry_points=[CallbackQueryHandler(self.search_deals_handler, pattern=pattern_entry)],
            states={self.State.MENU: self.handler_menu,
                    ConversationHandler.TIMEOUT: [CallbackQueryHandler(self.timeout_handler),
                                                  MessageHandler(Filters.all, self.timeout_handler)]},
            fallbacks=self.fallbacks,
            # persistent=True,
            conversation_timeout=self.timeout
        )
        dispatcher.add_handler(handler)
        return self
