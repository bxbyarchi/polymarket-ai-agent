from __future__ import annotations

from collections import defaultdict
from typing import Any

from app.services.calibration import score_prediction


def probability_bucket(probability: float, width: float = 0.1) -> str:
    p = max(0.0, min(1.0, float(probability)))
    start = min(int(p / width), int(1 / width) - 1)
    end = min(start + 1, int(1 / width))
    return f"{start * width:.1f}-{end * width:.1f}"


def backtest_predictions(predictions: list[dict[str, Any]]) -> dict[str, Any]:
    """Build calibration buckets from resolved historical predictions."""
    resolved = []
    for item in predictions:
        probability = item.get("probability")
        outcome = item.get("outcome")
        if probability is None or outcome not in (0, 1):
            continue
        score = score_prediction(float(probability), int(outcome))
        resolved.append({
            "probability": float(probability),
            "outcome": int(outcome),
            **score,
        })

    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in resolved:
        buckets[probability_bucket(item["probability"])].append(item)

    calibration = []
    for bucket in sorted(buckets):
        rows = buckets[bucket]
        calibration.append({
            "bucket": bucket,
            "predictions": len(rows),
            "mean_predicted_probability": round(
                sum(x["probability"] for x in rows) / len(rows), 6
            ),
            "observed_yes_rate": round(
                sum(x["outcome"] for x in rows) / len(rows), 6
            ),
            "brier_score": round(
                sum(x["brier_score"] for x in rows) / len(rows), 8
            ),
            "log_loss": round(
                sum(x["log_loss"] for x in rows) / len(rows), 8
            ),
        })

    overall = {
        "predictions": len(resolved),
        "brier_score": (
            round(sum(x["brier_score"] for x in resolved) / len(resolved), 8)
            if resolved else None
        ),
        "log_loss": (
            round(sum(x["log_loss"] for x in resolved) / len(resolved), 8)
            if resolved else None
        ),
    }
    return {"overall": overall, "calibration": calibration}
