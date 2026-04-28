'use client';

import { useSearchParams, useRouter } from 'next/navigation';
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
import type { WorkbenchStore } from '@/stores/workbench';
import { ErrorBoundary } from '@/components/error-boundary';
import { submitTripReviewAction } from '@/lib/api-client';
import { RunProgressPanel } from './RunProgressPanel';

const IntakeTab = dynamic(() => import('./IntakeTab'));
const PacketTab = dynamic(() => import('./PacketTab'));
const DecisionTab = dynamic(() => import('./DecisionTab'));
const StrategyTab = dynamic(() => import('./StrategyTab'));
const SafetyTab = dynamic(() => import('./SafetyTab'));
const SettingsPanel = dynamic(() => import('./SettingsPanel'));
const OutputPanel = dynamic(
  () => import('@/components/workspace/panels/OutputPanel'),
);
const FeedbackPanel = dynamic(
  () => import('@/components/workspace/panels/FeedbackPanel'),
);
const FrontierDashboard = dynamic(() =>
  import('@/components/workspace/FrontierDashboard').then((m) => ({
    default: m.FrontierDashboard,
  })),
);

const workspaceTabs = [
  { id: 'intake', label: 'New Inquiry' },
  { id: 'packet', label: 'Trip Details' },
  { id: 'decision', label: 'Ready to Quote?' },
  { id: 'strategy', label: 'Build Options' },
  { id: 'safety', label: 'Final Review' },
  { id: 'output', label: 'Output Delivery' },
  { id: 'frontier', label: 'Frontier OS' },
  { id: 'feedback', label: 'Feedback' },
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
 * Output, Frontier OS, and Feedback are workspace sections, not core pipeline stages.
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
  const tripId = searchParams.get('trip');
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
      // Clear only transient run artifacts (frontier, run_ts, acknowledged flags).
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
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [completedTripId, setCompletedTripId] = useState<string | null>(null);
  const {
    execute: executeSpineRun,
    isLoading: isSpineRunning,
    error: spineError,
    reset: resetSpine,
    runId: spineRunId,
    state: spineRunState,
  } = useSpineRun();
  const { mutate: saveTrip, isSaving } = useUpdateTrip();
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  const handleProcessTrip = useCallback(async () => {
    if (!store.input_raw_note && !store.input_owner_note) return;
    if (inFlightRef.current) return;  // Prevent double-clicks
    inFlightRef.current = true;
    setIsRunning(true);
    setRunError(null);
    setRunSuccess(false);

    try {
      const request: SpineRunRequest = {
        raw_note: store.input_raw_note || null,
        owner_note: store.input_owner_note || null,
        structured_json: store.input_structured_json
          ? JSON.parse(store.input_structured_json)
          : null,
        itinerary_text: store.input_itinerary_text || null,
        stage: spineStage,
        operating_mode: currentMode,
        strict_leakage: store.strict_leakage,
        scenario_id: currentScenario || null,
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
  }, [store, executeSpineRun, spineStage, currentMode, currentScenario]);

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
    <div className='min-h-screen bg-[#080a0c]'>
      {isRecoveryMode && (
        <div className='bg-[#2b1011] border-b border-[#6b2a2b] px-6 py-2 flex items-center justify-between'>
          <div className='flex items-center gap-3 text-[#ff7b72]'>
            <AlertTriangle className='h-4 w-4' />
            <span className='text-xs font-bold uppercase tracking-wider'>
              Recovery Mode: Critical Feedback Detected
            </span>
          </div>
          <button
            onClick={handleResolve}
            className='flex items-center gap-1.5 px-3 py-1 bg-[#ff7b72]/10 hover:bg-[#ff7b72]/20 border border-[#ff7b72]/30 rounded-md text-[#ff7b72] text-xs font-semibold transition-all'
          >
            <CheckCircle className='h-3.5 w-3.5' />
            Mark Resolved
          </button>
        </div>
      )}

      <PipelineFlow currentStage={pipelineStage} />

      <div className='px-6 py-6'>
        <header className='flex flex-col lg:flex-row lg:items-center justify-between gap-3 mb-6'>
          <div>
            <h1 className='text-2xl font-semibold text-[#e6edf3] mb-1'>
              {trip ? trip.destination : 'Trip Workspace'}
            </h1>
            <p className='text-base text-[#a8b3c1]'>
              {trip
                ? `${trip.id} · ${trip.type} · ${trip.age}`
                : 'Process travel requests and generate quotes'}
            </p>
            {tripLoading && (
              <p className='text-sm text-[#8b949e] mt-1'>Loading trip...</p>
            )}
            {tripError && (
              <p className='text-sm text-[#f85149] mt-1'>
                Failed to load trip: {tripError.message}
              </p>
            )}
            {store.result_run_ts && (
              <p className='text-xs text-[#8b949e] mt-1'>
                Last processed: {new Date(store.result_run_ts).toLocaleString()}
              </p>
            )}
          </div>
          <div className='flex items-center gap-3 flex-wrap'>
            {runError && (
              <div className='flex items-center gap-2 px-3 py-2 bg-[#f85149]/10 border border-[#f85149]/30 rounded-lg text-sm text-[#f85149]'>
                <AlertTriangle className='w-4 h-4' />
                <span className='max-w-xs truncate'>{runError}</span>
              </div>
            )}
            {runSuccess && (
              <div className='flex items-center gap-2 px-3 py-2 bg-[#3fb950]/10 border border-[#3fb950]/30 rounded-lg text-sm text-[#3fb950]'>
                <CheckCircle className='w-4 h-4' />
                Processed successfully
              </div>
            )}
            {saveSuccess && (
              <div className='flex items-center gap-2 px-3 py-2 bg-[#3fb950]/10 border border-[#3fb950]/30 rounded-lg text-sm text-[#3fb950]'>
                <CheckCircle className='w-4 h-4' />
                Saved
              </div>
            )}
            {saveError && (
              <div className='flex items-center gap-2 px-3 py-2 bg-[#f85149]/10 border border-[#f85149]/30 rounded-lg text-sm text-[#f85149]'>
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
              aria-label={isRunning ? 'Processing trip' : 'Process trip'}
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
                  Process Trip
                </>
              )}
            </button>
            {completedTripId && (
              <button
                type='button'
                onClick={() => router.push(`/workspace/${completedTripId}/intake`)}
                className='flex items-center gap-2 px-4 py-2 bg-[#3fb950] text-[#0d1117] rounded-lg font-medium hover:bg-[#4cc764] transition-colors'
              >
                <CheckCircle className='w-4 h-4' />
                View Trip
              </button>
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
                onViewTrip={completedTripId ? () => router.push(`/workspace/${completedTripId}/intake`) : undefined}
              />
            )}
            <button
              type='button'
              onClick={handleSave}
              disabled={isSaving || !tripId}
              className='flex items-center gap-2 px-3 py-2 bg-[#161b22] text-[#e6edf3] border border-[#30363d] rounded-lg font-medium hover:bg-[#21262d] disabled:opacity-50 disabled:cursor-not-allowed transition-colors'
              aria-label='Save changes'
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
                  Save
                </>
              )}
            </button>
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
              onClick={() => setSettingsOpen(true)}
              className='flex items-center gap-2 px-3 py-2 bg-[#161b22] text-[#e6edf3] border border-[#30363d] rounded-lg font-medium hover:bg-[#21262d] transition-colors'
              aria-label='Open settings'
            >
              <Settings className='w-4 h-4' aria-hidden='true' />
            </button>
          </div>
        </header>

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
            <Suspense fallback={<InlineLoading message='Loading tab...' />}>
              {activeTab === 'intake' && <IntakeTab trip={trip} />}
              {activeTab === 'packet' && <PacketTab trip={trip} />}
              {activeTab === 'decision' && <DecisionTab trip={trip} />}
              {activeTab === 'strategy' && <StrategyTab trip={trip} />}
              {activeTab === 'safety' && <SafetyTab trip={trip} />}
              {activeTab === 'output' && <OutputPanel trip={trip} />}
              {activeTab === 'frontier' && (
                <FrontierDashboard
                  packetId={trip?.id}
                  sentiment={store.result_frontier?.sentiment_score ?? 0.82}
                  isAnxious={store.result_frontier?.anxiety_alert ?? false}
                  ghostActive={store.result_frontier?.ghost_triggered ?? false}
                  intelHits={store.result_frontier?.intelligence_hits ?? []}
                  logicRationale={
                    store.result_frontier?.audit_reason ||
                    store.result_decision?.rationale ||
                    ''
                  }
                />
              )}
              {activeTab === 'feedback' && trip && (
                <FeedbackPanel trip={trip} />
              )}
            </Suspense>
          </div>
        </div>
      </div>

      <Suspense fallback={null}>
        <SettingsPanel
          open={settingsOpen}
          onClose={() => setSettingsOpen(false)}
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
