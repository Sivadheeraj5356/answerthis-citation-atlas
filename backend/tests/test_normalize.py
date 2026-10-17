import json
from pathlib import Path

from app.openalex import normalize_work, short_id

FIXTURES = Path(__file__).parent / "fixtures"


def test_short_id():
    assert short_id("https://openalex.org/W4389519118") == "W4389519118"
    assert short_id("W4389519118") == "W4389519118"


def test_normalize_work_flattens_openalex_record():
    raw = json.loads((FIXTURES / "work_W4389519118.json").read_text())
    work = normalize_work(raw)
    assert work["id"] == "W4389519118"
    assert work["title"] == "Active Retrieval Augmented Generation"
    assert work["year"] == 2023
    assert work["cited_by_count"] == raw["cited_by_count"]
    assert len(work["authors"]) >= 1
    assert work["url"]
    assert len(work["referenced_ids"]) == len(raw["referenced_works"])
