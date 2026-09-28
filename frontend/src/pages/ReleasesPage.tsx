import React, { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, GateEvaluation, post, Release } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { Badge, Card, ErrorBox, GateBadge, PageHeader, Spinner, StatusBadge, Table } from "../components/ui";

export const ReleasesPage: React.FC = () => {
  const { hasRole } = useAuth();
  const queryClient = useQueryClient();
  const [evaluation, setEvaluation] = useState<GateEvaluation | null>(null);
  const [evaluatingId, setEvaluatingId] = useState<number | null>(null);

  const releases = useQuery<Release[]>({
    queryKey: ["releases"],
    queryFn: () => api<Release[]>("/api/releases"),
  });

  const evaluateMutation = useMutation({
    mutationFn: (releaseId: number) => post<GateEvaluation>(`/api/releases/${releaseId}/evaluate`, {}),
    onSuccess: (data) => {
      setEvaluation(data);
      setEvaluatingId(data.release_id);
      queryClient.invalidateQueries({ queryKey: ["releases"] });
    },
  });

  return (
    <div>
      <PageHeader
        title="Cybersecurity Release Gate"
        subtitle="Deterministic gate checks with reasons — PASS / REVIEW / HOLD. Deliberately no composite “security score”."
      />

      {releases.isLoading && <Spinner />}
      {releases.error && <ErrorBox message={releases.error instanceof Error ? releases.error.message : "error"} />}

      {releases.data && (
        <Card>
          <Table headers={["Release", "ECU", "Type", "Status", "Gate", "Evaluated", ""]}>
            {releases.data.map((r) => (
              <tr key={r.id} className="hover:bg-ink-850/60">
                <td className="td font-mono text-white">{r.version}</td>
                <td className="td">ECU #{r.ecu_id}</td>
                <td className="td text-xs">{r.release_type}</td>
                <td className="td">
                  <StatusBadge status={r.status} />
                </td>
                <td className="td">
                  <GateBadge result={r.gate_result} />
                </td>
                <td className="td text-xs text-slate-500">{r.gate_evaluated_at ? r.gate_evaluated_at.slice(0, 16).replace("T", " ") : "—"}</td>
                <td className="td">
                  {hasRole("CYBERSECURITY_ENGINEER", "ARCHITECT") && (
                    <button
                      className="btn-primary text-xs px-3 py-1.5"
                      disabled={evaluateMutation.isPending && evaluatingId === r.id}
                      onClick={() => {
                        setEvaluatingId(r.id);
                        evaluateMutation.mutate(r.id);
                      }}
                    >
                      {evaluateMutation.isPending && evaluatingId === r.id ? "Evaluating…" : "Evaluate Gate"}
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </Table>
        </Card>
      )}

      {evaluateMutation.error && (
        <div className="mt-5">
          <ErrorBox message={evaluateMutation.error instanceof Error ? evaluateMutation.error.message : "failed"} />
        </div>
      )}

      {evaluation && (
        <div className="mt-6">
          <Card
            title={`Gate Evaluation — Release #${evaluation.release_id}`}
            subtitle="Blocking failures force HOLD; advisory failures force REVIEW"
            actions={<GateBadge result={evaluation.result} />}
          >
            <div className="space-y-2.5">
              {evaluation.checks.map((c) => (
                <div
                  key={c.key}
                  className={`rounded-lg border px-4 py-3 ${
                    c.passed
                      ? "border-emerald-500/30 bg-emerald-950/20"
                      : c.severity === "BLOCKING"
                        ? "border-rose-500/40 bg-rose-950/30"
                        : "border-amber-500/40 bg-amber-950/20"
                  }`}
                >
                  <div className="flex items-center justify-between gap-3">
                    <div className="flex items-center gap-2.5">
                      <span className={`font-bold ${c.passed ? "text-emerald-400" : "text-rose-400"}`}>{c.passed ? "✓" : "✗"}</span>
                      <span className="text-white font-medium text-sm">{c.label}</span>
                    </div>
                    <Badge tone={c.severity === "BLOCKING" ? "red" : "amber"}>{c.severity}</Badge>
                  </div>
                  <p className="text-xs text-slate-400 mt-1.5 ml-6">{c.detail}</p>
                </div>
              ))}
            </div>

            <div className="mt-5 rounded-lg border border-ink-700 bg-ink-850/60 p-4">
              <div className="text-xs uppercase tracking-wider text-slate-500 font-semibold mb-2">Verdict reasons</div>
              <ul className="space-y-1.5">
                {evaluation.reasons.map((reason, i) => (
                  <li key={i} className="text-sm text-slate-300 flex gap-2">
                    <span className="text-accent">▸</span>
                    {reason}
                  </li>
                ))}
              </ul>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};
