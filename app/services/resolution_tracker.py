from __future__ import annotations

from typing import Any

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
        checked = 0
        resolved = 0

        for market in markets:
            checked += 1
            try:
                current = await self.polymarket.get_market(market.id)
            except Exception:
                continue

            outcome = resolved_outcome(current)
            if outcome is None:
                continue

            existing = await session.get(MarketResolution, market.id)
            if existing is not None:
                continue

            session.add(
                MarketResolution(
                    market_id=market.id,
                    outcome=outcome,
                    source="polymarket",
                    raw_json=self._json(current),
                )
            )
            market.closed = True
            resolved += 1

        await session.commit()
        return {"checked": checked, "resolved": resolved}

    @staticmethod
    def _json(value: Any) -> str:
        import json
        return json.dumps(value, default=str)
