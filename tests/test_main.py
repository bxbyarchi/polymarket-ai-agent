from app.main import app
from app.api.routes import router as api_router
from fastapi.routing import APIRoute


def test_health_and_readiness_routes_exist():
    routes = {route.path: route for route in app.routes if isinstance(route, APIRoute)}
    assert "/health" in routes
    assert "/ready" in routes


def test_scan_and_analyze_use_post_for_side_effects():
    routes = {
        (route.path, tuple(sorted(route.methods or [])))
        for route in api_router.routes
        if isinstance(route, APIRoute)
    }
    assert ("/scan", ("POST",)) in routes
    assert ("/analyze/{market_id}", ("POST",)) in routes



def test_admin_key_guard_rejects_missing_or_invalid(monkeypatch):
    import pytest
    from app.api import routes
    from fastapi import HTTPException

    class Settings:
        admin_api_key = "expected-secret"

    monkeypatch.setattr(routes, "get_settings", lambda: Settings())
    class Unconfigured:
        admin_api_key = ""

    monkeypatch.setattr(routes, "get_settings", lambda: Unconfigured())
    with pytest.raises(HTTPException) as unconfigured:
        routes._require_admin_key("anything")
    assert unconfigured.value.status_code == 503

    monkeypatch.setattr(routes, "get_settings", lambda: Settings())
    with pytest.raises(HTTPException) as missing:
        routes._require_admin_key(None)
    assert missing.value.status_code == 401

    with pytest.raises(HTTPException) as invalid:
        routes._require_admin_key("wrong-secret")
    assert invalid.value.status_code == 401

    routes._require_admin_key("expected-secret")
