from __future__ import annotations

import json
from typing import Any

from openai import AsyncOpenAI

from app.config import get_settings


SYSTEM_PROMPT = """You are a skeptical second-pass reviewer for prediction-market research.

Review the analyst's proposed probability and evidence. Check:
- whether the market question and resolution criteria were interpreted correctly;
- whether important evidence is missing or weak;
- whether sources actually support the stated factors;
- whether the probability is internally consistent with the evidence;
- whether uncertainty is adequately reflected.

Do not blindly agree with the analyst. Return only valid JSON.
"""


class Critic:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.client: AsyncOpenAI | None = None

    def _client(self) -> AsyncOpenAI:
        if not self.settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured")
        if self.client is None:
            self.client = AsyncOpenAI(api_key=self.settings.openai_api_key)
        return self.client

    async def review(self, market: dict[str, Any], analysis: dict[str, Any]) -> dict[str, Any]:
        prompt = f"""Review this prediction-market analysis.

MARKET:
Question: {market.get("question")}
Description: {market.get("description")}
Resolution source: {market.get("resolutionSource") or market.get("resolution_source")}
End date: {market.get("endDate") or market.get("end_date")}

ANALYST:
{json.dumps(analysis, ensure_ascii=False)}

Return exactly:
{{
  "approved": true,
  "review_probability": 0.0,
  "confidence": 0.0,
  "issues": ["specific issue"],
  "missing_evidence": ["specific missing evidence"],
  "reasoning": "short review",
  "sources_to_verify": [{{"title": "source title", "url": "https://..."}}]
}}

review_probability and confidence must be between 0 and 1.
"""

        response = await self._client().responses.create(
            model=self.settings.openai_model,
            instructions=SYSTEM_PROMPT,
            tools=[{"type": "web_search"}],
            input=prompt,
            max_output_tokens=self.settings.ai_max_output_tokens,
        )
        result = self._parse_json(response.output_text)
        result["review_probability"] = self._clamp(result.get("review_probability"))
        result["confidence"] = self._clamp(result.get("confidence"))
        result["approved"] = bool(result.get("approved"))
        return result

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
        result = json.loads(cleaned)
        if not isinstance(result, dict):
            raise RuntimeError("Critic returned JSON that is not an object")
        return result
