from __future__ import annotations

from typing import Any


def calibrate_probability(
    probability: float,
    calibration: dict[str, Any],
    min_bucket_samples: int = 20,
) -> dict[str, Any]:
    """Apply empirical calibration only when a bucket has enough resolved samples."""
    p = max(0.0, min(1.0, float(probability)))
    bucket = _bucket(p)
    rows = calibration.get("calibration") or []

    match = next((row for row in rows if row.get("bucket") == bucket), None)
    if not match or int(match.get("predictions", 0)) < min_bucket_samples:
        return {
            "raw_probability": round(p, 6),
            "calibrated_probability": round(p, 6),
            "bucket": bucket,
            "samples": int(match.get("predictions", 0)) if match else 0,
            "applied": False,
        }

    observed = match.get("observed_yes_rate")
    if observed is None:
        return {
            "raw_probability": round(p, 6),
            "calibrated_probability": round(p, 6),
            "bucket": bucket,
            "samples": int(match.get("predictions", 0)),
            "applied": False,
        }

    calibrated = max(0.0, min(1.0, float(observed)))
    return {
        "raw_probability": round(p, 6),
        "calibrated_probability": round(calibrated, 6),
        "bucket": bucket,
        "samples": int(match.get("predictions", 0)),
        "applied": True,
    }


def _bucket(probability: float) -> str:
    start = min(int(probability / 0.1), 9)
    end = min(start + 1, 10)
    return f"{start / 10:.1f}-{end / 10:.1f}"
