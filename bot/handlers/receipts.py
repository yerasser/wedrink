import asyncio
import logging

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import auth
from api import ApiClient
from cache import CacheStore
from tokens import TokenStore
from services import ReceiptService
from ui import (
    PROCESSING_TEXT, TIMEOUT_TEXT,
    fmt_receipt_page, fmt_receipts_list,
    receipt_page_kb, receipts_list_kb,
    upload_mode_kb, UPLOAD_MODE_TEXT,
)

POLL_TRIES = 25
POLL_SLEEP = 1.4

log = logging.getLogger(__name__)
router = Router(name="receipts")


def setup(api: ApiClient, tokens: TokenStore, cache: CacheStore):
    svc = ReceiptService(api, tokens, cache)

    # ── helpers ───────────────────────────────────────────────────────────────

    async def _render_receipt(user_id: int, receipt_id: int, page: int = 0):
        receipt, items = await svc.fetch(user_id, receipt_id)
        text, p, pages = fmt_receipt_page(receipt, items, page)
        kb = receipt_page_kb(receipt_id, receipt["status"], p, pages, svc.has_unmatched(items))
        return text, kb

    async def _render_list(user_id: int, page: int):
        token = tokens.get(user_id)
        if not token:
            return "Нет доступа", None

        flt = cache.get_receipts_filter(user_id)
        api_status = "applied" if flt == "applied" else None

        s, receipts = await api.list_receipts(token, status=api_status)
        if s != 200 or not isinstance(receipts, list):
            log.warning("list_receipts returned status=%s for uid=%s", s, user_id)
            receipts = []

        if flt == "not_applied":
            receipts = [r for r in receipts if r.get("status") != "applied"]

        receipts.sort(key=lambda r: int(r.get("id", 0)), reverse=True)
        text, p, pages, chunk = fmt_receipts_list(receipts, page)
        return text, receipts_list_kb(chunk, p, pages)

    # ── upload ────────────────────────────────────────────────────────────────

    @router.message(F.text == "📸 Загрузить чек")
    async def upload_mode(message: Message, state: FSMContext):
        if not await auth.ensure_access(message):
            return
        from handlers.states import Flow
        await state.set_state(Flow.upload_receipt)
        await message.answer(UPLOAD_MODE_TEXT, reply_markup=upload_mode_kb())

    @router.message(F.photo)
    async def handle_photo(message: Message, state: FSMContext):
        from handlers.states import Flow
        if await state.get_state() != Flow.upload_receipt:
            await message.answer("Нажми «📸 Загрузить чек»")
            return

        token = tokens.get(message.from_user.id)
        if not token:
            return

        msg = await message.answer(PROCESSING_TEXT)

        try:
            _, r = await api.create_receipt(token)
            receipt_id = r["id"]

            photo = message.photo[-1]
            file = await message.bot.get_file(photo.file_id)
            buf = await message.bot.download_file(file.file_path)
            await api.enqueue_ocr(token, receipt_id, buf.read(), "receipt.jpg", "image/jpeg")

            for _ in range(POLL_TRIES):
                await asyncio.sleep(POLL_SLEEP)
                _, receipt = await api.get_receipt(token, receipt_id)
                if receipt["status"] == "failed":
                    await msg.edit_text("❌ OCR ошибка")
                    return
                if receipt["status"] in ("parsed", "edited", "applied"):
                    await svc.auto_match(token, receipt_id)
                    text, kb = await _render_receipt(message.from_user.id, receipt_id)
                    await msg.edit_text(text, reply_markup=kb)
                    return

            await msg.edit_text(TIMEOUT_TEXT)

        except Exception as e:
            log.error("OCR polling failed for uid=%s: %s", message.from_user.id, e, exc_info=True)
            await msg.edit_text("❌ Ошибка при обработке чека. Попробуй ещё раз.")

    # ── view / page ───────────────────────────────────────────────────────────

    @router.callback_query(F.data.startswith("r:view:"))
    @router.callback_query(F.data.startswith("r:page:"))
    async def view_or_page(call: CallbackQuery):
        if not await auth.ensure_access_cb(call):
            return
        try:
            _, _, rid, page = call.data.split(":")
        except ValueError:
            await call.answer("Неверный запрос", show_alert=True)
            return
        text, kb = await _render_receipt(call.from_user.id, int(rid), int(page))
        await call.message.edit_text(text, reply_markup=kb)
        await call.answer()

    # ── list ──────────────────────────────────────────────────────────────────

    @router.message(F.text == "🧾 Чеки")
    async def receipts_screen(message: Message):
        if not await auth.ensure_access(message):
            return
        text, kb = await _render_list(message.from_user.id, 0)
        await message.answer(text, reply_markup=kb)

    @router.callback_query(F.data.startswith("rc:page:"))
    async def receipts_page(call: CallbackQuery):
        if not await auth.ensure_access_cb(call):
            return
        page = int(call.data.split(":")[2])
        text, kb = await _render_list(call.from_user.id, page)
        await call.message.edit_text(text, reply_markup=kb)
        await call.answer()

    @router.callback_query(F.data.startswith("rc:filter:"))
    async def receipts_filter(call: CallbackQuery):
        if not await auth.ensure_access_cb(call):
            return
        try:
            _, _, flt, page = call.data.split(":")
        except ValueError:
            await call.answer()
            return
        if flt not in ("all", "not_applied", "applied"):
            flt = "all"
        cache.set_receipts_filter(call.from_user.id, flt)
        text, kb = await _render_list(call.from_user.id, int(page))
        await call.message.edit_text(text, reply_markup=kb)
        await call.answer()

    @router.callback_query(F.data.startswith("rc:open:"))
    async def receipts_open(call: CallbackQuery):
        if not await auth.ensure_access_cb(call):
            return
        rid = int(call.data.split(":")[2])
        text, kb = await _render_receipt(call.from_user.id, rid)
        await call.message.edit_text(text, reply_markup=kb)
        await call.answer()

    # ── apply / rollback ──────────────────────────────────────────────────────

    @router.callback_query(F.data.startswith("r:apply:"))
    async def apply_receipt(call: CallbackQuery):
        if not await auth.ensure_access_cb(call):
            return
        receipt_id = int(call.data.split(":")[2])
        token = tokens.get(call.from_user.id)

        receipt, items = await svc.fetch(call.from_user.id, receipt_id)
        if svc.has_unmatched(items):
            await call.answer("Есть позиции без матчинга", show_alert=True)
            return

        s, _ = await api.apply_receipt(token, receipt_id)
        if s not in (200, 201, 204):
            log.warning("apply_receipt returned status=%s for receipt=%s", s, receipt_id)
            await call.answer("Не удалось применить чек", show_alert=True)
            return

        text, kb = await _render_receipt(call.from_user.id, receipt_id)
        await call.message.edit_text(text, reply_markup=kb)
        await call.answer("Чек применён")

    @router.callback_query(F.data.startswith("r:rollback:"))
    async def rollback_receipt(call: CallbackQuery):
        if not await auth.ensure_access_cb(call):
            return
        receipt_id = int(call.data.split(":")[2])
        token = tokens.get(call.from_user.id)
        s, _ = await api.rollback_receipt(token, receipt_id)
        if s not in (200, 201, 204):
            log.warning("rollback_receipt returned status=%s for receipt=%s", s, receipt_id)
            await call.answer("Не удалось откатить", show_alert=True)
            return
        text, kb = await _render_receipt(call.from_user.id, receipt_id)
        await call.message.edit_text(text, reply_markup=kb)
        await call.answer("Откат выполнен")

    return router