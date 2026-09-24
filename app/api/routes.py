from fastapi import APIRouter, HTTPException, Query

from app.agents.orchestrator import ResearchOrchestrator
from app.db import SessionLocal, get_market_history
from app.services.persistence import PersistenceService
from app.services.polymarket import PolymarketClient
from app.services.scanner import MarketScanner
from app.services.scorer import MarketScorer

router = APIRouter()
scanner = MarketScanner()
polymarket = PolymarketClient()
research = ResearchOrchestrator()
scorer = MarketScorer()
persistence = PersistenceService()


@router.get("/")
async def root() -> dict:
    return {
        "name": "Polymarket AI Agent",
        "version": "0.4.0",
        "mode": "research-only",
    }


@router.get("/markets")
async def markets(
    limit: int = Query(default=50, ge=1, le=100),
    min_liquidity: float | None = Query(default=None, ge=0),
    min_volume: float | None = Query(default=None, ge=0),
) -> dict:
    return await scanner.discover(
        limit=limit,
        min_liquidity=min_liquidity,
        min_volume=min_volume,
    )


@router.get("/scan")
async def scan_markets(
    limit: int = Query(default=20, ge=1, le=100),
    min_liquidity: float | None = Query(default=None, ge=0),
    min_volume: float | None = Query(default=None, ge=0),
) -> dict:
    result = await scanner.discover(
        limit=limit,
        min_liquidity=min_liquidity,
        min_volume=min_volume,
    )
    markets_with_priority = [
        {**market, "research_priority": scorer.score(market)}
        for market in result["markets"]
    ]
    markets_with_priority.sort(
        key=lambda item: item["research_priority"], reverse=True
    )

    priorities = {
        str(market["id"]): market["research_priority"]
        for market in markets_with_priority
    }
    await persistence.save_scan(markets_with_priority, priorities)

    return {"count": len(markets_with_priority), "markets": markets_with_priority}


@router.get("/analyze/{market_id}")
async def analyze_market(market_id: str) -> dict:
    try:
        market = await polymarket.get_market(market_id)
        analysis = await research.run(market)
        run_id = await persistence.save_analysis(market, analysis)
        return {"research_run_id": run_id, "market": market, "analysis": analysis}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/history/{market_id}")
async def market_history(
    market_id: str,
    limit: int = Query(default=50, ge=1, le=200),
) -> dict:
    async with SessionLocal() as session:
        return await get_market_history(session, market_id, limit)
