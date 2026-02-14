import aiohttp
from typing import Optional


class ApiClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = aiohttp.ClientTimeout(total=60)

    async def auth_telegram(self, tg_user_id: int, username: Optional[str]):
        url = f"{self.base_url}/auth/telegram"
        payload = {"tg_user_id": tg_user_id, "username": username}
        async with aiohttp.ClientSession(timeout=self.timeout) as s:
            async with s.post(url, json=payload) as r:
                data = await r.json(content_type=None)
                return r.status, data

    async def create_receipt(self, token: str):
        url = f"{self.base_url}/receipts"
        headers = {"Authorization": f"Bearer {token}"}
        async with aiohttp.ClientSession(timeout=self.timeout) as s:
            async with s.post(url, headers=headers) as r:
                data = await r.json(content_type=None)
                return r.status, data

    async def enqueue_ocr(self, token: str, receipt_id: int, file_bytes: bytes, filename: str, content_type: str):
        url = f"{self.base_url}/receipts/{receipt_id}/ocr"
        headers = {"Authorization": f"Bearer {token}"}
        form = aiohttp.FormData()
        form.add_field("file", file_bytes, filename=filename, content_type=content_type)

        async with aiohttp.ClientSession(timeout=self.timeout) as s:
            async with s.post(url, headers=headers, data=form) as r:
                data = await r.json(content_type=None)
                return r.status, data

    async def get_receipt(self, token: str, receipt_id: int):
        url = f"{self.base_url}/receipts/{receipt_id}"
        headers = {"Authorization": f"Bearer {token}"}
        async with aiohttp.ClientSession(timeout=self.timeout) as s:
            async with s.get(url, headers=headers) as r:
                data = await r.json(content_type=None)
                return r.status, data

    async def list_items(self, token: str, receipt_id: int):
        url = f"{self.base_url}/receipts/{receipt_id}/items"
        headers = {"Authorization": f"Bearer {token}"}
        async with aiohttp.ClientSession(timeout=self.timeout) as s:
            async with s.get(url, headers=headers) as r:
                data = await r.json(content_type=None)
                return r.status, data

    async def list_products(self, token: str):
        url = f"{self.base_url}/products"
        headers = {"Authorization": f"Bearer {token}"}
        async with aiohttp.ClientSession(timeout=self.timeout) as s:
            async with s.get(url, headers=headers) as r:
                data = await r.json(content_type=None)
                return r.status, data

    async def patch_item(self, token: str, receipt_id: int, item_id: int, payload: dict):
        url = f"{self.base_url}/receipts/{receipt_id}/items/{item_id}"
        headers = {"Authorization": f"Bearer {token}"}
        async with aiohttp.ClientSession(timeout=self.timeout) as s:
            async with s.patch(url, headers=headers, json=payload) as r:
                data = await r.json(content_type=None)
                return r.status, data

    async def apply_receipt(self, token: str, receipt_id: int):
        url = f"{self.base_url}/receipts/{receipt_id}/apply"
        headers = {"Authorization": f"Bearer {token}"}
        async with aiohttp.ClientSession(timeout=self.timeout) as s:
            async with s.post(url, headers=headers) as r:
                data = await r.json(content_type=None)
                return r.status, data

    async def rollback_receipt(self, token: str, receipt_id: int):
        url = f"{self.base_url}/receipts/{receipt_id}/rollback"
        headers = {"Authorization": f"Bearer {token}"}
        async with aiohttp.ClientSession(timeout=self.timeout) as s:
            async with s.post(url, headers=headers) as r:
                data = await r.json(content_type=None)
                return r.status, data

    async def create_item(self, token: str, receipt_id: int, payload: dict):
        url = f"{self.base_url}/receipts/{receipt_id}/items"
        headers = {"Authorization": f"Bearer {token}"}
        async with aiohttp.ClientSession(timeout=self.timeout) as s:
            async with s.post(url, headers=headers, json=payload) as r:
                data = await r.json(content_type=None)
                return r.status, data

    async def match_item(self, token: str, receipt_id: int, item_id: int, payload: dict):
        url = f"{self.base_url}/receipts/{receipt_id}/items/{item_id}/match"
        headers = {"Authorization": f"Bearer {token}"}
        async with aiohttp.ClientSession(timeout=self.timeout) as s:
            async with s.post(url, headers=headers, json=payload) as r:
                data = await r.json(content_type=None)
                return r.status, data

    async def delete_item(self, token: str, receipt_id: int, item_id: int):
        url = f"{self.base_url}/receipts/{receipt_id}/items/{item_id}"
        headers = {"Authorization": f"Bearer {token}"}
        async with aiohttp.ClientSession(timeout=self.timeout) as s:
            async with s.delete(url, headers=headers) as r:
                return r.status, None

    async def list_receipts(self, token: str, status: str | None = None, from_: str | None = None, to: str | None = None):
        url = f"{self.base_url}/receipts"
        headers = {"Authorization": f"Bearer {token}"}
        params = {}
        if status:
            params["status"] = status
        if from_:
            params["from_"] = from_
        if to:
            params["to"] = to

        async with aiohttp.ClientSession(timeout=self.timeout) as s:
            async with s.get(url, headers=headers, params=params) as r:
                data = await r.json(content_type=None)
                return r.status, data

    async def list_inventory(self, token: str):
        url = f"{self.base_url}/inventory"
        headers = {"Authorization": f"Bearer {token}"}
        async with aiohttp.ClientSession(timeout=self.timeout) as s:
            async with s.get(url, headers=headers) as r:
                data = await r.json(content_type=None)
                return r.status, data

    async def get_inventory_item(self, token: str, ingredient_id: int):
        url = f"{self.base_url}/inventory/{ingredient_id}"
        headers = {"Authorization": f"Bearer {token}"}
        async with aiohttp.ClientSession(timeout=self.timeout) as s:
            async with s.get(url, headers=headers) as r:
                data = await r.json(content_type=None)
                return r.status, data

    async def list_ingredients(self, token: str):
        url = f"{self.base_url}/ingredients"
        headers = {"Authorization": f"Bearer {token}"}
        async with aiohttp.ClientSession(timeout=self.timeout) as s:
            async with s.get(url, headers=headers) as r:
                data = await r.json(content_type=None)
                return r.status, data

    async def report_consumption(self, token: str, from_: str, to: str, ingredient_id: int | None = None):
        url = f"{self.base_url}/reports/consumption"
        headers = {"Authorization": f"Bearer {token}"}
        params = {"from_": from_, "to": to}
        if ingredient_id:
            params["ingredient_id"] = ingredient_id

        async with aiohttp.ClientSession(timeout=self.timeout) as s:
            async with s.get(url, headers=headers, params=params) as r:
                data = await r.json(content_type=None)
                return r.status, data

    async def me(self, token: str):
        url = f"{self.base_url}/me"
        headers = {"Authorization": f"Bearer {token}"}
        async with aiohttp.ClientSession(timeout=self.timeout) as s:
            async with s.get(url, headers=headers) as r:
                data = await r.json(content_type=None)
                return r.status, data
