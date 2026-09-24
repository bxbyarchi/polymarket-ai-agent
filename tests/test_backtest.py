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
    assert result["overall"]["predictions"] == 3
    assert result["calibration"][0]["predictions"] == 1
