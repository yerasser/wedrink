from ui.formatters import (
    fmt_receipt_page,
    fmt_receipts_list,
    fmt_inventory_list,
    fmt_inventory_detail,
    fmt_consumption,
    fmt_purchase_plan
)
from ui.keyboards import (
    main_menu_kb,
    upload_mode_kb,
    receipt_page_kb,
    edit_items_page_kb,
    delete_items_page_kb,
    match_items_page_kb,
    products_page_kb,
    cancel_kb,
    receipts_list_kb,
    inventory_list_kb,
    inventory_detail_kb,
    consumption_period_kb,
    calendar_kb,
    purchase_plan_kb
)

WELCOME_TEXT      = "🍹 WeDrink • Склад\nВыбери действие ниже:"
UPLOAD_MODE_TEXT  = "📸 Загрузка чека\nОтправь фото чека одним сообщением."
NO_ACCESS_TEXT    = "⛔️ Нет доступа"
CHECKING_TEXT     = "🔐 Проверяю доступ…"
PROCESSING_TEXT   = "⏳ Идёт обработка чека…"
TIMEOUT_TEXT      = "⏳ Чек ещё обрабатывается. Открой позже через «Чеки»."

EDIT_ITEM_TEXT = (
    "Редактирование позиции\n\n"
    "Формат: Код Количество Цена Сумма\n"
    "Пример: 12 2 650 1300"
)
ADD_ITEM_TEXT = (
    "Добавление позиции\n\n"
    "Формат: Код Количество Цена\n"
    "Пример: 12 2 650"
)

__all__ = [
    "fmt_receipt_page", "fmt_receipts_list", "fmt_inventory_list",
    "fmt_inventory_detail", "fmt_consumption", "fmt_purchase_plan",
    "main_menu_kb", "upload_mode_kb", "receipt_page_kb", "edit_items_page_kb",
    "delete_items_page_kb", "match_items_page_kb", "products_page_kb", "cancel_kb",
    "receipts_list_kb", "inventory_list_kb", "inventory_detail_kb",
    "consumption_period_kb", "calendar_kb", "purchase_plan_kb",
    "WELCOME_TEXT", "UPLOAD_MODE_TEXT", "NO_ACCESS_TEXT", "CHECKING_TEXT",
    "PROCESSING_TEXT", "TIMEOUT_TEXT", "EDIT_ITEM_TEXT", "ADD_ITEM_TEXT",
]

