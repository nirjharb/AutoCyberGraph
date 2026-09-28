import React, { useRef, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { post } from "../api/client";
import { Badge, Card, ErrorBox, PageHeader } from "../components/ui";

interface AdvisorAnswer {
  question: string;
  intent: string;
  answer: string;
  data: unknown;
  grounded: boolean;
  links: { type: string; id: number }[];
}

const SUGGESTIONS = [
  "Which requirements are missing evidence?",
  "What happens if Gateway ECU changes?",
  "Which vulnerabilities affect ADAS ECU?",
  "Which TARA scenarios are connected to Gateway ECU?",
  "Which AUTOSAR mechanisms mitigate CS-REQ-001?",
  "Can release 2.4.0 pass the cybersecurity release gate?",
  "Which tests failed?",
  "What is the release readiness?",
];

interface ChatEntry {
  role: "user" | "advisor";
  text: string;
  answer?: AdvisorAnswer;
}

export const AdvisorPage: React.FC = () => {
  const navigate = useNavigate();
  const [question, setQuestion] = useState("");
  const [chat, setChat] = useState<ChatEntry[]>([]);
  const bottomRef = useRef<HTMLDivElement>(null);

  const askMutation = useMutation({
    mutationFn: (q: string) => post<AdvisorAnswer>("/api/advisor/ask", { question: q }),
    onSuccess: (answer) => {
      setChat((prev) => [...prev, { role: "user", text: answer.question }, { role: "advisor", text: answer.answer, answer }]);
      setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: "smooth" }), 50);
    },
  });

  const ask = (q: string) => {
    if (!q.trim()) return;
    askMutation.mutate(q.trim());
    setQuestion("");
  };

  return (
    <div>
      <PageHeader
        title="CyberAdvisor"
        subtitle="AI assistant grounded strictly in project data. If the database cannot determine an answer, it says: “Insufficient evidence in the project database.” It never invents compliance conclusions."
      />

      <div className="grid lg:grid-cols-4 gap-5">
        <div className="lg:col-span-3">
          <Card>
            <div className="space-y-4 min-h-[380px] max-h-[560px] overflow-y-auto pr-1">
              {chat.length === 0 && (
                <div className="text-center py-14">
                  <div className="text-4xl mb-3">✦</div>
                  <h3 className="text-lg font-semibold text-white">Ask about your cybersecurity project</h3>
                  <p className="text-sm text-slate-400 mt-1">
                    Answers include links to the real artifacts behind them.
                  </p>
                </div>
              )}
              {chat.map((entry, i) => (
                <div key={i} className={entry.role === "user" ? "flex justify-end" : "flex justify-start"}>
                  <div
                    className={
                      entry.role === "user"
                        ? "rounded-xl bg-accent/20 border border-accent/40 text-accent-glow px-4 py-2.5 max-w-[80%]"
                        : "rounded-xl bg-ink-850 border border-ink-700 text-slate-200 px-4 py-2.5 max-w-[85%]"
                    }
                  >
                    {entry.role === "advisor" && (
                      <div className="flex items-center gap-2 mb-1.5">
                        <span className="text-accent text-sm font-bold">✦ CyberAdvisor</span>
                        {entry.answer && <Badge tone={entry.answer.grounded ? "green" : "amber"}>{entry.answer.intent}</Badge>}
                      </div>
                    )}
                    <div className="text-sm leading-relaxed whitespace-pre-wrap">{entry.text}</div>
                    {entry.answer && entry.answer.links.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 mt-2.5">
                        {entry.answer.links.slice(0, 8).map((link, j) => (
                          <button
                            key={j}
                            className="chip bg-ink-800 border border-ink-700 text-slate-300 hover:border-accent/50"
                            onClick={() => {
                              const routeByType: Record<string, string> = {
                                requirement: `/app/requirements/${link.id}`,
                                CybersecurityRequirement: `/app/requirements/${link.id}`,
                                Release: "/app/releases",
                                Vulnerability: "/app/vulnerabilities",
                                TARA: "/app/tara",
                                ECU: `/app/ecus/${link.id}`,
                                TestCase: "/app/tests",
                                AutosarMechanism: "/app/standards",
                              };
                              const route = routeByType[link.type];
                              if (route) navigate(route);
                            }}
                          >
                            {link.type} #{link.id} ↗
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}
              {askMutation.isPending && (
                <div className="flex items-center gap-2 text-slate-400 text-sm">
                  <span className="h-4 w-4 rounded-full border-2 border-accent border-t-transparent animate-spin" />
                  Consulting project data…
                </div>
              )}
              <div ref={bottomRef} />
            </div>

            <form
              className="flex gap-2 mt-4 pt-4 border-t border-ink-700"
              onSubmit={(e) => {
                e.preventDefault();
                ask(question);
              }}
            >
              <input
                className="input"
                placeholder="Ask a question about requirements, TARA, vulnerabilities, changes, releases…"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
              />
              <button className="btn-primary shrink-0" disabled={askMutation.isPending || !question.trim()}>
                Ask
              </button>
            </form>
            {askMutation.error && (
              <div className="mt-3">
                <ErrorBox message={askMutation.error instanceof Error ? askMutation.error.message : "failed"} />
              </div>
            )}
          </Card>
        </div>

        <Card title="Example questions" subtitle="Grounded in the demo dataset">
          <div className="space-y-2">
            {SUGGESTIONS.map((q) => (
              <button
                key={q}
                className="w-full text-left rounded-lg border border-ink-700 bg-ink-850/60 px-3 py-2.5 text-xs text-slate-300 hover:border-accent/40 transition-colors"
                onClick={() => ask(q)}
              >
                {q}
              </button>
            ))}
          </div>
          <div className="mt-4 rounded-lg border border-ink-700 bg-ink-950/50 p-3">
            <div className="text-xs text-slate-500 leading-relaxed">
              CyberAdvisor answers are computed from live database queries. It will not fabricate compliance conclusions
              or certification status.
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};
