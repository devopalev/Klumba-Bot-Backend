from source import Commands as Cmd
from source import TextSnippets as GlobalTxt

ASK_FOR_DEAL_NUMBER = 'Введите номер заказа:'
WRONG_DEAL_STAGE = 'Заказ должен находиться в в стадии *Оплачен\\Предоплачен*\\.\n' \
                   'Измените стадию заказа и попробуйте снова\\.'

WILL_YOU_RESERVE = 'Резервируем товар для заказа {}?'
RESERVE_YES_TXT = 'Отложить товар сейчас  \U0001F4F7'
RESERVE_YES_KEY = 'reserve_yes'
SWITCH_STAGE_WAITING_FOR_SUPPLY_TXT = 'Ждет поставки \U0000231B'
SWITCH_STAGE_WAITING_FOR_SUPPLY_KEY = 'reserve_waiting_for_supply'
SWITCH_STAGE_PROCESSED_TXT = 'Резерв не нужен \U0001F90C'
SWITCH_STAGE_PROCESSED_KEY = 'reserve_not_needed'
RESERVE_CB_PATTERN = '^' + RESERVE_YES_KEY + '$|^' + SWITCH_STAGE_WAITING_FOR_SUPPLY_KEY + '$|^' \
                     + SWITCH_STAGE_PROCESSED_KEY + '$'

BITTER_TWIX_WARNING = 'Подтверждаю, что резерв не нужен \\- будет горький твикс, если это не так\\.\n' \
                      'Резерв товара нужно делать *ТОЛЬКО через телеграм\\-бота*,\n' \
                      'НО если заказ изготавливается прямо сейчас \\- переведи на стадию *У Флориста*'

BITTER_TWIX_APPROVE_TXT = 'Подтверждаю'
BITTER_TWIX_APPROVE_KEY = 'bt_approve'
BITTER_TWIX_SET_FLORIST_TXT = 'Назначить флориста'
BITTER_TWIX_SET_FLORIST_KEY = 'bt_set_florist'

ASK_FOR_PHOTO_TEXT = 'Загрузите одно или несколько фото резерва\\.\n' \

PHOTO_LOADED_TEXT = 'Фото успешно загружено\\.\n' \
                    'Загрузите другие фото, или завершите загрузку\\.'

FINISH_PHOTO_LOADING_TXT = 'Завершить'
FINISH_PHOTO_LOADING_KEY = 'finish_photo_loading'

NO_PHOTOS_TEXT = 'Нет загруженных фото резерва\\.'

REQUEST_DESCRIPTION = 'Введите текстовое описание отложенного:'


SWITCH_STAGE_CB_PATTERN = '^' + SWITCH_STAGE_WAITING_FOR_SUPPLY_KEY + '$|^' + SWITCH_STAGE_PROCESSED_KEY + '$'

CALENDAR_DESCRIPTION = 'Выберите дату, затем время поставки:\n'
DATE_TOO_EARLY = 'Дата поставки должна быть позже текущей!\n' \
                 'Попробуйте снова.'

NO_RESERVE_NEEDED_STUB = 'Резерв не нужен'



