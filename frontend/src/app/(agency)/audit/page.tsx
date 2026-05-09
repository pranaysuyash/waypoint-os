"use client";

import { useEffect, useState } from "react";
import { ClientDateTime } from "@/hooks/useClientDate";

interface AuditEvent {
  id: string;
  type: string;
  user_id: string;
  timestamp: string;
  details: Record<string, unknown>;
}

export default function AuditPage() {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function fetchAudit() {
      try {
        const res = await fetch("/api/audit?limit=50", { cache: "no-store" });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        if (!cancelled) {
          setEvents(data.items ?? []);
          setLoading(false);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load audit events");
          setLoading(false);
        }
      }
    }
    fetchAudit();
    return () => { cancelled = true; };
  }, []);

  if (loading) {
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
