from __future__ import annotations

from typing import Any

from app.db import SessionLocal, save_market_snapshot, save_research_run


class PersistenceService:
    async def save_scan(
        self, markets: list[dict[str, Any]], priorities: dict[str, float]
    ) -> None:
        async with SessionLocal() as session:
            for market in markets:
                await save_market_snapshot(
                    session, market, priorities.get(str(market.get("id")))
                )
            await session.commit()

    async def save_analysis(
        self, market: dict[str, Any], analysis: dict[str, Any]
    ) -> int:
        async with SessionLocal() as session:
            run = await save_research_run(session, market, analysis)
            await session.commit()
            return run.id
