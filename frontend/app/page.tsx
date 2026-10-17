"use client";

import { useState } from "react";
import GraphView, { Graph } from "./components/GraphView";

type SearchResult = {
  id: string;
  title: string;
  year: number | null;
  authors: string[];
  cited_by_count: number;
  url: string | null;
  rank_score: number;
};

type Node = Graph["nodes"][number];

export default function Home() {
  const [query, setQuery] = useState("retrieval augmented generation");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [graph, setGraph] = useState<Graph | null>(null);
  const [selected, setSelected] = useState<Node | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searched, setSearched] = useState(false);

  async function runSearch(e?: React.FormEvent) {
    e?.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    setGraph(null);
    setSelected(null);
    try {
      const res = await fetch(`/api/search?q=${encodeURIComponent(query)}&limit=10`);
      if (!res.ok) throw new Error(`search failed (HTTP ${res.status})`);
      const data = await res.json();
      setResults(data.results);
      setSearched(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "search failed");
    } finally {
      setLoading(false);
    }
  }

  async function loadGraph(id: string) {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/works/${id}/graph?refs=8&citing=8`);
      if (!res.ok) throw new Error(`graph failed (HTTP ${res.status})`);
      const data: Graph = await res.json();
      setGraph(data);
      setSelected(data.nodes.find((n) => n.id === data.root_id) ?? null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "graph failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="container">
      <h1>Citation Atlas</h1>
      <p className="subtitle">
        Search the OpenAlex index (over 320 million works), then explore the citation graph around any result.
        Node size = citation count (log scale). Click a node to re-center the graph on that paper.
      </p>
      <form className="searchbar" onSubmit={runSearch}>
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search papers, e.g. retrieval augmented generation"
          aria-label="search papers"
        />
        <button type="submit" disabled={loading}>
          {loading ? "Loading…" : "Search"}
        </button>
      </form>
      {error && <p className="error">{error}</p>}
      {searched && results.length === 0 && !loading && <p className="empty">No results.</p>}
      <div className="results">
        {results.map((r, i) => (
          <button
            key={r.id}
            className={`card${graph?.root_id === r.id ? " active" : ""}`}
            onClick={() => loadGraph(r.id)}
          >
            <p className="card-title">
              {i + 1}. {r.title}
            </p>
            <div className="card-meta">
              <span>{r.year ?? "n.d."}</span>
              <span>{r.authors.slice(0, 3).join(", ")}{r.authors.length > 3 ? " et al." : ""}</span>
              <span>{r.cited_by_count.toLocaleString()} citations</span>
              <span className="badge">rank {r.rank_score.toFixed(1)}</span>
            </div>
          </button>
        ))}
      </div>
      {graph && (
        <section className="graph-panel">
          <h2>{graph.nodes.find((n) => n.id === graph.root_id)?.title}</h2>
          <div className="legend">
            <span><span className="dot" style={{ background: "#f5a524" }} />Selected paper</span>
            <span><span className="dot" style={{ background: "#38bdf8" }} />References (it cites)</span>
            <span><span className="dot" style={{ background: "#34d399" }} />Citing papers (cite it)</span>
          </div>
          <GraphView graph={graph} onSelect={setSelected} onFocus={loadGraph} />
          {selected && (
            <div className="detail">
              <strong>{selected.title}</strong>
              {selected.authors.join(", ")} {selected.year ? `- ${selected.year}` : ""} -{" "}
              {selected.cited_by_count.toLocaleString()} citations
              {selected.url && (
                <>
                  {" "}- <a href={selected.url} target="_blank" rel="noreferrer">view paper</a>
                </>
              )}
            </div>
          )}
        </section>
      )}
    </main>
  );
}
