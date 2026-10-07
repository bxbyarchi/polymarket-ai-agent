import pytest

from app.services.calibration import resolved_outcome


@pytest.mark.parametrize(
    ("market", "expected"),
    [
        ({"closed": True, "outcomePrices": ["1", "0"]}, 1),
        ({"closed": True, "outcomePrices": ["0", "1"]}, 0),
        ({"closed": True, "outcomePrices": '["1", "0"]'}, 1),
        ({"closed": True, "outcomePrices": '["0", "1"]'}, 0),
        ({"closed": False, "outcomePrices": '["1", "0"]'}, None),
        ({"closed": True, "outcomePrices": '["0.5", "0.5"]'}, None),
    ],
)
def test_resolved_outcome_handles_gamma_price_formats(market, expected):
    assert resolved_outcome(market) == expected
