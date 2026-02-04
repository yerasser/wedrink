from __future__ import annotations
from .client import ApiClient

class StockApi:
    def __init__(self, client: ApiClient) -> None:
        self._c = client

    async def alerts(self) -> list[dict]:
        # GET /api/v1/stock/alerts
        data = await self._c.request("GET", "/api/v1/stock/alerts")
        return data if isinstance(data, list) else []
