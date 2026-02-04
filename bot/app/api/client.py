from __future__ import annotations
import httpx

class ApiError(RuntimeError):
    pass

class ApiClient:
    def __init__(self, base_url: str, timeout: float) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url,
            timeout=httpx.Timeout(timeout),
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def request(self, method: str, url: str, **kwargs):
        try:
            r = await self._client.request(method, url, **kwargs)
        except httpx.HTTPError as e:
            raise ApiError(f"HTTP error: {e}") from e

        if r.status_code >= 400:
            # покажем максимум полезного
            text = r.text[:2000]
            raise ApiError(f"{method} {url} -> {r.status_code}: {text}")

        # иногда у тебя schema пустая -> но ответ все равно json
        if "application/json" in (r.headers.get("content-type") or ""):
            return r.json()
        return r.text
