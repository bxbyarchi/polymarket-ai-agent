from app.services.calibration import resolved_outcome


def test_tracker_uses_terminal_prices():
    assert resolved_outcome({"outcomePrices": ["1", "0"], "closed": True}) == 1
    assert resolved_outcome({"outcomePrices": ["0", "1"], "closed": True}) == 0
