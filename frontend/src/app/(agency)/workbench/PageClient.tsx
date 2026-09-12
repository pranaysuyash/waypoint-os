'use client';

import Link from 'next/link';
import { useSearchParams, useRouter, usePathname } from 'next/navigation';
import dynamic from 'next/dynamic';
import { Suspense, useState, useCallback, useEffect, useRef, useReducer } from 'react';
import { ClientDateTime, ClientTime } from '@/hooks/useClientDate';
import { Tabs } from '@/components/ui/tabs';
import { PipelineFlow, type PipelineStageId } from './PipelineFlow';
import {
  Play,
  RotateCcw,
  Settings,
  CheckCircle,
  AlertTriangle,
  Save,
  ChevronRight,
} from 'lucide-react';
import { InlineLoading } from '@/components/ui/loading';
import { useTrip } from '@/hooks/useTrips';
import { useWorkbenchStore } from '@/stores/workbench';
import { useSpineRun } from '@/hooks/useSpineRun';
import { useSSEStream } from '@/hooks/useSSEStream';

import { useUpdateTrip } from '@/hooks/useTrips';
import { getWorkbenchBlockCopy, formatWorkbenchBlockReasonList, formatWorkbenchMissingFields } from '@/lib/workbench-blocking-copy';
import type {
  SpineRunRequest,
  SpineStage,
  OperatingMode,
  DecisionOutput,
  StrategyOutput,
  PromptBundle,
  ValidationReport,
} from '@/types/spine';
import type {
  FeeCalculationResult,
} from '@/types/spine';
import type { Trip } from '@/lib/api-client';
import { submitTripReviewAction, createDraft, getDraft, patchDraft, discardDraft, promoteDraft } from '@/lib/api-client';
import { getTripRoute, getPostRunTripRoute, getWorkbenchTripId, getTripRepairRoute } from '@/lib/routes';
import { buildRepairDeepLinkHref, getFirstRepairableFieldName } from '@/lib/repair-deep-link';
import type { WorkbenchStore, DraftStatus, SaveState } from '@/stores/workbench';
import { ErrorBoundary } from '@/components/error-boundary';
import { RunProgressPanel } from './RunProgressPanel';
import {
  REVIEW_MISSING_FIELDS_CONTROL_CLASSES,
  extractCompletedTripIdFromDraft,
  getPipelineStageForWorkbench,
  safeParseJson,
  toOperatingMode,
  toSpineStage,
  toWorkspaceTabId,
  workspaceTabs,
} from './workbench-state';

export { extractCompletedTripIdFromDraft } from './workbench-state';
import { ConfirmDialog } from '@/components/ui/confirm-dialog';
import { useHydrateStoreFromTrip } from '@/hooks/useHydrateStoreFromTrip';
import { useWorkbenchRunSync } from '@/hooks/useWorkbenchRunSync';
import { useWorkbenchDraftPersistence } from '@/hooks/useWorkbenchDraftPersistence';
import { useAuthStore } from '@/stores/auth';
import { ProtectedSurfaceNotice } from '@/components/auth/ProtectedSurfaceNotice';

const IntakeTab = dynamic(() => import('./IntakeTab'));
const PacketTab = dynamic(() => import('./PacketTab'));
const SafetyTab = dynamic(() => import('./SafetyTab'));
const PersonaCouncilPanel = dynamic(() => import('./PersonaCouncilPanel'));
const MemoryArchitectPanel = dynamic(() => import('./MemoryArchitectPanel').then(m => m.MemoryArchitectPanel));
const FrontierDashboard = dynamic(() =>
  import('@/components/workspace/FrontierDashboard').then((mod) => ({
    default: mod.FrontierDashboard,
  })),
);
const SettingsPanel = dynamic(() => import('./SettingsPanel'));
const ScenarioLab = dynamic(() => import('./ScenarioLab'));
const OutputPanel = dynamic(
  () => import('@/components/workspace/panels/OutputPanel'),
);
const FeedbackPanel = dynamic(
  () => import('@/components/workspace/panels/FeedbackPanel'),
);

// react-doctor-disable-next-line react-doctor/prefer-useReducer — too many independent state slices to consolidate meaningfully
function WorkbenchContent() {
  const searchParams = useSearchParams();
  const { push, refresh, replace } = useRouter();
  const pathname = usePathname();
  const getSearchParam = searchParams.get.bind(searchParams);
  const tripId = getWorkbenchTripId(searchParams);
  const draftParam = getSearchParam('draft');
  const stageParam = getSearchParam('stage');
  const scenarioParam = getSearchParam('scenario');
  const [completedTripId, setCompletedTripId] = useState<string | null>(null);

  // The ?stage= URL param drives Spine execution (not the pipeline UI)
  const spineStage = toSpineStage(stageParam) ?? 'discovery';
  const currentMode = toOperatingMode(getSearchParam('mode')) ?? 'normal_intake';
  const currentScenario = scenarioParam || '';

  const resolvedTripId = tripId ?? completedTripId;
  const {
    data: trip,
    isLoading: tripLoading,
    error: tripError,
  } = useTrip(resolvedTripId);
  useHydrateStoreFromTrip(trip);
  const store = useWorkbenchStore();

  const activeTab = toWorkspaceTabId(getSearchParam('tab')) ?? 'intake';

  const showPacket =
    Boolean(trip) ||
    Boolean(store.result_packet) ||
    Boolean(store.result_validation) ||
    store.draft_status === 'blocked' ||
    store.draft_status === 'failed';
  const {
    execute: executeSpineRun,
    isLoading: isSpineRunning,
    error: spineError,
    reset: resetSpine,
    runId: spineRunId,
    state: spineRunState,
  } = useSpineRun();

  // SSE / adaptive-polling live state subscription.
  // Connects when a run starts; merges live events into spineRunState so
  // RunProgressPanel reflects real-time progress without a page reload.
  // Falls back to polling when SSE is not available (NEXT_PUBLIC_SSE_ENABLED != 'true').
  const {
    connect: connectSSE,
    disconnect: disconnectSSE,
    isConnected: isSSEConnected,
    connectionMode: sseConnectionMode,
  } = useSSEStream();

  // Subscribe when a new run begins; disconnect on unmount or run change.
  useEffect(() => {
    if (!spineRunId) {
      disconnectSSE();
      return;
    }
    connectSSE(spineRunId);
    return () => { disconnectSSE(); };
  }, [spineRunId, connectSSE, disconnectSSE]);


  const runFrontier = spineRunState?.frontier_result;
  const showFrontier = Boolean(trip?.frontier_result) || Boolean(store.result_frontier) || Boolean(runFrontier);
  const blockCopy = getWorkbenchBlockCopy({ validation: store.result_validation, packet: store.result_packet ?? trip?.packet ?? null });
  const missingFieldsLabel = formatWorkbenchMissingFields(blockCopy.missingFields);
  // D-09: deep-link the first repairable missing field straight into its
  // intake editor (?repair=<field>), falling back to the plain intake route.
  const firstRepairableField = getFirstRepairableFieldName(blockCopy.missingFields);
  const tripRepairHref = trip?.id
    ? (firstRepairableField ? buildRepairDeepLinkHref(trip.id, firstRepairableField) : getTripRepairRoute(trip.id))
    : null;

  const visibleTabs = workspaceTabs.filter((tab) => {
    if (tab.id === 'packet') return showPacket;
    if (tab.id === 'frontier') return showFrontier;
    return true;
  });

  // Normalize: if URL requests a tab that isn't currently visible, fall back to intake
  const effectiveTab = visibleTabs.some((t) => t.id === activeTab)
    ? activeTab
    : 'intake';

  // Compatibility redirect: old Workbench Ops deep links → Trip Workspace Ops.
  // Uses replace() so the obsolete ?tab=ops URL is not kept in browser history.
  useEffect(() => {
    const tabParam = getSearchParam('tab');
    if (tabParam !== 'ops') return;
    if (tripId) {
      replace(getTripRoute(tripId, 'ops'));
    } else {
      // No trip context — ops requires a specific trip. Route back to intake surface.
      const params = new URLSearchParams(searchParams.toString());
      params.set('tab', 'intake');
      replace(`${pathname}?${params.toString()}`);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // run once on mount — handles stale bookmarks / SOP links

  // Fast-capture entry stays on Workbench until a real trip exists.
  useEffect(() => {
    const entry = getSearchParam('entry');
    const captureMode = getSearchParam('capture_mode');
    if (tripId || entry !== 'new' || captureMode !== 'call') return;
    if (draftParam && draftParam !== 'new') return;
    const params = new URLSearchParams(searchParams.toString());
    params.set('draft', 'new');
    params.set('tab', 'intake');
    const nextUrl = `${pathname}?${params.toString()}`;
    const currentUrl = `${pathname}?${searchParams.toString()}`;
    if (nextUrl !== currentUrl) {
      replace(nextUrl);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Draft hydration - load draft from backend and populate store
  const prevDraftRef = useRef<string | null>(null);
  const draftLoadingRef = useRef(false);
  const [draftError, setDraftError] = useState<string | null>(null);
  const {
    clearDraft,
    hydrateFromDraft,
    setDraftStatus,
    clearTransientRunResults,
    setResultValidation,
    setResultPacket,
    setResultDecision,
    setResultFrontier,
    setSaveState,
    setDraftMeta,
  } = store;
  useEffect(() => {
    if (!draftParam) return;
    if (draftParam === 'new') {
      if (prevDraftRef.current !== 'new') {
        clearDraft();
        setCompletedTripId(null);
        prevDraftRef.current = 'new';
      }
      return;
    }
    if (draftParam === prevDraftRef.current) return;
    prevDraftRef.current = draftParam;

    draftLoadingRef.current = true;
    setDraftError(null);
    getDraft(draftParam)
      .then((draft) => {
        hydrateFromDraft(draft);
        setCompletedTripId(extractCompletedTripIdFromDraft(draft));
        draftLoadingRef.current = false;
      })
      .catch((err) => {
        setDraftError(err instanceof Error ? err.message : 'Failed to load draft');
        setCompletedTripId(null);
        draftLoadingRef.current = false;
      });
  }, [draftParam, clearDraft, hydrateFromDraft]);

  useEffect(() => {
    if (!completedTripId || tripId) return;
    const params = new URLSearchParams(searchParams.toString());
    params.set('trip', completedTripId);
    if (!params.get('tab') || params.get('tab') === 'intake') {
      params.set('tab', 'packet');
    }
    const nextUrl = `${pathname}?${params.toString()}`;
    const currentUrl = `${pathname}?${searchParams.toString()}`;
    if (nextUrl !== currentUrl) {
      replace(nextUrl, { scroll: false });
    }
  }, [completedTripId, tripId, pathname, replace, searchParams]);

  // Invalidation logic: clear results if config changes
  const prevConfigRef = useRef({
    stage: spineStage,
    mode: currentMode,
    scenario: currentScenario,
  });
  useEffect(() => {
    if (
      prevConfigRef.current.stage !== spineStage ||
      prevConfigRef.current.mode !== currentMode ||
      prevConfigRef.current.scenario !== currentScenario
    ) {
      // Clear only transient run artifacts (run_ts, acknowledged flags, parked frontier).
      // Trip-persisted outputs (packet, decision, strategy, safety) remain visible
      // because they belong to the trip, not to a specific run config.
      clearTransientRunResults();
      prevConfigRef.current = {
        stage: spineStage,
        mode: currentMode,
        scenario: currentScenario,
      };
    }
  }, [spineStage, currentMode, currentScenario, clearTransientRunResults]);

  const handleTabChange = useCallback(
    (tab: string) => {
      if (!visibleTabs.some((t) => t.id === tab)) return;
      const params = new URLSearchParams(searchParams.toString());
      params.set('tab', tab);
      replace(`${pathname}?${params.toString()}`, { scroll: false });
    },
    [pathname, searchParams, replace, visibleTabs],
  );

  // Auto-switch away from packet tab if trip/results disappear
  const prevStageRef = useRef<string | null>(null);
  useEffect(() => {
    const currentStage = trip?.stage ?? null;
    prevStageRef.current = currentStage;
  }, [trip?.stage, activeTab, handleTabChange]);

  const [isRunning, setIsRunning] = useState(false);
  const [runError, setRunError] = useState<string | null>(null);
  const [runSuccess, setRunSuccess] = useState(false);
  const inFlightRef = useRef(false);
  const activePanel = getSearchParam('panel');
  const settingsOpen = activePanel === 'settings';
  const setPanelOpen = useCallback(
    (panel: 'settings', open: boolean) => {
      const params = new URLSearchParams(searchParams.toString());
      if (open) {
        params.set('panel', panel);
      } else if (params.get('panel') === panel) {
        params.delete('panel');
      }

      const query = params.toString();
      replace(query ? `${pathname}?${query}` : pathname, { scroll: false });
    },
    [pathname, replace, searchParams]
  );

  // Run-state -> store merge, draft lifecycle status, and terminal-tab
  // auto-switch. Effects live in one hook, in their original declaration
  // order, called at the same position the first effect previously occupied.
  useWorkbenchRunSync({ spineRunState, activeTab, handleTabChange });

  const { mutate: saveTrip, isSaving } = useUpdateTrip();
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [isResetDialogOpen, setIsResetDialogOpen] = useState(false);

  // Ensure a draft exists before processing - creates one if needed.
  // Returns the draft_id to use, or null if there's no meaningful content.
  // Draft create/patch/save lifecycle (manual save, ensure-saved-before-run,
  // 5s debounced auto-save). Extracted verbatim into
  // useWorkbenchDraftPersistence; called at the position the callbacks
  // previously occupied so effect ordering is unchanged.
  const { ensureDraftSaved, handleSaveDraft } = useWorkbenchDraftPersistence({
    store,
    searchParams,
    replace,
    isSpineRunning,
    spineStage,
    currentMode,
    currentScenario,
    setSaveSuccess,
    setSaveError,
  });

  const handleProcessTrip = useCallback(async () => {
    if (!store.input_raw_note && !store.input_owner_note) return;
    if (inFlightRef.current) return;
    inFlightRef.current = true;
    setIsRunning(true);
    setRunError(null);
    setRunSuccess(false);

    try {
      // Ensure draft exists before running
      const resolvedDraftId = await ensureDraftSaved();
      const structured_json = safeParseJson(store.input_structured_json);

      const request: SpineRunRequest = {
        raw_note: store.input_raw_note || null,
        owner_note: store.input_owner_note || null,
        structured_json,
        itinerary_text: store.input_itinerary_text || null,
        stage: spineStage,
        operating_mode: currentMode,
        strict_leakage: store.strict_leakage,
        scenario_id: currentScenario || null,
        draft_id: resolvedDraftId || undefined,
        // Preserves raw input for agency audit trail. Agency consent to us
        // is via ToS/Privacy Policy at signup, not per-submission.
        // Public checker handles consent via its own checkbox.
        retention_consent: true,
      };

      const result = await executeSpineRun(request);

      if (result?.trip_id) {
        setCompletedTripId(result.trip_id);
        setRunSuccess(true);
        return;
      }

      setRunSuccess(true);
      setTimeout(() => setRunSuccess(false), 3000);
    } catch (err) {
      setRunError(
        err instanceof Error
          ? err.message
          : 'Processing failed. Please try again or contact support if the issue persists.',
      );
      setTimeout(() => setRunError(null), 8000);
    } finally {
      inFlightRef.current = false;
      setIsRunning(false);
    }
  }, [store, executeSpineRun, spineStage, currentMode, currentScenario, ensureDraftSaved, setIsRunning, setRunError, setRunSuccess, setCompletedTripId]);

  const handleSave = useCallback(async () => {
    if (!resolvedTripId) return;
    setSaveError(null);
    const result = await saveTrip(resolvedTripId, {
      customerMessage: store.input_raw_note,
      agentNotes: store.input_owner_note,
    });
    if (result) {
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } else {
      setSaveError('Failed to save. Check connection and try again.');
      setTimeout(() => setSaveError(null), 8000);
    }
  }, [resolvedTripId, saveTrip, store.input_raw_note, store.input_owner_note]);

  const handleReset = useCallback(() => {
    store.resetAll();
    resetSpine();
    setCompletedTripId(null);
  }, [store, resetSpine, setCompletedTripId]);

  const handleResolve = useCallback(async () => {
    if (!tripId) return;
    try {
      await submitTripReviewAction(
        tripId,
        'resolve',
        'Recovery completed. Feedback addressed.',
      );
      // Refresh trip data to clear recovery state
      refresh();
    } catch (err) {
      console.error('Failed to resolve recovery:', err);
    }
  }, [tripId, refresh]);

  const isRecoveryMode =
    trip?.analytics?.feedback_reopen === true ||
    trip?.analytics?.recovery_status === 'IN_RECOVERY';

  const pipelineStage = getPipelineStageForWorkbench(trip, store);

  return (
    <div className='bg-[#080a0c]'>
      {isRecoveryMode && (
        <div className='bg-[#2b1011] border-b border-[#6b2a2b] px-6 py-2 flex items-center justify-between'>
          <div className='flex items-center gap-3 text-[#ff7b72]'>
            <AlertTriangle className='size-4' />
            <span className='text-ui-xs font-bold uppercase tracking-wider'>
              Recovery Mode: Critical Feedback Detected
            </span>
          </div>
          <button
            onClick={handleResolve}
            className='flex items-center gap-1.5 px-3 py-1 bg-[#ff7b72]/10 hover:bg-[#ff7b72]/20 border border-[#ff7b72]/30 rounded-md text-[#ff7b72] text-ui-xs font-semibold transition-all'
          >
            <CheckCircle className='size-3.5' />
            Mark Resolved
          </button>
        </div>
      )}

      <div className="mx-6 mt-2">
        <p className="text-[12px] text-[var(--text-muted)] leading-relaxed">
          After processing: incomplete leads appear in Lead Inbox · planning continues in Trips in Planning · quotes needing approval appear in Quote Review
        </p>
      </div>

      {/* Persistent blocked-state banner */}
      {store.result_validation && (
        store.result_validation.is_valid === false ||
        store.result_validation.status === "ESCALATED" ||
        store.result_validation.status === "BLOCKED"
      ) && !spineRunId && (
        <div className="mx-6 mt-4 rounded-xl border border-[#f85149]/40 bg-[#2b1011] px-5 py-3">
          <div className="flex items-start gap-3">
            <AlertTriangle className="size-5 text-[#f85149] shrink-0 mt-0.5" />
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <>
                    <h3 className="text-ui-sm font-semibold text-[#f85149]">
                      {blockCopy.title}
                    </h3>
                    <p className="text-ui-xs text-[#ffa198] mt-0.5">
                      {blockCopy.summary}
                      {blockCopy.details.length > 1 ? (
                        <span className='block mt-1 space-y-0.5'>
                          {blockCopy.details.slice(1).map((reason) => (
                            <span key={reason} className='block'>
                              • {reason}
                            </span>
                          ))}
                        </span>
                      ) : null}
                      {missingFieldsLabel ? (
                        <span className='block mt-1 font-medium text-[#e6edf3]'>
                          Missing: {missingFieldsLabel}
                        </span>
                      ) : null}
                      <span className='block mt-1'>
                        Open the Trip Details repair surface to fix the missing fields, then process the trip again.
                      </span>
                    </p>
                  </>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  {/*
                    IMP-05 (DEMO-06): when a persisted trip exists for this workbench
                    context, route the operator to the editable repair surface
                    (/trips/{tripId}/intake, IntakePanel) instead of re-setting the
                    identical ?tab=packet URL — a visual no-op when the blocked run
                    auto-switches to the packet tab. With no trip yet (fresh draft,
                    pre-persistence), fall back to the packet tab, which now carries
                    the validation context and self-resolves once the run persists.
                  */}
                  {tripRepairHref ? (
                    <Link
                      href={tripRepairHref}
                      className={REVIEW_MISSING_FIELDS_CONTROL_CLASSES}
                    >
                      Review Missing Fields
                    </Link>
                  ) : (
                    <button
                      onClick={() => handleTabChange('packet')}
                      className={REVIEW_MISSING_FIELDS_CONTROL_CLASSES}
                    >
                      Review Missing Fields
                    </button>
                  )}
                  {tripRepairHref && (
                    <Link
                      href={tripRepairHref}
                      className="px-3 py-1.5 bg-[#161b22] border border-[#30363d] text-[#e6edf3] text-ui-xs font-medium rounded-md hover:bg-[#21262d] transition-colors"
                    >
                      {blockCopy.actionLabel}
                    </Link>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className='p-4 sm:p-6'>
        <header className='mb-6 flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between'>
          <div className='min-w-0 flex-1'>
            <h1 className='text-ui-2xl font-semibold text-[#e6edf3] mb-1'>
              {trip ? trip.destination : (store.draft_name || 'New Inquiry')}
            </h1>
            <p className='flex flex-wrap items-center gap-x-3 gap-y-1 text-ui-base text-[#a8b3c1]'>
              {trip
                ? `${trip.id} · ${trip.type} · ${trip.age}`
                : 'Capture a customer request and send it into the workflow.'}
              {store.draft_id && !trip && (
                <>
                  <span className='text-[#30363d]'>·</span>
                  <span className='font-mono text-ui-xs text-[#8b949e]'>{store.draft_id}</span>
                </>
              )}
            </p>
            <div className='mt-1.5 flex flex-wrap items-center gap-x-2 gap-y-1'>
              {store.draft_id && (
                <span
                  className='inline-flex items-center px-2 py-0.5 rounded text-ui-xs font-medium'
                  style={{
                    background: store.draft_status === 'processing' ? 'var(--accent-amber)' : 'var(--bg-elevated)',
                    color: store.draft_status === 'processing' ? '#000' : 'var(--text-muted)',
                    border: '1px solid var(--border-default)',
                  }}
                >
                  {store.draft_status === 'processing' ? 'Processing' :
                   store.draft_status === 'blocked' ? 'Blocked' :
                   store.draft_status === 'failed' ? 'Failed' :
                   store.draft_status === 'promoted' ? 'Promoted' :
                   'Draft'}
                </span>
              )}
              {store.save_state === 'dirty' && (
                <span className='text-ui-xs text-[#d29922] font-medium'>Unsaved changes</span>
              )}
              {store.save_state === 'saving' && (
                <span className='text-ui-xs text-[#8b949e]'>Saving…</span>
              )}
              {store.save_state === 'saved' && store.draft_last_saved_at && (
                <span className='text-ui-xs text-[#3fb950]'>
                  Saved at <ClientTime value={store.draft_last_saved_at} options={{ hour: '2-digit', minute: '2-digit' }} />
                </span>
              )}
              {store.save_state === 'conflict' && (
                <span className='text-ui-xs text-[#f85149] font-medium'>Save conflict - refresh to reload</span>
              )}
              {store.save_state === 'error' && (
                <span className='text-ui-xs text-[#f85149] font-medium'>Save failed</span>
              )}
            </div>
            {tripLoading && (
              <p className='text-ui-sm text-[#8b949e] mt-1'>Loading trip…</p>
            )}
            {tripError && (
              <p className='text-ui-sm text-[#f85149] mt-1'>
                Failed to load trip: {tripError.message}
              </p>
            )}
            {draftError && (
              <p className='text-ui-sm text-[#f85149] mt-1'>
                Failed to load draft: {draftError}
              </p>
            )}
            {trip?.updatedAt && (
              <p className='text-ui-xs text-[#8b949e] mt-1'>
                Last processed: <ClientDateTime value={trip.updatedAt} />
              </p>
            )}
          </div>
          <form
            className='flex w-full flex-col items-stretch gap-3 sm:flex-row sm:flex-wrap sm:items-center xl:w-auto xl:justify-end'
            onSubmit={(e) => {
              e.preventDefault();
              void handleProcessTrip();
            }}
          >
            {runError && (
              <div className='flex w-full items-center gap-2 rounded-lg border border-[#f85149]/30 bg-[#f85149]/10 px-3 py-2 text-ui-sm text-[#f85149] sm:max-w-[32rem] xl:w-auto'>
                <AlertTriangle className='size-4' />
                {spineRunState?.validation && (
                  spineRunState.validation.is_valid === false ||
                  spineRunState.validation.status === "ESCALATED" ||
                  spineRunState.validation.status === "BLOCKED"
                ) ? (
                  <div className='flex flex-col'>
                    {(() => {
                      const blockCopy = getWorkbenchBlockCopy({ validation: spineRunState.validation });
                      return (
                        <>
                          <span className='font-medium'>{blockCopy.title}</span>
                          <span className='text-ui-xs text-[#ffa198]'>
                            {blockCopy.summary}
                            {blockCopy.details.length > 1 ? ` ${formatWorkbenchBlockReasonList(blockCopy.details.slice(1))}.` : ''}
                            {" "}Check the Trip Details tab.
                          </span>
                        </>
                      );
                    })()}
                  </div>
                ) : (
                  <span className='max-w-xs truncate'>{runError}</span>
                )}
              </div>
            )}
            {runSuccess && (
              <div className='flex w-full items-center gap-2 rounded-lg border border-[#3fb950]/30 bg-[#3fb950]/10 px-3 py-2 text-ui-sm text-[#3fb950] sm:w-auto'>
                <CheckCircle className='size-4' />
                Processed successfully
              </div>
            )}
            {saveSuccess && (
              <div className='flex w-full items-center gap-2 rounded-lg border border-[#3fb950]/30 bg-[#3fb950]/10 px-3 py-2 text-ui-sm text-[#3fb950] sm:w-auto'>
                <CheckCircle className='size-4' />
                Saved
              </div>
            )}
            {saveError && (
              <div className='flex w-full items-center gap-2 rounded-lg border border-[#f85149]/30 bg-[#f85149]/10 px-3 py-2 text-ui-sm text-[#f85149] sm:max-w-[24rem] xl:w-auto'>
                <AlertTriangle className='size-4' />
                <span className='max-w-xs truncate'>{saveError}</span>
              </div>
            )}
            <button
              type='submit'
              disabled={
                isRunning ||
                isSpineRunning ||
                (!store.input_raw_note && !store.input_owner_note)
              }
              className='flex w-full items-center justify-center gap-2 rounded-lg bg-[#58a6ff] px-4 py-2 font-medium text-[#0d1117] transition-colors hover:bg-[#6eb5ff] disabled:cursor-not-allowed disabled:opacity-50 sm:w-auto sm:justify-start'
              aria-label={isRunning ? 'Processing inquiry' : 'Process inquiry'}
            >
              {isRunning ? (
                <>
                  <div
                    className='size-4 border-2 border-[#0d1117]/30 border-t-[#0d1117] rounded-full animate-spin'
                    aria-hidden='true'
                  />
                  Processing…
                </>
              ) : (
                <>
                  <Play className='size-4' aria-hidden='true' />
                  Process Inquiry
                </>
              )}
            </button>
            {completedTripId && (
              <>
                {store.draft_id && (
                  <button
                    type='button'
                    onClick={async () => {
                      try {
                        await promoteDraft(store.draft_id!, completedTripId);
                        store.setDraftStatus('promoted');
                      } catch (err) {
                        setRunError(
                          err instanceof Error ? err.message : 'Promotion failed'
                        );
                        setTimeout(() => setRunError(null), 8000);
                        return;
                      }
                      push(getPostRunTripRoute({
                        tripId: completedTripId,
                        tripStage: spineRunState?.stage ?? trip?.stage,
                        validationStatus: spineRunState?.validation?.status,
                      }));
                    }}
                    className='flex w-full items-center justify-center gap-2 rounded-lg bg-[#58a6ff] px-4 py-2 font-medium text-[#0d1117] transition-colors hover:bg-[#6eb5ff] sm:w-auto sm:justify-start'
                  >
                    <CheckCircle className='size-4' />
                    Promote Draft
                  </button>
                )}
              </>
            )}
            {spineRunId && spineRunState && (
              <RunProgressPanel
                runId={spineRunId}
                runState={spineRunState}
                error={spineError}
                onRetry={() => {
                  setRunError(null);
                  resetSpine();
                  setCompletedTripId(null);
                }}
                onViewFrontier={showFrontier ? () => handleTabChange('frontier') : undefined}
                onFixDetails={() => {
                  resetSpine();
                  handleTabChange(showPacket ? 'packet' : 'intake');
                }}
                onViewTrip={completedTripId ? () => push(getPostRunTripRoute({
                  tripId: completedTripId,
                  tripStage: spineRunState?.stage ?? trip?.stage,
                  validationStatus: spineRunState?.validation?.status,
                })) : undefined}
              />
            )}
            <button
              type='button'
              onClick={handleSaveDraft}
              disabled={store.save_state === 'saving' || store.draft_status === 'promoted'}
              className='flex w-full items-center justify-center gap-2 rounded-lg border border-[#30363d] bg-[#161b22] px-3 py-2 font-medium text-[#e6edf3] transition-colors hover:bg-[#21262d] disabled:cursor-not-allowed disabled:opacity-50 sm:w-auto sm:justify-start'
              aria-label='Save draft'
            >
              {store.save_state === 'saving' ? (
                <>
                  <div
                    className='size-4 border-2 border-[#8b949e]/30 border-t-[#8b949e] rounded-full animate-spin'
                    aria-hidden='true'
                  />
                  Saving…
                </>
              ) : (
                <>
                  <Save className='size-4' aria-hidden='true' />
                  Save Draft
                </>
              )}
            </button>
            {resolvedTripId && (
              <button
                type='button'
                onClick={handleSave}
                disabled={isSaving}
              className='flex w-full items-center justify-center gap-2 rounded-lg border border-[#30363d] bg-[#161b22] px-3 py-2 font-medium text-[#e6edf3] transition-colors hover:bg-[#21262d] disabled:cursor-not-allowed disabled:opacity-50 sm:w-auto sm:justify-start'
              aria-label='Save trip changes'
            >
                {isSaving ? (
                  <>
                    <div
                      className='size-4 border-2 border-[#8b949e]/30 border-t-[#8b949e] rounded-full animate-spin'
                      aria-hidden='true'
                    />
                    Saving…
                  </>
                ) : (
                  <>
                    <Save className='size-4' aria-hidden='true' />
                    <span className='sm:hidden'>Save Trip</span>
                    <span className='hidden sm:inline'>Save Trip Changes</span>
                  </>
                )}
              </button>
            )}
            <button
              type='button'
              onClick={() => setIsResetDialogOpen(true)}
              className='flex w-full items-center justify-center gap-2 rounded-lg border border-[#30363d] bg-[#161b22] px-3 py-2 font-medium text-[#e6edf3] transition-colors hover:bg-[#21262d] sm:w-auto sm:justify-start'
              aria-label='Reset pipeline'
            >
              <RotateCcw className='size-4' aria-hidden='true' />
              Reset
            </button>
            <button
              type='button'
              onClick={() => setPanelOpen('settings', true)}
              className='flex w-full items-center justify-center gap-2 rounded-lg border border-[#30363d] bg-[#161b22] px-3 py-2 font-medium text-[#e6edf3] transition-colors hover:bg-[#21262d] sm:w-auto sm:justify-start'
              aria-label='Open settings'
            >
              <Settings className='size-4' aria-hidden='true' />
            </button>
          </form>
        </header>

        {process.env.NEXT_PUBLIC_ENABLE_SCENARIO_LAB === '1' && (
        <details className='mb-4'>
          <summary className='cursor-pointer list-none text-ui-xs font-medium text-text-muted hover:text-text-primary transition-colors px-6'>
            Dev: Scenario Lab
          </summary>
          <div className='mt-2'>
            <Suspense fallback={<div className="text-ui-xs text-text-muted">Loading scenario lab…</div>}>
              <ScenarioLab />
            </Suspense>
          </div>
        </details>
        )}

        <div className='bg-[#0f1115] border border-[#30363d] rounded-t-xl overflow-hidden'>
          <Tabs
            tabs={visibleTabs}
            activeTab={effectiveTab}
            onTabChange={handleTabChange}
            getTabHref={(tab) => {
              const params = new URLSearchParams(searchParams.toString());
              params.set('tab', tab);
              return `${pathname}?${params.toString()}`;
            }}
            ariaLabel='Trip workspace sections'
          />
        </div>

        <div
          className='bg-[#0f1115] border-x border-b border-[#30363d] rounded-b-xl'
          role='tabpanel'
          id={`tabpanel-${effectiveTab}`}
          aria-labelledby={`tab-${effectiveTab}`}
          tabIndex={0}
        >
          <div className='p-6'>
            <Suspense fallback={<InlineLoading message='Loading…' />}>
              {effectiveTab === 'safety' ? (
                <SafetyTab trip={trip} />
              ) : effectiveTab === 'council' ? (
                <PersonaCouncilPanel tripId={resolvedTripId} />
              ) : effectiveTab === 'frontier' ? (
                <FrontierDashboard />
              ) : effectiveTab === 'packet' ? (
                <PacketTab trip={trip} />
              ) : (
                <IntakeTab trip={trip} />
              )}
            </Suspense>
          </div>
        </div>
      </div>

      <Suspense fallback={null}>
        <SettingsPanel
          open={settingsOpen}
          onClose={() => setPanelOpen('settings', false)}
        />
      </Suspense>

      <ConfirmDialog
        isOpen={isResetDialogOpen}
        onClose={() => setIsResetDialogOpen(false)}
        onConfirm={handleReset}
        title="Reset Pipeline"
        message="This will clear the current workbench state and all processing results. Draft data will not be affected."
        confirmLabel="Reset"
        variant="danger"
      />
    </div>
  );
}

export default function WorkbenchPage() {
  return (
    <ErrorBoundary>
      <Suspense fallback={<WorkbenchLoading />}>
        <WorkbenchPageGate />
      </Suspense>
    </ErrorBoundary>
  );
}

function WorkbenchPageGate() {
  const searchParams = useSearchParams();
  const pathname = usePathname();
  const authIsLoading = useAuthStore((state) => state.isLoading);
  const authIsAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const searchQuery = searchParams.toString();
  const redirectTarget = `${pathname}${searchQuery ? `?${searchQuery}` : ''}`;

  if (!authIsLoading && !authIsAuthenticated) {
    return (
      <ProtectedSurfaceNotice
        surfaceName='Workbench'
        redirectTarget={redirectTarget}
        description='This browser session is not signed in yet. Sign in to capture a new inquiry, process a trip, and continue the agency workflow.'
      />
    );
  }

  return <WorkbenchContent />;
}

function WorkbenchLoading() {
  return (
    <div className='min-h-screen bg-[#080a0c] p-6'>
      <div className='h-8 bg-[#161b22] rounded animate-pulse mb-6 w-48' />
      <div className='h-12 bg-[#0f1115] rounded animate-pulse mb-4' />
      <div className='h-64 bg-[#0f1115] rounded animate-pulse' />
    </div>
  );
}
