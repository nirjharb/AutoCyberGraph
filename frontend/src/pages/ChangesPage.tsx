import React, { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, Change, ImpactReport, post } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { Badge, Card, Dialog, ErrorBox, Field, Input, PageHeader, RiskBadge, Select, Spinner, StatusBadge, Table, Textarea } from "../components/ui";

const CHANGE_TYPES = [
  "SOFTWARE_CHANGE",
  "AUTOSAR_CONFIG_CHANGE",
  "ECU_CHANGE",
  "NETWORK_MESSAGE_CHANGE",
  "CRYPTO_LIBRARY_CHANGE",
  "REQUIREMENT_CHANGE",
  "TARA_CHANGE",
  "VULNERABILITY",
  "SBOM_CHANGE",
];

const BUCKET_LABELS: Record<string, string> = {
  tara: "TARA Scenarios",
  requirements: "Requirements",
  tests: "Tests",
  test_results: "Test Results",
  controls: "Controls",
  autosar_mechanisms: "AUTOSAR Mechanisms",
  evidence: "Evidence",
  releases: "Releases",
  vulnerabilities: "Vulnerabilities",
  software_components: "Software Components",
  ecus: "ECUs",
  vehicles: "Vehicles",
  assets: "Assets",
  threats: "Threats",
  networks: "Networks",
  sboms: "SBOMs",
  sbom_components: "SBOM Components",
};

export const ChangesPage: React.FC = () => {
  const { user, hasRole } = useAuth();
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [report, setReport] = useState<ImpactReport | null>(null);
  const [expandedBucket, setExpandedBucket] = useState<string | null>(null);
  const [form, setForm] = useState({
    entity_type: "SoftwareComponent",
    entity_id: 1,
    change_type: "CRYPTO_LIBRARY_CHANGE",
    description: "",
    security_assessment: "",
  });

  const changes = useQuery<Change[]>({ queryKey: ["changes"], queryFn: () => api<Change[]>("/api/changes") });

  const createMutation = useMutation({
    mutationFn: () => post<Change>("/api/changes", { ...form, created_by: user?.email }),
    onSuccess: (change) => {
      queryClient.invalidateQueries({ queryKey: ["changes"] });
      setOpen(false);
      impactMutation.mutate(change.id);
    },
  });

  const impactMutation = useMutation({
    mutationFn: (changeId: number) => post<ImpactReport>(`/api/changes/${changeId}/impact`, {}),
    onSuccess: (data) => {
      setReport(data);
      setExpandedBucket(null);
      queryClient.invalidateQueries({ queryKey: ["changes"] });
    },
  });

  return (
    <div>
      <PageHeader
        title="Change Impact Engine"
        subtitle="Record a change and traverse the evidence graph: affected TARA, requirements, controls, mechanisms, tests, vulnerabilities, evidence and releases — each with the graph path that made it affected."
        actions={
          hasRole("CYBERSECURITY_ENGINEER", "ARCHITECT", "TESTER") ? (
            <button className="btn-primary" onClick={() => setOpen(true)}>+ Record Change</button>
          ) : null
        }
      />

      <div className="grid lg:grid-cols-2 gap-5">
        <Card title="Change Records" subtitle="Click ⏵ Analyze to run impact analysis">
          {changes.isLoading ? (
            <Spinner />
          ) : changes.error ? (
            <ErrorBox message={changes.error instanceof Error ? changes.error.message : "error"} />
          ) : (
            <Table headers={["#", "Description", "Type", "Impact", ""]}>
              {(changes.data ?? []).map((ch) => (
                <tr key={ch.id} className="hover:bg-ink-850/60">
                  <td className="td font-mono text-slate-400">#{ch.id}</td>
                  <td className="td max-w-[240px]">
                    <div className="truncate text-white">{ch.description}</div>
                    <div className="text-xs text-slate-500 mt-0.5">
                      {ch.entity_type}:{ch.entity_id} · {ch.created_by}
                    </div>
                  </td>
                  <td className="td text-xs">{ch.change_type.replaceAll("_", " ")}</td>
                  <td className="td">{ch.impact_level ? <RiskBadge level={ch.impact_level} /> : <span className="text-xs text-slate-500">pending</span>}</td>
                  <td className="td">
                    <button
                      className="btn-ghost text-xs px-2.5 py-1"
                      disabled={impactMutation.isPending}
                      onClick={() => impactMutation.mutate(ch.id)}
                    >
                      ⏵ Analyze
                    </button>
                  </td>
                </tr>
              ))}
            </Table>
          )}
        </Card>

        <div>
          {impactMutation.isPending && <Spinner label="Traversing evidence graph…" />}
          {impactMutation.error && <ErrorBox message={impactMutation.error instanceof Error ? impactMutation.error.message : "failed"} />}

          {report && (
            <Card
              title={`Impact Report — Change #${report.change_id}`}
              subtitle="Affected artifacts derived strictly from graph relationships"
              actions={<RiskBadge level={report.impact_level} />}
            >
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 mb-4">
                {Object.entries(report.summary)
                  .sort((a, b) => b[1] - a[1])
                  .map(([bucket, count]) => (
                    <button
                      key={bucket}
                      className={`rounded-lg border px-3 py-2 text-left transition-colors ${
                        expandedBucket === bucket ? "border-accent/60 bg-accent/10" : "border-ink-700 bg-ink-850/60 hover:border-accent/40"
                      }`}
                      onClick={() => setExpandedBucket(expandedBucket === bucket ? null : bucket)}
                    >
                      <div className="text-lg font-bold text-white font-mono">{count}</div>
                      <div className="text-[10px] uppercase tracking-wider text-slate-400">{BUCKET_LABELS[bucket] ?? bucket}</div>
                    </button>
                  ))}
              </div>

              {expandedBucket && report.affected[expandedBucket] && (
                <div className="rounded-lg border border-ink-700 bg-ink-950/50 p-3 mb-4 max-h-72 overflow-y-auto">
                  <div className="text-xs uppercase tracking-wider text-slate-500 font-semibold mb-2">
                    {BUCKET_LABELS[expandedBucket] ?? expandedBucket} — affected with reasons
                  </div>
                  <div className="space-y-2">
                    {report.affected[expandedBucket].map((item, i) => (
                      <div key={i} className="rounded bg-ink-850/80 border border-ink-800 px-3 py-2">
                        <div className="flex items-center justify-between gap-2">
                          <span className="text-slate-200 text-sm font-medium">{item.label}</span>
                          <Badge>depth {item.depth}</Badge>
                        </div>
                        <div className="text-xs text-slate-500 mt-1">
                          <span className="text-accent/80">why:</span> {item.reason}
                        </div>
                        {item.path.length > 0 && (
                          <div className="text-[10px] font-mono text-slate-600 mt-1">{item.path.join(" → ")}</div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="rounded-lg border border-ink-700 bg-ink-850/60 p-4">
                <div className="text-xs uppercase tracking-wider text-slate-500 font-semibold mb-2">Recommended actions</div>
                <ul className="space-y-1.5">
                  {report.recommended_actions.map((action, i) => (
                    <li key={i} className="text-sm text-slate-300 flex gap-2">
                      <span className="text-accent">▸</span>
                      {action}
                    </li>
                  ))}
                </ul>
              </div>

              <div className="rounded-lg border border-ink-700 bg-ink-850/60 p-4 mt-3">
                <div className="text-xs uppercase tracking-wider text-slate-500 font-semibold mb-2">Rationale</div>
                <ul className="space-y-1">
                  {report.rationale.map((line, i) => (
                    <li key={i} className="text-xs text-slate-400">{line}</li>
                  ))}
                </ul>
              </div>
            </Card>
          )}

          {!report && !impactMutation.isPending && (
            <Card title="How the engine works">
              <ol className="space-y-2 text-sm text-slate-400 list-decimal list-inside">
                <li>The change references an entity (component, ECU, requirement, TARA…).</li>
                <li>Breadth-first traversal follows every traceability relationship.</li>
                <li>Reachable artifacts are classified and reported per type.</li>
                <li>Each artifact carries the actual edge path that made it affected.</li>
                <li>Impact level is derived from change weight, risk, vulnerabilities and release exposure.</li>
              </ol>
              <p className="text-xs text-slate-500 mt-4">
                No arbitrary guesses: an object is affected if and only if it is reachable in the traceability graph.
              </p>
            </Card>
          )}
        </div>
      </div>

      <Dialog open={open} title="Record Change" onClose={() => setOpen(false)} wide>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Field label="Entity type">
              <Select value={form.entity_type} onChange={(e) => setForm({ ...form, entity_type: e.target.value })}>
                <option>SoftwareComponent</option>
                <option>ECU</option>
                <option>CybersecurityRequirement</option>
                <option>TARA</option>
                <option>AutosarMechanism</option>
                <option>Vulnerability</option>
                <option>SBOM</option>
                <option>Network</option>
              </Select>
            </Field>
            <Field label="Entity ID">
              <Input type="number" value={form.entity_id} onChange={(e) => setForm({ ...form, entity_id: Number(e.target.value) })} />
            </Field>
          </div>
          <Field label="Change type">
            <Select value={form.change_type} onChange={(e) => setForm({ ...form, change_type: e.target.value })}>
              {CHANGE_TYPES.map((t) => (
                <option key={t}>{t}</option>
              ))}
            </Select>
          </Field>
          <Field label="Description">
            <Textarea rows={3} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} placeholder="e.g. Gateway ECU crypto library v2.4 → v2.5" />
          </Field>
          <Field label="Security impact assessment (R156-style workflow)">
            <Textarea rows={3} value={form.security_assessment} onChange={(e) => setForm({ ...form, security_assessment: e.target.value })} placeholder="What must be re-verified because of this change?" />
          </Field>
          <div className="rounded-lg border border-accent/30 bg-accent/10 px-4 py-3 text-xs text-slate-300">
            After recording, the impact analysis runs automatically and the affected artifacts appear on the right.
          </div>
          {createMutation.error && <ErrorBox message={createMutation.error instanceof Error ? createMutation.error.message : "failed"} />}
          <div className="flex justify-end gap-2">
            <button className="btn-ghost" onClick={() => setOpen(false)}>Cancel</button>
            <button className="btn-primary" disabled={!form.description || createMutation.isPending} onClick={() => createMutation.mutate()}>
              {createMutation.isPending ? "Recording…" : "Record & Analyze"}
            </button>
          </div>
        </div>
      </Dialog>
    </div>
  );
};
