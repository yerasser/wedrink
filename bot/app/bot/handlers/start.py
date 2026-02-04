from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()

@router.message(Command("start", "help"))
async def start(m: Message):
    await m.answer(
        "Отправь фото/файл чека.\n"
    )
