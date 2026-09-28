import React from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api, ECU, Network, Vehicle } from "../api/client";
import { Badge, Card, ErrorBox, PageHeader, Spinner, Table } from "../components/ui";

interface Architecture {
  vehicle: Vehicle;
  ecus: ECU[];
  networks: Network[];
}

const NETWORK_COLORS: Record<string, string> = {
  "CAN": "#22d3ee",
  "CAN-FD": "#a78bfa",
  "Automotive Ethernet": "#34d399",
  "SOME/IP": "#fb923c",
};

export const VehicleDetailPage: React.FC = () => {
  const { vehicleId } = useParams();
  const navigate = useNavigate();
  const { data, isLoading, error } = useQuery<Architecture>({
    queryKey: ["architecture", vehicleId],
    queryFn: () => api<Architecture>(`/api/vehicles/${vehicleId}/architecture`),
  });

  if (isLoading) return <Spinner label="Loading vehicle architecture…" />;
  if (error || !data) return <ErrorBox message={error instanceof Error ? error.message : "Failed to load"} />;

  const { vehicle, ecus, networks } = data;

  return (
    <div>
      <PageHeader
        title={vehicle.name}
        subtitle={`${vehicle.model} · platform ${vehicle.platform} · v${vehicle.version}`}
        actions={<Link className="btn-ghost" to="/app/vehicles">← All vehicles</Link>}
      />

      <div className="grid lg:grid-cols-3 gap-5">
        {/* Architecture diagram */}
        <div className="lg:col-span-2">
          <Card title="ECU Architecture" subtitle="Click an ECU to open its security context">
            <div className="rounded-xl bg-ink-950/60 border border-ink-700/60 p-4 overflow-x-auto">
              <svg viewBox="0 0 760 420" className="w-full min-w-[640px]">
                {/* vehicle node */}
                <rect x="280" y="16" width="200" height="52" rx="10" fill="#13202e" stroke="#22d3ee" strokeWidth="1.5" />
                <text x="380" y="40" textAnchor="middle" fill="#e2e8f0" fontSize="15" fontWeight="700">{vehicle.name}</text>
                <text x="380" y="58" textAnchor="middle" fill="#64748b" fontSize="10">{vehicle.platform}</text>

                {/* network bus lines */}
                {networks.map((net, i) => {
                  const color = NETWORK_COLORS[net.network_type] ?? "#64748b";
                  const y = 130 + i * 62;
                  return (
                    <g key={net.id}>
                      <line x1="80" y1={y} x2="680" y2={y} stroke={color} strokeWidth="2" strokeDasharray={i % 2 ? "6 4" : "0"} opacity="0.65" />
                      <rect x="80" y={y - 11} width={12 + net.network_type.length * 6.2} height="22" rx="5" fill="#0f1722" stroke={color} />
                      <text x={86} y={y + 4} fill={color} fontSize="10" fontWeight="600">{net.network_type}</text>
                    </g>
                  );
                })}

                {/* ECU nodes positioned on bus lines */}
                {ecus.map((ecu, idx) => {
                  const x = 110 + (idx % 5) * 130;
                  const attached = networks.filter((n) => n.ecu_ids.includes(ecu.id));
                  const y = attached.length ? 130 + ((networks.indexOf(attached[0]) % 4) * 62) + 28 : 330;
                  return (
                    <g key={ecu.id} className="cursor-pointer" onClick={() => navigate(`/app/ecus/${ecu.id}`)}>
                      <rect x={x} y={y} width="118" height="46" rx="8" fill="#182938" stroke={ecu.criticality === "HIGH" ? "#fb923c" : "#22d3ee"} strokeWidth="1.2" />
                      <text x={x + 59} y={y + 19} textAnchor="middle" fill="#f1f5f9" fontSize="10.5" fontWeight="600">{ecu.name.replace(" ECU", "")}</text>
                      <text x={x + 59} y={y + 35} textAnchor="middle" fill="#64748b" fontSize="8.5">v{ecu.software_version}</text>
                    </g>
                  );
                })}
              </svg>
            </div>
            <div className="flex flex-wrap gap-3 mt-4">
              {Object.entries(NETWORK_COLORS).map(([name, color]) => (
                <span key={name} className="inline-flex items-center gap-1.5 text-xs text-slate-400">
                  <span className="h-2.5 w-2.5 rounded-full" style={{ background: color }} /> {name}
                </span>
              ))}
            </div>
          </Card>
        </div>

        {/* Networks */}
        <Card title="Networks" subtitle="In-vehicle bus segments">
          <div className="space-y-3">
            {networks.map((net) => (
              <div key={net.id} className="rounded-lg border border-ink-700 bg-ink-850/60 p-3">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-white text-sm">{net.name}</span>
                  <Badge tone="cyan">{net.network_type}</Badge>
                </div>
                <p className="text-xs text-slate-400 mt-1">{net.description}</p>
                <div className="flex flex-wrap gap-1.5 mt-2">
                  {net.ecu_ids.map((id) => {
                    const ecu = ecus.find((e) => e.id === id);
                    return ecu ? (
                      <button key={id} className="chip bg-ink-800 text-slate-300 border border-ink-700 hover:border-accent/50" onClick={() => navigate(`/app/ecus/${id}`)}>
                        {ecu.name}
                      </button>
                    ) : null;
                  })}
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <div className="mt-5">
        <Card title="ECUs" subtitle="Click a row for the ECU security context">
          <Table headers={["ECU", "Type", "Supplier", "HW", "SW", "Criticality", "Status"]}>
            {ecus.map((ecu) => (
              <tr key={ecu.id} className="hover:bg-ink-850/60 cursor-pointer" onClick={() => navigate(`/app/ecus/${ecu.id}`)}>
                <td className="td font-semibold text-white">{ecu.name}</td>
                <td className="td">{ecu.ecu_type}</td>
                <td className="td text-slate-400">{ecu.supplier}</td>
                <td className="td font-mono text-xs">{ecu.hardware_version}</td>
                <td className="td font-mono text-xs text-cyan-300">{ecu.software_version}</td>
                <td className="td">
                  <Badge tone={ecu.criticality === "HIGH" ? "amber" : "slate"}>{ecu.criticality}</Badge>
                </td>
                <td className="td text-slate-400">{ecu.status}</td>
              </tr>
            ))}
          </Table>
        </Card>
      </div>
    </div>
  );
};
