from __future__ import annotations

import asyncio
import logging
from typing import Any

from app.agents.orchestrator import ResearchOrchestrator
from app.config import get_settings
from app.db import SessionLocal, init_db, save_market_snapshot, save_research_run, MarketResolution, ResearchRun
from app.services.polymarket import PolymarketClient
from app.services.scanner import MarketScanner
from app.services.scorer import MarketScorer
from app.services.resolution_tracker import ResolutionTracker
from app.services.backtest import backtest_predictions

logger = logging.getLogger(__name__)


class MarketWorker:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.scanner = MarketScanner()
        self.polymarket = PolymarketClient()
        self.scorer = MarketScorer()
        self.research = ResearchOrchestrator()
        self.analyst = self.research.analyst
        self.critic = self.research.critic
        self.resolution_tracker = ResolutionTracker(self.polymarket)

    async def run_once(self) -> dict[str, Any]:
        async with SessionLocal() as session:
            resolution_summary = await self.resolution_tracker.resolve_stored_markets(session)

        result = await self.scanner.discover(
            limit=self.settings.default_market_limit,
            min_liquidity=self.settings.min_liquidity,
            min_volume=self.settings.min_volume,
        )

        markets = [
            {**market, "research_priority": self.scorer.score(market)}
            for market in result["markets"]
        ]
        markets.sort(key=lambda item: item["research_priority"], reverse=True)

        async with SessionLocal() as session:
            for market in markets:
                await save_market_snapshot(
                    session, market, market["research_priority"]
                )
            await session.commit()

        analyzed = 0
        failures = 0
        max_research = max(0, self.settings.worker_max_research_per_cycle)

        for market in markets[:max_research]:
            try:
                full_market = await self.polymarket.get_market(str(market["id"]))
                calibration = await self._load_calibration()
                analysis = await self.research.run(full_market, calibration=calibration)
                async with SessionLocal() as session:
                    await save_research_run(session, full_market, analysis)
                    await session.commit()
                analyzed += 1
            except Exception:
                failures += 1
                logger.exception("Research failed for market %s", market["id"])

        return {
            "markets_scanned": len(markets),
            "markets_checked_for_resolution": resolution_summary["checked"],
            "markets_resolved": resolution_summary["resolved"],
            "markets_researched": analyzed,
            "research_failures": failures,
        }

    async def _load_calibration(self) -> dict[str, Any]:
        from sqlalchemy import select

        async with SessionLocal() as session:
            result = await session.execute(
                select(
                    ResearchRun.probability,
                    ResearchRun.raw_probability,
                    ResearchRun.created_at,
                    MarketResolution.outcome,
                    MarketResolution.resolved_at,
                )
                .join(MarketResolution, ResearchRun.market_id == MarketResolution.market_id)
            )
            predictions = [
                {
                    "probability": probability,
                    "raw_probability": raw_probability,
                    "outcome": outcome,
                    "created_at": created_at,
                    "resolved_at": resolved_at,
                }
                for probability, raw_probability, created_at, outcome, resolved_at in result.all()
                if probability is not None
            ]
        return backtest_predictions(predictions)


async def run_forever() -> None:
    logging.basicConfig(level=get_settings().log_level)
    settings = get_settings()
    await init_db()

    worker = MarketWorker()
    while True:
        try:
            summary = await worker.run_once()
            logger.info("Worker cycle completed: %s", summary)
        except Exception:
            logger.exception("Worker cycle failed")

        await asyncio.sleep(settings.worker_interval_seconds)


if __name__ == "__main__":
    asyncio.run(run_forever())
