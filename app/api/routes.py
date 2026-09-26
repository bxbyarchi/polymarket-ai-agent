from fastapi import APIRouter, HTTPException, Query

from app.agents.orchestrator import ResearchOrchestrator
from app.db import SessionLocal, get_market_history, MarketResolution
from app.services.persistence import PersistenceService
from app.services.polymarket import PolymarketClient
from app.services.scanner import MarketScanner
from app.services.scorer import MarketScorer
from app.services.calibration import resolved_outcome, score_prediction, summarize
from app.services.backtest import backtest_predictions
from app.services.resolution_tracker import ResolutionTracker
from app.services.calibrator import calibrate_probability
from app.services.walk_forward import walk_forward_backtest
from sqlalchemy import func, case
from app.db import ResearchRun, Market, MarketSnapshot

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
        from sqlalchemy import select
        from app.db import ResearchRun, MarketResolution
        async with SessionLocal() as session:
            result = await session.execute(
                select(ResearchRun, MarketResolution)
                .join(MarketResolution, ResearchRun.market_id == MarketResolution.market_id)
            )
            calibration_rows = [
                {
                    "probability": run.probability,
                    "raw_probability": run.raw_probability,
                    "outcome": resolution.outcome,
                    "created_at": run.created_at,
                    "resolved_at": resolution.resolved_at,
                }
                for run, resolution in result.all()
                if run.probability is not None
            ]
        calibration = backtest_predictions(calibration_rows)
        analysis = await research.run(market, calibration=calibration)
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




@router.get("/metrics")
async def metrics() -> dict:
    """Return high-level system and research-quality metrics."""
    from sqlalchemy import select

    async with SessionLocal() as session:
        markets_count = await session.scalar(select(func.count(Market.id)))
        snapshots_count = await session.scalar(select(func.count(MarketSnapshot.id)))
        runs_count = await session.scalar(select(func.count(ResearchRun.id)))
        resolutions_count = await session.scalar(select(func.count(MarketResolution.market_id)))

        result = await session.execute(
            select(ResearchRun, MarketResolution)
            .join(MarketResolution, ResearchRun.market_id == MarketResolution.market_id)
            .order_by(ResearchRun.created_at.asc())
            .limit(10000)
        )
        rows = result.all()

        latest_result = await session.execute(
            select(ResearchRun)
            .order_by(ResearchRun.created_at.desc())
            .limit(10)
        )
        latest_runs = list(latest_result.scalars())

    predictions = [
        {
            "probability": run.probability,
            "raw_probability": run.raw_probability,
            "outcome": resolution.outcome,
            "created_at": run.created_at,
            "resolved_at": resolution.resolved_at,
        }
        for run, resolution in rows
        if run.probability is not None
    ]
    quality = walk_forward_backtest(predictions)

    return {
        "system": {
            "markets": markets_count or 0,
            "snapshots": snapshots_count or 0,
            "research_runs": runs_count or 0,
            "resolved_markets": resolutions_count or 0,
        },
        "quality": {
            "predictions_evaluated": quality["predictions"],
            "calibrated_predictions": quality["calibrated_predictions"],
            "raw": quality["raw"],
            "calibrated": quality["calibrated"],
            "delta": quality["delta"],
        },
        "latest_research": [
            {
                "id": run.id,
                "market_id": run.market_id,
                "created_at": run.created_at.isoformat(),
                "probability": run.probability,
                "raw_probability": run.raw_probability,
                "calibrated_probability": run.calibrated_probability,
                "calibration_applied": run.calibration_applied,
                "market_probability": run.market_probability,
                "edge": run.edge,
                "confidence": run.confidence,
            }
            for run in latest_runs
        ],
    }


@router.get("/calibration")
async def calibration(limit: int = Query(default=500, ge=1, le=5000)) -> dict:
    """Backtest saved research predictions against currently resolved markets."""
    from sqlalchemy import select
    from app.db import Market, ResearchRun, MarketResolution

    async with SessionLocal() as session:
        result = await session.execute(
            select(ResearchRun, MarketResolution)
            .join(MarketResolution, ResearchRun.market_id == MarketResolution.market_id)
            .order_by(ResearchRun.created_at.desc())
            .limit(limit)
        )
        rows = result.all()

    predictions = [
        {
            "research_run_id": run.id,
            "market_id": resolution.market_id,
            "probability": run.probability,
            "raw_probability": run.raw_probability,
            "calibrated_probability": run.calibrated_probability,
            "outcome": resolution.outcome,
            "created_at": run.created_at,
            "resolved_at": resolution.resolved_at,
        }
        for run, resolution in rows
        if run.probability is not None
    ]
    return walk_forward_backtest(predictions)


@router.get("/calibration/raw")
async def calibration_raw(limit: int = Query(default=5000, ge=1, le=10000)) -> dict:
    """Evaluate calibration out-of-sample using only earlier resolutions."""
    from sqlalchemy import select
    from app.db import ResearchRun, MarketResolution

    async with SessionLocal() as session:
        result = await session.execute(
            select(ResearchRun, MarketResolution)
            .join(MarketResolution, ResearchRun.market_id == MarketResolution.market_id)
            .order_by(ResearchRun.created_at.asc())
            .limit(limit)
        )
        rows = result.all()

    predictions = [
        {
            "probability": run.probability,
            "raw_probability": run.raw_probability,
            "outcome": resolution.outcome,
            "created_at": run.created_at,
            "resolved_at": resolution.resolved_at,
        }
        for run, resolution in rows
        if run.probability is not None
    ]
    return backtest_predictions(predictions)


@router.post("/resolutions/sync")
async def sync_resolutions() -> dict:
    tracker = ResolutionTracker(polymarket)
    async with SessionLocal() as session:
        return await tracker.resolve_stored_markets(session)


@router.get("/resolutions")
async def resolutions(limit: int = Query(default=100, ge=1, le=1000)) -> dict:
    from sqlalchemy import select

    async with SessionLocal() as session:
        result = await session.execute(
            select(MarketResolution)
            .order_by(MarketResolution.resolved_at.desc())
            .limit(limit)
        )
        rows = list(result.scalars())
        return {
            "count": len(rows),
            "resolutions": [
                {
                    "market_id": row.market_id,
                    "resolved_at": row.resolved_at.isoformat(),
                    "outcome": row.outcome,
                    "source": row.source,
                }
                for row in rows
            ],
        }


@router.get("/calibration/apply")
async def apply_calibration(
    probability: float = Query(..., ge=0, le=1),
    min_samples: int = Query(default=20, ge=1, le=1000),
) -> dict:
    """Return an empirically calibrated probability from resolved history."""
    from sqlalchemy import select
    from app.db import MarketResolution, ResearchRun

    async with SessionLocal() as session:
        result = await session.execute(
            select(ResearchRun, MarketResolution)
            .join(
                MarketResolution,
                ResearchRun.market_id == MarketResolution.market_id,
            )
        )
        predictions = [
            {"probability": run.probability, "outcome": resolution.outcome}
            for run, resolution in result.all()
            if run.probability is not None
        ]

    from app.services.backtest import backtest_predictions
    calibration = backtest_predictions(predictions)
    return calibrate_probability(probability, calibration, min_samples)
