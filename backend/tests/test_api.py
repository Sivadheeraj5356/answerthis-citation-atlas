import httpx
import pytest
from fastapi.testclient import TestClient

from app import main
from app.openalex import OpenAlexClient
from tests.conftest import ROOT_ID, fixture_transport


@pytest.fixture
def api(mock_transport):
    main.client = OpenAlexClient(transport=mock_transport, cache_dir=None)
    with TestClient(main.app) as test_client:
        yield test_client


def test_health(api):
    assert api.get("/api/health").json() == {"status": "ok"}


def test_search_returns_ranked_results(api):
    data = api.get("/api/search", params={"q": "retrieval augmented generation"}).json()
    assert data["count"] == 10
    scores = [r["rank_score"] for r in data["results"]]
    assert scores == sorted(scores, reverse=True)


def test_search_result_fields(api):
    data = api.get("/api/search", params={"q": "retrieval augmented generation"}).json()
    for r in data["results"]:
        assert r["id"].startswith("W")
        assert r["title"]
        assert isinstance(r["cited_by_count"], int)
        assert r["url"]


def test_search_requires_query(api):
    assert api.get("/api/search").status_code == 422
    assert api.get("/api/search", params={"q": "x"}).status_code == 422


def test_graph_structure(api):
    data = api.get(f"/api/works/{ROOT_ID}/graph").json()
    assert data["root_id"] == ROOT_ID
    assert data["node_count"] == len(data["nodes"])
    assert data["edge_count"] == len(data["edges"])
    node_ids = {n["id"] for n in data["nodes"]}
    assert ROOT_ID in node_ids
    for edge in data["edges"]:
        assert edge["source"] in node_ids
        assert edge["target"] in node_ids


def test_graph_edge_directions(api):
    data = api.get(f"/api/works/{ROOT_ID}/graph").json()
    kinds = {n["id"]: n["kinds"] for n in data["nodes"]}
    for edge in data["edges"]:
        if edge["source"] == ROOT_ID:
            assert "reference" in kinds[edge["target"]]
        else:
            assert edge["target"] == ROOT_ID
            assert "citing" in kinds[edge["source"]]


def test_graph_unknown_work_returns_404(api):
    assert api.get("/api/works/W9999999999/graph").status_code == 404


def test_graph_references_are_most_cited(api):
    data = api.get(f"/api/works/{ROOT_ID}/graph").json()
    ref_counts = [
        n["cited_by_count"] for n in data["nodes"] if "reference" in n["kinds"]
    ]
    assert ref_counts == sorted(ref_counts, reverse=True)
