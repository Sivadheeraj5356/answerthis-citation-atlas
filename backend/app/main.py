"""Citation Atlas - FastAPI backend.

Explore the citation graph around any paper indexed by OpenAlex:
  GET /api/health
  GET /api/search?q=...&limit=10        -> papers ranked by relevance + citations
  GET /api/works/{id}/graph?refs=8&citing=8 -> citation neighbourhood of a paper
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query

from .graph import build_graph
from .openalex import OpenAlexClient, OpenAlexError
from .ranking import rank_results

client = OpenAlexClient()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await client.aclose()


app = FastAPI(title="Citation Atlas", version="0.1.0", lifespan=lifespan)


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/api/search")
async def search(
    q: str = Query(..., min_length=2, max_length=200),
    limit: int = Query(10, ge=1, le=25),
) -> dict:
    try:
        results = await client.search_works(q, limit)
    except OpenAlexError as exc:
        raise HTTPException(status_code=502, detail=f"OpenAlex error: {exc}")
    return {"query": q, "count": len(results), "results": rank_results(results)}


@app.get("/api/works/{work_id}/graph")
async def graph(
    work_id: str,
    refs: int = Query(8, ge=0, le=25),
    citing: int = Query(8, ge=0, le=25),
) -> dict:
    try:
        root = await client.get_work(work_id)
        # OpenAlex does not order referenced_works, so batch-fetch a wider
        # slice and keep the most-cited references.
        references = []
        if refs > 0 and root["referenced_ids"]:
            pool = await client.get_works_by_ids(root["referenced_ids"][: min(refs * 2, 50)])
            references = sorted(pool, key=lambda w: w["cited_by_count"], reverse=True)[:refs]
        citing_works = await client.get_citing_works(work_id, citing)
    except OpenAlexError as exc:
        if "not found" in str(exc):
            raise HTTPException(status_code=404, detail=f"work {work_id} not found")
        raise HTTPException(status_code=502, detail=f"OpenAlex error: {exc}")
    return build_graph(root, references, citing_works)
