from __future__ import annotations

from collections import defaultdict
from typing import Any

from app.services.calibration import score_prediction


def probability_bucket(probability: float, width: float = 0.1) -> str:
    p = max(0.0, min(1.0, float(probability)))
    start = min(int(p / width), int(1 / width) - 1)
    end = min(start + 1, int(1 / width))
    return f"{start * width:.1f}-{end * width:.1f}"


def _metrics(items: list[dict[str, Any]], field: str) -> dict[str, Any]:
    scores = []
    for item in items:
        probability = item.get(field)
        outcome = item.get("outcome")
        if probability is None or outcome not in (0, 1):
            continue
        scores.append(score_prediction(float(probability), int(outcome)))
    return {
        "predictions": len(scores),
        "brier_score": round(sum(x["brier_score"] for x in scores) / len(scores), 8) if scores else None,
        "log_loss": round(sum(x["log_loss"] for x in scores) / len(scores), 8) if scores else None,
    }


def backtest_predictions(predictions: list[dict[str, Any]]) -> dict[str, Any]:
    """Compare raw and calibrated historical predictions."""
    rows = [x for x in predictions if x.get("outcome") in (0, 1)]
    for row in rows:
        if row.get("raw_probability") is None:
            row["raw_probability"] = row.get("probability")
        if row.get("calibrated_probability") is None:
            row["calibrated_probability"] = row.get("probability")

    raw = _metrics(rows, "raw_probability")
    calibrated = _metrics(rows, "calibrated_probability")
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        buckets[probability_bucket(float(row["raw_probability"]))].append(row)

    calibration = []
    for bucket in sorted(buckets):
        group = buckets[bucket]
        calibration.append({
            "bucket": bucket,
            "predictions": len(group),
            "mean_raw_probability": round(sum(float(x["raw_probability"]) for x in group) / len(group), 6),
            "observed_yes_rate": round(sum(int(x["outcome"]) for x in group) / len(group), 6),
            "raw_brier_score": _metrics(group, "raw_probability")["brier_score"],
            "calibrated_brier_score": _metrics(group, "calibrated_probability")["brier_score"],
        })

    return {
        "raw": raw,
        "calibrated": calibrated,
        "delta": {
            "brier_score": round(calibrated["brier_score"] - raw["brier_score"], 8) if raw["brier_score"] is not None and calibrated["brier_score"] is not None else None,
            "log_loss": round(calibrated["log_loss"] - raw["log_loss"], 8) if raw["log_loss"] is not None and calibrated["log_loss"] is not None else None,
        },
        "calibration": calibration,
    }
