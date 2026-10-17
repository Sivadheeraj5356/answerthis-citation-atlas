"""Build a citation graph around one paper.

Nodes: the root paper, its most-cited references (papers it builds on) and
its most-cited citing papers (papers that build on it).
Edges: every edge is a real citation link reported by OpenAlex - root->ref
(root cites ref) or citing->root (citing cites root). If a paper is both a
reference and a citing work it appears once with both edges.
"""
from __future__ import annotations


def build_graph(
    root: dict,
    references: list[dict],
    citing: list[dict],
) -> dict:
    nodes: dict[str, dict] = {}
    edges: list[dict] = []

    def add_node(work: dict, kind: str) -> None:
        existing = nodes.get(work["id"])
        if existing:
            if kind not in existing["kinds"]:
                existing["kinds"].append(kind)
            return
        nodes[work["id"]] = {
            "id": work["id"],
            "title": work["title"],
            "year": work["year"],
            "cited_by_count": work["cited_by_count"],
            "authors": work["authors"],
            "url": work["url"],
            "kinds": [kind],
        }

    add_node(root, "root")
    for ref in references:
        if ref["id"] != root["id"]:
            add_node(ref, "reference")
            edges.append({"source": root["id"], "target": ref["id"], "kind": "cites"})
    for c in citing:
        if c["id"] != root["id"]:
            add_node(c, "citing")
            edges.append({"source": c["id"], "target": root["id"], "kind": "cites"})

    return {
        "root_id": root["id"],
        "node_count": len(nodes),
        "edge_count": len(edges),
        "nodes": list(nodes.values()),
        "edges": edges,
    }
