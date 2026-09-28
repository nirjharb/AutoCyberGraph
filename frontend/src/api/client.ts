/**
 * Typed API client for AutoCyberGraph.
 * Uses relative /api URLs — works behind any deployment origin.
 */

const TOKEN_KEY = "acg_token";
const USER_KEY = "acg_user";

export interface ApiUser {
  id: number;
  organization_id: number;
  name: string;
  email: string;
  role: string;
  status: string;
}

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function getUser(): ApiUser | null {
  const raw = localStorage.getItem(USER_KEY);
  return raw ? (JSON.parse(raw) as ApiUser) : null;
}

export function setSession(token: string, user: ApiUser) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  const token = getToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
    // Some hosted preview proxies strip `Authorization`; the backend also
    // accepts X-Acg-Token and the auth cookie set at login.
    headers["X-Acg-Token"] = token;
  }

  const resp = await fetch(path, { ...options, headers, credentials: "same-origin" });
  if (!resp.ok) {
    let detail = resp.statusText;
    try {
      const body = await resp.json();
      detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail ?? body);
    } catch {
      /* keep statusText */
    }
    throw new ApiError(resp.status, detail);
  }
  return (await resp.json()) as T;
}

export const post = <T,>(path: string, body: unknown) =>
  api<T>(path, { method: "POST", body: JSON.stringify(body) });

export const patch = <T,>(path: string, body: unknown) =>
  api<T>(path, { method: "PATCH", body: JSON.stringify(body) });

// ------------------------- domain types -------------------------
export interface Vehicle {
  id: number;
  name: string;
  model: string;
  platform: string;
  version: string;
  description: string;
}
export interface ECU {
  id: number;
  vehicle_id: number;
  name: string;
  ecu_type: string;
  supplier: string;
  hardware_version: string;
  software_version: string;
  criticality: string;
  status: string;
}
export interface Network {
  id: number;
  vehicle_id: number;
  name: string;
  network_type: string;
  description: string;
  ecu_ids: number[];
}
export interface TARA {
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
export interface Requirement {
  id: number;
  tara_id: number | null;
  requirement_id: string;
  title: string;
  description: string;
  priority: string;
  status: string;
}
export interface Vulnerability {
  id: number;
  component_id: number;
  cve_id: string;
  cvss_score: number;
  severity: string;
  description: string;
  status: string;
  remediation: string;
}
export interface Release {
  id: number;
  ecu_id: number;
  version: string;
  release_type: string;
  release_date: string | null;
  status: string;
  gate_result: string | null;
  gate_reasons: GateCheck[];
  gate_evaluated_at: string | null;
}
export interface GateCheck {
  key: string;
  label: string;
  passed: boolean;
  severity: string;
  detail: string;
}
export interface GateEvaluation {
  release_id: number;
  result: string;
  checks: GateCheck[];
  reasons: string[];
}
export interface Change {
  id: number;
  entity_type: string;
  entity_id: number;
  change_type: string;
  description: string;
  created_at: string;
  created_by: string;
  impact_level: string | null;
  impact_report: { bucket: string; count: number; items: AffectedObject[] }[];
  impact_summary: Record<string, number>;
  analyzed_at: string | null;
  security_assessment: string;
}
export interface AffectedObject {
  entity_type: string;
  entity_id: number;
  label: string;
  depth: number;
  reason: string;
  path: string[];
}
export interface ImpactReport {
  change_id: number;
  impact_level: string;
  affected: Record<string, AffectedObject[]>;
  summary: Record<string, number>;
  recommended_actions: string[];
  rationale: string[];
}
export interface Evidence {
  id: number;
  name: string;
  type: string;
  description: string;
  file_reference: string;
  status: string;
  created_at: string;
  requirement_id: number | null;
  test_result_id: number | null;
  release_id: number | null;
  tara_id: number | null;
}
export interface Mechanism {
  id: number;
  name: string;
  category: string;
  description: string;
}
export interface Standard {
  id: number;
  key: string;
  name: string;
  description: string;
  reference_url: string;
  control_count: number;
}
export interface Control {
  id: number;
  standard_id: number;
  control_id: string;
  title: string;
  description: string;
  category: string;
}
export interface Submission {
  id: number;
  supplier_id: number;
  kind: string;
  title: string;
  description: string;
  payload: Record<string, unknown>;
  status: string;
  review_notes: string;
  created_at: string;
  reviewed_at: string | null;
  created_by: string;
}
export interface DashboardData {
  counts: Record<string, number>;
  risk_distribution: Record<string, number>;
  test_status_counts: Record<string, number>;
  vuln_severity_counts: Record<string, number>;
  recent_changes: {
    id: number;
    entity_type: string;
    entity_id: number;
    change_type: string;
    description: string;
    created_at: string | null;
    impact_level: string | null;
  }[];
  release_readiness: { id: number; version: string; ecu_id: number; status: string; gate_result: string | null }[];
  critical_vulnerability_list: { id: number; cve_id: string; severity: string; cvss_score: number; component_id: number; status: string }[];
  failed_test_list: { id: number; name: string; requirement_id: number | null }[];
  missing_evidence_list: { id: number; requirement_id: string; title: string }[];
}
export interface TraceCheck {
  key: string;
  present: boolean;
}
export interface RequirementDetail {
  id: number;
  requirement_id: string;
  title: string;
  description: string;
  priority: string;
  status: string;
  tara: { id: number; reference: string; risk_level: string; cybersecurity_goal: string } | null;
  asset: { id: number; name: string; criticality: string } | null;
  threat: { id: number; name: string; threat_type: string } | null;
  controls: { id: number; control_id: string; title: string; standard: string }[];
  mechanisms: { id: number; name: string; category: string; notes: string }[];
  tests: { id: number; name: string; status: string; test_type: string }[];
  test_results: { id: number; test_case_id: number; result: string; executed_at: string | null }[];
  evidence: { id: number; name: string; type: string; status: string }[];
  trace_checks: TraceCheck[];
  missing_links: string[];
}
