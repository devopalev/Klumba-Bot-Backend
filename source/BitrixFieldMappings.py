# deal stages
DEAL_NEW_STATUS_ID = 'C17:2'  # Новый заказ
DEAL_IN_PROCESS_STATUS_ID = 'C17:4'  # В обработке \ Надо проверить
DEAL_PAID_PREPAID_STATUS_ID = 'C17:UC_J0R30S'  # Оплачен \ Предоплачен
DEAL_PROCESSED_WAITING_FOR_SUPPLY_STATUS_ID = 'C17:13'  # Обработан, но ждет поставки
DEAL_PROCESSED_ON_HOLD_STATUS_ID = 'C17:6'  # Обработан,тов.отлож/не треб.
DEAL_PRINTED_STATUS_ID = 'C17:UC_EQMV7Y'  # Распечатан
DEAL_FLORIST_STATUS_ID = 'C17:7'  # У Флориста (Изготавливается)
DEAL_PROCESSED_1C_STATUS_ID = 'C17:8'  # Обработан в 1С
DEAL_IS_EQUIPPED_STATUS_ID = 'C17:NEW'  # Заказ укомплектован
DEAL_UNAPPROVED_STATUS_ID = 'C17:9'  # Несогласовано
DEAL_APPROVED_STATUS_ID = 'C17:10'  # Согласовано
DEAL_IS_IN_DELIVERY_STATUS_ID = 'C17:FINAL_INVOICE'  # В доставке
DEAL_SUCCESSFUL_STATUS_ID = 'C17:WON'  # Сделка успешна
DEAL_LOSE_STATUS_ID = 'C17:LOSE'  # Удален \ Провален
DEAL_STAGE_LIST_REFERENCE_ID = 'DEAL_STAGE_17'  # Стадии по Базе Заказов (направление 17)

# deal field values
# Доставка \ Самовывоз
DEAL_IS_FOR_TAKEAWAY = '461'
DEAL_IS_FOR_DELIVERY = '459'

# Есть резерв
DEAL_HAS_RESERVE_YES = '2551'
DEAL_HAS_RESERVE_YES_FRIENDLY = 'Да'
DEAL_HAS_RESERVE_NO = '2553'

# Есть открытка
DEAL_HAS_POSTCARD_YES = '2543'

# Оплата
DEAL_PAY_PREPAID_FRIENDLY = 'Предоплата'
DEAL_PAY_PERSONAL_FRIENDLY = 'При получении'
DEAL_PAY_TERMINAL_FRIENDLY = 'Терминал'
DEAL_PAY_CHANGE_FRIENDLY = 'Сдача с:'
DEAL_NEED_TERMINAL = '2331'
DEAL_NEED_CHANGE = '2333'

DEAL_TERMINAL_CHANGE_MAPPING = {
   DEAL_NEED_TERMINAL: DEAL_PAY_TERMINAL_FRIENDLY,
   DEAL_NEED_CHANGE: DEAL_PAY_CHANGE_FRIENDLY
}

# Заказ опоздал
DEAL_IS_LATE_YES = '2663'
DEAL_IS_LATE_NO = '2665'

# Заказ вернулся на склад
DEAL_IS_RETURNED_TO_WAREHOUSE_YES = '2845'
DEAL_IS_RETURNED_TO_WAREHOUSE_NO = '2847'


# mappings
DEAL_SUPPLY_METHOD_MAPPING = {
   DEAL_IS_FOR_TAKEAWAY: 'Самовывоз',
   DEAL_IS_FOR_DELIVERY: 'Доставка'
}
# Подтверждаю, что резерв не нужен (горький твикс иначе)
DEAL_ORDER_RESERVE_NOT_NEEDED_APPROVE = '2815'


DEAL_INCOGNITO_MAPPING_CLIENT = {
   '0': False,
   '1': True
}

DEAL_INCOGNITO_MAPPING_OPERATOR = {
   '0': 'нет',
   '1': 'ВНИМАНИЕ \\- ДА\\!'
}


# other field values
# contact
CONTACT_HAS_PHONE = 'Y'

# user positions
FLORIST_POSITION_ID = '2343'  # Флорист
COURIER_POSITION_ID = '2347'  # Курьер

# http server actions
HTTP_ACTION_FESTIVE_PROCESSED = 'festive_processed'


# festive approvement
FESTIVE_APPROVEMENT_YES = '2891'
FESTIVE_APPROVEMENT_NO = '2893'
FESTIVE_APPROVEMENT_NOT_SELECTED = '3003'
# festive dates list
FESTIVE_LIST_IBLOCK_ID = '75'
# actual dates dict {some_id: date}
FESTIVE_LIST_PROPERTY_NAME = 'PROPERTY_225'
