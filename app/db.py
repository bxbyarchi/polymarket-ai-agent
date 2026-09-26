from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.config import get_settings


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _json(value: Any) -> Any:
    if value is None:
        return None
    return json.loads(json.dumps(value, default=str))


class Base(DeclarativeBase):
    pass


class Market(Base):
    __tablename__ = "markets"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    question: Mapped[str | None] = mapped_column(Text)
    slug: Mapped[str | None] = mapped_column(String(512))
    condition_id: Mapped[str | None] = mapped_column(String(256))
    active: Mapped[bool] = mapped_column(default=True)
    closed: Mapped[bool] = mapped_column(default=False)
    start_date: Mapped[str | None] = mapped_column(String(64))
    end_date: Mapped[str | None] = mapped_column(String(64))
    resolution_source: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    outcomes_json: Mapped[str] = mapped_column(Text, default="[]")
    token_ids_json: Mapped[str] = mapped_column(Text, default="[]")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    snapshots: Mapped[list["MarketSnapshot"]] = relationship(
        back_populates="market", cascade="all, delete-orphan"
    )
    research_runs: Mapped[list["ResearchRun"]] = relationship(
        back_populates="market", cascade="all, delete-orphan"
    )
    resolution: Mapped["MarketResolution | None"] = relationship(
        back_populates="market", cascade="all, delete-orphan", uselist=False
    )


class MarketSnapshot(Base):
    __tablename__ = "market_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    market_id: Mapped[str] = mapped_column(ForeignKey("markets.id"), index=True)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, index=True)
    volume: Mapped[float] = mapped_column(Float, default=0.0)
    volume_24h: Mapped[float] = mapped_column(Float, default=0.0)
    liquidity: Mapped[float] = mapped_column(Float, default=0.0)
    yes_probability: Mapped[float | None] = mapped_column(Float)
    research_priority: Mapped[float | None] = mapped_column(Float)
    outcome_prices_json: Mapped[str] = mapped_column(Text, default="[]")
    raw_json: Mapped[str] = mapped_column(Text, default="{}")

    market: Mapped[Market] = relationship(back_populates="snapshots")


class MarketResolution(Base):
    __tablename__ = "market_resolutions"

    market_id: Mapped[str] = mapped_column(ForeignKey("markets.id"), primary_key=True)
    resolved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    outcome: Mapped[int] = mapped_column(Integer)
    source: Mapped[str] = mapped_column(String(64), default="polymarket")
    raw_json: Mapped[str] = mapped_column(Text, default="{}")

    market: Mapped[Market] = relationship(back_populates="resolution")


class ResearchRun(Base):
    __tablename__ = "research_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    market_id: Mapped[str] = mapped_column(ForeignKey("markets.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, index=True)
    model: Mapped[str] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(32), default="completed")
    probability: Mapped[float | None] = mapped_column(Float)
    raw_probability: Mapped[float | None] = mapped_column(Float)
    calibrated_probability: Mapped[float | None] = mapped_column(Float)
    calibration_applied: Mapped[bool] = mapped_column(default=False)
    confidence: Mapped[float | None] = mapped_column(Float)
    market_probability: Mapped[float | None] = mapped_column(Float)
    edge: Mapped[float | None] = mapped_column(Float)
    summary: Mapped[str | None] = mapped_column(Text)
    key_factors_json: Mapped[str] = mapped_column(Text, default="[]")
    counter_factors_json: Mapped[str] = mapped_column(Text, default="[]")
    raw_json: Mapped[str] = mapped_column(Text, default="{}")
    error: Mapped[str | None] = mapped_column(Text)

    market: Mapped[Market] = relationship(back_populates="research_runs")
    sources: Mapped[list["ResearchSource"]] = relationship(
        back_populates="research_run", cascade="all, delete-orphan"
    )


class ResearchSource(Base):
    __tablename__ = "research_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    research_run_id: Mapped[int] = mapped_column(ForeignKey("research_runs.id"), index=True)
    title: Mapped[str] = mapped_column(Text)
    url: Mapped[str] = mapped_column(Text)

    research_run: Mapped[ResearchRun] = relationship(back_populates="sources")


settings = get_settings()
database_url = settings.database_url
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
elif database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(database_url, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    await engine.dispose()


async def upsert_market(session: AsyncSession, market: dict[str, Any]) -> Market:
    market_id = str(market.get("id", ""))
    row = await session.get(Market, market_id)
    if row is None:
        row = Market(id=market_id)
        session.add(row)

    row.question = market.get("question")
    row.slug = market.get("slug")
    row.condition_id = market.get("condition_id") or market.get("conditionId")
    row.active = bool(market.get("active"))
    row.closed = bool(market.get("closed"))
    row.start_date = market.get("start_date") or market.get("startDate")
    row.end_date = market.get("end_date") or market.get("endDate")
    row.resolution_source = market.get("resolution_source") or market.get("resolutionSource")
    row.description = market.get("description")
    row.outcomes_json = json.dumps(_json(market.get("outcomes", [])))
    row.token_ids_json = json.dumps(
        _json(market.get("clob_token_ids") or market.get("clobTokenIds") or [])
    )
    row.updated_at = _utcnow()
    return row


async def save_market_snapshot(
    session: AsyncSession, market: dict[str, Any], research_priority: float | None = None
) -> MarketSnapshot:
    await upsert_market(session, market)
    snapshot = MarketSnapshot(
        market_id=str(market.get("id", "")),
        volume=float(market.get("volume") or market.get("volumeNum") or 0),
        volume_24h=float(
            market.get("volume_24h")
            or market.get("volume24hr")
            or market.get("volume24hrClob")
            or 0
        ),
        liquidity=float(market.get("liquidity") or market.get("liquidityNum") or 0),
        yes_probability=_first_float(
            market.get("outcome_prices") or market.get("outcomePrices") or []
        ),
        research_priority=research_priority,
        outcome_prices_json=json.dumps(
            _json(market.get("outcome_prices") or market.get("outcomePrices") or [])
        ),
        raw_json=json.dumps(_json(market)),
    )
    session.add(snapshot)
    return snapshot


async def save_research_run(
    session: AsyncSession, market: dict[str, Any], analysis: dict[str, Any]
) -> ResearchRun:
    await upsert_market(session, market)
    run = ResearchRun(
        market_id=str(market.get("id", "")),
        model=settings.openai_model,
        status="completed",
        probability=analysis.get("probability"),
        raw_probability=(analysis.get("calibration") or {}).get("raw_probability", analysis.get("probability")),
        calibrated_probability=(analysis.get("calibration") or {}).get("calibrated_probability", analysis.get("probability")),
        calibration_applied=bool((analysis.get("calibration") or {}).get("applied", False)),
        confidence=analysis.get("confidence"),
        market_probability=analysis.get("market_probability"),
        edge=analysis.get("edge"),
        summary=analysis.get("summary"),
        key_factors_json=json.dumps(_json(analysis.get("key_factors", []))),
        counter_factors_json=json.dumps(_json(analysis.get("counter_factors", []))),
        raw_json=json.dumps(_json(analysis)),
    )
    session.add(run)
    await session.flush()

    for source in analysis.get("sources") or []:
        if not isinstance(source, dict):
            continue
        url = str(source.get("url") or "").strip()
        title = str(source.get("title") or url).strip()
        if url:
            session.add(ResearchSource(research_run_id=run.id, title=title, url=url))

    return run


def _first_float(values: Any) -> float | None:
    if not isinstance(values, list) or not values:
        return None
    try:
        return float(values[0])
    except (TypeError, ValueError):
        return None


async def get_market_history(
    session: AsyncSession, market_id: str, limit: int = 50
) -> dict[str, Any]:
    market = await session.get(Market, market_id)
    if market is None:
        return {"market": None, "snapshots": [], "research_runs": []}

    snapshots_result = await session.execute(
        select(MarketSnapshot)
        .where(MarketSnapshot.market_id == market_id)
        .order_by(MarketSnapshot.captured_at.desc())
        .limit(limit)
    )
    runs_result = await session.execute(
        select(ResearchRun)
        .where(ResearchRun.market_id == market_id)
        .order_by(ResearchRun.created_at.desc())
        .limit(limit)
    )

    return {
        "market": {
            "id": market.id,
            "question": market.question,
            "slug": market.slug,
            "active": market.active,
            "closed": market.closed,
            "start_date": market.start_date,
            "end_date": market.end_date,
            "updated_at": market.updated_at.isoformat() if market.updated_at else None,
        },
        "snapshots": [
            {
                "id": row.id,
                "captured_at": row.captured_at.isoformat(),
                "volume": row.volume,
                "volume_24h": row.volume_24h,
                "liquidity": row.liquidity,
                "yes_probability": row.yes_probability,
                "research_priority": row.research_priority,
            }
            for row in snapshots_result.scalars()
        ],
        "research_runs": [
            {
                "id": row.id,
                "created_at": row.created_at.isoformat(),
                "model": row.model,
                "status": row.status,
                "probability": row.probability,
                "raw_probability": row.raw_probability,
                "calibrated_probability": row.calibrated_probability,
                "calibration_applied": row.calibration_applied,
                "confidence": row.confidence,
                "market_probability": row.market_probability,
                "edge": row.edge,
                "summary": row.summary,
            }
            for row in runs_result.scalars()
        ],
    }
