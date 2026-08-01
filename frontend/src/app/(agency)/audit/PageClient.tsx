"use client";

import { useCallback, useEffect, useMemo, useReducer, useState } from "react";
import { ClientDateTime } from "@/hooks/useClientDate";

type AuditEventType = string;
type AuditTriageAction = "acknowledge" | "close" | "escalate";

type AuditEvent = {
  id: string;
  type: AuditEventType;
  user_id: string;
  timestamp: string;
  details: Record<string, unknown>;
};

type AuditEntriesResponse = {
  items?: AuditEvent[];
  entries?: AuditEvent[];
  total?: number;
};

type RoutingHealthTriageSummary = {
  target_event_id: string;
  action: AuditTriageAction;
  note: string;
  user_id: string;
  timestamp: string;
};

type RoutingHealthBatchResult = {
  event_id: string;
  success: boolean;
  action?: AuditTriageAction;
  note?: string;
  triage_event?: AuditEvent;
  error?: string;
};

type RoutingHealthTriageBatchResponse = {
  success: boolean;
  requested: number;
  succeeded: number;
  failed: number;
  results: RoutingHealthBatchResult[];
};

type RoutingHealthState = {
  tripEvents: AuditEvent[];
  routingHealthAlerts: AuditEvent[];
  routingHealthPagingAlerts: AuditEvent[];
  routingHealthAlertTriages: AuditEvent[];
  routingHealthPagingSuppressions: AuditEvent[];
};

type AuditState =
  | {
      status: "loading";
      error: null;
      sources: null;
    }
  | {
      status: "success";
      sources: RoutingHealthState;
      error: null;
    }
  | { status: "error"; sources: RoutingHealthState; error: string };

type AuditAction =
  | { type: "loaded"; sources: RoutingHealthState }
  | { type: "failed"; error: string };

function auditReducer(state: AuditState, action: AuditAction): AuditState {
  switch (action.type) {
    case "loaded":
      return {
        status: "success",
        sources: action.sources,
        error: null,
      };
    case "failed":
      return {
        status: "error",
        sources:
          state.status === "success" && state.sources
            ? state.sources
            : {
                tripEvents: [],
                routingHealthAlerts: [],
                routingHealthPagingAlerts: [],
                routingHealthAlertTriages: [],
                routingHealthPagingSuppressions: [],
              },
        error: action.error,
      };
    default:
      return state;
  }
}

function isKnownAction(value: unknown): value is AuditTriageAction {
  return value === "acknowledge" || value === "close" || value === "escalate";
}

function toEntries(response: unknown): AuditEvent[] {
  if (!response || typeof response !== "object") {
    return [];
  }
  const payload = response as AuditEntriesResponse;
  if (Array.isArray(payload.entries)) {
    return payload.entries;
  }
  if (Array.isArray(payload.items)) {
    return payload.items;
  }
  return [];
}

function buildEventRowsLabel(event: AuditEvent): string {
  const details = event.details ?? {};
  const status = typeof details.status === "string" ? details.status : "unknown";
  const tripId = typeof details.trip_id === "string" ? details.trip_id : "unknown";
  const workflow = typeof details.workflow === "string" ? details.workflow : "unknown";
  const metric = typeof details.metric === "string" ? details.metric : "";
  const minOccurrences =
    typeof details.min_occurrences === "number" ? details.min_occurrences : "";
  const windowMinutes =
    typeof details.window_minutes === "number" ? details.window_minutes : "";

  const parts = [
    `status:${status}`,
    `trip:${tripId}`,
    workflow !== "unknown" ? `workflow:${workflow}` : null,
    metric ? `metric:${metric}` : null,
    minOccurrences ? `min_occurrences:${minOccurrences}` : null,
    windowMinutes ? `window:${windowMinutes}m` : null,
  ];
  return parts.filter(Boolean).join(" · ");
}

function buildPagingRowsLabel(event: AuditEvent): string {
  const details = event.details ?? {};
  const status = typeof details.status === "string" ? details.status : "unknown";
  const occurrence = typeof details.occurrence_index === "number" ? details.occurrence_index : "unknown";
  const tripId = typeof details.trip_id === "string" ? details.trip_id : "unknown";
  const sustainedWindow =
    typeof details.sustained_window_seconds === "number" ? details.sustained_window_seconds : "unknown";
  const pagingCooldown =
    typeof details.paging_cooldown_seconds === "number" ? details.paging_cooldown_seconds : "unknown";

  return `status:${status} · trip:${tripId} · occurrence:${occurrence} · sustained_window:${sustainedWindow}s · cooldown:${pagingCooldown}s`;
}

function readTriageEvents(events: AuditEvent[]): Record<string, RoutingHealthTriageSummary> {
  const merged: Record<string, RoutingHealthTriageSummary> = {};

  for (const event of events) {
    const details = event.details ?? {};
    const targetEventId =
      typeof details.target_event_id === "string" ? details.target_event_id : "";
    const action = details.action;

    if (!targetEventId || !isKnownAction(action)) {
      continue;
    }

    const existing = merged[targetEventId];
    if (!existing || event.timestamp > existing.timestamp) {
      merged[targetEventId] = {
        target_event_id: targetEventId,
        action,
        note: typeof details.note === "string" ? details.note : "",
        user_id: event.user_id || "system",
        timestamp: event.timestamp,
      };
    }
  }

  return merged;
}

function EventRows({
  title,
  events,
  formatter,
}: {
  title: string;
  events: AuditEvent[];
  formatter: (event: AuditEvent) => string;
}) {
  return (
    <section>
      <h2 className="text-base font-semibold mb-3">{title}</h2>
      {events.length === 0 ? (
        <p className="text-sm text-muted-foreground">No matching events.</p>
      ) : (
        <div className="space-y-3">
          {events.map((event) => (
            <div key={`${event.id}-${event.type}`} className="rounded border p-3 text-sm">
              <div className="flex items-center gap-2 mb-1">
                <span className="font-mono text-xs bg-muted px-1.5 py-0.5 rounded">{event.type}</span>
                <span className="text-muted-foreground text-xs">
                  <ClientDateTime value={event.timestamp} />
                </span>
              </div>
              <p className="text-sm">{formatter(event)}</p>
              <div className="text-xs text-muted-foreground font-mono break-all">
                {JSON.stringify(event.details)}
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

function RoutingHealthAlertCard({
  event,
  triageStatus,
  checked,
  onToggleSelection,
  onTriage,
}: {
  event: AuditEvent;
  triageStatus?: RoutingHealthTriageSummary;
  checked: boolean;
  onToggleSelection: (eventId: string) => void;
  onTriage: (eventId: string, action: AuditTriageAction, note: string) => Promise<AuditEvent>;
}) {
  const [note, setNote] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const details = event.details ?? {};
  const label = buildEventRowsLabel(event);

  async function submitAction(action: AuditTriageAction) {
    setIsSubmitting(true);
    setError(null);
    try {
      await onTriage(event.id, action, note.trim());
      setNote("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to triage alert");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="rounded border p-3 text-sm">
      <div className="flex items-center justify-between gap-2 mb-1">
        <div>
          <input
            type="checkbox"
            checked={checked}
            onChange={() => onToggleSelection(event.id)}
            aria-label={`Select alert ${event.id}`}
            className="mr-2"
          />
          <span className="font-mono text-xs bg-muted px-1.5 py-0.5 rounded">{event.type}</span>
          <span className="text-muted-foreground text-xs ml-2">
            <ClientDateTime value={event.timestamp} />
          </span>
        </div>
        {triageStatus ? (
          <span className="text-xs text-muted-foreground">
            Triaged: {triageStatus.action} by {triageStatus.user_id}
          </span>
        ) : null}
      </div>
      <p className="text-sm">{label}</p>
      <div className="text-xs text-muted-foreground font-mono mb-2 break-all">{JSON.stringify(details)}</div>
      {triageStatus ? (
        <p className="text-xs text-muted-foreground mb-2">Latest note: {triageStatus.note || "(no note)"}</p>
      ) : null}
      <form className="flex flex-wrap gap-2 items-start" onSubmit={(e) => e.preventDefault()}>
        <label className="text-xs text-muted-foreground" htmlFor={`note-${event.id}`}>
          Note
        </label>
        <input
          id={`note-${event.id}`}
          value={note}
          onChange={(evt) => setNote(evt.target.value)}
          className="border rounded px-2 py-1 text-xs flex-1 min-w-[220px]"
          placeholder="Optional action note"
        />
        <div className="flex gap-2">
          <button
            type="button"
            className="text-xs border rounded px-2 py-1"
            disabled={isSubmitting}
            onClick={() => void submitAction("acknowledge")}
          >
            Acknowledge
          </button>
          <button
            type="button"
            className="text-xs border rounded px-2 py-1"
            disabled={isSubmitting}
            onClick={() => void submitAction("close")}
          >
            Close
          </button>
          <button
            type="button"
            className="text-xs border rounded px-2 py-1"
            disabled={isSubmitting}
            onClick={() => void submitAction("escalate")}
          >
            Escalate
          </button>
        </div>
      </form>
      {error ? <p className="text-destructive text-xs mt-2">{error}</p> : null}
    </div>
  );
}

function RoutingHealthAlertRows({
  events,
  triageByAlert,
  selectedAlertIds,
  onToggleAlertSelection,
  onTriage,
}: {
  events: AuditEvent[];
  triageByAlert: Record<string, RoutingHealthTriageSummary>;
  selectedAlertIds: Record<string, boolean>;
  onToggleAlertSelection: (eventId: string) => void;
  onTriage: (eventId: string, action: AuditTriageAction, note: string) => Promise<AuditEvent>;
}) {
  return (
    <section>
      <h2 className="text-base font-semibold mb-3">Routing health alerts</h2>
      {events.length === 0 ? (
        <p className="text-sm text-muted-foreground">No matching events.</p>
      ) : (
        <div className="space-y-3">
          {events.map((event) => {
            const status = triageByAlert[event.id];
            return (
              <RoutingHealthAlertCard
                key={`${event.id}-${event.type}`}
                event={event}
                triageStatus={status}
                checked={Boolean(selectedAlertIds[event.id])}
                onToggleSelection={onToggleAlertSelection}
                onTriage={onTriage}
              />
            );
          })}
        </div>
      )}
    </section>
  );
}

function RoutingHealthPagingAlertCard({
  event,
  onSuppress,
}: {
  event: AuditEvent;
  onSuppress: (eventId: string, suppressMinutes: string, note: string) => Promise<AuditEvent>;
}) {
  const [note, setNote] = useState("");
  const [minutes, setMinutes] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const details = event.details ?? {};
  const label = buildPagingRowsLabel(event);

  async function submitSuppress() {
    setIsSubmitting(true);
    setError(null);
    try {
      await onSuppress(event.id, minutes.trim(), note.trim());
      setNote("");
      setMinutes("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to suppress paging alert");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="rounded border p-3 text-sm">
      <div className="flex items-center gap-2 mb-1">
        <span className="font-mono text-xs bg-muted px-1.5 py-0.5 rounded">{event.type}</span>
        <span className="text-muted-foreground text-xs">
          <ClientDateTime value={event.timestamp} />
        </span>
      </div>
      <p className="text-sm">{label}</p>
      <div className="text-xs text-muted-foreground font-mono mb-2 break-all">
        {JSON.stringify({
          trip_id: typeof details.trip_id === "string" ? details.trip_id : "unknown",
          status: typeof details.status === "string" ? details.status : "unknown",
          occurrence_index: details.occurrence_index,
        })}
      </div>
      <div className="flex flex-wrap gap-2 items-start">
        <label className="text-xs text-muted-foreground" htmlFor={`suppress-minutes-${event.id}`}>
          Suppress for (minutes)
        </label>
        <input
          id={`suppress-minutes-${event.id}`}
          value={minutes}
          onChange={(evt) => setMinutes(evt.target.value)}
          className="border rounded px-2 py-1 text-xs w-40"
          placeholder="e.g. 60"
          inputMode="numeric"
        />
        <label className="text-xs text-muted-foreground" htmlFor={`suppress-note-${event.id}`}>
          Suppression note
        </label>
        <input
          id={`suppress-note-${event.id}`}
          value={note}
          onChange={(evt) => setNote(evt.target.value)}
          className="border rounded px-2 py-1 text-xs flex-1 min-w-[220px]"
          placeholder="Optional suppression note"
        />
        <button
          type="button"
          className="text-xs border rounded px-2 py-1"
          disabled={isSubmitting}
          onClick={() => void submitSuppress()}
        >
          Suppress paging
        </button>
      </div>
      {error ? <p className="text-destructive text-xs mt-2">{error}</p> : null}
    </div>
  );
}

function RoutingHealthPagingAlertRows({
  events,
  onSuppress,
}: {
  events: AuditEvent[];
  onSuppress: (eventId: string, suppressMinutes: string, note: string) => Promise<AuditEvent>;
}) {
  return (
    <section>
      <h2 className="text-base font-semibold mb-3">Routing health paging alerts</h2>
      {events.length === 0 ? (
        <p className="text-sm text-muted-foreground">No matching events.</p>
      ) : (
        <div className="space-y-3">
          {events.map((event) => (
            <RoutingHealthPagingAlertCard
              key={`${event.id}-${event.type}`}
              event={event}
              onSuppress={onSuppress}
            />
          ))}
        </div>
      )}
    </section>
  );
}

function downloadFromBlob(name: string, blob: Blob) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = name;
  anchor.click();
  URL.revokeObjectURL(url);
}

export default function AuditPage() {
  const autoRefreshMs = 15000;
  const [state, dispatch] = useReducer(auditReducer, {
    status: "loading",
    error: null,
    sources: null,
  });
  const [autoRefreshEnabled, setAutoRefreshEnabled] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastRefreshAt, setLastRefreshAt] = useState<string | null>(null);
  const [triageOverrides, setTriageOverrides] = useState<Record<string, AuditEvent>>({});
  const [selectedAlertIds, setSelectedAlertIds] = useState<Record<string, boolean>>({});
  const [batchAction, setBatchAction] = useState<AuditTriageAction>("acknowledge");
  const [batchNote, setBatchNote] = useState("");
  const [isBatchSubmitting, setIsBatchSubmitting] = useState(false);
  const [batchError, setBatchError] = useState<string | null>(null);
  const [batchResult, setBatchResult] = useState<RoutingHealthTriageBatchResponse | null>(null);
  const [exportError, setExportError] = useState<string | null>(null);
  const [exportFormat, setExportFormat] = useState<"json" | "csv">("json");

  const { sources, error } = state;

  const tripEvents = sources?.tripEvents ?? [];
  const routingHealthAlerts = sources?.routingHealthAlerts ?? [];
  const routingHealthPagingAlerts = sources?.routingHealthPagingAlerts ?? [];
  const routingHealthAlertTriages = sources?.routingHealthAlertTriages ?? [];
  const routingHealthPagingSuppressions = sources?.routingHealthPagingSuppressions ?? [];

  const triageByAlert = useMemo(() => {
    const base = readTriageEvents(routingHealthAlertTriages);
    for (const [key, override] of Object.entries(triageOverrides)) {
      const existing = base[key];
      const details = override.details ?? {};
      const action = details.action;
      if (!isKnownAction(action)) {
        continue;
      }

      if (!existing || override.timestamp > existing.timestamp) {
        base[key] = {
          target_event_id: key,
          action,
          note: typeof details.note === "string" ? details.note : "",
          user_id: override.user_id,
          timestamp: override.timestamp,
        };
      }
    }
    return base;
  }, [routingHealthAlertTriages, triageOverrides]);

  const selectedAlertCount = Object.values(selectedAlertIds).filter(Boolean).length;

  function toggleAlertSelection(eventId: string) {
    setSelectedAlertIds((previous) => ({
      ...previous,
      [eventId]: !previous[eventId],
    }));
  }

  function clearSelectedAlerts() {
    setSelectedAlertIds({});
  }

  async function handleTriage(eventId: string, action: AuditTriageAction, note: string): Promise<AuditEvent> {
    const response = await fetch(`/legacy_ops/audit/${encodeURIComponent(eventId)}/triage`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ action, note }),
      cache: "no-store",
    });

    if (!response.ok) {
      const detail = await response.text().catch(() => "");
      throw new Error(`Failed to save triage (${response.status}): ${detail || response.statusText}`);
    }

    const payload = (await response.json()) as { triage_event?: AuditEvent };
    if (payload?.triage_event && typeof payload.triage_event === "object") {
      const triageEvent = payload.triage_event;
      setTriageOverrides((previous) => ({
        ...previous,
        [eventId]: triageEvent,
      }));
      return triageEvent;
    }

    throw new Error("Invalid triage response from server");
  }

  async function handleBatchTriage() {
    const selectedIds = Object.entries(selectedAlertIds)
      .filter(([, isSelected]) => isSelected)
      .map(([eventId]) => eventId);

    if (selectedIds.length === 0) {
      setBatchError("Select at least one alert before batch triage.");
      return;
    }

    setIsBatchSubmitting(true);
    setBatchError(null);
    setBatchResult(null);

    try {
      const payload = selectedIds.map((eventId) => ({
        event_id: eventId,
        action: batchAction,
        note: batchNote.trim() || undefined,
      }));

      const response = await fetch("/legacy_ops/audit/routing-health/batch-triage", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
        cache: "no-store",
      });

      if (!response.ok) {
        const detail = await response.text().catch(() => "");
        throw new Error(`Failed to run batch triage (${response.status}): ${detail || response.statusText}`);
      }

      const result = (await response.json()) as RoutingHealthTriageBatchResponse;
      setBatchResult(result);

      const newOverrides: Record<string, AuditEvent> = {};
      for (const item of result.results) {
        if (item.success && item.triage_event) {
          newOverrides[item.event_id] = item.triage_event;
        }
      }
      if (Object.keys(newOverrides).length > 0) {
        setTriageOverrides((previous) => ({ ...previous, ...newOverrides }));
      }
      if (result.failed === 0) {
        clearSelectedAlerts();
      }
    } finally {
      setIsBatchSubmitting(false);
    }
  }

  async function handleSuppressPaging(
    eventId: string,
    suppressMinutes: string,
    note: string,
  ): Promise<AuditEvent> {
    const minuteValue = suppressMinutes.trim() ? Number.parseInt(suppressMinutes, 10) : null;
    const body = {
      suppress_for_minutes: Number.isFinite(minuteValue as number) ? Number(minuteValue) : null,
      note: note.trim(),
    };

    const response = await fetch(
      `/legacy_ops/audit/${encodeURIComponent(eventId)}/suppress-routing-health-paging`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
        cache: "no-store",
      },
    );

    if (!response.ok) {
      const detail = await response.text().catch(() => "");
      throw new Error(
        `Failed to suppress paging alert (${response.status}): ${detail || response.statusText}`,
      );
    }

    const payload = (await response.json()) as {
      suppression_event?: AuditEvent;
    };
    if (payload?.suppression_event && typeof payload.suppression_event === "object") {
      return payload.suppression_event;
    }

    throw new Error("Invalid suppression response from server");
  }

  async function handleExportEvidence() {
    setExportError(null);
    const params = new URLSearchParams({
      format: exportFormat,
      include_paging: "true",
    });

    const response = await fetch(`/legacy_ops/audit/routing-health/export?${params.toString()}`, {
      cache: "no-store",
    });

    if (!response.ok) {
      const detail = await response.text().catch(() => "");
      throw new Error(`Failed to export evidence (${response.status}): ${detail || response.statusText}`);
    }

    if (exportFormat === "csv") {
      const text = await response.text();
      downloadFromBlob("routing-health-evidence.csv", new Blob([text], { type: "text/csv" }));
      return;
    }

    const payload = (await response.json()) as unknown;
    downloadFromBlob(
      "routing-health-evidence.json",
      new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" }),
    );
  }

  const fetchAudit = useCallback(async () => {
    setIsRefreshing(true);

    try {
      const [
        tripAuditRes,
        routingHealthRes,
        pagingHealthRes,
        routingHealthTriageRes,
        routingHealthSuppressedRes,
      ] = await Promise.all([
        fetch("/api/audit?limit=50", { cache: "no-store" }),
        fetch("/legacy_ops/audit?limit=100&event_type=routing_health_alert", {
          cache: "no-store",
        }),
        fetch("/legacy_ops/audit?limit=100&event_type=routing_health_paging_alert", {
          cache: "no-store",
        }),
        fetch("/legacy_ops/audit?limit=100&event_type=routing_health_alert_triage", {
          cache: "no-store",
        }),
        fetch("/legacy_ops/audit?limit=100&event_type=routing_health_paging_alert_suppressed", {
          cache: "no-store",
        }),
      ]);

      if (!tripAuditRes.ok) throw new Error(`HTTP ${tripAuditRes.status}`);
      if (!routingHealthRes.ok) throw new Error(`HTTP ${routingHealthRes.status}`);
      if (!pagingHealthRes.ok) throw new Error(`HTTP ${pagingHealthRes.status}`);
      if (!routingHealthTriageRes.ok) throw new Error(`HTTP ${routingHealthTriageRes.status}`);
      if (!routingHealthSuppressedRes.ok) {
        throw new Error(`HTTP ${routingHealthSuppressedRes.status}`);
      }

      const [tripAuditRaw, routingHealthRaw, routingPagingRaw, routingTriageRaw, routingSuppressedRaw] =
        await Promise.all([
          tripAuditRes.json(),
          routingHealthRes.json(),
          pagingHealthRes.json(),
          routingHealthTriageRes.json(),
          routingHealthSuppressedRes.json(),
        ]);

      const tripEvents = toEntries(tripAuditRaw);
      const routingHealthAlerts = toEntries(routingHealthRaw);
      const routingHealthPagingAlerts = toEntries(routingPagingRaw);
      const routingHealthAlertTriages = toEntries(routingTriageRaw);
      const routingHealthPagingSuppressions = toEntries(routingSuppressedRaw);

      dispatch({
        type: "loaded",
        sources: {
          tripEvents,
          routingHealthAlerts,
          routingHealthPagingAlerts,
          routingHealthAlertTriages,
          routingHealthPagingSuppressions,
        },
      });

      setLastRefreshAt(new Date().toISOString());
    } catch (err) {
      dispatch({ type: "failed", error: err instanceof Error ? err.message : "Failed to load audit events" });
      setLastRefreshAt(new Date().toISOString());
    } finally {
      setIsRefreshing(false);
    }
  }, [dispatch]);

  useEffect(() => {
    let cancelled = false;
    void fetchAudit();

    let timer: ReturnType<typeof setInterval> | null = null;
    if (autoRefreshEnabled) {
      timer = setInterval(() => {
        if (!cancelled) {
          void fetchAudit();
        }
      }, autoRefreshMs);
    }

    return () => {
      cancelled = true;

      if (timer) {
        clearInterval(timer);
      }
    };
  }, [autoRefreshEnabled, autoRefreshMs, fetchAudit]);

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
        and operator overrides, plus routing health escalation signals.
      </p>

      <section
        className="mb-6 rounded border border-muted p-3 space-y-2"
        aria-label="Live refresh controls"
      >
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            className="text-xs border rounded px-2 py-1"
            onClick={() => setAutoRefreshEnabled((previous) => !previous)}
            aria-label={autoRefreshEnabled ? "Pause live refresh" : "Enable live refresh"}
          >
            {autoRefreshEnabled ? "Pause live refresh" : "Enable live refresh"}
          </button>
          <button
            type="button"
            className="text-xs border rounded px-2 py-1"
            onClick={() => void fetchAudit()}
            disabled={isRefreshing}
          >
            {isRefreshing ? "Refreshing…" : "Refresh now"}
          </button>
          <p className="text-xs text-muted-foreground">
            status: {autoRefreshEnabled ? "live" : "paused"} · interval: {autoRefreshMs / 1000}s
          </p>
        </div>
        <p className="text-xs text-muted-foreground">
          last refresh: {lastRefreshAt ? new Date(lastRefreshAt).toLocaleTimeString() : "never"}
        </p>
      </section>

      {tripEvents.length === 0 ? (
        <p className="text-muted-foreground">No audit events recorded yet.</p>
      ) : (
        <EventRows
          title="Trip audit events"
          events={tripEvents}
          formatter={(event) => `${event.type} • ${event.user_id || "system"}`}
        />
      )}

      <div className="mt-8 space-y-8">
        <RoutingHealthAlertRows
          events={routingHealthAlerts}
          triageByAlert={triageByAlert}
          selectedAlertIds={selectedAlertIds}
          onToggleAlertSelection={toggleAlertSelection}
          onTriage={handleTriage}
        />

        <section className="rounded border border-dashed p-3 space-y-3">
          <h2 className="text-base font-semibold">Batch triage</h2>
          <p className="text-sm text-muted-foreground">
            Selected alerts: {selectedAlertCount}
          </p>
          <div className="flex flex-wrap gap-2 items-end">
            <label className="text-xs text-muted-foreground" htmlFor="batch-action">
              Action
            </label>
            <select
              id="batch-action"
              className="border rounded px-2 py-1 text-xs"
              value={batchAction}
              onChange={(evt) => setBatchAction(evt.target.value as AuditTriageAction)}
            >
              <option value="acknowledge">Acknowledge</option>
              <option value="close">Close</option>
              <option value="escalate">Escalate</option>
            </select>
            <label className="text-xs text-muted-foreground" htmlFor="batch-note">
              Note
            </label>
            <input
              id="batch-note"
              className="border rounded px-2 py-1 text-xs min-w-[240px]"
              value={batchNote}
              onChange={(evt) => setBatchNote(evt.target.value)}
              placeholder="Optional note for all selected"
            />
            <button
              type="button"
              className="text-xs border rounded px-2 py-1"
              disabled={isBatchSubmitting}
              onClick={() => void handleBatchTriage()}
            >
              Run batch triage
            </button>
          </div>
          {batchError ? <p className="text-destructive text-xs">{batchError}</p> : null}
          {batchResult ? (
            <p className="text-xs text-muted-foreground">
              batch result: requested={batchResult.requested}, succeeded={batchResult.succeeded},
              failed={batchResult.failed}
            </p>
          ) : null}
        </section>

        <RoutingHealthPagingAlertRows
          events={routingHealthPagingAlerts}
          onSuppress={handleSuppressPaging}
        />

        <EventRows
          title="Routing health paging suppressions"
          events={routingHealthPagingSuppressions}
          formatter={(event) => `suppressed_for:${event.details.suppress_for_minutes ?? "-"}m`}
        />

        <section className="rounded border border-dashed p-3 space-y-3">
          <h2 className="text-base font-semibold">Routing-health evidence export</h2>
          <div className="flex gap-2 items-center">
            <label className="text-xs text-muted-foreground" htmlFor="export-format">
              Format
            </label>
            <select
              id="export-format"
              className="border rounded px-2 py-1 text-xs"
              value={exportFormat}
              onChange={(evt) => {
                setExportFormat(evt.target.value as "json" | "csv");
              }}
            >
              <option value="json">JSON</option>
              <option value="csv">CSV</option>
            </select>
            <button
              type="button"
              className="text-xs border rounded px-2 py-1"
              onClick={() => {
                void handleExportEvidence().catch((error) => {
                  setExportError(error instanceof Error ? error.message : "Unable to export evidence");
                });
              }}
            >
              Export evidence
            </button>
          </div>
          {exportError ? <p className="text-destructive text-xs">{exportError}</p> : null}
        </section>
      </div>
    </div>
  );
}
