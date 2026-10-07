from __future__ import annotations

from typing import Any

from app.agents.analyst import Analyst
from app.agents.critic import Critic
from app.services.calibrator import calibrate_probability


class ResearchOrchestrator:
    def __init__(self, analyst: Analyst | None = None, critic: Critic | None = None) -> None:
        self.analyst = analyst or Analyst()
        self.critic = critic or Critic()

    async def close(self) -> None:
        await self.analyst.close()
        await self.critic.close()

    async def run(self, market: dict[str, Any], calibration: dict[str, Any] | None = None) -> dict[str, Any]:
        analysis = await self.analyst.analyze(market)
        review = await self.critic.review(market, analysis)

        final_probability = self._combine_probability(analysis, review)
        calibration_result = None
        if calibration is not None:
            calibration_result = calibrate_probability(final_probability, calibration)
            final_probability = calibration_result["calibrated_probability"]

        market_probability = analysis.get("market_probability")
        edge = (
            round(final_probability - market_probability, 6)
            if final_probability is not None and market_probability is not None
            else None
        )

        signal, signal_label, signal_reason = self._signal(final_probability, market_probability, analysis.get("confidence"), review.get("confidence"))
        return {
            **analysis,
            "probability": final_probability,
            "edge": edge,
            "review": review,
            "signal": signal,
            "signal_label": signal_label,
            "signal_reason": signal_reason,
            "pipeline": "analyst+critic+calibration" if calibration_result is not None else "analyst+critic",
            "calibration": calibration_result,
        }

    @staticmethod
    def _signal(
        probability: float | None,
        market_probability: float | None,
        analyst_confidence: float | None,
        critic_confidence: float | None,
    ) -> tuple[str, str, str]:
        """Turn model-vs-market disagreement into a simple, conservative UI signal."""
        if probability is None or market_probability is None:
            return ("NO_DATA", "НЕТ ДАННЫХ", "Недостаточно данных для сравнения AI с рынком.")
        edge = float(probability) - float(market_probability)
        confidences = [float(x) for x in (analyst_confidence, critic_confidence) if x is not None]
        confidence = sum(confidences) / len(confidences) if confidences else 0.0

        if confidence < 0.55 or abs(edge) < 0.03:
            return ("SKIP", "ПРОПУСК", "Преимущество AI слишком маленькое или уверенность недостаточна.")
        if edge >= 0.05 and confidence >= 0.65:
            return ("BUY_YES", "СТАВКА YES", f"AI оценивает YES на {edge * 100:.1f} п.п. выше рынка.")
        if edge <= -0.05 and confidence >= 0.65:
            return ("BUY_NO", "СТАВКА NO", f"AI оценивает YES на {abs(edge) * 100:.1f} п.п. ниже рынка.")
        if edge > 0:
            return ("WATCH_YES", "НАБЛЮДАТЬ YES", "Есть небольшой перевес в сторону YES, но он ниже сильного порога.")
        return ("WATCH_NO", "НАБЛЮДАТЬ NO", "Есть небольшой перевес в сторону NO, но он ниже сильного порога.")

    @staticmethod
    def _combine_probability(analysis: dict[str, Any], review: dict[str, Any]) -> float | None:
        analyst_probability = analysis.get("probability")
        review_probability = review.get("review_probability")
        if analyst_probability is None:
            return review_probability
        if review_probability is None:
            return analyst_probability
        return round((float(analyst_probability) + float(review_probability)) / 2, 6)
