/**
 * Demo-flow screenshot capture — drives the real AutoCyberGraph UI
 * (same app served at the preview URL) and saves screenshots for docs/README.
 */
import { chromium } from "playwright";
import { mkdirSync } from "fs";

const BASE = process.env.DEMO_BASE_URL || "http://localhost:8000";
const OUT = "../docs/images";
mkdirSync(OUT, { recursive: true });

const shot = async (page, name, full = false) => {
  await page.waitForTimeout(700);
  await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: full });
  console.log("✓", name);
};

const run = async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

  // 1. Landing
  await page.goto(`${BASE}/`, { waitUntil: "networkidle" });
  await shot(page, "01-landing", true);

  // 2. Login
  await page.goto(`${BASE}/login`, { waitUntil: "networkidle" });
  await shot(page, "02-login");

  // sign in as engineer (fields are prefilled)
  await page.getByRole("button", { name: "Sign in" }).click();
  await page.waitForURL("**/app", { timeout: 15000 });
  await page.waitForTimeout(1200);
  await shot(page, "03-dashboard", true);

  // 3. Vehicle architecture
  await page.goto(`${BASE}/app/vehicles`, { waitUntil: "networkidle" });
  await page.getByText("Demo EV Platform").first().click();
  await page.waitForTimeout(1200);
  await shot(page, "04-vehicle-architecture", true);

  // 4. Gateway ECU security context
  await page.getByText("Gateway ECU").first().click();
  await page.waitForTimeout(1200);
  await shot(page, "05-gateway-ecu-context", true);

  // 5. Requirement traceability
  await page.goto(`${BASE}/app/requirements`, { waitUntil: "networkidle" });
  await page.getByText("CS-REQ-001").first().click();
  await page.waitForTimeout(1200);
  await shot(page, "06-requirement-traceability", true);

  // 6. Vulnerability trace
  await page.goto(`${BASE}/app/vulnerabilities`, { waitUntil: "networkidle" });
  await page.getByText("CVE-2025-55555").first().click();
  await page.waitForTimeout(1000);
  await shot(page, "07-vulnerability-trace", true);

  // 7. Change impact — record the flagship change and analyze
  await page.goto(`${BASE}/app/changes`, { waitUntil: "networkidle" });
  await page.getByRole("button", { name: "+ Record Change" }).click();
  await page.getByPlaceholder(/crypto library/i).fill("Gateway ECU crypto library v2.4 → v2.5");
  await page.getByRole("button", { name: /Record & Analyze/ }).click();
  await page.waitForTimeout(2500);
  // expand a bucket to show reasons
  const bucket = page.getByRole("button", { name: /Requirements/ }).first();
  if (await bucket.count()) await bucket.click();
  await page.waitForTimeout(600);
  await shot(page, "08-change-impact", true);

  // 8. Release gate
  await page.goto(`${BASE}/app/releases`, { waitUntil: "networkidle" });
  await page.getByRole("button", { name: /Evaluate Gate/ }).first().click();
  await page.waitForTimeout(1800);
  await shot(page, "09-release-gate", true);

  // 9. CyberAdvisor
  await page.goto(`${BASE}/app/advisor`, { waitUntil: "networkidle" });
  await page.getByText("What happens if Gateway ECU changes?").click();
  await page.waitForTimeout(2200);
  await shot(page, "10-cyberadvisor", true);

  // 10. Evidence graph
  await page.goto(`${BASE}/app/trace`, { waitUntil: "networkidle" });
  await page.selectOption("select", { index: 1 });
  await page.waitForTimeout(2200);
  await shot(page, "11-evidence-graph", true);

  await browser.close();
  console.log("All screenshots saved to", OUT);
};

run().catch((err) => {
  console.error(err);
  process.exit(1);
});
