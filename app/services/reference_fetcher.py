from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urlparse

import httpx

from app.config import get_settings


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.title = ""
        self.description = ""
        self._skip_depth = 0
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in {"script", "style", "noscript", "svg", "canvas"}:
            self._skip_depth += 1
            return
        if tag == "title":
            self._in_title = True
        if tag == "meta":
            attrs_map = {str(k).lower(): str(v or "") for k, v in attrs}
            name = attrs_map.get("name", "").lower()
            if name in {"description", "og:description"}:
                self.description = attrs_map.get("content", "")[:2000]

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"script", "style", "noscript", "svg", "canvas"} and self._skip_depth:
            self._skip_depth -= 1
        elif tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        value = re.sub(r"\s+", " ", data).strip()
        if not value:
            return
        if self._in_title:
            self.title = f"{self.title} {value}".strip()
        self.parts.append(value)


class ReferenceFetcher:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def fetch(self, source_url: str) -> dict[str, Any]:
        parsed = urlparse(source_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("Reference URL must be a valid http(s) URL")

        host = parsed.netloc.lower()
        path_parts = [part for part in parsed.path.split("/") if part]
        if host.endswith("polymarket.com") and path_parts:
            if path_parts[0] == "event" and len(path_parts) >= 2:
                return await self._fetch_gamma_event(path_parts[1], source_url)
            if path_parts[0] == "market" and len(path_parts) >= 2:
                return await self._fetch_gamma_market(path_parts[1], source_url)

        headers = {
            "User-Agent": "Polymarket-AI-Research-Agent/0.5",
            "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
        }
        timeout = httpx.Timeout(self.settings.request_timeout_seconds)
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, headers=headers) as client:
            response = await client.get(source_url)
            response.raise_for_status()
            content_type = response.headers.get("content-type", "").lower()
            body = response.text[:2_000_000]

        if "json" in content_type or body.lstrip().startswith(("{", "[")):
            try:
                payload = json.loads(body)
                return {
                    "source_url": source_url,
                    "final_url": str(response.url),
                    "title": "JSON reference",
                    "description": "",
                    "text": json.dumps(payload, ensure_ascii=False, indent=2)[:20_000],
                    "method": "http-json",
                }
            except json.JSONDecodeError:
                pass

        parser = _TextExtractor()
        parser.feed(body)
        return {
            "source_url": source_url,
            "final_url": str(response.url),
            "title": parser.title[:500],
            "description": parser.description,
            "text": "\n".join(parser.parts)[:20_000],
            "method": "http-html",
        }

    async def _fetch_gamma_event(self, slug: str, source_url: str) -> dict[str, Any]:
        url = f"{self.settings.gamma_api_url.rstrip('/')}/events/slug/{slug}"
        timeout = httpx.Timeout(self.settings.request_timeout_seconds)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url)
            response.raise_for_status()
            event = response.json()

        return {
            "source_url": source_url,
            "final_url": source_url,
            "title": event.get("title") or event.get("question") or slug,
            "description": event.get("description") or "",
            "text": json.dumps(
                {
                    "event": {
                        "id": event.get("id"),
                        "title": event.get("title"),
                        "question": event.get("question"),
                        "description": event.get("description"),
                        "startDate": event.get("startDate"),
                        "endDate": event.get("endDate"),
                        "resolutionSource": event.get("resolutionSource"),
                        "tags": event.get("tags"),
                    },
                    "markets": event.get("markets") or [],
                },
                ensure_ascii=False,
                indent=2,
            )[:30_000],
            "method": "polymarket-gamma-event",
        }

    async def _fetch_gamma_market(self, slug: str, source_url: str) -> dict[str, Any]:
        url = f"{self.settings.gamma_api_url.rstrip('/')}/markets/slug/{slug}"
        timeout = httpx.Timeout(self.settings.request_timeout_seconds)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url)
            response.raise_for_status()
            market = response.json()

        return {
            "source_url": source_url,
            "final_url": source_url,
            "title": market.get("question") or slug,
            "description": market.get("description") or "",
            "text": json.dumps(market, ensure_ascii=False, indent=2)[:30_000],
            "method": "polymarket-gamma-market",
        }
