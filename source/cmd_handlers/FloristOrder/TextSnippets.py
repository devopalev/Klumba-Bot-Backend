from source import Commands as Cmd
from source import TextSnippets as GlobalTxt

NO_ORDERS = 'Нет назначенных заказов\\.'
RESERVE_POSTFIX = ' фото'


POSTCARD_ELT = '*Текст открытки:* {}\n'
ORDER_TEMPLATE = 'Заказ {} из {}\n' \
                 '*№ заказа*: {}\n' \
                 '*Доставка/Самовывоз*: {}\n' \
                 '*Что заказано*: {}\n' \
                 '*Комментарий к товару*: {}\n' \
                 '{}' \
                 '*Сумма*: {}\n' \
                 '*Дата*: {}\n' \
                 '*Время*: {}\n'

RESERVE_VIEWER_TEXT = 'Резерв товара: \n'

NO_PHOTOS_TEXT = 'Загрузите фото перед укомплектованием заказа\\.'

NEXT_ORDER_BUTTON_TEXT = '>'
NEXT_ORDER_BUTTON_CB = 'next_order'
PREV_ORDER_BUTTON_TEXT = '<'
PREV_ORDER_BUTTON_CB = 'prev_order'
SWITCH_ORDER_CB_PATTERN = '^' + NEXT_ORDER_BUTTON_CB + '$|^' + PREV_ORDER_BUTTON_CB + '$'

VIEW_RESERVE_PHOTO_BUTTON_TEXT = 'Фото отложенного'
VIEW_RESERVE_PHOTO_BUTTON_CB = 'reserve_photo'
EQUIP_BUTTON_TEXT = 'Укомплектовать'
EQUIP_BUTTON_CB = 'equip'
BACK_TO_ORDER_BUTTON_TEXT = 'Назад к заказам'
BACK_TO_ORDER_BUTTON_CB = 'back_to_orders'

