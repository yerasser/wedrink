import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import TelegramObject

log = logging.getLogger(__name__)

class RoleMiddleware(BaseMiddleware):
    def __init__(self, token_store, api_client):
        self.token_store = token_store
        self.api = api_client

    async def __call__(self, handler, event: TelegramObject, data: dict):
        tg_user = data.get("event_from_user")
        if tg_user:
            token = self.token_store.get(tg_user.id)
            role = None
            if token:
                s, me = await self.api.me(token)
                role = me.get("role")
            data["role"] = role
        return await handler(event, data)


class ErrorMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        try:
            return await handler(event, data)
        except TelegramBadRequest as e:
            if "message is not modified" in str(e).lower():
                return
            log.error("TelegramBadRequest: %s", e, exc_info=True)
            await self._notify(event, data)
        except Exception as e:
            log.error("Unhandled exception in handler: %s", e, exc_info=True)
            await self._notify(event, data)

    @staticmethod
    async def _notify(event: TelegramObject, data: dict[str, Any]) -> None:
        from aiogram.types import CallbackQuery, Message

        try:
            if isinstance(event, CallbackQuery):
                await event.answer("⚠️ Что-то пошло не так. Попробуй ещё раз.", show_alert=True)
            elif isinstance(event, Message):
                await event.answer("⚠️ Что-то пошло не так. Попробуй ещё раз.")
        except Exception:
            pass