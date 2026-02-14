import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message

import auth
from api import ApiClient
from cache import CacheStore
from tokens import TokenStore
from services import InventoryService
from ui import consumption_period_kb, calendar_kb, fmt_consumption

TZ = ZoneInfo("Asia/Almaty")
log = logging.getLogger(__name__)
router = Router(name="consumption")


def _period_range(period: str) -> tuple[str, str]:
    now = datetime.now(TZ)
    if period == "week":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=now.weekday())
        end = start + timedelta(days=7)
    elif period == "month":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end = start.replace(month=start.month + 1) if start.month < 12 else start.replace(year=start.year + 1, month=1)
    else:  # day
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
    return start.isoformat(), end.isoformat()


def setup(api: ApiClient, tokens: TokenStore, cache: CacheStore):
    inv_svc = InventoryService(api, tokens, cache)

    async def _show_consumption(call: CallbackQuery, from_: str, to: str, header: str):
        token = tokens.get(call.from_user.id)
        s, rows = await api.report_consumption(token, from_=from_, to=to)
        if s != 200 or not isinstance(rows, list):
            log.warning("report_consumption returned status=%s", s)
            await call.message.edit_text("Не удалось получить расход", reply_markup=consumption_period_kb())
            await call.answer()
            return

        id_to_name = await inv_svc._load_ingredients(token)
        text = fmt_consumption(rows, id_to_name, header)
        await call.message.edit_text(text, reply_markup=consumption_period_kb())
        await call.answer()

    # ── entry point ───────────────────────────────────────────────────────────

    @router.message(F.text == "📊 Расход")
    async def consumption_screen(message: Message):
        if not await auth.ensure_access(message):
            return
        await message.answer("📊 Расход: выбери период", reply_markup=consumption_period_kb())

    # ── period buttons ────────────────────────────────────────────────────────

    @router.callback_query(F.data == "cons:week")
    async def consumption_week(call: CallbackQuery):
        if not await auth.ensure_access_cb(call):
            return
        from_, to = _period_range("week")
        await _show_consumption(call, from_, to, "📊 Расход за неделю")

    @router.callback_query(F.data == "cons:month")
    async def consumption_month(call: CallbackQuery):
        if not await auth.ensure_access_cb(call):
            return
        from_, to = _period_range("month")
        await _show_consumption(call, from_, to, "📊 Расход за месяц")

    @router.callback_query(F.data == "cons:day")
    async def consumption_pick_day(call: CallbackQuery):
        if not await auth.ensure_access_cb(call):
            return
        today = datetime.now(TZ).date()
        await call.message.edit_text(
            "📅 Выбери день:",
            reply_markup=calendar_kb(today.year, today.month),
        )
        await call.answer()

    # ── calendar ──────────────────────────────────────────────────────────────

    @router.callback_query(F.data.startswith("cal:nav:"))
    async def calendar_nav(call: CallbackQuery):
        try:
            _, _, y, m = call.data.split(":")
        except ValueError:
            await call.answer()
            return
        await call.message.edit_text(
            "📅 Выбери день:",
            reply_markup=calendar_kb(int(y), int(m)),
        )
        await call.answer()

    @router.callback_query(F.data.startswith("cal:pick:"))
    async def calendar_pick(call: CallbackQuery):
        if not await auth.ensure_access_cb(call):
            return
        try:
            _, _, y, m, d = call.data.split(":")
        except ValueError:
            await call.answer()
            return
        year, month, day = int(y), int(m), int(d)
        start = datetime(year, month, day, tzinfo=TZ)
        end = start + timedelta(days=1)
        await _show_consumption(
            call, start.isoformat(), end.isoformat(),
            f"📊 Расход за {year}-{month:02d}-{day:02d}",
        )

    @router.callback_query(F.data == "cons:back")
    async def consumption_back(call: CallbackQuery):
        await call.message.edit_text("📊 Расход: выбери период", reply_markup=consumption_period_kb())
        await call.answer()

    return router