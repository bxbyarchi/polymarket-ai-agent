from __future__ import annotations

from datetime import datetime
from typing import Any

from app.services.backtest import _metrics, backtest_predictions, probability_bucket
from app.services.calibrator import calibrate_probability


def _timestamp(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def walk_forward_backtest(
    predictions: list[dict[str, Any]],
    min_bucket_samples: int = 20,
) -> dict[str, Any]:
    """Evaluate calibration out-of-sample using only resolutions before each prediction."""
    rows: list[dict[str, Any]] = []
    for item in predictions:
        if item.get("outcome") not in (0, 1):
            continue
        raw = item.get("raw_probability", item.get("probability"))
        created = _timestamp(item.get("created_at"))
        resolved = _timestamp(item.get("resolved_at"))
        if raw is None or created is None or resolved is None:
            continue
        rows.append({
            **item,
            "raw_probability": float(raw),
            "_created": created,
            "_resolved": resolved,
        })

    rows.sort(key=lambda x: x["_created"])
    history: list[dict[str, Any]] = []
    scored: list[dict[str, Any]] = []

    for row in rows:
        prior = [
            {"probability": item["raw_probability"], "outcome": item["outcome"]}
            for item in history
            if item["_resolved"] < row["_created"]
        ]
        calibration = backtest_predictions(prior)
        applied = calibrate_probability(
            row["raw_probability"],
            calibration,
            min_bucket_samples=min_bucket_samples,
        )
        scored.append({
            "raw_probability": row["raw_probability"],
            "calibrated_probability": applied["calibrated_probability"],
            "outcome": row["outcome"],
            "calibration_applied": applied["applied"],
            "calibration_samples": applied["samples"],
            "created_at": row["_created"].isoformat(),
            "resolved_at": row["_resolved"].isoformat(),
        })
        history.append(row)

    raw = _metrics(scored, "raw_probability")
    calibrated = _metrics(scored, "calibrated_probability")
    return {
        "predictions": len(scored),
        "calibrated_predictions": sum(1 for row in scored if row["calibration_applied"]),
        "raw": raw,
        "calibrated": calibrated,
        "delta": {
            "brier_score": round(calibrated["brier_score"] - raw["brier_score"], 8)
            if raw["brier_score"] is not None and calibrated["brier_score"] is not None else None,
            "log_loss": round(calibrated["log_loss"] - raw["log_loss"], 8)
            if raw["log_loss"] is not None and calibrated["log_loss"] is not None else None,
        },
        "calibration": [
            {
                "bucket": bucket,
                "predictions": len(group),
                "calibrated_predictions": sum(1 for x in group if x["calibration_applied"]),
                "mean_raw_probability": round(sum(x["raw_probability"] for x in group) / len(group), 6),
                "observed_yes_rate": round(sum(x["outcome"] for x in group) / len(group), 6),
                "raw_brier_score": _metrics(group, "raw_probability")["brier_score"],
                "calibrated_brier_score": _metrics(group, "calibrated_probability")["brier_score"],
            }
            for bucket, group in sorted(
                _bucket_groups(scored).items()
            )
        ],
    }


def _bucket_groups(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        bucket = probability_bucket(row["raw_probability"])
        groups.setdefault(bucket, []).append(row)
    return groups
