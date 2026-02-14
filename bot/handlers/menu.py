"""handlers/menu.py — /start, ⬅️ Меню, nav:menu"""
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import auth
from ui import WELCOME_TEXT, main_menu_kb
from ui.keyboards import main_menu_admin_kb, main_menu_operator_kb

router = Router(name="menu")


def setup():
    @router.message(F.text.in_({"/start", "⬅️ Меню"}))
    async def cmd_menu(message: Message, state: FSMContext, role: str | None):
        if not await auth.ensure_access(message):
            return
        from handlers.states import Flow
        await state.set_state(Flow.idle)
        kb = main_menu_admin_kb() if role == "admin" else main_menu_operator_kb()
        await message.answer(WELCOME_TEXT, reply_markup=kb)

    @router.callback_query(F.data == "nav:menu")
    async def cb_menu(call: CallbackQuery, state: FSMContext, role: str | None):
        from handlers.states import Flow
        await state.set_state(Flow.idle)
        kb = main_menu_admin_kb() if role == "admin" else main_menu_operator_kb()
        await call.message.answer(WELCOME_TEXT, reply_markup=kb)
        await call.answer()

    @router.callback_query(F.data == "noop")
    async def cb_noop(call: CallbackQuery):
        await call.answer()

    return router