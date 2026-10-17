"""Test fixtures: real OpenAlex API responses recorded 2026-10-17.

Nothing here is hand-written data - each file is the verbatim JSON body
returned by https://api.openalex.org for the request described in
FIXTURE_ROUTES, saved so tests run offline and deterministically.
"""
import json
from pathlib import Path

import httpx
import pytest

FIXTURES = Path(__file__).parent / "fixtures"
ROOT_ID = "W4389519118"  # "Active Retrieval Augmented Generation" (FLARE)


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


def fixture_transport() -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        params = request.url.params
        if path == "/works" and "search" in params:
            return httpx.Response(200, json=_load("search_rag.json"))
        if path == f"/works/{ROOT_ID}":
            return httpx.Response(200, json=_load(f"work_{ROOT_ID}.json"))
        if path == "/works" and params.get("filter", "").startswith("ids.openalex:"):
            return httpx.Response(200, json=_load(f"refs_{ROOT_ID}.json"))
        if path == "/works" and params.get("filter", "").startswith("cites:"):
            return httpx.Response(200, json=_load(f"citing_{ROOT_ID}.json"))
        if path.startswith("/works/"):
            return httpx.Response(404, json={"error": "not found"})
        return httpx.Response(500, json={"error": f"unstubbed request: {path}?{params}"})

    return httpx.MockTransport(handler)


@pytest.fixture
def mock_transport() -> httpx.MockTransport:
    return fixture_transport()
