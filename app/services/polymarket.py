from __future__ import annotations

from typing import Any

import httpx

from app.config import get_settings


class PolymarketClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def get_market(self, market_id: str) -> dict[str, Any]:
        timeout = httpx.Timeout(self.settings.request_timeout_seconds)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(
                f"{self.settings.gamma_api_url.rstrip('/')}/markets/{market_id}"
            )
            response.raise_for_status()
            return response.json()
