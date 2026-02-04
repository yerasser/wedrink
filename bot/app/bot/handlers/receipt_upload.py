# app/bot/handlers/receipt_upload.py
from __future__ import annotations

import asyncio

from aiogram import Router, F
from aiogram.types import Message
from aiogram.exceptions import TelegramBadRequest

from app.bot.formatters import (
    format_processing,
    format_ocr_empty,
    format_commit_success,
    format_api_error,
)

router = Router()


async def _download_bytes(m: Message, file_id: str) -> bytes:
    tg_file = await m.bot.get_file(file_id)
    stream = await m.bot.download_file(tg_file.file_path)
    return stream.read()


async def _wait_and_commit(bot, api, chat_id: str, task_id: str, store) -> None:
    """
    MVP flow (без редактирования):
    1) ждём OCR: /ocr/tasks/{task_id} -> status == "complete"
    2) берём result (code == product_id, qty == amount)
    3) POST /receipts
    4) POST /receipts/{id}/commit  -> списание склада
    5) аккуратное сообщение пользователю
    """

    status_resp = None

    # 1) ждём завершения OCR
    for _ in range(120):  # до ~120 секунд
        # если пользователь отправил новый чек — прекращаем старый
        if store.get_task(chat_id) != task_id:
            return

        status_resp = await api.ocr.task_status(task_id)
        if isinstance(status_resp, dict) and (status_resp.get("status") or "").lower() == "complete":
            break

        await asyncio.sleep(1)
    else:
        await bot.send_message(chat_id, format_api_error("Распознавание не завершилось."))
        return

    # 2) нормализация OCR-результата
    result = status_resp.get("result") if isinstance(status_resp, dict) else None
    if not isinstance(result, list) or not result:
        await bot.send_message(chat_id, format_ocr_empty())
        return

    items: list[dict] = []
    for r in result:
        try:
            pid = int(r["code"])      # code == product_id
            qty = float(r["qty"])     # qty == amount для списания
            if qty > 0:
                items.append({"product_id": pid, "amount": qty})
        except Exception:
            continue

    if not items:
        await bot.send_message(chat_id, format_api_error("Не удалось сформировать позиции для списания."))
        return

    # 3) создать чек
    try:
        receipt = await api.receipts.create(items)
        receipt_id = receipt.get("id")
        if not receipt_id:
            await bot.send_message(chat_id, format_api_error("Не удалось создать чек."))
            return
    except Exception:
        await bot.send_message(chat_id, format_api_error("Ошибка при создании чека."))
        return

    # 4) commit — здесь реально минусуется склад
    try:
        commit = await api.receipts.commit(int(receipt_id))
    except Exception:
        await bot.send_message(chat_id, format_api_error("Ошибка при списании со склада."))
        return

    # 5) финальное сообщение пользователю
    await bot.send_message(chat_id, format_commit_success(int(receipt_id), commit))


@router.message(F.photo)
async def photo_receipt(m: Message, api, store):
    chat_id = str(m.chat.id)

    try:
        file_id = m.photo[-1].file_id  # type: ignore[union-attr]
        content = await _download_bytes(m, file_id)
    except TelegramBadRequest:
        await m.answer(format_api_error("Не удалось загрузить изображение."))
        return

    try:
        res = await api.ocr.parse(
            chat_id=chat_id,
            file_bytes=content,
            filename="receipt.jpg",
            mime="image/jpeg",
        )
    except Exception:
        await m.answer(format_api_error("Не удалось отправить чек на распознавание."))
        return

    task_id = res.get("task_id") or res.get("id") or res.get("task")
    if not task_id:
        await m.answer(format_api_error("Ошибка запуска распознавания."))
        return

    task_id = str(task_id)
    store.set_task(chat_id, task_id)

    await m.answer(format_processing(task_id))
    asyncio.create_task(_wait_and_commit(m.bot, api, chat_id, task_id, store))


@router.message(F.document)
async def doc_receipt(m: Message, api, store):
    chat_id = str(m.chat.id)

    doc = m.document  # type: ignore[assignment]
    if not doc:
        await m.answer(format_api_error("Файл не найден."))
        return

    mime = (doc.mime_type or "").lower()
    if not mime.startswith("image/"):
        await m.answer(format_api_error("Нужен файл-изображение (jpg/png)."))
        return

    try:
        content = await _download_bytes(m, doc.file_id)
    except TelegramBadRequest:
        await m.answer(format_api_error("Не удалось загрузить файл."))
        return

    filename = doc.file_name or ("receipt.png" if mime == "image/png" else "receipt.jpg")
    if "." not in filename:
        filename += ".png" if mime == "image/png" else ".jpg"

    try:
        res = await api.ocr.parse(
            chat_id=chat_id,
            file_bytes=content,
            filename=filename,
            mime=mime,
        )
    except Exception:
        await m.answer(format_api_error("Не удалось отправить чек на распознавание."))
        return

    task_id = res.get("task_id") or res.get("id") or res.get("task")
    if not task_id:
        await m.answer(format_api_error("Ошибка запуска распознавания."))
        return

    task_id = str(task_id)
    store.set_task(chat_id, task_id)

    await m.answer(format_processing(task_id))
    asyncio.create_task(_wait_and_commit(m.bot, api, chat_id, task_id, store))
