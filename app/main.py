from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from sqlalchemy import text

from app.api.routes import router, polymarket, research
from app.api.dashboard import router as dashboard_router
from app.config import get_settings
from app.db import SessionLocal, close_db

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    await polymarket.close()
    await research.close()
    await close_db()


app = FastAPI(
    title="Polymarket AI Agent",
    version="0.4.0",
    description="Read-only Polymarket market research and probability estimation service.",
    lifespan=lifespan,
)

app.include_router(router)
app.include_router(dashboard_router)


async def _database_reachable() -> bool:
    try:
        async with SessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


@app.get("/health")
async def health() -> dict:
    database_reachable = await _database_reachable()
    return {
        "status": "ok" if database_reachable else "degraded",
        "environment": settings.app_env,
        "ai_configured": bool(settings.openai_api_key),
        "database_configured": bool(settings.database_url),
        "database_reachable": database_reachable,
    }


@app.get("/ready")
async def ready() -> dict:
    database_reachable = await _database_reachable()
    if not database_reachable:
        raise HTTPException(status_code=503, detail="Database is not reachable")
    return {"status": "ready"}