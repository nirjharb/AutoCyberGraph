import React from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { Bar, BarChart, CartesianGrid, Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api, DashboardData } from "../api/client";
import { Card, ErrorBox, GateBadge, PageHeader, RiskBadge, Spinner, StatCard, StatusBadge, Table } from "../components/ui";

const RISK_COLORS: Record<string, string> = {
  LOW: "#34d399",
  MEDIUM: "#facc15",
  HIGH: "#fb923c",
  CRITICAL: "#f43f5e",
};

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const { data, isLoading, error } = useQuery<DashboardData>({
    queryKey: ["dashboard"],
    queryFn: () => api<DashboardData>("/api/dashboard"),
  });

  if (isLoading) return <Spinner label="Loading live project metrics…" />;
  if (error || !data) return <ErrorBox message={error instanceof Error ? error.message : "Failed to load dashboard"} />;

  const riskData = Object.entries(data.risk_distribution).map(([name, value]) => ({ name, value }));
  const testData = Object.entries(data.test_status_counts).map(([name, value]) => ({ name, value }));
  const vulnData = Object.entries(data.vuln_severity_counts).map(([name, value]) => ({ name, value }));
  const c = data.counts;

  return (
    <div>
      <PageHeader
        title="Cybersecurity Dashboard"
        subtitle="Every metric is computed from live project data — click through to the underlying artifacts."
      />

      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4">
        <StatCard label="Vehicles" value={c.vehicles} to="/app/vehicles" onNavigate={navigate} />
        <StatCard label="ECUs" value={c.ecus} to="/app/vehicles" onNavigate={navigate} />
        <StatCard label="TARA Scenarios" value={c.tara_scenarios} to="/app/tara" onNavigate={navigate} />
        <StatCard label="Requirements" value={c.requirements} to="/app/requirements" onNavigate={navigate} />
        <StatCard label="Open Vulns" value={c.open_vulnerabilities} tone="amber" to="/app/vulnerabilities" onNavigate={navigate} />
        <StatCard label="Critical Vulns" value={c.critical_vulnerabilities} tone="red" to="/app/vulnerabilities" onNavigate={navigate} />
        <StatCard label="Failed Tests" value={c.failed_tests} tone="red" to="/app/tests" onNavigate={navigate} />
        <StatCard label="Missing Evidence" value={c.missing_evidence} tone="amber" to="/app/requirements?missing=evidence" onNavigate={navigate} />
        <StatCard label="Pending Reviews" value={c.pending_reviews} tone="amber" to="/app/tara" onNavigate={navigate} />
        <StatCard label="Changes" value={c.changes} to="/app/changes" onNavigate={navigate} />
        <StatCard label="Releases" value={c.releases} to="/app/releases" onNavigate={navigate} />
        <StatCard label="Evidence Items" value={c.evidence_items ?? 0} tone="cyan" to="/app/evidence" onNavigate={navigate} />
      </div>

      <div className="grid lg:grid-cols-3 gap-5 mt-6">
        <Card title="TARA Risk Distribution" subtitle="Live count per calculated risk level">
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={riskData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label>
                {riskData.map((entry) => (
                  <Cell key={entry.name} fill={RISK_COLORS[entry.name] ?? "#64748b"} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ background: "#13202e", border: "1px solid #22394c", borderRadius: 8 }} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </Card>

        <Card title="Test Execution Status" subtitle="Cybersecurity test cases by status">
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={testData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#22394c" />
              <XAxis dataKey="name" tick={{ fill: "#94a3b8", fontSize: 11 }} />
              <YAxis allowDecimals={false} tick={{ fill: "#94a3b8", fontSize: 11 }} />
              <Tooltip contentStyle={{ background: "#13202e", border: "1px solid #22394c", borderRadius: 8 }} />
              <Bar dataKey="value" fill="#22d3ee" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Card>

        <Card title="Open Vulnerabilities by Severity" subtitle="CVE/CVSS feed from SBOM components">
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={vulnData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#22394c" />
              <XAxis dataKey="name" tick={{ fill: "#94a3b8", fontSize: 11 }} />
              <YAxis allowDecimals={false} tick={{ fill: "#94a3b8", fontSize: 11 }} />
              <Tooltip contentStyle={{ background: "#13202e", border: "1px solid #22394c", borderRadius: 8 }} />
              <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                {vulnData.map((entry) => (
                  <Cell
                    key={entry.name}
                    fill={
                      entry.name === "CRITICAL" ? "#f43f5e" : entry.name === "HIGH" ? "#fb923c" : entry.name === "MEDIUM" ? "#facc15" : "#34d399"
                    }
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>

      <div className="grid lg:grid-cols-2 gap-5 mt-5">
        <Card
          title="Release Readiness"
          subtitle="Cybersecurity release gate status per release"
          actions={
            <button className="btn-ghost text-xs" onClick={() => navigate("/app/releases")}>
              Open Release Gate →
            </button>
          }
        >
          <Table headers={["Release", "ECU", "Status", "Gate"]}>
            {data.release_readiness.map((r) => (
              <tr key={r.id} className="hover:bg-ink-850/60 cursor-pointer" onClick={() => navigate("/app/releases")}>
                <td className="td font-mono">{r.version}</td>
                <td className="td">ECU #{r.ecu_id}</td>
                <td className="td">
                  <StatusBadge status={r.status} />
                </td>
                <td className="td">
                  <GateBadge result={r.gate_result} />
                </td>
              </tr>
            ))}
          </Table>
        </Card>

        <Card
          title="Recent Changes"
          subtitle="Latest change records with impact analysis level"
          actions={
            <button className="btn-ghost text-xs" onClick={() => navigate("/app/changes")}>
              Change Impact →
            </button>
          }
        >
          <Table headers={["#", "Change", "Type", "Impact"]}>
            {data.recent_changes.map((ch) => (
              <tr key={ch.id} className="hover:bg-ink-850/60 cursor-pointer" onClick={() => navigate("/app/changes")}>
                <td className="td font-mono text-slate-400">#{ch.id}</td>
                <td className="td">
                  <div className="truncate max-w-[220px]">{ch.description}</div>
                </td>
                <td className="td text-xs">{ch.change_type.replaceAll("_", " ")}</td>
                <td className="td">{ch.impact_level ? <RiskBadge level={ch.impact_level} /> : <span className="text-slate-500 text-xs">pending</span>}</td>
              </tr>
            ))}
          </Table>
        </Card>
      </div>

      <div className="grid lg:grid-cols-3 gap-5 mt-5">
        <Card title="Critical Vulnerabilities" subtitle="Blocking release gate items">
          {data.critical_vulnerability_list.length === 0 ? (
            <p className="text-sm text-slate-400">No open critical/high vulnerabilities.</p>
          ) : (
            <ul className="space-y-2">
              {data.critical_vulnerability_list.map((v) => (
                <li key={v.id} className="flex items-center justify-between rounded-lg bg-rose-950/30 border border-rose-500/30 px-3 py-2">
                  <span className="font-mono text-rose-200 text-sm">{v.cve_id}</span>
                  <span className="text-xs text-rose-300">CVSS {v.cvss_score}</span>
                </li>
              ))}
            </ul>
          )}
        </Card>

        <Card title="Failed Tests" subtitle="Cybersecurity verification failures">
          {data.failed_test_list.length === 0 ? (
            <p className="text-sm text-slate-400">No failed tests.</p>
          ) : (
            <ul className="space-y-2">
              {data.failed_test_list.map((t) => (
                <li key={t.id} className="rounded-lg bg-amber-950/30 border border-amber-500/30 px-3 py-2 text-sm text-amber-200">
                  {t.name}
                </li>
              ))}
            </ul>
          )}
        </Card>

        <Card title="Missing Evidence" subtitle="Requirements without linked evidence">
          {data.missing_evidence_list.length === 0 ? (
            <p className="text-sm text-slate-400">All requirements have evidence.</p>
          ) : (
            <ul className="space-y-2">
              {data.missing_evidence_list.map((r) => (
                <li
                  key={r.id}
                  className="flex items-center justify-between rounded-lg bg-ink-850 border border-ink-700 px-3 py-2 text-sm cursor-pointer hover:border-accent/40"
                  onClick={() => navigate(`/app/requirements/${r.id}`)}
                >
                  <span className="font-mono text-cyan-300">{r.requirement_id}</span>
                  <span className="text-slate-400 truncate max-w-[140px]">{r.title}</span>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>
    </div>
  );
};
