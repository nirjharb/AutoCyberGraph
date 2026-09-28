import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ApiUser, post } from "../api/client";
import { useAuth } from "../auth/AuthContext";

interface TokenResponse {
  access_token: string;
  user: ApiUser;
}

const DEMO_ACCOUNTS = [
  { email: "engineer@autocybergraph.io", role: "Cybersecurity Engineer" },
  { email: "admin@autocybergraph.io", role: "Administrator" },
  { email: "auditor@autocybergraph.io", role: "Auditor" },
  { email: "supplier@autocybergraph.io", role: "Supplier" },
];

export const LoginPage: React.FC = () => {
  const [email, setEmail] = useState("engineer@autocybergraph.io");
  const [password, setPassword] = useState("ChangeMe123!");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const data = await post<TokenResponse>("/api/auth/login", { email, password });
      login(data.access_token, data.user);
      navigate("/app");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <div className="w-full max-w-md">
        <Link to="/" className="flex items-center gap-3 mb-8 justify-center">
          <span className="h-12 w-12 rounded-xl bg-accent/15 border border-accent/40 flex items-center justify-center text-accent font-bold text-2xl">A</span>
          <div>
            <div className="font-bold text-white text-xl leading-tight">AutoCyberGraph</div>
            <div className="text-xs uppercase tracking-[0.2em] text-accent/80">Risk → Reality</div>
          </div>
        </Link>

        <div className="card p-8">
          <h1 className="text-2xl font-bold text-white">Sign in</h1>
          <p className="text-slate-400 text-sm mt-1">Access the cybersecurity digital thread workspace.</p>

          <form onSubmit={submit} className="mt-6 space-y-4">
            <label className="block">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Email</span>
              <input className="input mt-1.5" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
            </label>
            <label className="block">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Password</span>
              <input className="input mt-1.5" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
            </label>
            {error && <div className="rounded-lg border border-rose-500/40 bg-rose-950/40 text-rose-200 text-sm px-3 py-2">{error}</div>}
            <button className="btn-primary w-full justify-center" disabled={busy}>
              {busy ? "Signing in…" : "Sign in"}
            </button>
          </form>

          <div className="mt-6 pt-5 border-t border-ink-700">
            <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Demo accounts (password: ChangeMe123!)</div>
            <div className="grid grid-cols-1 gap-1.5">
              {DEMO_ACCOUNTS.map((acct) => (
                <button
                  key={acct.email}
                  type="button"
                  className="flex items-center justify-between rounded-lg bg-ink-850/80 border border-ink-700 px-3 py-2 text-xs hover:border-accent/40 transition-colors"
                  onClick={() => {
                    setEmail(acct.email);
                    setPassword("ChangeMe123!");
                  }}
                >
                  <span className="font-mono text-slate-300">{acct.email}</span>
                  <span className="text-slate-500">{acct.role}</span>
                </button>
              ))}
            </div>
          </div>
        </div>

        <p className="text-center text-xs text-slate-500 mt-6">
          Engineering & evidence platform — not a certification or compliance tool.
        </p>
      </div>
    </div>
  );
};
