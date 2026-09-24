from fastapi import FastAPI

from app.api.routes import router
from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title="Polymarket AI Agent",
    version="0.3.0",
    description="Read-only Polymarket market research and probability estimation service.",
)

app.include_router(router)


@app.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "environment": settings.app_env,
        "ai_configured": bool(settings.openai_api_key),
    }
