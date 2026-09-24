from app.services.calibrator import calibrate_probability


def test_calibration_requires_minimum_samples():
    result = calibrate_probability(
        0.75,
        {"calibration": [{"bucket": "0.7-0.8", "predictions": 3, "observed_yes_rate": 0.6}]},
    )
    assert result["calibrated_probability"] == 0.75
    assert result["applied"] is False


def test_calibration_uses_observed_rate():
    result = calibrate_probability(
        0.75,
        {"calibration": [{"bucket": "0.7-0.8", "predictions": 25, "observed_yes_rate": 0.64}]},
    )
    assert result["calibrated_probability"] == 0.64
    assert result["applied"] is True
