'use client';

import { useSearchParams, useRouter, usePathname } from 'next/navigation';
import dynamic from 'next/dynamic';
import { Suspense, useState, useCallback, useEffect, useRef } from 'react';
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
import { useUpdateTrip } from '@/hooks/useTrips';
import type {
  SpineRunRequest,
  SpineStage,
  OperatingMode,
  DecisionOutput,
  StrategyOutput,
  PromptBundle,
} from '@/types/spine';
import type {
  SafetyResult,
  ValidationReport,
  FeeCalculationResult,
} from '@/types/spine';
import type { Trip } from '@/lib/api-client';
import { submitTripReviewAction, createDraft, getDraft, patchDraft, discardDraft, promoteDraft } from '@/lib/api-client';
import type { WorkbenchStore, DraftStatus, SaveState } from '@/stores/workbench';
import { ErrorBoundary } from '@/components/error-boundary';
import { BackToOverviewLink } from '@/components/navigation/BackToOverviewLink';
import { RunProgressPanel } from './RunProgressPanel';

const IntakeTab = dynamic(() => import('./IntakeTab'));
const PacketTab = dynamic(() => import('./PacketTab'));
const DecisionTab = dynamic(() => import('./DecisionTab'));
const StrategyTab = dynamic(() => import('./StrategyTab'));
const SafetyTab = dynamic(() => import('./SafetyTab'));
const SettingsPanel = dynamic(() => import('./SettingsPanel'));
const IntegrityMonitorPanel = dynamic(() => import('./IntegrityMonitorPanel'));
const ScenarioLab = dynamic(() => import('./ScenarioLab'));
const OutputPanel = dynamic(
  () => import('@/components/workspace/panels/OutputPanel'),
);
const FeedbackPanel = dynamic(
  () => import('@/components/workspace/panels/FeedbackPanel'),
);

// Safely parse structured JSON — returns null on invalid rather than throwing.
function safeParseJson(raw: string): Record<string, unknown> | null {
  if (!raw.trim()) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

const workspaceTabs = [
  { id: 'intake', label: 'New Inquiry' },
] as const;

type WorkspaceTabId = (typeof workspaceTabs)[number]['id'];

const VALID_SPINE_STAGES = [
  'discovery',
  'shortlist',
  'proposal',
  'booking',
] as const satisfies readonly SpineStage[];

function toSpineStage(value: string | null): SpineStage | null {
  return VALID_SPINE_STAGES.find((stage) => stage === value) ?? null;
}

const VALID_OPERATING_MODES = [
  'normal_intake',
  'audit',
  'emergency',
  'follow_up',
  'cancellation',
  'post_trip',
  'coordinator_group',
  'owner_review',
] as const satisfies readonly OperatingMode[];

function toOperatingMode(value: string | null): OperatingMode | null {
  return VALID_OPERATING_MODES.find((mode) => mode === value) ?? null;
}

function toWorkspaceTabId(value: string | null): WorkspaceTabId | null {
  return workspaceTabs.find((tab) => tab.id === value)?.id ?? null;
}

/**
 * Derives the pipeline stage from actual trip/store state.
 * PipelineFlow shows processing progress (intake → packet → decision → strategy → safety),
 * not which tab the user clicked.
 * Output and Feedback are workspace sections, not core pipeline stages.
 * Frontier OS has been removed from the workbench UI (parked for future intelligence integration).
 */
function getPipelineStageForWorkbench(
  trip: Trip | null | undefined,
  store: WorkbenchStore,
): PipelineStageId {
  if (store.result_safety || trip?.safety) return 'safety';
  if (store.result_strategy || trip?.strategy) return 'strategy';
  if (store.result_decision || trip?.decision) return 'decision';
  if (store.result_packet || trip?.packet) return 'packet';
  return 'intake';
}

function useHydrateStoreFromTrip(trip: Trip | null | undefined) {
  const store = useWorkbenchStore();
  const hydratedRef = useRef<string | null>(null);

  useEffect(() => {
    if (!trip?.id) return;
    if (hydratedRef.current === trip.id) return;

    hydratedRef.current = trip.id;

    // Always overwrite from current trip (prevent stale cross-trip data)
    store.setResultPacket(trip.packet ?? null);
    store.setResultValidation(trip.validation ?? null);
    store.setResultDecision(trip.decision ?? null);
    store.setResultStrategy(trip.strategy ?? null);
    store.setResultInternalBundle(trip.internal_bundle ?? null);
    store.setResultTravelerBundle(trip.traveler_bundle ?? null);
    store.setResultSafety((trip.safety as SafetyResult) ?? null);
    store.setResultFees(trip.fees ?? null);
    store.setInputRawNote(trip.customerMessage ?? '');
    store.setInputOwnerNote(trip.agentNotes ?? '');
  }, [
    trip,
    store.setInputRawNote,
    store.setInputOwnerNote,
    store.setResultPacket,
    store.setResultValidation,
    store.setResultDecision,
    store.setResultStrategy,
    store.setResultInternalBundle,
    store.setResultTravelerBundle,
    store.setResultSafety,
    store.setResultFees,
  ]);
}

function WorkbenchContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const tripId = searchParams.get('trip');
  const draftParam = searchParams.get('draft');
  const stageParam = searchParams.get('stage');
  const scenarioParam = searchParams.get('scenario');

  // The ?stage= URL param drives Spine execution (not the pipeline UI)
  const spineStage = toSpineStage(stageParam) ?? 'discovery';
  const currentMode = toOperatingMode(searchParams.get('mode')) ?? 'normal_intake';
  const currentScenario = scenarioParam || '';

  const {
    data: trip,
    isLoading: tripLoading,
    error: tripError,
  } = useTrip(tripId);
  useHydrateStoreFromTrip(trip);

  const activeTab = toWorkspaceTabId(searchParams.get('tab')) ?? 'intake';

  const store = useWorkbenchStore();

  // Draft hydration — load draft from backend and populate store
  const prevDraftRef = useRef<string | null>(null);
  const [draftLoading, setDraftLoading] = useState(false);
  const [draftError, setDraftError] = useState<string | null>(null);
  const { clearDraft, hydrateFromDraft, setDraftStatus } = store;
  useEffect(() => {
    if (!draftParam) return;
    if (draftParam === 'new') {
      if (prevDraftRef.current !== 'new') {
        clearDraft();
        prevDraftRef.current = 'new';
      }
      return;
    }
    if (draftParam === prevDraftRef.current) return;
    prevDraftRef.current = draftParam;

    setDraftLoading(true);
    setDraftError(null);
    getDraft(draftParam)
      .then((draft) => {
        hydrateFromDraft(draft);
        setDraftLoading(false);
      })
      .catch((err) => {
        setDraftError(err instanceof Error ? err.message : 'Failed to load draft');
        setDraftLoading(false);
      });
  }, [draftParam, clearDraft, hydrateFromDraft]);

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
      store.clearTransientRunResults();
      prevConfigRef.current = {
        stage: spineStage,
        mode: currentMode,
        scenario: currentScenario,
      };
    }
  }, [spineStage, currentMode, currentScenario, store.clearTransientRunResults]);

  const handleTabChange = useCallback(
    (tab: string) => {
      if (!workspaceTabs.some((t) => t.id === tab)) return;
      const params = new URLSearchParams(searchParams.toString());
      params.set('tab', tab);
      router.replace(`?${params.toString()}`, { scroll: false });
    },
    [searchParams, router],
  );

  const [isRunning, setIsRunning] = useState(false);
  const [runError, setRunError] = useState<string | null>(null);
  const [runSuccess, setRunSuccess] = useState(false);
  const inFlightRef = useRef(false);
  const [completedTripId, setCompletedTripId] = useState<string | null>(null);
  const activePanel = searchParams.get('panel');
  const settingsOpen = activePanel === 'settings';
  const integrityOpen = activePanel === 'integrity';
  const setPanelOpen = useCallback(
    (panel: 'settings' | 'integrity', open: boolean) => {
      const params = new URLSearchParams(searchParams.toString());
      if (open) {
        params.set('panel', panel);
      } else if (params.get('panel') === panel) {
        params.delete('panel');
      }

      const query = params.toString();
      router.replace(query ? `${pathname}?${query}` : pathname, { scroll: false });
    },
    [pathname, router, searchParams]
  );
  const {
    execute: executeSpineRun,
    isLoading: isSpineRunning,
    error: spineError,
    reset: resetSpine,
    runId: spineRunId,
    state: spineRunState,
  } = useSpineRun();

  // Populate store with validation/packet from run status so blocked runs
  // still show specific field-level errors in the UI.
  useEffect(() => {
    if (spineRunState?.validation) {
      store.setResultValidation(spineRunState.validation);
    }
    if (spineRunState?.packet) {
      store.setResultPacket(spineRunState.packet);
    }
  }, [spineRunState, store.setResultValidation, store.setResultPacket]);

  // Update draft status based on run state, and refetch after terminal states
  // to pick up backend lifecycle changes (version bumps, status updates).
  useEffect(() => {
    if (!store.draft_id || !spineRunState?.state) return;
    const runState = spineRunState.state;
    if (runState === 'running' || runState === 'queued') {
      setDraftStatus('processing');
    } else if (runState === 'blocked') {
      setDraftStatus('blocked');
      // Refetch draft to get updated version from backend lifecycle
      getDraft(store.draft_id).then((draft) => hydrateFromDraft(draft)).catch(() => {});
    } else if (runState === 'failed') {
      setDraftStatus('failed');
      getDraft(store.draft_id).then((draft) => hydrateFromDraft(draft)).catch(() => {});
    } else if (runState === 'completed') {
      setDraftStatus('open');
      getDraft(store.draft_id).then((draft) => hydrateFromDraft(draft)).catch(() => {});
    }
  }, [spineRunState?.state, store.draft_id, setDraftStatus, hydrateFromDraft]);

  // Auto-switch to the tab containing errors when a run ends in blocked/failed state.
  // This prevents the user from missing field-level validation errors that are rendered
  // in the Trip Details (packet) tab or other stage-specific tabs.
  const prevRunStateRef = useRef<string | null>(null);
  useEffect(() => {
    const currentState = spineRunState?.state ?? null;
    const prevState = prevRunStateRef.current;

    // Only act when transitioning into a terminal error state
    if (
      currentState !== prevState &&
      (currentState === 'blocked' || currentState === 'failed')
    ) {
      handleTabChange('intake');
    }

    prevRunStateRef.current = currentState;
  }, [spineRunState, handleTabChange]);

  const { mutate: saveTrip, isSaving } = useUpdateTrip();
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  // Ensure a draft exists before processing — creates one if needed.
  // Returns the draft_id to use, or null if there's no meaningful content.
  const ensureDraftSaved = useCallback(async (): Promise<string | null> => {
    const hasContent =
      store.input_raw_note.trim() ||
      store.input_owner_note.trim() ||
      store.input_itinerary_text.trim() ||
      (store.input_structured_json.trim() ? safeParseJson(store.input_structured_json) !== null : false);

    if (!hasContent) return null;

    if (store.draft_id) {
      // Patch existing draft
      const structured_json = safeParseJson(store.input_structured_json);
      await patchDraft(store.draft_id, {
        customer_message: store.input_raw_note || null,
        agent_notes: store.input_owner_note || null,
        structured_json,
        itinerary_text: store.input_itinerary_text || null,
        stage: spineStage,
        operating_mode: currentMode,
        scenario_id: currentScenario || null,
        strict_leakage: store.strict_leakage,
        expected_version: store.draft_version,
        is_auto_save: false,
      });
      store.setSaveState('saved');
      return store.draft_id;
    }

    // Create new draft (create endpoint doesn't accept structured_json/itinerary_text)
    const result = await createDraft({
      customer_message: store.input_raw_note || null,
      agent_notes: store.input_owner_note || null,
      stage: spineStage,
      operating_mode: currentMode,
      scenario_id: currentScenario || null,
      strict_leakage: store.strict_leakage,
    });
    store.setDraftMeta({
      draft_id: result.draft_id,
      name: result.name,
      status: result.status as DraftStatus,
      version: 1,
      created_at: result.created_at,
    });
    // Update URL
    const params = new URLSearchParams(searchParams.toString());
    params.set('draft', result.draft_id);
    if (!params.get('tab')) params.set('tab', 'intake');
    router.replace(`?${params.toString()}`, { scroll: false });
    store.setSaveState('saved');
    return result.draft_id;
  }, [store, searchParams, router, spineStage, currentMode, currentScenario]);

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
  }, [store, executeSpineRun, spineStage, currentMode, currentScenario, ensureDraftSaved]);

  // ==========================================================================
  // Draft Save
  // ==========================================================================

  const handleSaveDraft = useCallback(async () => {
    const isAuto = false;
    if (store.save_state === 'saving') return;
    store.setSaveState('saving');

    try {
      const structured_json = safeParseJson(store.input_structured_json);
      const payload = {
        customer_message: store.input_raw_note || null,
        agent_notes: store.input_owner_note || null,
        structured_json,
        itinerary_text: store.input_itinerary_text || null,
        stage: spineStage,
        operating_mode: currentMode,
        scenario_id: currentScenario || null,
        strict_leakage: store.strict_leakage,
      };

      if (store.draft_id) {
        const updated = await patchDraft(store.draft_id, {
          ...payload,
          expected_version: store.draft_version,
          is_auto_save: isAuto,
        });
        store.setDraftMeta({
          draft_id: store.draft_id,
          name: (updated.name as string) || store.draft_name,
          status: (updated.status as DraftStatus) || 'open',
          version: (updated.version as number) || (store.draft_version ?? 0) + 1,
          created_at: updated.updated_at as string,
        });
      } else {
        const result = await createDraft({
          customer_message: store.input_raw_note || null,
          agent_notes: store.input_owner_note || null,
          stage: spineStage,
          operating_mode: currentMode,
          scenario_id: currentScenario || null,
          strict_leakage: store.strict_leakage,
        });
        store.setDraftMeta({
          draft_id: result.draft_id,
          name: result.name,
          status: result.status as DraftStatus,
          version: 1,
          created_at: result.created_at,
        });
        const params = new URLSearchParams(searchParams.toString());
        params.set('draft', result.draft_id);
        if (!params.get('tab')) params.set('tab', 'intake');
        router.replace(`?${params.toString()}`, { scroll: false });
      }

      store.setSaveState('saved');
      if (!isAuto) {
        setSaveSuccess(true);
        setTimeout(() => setSaveSuccess(false), 3000);
      }
    } catch (err) {
      const isConflict = err && typeof err === 'object' && 'status' in err && (err as { status: number }).status === 409;
      if (isConflict) {
        store.setSaveState('conflict');
      } else {
        store.setSaveState('error');
      }
      if (!isAuto) {
        setSaveError(
          isConflict
            ? 'Save conflict — draft was modified elsewhere. Refresh and try again.'
            : 'Failed to save draft. Check connection and try again.',
        );
        setTimeout(() => setSaveError(null), 8000);
      }
    }
  }, [store, searchParams, router, spineStage, currentMode, currentScenario]);

  // ----- Auto-save (5s debounce, guarded) -----
  const autoSaveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const prevContentRef = useRef<string>('');

  // Initialize prevContentRef after draft hydration so auto-save
  // doesn't immediately save loaded content as new.
  useEffect(() => {
    if (store.draft_id && store.save_state === 'clean') {
      const contentKey = JSON.stringify({
        raw: store.input_raw_note,
        owner: store.input_owner_note,
        json: store.input_structured_json,
        itin: store.input_itinerary_text,
        stage: store.stage,
        mode: store.operating_mode,
        scenario: store.scenario_id,
        strict: store.strict_leakage,
      });
      prevContentRef.current = contentKey;
    }
  }, [store.draft_id, store.save_state, store.input_raw_note, store.input_owner_note,
      store.input_structured_json, store.input_itinerary_text, store.stage,
      store.operating_mode, store.scenario_id, store.strict_leakage]);

  const buildContentKey = useCallback(() => JSON.stringify({
    raw: store.input_raw_note,
    owner: store.input_owner_note,
    json: store.input_structured_json,
    itin: store.input_itinerary_text,
    stage: spineStage,
    mode: currentMode,
    scenario: currentScenario,
    strict: store.strict_leakage,
  }), [store.input_raw_note, store.input_owner_note, store.input_structured_json,
      store.input_itinerary_text, store.strict_leakage, spineStage, currentMode, currentScenario]);

  useEffect(() => {
    const hasContent =
      store.input_raw_note.trim() ||
      store.input_owner_note.trim() ||
      store.input_structured_json.trim() ||
      store.input_itinerary_text.trim();

    if (!hasContent) return;
    if (store.draft_status === 'processing' || store.draft_status === 'promoted') return;
    if (isSpineRunning) return;
    if (store.save_state === 'saving') return;

    const contentKey = buildContentKey();
    if (contentKey === prevContentRef.current) return;

    if (autoSaveTimerRef.current) clearTimeout(autoSaveTimerRef.current);

    autoSaveTimerRef.current = setTimeout(() => {
      (async () => {
        store.setSaveState('saving');
        try {
          const structured_json = safeParseJson(store.input_structured_json);
          const payload = {
            customer_message: store.input_raw_note || null,
            agent_notes: store.input_owner_note || null,
            structured_json,
            itinerary_text: store.input_itinerary_text || null,
            stage: spineStage,
            operating_mode: currentMode,
            scenario_id: currentScenario || null,
            strict_leakage: store.strict_leakage,
          };

          if (store.draft_id) {
            const updated = await patchDraft(store.draft_id, {
              ...payload,
              expected_version: store.draft_version,
              is_auto_save: true,
            });
            store.setDraftMeta({
              draft_id: store.draft_id,
              name: (updated.name as string) || store.draft_name,
              status: (updated.status as DraftStatus) || 'open',
              version: (updated.version as number) || (store.draft_version ?? 0) + 1,
              created_at: updated.updated_at as string,
            });
          } else {
            const result = await createDraft({
              customer_message: payload.customer_message,
              agent_notes: payload.agent_notes,
              stage: payload.stage,
              operating_mode: payload.operating_mode,
              scenario_id: payload.scenario_id,
              strict_leakage: payload.strict_leakage,
            });
            store.setDraftMeta({
              draft_id: result.draft_id,
              name: result.name,
              status: result.status as DraftStatus,
              version: 1,
              created_at: result.created_at,
            });
            const params = new URLSearchParams(searchParams.toString());
            params.set('draft', result.draft_id);
            if (!params.get('tab')) params.set('tab', 'intake');
            router.replace(`?${params.toString()}`, { scroll: false });
          }
          // Mark as saved only after successful API call
          store.setSaveState('saved');
          prevContentRef.current = buildContentKey();
        } catch (err) {
          const isConflict = err && typeof err === 'object' && 'status' in err && (err as { status: number }).status === 409;
          store.setSaveState(isConflict ? 'conflict' : 'error');
          // Do NOT update prevContentRef on failure — same content is retryable
        }
      })();
    }, 5000);

    return () => {
      if (autoSaveTimerRef.current) clearTimeout(autoSaveTimerRef.current);
    };
  }, [
    store.input_raw_note,
    store.input_owner_note,
    store.input_structured_json,
    store.input_itinerary_text,
    store.draft_id,
    store.draft_status,
    store.draft_version,
    store.save_state,
    isSpineRunning,
    spineStage,
    currentMode,
    currentScenario,
    store.strict_leakage,
    searchParams,
    router,
    buildContentKey,
  ]);

  const handleSave = useCallback(async () => {
    if (!tripId) return;
    setSaveError(null);
    const result = await saveTrip(tripId, {
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
  }, [tripId, saveTrip, store.input_raw_note, store.input_owner_note]);

  const handleReset = useCallback(() => {
    store.resetAll();
    resetSpine();
    setCompletedTripId(null);
  }, [store, resetSpine]);

  const handleResolve = useCallback(async () => {
    if (!tripId) return;
    try {
      await submitTripReviewAction(
        tripId,
        'resolve',
        'Recovery completed. Feedback addressed.',
      );
      // Refresh trip data to clear recovery state
      router.refresh();
    } catch (err) {
      console.error('Failed to resolve recovery:', err);
    }
  }, [tripId, router]);

  const isRecoveryMode =
    trip?.analytics?.feedback_reopen === true ||
    trip?.analytics?.recovery_status === 'IN_RECOVERY';

  const pipelineStage = getPipelineStageForWorkbench(trip, store);

  return (
    <div className='bg-[#080a0c]'>
      {isRecoveryMode && (
        <div className='bg-[#2b1011] border-b border-[#6b2a2b] px-6 py-2 flex items-center justify-between'>
          <div className='flex items-center gap-3 text-[#ff7b72]'>
            <AlertTriangle className='h-4 w-4' />
            <span className='text-ui-xs font-bold uppercase tracking-wider'>
              Recovery Mode: Critical Feedback Detected
            </span>
          </div>
          <button
            onClick={handleResolve}
            className='flex items-center gap-1.5 px-3 py-1 bg-[#ff7b72]/10 hover:bg-[#ff7b72]/20 border border-[#ff7b72]/30 rounded-md text-[#ff7b72] text-ui-xs font-semibold transition-all'
          >
            <CheckCircle className='h-3.5 w-3.5' />
            Mark Resolved
          </button>
        </div>
      )}

      <div className="mx-6 mt-2">
        <p className="text-[11px] text-[var(--text-muted)] leading-relaxed">
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
            <AlertTriangle className="w-5 h-5 text-[#f85149] shrink-0 mt-0.5" />
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <h3 className="text-ui-sm font-semibold text-[#f85149]">
                    Trip Details Need Attention
                    {store.result_validation.gate && <span className="text-[#8b949e] font-mono ml-2">{store.result_validation.gate}</span>}
                  </h3>
                  <p className="text-ui-xs text-[#ffa198] mt-0.5">
                    {store.result_validation.reasons?.length
                      ? store.result_validation.reasons.join("; ")
                      : "Some details need attention."}
                    {" "}Check the <button
                      onClick={() => handleTabChange('packet')}
                      className="text-[#58a6ff] underline hover:no-underline font-medium inline"
                    >Trip Details</button> tab for specifics.
                  </p>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <button
                    onClick={() => handleTabChange('packet')}
                    className="px-3 py-1.5 bg-[#f85149]/10 border border-[#f85149]/30 text-[#f85149] text-ui-xs font-medium rounded-md hover:bg-[#f85149]/20 transition-colors"
                  >
                    View Details
                  </button>
                  <button
                    onClick={() => handleTabChange('intake')}
                    className="px-3 py-1.5 bg-[#161b22] border border-[#30363d] text-[#e6edf3] text-ui-xs font-medium rounded-md hover:bg-[#21262d] transition-colors"
                  >
                    Fix in Intake
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className='px-6 py-6'>
        {integrityOpen && <BackToOverviewLink className='mb-4' />}
        <header className='flex flex-col lg:flex-row lg:items-center justify-between gap-3 mb-6'>
          <div>
            <h1 className='text-ui-2xl font-semibold text-[#e6edf3] mb-1'>
              {trip ? trip.destination : (store.draft_name || 'New Inquiry')}
            </h1>
            <p className='text-ui-base text-[#a8b3c1] flex items-center gap-3'>
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
            <div className='flex items-center gap-2 mt-1.5'>
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
                <span className='text-ui-xs text-[#8b949e]'>Saving...</span>
              )}
              {store.save_state === 'saved' && store.draft_last_saved_at && (
                <span className='text-ui-xs text-[#3fb950]'>
                  Saved at {new Date(store.draft_last_saved_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              )}
              {store.save_state === 'conflict' && (
                <span className='text-ui-xs text-[#f85149] font-medium'>Save conflict — refresh to reload</span>
              )}
              {store.save_state === 'error' && (
                <span className='text-ui-xs text-[#f85149] font-medium'>Save failed</span>
              )}
            </div>
            {tripLoading && (
              <p className='text-ui-sm text-[#8b949e] mt-1'>Loading trip...</p>
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
            {store.result_run_ts && (
              <p className='text-ui-xs text-[#8b949e] mt-1'>
                Last processed: {new Date(store.result_run_ts).toLocaleString()}
              </p>
            )}
          </div>
          <div className='flex items-center gap-3 flex-wrap'>
            {runError && (
              <div className='flex items-center gap-2 px-3 py-2 bg-[#f85149]/10 border border-[#f85149]/30 rounded-lg text-ui-sm text-[#f85149]'>
                <AlertTriangle className='w-4 h-4' />
                {spineRunState?.validation && (
                  spineRunState.validation.is_valid === false ||
                  spineRunState.validation.status === "ESCALATED" ||
                  spineRunState.validation.status === "BLOCKED"
                ) ? (
                  <div className='flex flex-col'>
                    <span className='font-medium'>Validation failed</span>
                    <span className='text-ui-xs text-[#ffa198]'>
                      {spineRunState.validation.reasons?.length
                        ? spineRunState.validation.reasons.join("; ")
                        : "Trip details are incomplete."}
                      {" "}Check the Trip Details tab.
                    </span>
                  </div>
                ) : (
                  <span className='max-w-xs truncate'>{runError}</span>
                )}
              </div>
            )}
            {runSuccess && (
              <div className='flex items-center gap-2 px-3 py-2 bg-[#3fb950]/10 border border-[#3fb950]/30 rounded-lg text-ui-sm text-[#3fb950]'>
                <CheckCircle className='w-4 h-4' />
                Processed successfully
              </div>
            )}
            {saveSuccess && (
              <div className='flex items-center gap-2 px-3 py-2 bg-[#3fb950]/10 border border-[#3fb950]/30 rounded-lg text-ui-sm text-[#3fb950]'>
                <CheckCircle className='w-4 h-4' />
                Saved
              </div>
            )}
            {saveError && (
              <div className='flex items-center gap-2 px-3 py-2 bg-[#f85149]/10 border border-[#f85149]/30 rounded-lg text-ui-sm text-[#f85149]'>
                <AlertTriangle className='w-4 h-4' />
                <span className='max-w-xs truncate'>{saveError}</span>
              </div>
            )}
            <button
              type='button'
              onClick={handleProcessTrip}
              disabled={
                isRunning ||
                isSpineRunning ||
                (!store.input_raw_note && !store.input_owner_note)
              }
              className='flex items-center gap-2 px-4 py-2 bg-[#58a6ff] text-[#0d1117] rounded-lg font-medium hover:bg-[#6eb5ff] disabled:opacity-50 disabled:cursor-not-allowed transition-colors'
              aria-label={isRunning ? 'Processing inquiry' : 'Process inquiry'}
            >
              {isRunning ? (
                <>
                  <div
                    className='w-4 h-4 border-2 border-[#0d1117]/30 border-t-[#0d1117] rounded-full animate-spin'
                    aria-hidden='true'
                  />
                  Processing...
                </>
              ) : (
                <>
                  <Play className='w-4 h-4' aria-hidden='true' />
                  Process Inquiry
                </>
              )}
            </button>
            {completedTripId && (
              <>
                <button
                  type='button'
                  onClick={() => router.push(`/trips/${completedTripId}/intake`)}
                  className='flex items-center gap-2 px-4 py-2 bg-[#3fb950] text-[#0d1117] rounded-lg font-medium hover:bg-[#4cc764] transition-colors'
                >
                  <CheckCircle className='w-4 h-4' />
                  View Trip
                </button>
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
                      router.push(`/trips/${completedTripId}/intake`);
                    }}
                    className='flex items-center gap-2 px-4 py-2 bg-[#58a6ff] text-[#0d1117] rounded-lg font-medium hover:bg-[#6eb5ff] transition-colors'
                  >
                    <CheckCircle className='w-4 h-4' />
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
                onFixDetails={() => {
                  resetSpine();
                  const params = new URLSearchParams(searchParams.toString());
                  params.set('tab', 'intake');
                  router.replace(`/workbench?${params.toString()}`);
                }}
                onViewTrip={completedTripId ? () => router.push(`/trips/${completedTripId}/intake`) : undefined}
              />
            )}
            <button
              type='button'
              onClick={handleSaveDraft}
              disabled={store.save_state === 'saving' || store.draft_status === 'promoted'}
              className='flex items-center gap-2 px-3 py-2 bg-[#161b22] text-[#e6edf3] border border-[#30363d] rounded-lg font-medium hover:bg-[#21262d] disabled:opacity-50 disabled:cursor-not-allowed transition-colors'
              aria-label='Save draft'
            >
              {store.save_state === 'saving' ? (
                <>
                  <div
                    className='w-4 h-4 border-2 border-[#8b949e]/30 border-t-[#8b949e] rounded-full animate-spin'
                    aria-hidden='true'
                  />
                  Saving...
                </>
              ) : (
                <>
                  <Save className='w-4 h-4' aria-hidden='true' />
                  Save Draft
                </>
              )}
            </button>
            {tripId && (
              <button
                type='button'
                onClick={handleSave}
                disabled={isSaving}
                className='flex items-center gap-2 px-3 py-2 bg-[#161b22] text-[#e6edf3] border border-[#30363d] rounded-lg font-medium hover:bg-[#21262d] disabled:opacity-50 disabled:cursor-not-allowed transition-colors'
                aria-label='Save trip changes'
              >
                {isSaving ? (
                  <>
                    <div
                      className='w-4 h-4 border-2 border-[#8b949e]/30 border-t-[#8b949e] rounded-full animate-spin'
                      aria-hidden='true'
                    />
                    Saving...
                  </>
                ) : (
                  <>
                    <Save className='w-4 h-4' aria-hidden='true' />
                    Save Trip Changes
                  </>
                )}
              </button>
            )}
            <button
              type='button'
              onClick={handleReset}
              className='flex items-center gap-2 px-3 py-2 bg-[#161b22] text-[#e6edf3] border border-[#30363d] rounded-lg font-medium hover:bg-[#21262d] transition-colors'
              aria-label='Reset pipeline'
            >
              <RotateCcw className='w-4 h-4' aria-hidden='true' />
              Reset
            </button>
            <button
              type='button'
              onClick={() => setPanelOpen('settings', true)}
              className='flex items-center gap-2 px-3 py-2 bg-[#161b22] text-[#e6edf3] border border-[#30363d] rounded-lg font-medium hover:bg-[#21262d] transition-colors'
              aria-label='Open settings'
            >
              <Settings className='w-4 h-4' aria-hidden='true' />
            </button>
          </div>
        </header>

        {process.env.NEXT_PUBLIC_ENABLE_SCENARIO_LAB === '1' && (
        <details className='mb-4'>
          <summary className='cursor-pointer list-none text-ui-xs font-medium text-text-muted hover:text-text-primary transition-colors px-6'>
            Dev: Scenario Lab
          </summary>
          <div className='mt-2'>
            <ScenarioLab />
          </div>
        </details>
        )}

        <div className='bg-[#0f1115] border border-[#30363d] rounded-t-xl overflow-hidden'>
          <Tabs
            tabs={workspaceTabs}
            activeTab={activeTab}
            onTabChange={handleTabChange}
            ariaLabel='Trip workspace sections'
          />
        </div>

        <div
          className='bg-[#0f1115] border-x border-b border-[#30363d] rounded-b-xl'
          role='tabpanel'
          id={`tabpanel-${activeTab}`}
          aria-labelledby={`tab-${activeTab}`}
          tabIndex={0}
        >
          <div className='p-6'>
            <Suspense fallback={<InlineLoading message='Loading...' />}>
              <IntakeTab trip={trip} />
            </Suspense>
          </div>
        </div>
      </div>

      <Suspense fallback={null}>
        <SettingsPanel
          open={settingsOpen}
          onClose={() => setPanelOpen('settings', false)}
        />
        <IntegrityMonitorPanel
          open={integrityOpen}
          onClose={() => setPanelOpen('integrity', false)}
        />
      </Suspense>
    </div>
  );
}

export default function WorkbenchPage() {
  return (
    <ErrorBoundary>
      <Suspense fallback={<WorkbenchLoading />}>
        <WorkbenchContent />
      </Suspense>
    </ErrorBoundary>
  );
}

function WorkbenchLoading() {
  return (
    <div className='min-h-screen bg-[#080a0c] px-6 py-6'>
      <div className='h-8 bg-[#161b22] rounded animate-pulse mb-6 w-48' />
      <div className='h-12 bg-[#0f1115] rounded animate-pulse mb-4' />
      <div className='h-64 bg-[#0f1115] rounded animate-pulse' />
    </div>
  );
}
