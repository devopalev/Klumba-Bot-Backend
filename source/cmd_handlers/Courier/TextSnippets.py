from source import Commands as Cmd
import source.cmd_handlers.Courier.UserData as UserData

# deals list
DELIVERS_TODAY_BUTTON_TEXT = 'В доставке сегодня \U0001F7E9'
DELIVERS_TODAY_BUTTON_CB = 'delivers_today'
DELIVERS_TOMORROW_BUTTON_TEXT = 'В доставке завтра \U0001F7E8'
DELIVERS_TOMORROW_BUTTON_CB = 'delivers_tomorrow'
ADVANCE_BUTTON_TEXT = 'Назначенные (заранее) \U0001F7E6'
ADVANCE_BUTTON_CB = 'advance'
FINISHED_BUTTON_TEXT = 'Завершенные \U0001F3C1'
FINISHED_BUTTON_CB = 'finished'
NEXT_PAGE_TEXT = '>'
NEXT_PAGE_CB = 'next_page'
PREV_PAGE_TEXT = '<'
PREV_PAGE_CB = 'prev_page'

# finished deals
FINISHED_CHOOSE_DATE_TXT = 'Выберите дату:'
FINISHED_CHOOSE_TYPE_TXT = 'Выберите тип:'
LATE_BUTTON_TEXT = 'Опоздавшие \U0000274C'
LATE_BUTTON_CB = 'deals_late'
IN_TIME_BUTTON_TEXT = 'Доставленные вовремя \U00002705'
IN_TIME_BUTTON_CB = 'deals_in_time'


# deals list commands
VIEW_DEAL_PREFIX = 'v'
VIEW_DEAL_PATTERN = '^/' + VIEW_DEAL_PREFIX + '\\' + Cmd.CMD_DELIMETER + r'(\d+)$'


# deal view
FINISH_DEAL_BUTTON_TEXT = 'Заказ доставлен \U00002705 \U00002705 \U00002705'
FINISH_DEAL_BUTTON_CB = 'finish_deal'
WAREHOUSE_RETURN_DEAL_BUTTON_TEXT = 'Заказ вернулся на склад \U0001F3EA'
WAREHOUSE_RETURN_DEAL_BUTTON_CB = 'warehouse_return_deal'
ORDER_CONTENT_BUTTON_TEXT = 'Содержимое заказа \U0001F4DC'
ORDER_CONTENT_BUTTON_CB = 'deal_order_content'
BACK_TO_CUR_DEALS_LIST_BUTTON_TEXT = 'Назад к списку заказов \U000021A9'
BACK_TO_CUR_DEALS_LIST_BUTTON_CB = 'return_to_deals_list'
BACK_TO_CUR_DEAL_BUTTON_TEXT = 'Назад к заказу'
BACK_TO_CUR_DEAL_BUTTON_CB = 'return_to_deal'


# deal finish
APPROVE_DEAL_FINISH_BUTTON_TEXT = 'Да, я его доставил'
APPROVE_DEAL_FINISH_BUTTON_CB = 'approve_deal_finish'
APPROVE_DEAL_FINISH_TEXT = 'Подтвердить доставку заказа {}?'
DEAL_TIME_DELIMETER = '\\-'  # suppose deal delivery time is hh:mm - hh:mm interval (delimeter for escaped mdv2 string!)
DEAL_HOURS_MINUTES_DELIMETER = ':'
DEAL_IS_TOO_LATE_TEXT = 'Заказ {} должен был быть доставлен до {}\\.\n' \
                        'Напишите причину опоздания:'
DEAL_IS_IN_WRONG_STAGE_TXT = 'Заказ {} должен находиться в стадии \'*В доставке*\' для завершения\\.'
DEAL_FINISHED = 'Заказ {} успешно доставлен\\!'


# deal warehouse return
APPROVE_WAREHOUSE_RETURN_TEXT = 'Вернуть заказ {} на склад?'
APPROVE_WAREHOUSE_RETURN_BUTTON_TEXT = 'Да, я вернул заказ на склад'
APPROVE_WAREHOUSE_RETURN_BUTTON_CB = 'approve_deal_warehouse_return'
WAREHOUSE_RETURN_TEXT = 'Напишите почему заказ {} возвращен на склад, куда именно ' \
                        'и кому конкретно отдан \\(в одном сообщении\\)'
DEAL_RETURNED_TO_WAREHOUSE = 'Заказ {} возвращен на склад\\!'


ADDRESS_RESOLUTION_LINK = 'https://maps.yandex.ru/?text='

DEAL_TERMINAL_ELT = '*Терминал:* НУЖЕН \n'
DEAL_CHANGE_ELT = '*Сдача с:* {}\n'
DEAL_TO_PAY_ELT = '*К оплате:* {}\n'


DEALS_TYPE_STR_MAPPING = {
    UserData.DealsType.DELIVERS_TODAY: 'сегодня в доставке',
    UserData.DealsType.DELIVERS_TOMORROW: 'завтра в доставке',
    UserData.DealsType.IN_ADVANCE: 'назначенных \\(заранее\\)',
    UserData.DealsType.FINISHED_LATE: 'завершенных \\(с опозданием\\){}',
    UserData.DealsType.FINISHED_IN_TIME: 'завершенных \\(вовремя\\){}'
}

DEALS_DATE_ELT = ' на {}'
DEAL_TOTAL_ORDERS_HEADER = 'Всего {} заказов: {}\n\n'
DEAL_PAGE_HEADER = 'Страница {} из {}\n\n'

DEAL_PREVIEW_TEMPLATE = \
                '*№ заказа: ПОДРОБНЕЕ ЖМИ \\-\\-\\-\\>* {}\n' \
                '*Время:* {}\n' \
                '*Дата:* {}\n' \
                '*Адрес:* [{}]({})\n' \
                '*Квартира:* {}\n' \
                '*Имя получателя:* {}\n' \
                '*Телефон получателя:* [{}](tel:{})\n' \
                '*Район:* {}\n' \
                '*Комментарий по доставке:* {}\n\n' \
                '*Инкогнито:* {}\n' \
                '{}' \
                '{}' \
                '{}'


DEAL_VIEW_TEMPLATE = \
                '*№ заказа:* {}\n' \
                '*Время:* {}\n' \
                '*Дата:* {}\n' \
                '*Адрес:* [{}]({})\n' \
                '*Квартира:* {}\n' \
                '*Имя получателя:* {}\n' \
                '*Телефон получателя:* [{}](tel:{})\n' \
                '*Район:* {}\n' \
                '*Комментарий по доставке:* {}\n\n' \
                '*Инкогнито:* {}\n' \
                '{}' \
                '{}' \
                '{}\n' \
                '*Подразделение:* {}\n' \
                '*Кто отправил заказ:* {}\n' \
                '*Источник:* {}\n' \
                '*Телефон заказчика \\(если получатель не отвечает\\):*  [{}](tel:{})'

DEAL_DELIMETER = r'`\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-`'



