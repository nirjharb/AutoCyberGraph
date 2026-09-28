import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate, useSearchParams } from "react-router-dom";
import { api, Requirement } from "../api/client";
import { Badge, Card, ErrorBox, PageHeader, Spinner, StatusBadge, Table } from "../components/ui";

export const RequirementsPage: React.FC = () => {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const missing = params.get("missing");
  const [filter, setFilter] = useState(missing ?? "");

  const { data, isLoading, error } = useQuery<Requirement[]>({
    queryKey: ["requirements", filter],
    queryFn: () => api<Requirement[]>(`/api/requirements${filter ? `?missing=${filter}` : ""}`),
  });

  return (
    <div>
      <PageHeader
        title="Cybersecurity Requirements"
        subtitle="Click a requirement to open full traceability: TARA → asset → threat → control → AUTOSAR mechanism → test → evidence."
      />

      <div className="flex flex-wrap gap-2 mb-4">
        {[
          { key: "", label: "All" },
          { key: "evidence", label: "Missing evidence" },
          { key: "tests", label: "Missing tests" },
        ].map((f) => (
          <button
            key={f.key || "all"}
            className={`chip border cursor-pointer ${filter === f.key ? "bg-accent/20 border-accent/50 text-accent-glow" : "bg-ink-850 border-ink-700 text-slate-400"}`}
            onClick={() => setFilter(f.key)}
          >
            {f.label}
          </button>
        ))}
      </div>

      {isLoading && <Spinner />}
      {error && <ErrorBox message={error instanceof Error ? error.message : "error"} />}
      {data && (
        <Card>
          <Table headers={["ID", "Title", "Priority", "Status", "TARA"]}>
            {data.map((r) => (
              <tr key={r.id} className="hover:bg-ink-850/60 cursor-pointer" onClick={() => navigate(`/app/requirements/${r.id}`)}>
                <td className="td font-mono text-cyan-300">{r.requirement_id}</td>
                <td className="td text-white font-medium">{r.title}</td>
                <td className="td">
                  <Badge tone={r.priority === "HIGH" ? "amber" : "slate"}>{r.priority}</Badge>
                </td>
                <td className="td">
                  <StatusBadge status={r.status} />
                </td>
                <td className="td text-slate-400">{r.tara_id ? `TARA #${r.tara_id}` : <span className="text-rose-400 text-xs">not linked</span>}</td>
              </tr>
            ))}
          </Table>
        </Card>
      )}
    </div>
  );
};
