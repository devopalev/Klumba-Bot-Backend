# TODO: can't use Enum for now:
# https://github.com/python-telegram-bot/python-telegram-bot/pull/2817

class State:
    LOGIN_REQUESTED = 1
    IN_OPERATOR_MENU = 2

    # equip deal
    EQUIP_SET_DEAL_NUMBER = 3  # Запрошен номер заказа
    EQUIP_REPEATEDLY_APPROVE = 4  # Подтверждаем, что хотим повторно укомплектовать заказ
    EQUIP_SET_PHOTOS = 5  # Загружаем фото заказа
    EQUIP_SET_POSTCARD_FACIAL = 6  # Загружаем лицевую сторону открытки
    EQUIP_SET_POSTCARD_REVERSE = 7  # Загружаем оборотную сторону открытки
    EQUIP_SET_CHECKLIST = 8  # Запрошено фото бумажного чек-листа

    # send order loading actions
    SEND_SET_DEAL_NUMBER = 9  # Запрошен номер заказа
    SEND_CHANGE_COURIER = 10  # Запрошена реакция на изменение курьера
    SEND_SET_COURIER = 11  # Запрошен выбор полный список / начало фамилии
    SEND_CHOOSE_COURIER = 12  # Запрошен выбор курьера из списка
    SEND_COURIER_EQUIPPED_REQUEST = 13  # Обеспечен ли курьер?

    # process order
    PROCESS_SETTING_DEAL_NUMBER = 14  # Запрошен номер заказа
    PROCESS_WILL_YOU_RESERVE = 15  # Выбираем варианты резервирования
    PROCESS_LOADING_PHOTOS = 16  # Загружаем фото резерва
    PROCESS_DESCRIPTION = 17  # Заполняем описание резерва
    PROCESS_SUPPLY_CALENDAR = 18  # Работаем с календарем поставок
    PROCESS_APPROVE_RESERVE_NOT_NEEDED = 19  # Подтверждаем отказ от резерва

    # florist setting - # 4
    SETTING_FLORIST_DEAL_NUMBER = 20  # Запрошен номер заказа
    SETTING_FLORIST_CHANGE_FLORIST = 21  # Запрошена реакция на изменение флориста
    SETTING_FLORIST_SET_FLORIST = 22  # Запрошен выбор полный список / начало фамилии
    SETTING_FLORIST_CHOOSE_FLORIST = 23  # Запрошен выбор флориста из списка

    # florist operations - # 5
    FLORIST_VIEWS_ORDER = 24  # Просмотр конкретного заказа
    FLORIST_VIEWS_RESERVE_PHOTO = 25  # Просмотр фото резерва

    # courier's actions
    IN_COURIER_MENU = 26
    COURIER_CHOOSING_FINISHED_DATE = 27  # Выбор даты для просмотра завершенных
    COURIER_CHOOSING_FINISHED_TYPE = 28  # Выбор опоздавших / доставленных вовремя для завершенных
    COURIER_VIEWS_DEAL = 29  # Просматривает сделку
    COURIER_VIEWS_DEAL_ORDER = 30  # Просматривает "Что заказано"
    COURIER_FINISHES_DEAL = 31  # Подтверждает завершение заказа
    COURIER_WRITING_LATE_REASON = 32  # Пишет причину опоздания, если заказ опоздал
    COURIER_RETURNS_DEAL_TO_WAREHOUSE = 33  # Подтвержает возврат заказа на склад
    COURIER_WRITING_WAREHOUSE_RETURN_REASON = 34  # Пишет причину возврата, кому отдал и куда
