from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from app.api.routes import router
from app.api.dashboard import router as dashboard_router
from app.config import get_settings
from app.db import SessionLocal, close_db

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    await close_db()


app = FastAPI(
    title="Polymarket AI Agent",
    version="0.4.0",
    description="Read-only Polymarket market research and probability estimation service.",
    lifespan=lifespan,
)

app.include_router(router)
app.include_router(dashboard_router)


@app.get("/health")
async def health() -> dict:
    database_reachable = False
    try:
        async with SessionLocal() as session:
            await session.execute(text("SELECT 1"))
        database_reachable = True
    except Exception:
        database_reachable = False

    return {
        "status": "ok" if database_reachable else "degraded",
        "environment": settings.app_env,
        "ai_configured": bool(settings.openai_api_key),
        "database_configured": bool(settings.database_url),
        "database_reachable": database_reachable,
    }