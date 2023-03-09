from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
import datetime
import calendar
import logging

import source.config as cfg

logger = logging.getLogger(__name__)


class TgCalendar:
    CB_PREFIX = 'CAL'
    DELIMITER = '__'
    CB_PATTERN = CB_PREFIX + DELIMITER
    TODAY_BUTTON_TEXT = 'Сегодня'
    TIMES_ROW_SIZE = 6
    TIMES_LIST = ['00:00', '01:00', '02:00', '03:00', '04:00', '05:00', '06:00', '07:00', '08:00', '09:00', '10:00',
                  '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00', '19:00', '20:00','21:00',
                  '22:00', '23:00']

    class _State:
        IGNORE = 'IGNORE'
        DAY = 'DAY'
        HOUR = 'HOUR'
        PREV_MONTH = 'PREVMONTH'
        NEXT_MONTH = 'NEXTMONTH'
        TODAY = 'TODAY'

    def __init__(self, cb_prefix="CAL", no_more_now=False, other_keyboard=None, time_zone=3):
        self.cb_prefix = cb_prefix
        self.cb_pattern = '^' + cb_prefix + self.DELIMITER + '.+$'
        self.time_zone = datetime.timezone(datetime.timedelta(hours=time_zone))
        self.no_more_now = no_more_now
        self.other_keyboard = other_keyboard if other_keyboard else []

    def _create_callback_data(self, action, year, month, day, hour):
        return self.cb_prefix + self.DELIMITER + self.DELIMITER.join([action, str(year), str(month), str(day), str(hour)])

    def _separate_callback_data(self, data):
        return data.split(self.DELIMITER)

    def _create_timesheet(self, year, month, day):
        keyboard = []
        row = []

        for i, t in enumerate(self.TIMES_LIST):
            if row and i % self.TIMES_ROW_SIZE == 0:
                keyboard.append(row)
                row = []

            row.append(InlineKeyboardButton(t, callback_data=self._create_callback_data(self._State.HOUR, year, month, day, i)))

        if row:
            keyboard.append(row)

        keyboard.extend(self.other_keyboard)
        return InlineKeyboardMarkup(keyboard)

    def create_calendar(self, year=None, month=None) -> InlineKeyboardMarkup:
        now = datetime.datetime.now(tz=cfg.TIMEZONE)
        if year is None:
            year = now.year
        if month is None:
            month = now.month

        data_ignore = self._create_callback_data(self._State.IGNORE, year, month, 0, 0)
        keyboard = []
        # First row - Month and Year
        row = []

        # with calendar.different_locale('ru_RU'):
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
                if day == 0 or (self.no_more_now and day > now.day):
                    row.append(InlineKeyboardButton(" ", callback_data=data_ignore))
                else:
                    row.append(InlineKeyboardButton(str(day), callback_data=self._create_callback_data(self._State.DAY, year,
                                                                                                       month, day, 0)))
            keyboard.append(row)

        # Buttons
        row = [InlineKeyboardButton("<", callback_data=self._create_callback_data(self._State.PREV_MONTH, year, month, day, 0)),
               InlineKeyboardButton(" ", callback_data=data_ignore)]

        if self.no_more_now and now.month > month:
            row.append(
                InlineKeyboardButton(">", callback_data=self._create_callback_data(self._State.NEXT_MONTH, year, month, day, 0)))
        else:
            row.append(InlineKeyboardButton(" ", callback_data=data_ignore))

        keyboard.append(row)

        today = [InlineKeyboardButton(self.TODAY_BUTTON_TEXT,
                                      callback_data=self._create_callback_data(self._State.TODAY, now.year, now.month,
                                                                               now.day, now.hour))]

        keyboard.append(today)
        keyboard.extend(self.other_keyboard)
        return InlineKeyboardMarkup(keyboard)

    def process_selection(self, update: Update, context, with_hours=True, edit_message=True):
        ret_data = (False, None)
        query = update.callback_query

        (prefix, action, year, month, day, hour) = self._separate_callback_data(query.data)
        curr = datetime.datetime(int(year), int(month), 1)

        if action == self._State.IGNORE:
            query.answer()

        elif action == self._State.DAY:
            if with_hours:
                keyboard_timesheet = self._create_timesheet(int(year), int(month), int(day))
                if edit_message:
                    query.message.edit_text(text=query.message.text, reply_markup=keyboard_timesheet)
                    ret_data = False, None
                else:
                    ret_data = False, keyboard_timesheet
            else:
                ret_data = True, datetime.datetime(int(year), int(month), int(day))

        elif action == self._State.HOUR:
            ret_data = True, datetime.datetime(int(year), int(month), int(day), int(hour), tzinfo=self.time_zone)

        elif action == self._State.PREV_MONTH:
            pre = curr - datetime.timedelta(days=1)
            keyboard_calendar = self.create_calendar(int(pre.year), int(pre.month))
            if edit_message:
                query.message.edit_text(text=query.message.text, reply_markup=keyboard_calendar)
            else:
                ret_data = False, keyboard_calendar

        elif action == self._State.NEXT_MONTH:
            ne = curr + datetime.timedelta(days=31)
            keyboard_calendar = self.create_calendar(int(ne.year), int(ne.month))
            if edit_message:
                query.message.edit_text(text=query.message.text, reply_markup=keyboard_calendar)
            else:
                ret_data = False, keyboard_calendar

        elif action == self._State.TODAY:
            if with_hours:
                ret_data = True, datetime.datetime(int(year), int(month), int(day))
            else:
                ret_data = True, datetime.datetime(int(year), int(month), int(day), int(hour))
        else:
            logger.error(f'Unknown calendar action: {action}')

        return ret_data
