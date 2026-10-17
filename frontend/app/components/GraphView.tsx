"use client";

type Node = {
  id: string;
  title: string;
  year: number | null;
  cited_by_count: number;
  authors: string[];
  url: string | null;
  kinds: string[];
};
type Edge = { source: string; target: string; kind: string };
export type Graph = { root_id: string; nodes: Node[]; edges: Edge[] };

const W = 1000;
const H = 620;
const CX = W / 2;
const CY = H / 2;
const R = 225;

const COLORS: Record<string, string> = {
  root: "#f5a524",
  reference: "#38bdf8",
  citing: "#34d399",
};

function colorFor(n: Node): string {
  if (n.kinds.includes("root")) return COLORS.root;
  if (n.kinds.includes("reference")) return COLORS.reference;
  return COLORS.citing;
}

function layout(graph: Graph): Map<string, { x: number; y: number }> {
  const pos = new Map<string, { x: number; y: number }>();
  const refs = graph.nodes.filter(
    (n) => n.kinds.includes("reference") && !n.kinds.includes("root")
  );
  const citing = graph.nodes.filter(
    (n) => n.kinds.includes("citing") && !n.kinds.includes("root") && !n.kinds.includes("reference")
  );
  pos.set(graph.root_id, { x: CX, y: CY });
  refs.forEach((n, i) => {
    // left arc: 110deg .. 250deg
    const t = refs.length === 1 ? 0.5 : i / (refs.length - 1);
    const a = ((110 + 140 * t) * Math.PI) / 180;
    pos.set(n.id, { x: CX + R * Math.cos(a), y: CY + R * Math.sin(a) });
  });
  citing.forEach((n, i) => {
    // right arc: -70deg .. 70deg
    const t = citing.length === 1 ? 0.5 : i / (citing.length - 1);
    const a = ((-70 + 140 * t) * Math.PI) / 180;
    pos.set(n.id, { x: CX + R * Math.cos(a), y: CY + R * Math.sin(a) });
  });
  return pos;
}

function radius(n: Node): number {
  return 9 + 5 * Math.log10(1 + n.cited_by_count);
}

function truncate(s: string, n: number): string {
  return s.length <= n ? s : s.slice(0, n - 1) + "…";
}

// Stagger labels into two lanes so neighbours don't collide.
function labelLane(index: number): number {
  return index % 2 === 0 ? 0 : 12;
}

export default function GraphView({
  graph,
  onSelect,
  onFocus,
}: {
  graph: Graph;
  onSelect: (n: Node) => void;
  onFocus: (id: string) => void;
}) {
  const pos = layout(graph);
  const byId = new Map(graph.nodes.map((n) => [n.id, n]));
  return (
    <svg className="graph-svg" viewBox={`0 0 ${W} ${H}`} role="img" aria-label="citation graph">
      <defs>
        <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
          <path d="M 0 1 L 9 5 L 0 9 z" fill="#4b5b76" />
        </marker>
      </defs>
      {graph.edges.map((e, i) => {
        const a = pos.get(e.source);
        const b = pos.get(e.target);
        if (!a || !b) return null;
        const ta = byId.get(e.target)!;
        const sa = byId.get(e.source)!;
        // shorten the line so the arrowhead lands on the target circle edge
        const dx = b.x - a.x;
        const dy = b.y - a.y;
        const len = Math.hypot(dx, dy) || 1;
        const x1 = a.x + (dx / len) * radius(sa);
        const y1 = a.y + (dy / len) * radius(sa);
        const x2 = b.x - (dx / len) * (radius(ta) + 4);
        const y2 = b.y - (dy / len) * (radius(ta) + 4);
        return <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} stroke="#4b5b76" strokeWidth="1.4" markerEnd="url(#arrow)" />;
      })}
      {graph.nodes.map((n, ni) => {
        const p = pos.get(n.id);
        if (!p) return null;
        const isRoot = n.kinds.includes("root");
        return (
          <g
            key={n.id}
            className="node"
            onClick={() => (isRoot ? onSelect(n) : onFocus(n.id))}
            onMouseEnter={() => onSelect(n)}
          >
            <title>{`${n.title}${n.year ? ` (${n.year})` : ""} - ${n.cited_by_count} citations`}</title>
            <circle cx={p.x} cy={p.y} r={radius(n)} fill={colorFor(n)} fillOpacity={isRoot ? 1 : 0.85} stroke="#0b0f17" strokeWidth="2" />
            <text
              className="node-label"
              x={p.x}
              y={p.y + radius(n) + 14 + labelLane(ni)}
              textAnchor="middle"
            >
              {truncate(n.title, 26)}
            </text>
          </g>
        );
      })}
    </svg>
  );
}
