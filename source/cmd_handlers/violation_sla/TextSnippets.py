import source.http_server.TextSnippets as HttpTxt
import source.Commands as Cmd

REQUEST_DECLINE_COMMENT = 'Отклоняем заказ {}\\.\n' \
                          'Напишите, почему?'

REAPPROVE_BUTTON_TEXT = 'Исправлено, отправить на пересогласование \U00002705'
REAPPROVE_BUTTON_KEY_PREFIX = 'festive_reapprove'

FESTIVE_ACTION_PATTERN = '^(' + HttpTxt.FESTIVE_APPROVE_BUTTON_KEY + '|' + HttpTxt.FESTIVE_DECLINE_BUTTON_KEY + ')' \
                         + Cmd.CMD_DELIMETER + r'(\d+)$'
FESTIVE_REAPPROVE_PATTERN = '^' + REAPPROVE_BUTTON_KEY_PREFIX + Cmd.CMD_DELIMETER + r'(\d+)$'

DECLINED_HEADER = '{} *ОТКЛОНЕН*\U0000274C \n'
APPROVED_HEADER = '{} *СОГЛАСОВАН*\U00002705 \n'
REAPPROVED_HEADER = '{} *ИСПРАВЛЕН*\U00002705 \n'

DEAL_DECLINED = '*Кто отклонил:* {}\n' \
                '*Комментарий по отклонению:* {}\n\n' \
                '*Кто принял заказ:* {}\n' \
                '*Подразделение:* {}\n' \
                '*Ссылка:* {}\n' \
                '*Что заказано:* {}\n' \
                r'`\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-`' \
                '\n*ИНФО ПО ЗАКАЗУ*\n' \
                '*Дата:* {}\n' \
                '*Время:* {}\n' \
                '*Сумма:* *{}*\n' \
                '*Источник:* {}\n' \
                '*Контакт:* {}\n' \
                '{}' \
                '*Доставка / Самовывоз:* {}\n' \
                '*Район доставки:* {}\n' \
                '*Город / Улица / Дом*: {}\n' \
                '*Комментарий по доставке:* {}\n\n' \
                '*Способ оплаты:* {}\n' \
                '*Тип оплаты:* {}\n' \
                '{}' \
                '{}' \
                '{}' \
                '*К оплате:* {}\n' \
                '*Статус оплаты:* {}\n'
#               '{reserve photo}'


UNAPPROVED_HEADER_REPLACEMENT_PATTERN = ''

USER_NOT_FOUND = 'Пользователь {} не найден\\. \n' \
                 'Нужно зарегистрироваться в @KlumbaOperatorBot'


UNPROCESSED_STAT_TEMPLATE = 'Вы не решили что делать с *{}* заказами\n'
DECLINED_SUBDIV_STAT_TEMPLATE = 'Поздразделение *{}* не обработало *{}* несогласованных заказов\\.\n'
SPECIFIC_SUBDIV_STAT_TEMPLATE = 'Нужно исправить *{}* отклоненных заказов\\.\n'
