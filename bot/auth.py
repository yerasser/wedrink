import logging

from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from api import ApiClient
from tokens import TokenStore

log = logging.getLogger(__name__)

_api: ApiClient
_tokens: TokenStore


def init(api: ApiClient, tokens: TokenStore) -> None:
    global _api, _tokens
    _api = api
    _tokens = tokens


async def ensure_access(message: Message) -> bool:
    uid = message.from_user.id
    if _tokens.get(uid):
        return True

    await message.answer("🔐 Проверяю доступ…", reply_markup=ReplyKeyboardRemove())
    try:
        s, data = await _api.auth_telegram(uid, message.from_user.username)
    except Exception as e:
        log.error("auth_telegram failed for uid=%s: %s", uid, e)
        await message.answer("⛔️ Нет доступа")
        return False

    if s == 200 and data.get("access_token"):
        _tokens.set(uid, data["access_token"])
        return True

    await message.answer("⛔️ Нет доступа")
    return False


async def ensure_access_cb(call: CallbackQuery) -> bool:
    uid = call.from_user.id
    if _tokens.get(uid):
        return True

    try:
        s, data = await _api.auth_telegram(uid, call.from_user.username)
        if s == 200 and data.get("access_token"):
            _tokens.set(uid, data["access_token"])
            return True
    except Exception as e:
        log.error("auth_telegram failed for uid=%s: %s", uid, e)

    await call.answer("⛔️ Сессия истекла. Напиши /start", show_alert=True)
    return False