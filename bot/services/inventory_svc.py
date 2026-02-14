from __future__ import annotations
from math import ceil

from api import ApiClient
from cache import CacheStore
from tokens import TokenStore


class InventoryService:
    def __init__(self, api: ApiClient, tokens: TokenStore, cache: CacheStore) -> None:
        self.api = api
        self.tokens = tokens
        self.cache = cache

    async def get_ingredient_name(self, token: str, ingredient_id: int) -> str:
        if not self.cache.has_ingredients():
            await self._load_ingredients(token)
        m = self.cache.get_ingredients_map() or {}
        return m.get(ingredient_id, f"#{ingredient_id}")

    async def _load_ingredients(self, token: str) -> dict[int, str]:
        s, items = await self.api.list_ingredients(token)
        if s == 200 and isinstance(items, list):
            self.cache.set_ingredients(items)
        return self.cache.get_ingredients_map() or {}

    async def build_view(self, token: str) -> list[dict]:
        """Возвращает список позиций склада с вычисленными лейблами срочности."""
        s, rows = await self.api.list_inventory(token)
        if s != 200 or not isinstance(rows, list):
            return []

        id_to_name = await self._load_ingredients(token)

        result = []
        for r in rows:
            iid = r.get("ingredient_id") or r.get("id")
            name = id_to_name.get(iid, f"#{iid}")
            qty = r.get("on_hand_qty")
            minq = r.get("min_qty")

            result.append({
                "ingredient_id": iid,
                "name": name,
                "on_hand_qty": qty,
                "min_qty": minq,
                "label": self._urgency_label(qty, minq),
            })
        return result

    async def purchase_plan(self, token: str) -> tuple[list[dict], float]:
        s, rows = await self.api.list_inventory(token)
        if s != 200 or not isinstance(rows, list):
            return [], 0.0

        id_to_name = await self._load_ingredients(token)
        items = []
        total_cost = 0.0

        for r in rows:
            try:
                on_hand    = float(r.get("on_hand_qty") or 0)
                min_qty    = float(r.get("min_qty") or 0)
                pack_qty   = float(r.get("purchase_pack_qty") or 0)
                pack_price = float(r.get("purchase_price") or 0)
            except (TypeError, ValueError):
                continue

            # пропускаем: не дефицитный, или нет данных для расчёта
            if on_hand >= min_qty or min_qty <= 0 or pack_qty <= 0:
                continue

            deficit      = min_qty - on_hand
            packs_needed = ceil(deficit / pack_qty)
            cost         = round(packs_needed * pack_price, 2)
            after        = round(on_hand + packs_needed * pack_qty, 2)

            iid  = r.get("ingredient_id") or r.get("id")
            name = id_to_name.get(iid, f"#{iid}")

            items.append({
                "name":         name,
                "on_hand":      on_hand,
                "min_qty":      min_qty,
                "packs_needed": packs_needed,
                "pack_qty":     pack_qty,
                "pack_price":   pack_price,
                "cost":         cost,
                "after":        after,
            })
            total_cost += cost

        items.sort(key=lambda x: x["cost"], reverse=True)
        return items, round(total_cost, 2)

    @staticmethod
    def _urgency_label(qty, minq) -> str:
        try:
            qty_f, minq_f = float(qty), float(minq)
            if minq_f <= 0:
                return ""
            pct = (minq_f - qty_f) / minq_f * 100
            if pct >= 60:
                return "СРОЧНО"
            if pct >= 30:
                return "КОНТРОЛЬ"
        except Exception:
            pass
        return ""