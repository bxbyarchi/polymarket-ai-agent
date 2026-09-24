from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router
from app.config import get_settings
from app.db import close_db, init_db

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    yield
    await close_db()


app = FastAPI(
    title="Polymarket AI Agent",
    version="0.4.0",
    description="Read-only Polymarket market research and probability estimation service.",
    lifespan=lifespan,
)

app.include_router(router)


@app.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "environment": settings.app_env,
        "ai_configured": bool(settings.openai_api_key),
        "database_configured": bool(settings.database_url),
    }
