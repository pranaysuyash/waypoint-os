"use client";

import { useEffect, useReducer } from "react";
import { ClientDateTime } from "@/hooks/useClientDate";

interface AuditEvent {
  id: string;
  type: string;
  user_id: string;
  timestamp: string;
  details: Record<string, unknown>;
}

type AuditState =
  | { status: "loading"; events: AuditEvent[]; error: null }
  | { status: "success"; events: AuditEvent[]; error: null }
  | { status: "error"; events: AuditEvent[]; error: string };

type AuditAction =
  | { type: "loaded"; events: AuditEvent[] }
  | { type: "failed"; error: string };

function auditReducer(state: AuditState, action: AuditAction): AuditState {
  switch (action.type) {
    case "loaded":
      return { status: "success", events: action.events, error: null };
    case "failed":
      return { status: "error", events: state.events, error: action.error };
    default:
      return state;
  }
}

export default function AuditPage() {
  const [state, dispatch] = useReducer(auditReducer, {
    status: "loading",
    events: [],
    error: null,
  });
  const { events, error } = state;

  useEffect(() => {
    let cancelled = false;
    async function fetchAudit() {
      try {
        const res = await fetch("/api/audit?limit=50", { cache: "no-store" });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        if (!cancelled) {
          dispatch({ type: "loaded", events: data.items ?? [] });
        }
      } catch (err) {
        if (!cancelled) {
          dispatch({ type: "failed", error: err instanceof Error ? err.message : "Failed to load audit events" });
        }
      }
    }
    fetchAudit();
    return () => { cancelled = true; };
  }, []);

  if (state.status === "loading") {
    return (
      <div className="p-6">
        <h1 className="text-xl font-semibold mb-4">Trip Fit & Compliance Audit</h1>
        <p className="text-muted-foreground">Loading audit events…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <h1 className="text-xl font-semibold mb-4">Trip Fit & Compliance Audit</h1>
        <p className="text-destructive">Error: {error}</p>
      </div>
    );
  }

  return (
    <div className="p-6">
      <h1 className="text-xl font-semibold mb-4">Trip Fit & Compliance Audit</h1>
      <p className="text-muted-foreground mb-6">
        Audit trail of trip processing: stage transitions, validation outcomes,
        and operator overrides.
      </p>
      {events.length === 0 ? (
        <p className="text-muted-foreground">No audit events recorded yet.</p>
      ) : (
        <div className="space-y-3">
          {events.map((event) => (
            <div
              key={event.id}
              className="rounded border p-3 text-sm"
            >
              <div className="flex items-center gap-2 mb-1">
                <span className="font-mono text-xs bg-muted px-1.5 py-0.5 rounded">
                  {event.type}
                </span>
                <span className="text-muted-foreground text-xs">
                  <ClientDateTime value={event.timestamp} />
                </span>
              </div>
              <div className="text-xs text-muted-foreground font-mono truncate">
                {JSON.stringify(event.details)}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
