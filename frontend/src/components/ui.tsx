import React from "react";

// ------------------------------- primitives -------------------------------
export const Card: React.FC<{ title?: React.ReactNode; subtitle?: React.ReactNode; actions?: React.ReactNode; className?: string; children: React.ReactNode }> = ({
  title,
  subtitle,
  actions,
  className = "",
  children,
}) => (
  <div className={`card p-5 ${className}`}>
    {(title || actions) && (
      <div className="flex items-start justify-between gap-3 mb-4">
        <div>
          {title && <h3 className="text-lg font-semibold text-white">{title}</h3>}
          {subtitle && <p className="text-sm text-slate-400 mt-0.5">{subtitle}</p>}
        </div>
        {actions && <div className="flex items-center gap-2 shrink-0">{actions}</div>}
      </div>
    )}
    {children}
  </div>
);

export const PageHeader: React.FC<{ title: string; subtitle?: string; actions?: React.ReactNode }> = ({ title, subtitle, actions }) => (
  <div className="flex flex-wrap items-start justify-between gap-4 mb-6">
    <div>
      <h1 className="text-2xl font-bold text-white tracking-tight">{title}</h1>
      {subtitle && <p className="text-slate-400 mt-1 max-w-3xl">{subtitle}</p>}
    </div>
    {actions && <div className="flex items-center gap-2">{actions}</div>}
  </div>
);

export const Badge: React.FC<{ tone?: "slate" | "cyan" | "green" | "amber" | "red" | "violet"; children: React.ReactNode }> = ({
  tone = "slate",
  children,
}) => {
  const tones: Record<string, string> = {
    slate: "bg-slate-500/15 text-slate-300 border border-slate-500/30",
    cyan: "bg-cyan-500/15 text-cyan-300 border border-cyan-500/30",
    green: "bg-emerald-500/15 text-emerald-300 border border-emerald-500/30",
    amber: "bg-amber-500/15 text-amber-300 border border-amber-500/30",
    red: "bg-rose-500/15 text-rose-300 border border-rose-500/30",
    violet: "bg-violet-500/15 text-violet-300 border border-violet-500/30",
  };
  return <span className={`chip ${tones[tone]}`}>{children}</span>;
};

export const RiskBadge: React.FC<{ level: string }> = ({ level }) => {
  const map: Record<string, "green" | "amber" | "red" | "violet"> = {
    LOW: "green",
    MEDIUM: "amber",
    HIGH: "red",
    CRITICAL: "violet",
  };
  const colors: Record<string, string> = {
    LOW: "bg-emerald-500/15 text-emerald-300 border-emerald-500/40",
    MEDIUM: "bg-amber-500/15 text-amber-300 border-amber-500/40",
    HIGH: "bg-orange-500/15 text-orange-300 border-orange-500/40",
    CRITICAL: "bg-rose-500/20 text-rose-300 border-rose-500/50",
  };
  return <span className={`chip border ${colors[level] ?? colors.MEDIUM}`}>{level}</span>;
};

export const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
  const green = ["PASSED", "APPROVED", "RELEASED", "RESOLVED", "PASS", "ACTIVE", "IMPLEMENTED"];
  const red = ["FAILED", "REJECTED", "BLOCKED", "HOLD", "OPEN", "CRITICAL"];
  const amber = ["NOT_RUN", "DRAFT", "IN_REVIEW", "REVIEW", "PLANNED", "IN_PROGRESS", "SUBMITTED", "IN_VALIDATION", "CHANGES_REQUESTED", "MISSING"];
  const tone = green.includes(status) ? "green" : red.includes(status) ? "red" : amber.includes(status) ? "amber" : "slate";
  return <Badge tone={tone as "green" | "red" | "amber" | "slate"}>{status}</Badge>;
};

export const GateBadge: React.FC<{ result: string | null }> = ({ result }) => {
  if (!result) return <Badge tone="slate">NOT EVALUATED</Badge>;
  const tone = result === "PASS" ? "green" : result === "HOLD" ? "red" : "amber";
  return <Badge tone={tone as "green" | "red" | "amber"}>{result}</Badge>;
};

export const Spinner: React.FC<{ label?: string }> = ({ label = "Loading…" }) => (
  <div className="flex items-center gap-3 text-slate-400 py-10 justify-center">
    <span className="h-5 w-5 rounded-full border-2 border-accent border-t-transparent animate-spin" />
    <span className="text-sm">{label}</span>
  </div>
);

export const ErrorBox: React.FC<{ message: string }> = ({ message }) => (
  <div className="card p-4 border-rose-500/40 bg-rose-950/30 text-rose-200 text-sm">
    <strong className="font-semibold">Error:</strong> {message}
  </div>
);

export const EmptyState: React.FC<{ title: string; hint?: string }> = ({ title, hint }) => (
  <div className="text-center py-12 text-slate-400">
    <p className="text-lg font-semibold text-slate-300">{title}</p>
    {hint && <p className="text-sm mt-1">{hint}</p>}
  </div>
);

export const StatCard: React.FC<{ label: string; value: number | string; tone?: "default" | "red" | "amber" | "green" | "cyan"; to?: string; onNavigate?: (to: string) => void }> = ({
  label,
  value,
  tone = "default",
  to,
  onNavigate,
}) => {
  const valueColor =
    tone === "red" ? "text-rose-400" : tone === "amber" ? "text-amber-300" : tone === "green" ? "text-emerald-400" : tone === "cyan" ? "text-cyan-300" : "text-white";
  const clickable = Boolean(to && onNavigate);
  return (
    <div
      className={`card p-4 ${clickable ? "cursor-pointer hover:border-accent/50 transition-colors" : ""}`}
      onClick={() => to && onNavigate?.(to)}
      role={clickable ? "button" : undefined}
    >
      <div className="text-xs uppercase tracking-wider text-slate-400 font-semibold">{label}</div>
      <div className={`text-3xl font-bold mt-1 font-mono ${valueColor}`}>{value}</div>
    </div>
  );
};

// ------------------------------- form controls -------------------------------
export const Input: React.FC<React.InputHTMLAttributes<HTMLInputElement>> = (props) => (
  <input {...props} className={`input ${props.className ?? ""}`} />
);

export const Select: React.FC<React.SelectHTMLAttributes<HTMLSelectElement>> = (props) => (
  <select {...props} className={`input ${props.className ?? ""}`}>
    {props.children}
  </select>
);

export const Textarea: React.FC<React.TextareaHTMLAttributes<HTMLTextAreaElement>> = (props) => (
  <textarea {...props} className={`input ${props.className ?? ""}`} />
);

export const Field: React.FC<{ label: string; children: React.ReactNode }> = ({ label, children }) => (
  <label className="block">
    <span className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">{label}</span>
    {children}
  </label>
);

// ------------------------------- dialog -------------------------------
export const Dialog: React.FC<{ open: boolean; title: string; onClose: () => void; children: React.ReactNode; wide?: boolean }> = ({
  open,
  title,
  onClose,
  children,
  wide,
}) => {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70" onClick={onClose}>
      <div
        className={`card w-full ${wide ? "max-w-3xl" : "max-w-lg"} max-h-[90vh] overflow-y-auto p-6`}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-white">{title}</h2>
          <button className="text-slate-400 hover:text-white text-xl leading-none" onClick={onClose} aria-label="Close">
            ×
          </button>
        </div>
        {children}
      </div>
    </div>
  );
};

// ------------------------------- table -------------------------------
export const Table: React.FC<{ headers: string[]; children: React.ReactNode }> = ({ headers, children }) => (
  <div className="overflow-x-auto rounded-lg border border-ink-700/60">
    <table className="w-full">
      <thead className="bg-ink-850/80">
        <tr>
          {headers.map((h) => (
            <th key={h} className="th">
              {h}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>{children}</tbody>
    </table>
  </div>
);

// ------------------------------- trace checklist -------------------------------
export const TraceChecklist: React.FC<{ checks: { key: string; present: boolean }[] }> = ({ checks }) => (
  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
    {checks.map((c) => (
      <div
        key={c.key}
        className={`flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm border ${
          c.present
            ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-200"
            : "bg-rose-500/10 border-rose-500/30 text-rose-200"
        }`}
      >
        <span className="font-bold">{c.present ? "✓" : "✗"}</span>
        <span>{c.key}</span>
        {!c.present && <span className="ml-auto text-xs opacity-80">missing</span>}
      </div>
    ))}
  </div>
);

// ------------------------------- nav helpers -------------------------------
export function useGo() {
  const [, force] = React.useState(0);
  void force;
  return (to: string) => {
    window.location.hash = "";
    window.history.pushState({}, "", to);
    window.dispatchEvent(new PopStateEvent("popstate"));
  };
}
