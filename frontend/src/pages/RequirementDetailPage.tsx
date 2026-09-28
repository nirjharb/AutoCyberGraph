import React from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { api, RequirementDetail } from "../api/client";
import { Badge, Card, ErrorBox, PageHeader, RiskBadge, Spinner, StatusBadge, TraceChecklist } from "../components/ui";

export const RequirementDetailPage: React.FC = () => {
  const { reqId } = useParams();
  const { data, isLoading, error } = useQuery<RequirementDetail>({
    queryKey: ["requirement", reqId],
    queryFn: () => api<RequirementDetail>(`/api/requirements/${reqId}/traceability`),
  });

  if (isLoading) return <Spinner label="Loading requirement traceability…" />;
  if (error || !data) return <ErrorBox message={error instanceof Error ? error.message : "Failed to load"} />;

  return (
    <div>
      <PageHeader
        title={`${data.requirement_id} — ${data.title}`}
        subtitle={data.description}
        actions={<Link className="btn-ghost" to="/app/requirements">← All requirements</Link>}
      />

      <div className="flex flex-wrap items-center gap-2 mb-6">
        <Badge tone="cyan">Priority: {data.priority}</Badge>
        <StatusBadge status={data.status} />
        {data.missing_links.length > 0 ? (
          <Badge tone="red">Missing: {data.missing_links.join(", ")}</Badge>
        ) : (
          <Badge tone="green">Fully traced</Badge>
        )}
      </div>

      <Card title="Traceability Checklist" subtitle="✓ present · ✗ missing — the digital thread at a glance">
        <TraceChecklist checks={data.trace_checks} />
      </Card>

      <div className="grid lg:grid-cols-2 gap-5 mt-5">
        <Card title="TARA & Threat Context">
          {data.tara ? (
            <div className="space-y-3">
              <div className="rounded-lg border border-ink-700 bg-ink-850/60 p-3">
                <div className="flex items-center justify-between">
                  <Link to="/app/tara" className="font-mono text-cyan-300">{data.tara.reference}</Link>
                  <RiskBadge level={data.tara.risk_level} />
                </div>
                <p className="text-xs text-slate-400 mt-1">Goal: {data.tara.cybersecurity_goal}</p>
              </div>
              {data.asset && (
                <div className="rounded-lg border border-ink-700 bg-ink-850/60 p-3">
                  <div className="text-xs uppercase text-slate-500 font-semibold">Asset</div>
                  <div className="text-white">{data.asset.name}</div>
                  <Badge tone={data.asset.criticality === "HIGH" ? "amber" : "slate"}>{data.asset.criticality}</Badge>
                </div>
              )}
              {data.threat && (
                <div className="rounded-lg border border-ink-700 bg-ink-850/60 p-3">
                  <div className="text-xs uppercase text-slate-500 font-semibold">Threat</div>
                  <div className="text-white">{data.threat.name}</div>
                  <div className="text-xs text-slate-400">{data.threat.threat_type}</div>
                </div>
              )}
            </div>
          ) : (
            <p className="text-sm text-rose-300">✗ No TARA linked — this requirement is not derived from a risk assessment.</p>
          )}
        </Card>

        <Card title="AUTOSAR Security Mechanisms" subtitle="Mitigations mapped to this requirement">
          {data.mechanisms.length === 0 ? (
            <p className="text-sm text-rose-300">✗ No AUTOSAR mechanism mapped.</p>
          ) : (
            <div className="space-y-2">
              {data.mechanisms.map((m) => (
                <div key={m.id} className="rounded-lg border border-ink-700 bg-ink-850/60 p-3">
                  <div className="flex items-center justify-between">
                    <span className="text-white font-semibold">{m.name}</span>
                    <Badge tone="violet">{m.category}</Badge>
                  </div>
                  {m.notes && <div className="text-xs text-slate-400 mt-1">{m.notes}</div>}
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card title="Security Controls" subtitle="Standards mapping layer (NIST / R155 / R156 / 21434)">
          {data.controls.length === 0 ? (
            <p className="text-sm text-rose-300">✗ No control mapped.</p>
          ) : (
            <div className="space-y-2">
              {data.controls.map((c) => (
                <div key={c.id} className="flex items-center justify-between rounded-lg border border-ink-700 bg-ink-850/60 p-3">
                  <div>
                    <div className="font-mono text-cyan-300 text-sm">{c.control_id}</div>
                    <div className="text-xs text-slate-400">{c.title}</div>
                  </div>
                  <Badge>{c.standard}</Badge>
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card title="Verification" subtitle="Test cases and results">
          {data.tests.length === 0 ? (
            <p className="text-sm text-rose-300">✗ No test linked.</p>
          ) : (
            <div className="space-y-2">
              {data.tests.map((t) => {
                const results = data.test_results.filter((r) => r.test_case_id === t.id);
                return (
                  <div key={t.id} className="rounded-lg border border-ink-700 bg-ink-850/60 p-3">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-white text-sm">{t.name}</span>
                      <StatusBadge status={t.status} />
                    </div>
                    <div className="text-xs text-slate-500 mt-1">
                      {t.test_type}
                      {results.length > 0 && ` · last run ${results[results.length - 1].executed_at?.slice(0, 10) ?? ""}`}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </Card>
      </div>

      <div className="mt-5">
        <Card title="Evidence" subtitle="Linked evidence artifacts">
          {data.evidence.length === 0 ? (
            <p className="text-sm text-rose-300">✗ Evidence missing — this requirement cannot currently support a cybersecurity case.</p>
          ) : (
            <div className="grid sm:grid-cols-2 gap-2.5">
              {data.evidence.map((e) => (
                <div key={e.id} className="flex items-center justify-between rounded-lg border border-ink-700 bg-ink-850/60 p-3">
                  <div>
                    <div className="text-white text-sm">{e.name}</div>
                    <div className="text-xs text-slate-500">{e.type}</div>
                  </div>
                  <StatusBadge status={e.status} />
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
};
