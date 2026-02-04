from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

def kb_draft_actions() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="✅ Confirm", callback_data="draft:confirm")
    b.button(text="✏️ Edit", callback_data="draft:edit")
    b.button(text="🔄 Refresh", callback_data="draft:refresh")
    b.adjust(2, 1)
    return b.as_markup()

def kb_edit_actions() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="✅ Done", callback_data="edit:done")
    b.button(text="❌ Cancel", callback_data="edit:cancel")
    b.adjust(2)
    return b.as_markup()
