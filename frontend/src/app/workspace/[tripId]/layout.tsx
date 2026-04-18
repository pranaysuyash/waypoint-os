"use client";

import { useMemo, useState, type ReactNode } from "react";
import Link from "next/link";
import { useParams, usePathname } from "next/navigation";
import { ChevronLeft, PanelRightClose, PanelRightOpen } from "lucide-react";
import { ErrorBoundary, InlineError } from "@/components/error-boundary";
import { InlineLoading } from "@/components/ui/loading";
import { useTrip } from "@/hooks/useTrips";
import { getTripRoute, type WorkspaceStage } from "@/lib/routes";
import { TripContextProvider } from "@/contexts/TripContext";

const STAGE_TABS: { id: WorkspaceStage; label: string }[] = [
  { id: "intake", label: "Intake" },
  { id: "packet", label: "Packet" },
  { id: "decision", label: "Decision" },
  { id: "strategy", label: "Strategy" },
  { id: "output", label: "Output" },
  { id: "safety", label: "Safety" },
];

const STATE_META: Record<string, { label: string; className: string }> = {
  green: { label: "Ready", className: "text-[#3fb950] bg-[#3fb950]/10" },
  amber: { label: "In Progress", className: "text-[#d29922] bg-[#d29922]/10" },
  red: { label: "Needs Review", className: "text-[#f85149] bg-[#f85149]/10" },
  blue: { label: "Awaiting Info", className: "text-[#58a6ff] bg-[#58a6ff]/10" },
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
  const { data: trip, isLoading, error } = useTrip(tripId);
  const [isRailOpen, setIsRailOpen] = useState(false);

  const activeStage = useMemo(() => getActiveStage(pathname), [pathname]);
  const stateMeta = STATE_META[trip?.state ?? "blue"] ?? STATE_META.blue;

  if (isLoading && !trip) {
    return (
      <div className="min-h-screen bg-[#080a0c] p-6">
        <InlineLoading message="Loading workspace..." />
      </div>
    );
  }

  if (error || !tripId || !trip) {
    return (
      <div className="min-h-screen bg-[#080a0c] p-6">
        <div className="max-w-[900px] mx-auto rounded-xl border border-[#1c2128] bg-[#0f1115] p-6 space-y-4">
          <InlineError
            title="Workspace unavailable"
            message={error?.message ?? "Trip not found. Please return to Workspace list and try again."}
          />
          <Link
            href="/workspace"
            className="inline-flex items-center gap-2 px-3 py-2 rounded-lg border border-[#30363d] text-sm text-[#e6edf3] hover:bg-[#161b22] transition-colors"
          >
            <ChevronLeft className="w-4 h-4" aria-hidden="true" />
            Back to Workspaces
          </Link>
        </div>
      </div>
    );
  }

  return (
    <TripContextProvider value={{ tripId, trip, isLoading, error }}>
      <div className="min-h-screen bg-[#080a0c] text-[#e6edf3]">
        <div className="max-w-[1600px] mx-auto px-4 sm:px-6 py-5 space-y-4">
          <header className="rounded-xl border border-[#1c2128] bg-[#0f1115] p-4 sm:p-5">
            <div className="flex items-start justify-between gap-3">
              <div className="space-y-1 min-w-0">
                <div className="flex items-center gap-2 text-xs text-[#8b949e]">
                  <Link href="/workspace" className="hover:text-[#c9d1d9] transition-colors">
                    Workspace
                  </Link>
                  <span>/</span>
                  <span className="truncate">{trip.destination || trip.id}</span>
                </div>
                <h1 className="text-lg sm:text-xl font-semibold truncate">
                  {trip.destination || trip.id}
                </h1>
                <div className="flex flex-wrap items-center gap-2 text-xs text-[#8b949e]">
                  <span className={`px-2 py-0.5 rounded-md font-medium ${stateMeta.className}`}>
                    {stateMeta.label}
                  </span>
                  <span>{trip.type}</span>
                  <span>•</span>
                  <span>{trip.age}</span>
                  <span>•</span>
                  <span className="font-mono">{trip.id}</span>
                </div>
              </div>

              <button
                type="button"
                onClick={() => setIsRailOpen((open) => !open)}
                className="inline-flex items-center gap-2 px-3 py-2 text-sm rounded-lg border border-[#30363d] hover:bg-[#161b22] transition-colors"
                aria-expanded={isRailOpen}
                aria-controls="workspace-right-rail"
              >
                {isRailOpen ? (
                  <PanelRightClose className="w-4 h-4" aria-hidden="true" />
                ) : (
                  <PanelRightOpen className="w-4 h-4" aria-hidden="true" />
                )}
                {isRailOpen ? "Hide AI rail" : "Show AI rail"}
              </button>
            </div>

            <nav className="mt-4 border-t border-[#1c2128] pt-3" aria-label="Workspace stage tabs">
              <div className="flex overflow-x-auto gap-2 pb-1">
                {STAGE_TABS.map((tab) => {
                  const isActive = tab.id === activeStage;
                  return (
                    <Link
                      key={tab.id}
                      href={getTripRoute(tripId, tab.id)}
                      aria-current={isActive ? "page" : undefined}
                      className={`px-3 py-1.5 rounded-lg text-sm transition-colors whitespace-nowrap border ${
                        isActive
                          ? "border-[#58a6ff] bg-[#58a6ff]/10 text-[#c9d1d9]"
                          : "border-[#30363d] text-[#8b949e] hover:text-[#c9d1d9] hover:bg-[#161b22]"
                      }`}
                    >
                      {tab.label}
                    </Link>
                  );
                })}
              </div>
            </nav>
          </header>

          <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_320px] gap-4">
            <main className="rounded-xl border border-[#1c2128] bg-[#0f1115] min-h-[440px]">
              {children}
            </main>

            {isRailOpen && (
              <aside
                id="workspace-right-rail"
                className="rounded-xl border border-[#1c2128] bg-[#0f1115] p-4"
                aria-label="Right rail"
              >
                <h2 className="text-sm font-semibold text-[#c9d1d9]">AI Copilot Panel</h2>
                <p className="text-xs text-[#8b949e] mt-2 leading-relaxed">
                  Collapsed-by-default Wave 2 container. Stage-aware copilots and insights will
                  land incrementally without reshaping the workspace frame.
                </p>
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
