"use client";

import { useMemo, useState, type ReactNode } from "react";
import Link from "next/link";
import { useParams, usePathname } from "next/navigation";
import { AlertTriangle, ChevronLeft, PanelRightClose, PanelRightOpen } from "lucide-react";
import { ErrorBoundary, InlineError } from "@/components/error-boundary";
import { InlineLoading } from "@/components/ui/loading";
import { useTrip } from "@/hooks/useTrips";
import { getTripRoute, type WorkspaceStage } from "@/lib/routes";
import { TripContextProvider } from "@/contexts/TripContext";
import { useWorkbenchStore } from "@/stores/workbench";
import { TimelineSummary } from "@/components/workspace/panels/TimelineSummary";

const STAGE_TABS: { id: WorkspaceStage; label: string }[] = [
  { id: "intake",   label: "Intake"          },
  { id: "packet",   label: "Trip Details"    },
  { id: "decision", label: "Quote Assessment"},
  { id: "strategy", label: "Options"         },
  { id: "output",   label: "Output"          },
  { id: "safety",   label: "Safety Review"   },
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

export function WorkspaceTripLayoutShell({ children }: { children: ReactNode }) {
  const params = useParams<{ tripId?: string | string[] }>();
  const pathname = usePathname();
  const tripId = parseTripId(params?.tripId);
  const { data: trip, isLoading, error, refetch: refetchTrip, replaceTrip } = useTrip(tripId);
  const [isRailOpen, setIsRailOpen] = useState(false);
  const { result_run_ts } = useWorkbenchStore();

  const activeStage = useMemo(() => getActiveStage(pathname), [pathname]);
  const accent = STATE_ACCENT[trip?.state ?? "blue"] ?? STATE_ACCENT.blue;
  const isLeadReview = trip?.status === "new" || trip?.status === "incomplete";
  const backHref = isLeadReview ? "/inbox" : "/trips";
  const backLabel = isLeadReview ? "Lead Inbox" : "Workspaces";

  if (isLoading && !trip) {
    return (
      <div className="p-6">
        <InlineLoading message="Loading workspace..." />
      </div>
    );
  }

  if (error || !tripId || !trip) {
    return (
      <div className="p-6">
        <div className="max-w-[900px] mx-auto rounded-xl border border-[#1c2128] bg-[#0f1115] p-6 space-y-4">
          <InlineError
            title="Workspace unavailable"
            message={error?.message ?? "Trip not found. Please return to Workspace list and try again."}
          />
          <Link
            href="/trips"
            className="inline-flex items-center gap-2 px-3 py-2 rounded-lg border border-[var(--border-default)] text-ui-sm text-[#e6edf3] hover:bg-[#161b22] transition-colors"
          >
            <ChevronLeft className="w-4 h-4" aria-hidden="true" />
            Back to Trips
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
                    {trip.destination || trip.id}
                  </span>
                </div>

                <button
                  type="button"
                  onClick={() => setIsRailOpen((open) => !open)}
                  className="inline-flex items-center gap-1.5 px-2.5 py-1.5 text-ui-xs rounded-lg border border-[var(--border-default)] hover:bg-[#161b22] transition-colors text-[var(--text-muted)] hover:text-[#e6edf3]"
                  aria-expanded={isRailOpen}
                  aria-controls="workspace-right-rail"
                >
                  {isRailOpen
                    ? <><PanelRightClose className="w-3.5 h-3.5" aria-hidden="true" /> Hide timeline</>
                    : <><PanelRightOpen  className="w-3.5 h-3.5" aria-hidden="true" /> Show timeline</>
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
                    {trip.destination || trip.id}
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
                      {accent.label}
                    </span>
                    {trip.type && (
                      <span className="text-[var(--ui-text-xs)] font-bold uppercase tracking-widest text-[var(--text-tertiary)]">
                        {trip.type}
                      </span>
                    )}
                    {trip.age && (
                      <span className="text-[var(--ui-text-xs)] text-[var(--text-tertiary)]">{trip.age}</span>
                    )}
                    <span className="text-[var(--ui-text-xs)] font-mono text-[var(--border-default)]">{trip.id}</span>
                    {result_run_ts && (
                      <span className="text-[var(--ui-text-xs)] text-[var(--border-default)]">
                        processed {new Date(result_run_ts).toLocaleTimeString()}
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* Stage tabs — underline style */}
              <nav
                className="flex overflow-x-auto gap-0 -mb-px"
                aria-label="Workspace stage tabs"
              >
                {STAGE_TABS.map((tab) => {
                  const isActive = tab.id === activeStage;
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
          <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_320px] gap-4">
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
                    <TimelineSummary tripId={tripId as string} />
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
