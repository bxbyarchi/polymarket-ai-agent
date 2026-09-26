from app.main import app


def test_health_and_readiness_routes_exist():
    routes = {route.path: route for route in app.routes}
    assert "/health" in routes
    assert "/ready" in routes


def test_scan_and_analyze_use_post_for_side_effects():
    routes = {
        (route.path, tuple(sorted(route.methods or [])))
        for route in app.routes
    }
    assert ("/scan", ("POST",)) in routes
    assert ("/analyze/{market_id}", ("POST",)) in routes
