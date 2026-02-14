import logging

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import auth
from api import ApiClient
from cache import CacheStore
from tokens import TokenStore
from services import ReceiptService
from handlers.states import Flow
from ui import (
    EDIT_ITEM_TEXT, ADD_ITEM_TEXT,
    fmt_receipt_page, receipt_page_kb,
    edit_items_page_kb, delete_items_page_kb,
    match_items_page_kb, products_page_kb,
    cancel_kb,
)

log = logging.getLogger(__name__)
router = Router(name="items")


def setup(api: ApiClient, tokens: TokenStore, cache: CacheStore):
    svc = ReceiptService(api, tokens, cache)

    async def _show_receipt(target, user_id: int, receipt_id: int, page: int = 0):
        receipt, items = await svc.fetch(user_id, receipt_id)
        text, p, pages = fmt_receipt_page(receipt, items, page)
        kb = receipt_page_kb(receipt_id, receipt["status"], p, pages, svc.has_unmatched(items))
        if isinstance(target, CallbackQuery):
            await target.message.edit_text(text, reply_markup=kb)
        else:
            await target.answer(text, reply_markup=kb)

    def _split(data: str, expected: int) -> list[str] | None:
        parts = data.split(":")
        if len(parts) != expected:
            log.warning("Unexpected callback_data=%r (expected %d parts)", data, expected)
            return None
        return parts

    # ── edit ──────────────────────────────────────────────────────────────────

    @router.callback_query(F.data.startswith("r:edit:"))
    async def edit_items(call: CallbackQuery):
        if not await auth.ensure_access_cb(call):
            return
        p = _split(call.data, 4)
        if not p:
            await call.answer()
            return
        _, _, rid, page = p
        _, items = await svc.fetch(call.from_user.id, int(rid))
        await call.message.edit_text(
            "Выбери позицию:",
            reply_markup=edit_items_page_kb(int(rid), items, int(page)),
        )
        await call.answer()

    @router.callback_query(F.data.startswith("i:pick:"))
    async def edit_pick_item(call: CallbackQuery, state: FSMContext):
        if not await auth.ensure_access_cb(call):
            return
        p = _split(call.data, 4)
        if not p:
            await call.answer()
            return
        _, _, rid, item_id = p
        await state.set_state(Flow.edit_item)
        await state.update_data(receipt_id=int(rid), item_id=int(item_id), page=0)
        await call.message.edit_text(EDIT_ITEM_TEXT, reply_markup=cancel_kb(int(rid)))
        await call.answer()

    @router.callback_query(F.data.startswith("i:page:"))
    async def edit_items_page(call: CallbackQuery):
        if not await auth.ensure_access_cb(call):
            return
        p = _split(call.data, 4)
        if not p:
            await call.answer()
            return
        _, _, rid, page = p
        _, items = await svc.fetch(call.from_user.id, int(rid))
        await call.message.edit_text(
            "Выбери позицию:",
            reply_markup=edit_items_page_kb(int(rid), items, int(page)),
        )
        await call.answer()

    @router.message(Flow.edit_item)
    async def save_item(message: Message, state: FSMContext):
        data = await state.get_data()
        receipt_id, item_id = data["receipt_id"], data["item_id"]
        token = tokens.get(message.from_user.id)

        parts = (message.text or "").strip().split()
        if len(parts) != 4:
            await message.answer("Неверный формат.\nКод Количество Цена Сумма\nПример: 12 2 450 900")
            return

        code, qty_s, price_s, total_s = parts
        try:
            qty = float(qty_s.replace(",", "."))
            price = float(price_s.replace(",", "."))
            if qty <= 0 or price <= 0:
                raise ValueError
        except ValueError:
            await message.answer("QTY и ЦЕНА должны быть числами больше 0")
            return

        await api.patch_item(token, receipt_id, item_id, {
            "product_code_raw": code, "qty": qty,
            "unit_price": price, "line_total": total_s,
        })
        await svc.auto_match(token, receipt_id)
        await state.set_state(Flow.idle)
        await _show_receipt(message, message.from_user.id, receipt_id)

    # ── cancel ────────────────────────────────────────────────────────────────

    @router.callback_query(F.data.startswith("i:cancel:"))
    async def cancel_edit(call: CallbackQuery, state: FSMContext):
        data = await state.get_data()
        receipt_id = data.get("receipt_id")
        page = data.get("page", 0)
        await state.set_state(Flow.idle)

        if not receipt_id:
            await call.answer("Нет данных о чеке", show_alert=True)
            return

        receipt, items = await svc.fetch(call.from_user.id, receipt_id)
        if not receipt:
            await call.message.edit_text("Не удалось вернуть чек")
            await call.answer()
            return

        await _show_receipt(call, call.from_user.id, receipt_id, page)
        await call.answer("Отменено")

    # ── add ───────────────────────────────────────────────────────────────────

    @router.callback_query(F.data.startswith("r:add:"))
    async def add_item_start(call: CallbackQuery, state: FSMContext):
        if not await auth.ensure_access_cb(call):
            return
        p = _split(call.data, 4)
        if not p:
            await call.answer()
            return
        _, _, rid, page = p
        await state.set_state(Flow.add_item)
        await state.update_data(receipt_id=int(rid), page=int(page))
        await call.message.edit_text(ADD_ITEM_TEXT, reply_markup=cancel_kb(int(rid)))
        await call.answer()

    @router.message(Flow.add_item)
    async def add_item_save(message: Message, state: FSMContext):
        data = await state.get_data()
        receipt_id, page = data["receipt_id"], data.get("page", 0)
        token = tokens.get(message.from_user.id)

        parts = (message.text or "").strip().split()
        if len(parts) != 3:
            await message.answer("Неверный формат\nКОД QTY ЦЕНА\nПример: 11 2 450")
            return

        code, qty_s, price_s = parts
        try:
            qty = float(qty_s.replace(",", "."))
            unit_price = float(price_s.replace(",", "."))
            if qty <= 0 or unit_price <= 0:
                raise ValueError
        except ValueError:
            await message.answer("QTY и ЦЕНА должны быть числами больше 0")
            return

        product_id = await svc.get_product_id_by_code(token, code)
        line_total = svc.calc_line_total(qty, unit_price)

        status, _ = await api.create_item(token, receipt_id, {
            "product_code_raw": code, "qty": qty,
            "unit_price": unit_price, "line_total": line_total,
            "product_id": product_id,
        })
        if status not in (200, 201):
            log.warning("create_item returned status=%s for receipt=%s", status, receipt_id)
            await message.answer("Не удалось добавить позицию")
            return

        await state.set_state(Flow.idle)
        await _show_receipt(message, message.from_user.id, receipt_id, page)

    # ── delete ────────────────────────────────────────────────────────────────

    @router.callback_query(F.data.startswith("r:del:"))
    async def enter_delete_mode(call: CallbackQuery):
        if not await auth.ensure_access_cb(call):
            return
        p = _split(call.data, 4)
        if not p:
            await call.answer()
            return
        _, _, rid, page = p
        _, items = await svc.fetch(call.from_user.id, int(rid))
        await call.message.edit_text(
            "Выбери позицию для удаления:",
            reply_markup=delete_items_page_kb(int(rid), items, int(page)),
        )
        await call.answer()

    @router.callback_query(F.data.startswith("d:pick:"))
    async def delete_item(call: CallbackQuery):
        if not await auth.ensure_access_cb(call):
            return
        p = _split(call.data, 5)
        if not p:
            await call.answer()
            return
        _, _, rid, page, item_id = p
        token = tokens.get(call.from_user.id)

        status, _ = await api.delete_item(token, int(rid), int(item_id))
        if status != 204:
            log.warning("delete_item returned status=%s", status)
            await call.answer("Не удалось удалить", show_alert=True)
            return

        await _show_receipt(call, call.from_user.id, int(rid), int(page))
        await call.answer("Удалено")

    @router.callback_query(F.data.startswith("d:page:"))
    async def delete_items_page(call: CallbackQuery):
        if not await auth.ensure_access_cb(call):
            return
        p = _split(call.data, 4)
        if not p:
            await call.answer()
            return
        _, _, rid, page = p
        _, items = await svc.fetch(call.from_user.id, int(rid))
        await call.message.edit_text(
            "Выбери позицию для удаления:",
            reply_markup=delete_items_page_kb(int(rid), items, int(page)),
        )
        await call.answer()

    # ── match ─────────────────────────────────────────────────────────────────

    @router.callback_query(F.data.startswith("r:match:"))
    async def match_mode(call: CallbackQuery):
        if not await auth.ensure_access_cb(call):
            return
        p = _split(call.data, 4)
        if not p:
            await call.answer()
            return
        _, _, rid, _ = p
        _, items = await svc.fetch(call.from_user.id, int(rid))
        await call.message.edit_text(
            "Выбери позицию для матчинга:",
            reply_markup=match_items_page_kb(int(rid), items, 0),
        )
        await call.answer()

    @router.callback_query(F.data.startswith("m:page:"))
    async def match_items_page(call: CallbackQuery):
        if not await auth.ensure_access_cb(call):
            return
        p = _split(call.data, 4)
        if not p:
            await call.answer()
            return
        _, _, rid, page = p
        _, items = await svc.fetch(call.from_user.id, int(rid))
        await call.message.edit_text(
            "Выбери позицию для матчинга:",
            reply_markup=match_items_page_kb(int(rid), items, int(page)),
        )
        await call.answer()

    @router.callback_query(F.data.startswith("m:item:"))
    async def match_pick_item(call: CallbackQuery):
        if not await auth.ensure_access_cb(call):
            return
        p = _split(call.data, 5)
        if not p:
            await call.answer()
            return
        _, _, rid, _, item_id = p
        token = tokens.get(call.from_user.id)
        products = await svc.get_products(token)
        await call.message.edit_text(
            "Выбери продукт:",
            reply_markup=products_page_kb(int(rid), 0, int(item_id), products, 0),
        )
        await call.answer()

    @router.callback_query(F.data.startswith("m:prodpage:"))
    async def products_page_cb(call: CallbackQuery):
        if not await auth.ensure_access_cb(call):
            return
        p = _split(call.data, 6)
        if not p:
            await call.answer()
            return
        _, _, rid, receipt_page, item_id, page = p
        token = tokens.get(call.from_user.id)
        products = await svc.get_products(token)
        await call.message.edit_text(
            "Выбери продукт:",
            reply_markup=products_page_kb(int(rid), int(receipt_page), int(item_id), products, int(page)),
        )
        await call.answer()

    @router.callback_query(F.data.startswith("m:prod:"))
    async def match_apply(call: CallbackQuery):
        # m:prod:{rid}:{receipt_page}:{item_id}:{product_id}:{prod_page}
        if not await auth.ensure_access_cb(call):
            return
        p = _split(call.data, 7)
        if not p:
            await call.answer()
            return
        _, _, rid, receipt_page, item_id, product_id, _ = p
        token = tokens.get(call.from_user.id)

        s, _ = await api.match_item(token, int(rid), int(item_id), {"product_id": int(product_id)})
        if s not in (200, 201):
            log.warning("match_item returned status=%s", s)
            await call.answer("Не удалось сматчить", show_alert=True)
            return

        await _show_receipt(call, call.from_user.id, int(rid), int(receipt_page))
        await call.answer("Сматчено")

    return router