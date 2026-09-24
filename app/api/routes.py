from fastapi import APIRouter, HTTPException, Query

from app.agents.analyst import Analyst
from app.services.polymarket import PolymarketClient
from app.services.scanner import MarketScanner

router = APIRouter()
scanner = MarketScanner()
polymarket = PolymarketClient()
analyst = Analyst()


@router.get("/")
async def root() -> dict:
    return {
        "name": "Polymarket AI Agent",
        "version": "0.2.0",
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


@router.get("/analyze/{market_id}")
async def analyze_market(market_id: str) -> dict:
    try:
        market = await polymarket.get_market(market_id)
        return analyst.analyze(market)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
