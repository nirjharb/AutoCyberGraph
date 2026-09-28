import React from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

const NAV_SECTIONS: { label: string; items: { to: string; label: string; roles?: string[] }[] }[] = [
  {
    label: "Overview",
    items: [
      { to: "/app", label: "◈ Dashboard" },
      { to: "/app/vehicles", label: "⛨ Vehicle Architecture" },
    ],
  },
  {
    label: "Cybersecurity Engineering",
    items: [
      { to: "/app/tara", label: "◉ TARA" },
      { to: "/app/requirements", label: "≣ Requirements" },
      { to: "/app/trace", label: "🕸 Evidence Graph" },
      { to: "/app/standards", label: "§ Standards Mapping" },
    ],
  },
  {
    label: "Supply Chain & Quality",
    items: [
      { to: "/app/vulnerabilities", label: "⚠ Vulnerabilities & SBOM" },
      { to: "/app/tests", label: "✓ Tests" },
      { to: "/app/evidence", label: "🗄 Evidence" },
      { to: "/app/releases", label: "🚀 Release Gate" },
    ],
  },
  {
    label: "Change & Advisory",
    items: [
      { to: "/app/changes", label: "⟲ Change Impact" },
      { to: "/app/advisor", label: "✦ CyberAdvisor" },
      { to: "/app/suppliers", label: "⇄ Supplier Portal" },
    ],
  },
];

export const Layout: React.FC = () => {
  const { user, logout, hasRole } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex">
      <aside className="w-64 shrink-0 border-r border-ink-700/60 bg-ink-900/60 backdrop-blur-sm hidden lg:flex flex-col">
        <div className="p-5 border-b border-ink-700/60">
          <NavLink to="/" className="flex items-center gap-2.5">
            <span className="h-9 w-9 rounded-lg bg-accent/15 border border-accent/40 flex items-center justify-center text-accent font-bold text-lg">A</span>
            <div>
              <div className="font-bold text-white leading-tight">AutoCyberGraph</div>
              <div className="text-[10px] uppercase tracking-widest text-accent/80">Digital Thread</div>
            </div>
          </NavLink>
        </div>
        <nav className="flex-1 overflow-y-auto p-3 space-y-5">
          {NAV_SECTIONS.map((section) => (
            <div key={section.label}>
              <div className="px-3 mb-1.5 text-[10px] font-bold uppercase tracking-widest text-slate-500">{section.label}</div>
              <div className="space-y-0.5">
                {section.items
                  .filter((item) => !item.roles || hasRole(...item.roles))
                  .map((item) => (
                    <NavLink
                      key={item.to}
                      to={item.to}
                      end={item.to === "/app"}
                      className={({ isActive }) =>
                        `block rounded-lg px-3 py-2 text-sm transition-colors ${
                          isActive
                            ? "bg-accent/15 text-accent-glow font-semibold border border-accent/30"
                            : "text-slate-300 hover:bg-ink-800/80 hover:text-white"
                        }`
                      }
                    >
                      {item.label}
                    </NavLink>
                  ))}
              </div>
            </div>
          ))}
        </nav>
        <div className="p-4 border-t border-ink-700/60">
          <div className="text-sm font-semibold text-white truncate">{user?.name}</div>
          <div className="text-xs text-slate-400 truncate">{user?.role}</div>
          <button
            className="btn-ghost w-full mt-3 justify-center text-xs"
            onClick={() => {
              logout();
              navigate("/login");
            }}
          >
            Sign out
          </button>
        </div>
      </aside>

      <div className="flex-1 min-w-0 flex flex-col">
        <header className="lg:hidden flex items-center justify-between px-4 py-3 border-b border-ink-700/60 bg-ink-900/80 sticky top-0 z-40">
          <span className="font-bold text-white">AutoCyberGraph</span>
          <button className="btn-ghost text-xs" onClick={() => { logout(); navigate("/login"); }}>
            Sign out
          </button>
        </header>
        <main className="flex-1 p-5 lg:p-8 max-w-[1400px] w-full mx-auto">
          <Outlet />
        </main>
        <footer className="px-8 py-4 text-xs text-slate-500 border-t border-ink-800">
          AutoCyberGraph is an engineering and evidence-management platform. It does not provide legal, regulatory,
          certification, or compliance advice.
        </footer>
      </div>
    </div>
  );
};
