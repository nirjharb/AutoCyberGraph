import React, { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, post } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { Badge, Card, Dialog, ErrorBox, Field, Input, PageHeader, RiskBadge, Select, Spinner, StatusBadge, Table, Textarea } from "../components/ui";

interface TaraRow {
  id: number;
  asset_id: number;
  threat_id: number | null;
  reference: string;
  damage_scenario: string;
  threat_scenario: string;
  impact: string;
  impact_level: number;
  attack_feasibility: string;
  feasibility_level: number;
  risk_level: string;
  cybersecurity_goal: string;
  status: string;
}
interface AssetRow {
  id: number;
  name: string;
  ecu_id: number;
  criticality: string;
}

const IMPACTS = ["NEGLIGIBLE", "MINOR", "MODERATE", "MAJOR", "SEVERE"];
const FEASIBILITIES = ["VERY_LOW", "LOW", "MEDIUM", "HIGH", "VERY_HIGH"];

function riskPreview(impact: string, feasibility: string): string {
  const il = IMPACTS.indexOf(impact);
  const fl = FEASIBILITIES.indexOf(feasibility);
  const score = (il + 1) * (fl + 1);
  if (score >= 20) return "CRITICAL";
  if (score >= 12) return "HIGH";
  if (score >= 6) return "MEDIUM";
  return "LOW";
}

export const TaraPage: React.FC = () => {
  const { hasRole } = useAuth();
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [filter, setFilter] = useState("");
  const [form, setForm] = useState({
    asset_id: 0,
    damage_scenario: "",
    threat_scenario: "",
    impact: "MODERATE",
    attack_feasibility: "MEDIUM",
    cybersecurity_goal: "",
    status: "DRAFT",
  });

  const taras = useQuery<TaraRow[]>({ queryKey: ["tara"], queryFn: () => api<TaraRow[]>("/api/tara") });
  const assets = useQuery<AssetRow[]>({ queryKey: ["assets"], queryFn: () => api<AssetRow[]>("/api/assets") });

  const createMutation = useMutation({
    mutationFn: () => post<TaraRow>("/api/tara", form),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tara"] });
      setOpen(false);
    },
  });

  const rows = (taras.data ?? []).filter(
    (t) =>
      !filter ||
      t.reference.toLowerCase().includes(filter.toLowerCase()) ||
      t.risk_level === filter.toUpperCase(),
  );

  return (
    <div>
      <PageHeader
        title="TARA — Threat Analysis & Risk Assessment"
        subtitle="Lightweight TARA workflow with a configurable risk calculation. This is an application risk method — not an official certification methodology (see docs/tara.md)."
        actions={
          hasRole("CYBERSECURITY_ENGINEER", "ARCHITECT") ? (
            <button className="btn-primary" onClick={() => setOpen(true)}>
              + New TARA Scenario
            </button>
          ) : null
        }
      />

      <div className="flex flex-wrap gap-2 mb-4">
        {["", "LOW", "MEDIUM", "HIGH", "CRITICAL"].map((level) => (
          <button
            key={level || "all"}
            className={`chip border cursor-pointer ${filter.toUpperCase() === level || (!level && !filter) ? "bg-accent/20 border-accent/50 text-accent-glow" : "bg-ink-850 border-ink-700 text-slate-400"}`}
            onClick={() => setFilter(level)}
          >
            {level || "ALL"}
          </button>
        ))}
      </div>

      {taras.isLoading && <Spinner />}
      {taras.error && <ErrorBox message={taras.error instanceof Error ? taras.error.message : "error"} />}

      {taras.data && (
        <Card>
          <Table headers={["Ref", "Damage Scenario", "Threat Scenario", "Impact", "Feasibility", "Risk", "Goal", "Status"]}>
            {rows.map((t) => (
              <tr key={t.id} className="hover:bg-ink-850/60">
                <td className="td font-mono text-cyan-300">{t.reference}</td>
                <td className="td max-w-[180px] truncate">{t.damage_scenario}</td>
                <td className="td max-w-[180px] truncate">{t.threat_scenario}</td>
                <td className="td text-xs">
                  {t.impact} <span className="text-slate-500">({t.impact_level})</span>
                </td>
                <td className="td text-xs">
                  {t.attack_feasibility} <span className="text-slate-500">({t.feasibility_level})</span>
                </td>
                <td className="td">
                  <RiskBadge level={t.risk_level} />
                </td>
                <td className="td max-w-[200px] truncate text-slate-400">{t.cybersecurity_goal}</td>
                <td className="td">
                  <StatusBadge status={t.status} />
                </td>
              </tr>
            ))}
          </Table>
        </Card>
      )}

      <Dialog open={open} title="New TARA Scenario" onClose={() => setOpen(false)} wide>
        <div className="space-y-4">
          <Field label="Asset">
            <Select value={form.asset_id} onChange={(e) => setForm({ ...form, asset_id: Number(e.target.value) })}>
              <option value={0}>Select an asset…</option>
              {(assets.data ?? []).map((a) => (
                <option key={a.id} value={a.id}>
                  {a.name} (ECU #{a.ecu_id}, {a.criticality})
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Damage Scenario">
            <Textarea rows={2} value={form.damage_scenario} onChange={(e) => setForm({ ...form, damage_scenario: e.target.value })} placeholder="e.g. Loss of vehicle dynamics integrity" />
          </Field>
          <Field label="Threat Scenario">
            <Textarea rows={2} value={form.threat_scenario} onChange={(e) => setForm({ ...form, threat_scenario: e.target.value })} placeholder="e.g. Attacker injects false speed data over CAN-FD" />
          </Field>
          <div className="grid grid-cols-2 gap-4">
            <Field label="Impact">
              <Select value={form.impact} onChange={(e) => setForm({ ...form, impact: e.target.value })}>
                {IMPACTS.map((i) => (
                  <option key={i}>{i}</option>
                ))}
              </Select>
            </Field>
            <Field label="Attack Feasibility">
              <Select value={form.attack_feasibility} onChange={(e) => setForm({ ...form, attack_feasibility: e.target.value })}>
                {FEASIBILITIES.map((f) => (
                  <option key={f}>{f}</option>
                ))}
              </Select>
            </Field>
          </div>
          <div className="rounded-lg border border-accent/30 bg-accent/10 px-4 py-3 flex items-center justify-between">
            <span className="text-sm text-slate-300">Calculated risk (configurable matrix, impact × feasibility)</span>
            <RiskBadge level={riskPreview(form.impact, form.attack_feasibility)} />
          </div>
          <Field label="Cybersecurity Goal">
            <Input value={form.cybersecurity_goal} onChange={(e) => setForm({ ...form, cybersecurity_goal: e.target.value })} placeholder="e.g. Prevent spoofing of safety-relevant messages" />
          </Field>
          <Field label="Status">
            <Select value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}>
              <option>DRAFT</option>
              <option>REVIEWED</option>
              <option>APPROVED</option>
            </Select>
          </Field>
          {createMutation.error && <ErrorBox message={createMutation.error instanceof Error ? createMutation.error.message : "failed"} />}
          <div className="flex justify-end gap-2 pt-2">
            <button className="btn-ghost" onClick={() => setOpen(false)}>Cancel</button>
            <button
              className="btn-primary"
              disabled={!form.asset_id || !form.damage_scenario || createMutation.isPending}
              onClick={() => createMutation.mutate()}
            >
              {createMutation.isPending ? "Creating…" : "Create TARA Scenario"}
            </button>
          </div>
        </div>
      </Dialog>
    </div>
  );
};
