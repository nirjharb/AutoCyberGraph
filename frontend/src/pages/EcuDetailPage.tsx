import React from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../api/client";
import { Badge, Card, ErrorBox, PageHeader, RiskBadge, Spinner, StatusBadge, Table } from "../components/ui";

interface SecurityContext {
  ecu: { id: number; name: string; ecu_type: string; supplier: string; software_version: string; criticality: string; hardware_version: string; status: string };
  vehicle: { id: number; name: string; platform: string };
  assets: { id: number; name: string; type: string; criticality: string }[];
  taras: { id: number; reference: string; risk_level: string; cybersecurity_goal: string; status: string }[];
  requirements: { id: number; requirement_id: string; title: string; status: string; priority: string }[];
  components: { id: number; name: string; version: string; supplier: string }[];
  vulnerabilities: { id: number; cve_id: string; severity: string; status: string; cvss_score: number }[];
  releases: { id: number; version: string; status: string; gate_result: string | null }[];
  autosar_mechanisms: { id: number; name: string; category: string; status: string; notes: string }[];
}

export const EcuDetailPage: React.FC = () => {
  const { ecuId } = useParams();
  const navigate = useNavigate();
  const { data, isLoading, error } = useQuery<SecurityContext>({
    queryKey: ["ecu-context", ecuId],
    queryFn: () => api<SecurityContext>(`/api/ecus/${ecuId}/security-context`),
  });

  if (isLoading) return <Spinner label="Loading ECU security context…" />;
  if (error || !data) return <ErrorBox message={error instanceof Error ? error.message : "Failed to load"} />;

  const { ecu, vehicle, assets, taras, requirements, components, vulnerabilities, releases, autosar_mechanisms } = data;

  return (
    <div>
      <PageHeader
        title={ecu.name}
        subtitle={`${ecu.ecu_type} · ${ecu.supplier} · HW ${ecu.hardware_version} · SW ${ecu.software_version} · ${vehicle.name}`}
        actions={
          <>
            <Link className="btn-ghost" to={`/app/vehicles/${vehicle.id}`}>← {vehicle.name}</Link>
            <Link className="btn-primary" to={`/app/changes`}>Change Impact →</Link>
          </>
        }
      />

      <div className="flex flex-wrap gap-2 mb-6">
        <Badge tone={ecu.criticality === "HIGH" ? "amber" : "slate"}>Criticality: {ecu.criticality}</Badge>
        <Badge tone="cyan">Assets: {assets.length}</Badge>
        <Badge tone="violet">TARA: {taras.length}</Badge>
        <Badge tone="slate">Requirements: {requirements.length}</Badge>
        <Badge tone={vulnerabilities.some((v) => v.status === "OPEN") ? "red" : "green"}>
          Vulns: {vulnerabilities.filter((v) => v.status === "OPEN").length} open
        </Badge>
      </div>

      <div className="grid lg:grid-cols-2 gap-5">
        <Card title="Assets & Threat Scope" subtitle="Security-relevant assets hosted on this ECU">
          <Table headers={["Asset", "Type", "Criticality"]}>
            {assets.map((a) => (
              <tr key={a.id}>
                <td className="td text-white font-medium">{a.name}</td>
                <td className="td">{a.type}</td>
                <td className="td">
                  <Badge tone={a.criticality === "HIGH" ? "amber" : "slate"}>{a.criticality}</Badge>
                </td>
              </tr>
            ))}
          </Table>
        </Card>

        <Card title="TARA Scenarios" subtitle="Risk assessments covering this ECU's assets">
          <div className="space-y-2.5">
            {taras.map((t) => (
              <div key={t.id} className="rounded-lg border border-ink-700 bg-ink-850/60 p-3">
                <div className="flex items-center justify-between gap-2">
                  <span className="font-mono text-cyan-300 text-sm">{t.reference}</span>
                  <div className="flex gap-2">
                    <RiskBadge level={t.risk_level} />
                    <StatusBadge status={t.status} />
                  </div>
                </div>
                <p className="text-xs text-slate-400 mt-1.5">Goal: {t.cybersecurity_goal}</p>
              </div>
            ))}
          </div>
        </Card>

        <Card title="Cybersecurity Requirements" subtitle="Derived requirements in this ECU's scope">
          <Table headers={["ID", "Title", "Priority", "Status"]}>
            {requirements.map((r) => (
              <tr key={r.id} className="hover:bg-ink-850/60 cursor-pointer" onClick={() => navigate(`/app/requirements/${r.id}`)}>
                <td className="td font-mono text-cyan-300">{r.requirement_id}</td>
                <td className="td">{r.title}</td>
                <td className="td">{r.priority}</td>
                <td className="td">
                  <StatusBadge status={r.status} />
                </td>
              </tr>
            ))}
          </Table>
        </Card>

        <Card title="AUTOSAR Security Mechanisms" subtitle="Mechanisms implemented on this ECU">
          <div className="grid sm:grid-cols-2 gap-2.5">
            {autosar_mechanisms.map((m) => (
              <div key={m.id} className="rounded-lg border border-ink-700 bg-ink-850/60 p-3">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-white text-sm">{m.name}</span>
                  <StatusBadge status={m.status} />
                </div>
                <div className="text-xs text-slate-500 mt-1">{m.category}</div>
                {m.notes && <div className="text-xs text-slate-400 mt-1 italic">{m.notes}</div>}
              </div>
            ))}
            {autosar_mechanisms.length === 0 && <p className="text-sm text-slate-400">No mechanism implementations recorded.</p>}
          </div>
        </Card>

        <Card title="Software Components" subtitle="SBOM-relevant components running on this ECU">
          <Table headers={["Component", "Version", "Supplier"]}>
            {components.map((comp) => (
              <tr key={comp.id}>
                <td className="td text-white">{comp.name}</td>
                <td className="td font-mono text-cyan-300">{comp.version}</td>
                <td className="td text-slate-400">{comp.supplier}</td>
              </tr>
            ))}
          </Table>
        </Card>

        <Card title="Vulnerabilities" subtitle="CVEs mapped through components to this ECU">
          <div className="space-y-2">
            {vulnerabilities.map((v) => (
              <div key={v.id} className="flex items-center justify-between rounded-lg border border-ink-700 bg-ink-850/60 px-3 py-2">
                <div>
                  <div className="font-mono text-rose-300 text-sm">{v.cve_id}</div>
                  <div className="text-xs text-slate-500">CVSS {v.cvss_score}</div>
                </div>
                <div className="flex gap-2">
                  <RiskBadge level={v.severity} />
                  <StatusBadge status={v.status} />
                </div>
              </div>
            ))}
            {vulnerabilities.length === 0 && <p className="text-sm text-slate-400">No vulnerabilities recorded.</p>}
          </div>
        </Card>
      </div>

      <div className="mt-5">
        <Card title="Releases" subtitle="Software releases for this ECU — evaluate the Cybersecurity Release Gate">
          <Table headers={["Version", "Status", "Gate Result"]}>
            {releases.map((r) => (
              <tr key={r.id} className="hover:bg-ink-850/60 cursor-pointer" onClick={() => navigate("/app/releases")}>
                <td className="td font-mono text-white">{r.version}</td>
                <td className="td">
                  <StatusBadge status={r.status} />
                </td>
                <td className="td">{r.gate_result ?? <span className="text-slate-500 text-xs">not evaluated</span>}</td>
              </tr>
            ))}
          </Table>
        </Card>
      </div>
    </div>
  );
};
