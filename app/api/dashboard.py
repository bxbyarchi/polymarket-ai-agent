from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

DASHBOARD_PATH = Path(__file__).resolve().parents[1] / "dashboard.html"


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard() -> str:
    return DASHBOARD_PATH.read_text(encoding="utf-8")
