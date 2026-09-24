from __future__ import annotations

import json
from typing import Any

import httpx

from app.config import get_settings


class MarketScanner:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def discover(
        self,
        *,
        limit: int,
        min_liquidity: float | None = None,
        min_volume: float | None = None,
    ) -> dict[str, Any]:
        params = {
            "active": "true",
            "closed": "false",
            "limit": limit,
            "offset": 0,
            "order": "volumeNum",
            "ascending": "false",
        }

        timeout = httpx.Timeout(self.settings.request_timeout_seconds)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(
                f"{self.settings.gamma_api_url.rstrip('/')}/markets",
                params=params,
            )
            response.raise_for_status()
            raw_markets = response.json()

        normalized = [self._normalize_market(m) for m in raw_markets]
        normalized = [
            m
            for m in normalized
            if (min_liquidity is None or m["liquidity"] >= min_liquidity)
            and (min_volume is None or m["volume"] >= min_volume)
        ]

        return {
            "count": len(normalized),
            "markets": normalized,
        }

    @staticmethod
    def _parse_json_field(value: Any, default: list[Any]) -> list[Any]:
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                return parsed if isinstance(parsed, list) else default
            except json.JSONDecodeError:
                return default
        return default

    def _normalize_market(self, market: dict[str, Any]) -> dict[str, Any]:
        outcomes = self._parse_json_field(market.get("outcomes"), [])
        prices = self._parse_json_field(market.get("outcomePrices"), [])
        token_ids = self._parse_json_field(market.get("clobTokenIds"), [])

        probability = None
        if prices:
            try:
                probability = float(prices[0])
            except (TypeError, ValueError):
                probability = None

        return {
            "id": str(market.get("id", "")),
            "question": market.get("question"),
            "slug": market.get("slug"),
            "condition_id": market.get("conditionId"),
            "active": bool(market.get("active")),
            "closed": bool(market.get("closed")),
            "start_date": market.get("startDate"),
            "end_date": market.get("endDate"),
            "volume": float(market.get("volumeNum") or market.get("volume") or 0),
            "volume_24h": float(market.get("volume24hr") or market.get("volume24hrClob") or 0),
            "liquidity": float(market.get("liquidityNum") or market.get("liquidity") or 0),
            "outcomes": outcomes,
            "outcome_prices": prices,
            "yes_probability": probability,
            "clob_token_ids": token_ids,
        }
