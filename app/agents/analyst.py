from __future__ import annotations

import json
from typing import Any

from openai import OpenAI

from app.config import get_settings


SYSTEM_PROMPT = """You are a neutral prediction-market research analyst.

Your job is to estimate the probability that the specified Polymarket outcome will resolve YES.

Rules:
- Research the question using current web information before estimating.
- Prioritize primary/official sources, then high-quality reporting and data.
- Pay attention to the market's exact resolution wording and end date.
- Separate facts from assumptions.
- Do not treat the current Polymarket price as truth; it is a market reference point.
- Consider base rates, recent evidence, counterevidence, and uncertainty.
- Do not invent facts or sources.
- Return ONLY valid JSON with this schema:
{
  "probability": number,
  "confidence": number,
  "market_probability": number|null,
  "edge": number|null,
  "summary": string,
  "key_factors": [string],
  "counter_factors": [string],
  "sources": [{"title": string, "url": string}],
  "as_of": string
}
probability and market_probability are decimals from 0 to 1.
confidence is 0 to 1.
edge = probability - market_probability when market_probability is available.
"""


class Analyst:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = None

    def _client(self) -> OpenAI:
        if not self.settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured")
        if self.client is None:
            self.client = OpenAI(api_key=self.settings.openai_api_key)
        return self.client

    def analyze(self, market: dict[str, Any]) -> dict[str, Any]:
        prices = market.get("outcomePrices") or market.get("outcome_prices") or []
        market_probability = None
        if isinstance(prices, list) and prices:
            try:
                market_probability = float(prices[0])
            except (TypeError, ValueError):
                pass

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

Research the exact event and its resolution criteria. Use web search for fresh evidence.
Then estimate the YES probability as of now.
"""

        response = self._client().responses.create(
            model=self.settings.openai_model,
            instructions=SYSTEM_PROMPT,
            tools=[{"type": "web_search"}],
            input=prompt,
            max_output_tokens=self.settings.ai_max_output_tokens,
        )

        raw = response.output_text.strip()
        try:
            result = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Model returned non-JSON analysis: {raw}") from exc

        result["market_probability"] = market_probability
        if market_probability is not None and result.get("probability") is not None:
            result["edge"] = float(result["probability"]) - market_probability

        return result
