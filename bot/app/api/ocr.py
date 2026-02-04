# app/api/ocr.py
from __future__ import annotations
from .client import ApiClient

class OcrApi:
    def __init__(self, client: ApiClient) -> None:
        self._c = client

    async def parse(self, chat_id: str, file_bytes: bytes, filename: str, mime: str) -> dict:
        files = {"file": (filename, file_bytes, mime)}
        return await self._c.request(
            "POST",
            "/api/v1/ocr/parse",
            params={"chat_id": chat_id},
            files=files,
        )

    async def task_status(self, task_id: str) -> dict:
        return await self._c.request("GET", f"/api/v1/ocr/tasks/{task_id}")

    async def draft_get(self, chat_id: str) -> dict:
        return await self._c.request("GET", f"/api/v1/ocr/draft/{chat_id}")

    async def draft_save(self, chat_id: str, payload: dict) -> dict:
        return await self._c.request("POST", f"/api/v1/ocr/draft/{chat_id}/save", json=payload)
