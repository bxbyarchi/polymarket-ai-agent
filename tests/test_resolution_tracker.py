from app.services.calibration import resolved_outcome


def test_tracker_uses_terminal_prices():
    assert resolved_outcome({"outcomePrices": ["1", "0"], "closed": True}) == 1
    assert resolved_outcome({"outcomePrices": ["0", "1"], "closed": True}) == 0


def test_tracker_rejects_terminal_price_on_open_market():
    assert resolved_outcome({"outcomePrices": ["1", "0"], "closed": False}) is None
    assert resolved_outcome({"outcomePrices": ["1", "0"]}) is None
