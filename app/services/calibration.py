from __future__ import annotations

import math
from typing import Any


def resolved_outcome(market: dict[str, Any]) -> int | None:
    if market.get("closed") is not True:
        return None
    prices = market.get("outcomePrices") or market.get("outcome_prices") or []
    if not isinstance(prices, list) or not prices:
        return None
    try:
        yes = float(prices[0])
    except (TypeError, ValueError):
        return None
    if yes >= 0.99:
        return 1
    if yes <= 0.01:
        return 0
    return None


def score_prediction(probability: float, outcome: int) -> dict[str, float]:
    p = max(1e-6, min(1 - 1e-6, float(probability)))
    y = int(outcome)
    return {"brier_score": round((p - y) ** 2, 8), "log_loss": round(-(y * math.log(p) + (1 - y) * math.log(1 - p)), 8)}


def summarize(scores: list[dict[str, float]]) -> dict[str, Any]:
    if not scores:
        return {"resolved_predictions": 0, "brier_score": None, "log_loss": None}
    return {"resolved_predictions": len(scores), "brier_score": round(sum(x["brier_score"] for x in scores) / len(scores), 8), "log_loss": round(sum(x["log_loss"] for x in scores) / len(scores), 8)}
