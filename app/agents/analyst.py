from __future__ import annotations

import json
from typing import Any

from openai import AsyncOpenAI

from app.config import get_settings


SYSTEM_PROMPT = """You are a neutral prediction-market research analyst.

Estimate the probability that the specified Polymarket YES outcome will resolve YES.

Rules:
- Research the exact question and resolution criteria using current web information.
- Prefer primary/official sources, then high-quality reporting and data.
- Distinguish facts, assumptions, and uncertainty.
- Do not treat the current Polymarket price as truth; it is only the market reference.
- Consider base rates, recent evidence, counterevidence, timing, and ambiguity.
- Never invent facts or sources.
- Return ONLY valid JSON matching the requested fields.
"""


class Analyst:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.client: AsyncOpenAI | None = None

    def _client(self) -> AsyncOpenAI:
        if not self.settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured")
        if self.client is None:
            self.client = AsyncOpenAI(api_key=self.settings.openai_api_key)
        return self.client

    async def analyze(self, market: dict[str, Any]) -> dict[str, Any]:
        prices = market.get("outcomePrices") or market.get("outcome_prices") or []
        market_probability = self._first_float(prices)

        prompt = f"""Analyze this Polymarket market.

Question: {market.get("question")}
Market ID: {market.get("id")}
Slug: {market.get("slug")}
Start date: {market.get("startDate") or market.get("start_date")}
End date: {market.get("endDate") or market.get("end_date")}
Resolution source: {market.get("resolutionSource")}
Description: {market.get("description")}
Outcomes: {market.get("outcomes")}
Current outcome prices: {prices}
Current YES market probability: {market_probability}

Research the exact event and resolution criteria with web search.

Return JSON with exactly:
{{
  "probability": 0.0,
  "confidence": 0.0,
  "summary": "short evidence-based explanation",
  "key_factors": ["factor"],
  "counter_factors": ["counter-factor"],
  "sources": [{{"title": "source title", "url": "https://..."}}],
  "as_of": "ISO-8601 timestamp"
}}

probability and confidence must be decimals from 0 to 1.
"""

        response = await self._client().responses.create(
            model=self.settings.openai_model,
            instructions=SYSTEM_PROMPT,
            tools=[{"type": "web_search"}],
            input=prompt,
            max_output_tokens=self.settings.ai_max_output_tokens,
        )

        result = self._parse_json(response.output_text)
        probability = self._clamp(result.get("probability"))
        confidence = self._clamp(result.get("confidence"))

        result["probability"] = probability
        result["confidence"] = confidence
        result["market_probability"] = market_probability
        result["edge"] = (
            probability - market_probability
            if probability is not None and market_probability is not None
            else None
        )
        return result

    @staticmethod
    def _first_float(values: Any) -> float | None:
        if not isinstance(values, list) or not values:
            return None
        try:
            return float(values[0])
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _clamp(value: Any) -> float | None:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None
        return max(0.0, min(1.0, number))

    @staticmethod
    def _parse_json(raw: str) -> dict[str, Any]:
        cleaned = raw.strip()
        if cleaned.startswith("~~~"):
            lines = cleaned.splitlines()
            lines = lines[1:] if lines and lines[0].startswith("~~~") else lines
            lines = lines[:-1] if lines and lines[-1].strip() == "~~~" else lines
            cleaned = "\n".join(lines).strip()

        try:
            result = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Model returned invalid JSON: {raw}") from exc

        if not isinstance(result, dict):
            raise RuntimeError("Model returned JSON that is not an object")
        return result
