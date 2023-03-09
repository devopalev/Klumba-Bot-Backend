FIELD_IS_EMPTY_PLACEHOLDER = 'нет'
CANCEL_BUTTON_TEXT = 'Отмена \U0001F6AB'
CANCEL_BUTTON_CB_DATA = 'cancel'
ANY_STRING_PATTERN = '^.*$'  # matching any string without newline characters


SEND_CONTACT_BUTTON_TEXT = 'ВОЙТИ ПО НОМЕРУ ТЕЛЕФОНА'
REQUEST_LOGIN_MESSAGE = 'Добро пожаловать в *Клумба: общий интерфейс*\\!\n' \
                        'Нажмите *' + SEND_CONTACT_BUTTON_TEXT + '* для входа\\.\n' \
                        'КНОПКА НАХОДИТСЯ ПОД ИЛИ НАД КЛАВИАТУРОЙ\\. \n' \
                        'ЕСЛИ ОНА СКРЫТА \\- НУЖНО НАЖАТЬ НА КНОПКУ \U0001F39B РЯДОМ С КЛАВИАТУРОЙ\\.'

AUTHORIZATION_SUCCESSFUL = 'Авторизация пройдена\\!\n' \
                           'Теперь вы можете использовать возможности бота\\.'

AUTHORIZATION_FAILED = '❗ Авторизация не пройдена\\.\n' \
                       'Проверьте настройки мобильного номера в ' \
                       '[профиле битрикс](https://klumba.bitrix24.ru/company/personal/user/) и ' \
                       'совпадает ли он с номером в Вашей учетной записи telegram\\. ' \
                       '\nПосле проверки попробуйте снова\\.\n\n'\
                       + REQUEST_LOGIN_MESSAGE


ASK_FOR_DEAL_NUMBER_TEXT = 'Введите номер заказа\\.'

UNKNOWN_COMMAND = 'Неизвестная команда\\. Попробуйте снова\\.\n'


# operator's menu
MENU_TEXT = 'Меню:\n'
MENU_DEAL_PROCESS_BUTTON_TEXT = 'Обработать заказ \U0001F44C'
MENU_DEAL_PROCESS_BUTTON_CB = 'deal_process'
MENU_DEAL_SET_FLORIST_BUTTON_TEXT = 'Назначить флориста \U0001F469\u200d\U0001F33E'
MENU_DEAL_SET_FLORIST_BUTTON_CB = 'deal_set_florist'
MENU_DEAL_EQUIP_BUTTON_TEXT = 'Укомплектовать заказ \U0001F490'
MENU_DEAL_EQUIP_BUTTON_CB = 'deal_equip'
MENU_DEAL_SEND_BUTTON_TEXT = 'Отправить заказ (назначить курьера) \U0001F69A'
MENU_DEAL_SEND_BUTTON_CB = 'deal_send'
MENU_DEAL_COURIER_BUTTON_TEXT = 'Назначить курьера (заранее) \U0001F468\u200d\U0001F9BC'
MENU_DEAL_COURIER_BUTTON_CB = 'deal_courier'
MENU_DEAL_FLORIST_ORDERS_BUTTON_TEXT = 'Заказы, где я флорист \U0001F5DE'
MENU_DEAL_FLORIST_ORDERS_BUTTON_CB = 'deal_florist_orders'



ERROR_BITRIX_REQUEST = 'Произошла ошибка при обращении к серверу\\.\n' \
                       'Попробуйте снова или подождите некоторое время\\.\n'

BITRIX_DEAL_NUMBER_PATTERN = r'^\d+$'

UNKNOWN_ERROR = 'Произошла непредвиденная ошибка\\.\n' \
                'Попробуйте снова, или подождите некоторое время\\.\n'

DEAL_UPDATED = 'Заказ {} успешно обновлен\\!'

NO_SUCH_DEAL = 'Заказ {} не существует\\.\nПопробуйте снова\\.\n'
