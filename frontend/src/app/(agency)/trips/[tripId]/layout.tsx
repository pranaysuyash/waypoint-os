"use client";

import { useEffect, useMemo, useState, type ReactNode } from "react";
import Link from "next/link";
import { useParams, usePathname } from "next/navigation";
import { AlertTriangle, ChevronLeft, Lock, PanelRightClose, PanelRightOpen } from "lucide-react";
import { ErrorBoundary, InlineError } from "@/components/error-boundary";
import { InlineLoading } from "@/components/ui/loading";
import { useTrip } from "@/hooks/useTrips";
import { formatBudgetDisplay, formatDateWindowDisplay, formatInquiryReference, formatLeadTitle } from "@/lib/lead-display";
import {
  canAccessPlanningStage,
  getPlanningHeaderTitle,
  getPlanningIdentityLine,
  getPlanningLockedTabHint,
  getPlanningQueueLine,
  getPlanningStageGateReason,
  getPlanningStatusLabel,
  getPlanningStatusTone,
  getPlanningUnlockHint,
} from "@/lib/planning-status";
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
  { id: "safety",   label: "Safety Review"   },
  { id: "timeline", label: "Timeline"        },
];

const LEAD_REVIEW_TABS: { id: WorkspaceStage; label: string }[] = [
  { id: "intake", label: "Intake" },
  { id: "packet", label: "Trip Details" },
  { id: "timeline", label: "Timeline" },
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

export function WorkspaceTripLayoutShell({ children }: { children: ReactNode }) {
  const params = useParams<{ tripId?: string | string[] }>();
  const pathname = usePathname();
  const tripId = parseTripId(params?.tripId);
  const { data: trip, isLoading, error, refetch: refetchTrip, replaceTrip } = useTrip(tripId);
  const [isRailOpen, setIsRailOpen] = useState(false);
  const [hasRailPreference, setHasRailPreference] = useState(false);
  const [timeline, setTimeline] = useState<TimelineResponse | null>(null);
  const [timelineLoading, setTimelineLoading] = useState(false);
  const [timelineError, setTimelineError] = useState<string | null>(null);
  const { result_run_ts } = useWorkbenchStore();
  const isIntakeRoute = pathname.endsWith("/intake");

  const activeStage = useMemo(() => getActiveStage(pathname), [pathname]);
  const isLeadReview = trip?.status === "new" || trip?.status === "incomplete";
  const optimisticLeadReview = isIntakeRoute && (!trip || isLoading);
  const planningTone = getPlanningStatusTone(trip);
  const accent = isLeadReview
    ? (trip?.status === "incomplete" ? STATE_ACCENT.amber : STATE_ACCENT.blue)
    : (STATE_ACCENT[planningTone ?? "blue"] ?? STATE_ACCENT.blue);
  const backHref = isLeadReview ? "/inbox" : "/trips";
  const backLabel = isLeadReview ? "Lead Inbox" : "Trips in Planning";
  const leadTitle = formatLeadTitle(trip?.destination, trip?.type);
  const leadStatusLabel = trip?.status === "incomplete" ? "Needs details" : "New lead";
  const leadMeta = [
    trip?.party ? `${trip.party} pax` : null,
    trip?.dateWindow ? formatDateWindowDisplay(trip.dateWindow) : null,
    formatBudgetDisplay(trip?.budget),
    trip?.id ? `Inquiry Ref ${formatInquiryReference(trip.id)}` : null,
  ].filter(Boolean);
  const planningTitle = getPlanningHeaderTitle(trip);
  const planningIdentity = getPlanningIdentityLine(trip);
  const planningQueueLine = getPlanningQueueLine(trip);
  const planningUnlockHint = getPlanningUnlockHint(trip);
  const visibleTabs = isLeadReview ? LEAD_REVIEW_TABS : STAGE_TABS;
  const timelineEvents = timeline?.events ?? [];

  useEffect(() => {
    setHasRailPreference(false);
    setIsRailOpen(false);
  }, [tripId]);

  useEffect(() => {
    if (!tripId) return;

    let cancelled = false;

    const fetchTimeline = async () => {
      try {
        setTimelineLoading(true);
        setTimelineError(null);
        const response = await fetch(`/api/trips/${tripId}/timeline`, {
          credentials: "include",
          cache: "no-store",
        });
        if (!response.ok) throw new Error(`Failed to fetch timeline: ${response.statusText}`);
        const data = (await response.json()) as TimelineResponse;
        if (cancelled) return;
        setTimeline(data);
        if (!hasRailPreference) {
          setIsRailOpen(hasImportantTimelineEvent(data.events ?? []));
        }
      } catch (err) {
        if (cancelled) return;
        setTimelineError(err instanceof Error ? err.message : "Failed to load timeline");
      } finally {
        if (!cancelled) setTimelineLoading(false);
      }
    };

    void fetchTimeline();

    return () => {
      cancelled = true;
    };
  }, [tripId, hasRailPreference]);

  if (isLoading && !trip) {
    return (
      <div className="p-6">
        <InlineLoading message={optimisticLeadReview ? "Loading lead review..." : "Loading workspace..."} />
      </div>
    );
  }

  if (error || !tripId || !trip) {
    const fallbackTitle = optimisticLeadReview ? "Lead unavailable" : "Workspace unavailable";
    const fallbackMessage = optimisticLeadReview
      ? "Lead not found. Please return to Lead Inbox and try again."
      : "Trip not found. Please return to Trips in Planning and try again.";
    const fallbackHref = optimisticLeadReview ? "/inbox" : "/trips";
    const fallbackLabel = optimisticLeadReview ? "Back to Lead Inbox" : "Back to Trips in Planning";
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
            <ChevronLeft className="w-4 h-4" aria-hidden="true" />
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
                    <ChevronLeft className="w-3 h-3" />
                    {backLabel}
                  </Link>
                  <span>/</span>
                  <span className="text-[var(--text-muted)] truncate max-w-[200px]">
                    {isLeadReview ? (trip.destination || "Lead review") : getPlanningHeaderTitle(trip)}
                  </span>
                </div>

                <button
                  type="button"
                  onClick={() => {
                    setHasRailPreference(true);
                    setIsRailOpen((open) => !open);
                  }}
                  className="inline-flex items-center gap-1.5 px-2.5 py-1.5 text-ui-xs rounded-lg border border-[var(--border-default)] hover:bg-[#161b22] transition-colors text-[var(--text-muted)] hover:text-[#e6edf3]"
                  aria-expanded={isRailOpen}
                  aria-controls="workspace-right-rail"
                >
                  {isRailOpen
                    ? <><PanelRightClose className="w-3.5 h-3.5" aria-hidden="true" /> Hide activity</>
                    : <><PanelRightOpen  className="w-3.5 h-3.5" aria-hidden="true" /> Show activity</>
                  }
                </button>
              </div>

              {/* Main identity row */}
              <div className="flex items-start justify-between gap-4 mb-3">
                <div className="min-w-0">
                  <h1
                    className="text-ui-2xl font-black tracking-tight leading-none mb-2 truncate"
                    style={{ fontFamily: "'Outfit', system-ui, sans-serif", color: '#f0f6fc' }}
                  >
                    {isLeadReview ? leadTitle : planningTitle}
                  </h1>
                  <div className="flex flex-wrap items-center gap-2">
                    {/* State badge */}
                    <span
                      className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-ui-xs font-bold"
                      style={{ color: accent.color, background: `${accent.color}18`, border: `1px solid ${accent.border}` }}
                    >
                      <span
                        className="w-1.5 h-1.5 rounded-full"
                        style={{ background: accent.color, boxShadow: `0 0 4px ${accent.color}` }}
                      />
                      {isLeadReview ? leadStatusLabel : getPlanningStatusLabel(trip)}
                    </span>
                    {isLeadReview ? (
                      <span className="text-[var(--ui-text-xs)] text-[var(--text-tertiary)]">
                        {leadMeta.join(" · ")}
                      </span>
                    ) : (
                      <>
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
                            processed {new Date(result_run_ts).toLocaleTimeString()}
                          </span>
                        )}
                       </>
                     )}
                   </div>
                </div>
              </div>

              {/* Stage tabs — underline style */}
              {planningUnlockHint && (
                <div className="mb-2 flex items-center gap-2 rounded-lg border border-[rgba(210,153,34,0.22)] bg-[rgba(210,153,34,0.06)] px-3 py-2">
                  <Lock className="h-3.5 w-3.5 shrink-0 text-[var(--accent-amber)]" aria-hidden="true" />
                  <span className="text-[12px] font-medium text-[var(--text-secondary)]">
                    {planningUnlockHint}
                  </span>
                </div>
              )}
              <nav
                className="flex overflow-x-auto gap-0 -mb-px"
                aria-label="Workspace stage tabs"
              >
                {visibleTabs.map((tab) => {
                  const isActive = tab.id === activeStage;
                  const isAccessible = isLeadReview || canAccessPlanningStage(trip, tab.id);
                  const gateReason = isLeadReview ? null : getPlanningStageGateReason(trip, tab.id);
                  const lockedLabel = isLeadReview ? null : getPlanningLockedTabHint(trip, tab.id);

                  if (!isAccessible) {
                    return (
                      <div
                        key={tab.id}
                        aria-current={isActive ? "page" : undefined}
                        aria-disabled="true"
                        title={gateReason ?? undefined}
                        className="px-4 py-2.5 whitespace-nowrap border-b-2"
                        style={{
                          color: "var(--text-secondary)",
                          borderColor: isActive ? accent.color : `${accent.color}55`,
                        }}
                      >
                        <div
                          className="flex items-center gap-1.5 text-[13px]"
                          style={{ fontWeight: isActive ? 600 : 500 }}
                        >
                          <Lock className="h-3.5 w-3.5 shrink-0 text-[var(--accent-amber)]" aria-hidden="true" />
                          <span>{tab.label}</span>
                        </div>
                        {lockedLabel && (
                          <div className="mt-0.5 text-[11px] leading-tight text-[var(--text-secondary)]">
                            {lockedLabel}
                          </div>
                        )}
                      </div>
                    );
                  }

                  return (
                    <Link
                      key={tab.id}
                      href={getTripRoute(tripId, tab.id)}
                      aria-current={isActive ? "page" : undefined}
                      className="px-4 py-2.5 text-[13px] whitespace-nowrap border-b-2 transition-all"
                      style={{
                        color: isActive ? '#e6edf3' : 'var(--text-tertiary)',
                        borderColor: isActive ? accent.color : 'transparent',
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

          {/* ── Flags alert — shown separately if blocked ── */}
          {trip.state === 'red' && (
            <div className="flex items-center gap-3 px-4 py-3 rounded-xl border border-[rgba(248,81,73,0.35)] bg-[rgba(248,81,73,0.07)]">
              <AlertTriangle className="w-4 h-4 text-[#f85149] shrink-0" aria-hidden="true" />
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
                <div className="flex-1 overflow-y-auto">
                  <ErrorBoundary>
                    <TimelineSummary
                      tripId={tripId as string}
                      timeline={timeline}
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
