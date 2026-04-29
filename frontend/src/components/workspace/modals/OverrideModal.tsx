"use client";

import { useState } from "react";
import { X, AlertCircle, CheckCircle2, ChevronDown } from "lucide-react";

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

export function OverrideModal({
  isOpen,
  flag,
  tripId,
  userId,
  onClose,
  onSubmit,
}: OverrideModalProps) {
  const [action, setAction] = useState<"suppress" | "downgrade" | "acknowledge">("suppress");
  const [newSeverity, setNewSeverity] = useState<string>("");
  const [reason, setReason] = useState<string>("");
  const [scope, setScope] = useState<"this_trip" | "pattern">("this_trip");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const reasonLength = reason.length;
  const reasonValid = reasonLength >= 10;
  const currentSeverityIndex = SEVERITY_LEVELS.indexOf(flag.severity);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validation
    if (!reason.trim()) {
      setError("Reason is required");
      return;
    }

    if (reasonLength < 10) {
      setError("Reason must be at least 10 characters");
      return;
    }

    if (action === "downgrade" && !newSeverity) {
      setError("New severity is required for downgrade");
      return;
    }

    if (action === "downgrade" && newSeverity) {
      const newIndex = SEVERITY_LEVELS.indexOf(newSeverity);
      if (newIndex >= currentSeverityIndex) {
        setError("New severity must be lower than current severity");
        return;
      }
    }

    try {
      setIsLoading(true);
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
      
      // Reset form
      setAction("suppress");
      setNewSeverity("");
      setReason("");
      setScope("this_trip");
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to submit override");
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-[#0d1117] border border-[#30363d] rounded-2xl shadow-2xl w-full max-w-lg mx-4">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-[#30363d]">
          <div>
            <h2 className="text-ui-lg font-semibold text-[#e6edf3]">Override Risk Flag</h2>
            <p className="text-ui-sm text-[#8b949e] mt-1">
              {flag.flag.replace(/_/g, " ")}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-[#161b22] rounded-lg transition-colors"
          >
            <X className="h-5 w-5 text-[#8b949e]" />
          </button>
        </div>

        {/* Content */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Current Severity Badge */}
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

          {/* Action Selection */}
          <div>
            <label className="block text-ui-sm font-medium text-[#e6edf3] mb-3">
              Action
            </label>
            <div className="space-y-2">
              {[
                { value: "suppress" as const, label: "Suppress", desc: "Remove flag entirely" },
                { value: "downgrade" as const, label: "Downgrade", desc: "Lower severity" },
                { value: "acknowledge" as const, label: "Acknowledge", desc: "Keep but noted" },
              ].map((opt) => (
                <label key={opt.value} className="flex items-start gap-3 p-3 rounded-lg hover:bg-[#161b22] cursor-pointer transition-colors">
                  <input
                    type="radio"
                    name="action"
                    value={opt.value}
                    checked={action === opt.value}
                    onChange={(e) => setAction(e.target.value as typeof action)}
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

          {/* Downgrade Severity Selector */}
          {action === "downgrade" && (
            <div>
              <label className="block text-ui-sm font-medium text-[#e6edf3] mb-3">
                Downgrade to
              </label>
              <div className="relative">
                <select
                  value={newSeverity}
                  onChange={(e) => setNewSeverity(e.target.value)}
                  className="w-full px-4 py-2.5 bg-[#0d1117] border border-[#30363d] rounded-lg text-[#e6edf3] text-ui-sm focus:outline-none focus:border-[#58a6ff] appearance-none cursor-pointer"
                >
                  <option value="">Select severity...</option>
                  {SEVERITY_LEVELS.slice(currentSeverityIndex + 1).map((sev) => (
                    <option key={sev} value={sev}>
                      {sev.charAt(0).toUpperCase() + sev.slice(1)}
                    </option>
                  ))}
                </select>
                <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#8b949e] pointer-events-none" />
              </div>
              <p className="text-ui-xs text-[#8b949e] mt-2">
                Must be lower than current severity ({flag.severity})
              </p>
            </div>
          )}

          {/* Scope Selection */}
          <div>
            <label className="block text-ui-sm font-medium text-[#e6edf3] mb-3">
              Scope
            </label>
            <div className="space-y-2">
              {[
                { value: "this_trip" as const, label: "This Trip", desc: "Override applies only to this trip" },
                { value: "pattern" as const, label: "Pattern", desc: "Use for future similar cases" },
              ].map((opt) => (
                <label key={opt.value} className="flex items-start gap-3 p-3 rounded-lg hover:bg-[#161b22] cursor-pointer transition-colors">
                  <input
                    type="radio"
                    name="scope"
                    value={opt.value}
                    checked={scope === opt.value}
                    onChange={(e) => setScope(e.target.value as typeof scope)}
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

          {/* Reason Input */}
          <div>
            <label className="block text-ui-sm font-medium text-[#e6edf3] mb-3">
              Reason for Override
            </label>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Explain why you're overriding this flag (minimum 10 characters)..."
              className="w-full px-4 py-3 bg-[#0d1117] border border-[#30363d] rounded-lg text-[#e6edf3] text-ui-sm placeholder-[#6e7681] focus:outline-none focus:border-[#58a6ff] resize-none"
              rows={4}
            />
            <div className="flex items-center justify-between mt-2">
              <p className={`text-ui-xs ${reasonValid ? "text-[#3fb950]" : "text-[#8b949e]"}`}>
                {reasonLength} / 10 characters minimum
              </p>
              {reasonValid && <CheckCircle2 className="h-4 w-4 text-[#3fb950]" />}
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="flex items-start gap-3 p-4 bg-[#161b22] border border-[#da3633] rounded-lg">
              <AlertCircle className="h-4 w-4 text-[#da3633] mt-0.5 flex-shrink-0" />
              <p className="text-ui-sm text-[#da3633]">{error}</p>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3">
            <button
              type="button"
              onClick={onClose}
              disabled={isLoading}
              className="flex-1 px-4 py-2.5 border border-[#30363d] rounded-lg text-[#e6edf3] font-medium hover:bg-[#161b22] disabled:opacity-50 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading || !reasonValid || (action === "downgrade" && !newSeverity)}
              className="flex-1 px-4 py-2.5 bg-[#238636] text-white rounded-lg font-medium hover:bg-[#2ea043] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isLoading ? "Submitting..." : "Submit Override"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
