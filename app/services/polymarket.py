from __future__ import annotations

from typing import Any

import httpx

from app.config import get_settings


class PolymarketClient:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            timeout = httpx.Timeout(self.settings.request_timeout_seconds)
            self._client = httpx.AsyncClient(timeout=timeout)
        return self._client

    async def get_market(self, market_id: str) -> dict[str, Any]:
        response = await self._get_client().get(
            f"{self.settings.gamma_api_url.rstrip('/')}/markets/{market_id}"
        )
        response.raise_for_status()
        return response.json()

    async def close(self) -> None:
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
        self._client = None

    async def __aenter__(self) -> "PolymarketClient":
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        await self.close()
