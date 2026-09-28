import React from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { Card, ErrorBox, PageHeader, Spinner, StatusBadge, Table } from "../components/ui";

interface TestRow {
  id: number;
  requirement_id: number | null;
  name: string;
  description: string;
  test_type: string;
  expected_result: string;
  status: string;
}

export const TestsPage: React.FC = () => {
  const navigate = useNavigate();
  const { data, isLoading, error } = useQuery<TestRow[]>({
    queryKey: ["tests"],
    queryFn: () => api<TestRow[]>("/api/tests"),
  });

  return (
    <div>
      <PageHeader
        title="Cybersecurity Tests"
        subtitle="Verification test cases linked to requirements. Test results feed the release gate and evidence graph."
      />
      {isLoading && <Spinner />}
      {error && <ErrorBox message={error instanceof Error ? error.message : "error"} />}
      {data && (
        <Card>
          <Table headers={["Name", "Type", "Expected Result", "Requirement", "Status"]}>
            {data.map((t) => (
              <tr
                key={t.id}
                className="hover:bg-ink-850/60 cursor-pointer"
                onClick={() => t.requirement_id && navigate(`/app/requirements/${t.requirement_id}`)}
              >
                <td className="td text-white font-medium">{t.name}</td>
                <td className="td">
                  <span className="chip bg-ink-800 text-slate-300 border border-ink-700">{t.test_type}</span>
                </td>
                <td className="td text-slate-400 max-w-md truncate">{t.expected_result}</td>
                <td className="td text-cyan-300 font-mono text-xs">{t.requirement_id ? `#${t.requirement_id}` : "—"}</td>
                <td className="td">
                  <StatusBadge status={t.status} />
                </td>
              </tr>
            ))}
          </Table>
        </Card>
      )}
    </div>
  );
};
