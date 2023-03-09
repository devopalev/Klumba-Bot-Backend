ASK_FOR_DEAL_NUMBER = 'Введите номер заказа:'

WRONG_DEAL_STAGE = 'Заказ должен находиться в одной из стадий: ' \
                   '*Оплачен\\Предоплачен*, *Обработан, но ждет поставки*, *Обработан, товар отложен\\Не треб*\n' \
                   'Измените стадию заказа и попробуйте снова\\.'

FLORIST_ALREADY_SET_HEADER = 'Флорист *{}* уже назначен на заказ *{}*\\.'
CHANGE_FLORIST_BUTTON_TEXT = 'Изменить'
CHANGE_FLORIST_BUTTON_CB = 'change_florist'
LEAVE_FLORIST_BUTTON_TEXT = 'Оставить флориста {}'
LEAVE_FLORIST_BUTTON_CB = 'leave_florist'

CHOOSE_FLORIST_HEADER = '*ВВЕДИТЕ НАЧАЛО ФАМИЛИИ ФЛОРИСТА:*'
SHOW_ALL_FLORISTS_BUTTON_TEXT = 'Показать весь список'
SHOW_ALL_FLORISTS_BUTTON_CB = 'show_all'

FLORISTS_LIST_SURNAME_STARTS_ELT = ' с фамилией на *{}*'
FLORISTS_LIST_HEADER = 'Флористы{}:\n'
FLORISTS_PAGE_HEADER = 'Страница {} из {}\n\n'
NEXT_PAGE_TEXT = '>'
NEXT_PAGE_CB = 'next_page'
PREV_PAGE_TEXT = '<'
PREV_PAGE_CB = 'prev_page'
FLORIST_CHOOSE_BUTTON_PATTERN = r'^(\d+)$'

DEAL_UPDATED = 'На заказ {} назначен флорист {}\\!'

FLORIST_TEMPLATE = '*{}*\n*{}*\n\n'

DEAL_INFO_TEMPLATE = '*Заказ №*: {}\n' \
                     '*Что заказано*: {}\n' \
                     '*Контакт*: {}\n' \
                     '*Флорист*: {}\n' \
                     '*Кто принял заказ*: {}\n' \
                     '*Инкогнито*: {}\n' \
                     '*Комментарий к товару*: {}\n' \
                     '*Комментарий по доставке*: {}\n' \
                     '*Сумма заказа общая\\(итоговая\\):* {}\n\n' \
                     '*Тип оплаты*: {}\n' \
                     '*Способ оплаты*: {}\n' \
                     '*Статус оплаты*: {}\n' \
                     '*Предоплата*: {}\n' \
                     '*К оплате*: {}\n' \
                     '*Курьер*: {}\n' \
                     '*Тип заказа*: {}'
