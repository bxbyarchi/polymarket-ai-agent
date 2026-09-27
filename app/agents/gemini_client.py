from __future__ import annotations

import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)

_TRANSIENT_MARKERS = ("429", "500", "502", "503", "504", "UNAVAILABLE", "RESOURCE_EXHAUSTED")


async def generate_with_resilience(
    client: Any,
    *,
    model: str,
    fallback_model: str | None,
    contents: Any,
    config: Any,
    retries: int = 2,
) -> Any:
    models: list[str] = [model]
    if fallback_model and fallback_model != model:
        models.append(fallback_model)

    last_error: Exception | None = None

    for index, candidate in enumerate(models):
        attempts = retries + 1
        for attempt in range(attempts):
            try:
                return await client.aio.models.generate_content(
                    model=candidate,
                    contents=contents,
                    config=config,
                )
            except Exception as exc:
                last_error = exc
                if not _is_transient(exc) or attempt >= retries:
                    break

                delay = 2 ** attempt
                logger.warning(
                    "Gemini transient error on model %s (attempt %s/%s); retrying in %ss",
                    candidate,
                    attempt + 1,
                    attempts,
                    delay,
                )
                await asyncio.sleep(delay)

        if index < len(models) - 1:
            logger.warning(
                "Gemini model %s unavailable after retries; falling back to %s",
                candidate,
                models[index + 1],
            )

    assert last_error is not None
    raise last_error


def _is_transient(exc: Exception) -> bool:
    message = str(exc).upper()
    return any(marker in message for marker in _TRANSIENT_MARKERS)
