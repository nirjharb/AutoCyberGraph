import { chromium } from "playwright";

const BASE = process.env.DEMO_BASE_URL || "http://localhost:8000";
const OUT = "../docs/images";

const run = async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

  // Login
  await page.goto(`${BASE}/login`, { waitUntil: "networkidle" });
  await page.getByRole("button", { name: "Sign in" }).click();
  await page.waitForURL("**/app", { timeout: 15000 });

  // Change impact — viewport shot focused on the impact report
  await page.goto(`${BASE}/app/changes`, { waitUntil: "networkidle" });
  await page.getByRole("button", { name: /Analyze/ }).first().click();
  await page.waitForTimeout(2500);
  const bucket = page.getByRole("button", { name: /^Requirements$/ }).first();
  if (await bucket.count()) await bucket.click();
  await page.waitForTimeout(500);
  await page.screenshot({ path: `${OUT}/08-change-impact.png` });
  console.log("✓ 08-change-impact (viewport)");

  // Release gate
  await page.goto(`${BASE}/app/releases`, { waitUntil: "networkidle" });
  await page.getByRole("button", { name: /Evaluate Gate/ }).first().click();
  await page.waitForTimeout(1800);
  await page.screenshot({ path: `${OUT}/09-release-gate.png` });
  console.log("✓ 09-release-gate (viewport)");

  // Advisor
  await page.goto(`${BASE}/app/advisor`, { waitUntil: "networkidle" });
  await page.getByText("What happens if Gateway ECU changes?").click();
  await page.waitForTimeout(2200);
  await page.screenshot({ path: `${OUT}/10-cyberadvisor.png` });
  console.log("✓ 10-cyberadvisor (viewport)");

  // Gateway ECU — viewport
  await page.goto(`${BASE}/app/ecus/1`, { waitUntil: "networkidle" });
  await page.waitForTimeout(1200);
  await page.screenshot({ path: `${OUT}/05-gateway-ecu-context.png` });
  console.log("✓ 05-gateway-ecu-context (viewport)");

  // Requirement traceability — viewport
  await page.goto(`${BASE}/app/requirements/1`, { waitUntil: "networkidle" });
  await page.waitForTimeout(1200);
  await page.screenshot({ path: `${OUT}/06-requirement-traceability.png` });
  console.log("✓ 06-requirement-traceability (viewport)");

  await browser.close();
};

run().catch((e) => { console.error(e); process.exit(1); });
