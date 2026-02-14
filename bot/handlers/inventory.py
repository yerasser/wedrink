"""handlers/inventory.py — просмотр складских остатков."""
import logging

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message

import auth
from api import ApiClient
from cache import CacheStore
from tokens import TokenStore
from services import InventoryService
from ui import fmt_inventory_list, fmt_inventory_detail, fmt_purchase_plan, inventory_list_kb, inventory_detail_kb, purchase_plan_kb

log = logging.getLogger(__name__)
router = Router(name="inventory")


def setup(api: ApiClient, tokens: TokenStore, cache: CacheStore):
    svc = InventoryService(api, tokens, cache)

    async def _render(user_id: int, page: int):
        token = tokens.get(user_id)
        if not token:
            return "Нет доступа", None
        rows = await svc.build_view(token)
        text, p, pages, chunk = fmt_inventory_list(rows, page)
        return text, inventory_list_kb(chunk, p, pages)

    @router.message(F.text == "📦 Остатки")
    async def inventory_screen(message: Message):
        if not await auth.ensure_access(message):
            return
        text, kb = await _render(message.from_user.id, 0)
        await message.answer(text, reply_markup=kb)

    @router.callback_query(F.data.startswith("inv:page:"))
    async def inventory_page(call: CallbackQuery):
        if not await auth.ensure_access_cb(call):
            return
        page = int(call.data.split(":")[2])
        text, kb = await _render(call.from_user.id, page)
        await call.message.edit_text(text, reply_markup=kb)
        await call.answer()

    @router.callback_query(F.data.startswith("inv:open:"))
    async def inventory_open(call: CallbackQuery):
        if not await auth.ensure_access_cb(call):
            return
        try:
            _, _, iid, list_page = call.data.split(":")
        except ValueError:
            await call.answer()
            return

        token = tokens.get(call.from_user.id)
        s, row = await api.get_inventory_item(token, int(iid))
        if s != 200 or not isinstance(row, dict):
            log.warning("get_inventory_item returned status=%s for iid=%s", s, iid)
            await call.answer("Не удалось открыть", show_alert=True)
            return

        # API возвращает только ingredient_id без имени —
        # подтягиваем название из кеша ингредиентов
        ingredient_id = row.get("ingredient_id") or row.get("id")
        row["ingredient_name"] = await svc.get_ingredient_name(token, int(ingredient_id))

        await call.message.edit_text(
            fmt_inventory_detail(row),
            reply_markup=inventory_detail_kb(int(list_page)),
        )
        await call.answer()

    @router.callback_query(F.data == "inv:purchase")
    async def purchase_screen(call: CallbackQuery):
        if not await auth.ensure_access_cb(call):
            return
        token = tokens.get(call.from_user.id)
        items, total_cost = await svc.purchase_plan(token)
        # запоминаем страницу списка чтобы вернуться (берём из call.message если можем)
        list_page = 0
        text = fmt_purchase_plan(items, total_cost)
        await call.message.edit_text(text, reply_markup=purchase_plan_kb(list_page))
        await call.answer()

    return router