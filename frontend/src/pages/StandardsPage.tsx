import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api, Control, Mechanism, Standard } from "../api/client";
import { Badge, Card, ErrorBox, PageHeader, Spinner, Table } from "../components/ui";

type Tab = "ISO21434" | "R155" | "R156" | "NIST80053" | "AUTOSAR";

const TAB_INFO: Record<Tab, string> = {
  ISO21434:
    "ISO/SAE 21434 engineering concepts (item definition, asset, TARA, goal, requirement, verification, validation, cybersecurity case, evidence) represented as a mapping layer. AutoCyberGraph is not an official implementation of the standard.",
  R155:
    "UNECE R155 process/risk clause mapping layer: evidence → process → risk → control → vehicle/ECU. The application does not automatically prove regulatory compliance.",
  R156:
    "UNECE R156 software update evidence workflow: release → changed components → security impact → testing → approval → evidence.",
  NIST80053:
    "NIST SP 800-53 as a security-control catalog and mapping layer (AC, AU, CM, IA, IR, RA, SA, SC, SI, SR). NIST is not an automotive regulation. Representative controls only — see official NIST material for the full catalog.",
  AUTOSAR:
    "AUTOSAR security mechanism catalog: SecOC, Crypto Service Manager, Crypto Interface, Crypto Driver, HSM, Secure Boot, Secure Diagnostics, Key Management, Authentication, Freshness and cryptographic services.",
};

export const StandardsPage: React.FC = () => {
  const [tab, setTab] = useState<Tab>("ISO21434");

  const standards = useQuery<Standard[]>({ queryKey: ["standards"], queryFn: () => api<Standard[]>("/api/standards") });
  const controls = useQuery<Control[]>({ queryKey: ["controls"], queryFn: () => api<Control[]>("/api/controls") });
  const mechanisms = useQuery<Mechanism[]>({ queryKey: ["mechanisms"], queryFn: () => api<Mechanism[]>("/api/autosar/mechanisms") });

  const std = (standards.data ?? []).find((s) => s.key === tab);
  const filteredControls = (controls.data ?? []).filter((c) => std && c.standard_id === std.id);

  return (
    <div>
      <PageHeader
        title="Standards Mapping"
        subtitle="ISO/SAE 21434 · UNECE R155 · UNECE R156 · NIST SP 800-53 · AUTOSAR Security — reference/mapping concepts only. AutoCyberGraph is not a certification tool or compliance guarantee."
      />

      <div className="flex flex-wrap gap-2 mb-4">
        {(Object.keys(TAB_INFO) as Tab[]).map((t) => (
          <button
            key={t}
            className={`chip border cursor-pointer px-3 py-1.5 ${tab === t ? "bg-accent/20 border-accent/50 text-accent-glow" : "bg-ink-850 border-ink-700 text-slate-400"}`}
            onClick={() => setTab(t)}
          >
            {t === "NIST80053" ? "NIST SP 800-53" : t === "ISO21434" ? "ISO/SAE 21434" : t}
          </button>
        ))}
      </div>

      <Card title={std?.name ?? tab} subtitle={std?.reference_url}>
        <p className="text-sm text-slate-400 leading-relaxed">{TAB_INFO[tab]}</p>
      </Card>

      {tab !== "AUTOSAR" ? (
        <div className="mt-5">
          <Card title="Controls / Concepts" subtitle={`${filteredControls.length} representative entries${std ? ` · ${std.control_count} total` : ""}`}>
            {standards.isLoading || controls.isLoading ? (
              <Spinner />
            ) : controls.error ? (
              <ErrorBox message={controls.error instanceof Error ? controls.error.message : "error"} />
            ) : (
              <Table headers={["ID", "Title", "Category", "Description"]}>
                {filteredControls.map((c) => (
                  <tr key={c.id}>
                    <td className="td font-mono text-cyan-300">{c.control_id}</td>
                    <td className="td text-white">{c.title}</td>
                    <td className="td">
                      <Badge>{c.category}</Badge>
                    </td>
                    <td className="td text-slate-400 max-w-md">{c.description}</td>
                  </tr>
                ))}
              </Table>
            )}
          </Card>
        </div>
      ) : (
        <div className="mt-5">
          <Card title="AUTOSAR Security Mechanisms" subtitle="Click-through catalog — map mechanisms to requirements from the requirement detail page">
            {mechanisms.isLoading ? (
              <Spinner />
            ) : (
              <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {(mechanisms.data ?? []).map((m) => (
                  <div key={m.id} className="rounded-xl border border-ink-700 bg-ink-850/60 p-4">
                    <div className="flex items-center justify-between">
                      <h4 className="font-semibold text-white">{m.name}</h4>
                      <Badge tone="violet">{m.category}</Badge>
                    </div>
                    <p className="text-xs text-slate-400 mt-2 leading-relaxed">{m.description}</p>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      )}
    </div>
  );
};
