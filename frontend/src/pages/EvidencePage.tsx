import React from "react";
import { useQuery } from "@tanstack/react-query";
import { api, Evidence } from "../api/client";
import { Card, ErrorBox, PageHeader, Spinner, StatusBadge, Table } from "../components/ui";

export const EvidencePage: React.FC = () => {
  const { data, isLoading, error } = useQuery<Evidence[]>({
    queryKey: ["evidence"],
    queryFn: () => api<Evidence[]>("/api/evidence"),
  });

  return (
    <div>
      <PageHeader
        title="Evidence Management"
        subtitle="Evidence artifacts supporting TARA, requirements, tests and releases — the raw material of the cybersecurity case."
      />
      {isLoading && <Spinner />}
      {error && <ErrorBox message={error instanceof Error ? error.message : "error"} />}
      {data && (
        <Card>
          <Table headers={["Name", "Type", "File Reference", "Links", "Status", "Created"]}>
            {data.map((e) => (
              <tr key={e.id} className="hover:bg-ink-850/60">
                <td className="td text-white font-medium">{e.name}</td>
                <td className="td">
                  <span className="chip bg-ink-800 text-slate-300 border border-ink-700">{e.type}</span>
                </td>
                <td className="td font-mono text-xs text-slate-400 max-w-[220px] truncate">{e.file_reference}</td>
                <td className="td text-xs text-slate-400">
                  {[
                    e.requirement_id ? `REQ #${e.requirement_id}` : null,
                    e.tara_id ? `TARA #${e.tara_id}` : null,
                    e.release_id ? `REL #${e.release_id}` : null,
                    e.test_result_id ? `TR #${e.test_result_id}` : null,
                  ]
                    .filter(Boolean)
                    .join(" · ") || "—"}
                </td>
                <td className="td">
                  <StatusBadge status={e.status} />
                </td>
                <td className="td text-xs text-slate-500">{e.created_at.slice(0, 10)}</td>
              </tr>
            ))}
          </Table>
        </Card>
      )}
    </div>
  );
};
