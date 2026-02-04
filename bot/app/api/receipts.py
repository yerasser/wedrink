from __future__ import annotations
from .client import ApiClient

class ReceiptsApi:
    def __init__(self, client: ApiClient) -> None:
        self._c = client

    async def create(self, items: list[dict]) -> dict:
        # POST /api/v1/receipts  body: {items:[{product_id, amount}]}
        return await self._c.request("POST", "/api/v1/receipts", json={"items": items})

    async def commit(self, receipt_id: int) -> dict:
        # POST /api/v1/receipts/{receipt_id}/commit
        return await self._c.request("POST", f"/api/v1/receipts/{receipt_id}/commit")
