"use client";

import { useCallback, useEffect, useState } from "react";
import {
  CheckCircle,
  Circle,
  Eye,
  EyeOff,
  FileText,
  Loader,
  ShieldCheck,
  XCircle,
} from "lucide-react";
import {
  listConfirmations,
  getConfirmation,
  createConfirmation,
  updateConfirmation,
  recordConfirmation,
  verifyConfirmation,
  voidConfirmation,
  type ConfirmationSummary,
  type ConfirmationDetail,
  type CreateConfirmationRequest,
} from "@/lib/api-client";

// ── Constants ────────────────────────────────────────────────────────────────

const CONFIRMATION_TYPE_OPTIONS = [
  { value: "flight", label: "Flight" },
  { value: "hotel", label: "Hotel" },
  { value: "insurance", label: "Insurance" },
  { value: "payment", label: "Payment" },
  { value: "other", label: "Other" },
] as const;

const STATUS_META: Record<string, { label: string; color: string; icon: typeof Circle }> = {
  draft: { label: "Draft", color: "text-zinc-400", icon: Circle },
  recorded: { label: "Recorded", color: "text-blue-400", icon: FileText },
  verified: { label: "Verified", color: "text-emerald-400", icon: ShieldCheck },
  voided: { label: "Voided", color: "text-zinc-500", icon: XCircle },
};

const NOTES_MAX_LENGTH = 2000;

// ── Component ────────────────────────────────────────────────────────────────

interface ConfirmationPanelProps {
  tripId: string;
}

// react-doctor-disable-next-line react-doctor/prefer-useReducer — 14 state vars are independent UI concerns
export default function ConfirmationPanel({ tripId }: ConfirmationPanelProps) {
  const [confirmations, setConfirmations] = useState<ConfirmationSummary[]>([]);
  const [detail, setDetail] = useState<ConfirmationDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form state
  const [formType, setFormType] = useState("flight");
  const [formSupplier, setFormSupplier] = useState("");
  const [formNumber, setFormNumber] = useState("");
  const [formNotes, setFormNotes] = useState("");
  const [formExternalRef, setFormExternalRef] = useState("");
  const [formSaving, setFormSaving] = useState(false);

  // Reveal toggles
  const [showSupplier, setShowSupplier] = useState(false);
  const [showNumber, setShowNumber] = useState(false);
  const [showNotes, setShowNotes] = useState(false);

  const fetchList = useCallback(async () => {
    try {
      const res = await listConfirmations(tripId);
      setConfirmations(res.confirmations);
    } catch {
      setError("Failed to load confirmations");
    } finally {
      setLoading(false);
    }
  }, [tripId]);

  useEffect(() => {
    fetchList();
  }, [fetchList]);

  const handleCreate = useCallback(async () => {
    setFormSaving(true);
    setError(null);
    try {
      const data: CreateConfirmationRequest = {
        confirmation_type: formType,
        supplier_name: formSupplier || undefined,
        confirmation_number: formNumber || undefined,
        notes: formNotes || undefined,
        external_ref: formExternalRef || undefined,
      };
      await createConfirmation(tripId, data);
      setShowForm(false);
      setFormSupplier("");
      setFormNumber("");
      setFormNotes("");
      setFormExternalRef("");
      await fetchList();
    } catch {
      setError("Failed to create confirmation");
    } finally {
      setFormSaving(false);
    }
  }, [tripId, formType, formSupplier, formNumber, formNotes, formExternalRef, fetchList]);

  const handleViewDetail = useCallback(
    async (id: string) => {
      try {
        const res = await getConfirmation(tripId, id);
        setDetail(res.confirmation);
      } catch {
        setError("Failed to load confirmation detail");
      }
    },
    [tripId],
  );

  const handleAction = useCallback(
    async (id: string, action: "record" | "verify" | "void") => {
      setError(null);
      try {
        const fn = { record: recordConfirmation, verify: verifyConfirmation, void: voidConfirmation }[action];
        await fn(tripId, id);
        setDetail(null);
        await fetchList();
      } catch {
        setError(`Failed to ${action} confirmation`);
      }
    },
    [tripId, fetchList],
  );

  // ── Render ──────────────────────────────────────────────────────────────

  return loading ? (
      <div className="bg-elevated border border-border-default rounded-xl p-4">
        <div className="flex items-center gap-2 text-sm text-muted">
          <Loader className="size-4 animate-spin" />
          Loading confirmations…
        </div>
      </div>
  ) : (
    <div className="bg-elevated border border-border-default rounded-xl p-4 space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-medium text-[#e6edf3]">Confirmations</h4>
        <button
          onClick={() => setShowForm(!showForm)}
          className="text-xs px-3 py-1.5 rounded bg-[#1f6feb] text-white hover:bg-[#388bfd]"
        >
          {showForm ? "Cancel" : "Add Confirmation"}
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="text-xs text-red-400 bg-red-900/20 rounded p-2">{error}</div>
      )}

      {/* Create form */}
      {showForm && (
        <div className="space-y-2 bg-zinc-800/50 rounded p-3">
          <div className="flex gap-2">
            <select
              value={formType}
              onChange={(e) => setFormType(e.target.value)}
              className="text-xs bg-zinc-900 border border-zinc-700 rounded px-2 py-1.5 text-zinc-200"
            >
              {CONFIRMATION_TYPE_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>
          <MaskedInput label="Supplier" value={formSupplier} onChange={setFormSupplier} />
          <MaskedInput label="Confirmation #" value={formNumber} onChange={setFormNumber} />
          <div>
            <label className="text-[10px] text-zinc-500">Notes (max {NOTES_MAX_LENGTH})</label>
            <textarea
              value={formNotes}
              onChange={(e) => setFormNotes(e.target.value.slice(0, NOTES_MAX_LENGTH))}
              rows={2}
              className="w-full text-xs bg-zinc-900 border border-zinc-700 rounded px-2 py-1.5 text-zinc-200"
            />
          </div>
          <MaskedInput label="External ref" value={formExternalRef} onChange={setFormExternalRef} />
          <button
            onClick={handleCreate}
            disabled={formSaving}
            className="text-xs px-3 py-1.5 rounded bg-emerald-700 text-white hover:bg-emerald-600 disabled:opacity-50"
          >
            {formSaving ? "Saving…" : "Create"}
          </button>
        </div>
      )}

      {/* Detail view */}
      {detail && (
        <div className="bg-zinc-800/50 rounded p-3 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-zinc-200">
              {detail.confirmation_type} - {detail.confirmation_status}
            </span>
            <button
              onClick={() => setDetail(null)}
              className="text-xs text-zinc-500 hover:text-zinc-300"
            >
              Close
            </button>
          </div>
          <RevealField label="Supplier" value={detail.supplier_name} show={showSupplier} onToggle={() => setShowSupplier(!showSupplier)} />
          <RevealField label="Confirmation #" value={detail.confirmation_number} show={showNumber} onToggle={() => setShowNumber(!showNumber)} />
          <RevealField label="Notes" value={detail.notes} show={showNotes} onToggle={() => setShowNotes(!showNotes)} />
          {detail.evidence_refs && detail.evidence_refs.length > 0 && (
            <div className="text-xs text-zinc-400">
              Evidence: {detail.evidence_refs.map((r) => `${r.type}:${r.id.slice(0, 8)}`).join(", ")}
            </div>
          )}
          <div className="flex gap-2 pt-1">
            {detail.confirmation_status === "draft" && (
              <button
                onClick={() => handleAction(detail.id, "record")}
                className="text-xs px-2 py-1 rounded bg-blue-900/50 text-blue-300 hover:bg-blue-800/50"
              >
                Record
              </button>
            )}
            {detail.confirmation_status === "recorded" && (
              <button
                onClick={() => handleAction(detail.id, "verify")}
                className="text-xs px-2 py-1 rounded bg-emerald-900/50 text-emerald-300 hover:bg-emerald-800/50"
              >
                Verify
              </button>
            )}
            {detail.confirmation_status !== "voided" && (
              <button
                onClick={() => handleAction(detail.id, "void")}
                className="text-xs px-2 py-1 rounded bg-red-900/50 text-red-300 hover:bg-red-800/50"
              >
                Void
              </button>
            )}
          </div>
        </div>
      )}

      {/* Summary list */}
      {confirmations.length === 0 ? (
        <div className="text-xs text-zinc-500 py-2">
          No confirmations yet. Click &quot;Add Confirmation&quot; to record one.
        </div>
      ) : (
        <div className="space-y-1">
          {confirmations.map((c) => {
            const meta = STATUS_META[c.confirmation_status] ?? STATUS_META.draft;
            const Icon = meta.icon;
            return (
              <button
                key={c.id}
                onClick={() => handleViewDetail(c.id)}
                className="w-full flex items-center gap-2 px-2 py-1.5 rounded text-xs hover:bg-zinc-800/50 text-left"
              >
                <Icon className={`size-3.5 shrink-0 ${meta.color}`} />
                <span className="flex-1 truncate text-zinc-200">
                  {c.confirmation_type}
                </span>
                {c.has_supplier && (
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-500">supplier</span>
                )}
                {c.has_confirmation_number && (
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-500">ref#</span>
                )}
                {c.notes_present && (
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-500">notes</span>
                )}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ── Sub-components ───────────────────────────────────────────────────────────

function MaskedInput({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <div>
      <label className="text-[10px] text-zinc-500">{label}</label>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full text-xs bg-zinc-900 border border-zinc-700 rounded px-2 py-1.5 text-zinc-200"
      />
    </div>
  );
}

function RevealField({
  label,
  value,
  show,
  onToggle,
}: {
  label: string;
  value: string | null;
  show: boolean;
  onToggle: () => void;
}) {
  if (!value) return null;
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="text-zinc-500 w-24 shrink-0">{label}</span>
      <span className="flex-1 truncate text-zinc-200">
        {show ? value : "••••••••"}
      </span>
      <button onClick={onToggle} className="p-1 rounded hover:bg-zinc-700 text-zinc-500">
        {show ? <EyeOff className="size-3" /> : <Eye className="size-3" />}
      </button>
    </div>
  );
}
