import React, { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, post, Vulnerability } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { Badge, Card, Dialog, ErrorBox, Field, Input, PageHeader, RiskBadge, Select, Spinner, StatusBadge, Table, Textarea } from "../components/ui";

interface SbomRow {
  id: number;
  vehicle_id: number | null;
  ecu_id: number | null;
  format: string;
  file_name: string;
  version: string;
  uploaded_at: string;
  component_count: number;
}

interface VulnTrace {
  vulnerability: Vulnerability;
  component: { id: number; name: string; version: string } | null;
  ecu: { id: number; name: string; criticality: string } | null;
  vehicle: { id: number; name: string } | null;
}

const SAMPLE_CYCLONEDX = `{
  "bomFormat": "CycloneDX",
  "specVersion": "1.5",
  "components": [
    {"type": "library", "name": "libexample", "version": "1.0.0", "purl": "pkg:generic/libexample@1.0.0"}
  ]
}`;

export const VulnerabilitiesPage: React.FC = () => {
  const { hasRole } = useAuth();
  const queryClient = useQueryClient();
  const [importOpen, setImportOpen] = useState(false);
  const [traceId, setTraceId] = useState<number | null>(null);
  const [sbomForm, setSbomForm] = useState({ ecu_id: "", file_name: "sbom.json", format: "auto", content: "" });

  const vulns = useQuery<Vulnerability[]>({ queryKey: ["vulnerabilities"], queryFn: () => api<Vulnerability[]>("/api/vulnerabilities") });
  const sboms = useQuery<SbomRow[]>({ queryKey: ["sboms"], queryFn: () => api<SbomRow[]>("/api/sbom") });
  const trace = useQuery<VulnTrace>({
    queryKey: ["vuln-trace", traceId],
    queryFn: () => api<VulnTrace>(`/api/vulnerabilities/${traceId}/trace`),
    enabled: Boolean(traceId),
  });

  const importMutation = useMutation({
    mutationFn: () =>
      post<SbomRow>("/api/sbom/import", {
        ecu_id: sbomForm.ecu_id ? Number(sbomForm.ecu_id) : null,
        vehicle_id: 1,
        file_name: sbomForm.file_name,
        format: sbomForm.format,
        content: sbomForm.content,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sboms"] });
      setImportOpen(false);
    },
  });

  return (
    <div>
      <PageHeader
        title="Vulnerabilities & SBOM"
        subtitle="CVE → Component → ECU → Vehicle traceability. SBOM import supports CycloneDX and SPDX JSON."
        actions={
          hasRole("CYBERSECURITY_ENGINEER", "ARCHITECT") ? (
            <button className="btn-primary" onClick={() => setImportOpen(true)}>⇪ Import SBOM</button>
          ) : null
        }
      />

      <div className="grid lg:grid-cols-3 gap-5">
        <div className="lg:col-span-2">
          <Card title="Vulnerabilities" subtitle="Click a CVE to trace it to the affected vehicle">
            {vulns.isLoading ? (
              <Spinner />
            ) : vulns.error ? (
              <ErrorBox message={vulns.error instanceof Error ? vulns.error.message : "error"} />
            ) : (
              <Table headers={["CVE", "CVSS", "Severity", "Status", "Remediation"]}>
                {(vulns.data ?? []).map((v) => (
                  <tr key={v.id} className="hover:bg-ink-850/60 cursor-pointer" onClick={() => setTraceId(v.id)}>
                    <td className="td font-mono text-rose-300">{v.cve_id}</td>
                    <td className="td font-mono">{v.cvss_score}</td>
                    <td className="td">
                      <RiskBadge level={v.severity} />
                    </td>
                    <td className="td">
                      <StatusBadge status={v.status} />
                    </td>
                    <td className="td text-slate-400 max-w-[260px] truncate">{v.remediation}</td>
                  </tr>
                ))}
              </Table>
            )}
          </Card>

          {trace.data && (
            <div className="mt-5">
              <Card
                title={`Trace — ${trace.data.vulnerability.cve_id}`}
                subtitle="Graph path: vulnerability → component → ECU → vehicle"
              >
                <div className="flex flex-wrap items-center gap-2 text-sm">
                  <Badge tone="red">{trace.data.vulnerability.cve_id}</Badge>
                  <span className="text-slate-500">→</span>
                  <Badge tone="cyan">{trace.data.component?.name} {trace.data.component?.version}</Badge>
                  <span className="text-slate-500">→</span>
                  <Badge tone="amber">{trace.data.ecu?.name}</Badge>
                  <span className="text-slate-500">→</span>
                  <Badge tone="green">{trace.data.vehicle?.name}</Badge>
                </div>
                <p className="text-sm text-slate-400 mt-3">{trace.data.vulnerability.description}</p>
                <div className="rounded-lg border border-ink-700 bg-ink-850/60 p-3 mt-3">
                  <div className="text-xs uppercase text-slate-500 font-semibold">Remediation</div>
                  <div className="text-slate-200 text-sm mt-1">{trace.data.vulnerability.remediation}</div>
                </div>
              </Card>
            </div>
          )}
        </div>

        <Card title="SBOM Documents" subtitle="CycloneDX / SPDX imports">
          <div className="space-y-2.5">
            {(sboms.data ?? []).map((s) => (
              <div key={s.id} className="rounded-lg border border-ink-700 bg-ink-850/60 p-3">
                <div className="flex items-center justify-between">
                  <span className="text-white text-sm font-medium truncate">{s.file_name}</span>
                  <Badge tone={s.format === "CycloneDX" ? "cyan" : "violet"}>{s.format}</Badge>
                </div>
                <div className="text-xs text-slate-500 mt-1">
                  {s.component_count} components · v{s.version || "?"} · {s.uploaded_at.slice(0, 10)}
                </div>
              </div>
            ))}
            {(sboms.data ?? []).length === 0 && <p className="text-sm text-slate-400">No SBOMs imported.</p>}
          </div>
        </Card>
      </div>

      <Dialog open={importOpen} title="Import SBOM" onClose={() => setImportOpen(false)} wide>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Field label="File name">
              <Input value={sbomForm.file_name} onChange={(e) => setSbomForm({ ...sbomForm, file_name: e.target.value })} />
            </Field>
            <Field label="Format">
              <Select value={sbomForm.format} onChange={(e) => setSbomForm({ ...sbomForm, format: e.target.value })}>
                <option value="auto">Auto-detect</option>
                <option value="CycloneDX">CycloneDX</option>
                <option value="SPDX">SPDX</option>
              </Select>
            </Field>
          </div>
          <Field label="SBOM content (JSON)">
            <Textarea rows={10} value={sbomForm.content} onChange={(e) => setSbomForm({ ...sbomForm, content: e.target.value })} placeholder="Paste CycloneDX or SPDX JSON…" className="font-mono text-xs" />
          </Field>
          <button className="btn-ghost text-xs" onClick={() => setSbomForm({ ...sbomForm, content: SAMPLE_CYCLONEDX })}>
            Use sample CycloneDX
          </button>
          {importMutation.error && <ErrorBox message={importMutation.error instanceof Error ? importMutation.error.message : "failed"} />}
          <div className="flex justify-end gap-2">
            <button className="btn-ghost" onClick={() => setImportOpen(false)}>Cancel</button>
            <button className="btn-primary" disabled={!sbomForm.content || importMutation.isPending} onClick={() => importMutation.mutate()}>
              {importMutation.isPending ? "Importing…" : "Import"}
            </button>
          </div>
        </div>
      </Dialog>
    </div>
  );
};
