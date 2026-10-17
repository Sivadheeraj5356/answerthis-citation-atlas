"""Async client for the OpenAlex API (https://docs.openalex.org).

OpenAlex is free and requires no API key. We send a `mailto` parameter to
join the polite pool and cache every response on disk so repeated demo runs
and CI tests do not re-hit the API.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

import httpx

BASE_URL = "https://api.openalex.org"
MAILTO = os.environ.get("CITATION_ATLAS_MAILTO", "sivadheeraj5356@gmail.com")
CACHE_DIR = Path(os.environ.get("CITATION_ATLAS_CACHE_DIR", ".cache/openalex"))

WORK_FIELDS = (
    "id,display_name,publication_year,cited_by_count,authorships,doi,"
    "primary_location,relevance_score,referenced_works"
)


class OpenAlexError(Exception):
    """Raised when OpenAlex returns an error or an unexpected payload."""


class OpenAlexClient:
    def __init__(
        self,
        transport: httpx.AsyncBaseTransport | None = None,
        cache_dir: Path | None = CACHE_DIR,
        timeout: float = 20.0,
    ) -> None:
        self._client = httpx.AsyncClient(
            base_url=BASE_URL,
            transport=transport,
            timeout=timeout,
            headers={"User-Agent": f"citation-atlas/0.1 (mailto:{MAILTO})"},
        )
        self._cache_dir = cache_dir
        if cache_dir:
            cache_dir.mkdir(parents=True, exist_ok=True)

    async def aclose(self) -> None:
        await self._client.aclose()

    # -- HTTP + cache ------------------------------------------------------

    def _cache_path(self, path: str, params: dict[str, Any]) -> Path:
        key = hashlib.sha256(f"{path}?{sorted(params.items())}".encode()).hexdigest()
        return self._cache_dir / f"{key}.json"  # type: ignore[operator]

    async def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        params = {**params, "mailto": MAILTO}
        cache_file = self._cache_path(path, params) if self._cache_dir else None
        if cache_file and cache_file.exists():
            return json.loads(cache_file.read_text())
        resp = await self._client.get(path, params=params)
        if resp.status_code == 404:
            raise OpenAlexError("not found")
        if resp.status_code != 200:
            raise OpenAlexError(f"OpenAlex returned HTTP {resp.status_code}")
        data = resp.json()
        if cache_file:
            cache_file.write_text(json.dumps(data))
        return data

    # -- Public API --------------------------------------------------------

    async def search_works(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        data = await self._get(
            "/works",
            {"search": query, "per-page": str(limit), "select": WORK_FIELDS},
        )
        return [normalize_work(w) for w in data.get("results", [])]

    async def get_work(self, work_id: str) -> dict[str, Any]:
        data = await self._get(f"/works/{work_id}", {"select": WORK_FIELDS})
        return normalize_work(data)

    async def get_works_by_ids(self, work_ids: list[str]) -> list[dict[str, Any]]:
        """Batch-fetch works by OpenAlex ids (short form, e.g. 'W123')."""
        if not work_ids:
            return []
        data = await self._get(
            "/works",
            {
                "filter": "ids.openalex:" + "|".join(work_ids[:50]),
                "per-page": "50",
                "select": WORK_FIELDS,
            },
        )
        return [normalize_work(w) for w in data.get("results", [])]

    async def get_citing_works(self, work_id: str, limit: int = 8) -> list[dict[str, Any]]:
        data = await self._get(
            "/works",
            {
                "filter": f"cites:{work_id}",
                "sort": "cited_by_count:desc",
                "per-page": str(limit),
                "select": WORK_FIELDS,
            },
        )
        return [normalize_work(w) for w in data.get("results", [])]


# -- Normalization ---------------------------------------------------------


def short_id(openalex_url: str) -> str:
    """'https://openalex.org/W123' -> 'W123'."""
    return openalex_url.rstrip("/").rsplit("/", 1)[-1]


def normalize_work(raw: dict[str, Any]) -> dict[str, Any]:
    """Flatten an OpenAlex work record into the shape the API returns."""
    primary = raw.get("primary_location") or {}
    return {
        "id": short_id(raw.get("id", "")),
        "title": raw.get("display_name") or "(untitled)",
        "year": raw.get("publication_year"),
        "cited_by_count": raw.get("cited_by_count") or 0,
        "authors": [
            a.get("author", {}).get("display_name", "")
            for a in (raw.get("authorships") or [])[:6]
        ],
        "doi": raw.get("doi"),
        "url": primary.get("landing_page_url") or raw.get("id"),
        "relevance_score": raw.get("relevance_score"),
        "referenced_ids": [short_id(r) for r in (raw.get("referenced_works") or [])],
    }
