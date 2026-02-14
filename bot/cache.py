import time
from typing import Any

# Продукты меняются редко, но всё же меняются
PRODUCTS_TTL = 300       # 5 минут
INGREDIENTS_TTL = 300    # 5 минут


class CacheStore:
    def __init__(self) -> None:
        self._data: dict[str, Any] = {}
        self._expires: dict[str, float] = {}

    # ── internal ──────────────────────────────────────────────────────────────

    def _get(self, key: str) -> Any | None:
        exp = self._expires.get(key)
        if exp is not None and time.monotonic() > exp:
            self._data.pop(key, None)
            self._expires.pop(key, None)
            return None
        return self._data.get(key)

    def _set(self, key: str, value: Any, ttl: float | None = None) -> None:
        self._data[key] = value
        if ttl is not None:
            self._expires[key] = time.monotonic() + ttl
        else:
            self._expires.pop(key, None)

    def _has(self, key: str) -> bool:
        return self._get(key) is not None

    def _pop(self, *keys: str) -> None:
        for k in keys:
            self._data.pop(k, None)
            self._expires.pop(k, None)

    # ── products ──────────────────────────────────────────────────────────────

    def get_products_list(self) -> list[dict] | None:
        return self._get("products_list")

    def set_products_list(self, products: list[dict]) -> None:
        self._set("products_list", products, ttl=PRODUCTS_TTL)
        self._set("products_code_map", {
            (p.get("code") or "").upper(): p["id"]
            for p in products
            if p.get("code") and p.get("id")
        }, ttl=PRODUCTS_TTL)

    def get_product_id_by_code(self, code: str) -> int | None:
        m = self._get("products_code_map")
        if m is None:
            return None
        return m.get(code.strip().upper())

    def has_products(self) -> bool:
        return self._has("products_list")

    def invalidate_products(self) -> None:
        self._pop("products_list", "products_code_map")

    # ── ingredients ───────────────────────────────────────────────────────────

    def get_ingredients_map(self) -> dict[int, str] | None:
        return self._get("ingredients_map")

    def set_ingredients(self, ingredients: list[dict]) -> None:
        self._set("ingredients_map", {
            int(i["id"]): i.get("name", f"#{i['id']}")
            for i in ingredients
            if i.get("id")
        }, ttl=INGREDIENTS_TTL)

    def has_ingredients(self) -> bool:
        return self._has("ingredients_map")

    def invalidate_ingredients(self) -> None:
        self._pop("ingredients_map")

    # ── per-user receipts filter ─────────────

    def get_receipts_filter(self, user_id: int) -> str:
        return self._data.get(f"rf:{user_id}", "all")

    def set_receipts_filter(self, user_id: int, flt: str) -> None:
        self._data[f"rf:{user_id}"] = flt

    # ── full invalidation ─────────────────────────────────────────────────────

    def clear(self) -> None:
        self._data.clear()
        self._expires.clear()