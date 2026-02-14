import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, API_BASE_URL
from api import ApiClient
from tokens import TokenStore
from cache import CacheStore
import auth
from middleware import ErrorMiddleware, RoleMiddleware
from handlers import menu, receipts, items, inventory, consumption

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger(__name__)


async def main():
    # ── зависимости ───────────────────────────────────────────────────────────
    api_client   = ApiClient(API_BASE_URL)
    token_store  = TokenStore()
    cache_store  = CacheStore()

    auth.init(api_client, token_store)

    # ── роутеры ───────────────────────────────────────────────────────────────
    menu_router     = menu.setup()
    receipts_router = receipts.setup(api_client, token_store, cache_store)
    items_router    = items.setup(api_client, token_store, cache_store)
    inv_router      = inventory.setup(api_client, token_store, cache_store)
    cons_router     = consumption.setup(api_client, token_store, cache_store)

    dp = Dispatcher(storage=MemoryStorage())

    dp.update.middleware(RoleMiddleware(token_store, api_client))
    dp.update.middleware(ErrorMiddleware())

    dp.include_routers(
        menu_router,
        receipts_router,
        items_router,
        inv_router,
        cons_router,
    )

    bot = Bot(BOT_TOKEN)
    log.info("Bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())