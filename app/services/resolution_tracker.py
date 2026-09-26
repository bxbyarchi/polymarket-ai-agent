from __future__ import annotations

from typing import Any
import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import Market, MarketResolution
from app.services.calibration import resolved_outcome
from app.services.polymarket import PolymarketClient


class ResolutionTracker:
    def __init__(self, polymarket: PolymarketClient | None = None) -> None:
        self.polymarket = polymarket or PolymarketClient()

    async def resolve_stored_markets(self, session: AsyncSession) -> dict[str, int]:
        result = await session.execute(
            select(Market).where(Market.resolution.is_(None))
        )
        markets = list(result.scalars())
        checked = len(markets)
        resolved = 0
        concurrency = max(1, self.polymarket.settings.resolution_concurrency)
        semaphore = asyncio.Semaphore(concurrency)

        async def fetch_outcome(market: Market) -> tuple[str, int | None, str | None]:
            async with semaphore:
                try:
                    current = await self.polymarket.get_market(market.id)
                except Exception:
                    return market.id, None, None
                return market.id, resolved_outcome(current), self._json(current)

        results = await asyncio.gather(*(fetch_outcome(market) for market in markets))

        for market_id, outcome, raw_json in results:
            if outcome is None:
                continue

            existing = await session.get(MarketResolution, market_id)
            if existing is not None:
                continue

            session.add(
                MarketResolution(
                    market_id=market_id,
                    outcome=outcome,
                    source="polymarket",
                    raw_json=raw_json or "{}",
                )
            )
            market = await session.get(Market, market_id)
            if market is not None:
                market.closed = True
            resolved += 1

        await session.commit()
        return {"checked": checked, "resolved": resolved}

    @staticmethod
    def _json(value: Any) -> str:
        import json
        return json.dumps(value, default=str)
