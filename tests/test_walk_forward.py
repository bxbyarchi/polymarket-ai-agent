from datetime import datetime, timezone, timedelta

from app.services.walk_forward import walk_forward_backtest


def test_walk_forward_does_not_use_future_resolutions():
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    rows = [
        {"probability": 0.8, "outcome": 0, "created_at": base, "resolved_at": base + timedelta(days=10)},
        {"probability": 0.8, "outcome": 1, "created_at": base + timedelta(days=1), "resolved_at": base + timedelta(days=2)},
    ]
    result = walk_forward_backtest(rows, min_bucket_samples=1)
    assert result["predictions"] == 2
    assert result["calibrated_predictions"] == 0


def test_walk_forward_uses_only_prior_resolutions():
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    rows = [
        {"probability": 0.8, "outcome": 0, "created_at": base, "resolved_at": base + timedelta(hours=1)},
        {"probability": 0.8, "outcome": 1, "created_at": base + timedelta(days=2), "resolved_at": base + timedelta(days=3)},
    ]
    result = walk_forward_backtest(rows, min_bucket_samples=1)
    assert result["calibrated_predictions"] == 1


def test_walk_forward_requires_resolution_before_prediction_for_calibration():
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    rows = [
        {"probability": 0.8, "outcome": 0, "created_at": base, "resolved_at": base + timedelta(days=5)},
        {"probability": 0.8, "outcome": 1, "created_at": base + timedelta(days=1), "resolved_at": base + timedelta(days=2)},
        {"probability": 0.8, "outcome": 1, "created_at": base + timedelta(days=6), "resolved_at": base + timedelta(days=7)},
    ]
    result = walk_forward_backtest(rows, min_bucket_samples=1)
    assert result["calibrated_predictions"] == 1


def test_walk_forward_excludes_predictions_created_after_resolution():
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    rows = [
        {"probability": 0.9, "outcome": 1, "created_at": base + timedelta(days=2), "resolved_at": base + timedelta(days=1)},
    ]
    result = walk_forward_backtest(rows, min_bucket_samples=1)
    assert result["predictions"] == 0
