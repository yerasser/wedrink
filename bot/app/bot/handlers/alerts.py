from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from ..formatters import format_alerts, format_api_error

router = Router()

@router.message(Command("alerts"))
async def alerts(m: Message, api):
    try:
        res = await api.stock.alerts()
    except Exception:
        await m.answer(format_api_error("Не смог получить отчёт по складу."))
        return

    for text in format_alerts(res):   # ✅ list[str] -> отправляем по одному
        await m.answer(text)
