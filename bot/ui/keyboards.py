"""
Клавиатуры: только построение InlineKeyboard / ReplyKeyboard.
"""
from calendar import monthrange

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from ui.formatters import short, clamp_page, total_pages, PAGE_SIZE, RECEIPTS_PAGE_SIZE, INV_PAGE_SIZE


# ── reply keyboards ───────────────────────────────────────────────────────────

def main_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📸 Загрузить чек")],
            [KeyboardButton(text="📦 Остатки"), KeyboardButton(text="🧾 Чеки")],
            [KeyboardButton(text="📊 Расход")],
        ],
        resize_keyboard=True,
    )

def main_menu_admin_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📸 Загрузить чек")],
            [KeyboardButton(text="📦 Остатки"), KeyboardButton(text="🧾 Чеки")],
            [KeyboardButton(text="📊 Расход")],
        ],
        resize_keyboard=True,
    )

def main_menu_operator_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📸 Загрузить чек")],
            [KeyboardButton(text="🧾 Чеки")],
        ],
        resize_keyboard=True,
    )


def upload_mode_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="⬅️ Меню")]],
        resize_keyboard=True,
    )


# ── receipt keyboards ─────────────────────────────────────────────────────────

def receipt_page_kb(
    receipt_id: int, status: str, page: int, pages: int, has_unmatched_items: bool
) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()

    if pages > 1:
        if page > 0:
            b.button(text="◀️", callback_data=f"r:page:{receipt_id}:{page-1}")
        b.button(text=f"{page+1}/{pages}", callback_data="noop")
        if page < pages - 1:
            b.button(text="▶️", callback_data=f"r:page:{receipt_id}:{page+1}")
        b.adjust(3)

    if status in ("parsed", "edited"):
        b.button(text="➕ Добавить",      callback_data=f"r:add:{receipt_id}:{page}")
        b.button(text="✏️ Редактировать", callback_data=f"r:edit:{receipt_id}:{page}")
        b.button(text="🗑 Удалить",       callback_data=f"r:del:{receipt_id}:{page}")
        b.button(text="🔗 Матчинг",       callback_data=f"r:match:{receipt_id}:{page}")
        if not has_unmatched_items:
            b.button(text="✅ Применить",      callback_data=f"r:apply:{receipt_id}")
        else:
            b.button(text="⚠ Сначала сматчить", callback_data="noop")
        b.adjust(2, 2, 1)

    if status == "applied":
        b.button(text="↩️ Откат", callback_data=f"r:rollback:{receipt_id}")
        b.adjust(1)

    b.button(text="⬅️ Меню", callback_data="nav:menu")
    b.adjust(1)
    return b.as_markup()


def edit_items_page_kb(receipt_id: int, items: list[dict], page: int) -> InlineKeyboardMarkup:
    pages = total_pages(len(items))
    page = clamp_page(page, pages)
    start = page * PAGE_SIZE

    b = InlineKeyboardBuilder()
    for it in items[start : start + PAGE_SIZE]:
        name = short(it.get("product_code_raw"), 28)
        b.button(
            text=f"{name} | qty={it.get('qty')}",
            callback_data=f"i:pick:{receipt_id}:{it['id']}",
        )
    b.adjust(1)
    _pagination(b, pages, page, f"i:page:{receipt_id}")
    b.button(text="⬅️ Назад", callback_data=f"r:view:{receipt_id}:{page}")
    b.adjust(1)
    return b.as_markup()


def delete_items_page_kb(receipt_id: int, items: list[dict], page: int) -> InlineKeyboardMarkup:
    pages = total_pages(len(items))
    page = clamp_page(page, pages)
    start = page * PAGE_SIZE

    b = InlineKeyboardBuilder()
    for it in items[start : start + PAGE_SIZE]:
        name = short(it.get("product_code_raw"), 28)
        b.button(text=f"🗑 {name}", callback_data=f"d:pick:{receipt_id}:{page}:{it['id']}")
    b.adjust(1)
    _pagination(b, pages, page, f"d:page:{receipt_id}")
    b.row(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"r:view:{receipt_id}:{page}"))
    return b.as_markup()


def match_items_page_kb(receipt_id: int, items: list[dict], page: int) -> InlineKeyboardMarkup:
    target = [it for it in items if not it.get("product_id")]
    pages = total_pages(len(target))
    page = clamp_page(page, pages)
    start = page * PAGE_SIZE

    b = InlineKeyboardBuilder()
    for it in target[start : start + PAGE_SIZE]:
        name = short(it.get("product_code_raw"), 28)
        b.button(text=f"⚠ {name}", callback_data=f"m:item:{receipt_id}:{page}:{it['id']}")
    b.adjust(1)
    _pagination(b, pages, page, f"m:page:{receipt_id}")
    b.row(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"r:view:{receipt_id}:0"))
    return b.as_markup()


def products_page_kb(
    receipt_id: int, receipt_page: int, item_id: int, products: list[dict], page: int
) -> InlineKeyboardMarkup:
    pages = total_pages(len(products))
    page = clamp_page(page, pages)
    start = page * PAGE_SIZE

    b = InlineKeyboardBuilder()
    for p in products[start : start + PAGE_SIZE]:
        code = short(p.get("code"), 18)
        name = short(p.get("name") or "", 18)
        title = f"{code} - {name}" if name else code
        b.button(
            text=title,
            callback_data=f"m:prod:{receipt_id}:{receipt_page}:{item_id}:{p['id']}:{page}",
        )
    b.adjust(1)

    if pages > 1:
        b.row(
            InlineKeyboardButton(text="◀️", callback_data=f"m:prodpage:{receipt_id}:{receipt_page}:{item_id}:{page-1}"),
            InlineKeyboardButton(text=f"{page+1}/{pages}", callback_data="noop"),
            InlineKeyboardButton(text="▶️", callback_data=f"m:prodpage:{receipt_id}:{receipt_page}:{item_id}:{page+1}"),
        )
    b.row(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"r:match:{receipt_id}:{receipt_page}"))
    return b.as_markup()


def cancel_kb(receipt_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="Отмена", callback_data=f"i:cancel:{receipt_id}")
    return b.as_markup()


# ── receipts list keyboard ────────────────────────────────────────────────────

def receipts_list_kb(chunk: list[dict], page: int, pages: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for r in chunk:
        b.button(
            text=f"Открыть #{r.get('id')} ({r.get('status', '—')})",
            callback_data=f"rc:open:{r.get('id')}:{page}",
        )
    b.adjust(1)
    _pagination(b, pages, page, "rc:page")

    b.row(
        InlineKeyboardButton(text="Все",          callback_data="rc:filter:all:0"),
        InlineKeyboardButton(text="Не применены", callback_data="rc:filter:not_applied:0"),
        InlineKeyboardButton(text="Применены",    callback_data="rc:filter:applied:0"),
    )
    b.row(InlineKeyboardButton(text="⬅️ Меню", callback_data="nav:menu"))
    return b.as_markup()


# ── inventory keyboards ───────────────────────────────────────────────────────

def inventory_list_kb(chunk: list[dict], page: int, pages: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for r in chunk:
        iid = r.get("ingredient_id") or r.get("id")
        name = short(r.get("ingredient_name") or r.get("name"), 28)
        b.button(text=name, callback_data=f"inv:open:{iid}:{page}")
    b.adjust(1)
    _pagination(b, pages, page, "inv:page")
    b.row(InlineKeyboardButton(text="🛒 Закупка", callback_data="inv:purchase"))
    b.row(InlineKeyboardButton(text="⬅️ Меню", callback_data="nav:menu"))
    return b.as_markup()


def purchase_plan_kb(list_page: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🔄 Обновить", callback_data="inv:purchase")
    b.button(text="⬅️ Назад",   callback_data=f"inv:page:{list_page}")
    b.button(text="⬅️ Меню",    callback_data="nav:menu")
    b.adjust(1)
    return b.as_markup()


def inventory_detail_kb(list_page: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="⬅️ Назад", callback_data=f"inv:page:{list_page}")
    b.button(text="⬅️ Меню",  callback_data="nav:menu")
    b.adjust(1)
    return b.as_markup()


# ── consumption keyboards ─────────────────────────────────────────────────────

def consumption_period_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="📅 День",    callback_data="cons:day")
    b.button(text="📆 Неделя",  callback_data="cons:week")
    b.button(text="🗓 Месяц",   callback_data="cons:month")
    b.button(text="⬅️ Меню",    callback_data="nav:menu")
    b.adjust(3, 1)
    return b.as_markup()


def calendar_kb(year: int, month: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text=f"{year}-{month:02d}", callback_data="noop"))

    for d in ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]:
        b.button(text=d, callback_data="noop")
    b.adjust(7)

    first_wd, days_in_month = monthrange(year, month)
    first_wd = (first_wd + 6) % 7  # Monday=0

    for _ in range(first_wd):
        b.button(text=" ", callback_data="noop")
    for day in range(1, days_in_month + 1):
        b.button(text=str(day), callback_data=f"cal:pick:{year}:{month}:{day}")
    b.adjust(7)

    prev_y, prev_m = (year, month - 1) if month > 1 else (year - 1, 12)
    next_y, next_m = (year, month + 1) if month < 12 else (year + 1, 1)
    b.row(
        InlineKeyboardButton(text="◀️", callback_data=f"cal:nav:{prev_y}:{prev_m}"),
        InlineKeyboardButton(text="▶️", callback_data=f"cal:nav:{next_y}:{next_m}"),
    )
    b.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="cons:back"))
    return b.as_markup()


# ── internal helper ───────────────────────────────────────────────────────────

def _pagination(b: InlineKeyboardBuilder, pages: int, page: int, prefix: str) -> None:
    """Добавляет ряд пагинации ◀ N/M ▶ к билдеру."""
    if pages <= 1:
        return
    row = []
    if page > 0:
        row.append(InlineKeyboardButton(text="◀️", callback_data=f"{prefix}:{page-1}"))
    row.append(InlineKeyboardButton(text=f"{page+1}/{pages}", callback_data="noop"))
    if page < pages - 1:
        row.append(InlineKeyboardButton(text="▶️", callback_data=f"{prefix}:{page+1}"))
    b.row(*row)