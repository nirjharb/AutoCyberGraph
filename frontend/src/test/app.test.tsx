/**
 * Frontend critical-path tests: login, dashboard, traceability display,
 * change impact display, release gate display.
 */
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, beforeEach, vi } from "vitest";
import { AuthProvider } from "../auth/AuthContext";
import { TraceChecklist, RiskBadge, GateBadge } from "../components/ui";
import { LoginPage } from "../pages/LoginPage";
import { RequirementDetailPage } from "../pages/RequirementDetailPage";
import { ReleasesPage } from "../pages/ReleasesPage";
import { ChangesPage } from "../pages/ChangesPage";

const jsonResponse = (data: unknown, status = 200) =>
  new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json" },
  });

function renderApp(ui: React.ReactElement, route = "/") {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <AuthProvider>
        <MemoryRouter initialEntries={[route]}>
          <Routes>
            <Route path="*" element={ui} />
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  localStorage.clear();
  vi.restoreAllMocks();
});

const loginAsEngineer = () => {
  localStorage.setItem(
    "acg_user",
    JSON.stringify({ id: 2, organization_id: 1, name: "Eric", email: "engineer@autocybergraph.io", role: "CYBERSECURITY_ENGINEER", status: "ACTIVE" }),
  );
  localStorage.setItem("acg_token", "test-token");
};

describe("Login flow", () => {
  it("renders demo accounts and logs in", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({
        access_token: "test-token",
        user: { id: 1, organization_id: 1, name: "Eric", email: "engineer@autocybergraph.io", role: "CYBERSECURITY_ENGINEER", status: "ACTIVE" },
      }),
    );
    renderApp(<LoginPage />);
    expect(screen.getByRole("heading", { name: "Sign in" })).toBeInTheDocument();
    expect(screen.getByText("engineer@autocybergraph.io")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    const [url, init] = fetchMock.mock.calls[0];
    expect(String(url)).toBe("/api/auth/login");
    expect(JSON.parse(String((init as RequestInit).body))).toMatchObject({
      email: "engineer@autocybergraph.io",
    });
  });

  it("shows error on invalid credentials", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ detail: "Invalid email or password" }), {
        status: 401,
        headers: { "Content-Type": "application/json" },
      }),
    );
    renderApp(<LoginPage />);
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));
    await waitFor(() => expect(screen.getByText(/Invalid email or password/)).toBeInTheDocument());
  });
});

describe("UI badges", () => {
  it("renders risk levels", () => {
    render(<RiskBadge level="CRITICAL" />);
    expect(screen.getByText("CRITICAL")).toBeInTheDocument();
  });
  it("renders gate results", () => {
    render(<GateBadge result="HOLD" />);
    expect(screen.getByText("HOLD")).toBeInTheDocument();
    render(<GateBadge result={null} />);
    expect(screen.getByText("NOT EVALUATED")).toBeInTheDocument();
  });
});

describe("Requirement traceability display", () => {
  it("shows present and missing links", () => {
    render(
      <TraceChecklist
        checks={[
          { key: "TARA", present: true },
          { key: "Evidence", present: false },
        ]}
      />,
    );
    expect(screen.getByText("✓")).toBeInTheDocument();
    expect(screen.getByText("✗")).toBeInTheDocument();
    expect(screen.getByText("missing")).toBeInTheDocument();
  });

  it("loads requirement detail with missing links badge", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({
        id: 7,
        requirement_id: "CS-REQ-017",
        title: "Critical messages require authenticity",
        description: "test",
        priority: "HIGH",
        status: "APPROVED",
        tara: { id: 1, reference: "TARA-001", risk_level: "HIGH", cybersecurity_goal: "goal" },
        asset: { id: 1, name: "Vehicle speed messages", criticality: "HIGH" },
        threat: null,
        controls: [],
        mechanisms: [{ id: 1, name: "SecOC", category: "Communication protection", notes: "auth + freshness" }],
        tests: [{ id: 1, name: "SecOC verification", status: "PASSED", test_type: "FUNCTIONAL" }],
        test_results: [],
        evidence: [],
        trace_checks: [
          { key: "TARA", present: true },
          { key: "Asset", present: true },
          { key: "Threat", present: false },
          { key: "Control", present: false },
          { key: "AUTOSAR mechanism", present: true },
          { key: "Test", present: true },
          { key: "Evidence", present: false },
        ],
        missing_links: ["Threat", "Control", "Evidence"],
      }),
    );
    renderApp(<RequirementDetailPage />, "/app/requirements/7");
    await waitFor(() => expect(screen.getByText(/CS-REQ-017/)).toBeInTheDocument());
    expect(screen.getByText(/Missing: Threat, Control, Evidence/)).toBeInTheDocument();
    expect(screen.getByText("SecOC")).toBeInTheDocument();
  });
});

describe("Release gate display", () => {
  it("shows gate checks with reasons after evaluation", async () => {
    loginAsEngineer();
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      const url = String(input);
      if (url === "/api/releases" && (!init || !init.method || init.method === "GET")) {
        return jsonResponse([
          {
            id: 1,
            ecu_id: 1,
            version: "2.4.0",
            release_type: "PRODUCTION",
            release_date: "2026-06-01",
            status: "RELEASED",
            gate_result: null,
            gate_reasons: [],
            gate_evaluated_at: null,
          },
        ]);
      }
      if (url === "/api/releases/1/evaluate") {
        return jsonResponse({
          release_id: 1,
          result: "HOLD",
          checks: [
            { key: "vulns_resolved", label: "Critical/high vulnerabilities resolved", passed: false, severity: "BLOCKING", detail: "1 open critical/high vulnerability(ies): CVE-2025-55555" },
            { key: "sbom_available", label: "SBOM available", passed: true, severity: "BLOCKING", detail: "1 SBOM document(s) registered for this ECU." },
          ],
          reasons: ["Open critical/high vulnerabilities: CVE-2025-55555."],
        });
      }
      return jsonResponse({});
    });

    renderApp(<ReleasesPage />, "/app/releases");
    await waitFor(() => expect(screen.getByText("2.4.0")).toBeInTheDocument());

    await userEvent.click(screen.getByRole("button", { name: /Evaluate Gate/ }));
    await waitFor(() => expect(screen.getByText("Gate Evaluation — Release #1")).toBeInTheDocument());
    expect(screen.getByText("HOLD")).toBeInTheDocument();
    expect(screen.getAllByText(/CVE-2025-55555/).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("Verdict reasons")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalled();
  });
});

describe("Change impact display", () => {
  it("records a change and shows affected buckets with reasons", async () => {
    loginAsEngineer();
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      const url = String(input);
      const method = init?.method ?? "GET";
      if (url === "/api/changes" && method === "GET") {
        return jsonResponse([]);
      }
      if (url === "/api/changes" && method === "POST") {
        return jsonResponse({
          id: 42,
          entity_type: "SoftwareComponent",
          entity_id: 1,
          change_type: "CRYPTO_LIBRARY_CHANGE",
          description: "Gateway ECU crypto library v2.4 → v2.5",
          created_at: "2026-09-28T00:00:00Z",
          created_by: "engineer@autocybergraph.io",
          impact_level: null,
          impact_report: [],
          impact_summary: {},
          analyzed_at: null,
          security_assessment: "",
        }, 201);
      }
      if (url === "/api/changes/42/impact") {
        return jsonResponse({
          change_id: 42,
          impact_level: "CRITICAL",
          affected: {
            requirements: [
              {
                entity_type: "CybersecurityRequirement",
                entity_id: 1,
                label: "CybersecurityRequirement:CS-REQ-001",
                depth: 3,
                reason: "[TARA derives cybersecurity requirement] → [Requirement verified by test]",
                path: ["derives", "verified_by"],
              },
            ],
          },
          summary: { requirements: 1 },
          recommended_actions: ["Re-review affected TARA scenarios and confirm risk levels are still valid."],
          rationale: ["Change type CRYPTO_LIBRARY_CHANGE starts at SoftwareComponent:1."],
        });
      }
      return jsonResponse({});
    });

    renderApp(<ChangesPage />, "/app/changes");
    await waitFor(() => expect(screen.getByText("Change Impact Engine")).toBeInTheDocument());

    await userEvent.click(screen.getByRole("button", { name: "+ Record Change" }));
    const dialog = screen.getByText("Record Change").closest(".card") as HTMLElement;
    const desc = within(dialog).getByPlaceholderText(/crypto library/i);
    await userEvent.type(desc, "Gateway ECU crypto library v2.4 → v2.5");
    await userEvent.click(within(dialog).getByRole("button", { name: /Record & Analyze/ }));

    await waitFor(() => expect(screen.getByText("Impact Report — Change #42")).toBeInTheDocument());
    expect(screen.getByText("CRITICAL")).toBeInTheDocument();
    expect(screen.getByText(/Re-review affected TARA scenarios/)).toBeInTheDocument();

    // expand affected bucket to see the reason
    await userEvent.click(screen.getByText("Requirements"));
    await waitFor(() => expect(screen.getByText(/why:/)).toBeInTheDocument());
  });
});
