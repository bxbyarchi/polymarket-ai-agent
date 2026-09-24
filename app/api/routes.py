from fastapi import APIRouter, Query

from app.services.scanner import MarketScanner

router = APIRouter()
scanner = MarketScanner()


@router.get("/")
async def root() -> dict:
    return {
        "name": "Polymarket AI Agent",
        "version": "0.1.0",
        "mode": "research-only",
    }


@router.get("/markets")
async def markets(
    limit: int = Query(default=50, ge=1, le=100),
    min_liquidity: float | None = Query(default=None, ge=0),
    min_volume: float | None = Query(default=None, ge=0),
) -> dict:
    result = await scanner.discover(
        limit=limit,
        min_liquidity=min_liquidity,
        min_volume=min_volume,
    )
    return result
