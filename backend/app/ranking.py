"""Search ranking for related papers.

OpenAlex returns a `relevance_score` per hit (text match quality). We keep
relevance as the dominant signal and add a small log-scaled citation boost
so that, among papers of similar relevance, the more influential ones rank
higher. Log scaling keeps mega-cited classics from drowning out recent,
directly relevant work.
"""
from __future__ import annotations

import math

CITATION_WEIGHT = 2.0


def rank_score(relevance_score: float | None, cited_by_count: int | None) -> float:
    rel = relevance_score or 0.0
    boost = CITATION_WEIGHT * math.log10(1 + max(0, cited_by_count or 0))
    return round(rel + boost, 4)


def rank_results(results: list[dict]) -> list[dict]:
    """Attach rank_score to each result and sort by it, descending."""
    for r in results:
        r["rank_score"] = rank_score(r.get("relevance_score"), r.get("cited_by_count"))
    return sorted(results, key=lambda r: (r["rank_score"], r["cited_by_count"]), reverse=True)
