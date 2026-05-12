"use client";

import { useEffect, useMemo, useState, useRef, useReducer, type ReactNode } from "react";
import Link from "next/link";
import { useParams, usePathname } from "next/navigation";
import { AlertTriangle, ChevronLeft, Lock, PanelRightClose, PanelRightOpen } from "lucide-react";
import { ErrorBoundary, InlineError } from "@/components/error-boundary";
import { InlineLoading } from "@/components/ui/loading";
import { toast } from "@/lib/toast-store";
import { useTrip } from "@/hooks/useTrips";
import { ClientTime } from "@/hooks/useClientDate";
import {
  canAccessPlanningStage,
  getPlanningBlockerBody,
  getPlanningBlockerTitle,
  getPlanningHeaderTitle,
  getPlanningIdentityLine,
  getPlanningLockedTabHint,
  getPlanningNextAction,
  getPlanningQueueLine,
  getPlanningSuggestedNextMove,
  getPlanningStageGateReason,
  getPlanningStatusLabel,
  getPlanningStatusTone,
  getPlanningUnlockHint,
} from "@/lib/planning-status";
import { getPlanningStageProgressItems } from "@/lib/planning-list-display";
import { getTripRoute, type WorkspaceStage } from "@/lib/routes";
import { TripContextProvider } from "@/contexts/TripContext";
import { useWorkbenchStore } from "@/stores/workbench";
import { TimelineSummary } from "@/components/workspace/panels/TimelineSummary";
import { hasImportantTimelineEvent } from "@/lib/timeline-rail";
import type { TimelineResponse } from "@/types/spine";

const STAGE_TABS: { id: WorkspaceStage; label: string }[] = [
  { id: "intake",   label: "Intake"          },
  { id: "packet",   label: "Trip Details"    },
  { id: "strategy", label: "Options"         },
  { id: "decision", label: "Quote Assessment"},
  { id: "output",   label: "Output"          },
  { id: "safety",   label: "Risk Review"     },
  { id: "timeline", label: "Timeline"        },
];

// State → accent colour mapping (matches WP design tokens)
const STATE_ACCENT: Record<string, { color: string; bg: string; border: string; label: string }> = {
  green: { color: '#3fb950', bg: 'rgba(63,185,80,0.08)',   border: 'rgba(63,185,80,0.22)',   label: 'Ready'         },
  amber: { color: '#d29922', bg: 'rgba(210,153,34,0.08)',  border: 'rgba(210,153,34,0.22)',  label: 'In Progress'   },
  red:   { color: '#f85149', bg: 'rgba(248,81,73,0.08)',   border: 'rgba(248,81,73,0.25)',   label: 'Needs Review'  },
  blue:  { color: '#58a6ff', bg: 'rgba(88,166,255,0.06)',  border: 'rgba(88,166,255,0.2)',   label: 'Awaiting Info' },
};

function parseTripId(param: string | string[] | undefined): string | null {
  if (!param) return null;
  return Array.isArray(param) ? (param[0] ?? null) : param;
}

function getActiveStage(pathname: string): WorkspaceStage {
  const segment = pathname.split("/").filter(Boolean).at(-1);
  const stage = STAGE_TABS.find((item) => item.id === segment)?.id;
  return stage ?? "intake";
}

type TimelineRailState =
  | { status: "idle"; timeline: TimelineResponse | null; error: null }
  | { status: "loading"; timeline: TimelineResponse | null; error: null }
  | { status: "success"; timeline: TimelineResponse; error: null }
  | { status: "error"; timeline: TimelineResponse | null; error: string };

type TimelineRailAction =
  | { type: "loading" }
  | { type: "loaded"; timeline: TimelineResponse }
  | { type: "failed"; error: string };

function timelineRailReducer(
  state: TimelineRailState,
  action: TimelineRailAction,
): TimelineRailState {
  switch (action.type) {
    case "loading":
      return { status: "loading", timeline: state.timeline, error: null };
    case "loaded":
      return { status: "success", timeline: action.timeline, error: null };
    case "failed":
      return { status: "error", timeline: state.timeline, error: action.error };
    default:
      return state;
  }
}

export function WorkspaceTripLayoutShell({ children }: { children: ReactNode }) {
  const params = useParams<{ tripId?: string | string[] }>();
  const pathname = usePathname();
  const tripId = parseTripId(params?.tripId);
  const { data: trip, isLoading, error, refetch: refetchTrip, replaceTrip } = useTrip(tripId);
  const [isRailOpen, setIsRailOpen] = useState(false);
  const [timelineState, dispatchTimeline] = useReducer(timelineRailReducer, {
    status: "idle",
    timeline: null,
    error: null,
  });
  const hasRailPreferenceRef = useRef(false);
  const { result_run_ts } = useWorkbenchStore();

  const activeStage = useMemo(() => getActiveStage(pathname), [pathname]);
  const isLeadReview = trip?.status === "new" || trip?.status === "incomplete";
  const planningTone = getPlanningStatusTone(trip);
  const accent = STATE_ACCENT[planningTone ?? "blue"] ?? STATE_ACCENT.blue;
  const backHref = "/trips";
  const backLabel = "Trips in Planning";
  const planningTitle = getPlanningHeaderTitle(trip);
  const planningIdentity = getPlanningIdentityLine(trip);
  const planningQueueLine = getPlanningQueueLine(trip);
  const planningUnlockHint = getPlanningUnlockHint(trip);
  const visibleTabs = STAGE_TABS;
  const stageProgressItems = useMemo(() => getPlanningStageProgressItems(trip), [trip]);
  const timelineEvents = timelineState.timeline?.events ?? [];
  const timelineLoading = timelineState.status === "loading";
  const timelineError = timelineState.error;

  useEffect(() => {
    hasRailPreferenceRef.current = false;
    setIsRailOpen(false);
    // Resets rail on trip change - ref + state are coupled and cannot be batched
  }, [tripId]);

  // Auto-close side rail when on Timeline tab (avoids duplicate activity views)
  useEffect(() => {
    if (activeStage === 'timeline') {
      setIsRailOpen(false);
    }
  }, [activeStage]);

  useEffect(() => {
    if (!tripId || isLoading || !trip) return;

    let cancelled = false;

    const fetchTimeline = async () => {
      try {
        dispatchTimeline({ type: "loading" });
        const response = await fetch(`/api/trips/${tripId}/timeline`, {
          credentials: "include",
          cache: "no-store",
        });
        if (!response.ok) throw new Error(`Failed to fetch timeline: ${response.statusText}`);
        const data = (await response.json()) as TimelineResponse;
        if (cancelled) return;
        dispatchTimeline({ type: "loaded", timeline: data });
        if (!hasRailPreferenceRef.current) {
          setIsRailOpen(hasImportantTimelineEvent(data.events ?? []));
        }
      } catch (err) {
        if (cancelled) return;
        dispatchTimeline({ type: "failed", error: err instanceof Error ? err.message : "Failed to load timeline" });
      }
    };

    void fetchTimeline();

    return () => {
      cancelled = true;
    };
  }, [tripId, isLoading, trip?.id]);

  if (isLoading && !trip) {
    return (
      <div className="p-6">
        <InlineLoading message="Loading workspace…" />
      </div>
    );
  }

  if (error || !tripId || !trip) {
    const fallbackTitle = "Workspace unavailable";
    const fallbackMessage = "Trip not found. Please return to Trips in Planning and try again.";
    const fallbackHref = "/trips";
    const fallbackLabel = "Back to Trips in Planning";
    return (
      <div className="p-6">
        <div className="max-w-[900px] mx-auto rounded-xl border border-[#1c2128] bg-[#0f1115] p-6 space-y-4">
          <InlineError
            title={fallbackTitle}
            message={error?.message ?? fallbackMessage}
          />
          <Link
            href={fallbackHref}
            className="inline-flex items-center gap-2 px-3 py-2 rounded-lg border border-[var(--border-default)] text-ui-sm text-[#e6edf3] hover:bg-[#161b22] transition-colors"
          >
            <ChevronLeft className="size-4" aria-hidden="true" />
            {fallbackLabel}
          </Link>
        </div>
      </div>
    );
  }

  return (
    <TripContextProvider value={{ tripId, trip, isLoading, error, refetchTrip, replaceTrip }}>
      <div className="min-h-full bg-[#080a0c] text-[#e6edf3]">
        <div className="max-w-[1600px] mx-auto px-4 sm:px-6 py-5 space-y-4">

          {/* ── Trip header ── */}
          <header
            className="rounded-xl border overflow-hidden"
            style={{ borderColor: accent.border, background: accent.bg }}
          >
            {/* State accent strip */}
            <div className="h-[3px] w-full" style={{ background: accent.color }} />

            <div className="px-5 pt-4 pb-0">
              {/* Top row: breadcrumb + timeline toggle */}
              <div className="flex items-center justify-between gap-3 mb-3">
                <div className="flex items-center gap-2 text-ui-xs text-[var(--text-tertiary)]">
                  <Link href={backHref} className="hover:text-[var(--text-muted)] transition-colors flex items-center gap-1">
                    <ChevronLeft className="size-3" />
                    {backLabel}
                  </Link>
                  <span>/</span>
                  <span className="text-[var(--text-muted)] truncate max-w-[200px]">
                    {getPlanningHeaderTitle(trip)}
                  </span>
                </div>

                <button
                  type="button"
                  onClick={() => {
                    hasRailPreferenceRef.current = true;
                    setIsRailOpen((open) => !open);
                  }}
                  className="inline-flex items-center gap-1.5 px-2.5 py-1.5 text-ui-xs rounded-lg border border-[var(--border-default)] hover:bg-[#161b22] transition-colors text-[var(--text-muted)] hover:text-[#e6edf3]"
                  aria-expanded={isRailOpen}
                  aria-controls="workspace-right-rail"
                >
                  {isRailOpen
                    ? <><PanelRightClose className="size-3.5" aria-hidden="true" /> Hide activity</>
                    : <><PanelRightOpen  className="size-3.5" aria-hidden="true" /> Show activity</>
                  }
                </button>
              </div>

              {/* Main identity row */}
              <div className="flex items-start justify-between gap-4 mb-3">
                <div className="min-w-0">
                  <h1
	                    className="text-ui-2xl font-semibold tracking-tight leading-none mb-2 truncate"
                    style={{ fontFamily: "'Outfit', system-ui, sans-serif", color: '#f0f6fc' }}
                  >
                    {planningTitle}
                  </h1>
                  <div className="flex flex-wrap items-center gap-2">
                    {/* State badge */}
                    <span
                      className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-ui-xs font-bold"
                      style={{ color: accent.color, background: `${accent.color}18`, border: `1px solid ${accent.border}` }}
                    >
                      <span
                        className="size-1.5 rounded-full"
                        style={{ background: accent.color, boxShadow: `0 0 4px ${accent.color}` }}
                      />
                      {getPlanningStatusLabel(trip)}
                    </span>
                    {planningIdentity && (
                      <span className="text-[var(--ui-text-xs)] text-[var(--text-tertiary)]">
                        {planningIdentity}
                      </span>
                    )}
                    <span className="text-[var(--ui-text-xs)] text-[var(--border-default)]">
                      {planningQueueLine}
                    </span>
                    {result_run_ts && (
                      <span className="text-[var(--ui-text-xs)] text-[var(--border-default)]">
                        processed <ClientTime value={result_run_ts} />
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* Stage tabs - underline style */}
              {planningUnlockHint && (
                <div className="mb-2 flex items-center gap-2 rounded-lg border border-[rgba(210,153,34,0.22)] bg-[rgba(210,153,34,0.06)] px-3 py-2">
                  <Lock className="size-3.5 shrink-0 text-[var(--accent-amber)]" aria-hidden="true" />
                  <span className="text-[12px] font-medium text-[var(--text-secondary)]">
                    {planningUnlockHint}
                  </span>
                </div>
              )}
              <div className="mb-2 flex flex-wrap items-center gap-x-1.5 gap-y-1 px-1">
                <span className="text-[12px] font-semibold uppercase tracking-[0.14em] text-[var(--text-tertiary)]">
                  Stage
                </span>
                {stageProgressItems.map((item, index) => (
                  <span key={item.label} className="flex items-center">
                    <span className="text-[12px] font-medium" style={{ color: item.color }}>
                      {item.label}
                    </span>
                    {index < stageProgressItems.length - 1 && (
                      <span className="mx-1 text-[12px] text-[var(--text-muted)]">→</span>
                    )}
                  </span>
                ))}
              </div>
              <nav
                className="flex overflow-x-auto gap-0 -mb-px"
                aria-label="Workspace stage tabs"
              >
                {visibleTabs.map((tab) => {
                  const isActive = tab.id === activeStage;
                  const isAccessible = canAccessPlanningStage(trip, tab.id);
                  const gateReason = getPlanningStageGateReason(trip, tab.id);
                  const lockedLabel = getPlanningLockedTabHint(trip, tab.id);

                  if (!isAccessible) {
                    return (
                      <button
                        key={tab.id}
                        type="button"
                        onClick={() => toast(gateReason ?? `Complete the current stage first to unlock ${tab.label}.`, 'info')}
                        aria-current={isActive ? "page" : undefined}
                        aria-disabled="true"
                        title={gateReason ?? undefined}
                        className="px-4 py-2.5 whitespace-nowrap border-b-2 cursor-pointer hover:opacity-80 transition-opacity text-left"
                        style={{
                          color: "var(--text-secondary)",
                          borderColor: isActive ? accent.color : `${accent.color}55`,
                        }}
                      >
                        <div
                          className="flex items-center gap-1.5 text-[13px]"
                          style={{ fontWeight: isActive ? 600 : 500 }}
                        >
                          <Lock className="size-3.5 shrink-0 text-[var(--accent-amber)]" aria-hidden="true" />
                          <span>{tab.label}</span>
                        </div>
                        {lockedLabel && (
                          <div className="mt-0.5 text-[12px] leading-tight text-[var(--text-secondary)]">
                            {lockedLabel}
                          </div>
                        )}
                      </button>
                    );
                  }

                  return (
                    <Link
                      key={tab.id}
                      href={getTripRoute(tripId, tab.id)}
                      aria-current={isActive ? "page" : undefined}
                      className="px-4 py-2.5 text-[13px] whitespace-nowrap border-b-2 transition-all rounded-t-md"
                      style={{
                        color: isActive ? '#e6edf3' : 'var(--text-tertiary)',
                        borderColor: isActive ? accent.color : 'transparent',
                        background: isActive ? `${accent.color}1a` : 'transparent',
                        fontWeight: isActive ? 600 : 400,
                      }}
                    >
                      {tab.label}
                    </Link>
                  );
                })}
              </nav>
            </div>
          </header>

          {/* ── Flags alert - shown separately if blocked ── */}
          {trip.state === 'red' && (
            <div className="flex items-center gap-3 px-4 py-3 rounded-xl border border-[rgba(248,81,73,0.35)] bg-[rgba(248,81,73,0.07)]">
              <AlertTriangle className="size-4 text-[#f85149] shrink-0" aria-hidden="true" />
              <span className="text-ui-sm font-semibold text-[#f85149]">Action required</span>
              <span className="text-ui-sm text-[#c9d1d9]">This trip has blockers that must be resolved before it can proceed.</span>
            </div>
          )}

          {/* ── Main content + optional rail ── */}
          <div className={isRailOpen ? "grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_320px] gap-4" : "grid grid-cols-1 gap-4"}>
            <main className="rounded-xl border border-[#1c2128] bg-[#0f1115] min-h-[440px]">
              {children}
            </main>

            {isRailOpen && (
              <aside
                id="workspace-right-rail"
                className="rounded-xl border border-[#1c2128] bg-[#0f1115] h-[calc(100vh-140px)] overflow-hidden flex flex-col"
                aria-label="Trip timeline"
              >
                <div className="border-b border-[#1c2128] p-3 space-y-2">
                  <div className="rounded-lg border border-[rgba(88,166,255,0.25)] bg-[rgba(88,166,255,0.08)] p-2.5">
                    <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-[#58a6ff]">Next Suggestions</p>
                    <p className="mt-1 text-[12px] text-[#c9d1d9]">{getPlanningSuggestedNextMove(isLeadReview, trip)}</p>
                  </div>
                  <div className="rounded-lg border border-[rgba(48,54,61,0.9)] bg-[rgba(255,255,255,0.02)] p-2.5">
                    <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-[var(--text-tertiary)]">
                      {getPlanningBlockerTitle(isLeadReview, trip)}
                    </p>
                    <p className="mt-1 text-[12px] text-[var(--text-secondary)]">
                      {getPlanningBlockerBody(isLeadReview, trip)}
                    </p>
                    <p className="mt-1.5 text-[12px] text-[var(--text-muted)]">{getPlanningNextAction(trip)}</p>
                  </div>
                </div>
                <div className="flex-1 overflow-y-auto">
                  <ErrorBoundary>
                    <TimelineSummary
                      tripId={tripId as string}
                      timeline={timelineState.timeline}
                      loading={timelineLoading}
                      error={timelineError}
                    />
                  </ErrorBoundary>
                </div>
              </aside>
            )}
          </div>
        </div>
      </div>
    </TripContextProvider>
  );
}

export default function WorkspaceTripLayout({ children }: { children: ReactNode }) {
  return (
    <ErrorBoundary>
      <WorkspaceTripLayoutShell>{children}</WorkspaceTripLayoutShell>
    </ErrorBoundary>
  );
}
