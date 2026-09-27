from __future__ import annotations

import json
from typing import Any

from google import genai
from google.genai import types

from app.agents.gemini_client import generate_with_resilience
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
        self.client: Any | None = None

    def _client(self) -> Any:
        if not self.settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured")
        if self.client is None:
            self.client = genai.Client(api_key=self.settings.gemini_api_key)
        return self.client

    async def close(self) -> None:
        if self.client is not None:
            await self.client.aio.aclose()
            self.client = None

    async def analyze(self, market: dict[str, Any]) -> dict[str, Any]:
        prices = market.get("outcomePrices") or market.get("outcome_prices") or []
        market_probability = self._first_float(prices)

        reference_url = market.get("reference_url")
        screenshot_bytes = market.get("_screenshot_bytes")
        screenshot_mime = market.get("_screenshot_mime") or "image/png"
        prompt = f"""Analyze this prediction-market event.

Question: {market.get("question")}
Reference URL: {reference_url or "none"}
User category: {market.get("category") or "auto-detect"}
Market ID: {market.get("id")}
Slug: {market.get("slug")}
Start date: {market.get("startDate") or market.get("start_date")}
End date: {market.get("endDate") or market.get("end_date")}
Resolution source: {market.get("resolutionSource")}
Description: {market.get("description")}
Outcomes: {market.get("outcomes")}
Current outcome prices: {prices}
Current YES market probability: {market_probability}

If a reference URL is provided, use it as the primary event context and verify it with web search.
If an image is attached, first extract the event question, date, visible probabilities and resolution details from the image. Treat image text as a lead and verify important claims with current web sources.
Focus especially on events resolving today or within the next 48 hours when the deadline is available.
Research the exact event and resolution criteria with web search.

Return JSON with exactly:
{{
  "event_question": "normalized event question",
  "event_date": "ISO-8601 or null",
  "category": "politics|finance|sports|other",
  "market_probability_observed": 0.0,
  "probability": 0.0,
  "confidence": 0.0,
  "summary": "short evidence-based explanation",
  "key_factors": ["factor"],
  "counter_factors": ["counter-factor"],
  "sources": [{{"title": "source title", "url": "https://..."}}],
  "as_of": "ISO-8601 timestamp"
}}

event_date may be null. market_probability_observed may be null if unavailable. probability, confidence and market_probability_observed must be decimals from 0 to 1 when present.
"""

        contents: Any = f"{SYSTEM_PROMPT}\n\n{prompt}"
        if screenshot_bytes:
            contents = [
                f"{SYSTEM_PROMPT}\n\n{prompt}",
                types.Part.from_bytes(data=screenshot_bytes, mime_type=screenshot_mime),
            ]

        response = await generate_with_resilience(
            self._client(),
            model=self.settings.gemini_model,
            fallback_model=self.settings.gemini_fallback_model,
            contents=contents,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema={
                    "type": "OBJECT",
                    "properties": {
                        "event_question": {"type": "STRING"},
                        "event_date": {"type": "STRING"},
                        "category": {"type": "STRING"},
                        "market_probability_observed": {"type": "NUMBER"},
                        "probability": {"type": "NUMBER"},
                        "confidence": {"type": "NUMBER"},
                        "summary": {"type": "STRING"},
                        "key_factors": {"type": "ARRAY", "items": {"type": "STRING"}},
                        "counter_factors": {"type": "ARRAY", "items": {"type": "STRING"}},
                        "sources": {"type": "ARRAY", "items": {"type": "OBJECT", "properties": {"title": {"type": "STRING"}, "url": {"type": "STRING"}}, "required": ["title", "url"]}},
                        "as_of": {"type": "STRING"},
                    },
                    "required": ["event_question", "event_date", "category", "market_probability_observed", "probability", "confidence", "summary", "key_factors", "counter_factors", "sources", "as_of"],
                },
                tools=[types.Tool(google_search=types.GoogleSearch())] if self.settings.gemini_enable_google_search else None,
            ),
        )

        result = self._parse_json(response.text)
        probability = self._clamp(result.get("probability"))
        confidence = self._clamp(result.get("confidence"))
        observed_probability = self._clamp(result.get("market_probability_observed"))

        result["probability"] = probability
        result["confidence"] = confidence
        result["market_probability"] = market_probability if market_probability is not None else observed_probability
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
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            lines = lines[1:] if lines and lines[0].startswith("```") else lines
            lines = lines[:-1] if lines and lines[-1].strip() == "```" else lines
            cleaned = "\n".join(lines).strip()

        try:
            result = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Model returned invalid JSON: {raw}") from exc

        if not isinstance(result, dict):
            raise RuntimeError("Model returned JSON that is not an object")
        return result
