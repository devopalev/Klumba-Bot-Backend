from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import datetime
import calendar
import logging

import source.config as cfg

logger = logging.getLogger(__name__)

TIMES_ROW_SIZE = 6
TIMES_LIST = [
    '00:00',
    '01:00',
    '02:00',
    '03:00',
    '04:00',
    '05:00',
    '06:00',
    '07:00',
    '08:00',
    '09:00',
    '10:00',
    '11:00',
    '12:00',
    '13:00',
    '14:00',
    '15:00',
    '16:00',
    '17:00',
    '18:00',
    '19:00',
    '20:00',
    '21:00',
    '22:00',
    '23:00'
]

DELIMETER = '_'
CB_PREFIX = 'CAL'
PATTERN = '^' + CB_PREFIX + DELIMETER + '.+$'
TODAY_BUTTON_TEXT = 'Сегодня'


class State:
    IGNORE = 'IGNORE'
    DAY = 'DAY'
    HOUR = 'HOUR'
    PREV_MONTH = 'PREVMONTH'
    NEXT_MONTH = 'NEXTMONTH'
    TODAY = 'TODAY'


def create_callback_data(action, year, month, day, hour):
    return CB_PREFIX + DELIMETER + DELIMETER.join([action, str(year), str(month), str(day), str(hour)])


def separate_callback_data(data):
    return data.split(DELIMETER)


def create_calendar(year=None, month=None):
    now = datetime.datetime.now(tz=cfg.TIMEZONE)
    if year is None:
        year = now.year
    if month is None:
        month = now.month

    data_ignore = create_callback_data(State.IGNORE, year, month, 0, 0)
    keyboard = []
    # First row - Month and Year
    row = []

    with calendar.different_locale('ru_RU.UTF-8'):
        row.append(InlineKeyboardButton(calendar.month_name[month] + " " + str(year), callback_data=data_ignore))

    keyboard.append(row)
    # Second row - Week Days
    row = []
    for day in ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]:
        row.append(InlineKeyboardButton(day, callback_data=data_ignore))
    keyboard.append(row)

    my_calendar = calendar.monthcalendar(year, month)
    for week in my_calendar:
        row = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(" ", callback_data=data_ignore))
            else:
                row.append(InlineKeyboardButton(str(day), callback_data=create_callback_data(State.DAY, year, month,
                                                                                             day, 0)))
        keyboard.append(row)

    # Buttons
    row = [InlineKeyboardButton("<", callback_data=create_callback_data(State.PREV_MONTH, year, month, day, 0)),
           InlineKeyboardButton(" ", callback_data=data_ignore),
           InlineKeyboardButton(">", callback_data=create_callback_data(State.NEXT_MONTH, year, month, day, 0))]

    keyboard.append(row)

    today = [InlineKeyboardButton(TODAY_BUTTON_TEXT,
                                  callback_data=create_callback_data(State.TODAY, now.year, now.month, now.day, 0))]

    keyboard.append(today)

    return keyboard


def create_timesheet(year, month, day):
    keyboard = []
    row = []

    for i, t in enumerate(TIMES_LIST):
        if row and i % TIMES_ROW_SIZE == 0:
            keyboard.append(row)
            row = []

        row.append(InlineKeyboardButton(t, callback_data=create_callback_data(State.HOUR, year, month, day, i)))

    if row:
        keyboard.append(row)

    return InlineKeyboardMarkup(keyboard)


def process_calendar_selection(update, context, with_hours=True):
    def day_handler(_query, _context, _with_hours, _year, _month, _day):
        if _with_hours:
            _context.bot.edit_message_text(text=_query.message.text,
                                           chat_id=_query.message.chat_id,
                                           message_id=_query.message.message_id,
                                           reply_markup=create_timesheet(int(year), int(month), int(day))
                                           )
            return False, None
        else:
            return True, datetime.datetime(int(_year), int(_month), int(_day))

    ret_data = (False, None)
    query = update.callback_query

    (prefix, action, year, month, day, hour) = separate_callback_data(query.data)
    curr = datetime.datetime(int(year), int(month), 1)

    if action == State.IGNORE:
        pass
    elif action == State.DAY:
        ret_data = day_handler(query, context, with_hours, year, month, day)
    elif action == State.HOUR:
        # context.bot.edit_message_text(text=query.message.text,
        #                               chat_id=query.message.chat_id,
        #                               message_id=query.message.message_id
        #                               )
        ret_data = True, datetime.datetime(int(year), int(month), int(day), int(hour), tzinfo=cfg.TIMEZONE)
    elif action == State.PREV_MONTH:
        pre = curr - datetime.timedelta(days=1)
        context.bot.edit_message_text(text=query.message.text,
                                      chat_id=query.message.chat_id,
                                      message_id=query.message.message_id,
                                      reply_markup=InlineKeyboardMarkup(create_calendar(int(pre.year), int(pre.month))))
    elif action == State.NEXT_MONTH:
        ne = curr + datetime.timedelta(days=31)
        context.bot.edit_message_text(text=query.message.text,
                                      chat_id=query.message.chat_id,
                                      message_id=query.message.message_id,
                                      reply_markup=InlineKeyboardMarkup(create_calendar(int(ne.year), int(ne.month))))

    elif action == State.TODAY:
        ret_data = day_handler(query, context, with_hours, year, month, day)
    else:
        logger.error('Unknown calendar action: %s'), action

    return ret_data
