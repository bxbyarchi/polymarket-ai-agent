from app.services.backtest import backtest_predictions, probability_bucket


def test_probability_bucket():
    assert probability_bucket(0.57) == "0.5-0.6"
    assert probability_bucket(0.99) == "0.9-1.0"


def test_backtest_calibration():
    result = backtest_predictions([
        {"probability": 0.8, "outcome": 1},
        {"probability": 0.6, "outcome": 0},
        {"probability": 0.9, "outcome": 1},
    ])
    assert result["predictions"] == 3
    assert result["calibration"][0]["predictions"] == 1


def test_raw_vs_calibrated_metrics():
    result = backtest_predictions([
        {"raw_probability": 0.8, "calibrated_probability": 0.6, "outcome": 1},
        {"raw_probability": 0.8, "calibrated_probability": 0.6, "outcome": 0},
    ])
    assert result["raw"]["predictions"] == 2
    assert result["calibrated"]["predictions"] == 2
    assert result["delta"]["brier_score"] < 0
