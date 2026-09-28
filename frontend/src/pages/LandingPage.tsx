import React from "react";
import { Link } from "react-router-dom";

const Section: React.FC<{ id: string; eyebrow: string; title: string; children: React.ReactNode; invert?: boolean }> = ({
  id,
  eyebrow,
  title,
  children,
  invert,
}) => (
  <section id={id} className={`py-16 border-t border-ink-800 ${invert ? "bg-ink-900/40" : ""}`}>
    <div className="max-w-6xl mx-auto px-6">
      <div className="text-xs font-bold uppercase tracking-[0.25em] text-accent mb-3">{eyebrow}</div>
      <h2 className="text-3xl font-bold text-white mb-6 tracking-tight">{title}</h2>
      <div className="text-slate-300 leading-relaxed space-y-4 max-w-4xl">{children}</div>
    </div>
  </section>
);

const FeatureCard: React.FC<{ icon: string; title: string; children: React.ReactNode }> = ({ icon, title, children }) => (
  <div className="card p-6 hover:border-accent/40 transition-colors">
    <div className="text-2xl mb-3">{icon}</div>
    <h3 className="text-lg font-semibold text-white mb-2">{title}</h3>
    <p className="text-sm text-slate-400 leading-relaxed">{children}</p>
  </div>
);

export const LandingPage: React.FC = () => (
  <div className="min-h-screen">
    {/* Header */}
    <header className="border-b border-ink-800/80 bg-ink-950/80 backdrop-blur sticky top-0 z-40">
      <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="h-10 w-10 rounded-xl bg-accent/15 border border-accent/40 flex items-center justify-center text-accent font-bold text-xl">A</span>
          <div>
            <div className="font-bold text-white leading-tight">AutoCyberGraph</div>
            <div className="text-[10px] uppercase tracking-[0.2em] text-accent/80">Automotive Cybersecurity Digital Thread</div>
          </div>
        </div>
        <nav className="hidden md:flex items-center gap-6 text-sm text-slate-300">
          <a href="#problem" className="hover:text-white">Problem</a>
          <a href="#thread" className="hover:text-white">Digital Thread</a>
          <a href="#impact" className="hover:text-white">Change Impact</a>
          <a href="#gate" className="hover:text-white">Release Gate</a>
          <a href="#demo" className="hover:text-white">Demo</a>
          <Link to="/login" className="btn-primary">Open Platform</Link>
        </nav>
      </div>
    </header>

    {/* Hero */}
    <div className="relative overflow-hidden">
      <div className="absolute inset-0 opacity-[0.15]" style={{
        backgroundImage:
          "linear-gradient(rgba(34,211,238,0.25) 1px, transparent 1px), linear-gradient(90deg, rgba(34,211,238,0.25) 1px, transparent 1px)",
        backgroundSize: "48px 48px",
        maskImage: "radial-gradient(ellipse at 50% 0%, black 30%, transparent 75%)",
      }} />
      <div className="max-w-6xl mx-auto px-6 pt-24 pb-20 relative">
        <div className="max-w-3xl">
          <div className="inline-flex items-center gap-2 rounded-full border border-accent/30 bg-accent/10 px-4 py-1.5 text-xs font-semibold text-accent-glow mb-8">
            <span className="h-1.5 w-1.5 rounded-full bg-accent animate-pulse" />
            Open-source prototype · ISO/SAE 21434 · UNECE R155 / R156 · NIST SP 800-53 · AUTOSAR Security
          </div>
          <h1 className="text-5xl lg:text-6xl font-bold text-white leading-[1.05] tracking-tight">
            Connect Automotive Cybersecurity <span className="text-accent">Risk to Reality</span>.
          </h1>
          <p className="mt-6 text-lg text-slate-300 leading-relaxed">
            AutoCyberGraph creates a continuous cybersecurity digital thread from TARA and requirements to AUTOSAR
            implementation, vulnerabilities, testing and regulatory evidence — so every change answers one question:
            <em className="text-white"> what cybersecurity artifacts does it break?</em>
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link to="/login" className="btn-primary text-base px-6 py-3">Launch Demo Platform</Link>
            <a href="#demo" className="btn-ghost text-base px-6 py-3">3-Minute Demo Flow</a>
            <a href="https://github.com/autocybergraph/autocybergraph" className="btn-ghost text-base px-6 py-3" target="_blank" rel="noreferrer">
              ★ GitHub
            </a>
          </div>
          <p className="mt-6 text-xs text-slate-500 max-w-2xl">
            AutoCyberGraph is an engineering and evidence-management platform. It does not provide legal, regulatory,
            certification, or compliance advice. Standards are represented as reference/mapping concepts only.
          </p>
        </div>
      </div>
    </div>

    {/* Problem / Solution */}
    <Section id="problem" eyebrow="The Problem" title="Cybersecurity artifacts live in disconnected tools">
      <p>
        Automotive teams run TARA in spreadsheets, requirements in DOORS, tests in ALM tools, SBOMs in build pipelines
        and evidence in shared drives. When a crypto library, ECU configuration or CAN message changes, nobody can
        answer — with evidence — which cybersecurity goals, requirements, tests and release evidence are affected.
        Audits become archaeology.
      </p>
    </Section>
    <Section id="solution" eyebrow="The Solution" title="One traceable graph across the cybersecurity lifecycle" invert>
      <p>
        AutoCyberGraph links every engineering object into a single evidence graph: Vehicle → ECU → Software → Asset →
        Threat → TARA → Goal → Requirement → Control → AUTOSAR Mechanism → Test → Vulnerability → Evidence → Release.
        Traceability is not a report you generate — it is the data model.
      </p>
      <div className="grid md:grid-cols-3 gap-4 pt-4">
        <FeatureCard icon="🧵" title="Digital Thread">Bi-directional traceability with missing-link detection on every requirement.</FeatureCard>
        <FeatureCard icon="🛰" title="Impact, Not Guesses">Graph traversal explains <em>why</em> each artifact is affected — via real relationship paths.</FeatureCard>
        <FeatureCard icon="🔐" title="Evidence-First">Release decisions are gate checks with reasons, never a vanity "security score".</FeatureCard>
      </div>
    </Section>

    {/* Digital thread */}
    <Section id="thread" eyebrow="Digital Thread" title="TARA → requirements → AUTOSAR → tests → evidence">
      <pre className="card p-6 text-sm font-mono text-accent-glow overflow-x-auto leading-relaxed">
{`Vehicle → ECU → Software Component → Asset → Threat → TARA → Cybersecurity Goal
        → Requirement → Security Control → AUTOSAR Security Mechanism
        → Test Case → Test Result → Evidence → Release → R155 / R156 / 21434 mapping

Software Component → SBOM → Vulnerability → ECU → Vehicle

Change → Affected Entity → Relationships → TARA → Requirements → Tests
        → Evidence → Release Gate`}
      </pre>
    </Section>

    {/* Change impact */}
    <Section id="impact" eyebrow="Change Impact Analysis" title="The core differentiator" invert>
      <p>
        Introduce a change — a crypto library upgrade, an AUTOSAR configuration edit, a CAN message redefinition, a new
        CVE — and the impact engine traverses the evidence graph to list affected TARA scenarios, requirements, controls,
        mechanisms, tests, evidence and releases.
      </p>
      <p>
        Every affected object carries the <strong className="text-white">graph path</strong> that made it affected.
        Nothing is guessed. Impact level is derived from change weight, TARA risk, open vulnerabilities, ECU criticality
        and release exposure.
      </p>
    </Section>

    {/* Release gate */}
    <Section id="gate" eyebrow="Cybersecurity Release Gate" title="PASS · REVIEW · HOLD — always with reasons">
      <p>
        TARA reviewed · Requirements traced · Tests completed · Critical vulnerabilities resolved · SBOM available ·
        AUTOSAR mappings present · Required evidence available · Security-impact analysis complete.
      </p>
      <p>
        A release does not get a mysterious score. It gets a deterministic verdict and the exact list of failed checks
        blocking it.
      </p>
    </Section>

    {/* Feature grid */}
    <Section id="features" eyebrow="Platform" title="Built for automotive cybersecurity engineers" invert>
      <div className="grid md:grid-cols-3 gap-4 pt-2">
        <FeatureCard icon="🚗" title="Vehicle Architecture">ECU topology with CAN, CAN-FD, Automotive Ethernet and SOME/IP networks. Click an ECU for its full security context.</FeatureCard>
        <FeatureCard icon="◉" title="TARA Workflow">Lightweight, configurable risk calculation (Low→Critical) with goals and derived requirements. Documented method, no false certification claims.</FeatureCard>
        <FeatureCard icon="⚙" title="AUTOSAR Security">SecOC, CSM, CDD, HSM, Secure Boot, Secure Diagnostics, Key Management — mapped to requirements and implementations.</FeatureCard>
        <FeatureCard icon="📦" title="SBOM & Vulnerabilities">CycloneDX and SPDX import, CVE/CVSS tracking, and CVE → Component → ECU → Vehicle reachability.</FeatureCard>
        <FeatureCard icon="§" title="Standards Mapping">ISO/SAE 21434, UNECE R155, R156 and NIST SP 800-53 as mapping layers — honestly positioned as reference concepts.</FeatureCard>
        <FeatureCard icon="✦" title="CyberAdvisor">Grounded Q&A over project data. If the data cannot answer, it says so — it never invents compliance conclusions.</FeatureCard>
      </div>
    </Section>

    {/* Demo */}
    <Section id="demo" eyebrow="Demo Workflow" title="From Gateway ECU to Release Gate in under 3 minutes">
      <ol className="space-y-2 list-decimal list-inside text-slate-300">
        <li>Open <strong className="text-white">Demo EV Platform</strong> → select <strong className="text-white">Gateway ECU</strong> → view security context</li>
        <li>Open its <strong className="text-white">TARA</strong> scenarios and the requirement <strong className="text-white">CS-REQ-001</strong></li>
        <li>Show the <strong className="text-white">AUTOSAR SecOC</strong> mapping, verification tests and evidence</li>
        <li>Inspect the <strong className="text-white">SBOM</strong> and open vulnerability <strong className="text-white">CVE-2025-55555</strong> on the crypto library</li>
        <li>Introduce <strong className="text-white">crypto library v2.4 → v2.5</strong> and run <strong className="text-white">Change Impact Analysis</strong></li>
        <li>See affected TARA, requirements, tests, vulnerabilities and evidence — with reasons</li>
        <li>Run the <strong className="text-white">Cybersecurity Release Gate</strong> → <strong className="text-amber-300">REVIEW / HOLD</strong> and understand exactly why</li>
      </ol>
    </Section>

    {/* Docs / github */}
    <Section id="docs" eyebrow="Open Source" title="Documentation, GitHub, and honest positioning" invert>
      <p>
        The repository ships with architecture documentation, threat model, API reference (OpenAPI), contribution
        guidelines and a full demo dataset. AutoCyberGraph combines concepts from ISO/SAE 21434, UNECE R155/R156,
        NIST SP 800-53 and AUTOSAR security — but it is <strong className="text-white">not</strong> an official
        implementation, certification tool, or compliance guarantee of any of them.
      </p>
      <div className="flex flex-wrap gap-3 pt-2">
        <Link to="/login" className="btn-primary">Open the Platform</Link>
        <a href="https://github.com/autocybergraph/autocybergraph" className="btn-ghost" target="_blank" rel="noreferrer">GitHub Repository</a>
      </div>
    </Section>

    <footer className="border-t border-ink-800 py-10">
      <div className="max-w-6xl mx-auto px-6 text-sm text-slate-500 space-y-2">
        <div className="font-semibold text-slate-300">AutoCyberGraph</div>
        <p>
          AutoCyberGraph is an engineering and evidence-management platform. It does not provide legal, regulatory,
          certification, or compliance advice.
        </p>
        <p>© {new Date().getFullYear()} AutoCyberGraph contributors · Apache-2.0 License</p>
      </div>
    </footer>
  </div>
);
