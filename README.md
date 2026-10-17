# Citation Atlas

Explore the citation graph around any academic paper. Search the
[OpenAlex](https://openalex.org) index (over 320 million works as of October
2026, per the live API count), get results ranked by relevance plus citation
influence, then expand any paper into an interactive graph of the work it
builds on and the work that builds on it.

Built as an original work sample for a Product Engineer application. The
stack mirrors the target product area (research / literature tooling):
**Python + FastAPI** backend, **Next.js + React + TypeScript** frontend.

![Ranked search results](docs/search-results.png)
![Citation graph](docs/citation-graph.png)

## What it does

- **Ranked paper search** - `GET /api/search?q=...` combines OpenAlex's text
  relevance score with a log-scaled citation boost, so directly relevant
  papers win and influential papers break ties. Formula:
  `rank = relevance + 2.0 * log10(1 + citations)`.
- **Citation graph** - `GET /api/works/{id}/graph` returns the paper's
  most-cited references (blue, left) and most-cited citing papers (green,
  right) as a node-link diagram. Every edge is a real citation link reported
  by OpenAlex. Click any node to re-center the graph on that paper.
- **Live public data, no keys or signup** - OpenAlex is free to use and this
  app needs no API key or account. We send a `mailto` contact (polite pool)
  and cache responses on disk so repeat runs don't re-hit the API.

## Run it

Backend (Python 3.10+):

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --port 8000
```

Frontend (Node 18+), in a second terminal:

```bash
cd frontend
npm install
npm run build && npm run start   # or: npm run dev
```

Open http://localhost:3000. The frontend proxies `/api/*` to the backend on
port 8000 (see `frontend/next.config.mjs`).

## Tests

```bash
cd backend
python3 -m pytest -q     # 15 tests
```

Tests run offline against `backend/tests/fixtures/` - verbatim OpenAlex API
responses recorded on 2026-10-17, not hand-written data. They cover the
ranking math, OpenAlex response normalization, graph structure and edge
direction, API validation and 404s, and the disk cache.

## Layout

```
backend/app/openalex.py   async OpenAlex client (polite-pool mailto, disk cache)
backend/app/ranking.py    relevance + log-citation ranking
backend/app/graph.py      citation graph assembly (dedupes nodes, labels edge direction)
backend/app/main.py       FastAPI endpoints
frontend/app/page.tsx     search + results UI
frontend/app/components/GraphView.tsx   SVG citation graph
```

## Honest limits

- The graph shows one hop around a paper (its references and citing works),
  not a transitive crawl.
- "Most-cited references" samples from the first 100 reference ids OpenAlex
  lists for a paper; for papers with very large reference lists this is a
  sample, not an exhaustive ranking.
- OpenAlex citation counts drift over time as their index updates, and
  titles/metadata are rendered as-is from their API; their index occasionally
  contains erroneous records (this tool does not editorialize source data).
