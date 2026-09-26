from app.main import app


def test_dashboard_route_is_registered():
    paths = {route.path for route in app.routes}
    assert "/dashboard" in paths
