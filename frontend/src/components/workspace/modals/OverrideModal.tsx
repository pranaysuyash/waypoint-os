"use client";

import { useReducer, useId } from "react";
import { AlertCircle, CheckCircle2, ChevronDown } from "lucide-react";
import { Modal } from "@/components/ui/modal";

export interface OverrideRequest {
  flag: string;
  decision_type?: string;
  action: "suppress" | "downgrade" | "acknowledge";
  new_severity?: string;
  overridden_by: string;
  reason: string;
  scope: "this_trip" | "pattern";
  original_severity?: string;
}

interface OverrideModalProps {
  isOpen: boolean;
  flag: {
    flag: string;
    severity: string;
    reason: string;
  };
  tripId: string;
  userId: string;
  onClose: () => void;
  onSubmit: (request: OverrideRequest) => Promise<void>;
}

const SEVERITY_LEVELS = ["critical", "high", "medium", "low"];

type OverrideFormState = {
  action: OverrideRequest["action"];
  newSeverity: string;
  reason: string;
  scope: OverrideRequest["scope"];
  status: "idle" | "submitting";
  error: string | null;
};

type OverrideFormAction =
  | { type: "SET_ACTION"; action: OverrideRequest["action"] }
  | { type: "SET_NEW_SEVERITY"; newSeverity: string }
  | { type: "SET_REASON"; reason: string }
  | { type: "SET_SCOPE"; scope: OverrideRequest["scope"] }
  | { type: "SET_STATUS"; status: OverrideFormState["status"] }
  | { type: "SET_ERROR"; error: string | null }
  | { type: "RESET_FORM" };

function createInitialOverrideState(): OverrideFormState {
  return {
    action: "suppress",
    newSeverity: "",
    reason: "",
    scope: "this_trip",
    status: "idle",
    error: null,
  };
}

function overrideFormReducer(
  state: OverrideFormState,
  action: OverrideFormAction
): OverrideFormState {
  switch (action.type) {
    case "SET_ACTION":
      return { ...state, action: action.action };
    case "SET_NEW_SEVERITY":
      return { ...state, newSeverity: action.newSeverity };
    case "SET_REASON":
      return { ...state, reason: action.reason };
    case "SET_SCOPE":
      return { ...state, scope: action.scope };
    case "SET_STATUS":
      return { ...state, status: action.status };
    case "SET_ERROR":
      return { ...state, error: action.error };
    case "RESET_FORM":
      return createInitialOverrideState();
    default:
      return state;
  }
}

export function OverrideModal({
  isOpen,
  flag,
  tripId,
  userId,
  onClose,
  onSubmit,
}: OverrideModalProps) {
  const [state, dispatch] = useReducer(overrideFormReducer, undefined, createInitialOverrideState);
  const { action, newSeverity, reason, scope, status, error } = state;
  const isSubmitting = status === "submitting";
  const actionId = useId();
  const downgradeId = useId();
  const scopeId = useId();
  const reasonId = useId();

  const reasonLength = reason.length;
  const reasonValid = reasonLength >= 10;
  const currentSeverityIndex = SEVERITY_LEVELS.indexOf(flag.severity);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    dispatch({ type: "SET_ERROR", error: null });

    if (!reason.trim()) {
      dispatch({ type: "SET_ERROR", error: "Reason is required" });
      return;
    }

    if (reasonLength < 10) {
      dispatch({ type: "SET_ERROR", error: "Reason must be at least 10 characters" });
      return;
    }

    if (action === "downgrade" && !newSeverity) {
      dispatch({ type: "SET_ERROR", error: "New severity is required for downgrade" });
      return;
    }

    if (action === "downgrade" && newSeverity) {
      const newIndex = SEVERITY_LEVELS.indexOf(newSeverity);
      if (newIndex >= currentSeverityIndex) {
        dispatch({ type: "SET_ERROR", error: "New severity must be lower than current severity" });
        return;
      }
    }

    try {
      dispatch({ type: "SET_STATUS", status: "submitting" });
      const request: OverrideRequest = {
        flag: flag.flag,
        decision_type: flag.flag,
        action,
        new_severity: action === "downgrade" ? newSeverity : undefined,
        overridden_by: userId,
        reason: reason.trim(),
        scope,
        original_severity: flag.severity,
      };

      await onSubmit(request);
      dispatch({ type: "RESET_FORM" });
      onClose();
    } catch (err) {
      dispatch({
        type: "SET_ERROR",
        error: err instanceof Error ? err.message : "Failed to submit override",
      });
    } finally {
      dispatch({ type: "SET_STATUS", status: "idle" });
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Override Risk Flag"
      description={flag.flag.replace(/_/g, " ")}
      size="md"
    >
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="p-4 bg-[#161b22] border border-[#30363d] rounded-lg">
          <p className="text-ui-xs text-[#8b949e] mb-2 uppercase tracking-wide">Current Severity</p>
          <div className="flex items-center gap-2">
            <div
              className={`px-3 py-1 rounded-full text-ui-sm font-semibold text-white ${
                flag.severity === "critical"
                  ? "bg-[#da3633]"
                  : flag.severity === "high"
                  ? "bg-[#d1242f]"
                  : flag.severity === "medium"
                  ? "bg-[#fb8500]"
                  : "bg-[#1f6feb]"
              }`}
            >
              {flag.severity.toUpperCase()}
            </div>
            <p className="text-ui-sm text-[#8b949e]">{flag.reason}</p>
          </div>
        </div>

        <div>
          <span className="block text-ui-sm font-medium text-[#e6edf3] mb-3">
            Action
          </span>
          <div className="space-y-2">
            {[
              { value: "suppress" as const, label: "Suppress", desc: "Remove flag entirely" },
              { value: "downgrade" as const, label: "Downgrade", desc: "Lower severity" },
              { value: "acknowledge" as const, label: "Acknowledge", desc: "Keep but noted" },
            ].map((opt) => (
              <label key={opt.value} htmlFor={`action-${opt.value}`} className="flex items-start gap-3 p-3 rounded-lg hover:bg-[#161b22] cursor-pointer transition-colors">
                <input
                  id={`action-${opt.value}`}
                  type="radio"
                  name="action"
                  value={opt.value}
                  aria-label={opt.label}
                  checked={action === opt.value}
                  onChange={(e) =>
                    dispatch({ type: "SET_ACTION", action: e.target.value as OverrideRequest["action"] })
                  }
                  className="mt-1"
                />
                <div>
                  <p className="text-ui-sm font-medium text-[#e6edf3]">{opt.label}</p>
                  <p className="text-ui-xs text-[#8b949e]">{opt.desc}</p>
                </div>
              </label>
            ))}
          </div>
        </div>

        {action === "downgrade" && (
          <div>
            <label htmlFor={downgradeId} className="block text-ui-sm font-medium text-[#e6edf3] mb-3">
              Downgrade to
            </label>
            <div className="relative">
                <select
                  id={downgradeId}
                  value={newSeverity}
                  onChange={(e) => dispatch({ type: "SET_NEW_SEVERITY", newSeverity: e.target.value })}
                className="w-full px-4 py-2.5 bg-[#0d1117] border border-[#30363d] rounded-lg text-[#e6edf3] text-ui-sm focus:outline-none focus:border-[#58a6ff] appearance-none cursor-pointer"
              >
                <option value="">Select severity…</option>
                {SEVERITY_LEVELS.slice(currentSeverityIndex + 1).map((sev) => (
                  <option key={sev} value={sev}>
                    {sev.charAt(0).toUpperCase() + sev.slice(1)}
                  </option>
                ))}
              </select>
              <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 size-4 text-[#8b949e] pointer-events-none" />
            </div>
            <p className="text-ui-xs text-[#8b949e] mt-2">
              Must be lower than current severity ({flag.severity})
            </p>
          </div>
        )}

        <div>
          <span className="block text-ui-sm font-medium text-[#e6edf3] mb-3">
            Scope
          </span>
          <div className="space-y-2">
            {[
              { value: "this_trip" as const, label: "This Trip", desc: "Override applies only to this trip" },
              { value: "pattern" as const, label: "Pattern", desc: "Use for future similar cases" },
            ].map((opt) => (
              <label key={opt.value} htmlFor={`scope-${opt.value}`} className="flex items-start gap-3 p-3 rounded-lg hover:bg-[#161b22] cursor-pointer transition-colors">
                <input
                  id={`scope-${opt.value}`}
                  type="radio"
                  name="scope"
                  value={opt.value}
                  aria-label={opt.label}
                  checked={scope === opt.value}
                  onChange={(e) =>
                    dispatch({ type: "SET_SCOPE", scope: e.target.value as OverrideRequest["scope"] })
                  }
                  className="mt-1"
                />
                <div>
                  <p className="text-ui-sm font-medium text-[#e6edf3]">{opt.label}</p>
                  <p className="text-ui-xs text-[#8b949e]">{opt.desc}</p>
                </div>
              </label>
            ))}
          </div>
        </div>

        <div>
          <label htmlFor={reasonId} className="block text-ui-sm font-medium text-[#e6edf3] mb-3">
            Reason for Override
          </label>
          <textarea
            id={reasonId}
            value={reason}
            onChange={(e) => dispatch({ type: "SET_REASON", reason: e.target.value })}
            placeholder="Explain why you're overriding this flag (minimum 10 characters)..."
            className="w-full px-4 py-3 bg-[#0d1117] border border-[#30363d] rounded-lg text-[#e6edf3] text-ui-sm placeholder-[#6e7681] focus:outline-none focus:border-[#58a6ff] resize-none"
            rows={4}
          />
          <div className="flex items-center justify-between mt-2">
            <p className={`text-ui-xs ${reasonValid ? "text-[#3fb950]" : "text-[#8b949e]"}`}>
              {reasonLength} / 10 characters minimum
            </p>
            {reasonValid && <CheckCircle2 className="size-4 text-[#3fb950]" />}
          </div>
        </div>

        {error && (
          <div className="flex items-start gap-3 p-4 bg-[#161b22] border border-[#da3633] rounded-lg">
            <AlertCircle className="size-4 text-[#da3633] mt-0.5 flex-shrink-0" />
            <p className="text-ui-sm text-[#da3633]">{error}</p>
          </div>
        )}

        <div className="flex gap-3">
          <button
            type="button"
            onClick={onClose}
            disabled={isSubmitting}
            className="flex-1 px-4 py-2.5 border border-[#30363d] rounded-lg text-[#e6edf3] font-medium hover:bg-[#161b22] disabled:opacity-50 transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={isSubmitting || !reasonValid || (action === "downgrade" && !newSeverity)}
            className="flex-1 px-4 py-2.5 bg-[#238636] text-white rounded-lg font-medium hover:bg-[#2ea043] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isSubmitting ? "Submitting…" : "Submit Override"}
          </button>
        </div>
      </form>
    </Modal>
  );
}
