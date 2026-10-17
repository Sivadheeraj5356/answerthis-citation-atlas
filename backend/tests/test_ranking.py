from app.ranking import rank_results, rank_score


def test_rank_score_relevance_dominates():
    # A clearly more relevant paper beats a barely-relevant highly-cited one.
    assert rank_score(50.0, 10) > rank_score(10.0, 10000)


def test_rank_score_citation_boost_breaks_ties():
    assert rank_score(30.0, 500) > rank_score(30.0, 5)


def test_rank_score_handles_missing_values():
    assert rank_score(None, None) == 0.0
    assert rank_score(12.5, None) == 12.5


def test_rank_results_sorted_and_annotated():
    results = [
        {"id": "A", "relevance_score": 10.0, "cited_by_count": 0},
        {"id": "B", "relevance_score": 20.0, "cited_by_count": 3},
        {"id": "C", "relevance_score": 10.0, "cited_by_count": 1000},
    ]
    ranked = rank_results(results)
    assert [r["id"] for r in ranked] == ["B", "C", "A"]
    assert all("rank_score" in r for r in ranked)
    scores = [r["rank_score"] for r in ranked]
    assert scores == sorted(scores, reverse=True)
