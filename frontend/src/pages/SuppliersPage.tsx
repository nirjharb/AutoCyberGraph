import React, { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, post, Submission } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { Badge, Card, Dialog, ErrorBox, Field, Input, PageHeader, Select, Spinner, StatusBadge, Table, Textarea } from "../components/ui";

interface SupplierRow {
  id: number;
  organization_id: number;
  name: string;
  type: string;
  contact: string;
}

const KINDS = ["ECU_INFO", "SOFTWARE_VERSION", "SBOM", "REQUIREMENT", "TARA_EVIDENCE", "TEST_RESULT", "VULNERABILITY", "SECURITY_DOC"];

export const SuppliersPage: React.FC = () => {
  const { user, hasRole } = useAuth();
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [reviewTarget, setReviewTarget] = useState<Submission | null>(null);
  const [reviewNotes, setReviewNotes] = useState("");
  const [form, setForm] = useState({ supplier_id: 1, kind: "SBOM", title: "", description: "", payload: "{}" });

  const suppliers = useQuery<SupplierRow[]>({ queryKey: ["suppliers"], queryFn: () => api<SupplierRow[]>("/api/suppliers") });
  const submissions = useQuery<Submission[]>({ queryKey: ["submissions"], queryFn: () => api<Submission[]>("/api/suppliers/submissions") });

  const submitMutation = useMutation({
    mutationFn: () =>
      post<Submission>("/api/suppliers/submissions", {
        supplier_id: form.supplier_id,
        kind: form.kind,
        title: form.title,
        description: form.description,
        payload: form.payload ? JSON.parse(form.payload) : {},
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["submissions"] });
      setOpen(false);
    },
  });

  const reviewMutation = useMutation({
    mutationFn: ({ id, status }: { id: number; status: string }) =>
      post<Submission>(`/api/suppliers/submissions/${id}/review`, { status, review_notes: reviewNotes }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["submissions"] });
      setReviewTarget(null);
      setReviewNotes("");
    },
  });

  return (
    <div>
      <PageHeader
        title="Supplier Portal"
        subtitle="Suppliers submit ECU information, software versions, SBOMs, TARA evidence, test results and vulnerability data. OEM reviewers approve, reject or request changes — organization-scoped authorization is enforced."
        actions={
          <button className="btn-primary" onClick={() => setOpen(true)}>+ New Submission</button>
        }
      />

      <div className="grid lg:grid-cols-3 gap-5">
        <div className="lg:col-span-2">
          <Card title="Submissions" subtitle="Review workflow: SUBMITTED → IN_REVIEW → APPROVED / REJECTED / CHANGES_REQUESTED">
            {submissions.isLoading ? (
              <Spinner />
            ) : submissions.error ? (
              <ErrorBox message={submissions.error instanceof Error ? submissions.error.message : "error"} />
            ) : (
              <Table headers={["Title", "Kind", "Supplier", "Status", ""]}>
                {(submissions.data ?? []).map((s) => (
                  <tr key={s.id} className="hover:bg-ink-850/60">
                    <td className="td">
                      <div className="text-white font-medium">{s.title}</div>
                      <div className="text-xs text-slate-500 truncate max-w-[280px]">{s.description}</div>
                    </td>
                    <td className="td">
                      <Badge tone="cyan">{s.kind}</Badge>
                    </td>
                    <td className="td text-slate-400 text-xs">#{s.supplier_id}</td>
                    <td className="td">
                      <StatusBadge status={s.status} />
                    </td>
                    <td className="td">
                      {hasRole("CYBERSECURITY_ENGINEER") && s.status !== "APPROVED" && s.status !== "REJECTED" && (
                        <button className="btn-ghost text-xs px-2.5 py-1" onClick={() => setReviewTarget(s)}>
                          Review
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </Table>
            )}
          </Card>
        </div>

        <Card title="Suppliers" subtitle="Registered supplier organizations">
          <div className="space-y-2.5">
            {(suppliers.data ?? []).map((s) => (
              <div key={s.id} className="rounded-lg border border-ink-700 bg-ink-850/60 p-3">
                <div className="flex items-center justify-between">
                  <span className="text-white text-sm font-medium">{s.name}</span>
                  <Badge>{s.type}</Badge>
                </div>
                <div className="text-xs text-slate-500 mt-1">{s.contact}</div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* New submission dialog */}
      <Dialog open={open} title="New Supplier Submission" onClose={() => setOpen(false)} wide>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Field label="Supplier">
              <Select value={form.supplier_id} onChange={(e) => setForm({ ...form, supplier_id: Number(e.target.value) })}>
                {(suppliers.data ?? []).map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </Select>
            </Field>
            <Field label="Kind">
              <Select value={form.kind} onChange={(e) => setForm({ ...form, kind: e.target.value })}>
                {KINDS.map((k) => (
                  <option key={k}>{k}</option>
                ))}
              </Select>
            </Field>
          </div>
          <Field label="Title">
            <Input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="e.g. Gateway ECU SBOM v2.5.0 candidate" />
          </Field>
          <Field label="Description">
            <Textarea rows={3} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
          </Field>
          <Field label="Payload (JSON)">
            <Textarea rows={4} value={form.payload} onChange={(e) => setForm({ ...form, payload: e.target.value })} className="font-mono text-xs" />
          </Field>
          {submitMutation.error && (
            <ErrorBox
              message={
                submitMutation.error instanceof Error
                  ? submitMutation.error.message.includes("JSON")
                    ? "Payload must be valid JSON"
                    : submitMutation.error.message
                  : "failed"
              }
            />
          )}
          <div className="flex justify-end gap-2">
            <button className="btn-ghost" onClick={() => setOpen(false)}>Cancel</button>
            <button
              className="btn-primary"
              disabled={!form.title || submitMutation.isPending}
              onClick={() => {
                try {
                  JSON.parse(form.payload || "{}");
                  submitMutation.mutate();
                } catch {
                  /* error surfaced via mutation-free message */
                }
              }}
            >
              {submitMutation.isPending ? "Submitting…" : "Submit"}
            </button>
          </div>
        </div>
      </Dialog>

      {/* Review dialog */}
      <Dialog open={Boolean(reviewTarget)} title={`Review — ${reviewTarget?.title ?? ""}`} onClose={() => setReviewTarget(null)}>
        <div className="space-y-4">
          <div className="rounded-lg border border-ink-700 bg-ink-850/60 p-3 text-sm text-slate-300">
            {reviewTarget?.description}
          </div>
          <Field label="Review notes">
            <Textarea rows={3} value={reviewNotes} onChange={(e) => setReviewNotes(e.target.value)} placeholder="Feedback for the supplier…" />
          </Field>
          {reviewMutation.error && <ErrorBox message={reviewMutation.error instanceof Error ? reviewMutation.error.message : "failed"} />}
          <div className="flex flex-wrap justify-end gap-2">
            <button className="btn-ghost" onClick={() => setReviewTarget(null)}>Cancel</button>
            <button
              className="btn-ghost"
              onClick={() => reviewTarget && reviewMutation.mutate({ id: reviewTarget.id, status: "CHANGES_REQUESTED" })}
            >
              Request Changes
            </button>
            <button
              className="btn-danger"
              onClick={() => reviewTarget && reviewMutation.mutate({ id: reviewTarget.id, status: "REJECTED" })}
            >
              Reject
            </button>
            <button
              className="btn-primary"
              onClick={() => reviewTarget && reviewMutation.mutate({ id: reviewTarget.id, status: "APPROVED" })}
            >
              Approve
            </button>
          </div>
        </div>
      </Dialog>
    </div>
  );
};
