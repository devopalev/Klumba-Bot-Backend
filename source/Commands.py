from telegram import BotCommand

# general
CMD_PREFIX = '/'
CMD_DELIMETER = '_'

# menu
START = 'start'
CANCEL = 'cancel'
LOGOUT = 'logout'


BOT_COMMANDS_LIST = [BotCommand(START, 'Старт или возврат в меню'),
                     BotCommand(CANCEL, 'Отмена операции'),
                     BotCommand(LOGOUT, 'Сменить пользователя (выход из системы)')]
