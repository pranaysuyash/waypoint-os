'use client';

import { useSearchParams, useRouter } from 'next/navigation';
import { Suspense, useState, lazy, useCallback, useEffect, useRef } from 'react';
import { Tabs } from '@/components/ui/tabs';
import { PipelineFlow } from './PipelineFlow';
import { Play, RotateCcw, Settings, CheckCircle, AlertTriangle, Save } from 'lucide-react';
import { InlineLoading } from '@/components/ui/loading';
import { useTrip } from '@/hooks/useTrips';
import { useWorkbenchStore } from '@/stores/workbench';
import { useSpineRun } from '@/hooks/useSpineRun';
import { useUpdateTrip } from '@/hooks/useTrips';
import type { SpineRunRequest, SpineStage, OperatingMode } from '@/types/spine';
import type { SafetyResult } from '@/types/spine';
import type { Trip } from '@/lib/api-client';
import { ErrorBoundary } from '@/components/error-boundary';
import { submitTripReviewAction } from "@/lib/api-client";

const IntakeTab = lazy(() =>
  import('./IntakeTab').then((m) => ({ default: m.IntakeTab }))
);
const PacketTab = lazy(() =>
  import('./PacketTab').then((m) => ({ default: m.PacketTab }))
);
const DecisionTab = lazy(() =>
  import('./DecisionTab').then((m) => ({ default: m.DecisionTab }))
);
const StrategyTab = lazy(() =>
  import('./StrategyTab').then((m) => ({ default: m.StrategyTab }))
);
const SafetyTab = lazy(() =>
  import('./SafetyTab').then((m) => ({ default: m.SafetyTab }))
);
const SettingsPanel = lazy(() =>
  import('./SettingsPanel').then((m) => ({ default: m.SettingsPanel }))
);
const OutputPanel = lazy(() =>
  import('@/components/workspace/panels/OutputPanel').then((m) => ({ default: m.OutputPanel }))
);
const FeedbackPanel = lazy(() =>
  import('@/components/workspace/panels/FeedbackPanel').then((m) => ({ default: m.FeedbackPanel }))
);

const workspaceTabs = [
  { id: 'intake', label: 'New Inquiry' },
  { id: 'packet', label: 'Trip Details' },
  { id: 'decision', label: 'Ready to Quote?' },
  { id: 'strategy', label: 'Build Options' },
  { id: 'safety', label: 'Final Review' },
  { id: 'output', label: 'Output Delivery' },
  { id: 'feedback', label: 'Feedback' },
];

type WorkspaceTabId = (typeof workspaceTabs)[number]['id'];

function useHydrateStoreFromTrip(trip: Trip | null | undefined) {
  const store = useWorkbenchStore();
  const hydratedRef = useRef<string | null>(null);

  useEffect(() => {
    if (!trip?.id) return;
    if (hydratedRef.current === trip.id) return;

    hydratedRef.current = trip.id;

    if (!store.result_packet && trip.packet) store.setResultPacket(trip.packet);
    if (!store.result_validation && trip.validation) store.setResultValidation(trip.validation);
    if (!store.result_decision && trip.decision) store.setResultDecision(trip.decision);
    if (!store.result_strategy && trip.strategy) store.setResultStrategy(trip.strategy);
    if (!store.result_internal_bundle && trip.internal_bundle) store.setResultInternalBundle(trip.internal_bundle);
    if (!store.result_traveler_bundle && trip.traveler_bundle) store.setResultTravelerBundle(trip.traveler_bundle);
    if (!store.result_safety && trip.safety) store.setResultSafety(trip.safety as SafetyResult | null);
    if (!store.result_fees && trip.fees) store.setResultFees(trip.fees);
    if (!store.input_raw_note && trip.customerMessage) store.setInputRawNote(trip.customerMessage);
    if (!store.input_owner_note && trip.agentNotes) store.setInputOwnerNote(trip.agentNotes);
  }, [trip, store.input_raw_note, store.input_owner_note, store.setInputRawNote, store.setInputOwnerNote, store.setResultPacket, store.setResultValidation, store.setResultDecision, store.setResultStrategy, store.setResultInternalBundle, store.setResultTravelerBundle, store.setResultSafety, store.setResultFees, store.result_packet, store.result_validation, store.result_decision, store.result_strategy, store.result_internal_bundle, store.result_traveler_bundle, store.result_safety, store.result_fees]);
}

function WorkbenchContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const tripId = searchParams.get('trip');
  const stageParam = searchParams.get('stage') as SpineStage | null;
  const modeParam = searchParams.get('mode') as OperatingMode | null;
  const scenarioParam = searchParams.get('scenario');

  const currentStage = stageParam || 'discovery';
  const currentMode = modeParam || 'normal_intake';
  const currentScenario = scenarioParam || '';

  const { data: trip, isLoading: tripLoading, error: tripError } = useTrip(tripId);
  useHydrateStoreFromTrip(trip);

  const tabParam = searchParams.get('tab') as WorkspaceTabId | null;
  const activeTab =
    tabParam && workspaceTabs.some((t) => t.id === tabParam)
      ? tabParam
      : 'intake';

  const store = useWorkbenchStore();

  // Invalidation logic: clear results if config changes
  const prevConfigRef = useRef({ stage: currentStage, mode: currentMode, scenario: currentScenario });
  useEffect(() => {
    if (
      prevConfigRef.current.stage !== currentStage ||
      prevConfigRef.current.mode !== currentMode ||
      prevConfigRef.current.scenario !== currentScenario
    ) {
      store.clearResults();
      prevConfigRef.current = { stage: currentStage, mode: currentMode, scenario: currentScenario };
    }
  }, [currentStage, currentMode, currentScenario, store.clearResults]);

  const handleTabChange = useCallback(
    (tab: WorkspaceTabId) => {
      const params = new URLSearchParams(searchParams.toString());
      params.set('tab', tab);
      router.replace(`?${params.toString()}`, { scroll: false });
    },
    [searchParams, router]
  );

  const [isRunning, setIsRunning] = useState(false);
  const [runError, setRunError] = useState<string | null>(null);
  const [runSuccess, setRunSuccess] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const { execute: executeSpineRun, isLoading: isSpineRunning, error: spineError, reset: resetSpine } = useSpineRun();
  const { mutate: saveTrip, isSaving } = useUpdateTrip();
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  const handleProcessTrip = useCallback(async () => {
    if (!store.input_raw_note && !store.input_owner_note) return;
    setIsRunning(true);
    setRunError(null);
    setRunSuccess(false);

    try {
      const request: SpineRunRequest = {
        raw_note: store.input_raw_note || null,
        owner_note: store.input_owner_note || null,
        structured_json: store.input_structured_json ? JSON.parse(store.input_structured_json) : null,
        itinerary_text: store.input_itinerary_text || null,
        stage: currentStage,
        operating_mode: currentMode,
        strict_leakage: store.strict_leakage,
        scenario_id: currentScenario || null,
      };

      const result = await executeSpineRun(request);

      if (result.packet) store.setResultPacket(result.packet);
      if (result.validation) store.setResultValidation(result.validation);
      if (result.decision) store.setResultDecision(result.decision);
      if (result.strategy) store.setResultStrategy(result.strategy);
      if (result.internal_bundle) store.setResultInternalBundle(result.internal_bundle);
      if (result.traveler_bundle) store.setResultTravelerBundle(result.traveler_bundle);
      if (result.safety) store.setResultSafety(result.safety);
      if (result.fees) store.setResultFees(result.fees);
      store.setResultRunTs(new Date().toISOString());

      setRunSuccess(true);
      setTimeout(() => setRunSuccess(false), 3000);
    } catch (err) {
      setRunError(err instanceof Error ? err.message : 'Processing failed. Is the spine API running on localhost:8000?');
      setTimeout(() => setRunError(null), 8000);
    } finally {
      setIsRunning(false);
    }
  }, [store, executeSpineRun, currentStage, currentMode, currentScenario]);

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
  }, [store, resetSpine]);

  const handleResolve = useCallback(async () => {
    if (!tripId) return;
    try {
      await submitTripReviewAction(tripId, 'resolve', 'Recovery completed. Feedback addressed.');
      // Refresh trip data to clear recovery state
      router.refresh();
    } catch (err) {
      console.error('Failed to resolve recovery:', err);
    }
  }, [tripId, router]);

  const isRecoveryMode = trip?.analytics?.feedback_reopen === true || trip?.analytics?.recovery_status === 'IN_RECOVERY';

  return (
    <div className='min-h-screen bg-[#080a0c]'>
      {isRecoveryMode && (
        <div className='bg-[#2b1011] border-b border-[#6b2a2b] px-6 py-2 flex items-center justify-between'>
          <div className='flex items-center gap-3 text-[#ff7b72]'>
            <AlertTriangle className='h-4 w-4' />
            <span className='text-xs font-bold uppercase tracking-wider'>Recovery Mode: Critical Feedback Detected</span>
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
      
      <PipelineFlow currentStage={activeTab} />

      <div className='px-6 py-6'>
        <header className='flex flex-col lg:flex-row lg:items-center justify-between gap-3 mb-6'>
          <div>
            <h1 className='text-2xl font-semibold text-[#e6edf3] mb-1'>
              {trip ? trip.destination : 'Trip Workspace'}
            </h1>
            <p className='text-base text-[#a8b3c1]'>
              {trip
                ? `${trip.id} · ${trip.type} · ${trip.age}`
                : 'Process travel requests through the analysis pipeline'}
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
              disabled={isRunning || isSpineRunning || (!store.input_raw_note && !store.input_owner_note)}
              className='flex items-center gap-2 px-4 py-2 bg-[#58a6ff] text-[#0d1117] rounded-lg font-medium hover:bg-[#6eb5ff] disabled:opacity-50 disabled:cursor-not-allowed transition-colors'
              aria-label={
                isRunning ? 'Processing trip' : 'Process trip'
              }
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
              {activeTab === 'feedback' && trip && <FeedbackPanel trip={trip} />}
            </Suspense>
          </div>
        </div>
      </div>

      <Suspense fallback={null}>
        <SettingsPanel open={settingsOpen} onClose={() => setSettingsOpen(false)} />
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
