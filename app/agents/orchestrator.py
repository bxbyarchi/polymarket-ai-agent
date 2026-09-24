from __future__ import annotations

from typing import Any

from app.agents.analyst import Analyst
from app.agents.critic import Critic


class ResearchOrchestrator:
    def __init__(self, analyst: Analyst | None = None, critic: Critic | None = None) -> None:
        self.analyst = analyst or Analyst()
        self.critic = critic or Critic()

    async def run(self, market: dict[str, Any]) -> dict[str, Any]:
        analysis = await self.analyst.analyze(market)
        review = await self.critic.review(market, analysis)

        final_probability = self._combine_probability(analysis, review)
        market_probability = analysis.get("market_probability")
        edge = (
            final_probability - market_probability
            if final_probability is not None and market_probability is not None
            else None
        )

        return {
            **analysis,
            "probability": final_probability,
            "edge": edge,
            "review": review,
            "pipeline": "analyst+critic",
        }

    @staticmethod
    def _combine_probability(analysis: dict[str, Any], review: dict[str, Any]) -> float | None:
        analyst_probability = analysis.get("probability")
        review_probability = review.get("review_probability")
        if analyst_probability is None:
            return review_probability
        if review_probability is None:
            return analyst_probability
        return round((float(analyst_probability) + float(review_probability)) / 2, 6)
