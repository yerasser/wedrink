from __future__ import annotations
import asyncio
import logging

from api import ApiClient
from cache import CacheStore
from tokens import TokenStore

log = logging.getLogger(__name__)


class ReceiptService:
    def __init__(self, api: ApiClient, tokens: TokenStore, cache: CacheStore) -> None:
        self.api = api
        self.tokens = tokens
        self.cache = cache

    async def fetch(self, user_id: int, receipt_id: int) -> tuple[dict | None, list[dict]]:
        token = self.tokens.get(user_id)
        if not token:
            return None, []
        _, receipt = await self.api.get_receipt(token, receipt_id)
        _, items = await self.api.list_items(token, receipt_id)
        if not isinstance(items, list):
            items = []
        items = [it for it in items if not it.get("is_deleted")]
        return receipt, items

    async def get_products(self, token: str) -> list[dict]:
        if self.cache.has_products():
            return self.cache.get_products_list()  # type: ignore[return-value]
        s, products = await self.api.list_products(token)
        if s == 200 and isinstance(products, list):
            self.cache.set_products_list(products)
            return products
        log.warning("list_products returned status=%s", s)
        return []

    async def get_product_id_by_code(self, token: str, code: str) -> int | None:
        if not self.cache.has_products():
            await self.get_products(token)
        return self.cache.get_product_id_by_code(code)

    async def auto_match(self, token: str, receipt_id: int) -> None:
        products = await self.get_products(token)
        code_to_id = {
            (p.get("code") or "").upper(): p["id"]
            for p in products
            if p.get("code") and p.get("id")
        }

        s, items = await self.api.list_items(token, receipt_id)
        if s != 200 or not isinstance(items, list):
            return

        tasks = []
        for it in items:
            if it.get("product_id"):
                continue
            raw_code = (it.get("product_code_raw") or "").strip().upper()
            product_id = code_to_id.get(raw_code)
            if not product_id:
                continue
            tasks.append(
                self.api.match_item(token, receipt_id, it["id"], {"product_id": product_id})
            )

        if tasks:
            await asyncio.gather(*tasks)

    @staticmethod
    def has_unmatched(items: list[dict]) -> bool:
        return any(not it.get("product_id") for it in items)

    @staticmethod
    def calc_line_total(qty: float, unit_price: float | None) -> float | None:
        if unit_price is None:
            return None
        return round(qty * unit_price, 2)