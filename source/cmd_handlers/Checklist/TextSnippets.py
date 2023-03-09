ASK_FOR_DEAL_NUMBER = 'Введите номер заказа:'
WRONG_DEAL_STAGE = 'Заказ должен находиться в стадии *Согласовано*\\.\n' \
                   'Измените стадию заказа и попробуйте снова\\.'


COURIER_ALREADY_SET_HEADER = 'Курьер *{}* уже назначен на заказ *{}*\\.'
CHANGE_COURIER_BUTTON_TEXT = 'Изменить'
CHANGE_COURIER_BUTTON_CB = 'change_courier'
LEAVE_COURIER_BUTTON_TEXT = 'Отправить с курьером {}'
LEAVE_COURIER_BUTTON_CB = 'leave_courier'

CHOOSE_COURIER_HEADER = '*ВВЕДИТЕ НАЧАЛО ФАМИЛИИ КУРЬЕРА:*:'
SHOW_ALL_COURIERS_BUTTON_TEXT = 'Показать весь список'
SHOW_ALL_COURIERS_BUTTON_CB = 'show_all'

COURIERS_LIST_SURNAME_STARTS_ELT = ' с фамилией на *{}*'
COURIERS_LIST_HEADER = 'Курьеры{}:\n'
COURIERS_PAGE_HEADER = 'Страница {} из {}\n\n'
NEXT_PAGE_TEXT = '>'
NEXT_PAGE_CB = 'next_page'
PREV_PAGE_TEXT = '<'
PREV_PAGE_CB = 'prev_page'
COURIER_CHOOSE_BUTTON_PATTERN = r'^(\d+)$'


DEAL_TERMINAL_ELT = '*Терминал:* НУЖЕН \n'
DEAL_CHANGE_ELT = '*Сдача с:* {}\n'

DEAL_TEMPLATE = 'Заказ *{}*\n' \
                'Выбран курьер: *{}*\n' \
                'Тип оплаты: {}\n' \
                '{}' \
                '{}' \
                'К оплате: {}\n\n' \
                'Загрузите *фото бумажного чек\\-листа*'

DEAL_UPDATED = 'Заказ {} отправлен с курьером {}\\!'
