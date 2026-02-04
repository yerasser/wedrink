# app/main.py
import asyncio
from aiogram import Bot, Dispatcher

from .config import load_settings
from .log import setup_logging
from .api.client import ApiClient
from .api.ocr import OcrApi
from .api.receipts import ReceiptsApi
from .api.stock import StockApi
from .storage.memory import MemoryStore
from .bot.router import build_router

class ApiBundle:
    def __init__(self, base_url: str, timeout: float) -> None:
        self.client = ApiClient(base_url, timeout)
        self.ocr = OcrApi(self.client)
        self.receipts = ReceiptsApi(self.client)
        self.stock = StockApi(self.client)

    async def close(self) -> None:
        await self.client.close()

async def main():
    setup_logging()
    s = load_settings()

    bot = Bot(token=s.bot_token)
    dp = Dispatcher()
    dp.include_router(build_router())

    api = ApiBundle(s.api_base_url, s.api_timeout)
    store = MemoryStore()

    dp.workflow_data["api"] = api
    dp.workflow_data["store"] = store

    try:
        await dp.start_polling(bot)
    finally:
        await api.close()

if __name__ == "__main__":
    asyncio.run(main())
