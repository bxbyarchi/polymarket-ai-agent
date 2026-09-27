from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


class MarketScorer:
    """Ranks markets for research priority; it does not place trades."""

    def score(self, market: dict[str, Any]) -> float:
        liquidity = max(0.0, float(market.get("liquidity") or 0.0))
        volume_24h = max(0.0, float(market.get("volume_24h") or 0.0))
        volume = max(0.0, float(market.get("volume") or 0.0))

        liquidity_component = min(1.0, liquidity / 100_000.0)
        volume_24h_component = min(1.0, volume_24h / 50_000.0)
        volume_component = min(1.0, volume / 1_000_000.0)

        freshness = self._freshness_score(market.get("end_date"))
        category = self._category_score(market)
        return round(
            0.25 * liquidity_component
            + 0.25 * volume_24h_component
            + 0.10 * volume_component
            + 0.30 * freshness
            + 0.10 * category,
            4,
        )

    @staticmethod
    def _category_score(market: dict[str, Any]) -> float:
        text = " ".join(
            str(market.get(key) or "")
            for key in ("question", "slug", "description")
        ).lower()
        words = (
            "election", "president", "prime minister", "senate", "congress",
            "vote", "politic", "trump", "fed", "interest rate", "inflation",
            "cpi", "stock", "bitcoin", "btc", "ethereum", "eth", "finance",
            "nba", "nfl", "mlb", "nhl", "ufc", "football", "soccer", "tennis",
            "match", "game", "sport",
        )
        return 1.0 if any(word in text for word in words) else 0.0

    @staticmethod
    def _freshness_score(end_date: Any) -> float:
        if not end_date:
            return 0.0
        try:
            raw = str(end_date).replace("Z", "+00:00")
            end = datetime.fromisoformat(raw)
            if end.tzinfo is None:
                end = end.replace(tzinfo=timezone.utc)
            days = (end - datetime.now(timezone.utc)).total_seconds() / 86400
        except ValueError:
            return 0.0

        if days <= 0:
            return 0.0
        if days <= 1:
            return 1.0
        if days <= 7:
            return 0.8
        if days <= 30:
            return 0.5
        return 0.2
