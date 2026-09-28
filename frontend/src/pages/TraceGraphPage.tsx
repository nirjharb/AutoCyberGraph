import React, { useEffect, useRef, useState } from "react";
import cytoscape from "cytoscape";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { api, Requirement, TARA } from "../api/client";
import { Card, ErrorBox, PageHeader, Select, Spinner } from "../components/ui";

interface GraphPayload {
  nodes: { id: string; label: string; entity_type: string; entity_id: number; depth: number }[];
  edges: { id: string; source: string; target: string; label: string }[];
}

const TYPE_COLORS: Record<string, string> = {
  TARA: "#a78bfa",
  CybersecurityRequirement: "#22d3ee",
  Control: "#34d399",
  AutosarMechanism: "#fb923c",
  TestCase: "#facc15",
  TestResult: "#fde68a",
  Evidence: "#f43f5e",
  Release: "#38bdf8",
  Asset: "#c084fc",
  Threat: "#fb7185",
  ECU: "#94a3b8",
};

export const TraceGraphPage: React.FC = () => {
  const navigate = useNavigate();
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);
  const [reqId, setReqId] = useState<number | null>(null);

  const reqs = useQuery<Requirement[]>({ queryKey: ["requirements"], queryFn: () => api<Requirement[]>("/api/requirements") });

  const graph = useQuery<GraphPayload>({
    queryKey: ["evidence-graph", reqId],
    queryFn: () => api<GraphPayload>(`/api/evidence-graph?requirement_id=${reqId}`),
    enabled: Boolean(reqId),
  });

  useEffect(() => {
    if (!graph.data || !containerRef.current) return;
    if (cyRef.current) cyRef.current.destroy();

    const cy = cytoscape({
      container: containerRef.current,
      elements: [
        ...graph.data.nodes.map((n) => ({
          data: { ...n, color: TYPE_COLORS[n.entity_type] ?? "#64748b" },
        })),
        ...graph.data.edges.map((e) => ({ data: e })),
      ],
      style: ([
        {
          selector: "node",
          style: {
            label: "data(label)",
            "background-color": "data(color)",
            color: "#e2e8f0",
            "font-size": 9,
            "text-wrap": "ellipsis",
            "text-max-width": 110,
            "text-valign": "bottom",
            "text-margin-y": 5,
            width: 34,
            height: 34,
            "border-width": 2,
            "border-color": "#0f1722",
          },
        },
        {
          selector: "edge",
          style: {
            width: 1.6,
            "line-color": "#334155",
            "curve-style": "bezier",
            "target-arrow-color": "#334155",
            "target-arrow-shape": "triangle",
            "arrow-scale": 0.8,
          },
        },
        {
          selector: "node:selected",
          style: { "border-color": "#22d3ee", "border-width": 3 },
        },
      ] as never),
      layout: {
        name: "cose",
        animate: false,
        padding: 30,
        nodeRepulsion: 4200,
        idealEdgeLength: 110,
      } as cytoscape.LayoutOptions,
    });

    cy.on("tap", "node", (evt) => {
      const d = evt.target.data();
      const routeByType: Record<string, string> = {
        CybersecurityRequirement: `/app/requirements/${d.entity_id}`,
        TARA: "/app/tara",
        TestCase: "/app/tests",
        Evidence: "/app/evidence",
        Release: "/app/releases",
        Vulnerability: "/app/vulnerabilities",
        ECU: `/app/ecus/${d.entity_id}`,
      };
      const route = routeByType[d.entity_type];
      if (route) navigate(route);
    });

    cyRef.current = cy;
    return () => {
      cy.destroy();
    };
  }, [graph.data, navigate]);

  return (
    <div>
      <PageHeader
        title="Evidence Graph"
        subtitle="TARA → Goal → Requirement → Control → AUTOSAR Mechanism → Test → Evidence. Click a node to open its detail page."
      />

      <Card>
        <div className="flex flex-wrap items-center gap-3 mb-4">
          <span className="text-sm text-slate-400">Start from requirement:</span>
          <Select
            className="max-w-md"
            value={reqId ?? ""}
            onChange={(e) => setReqId(e.target.value ? Number(e.target.value) : null)}
          >
            <option value="">Select a requirement…</option>
            {(reqs.data ?? []).map((r) => (
              <option key={r.id} value={r.id}>
                {r.requirement_id} — {r.title}
              </option>
            ))}
          </Select>
          {graph.isLoading && <Spinner label="Traversing graph…" />}
          {graph.error && <ErrorBox message={graph.error instanceof Error ? graph.error.message : "error"} />}
        </div>

        <div
          ref={containerRef}
          className="rounded-xl border border-ink-700/60 bg-ink-950/70"
          style={{ height: "560px", display: reqId ? "block" : "none" }}
        />

        {!reqId && (
          <div className="text-center py-16 text-slate-400">
            <p className="text-lg font-semibold text-slate-300">Select a requirement to render its evidence graph</p>
            <p className="text-sm mt-1">The graph is computed live from the traceability relationships in the database.</p>
          </div>
        )}

        <div className="flex flex-wrap gap-3 mt-4">
          {Object.entries(TYPE_COLORS).map(([type, color]) => (
            <span key={type} className="inline-flex items-center gap-1.5 text-xs text-slate-400">
              <span className="h-2.5 w-2.5 rounded-full" style={{ background: color }} /> {type}
            </span>
          ))}
        </div>
      </Card>
    </div>
  );
};
