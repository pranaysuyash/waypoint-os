'use client';

import { useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import {
  ChevronDown,
  FileText,
  User,
  MapPin,
  Calendar,
  Users,
  Wallet,
  Settings,
  Plane,
  Play,
  Save,
  CheckCircle,
  AlertTriangle,
} from 'lucide-react';
import type { Trip } from '@/lib/api-client';
import { useWorkbenchStore } from '@/stores/workbench';
import { useSpineRun } from '@/hooks/useSpineRun';
import { useUpdateTrip } from '@/hooks/useTrips';
import { getTripRoute } from '@/lib/routes';
import type { SpineStage, OperatingMode, SpineRunRequest } from '@/types/spine';

const stages: { value: SpineStage; label: string }[] = [
  { value: 'discovery', label: 'Discovery' },
  { value: 'shortlist', label: 'Shortlist' },
  { value: 'proposal', label: 'Proposal' },
  { value: 'booking', label: 'Booking' },
];

const VALID_STAGES = new Set<SpineStage>(stages.map(s => s.value));

const modes: { value: OperatingMode; label: string }[] = [
  { value: 'normal_intake', label: 'New Request' },
  { value: 'audit', label: 'Audit' },
  { value: 'emergency', label: 'Emergency' },
  { value: 'follow_up', label: 'Follow Up' },
  { value: 'cancellation', label: 'Cancellation' },
  { value: 'post_trip', label: 'Post Trip' },
];

const VALID_MODES = new Set<OperatingMode>(modes.map(m => m.value));

interface IntakePanelProps {
  tripId: string;
  trip?: Trip | null;
}

export function IntakePanel({ tripId, trip }: IntakePanelProps) {
  const store = useWorkbenchStore();
  const { 
    input_raw_note, 
    input_owner_note, 
    setInputRawNote, 
    setInputOwnerNote, 
    stage, 
    setStage, 
    operating_mode, 
    setOperatingMode 
  } = store;

  const router = useRouter();
  const [isRunning, setIsRunning] = useState(false);
  const [runError, setRunError] = useState<string | null>(null);
  const [runSuccess, setRunSuccess] = useState(false);
  const { execute: executeSpineRun, isLoading: isSpineRunning } = useSpineRun();

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
        stage: store.stage,
        operating_mode: store.operating_mode,
        strict_leakage: store.strict_leakage,
        scenario_id: store.scenario_id || null,
      };

      const result = await executeSpineRun(request);

      if (result.packet) store.setResultPacket(result.packet);
      if (result.validation) store.setResultValidation(result.validation);
      if (result.decision) store.setResultDecision(result.decision);
      if (result.strategy) store.setResultStrategy(result.strategy);
      if (result.internal_bundle) store.setResultInternalBundle(result.internal_bundle);
      if (result.traveler_bundle) store.setResultTravelerBundle(result.traveler_bundle);
      if (result.safety) store.setResultSafety(result.safety);
      store.setResultRunTs(new Date().toISOString());

      setRunSuccess(true);
      setTimeout(() => setRunSuccess(false), 3000);
      router.push(getTripRoute(tripId, 'packet'));
    } catch (err) {
      setRunError(err instanceof Error ? err.message : 'Processing failed. Is the spine API running on localhost:8000?');
      setTimeout(() => setRunError(null), 8000);
    } finally {
      setIsRunning(false);
    }
  }, [store, executeSpineRun, router, tripId]);

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

  const budget = trip?.budget || '—';
  const party = trip?.party || '—';
  const dateWindow = trip?.dateWindow || '—';

  return (
    <div className='space-y-6'>
      <div className='bg-[#161b22] border border-[#30363d] rounded-xl p-4'>
        <div className='flex items-center gap-2 mb-4'>
          <Plane className='w-4 h-4 text-[#58a6ff]' />
          <h3 className='text-sm font-semibold text-[#e6edf3]'>
            Trip Details
          </h3>
        </div>
        {trip ? (
          <div className='grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3'>
            <div>
              <span className='text-xs text-[#8b949e] uppercase tracking-wide'>Destination</span>
              <p className='text-sm text-[#e6edf3] font-medium mt-0.5 flex items-center gap-1'>
                <MapPin className='w-3 h-3 text-[#58a6ff]' />{trip.destination}
              </p>
            </div>
            <div>
              <span className='text-xs text-[#8b949e] uppercase tracking-wide'>Type</span>
              <p className='text-sm text-[#e6edf3] font-medium mt-0.5'>{trip.type}</p>
            </div>
            <div>
              <span className='text-xs text-[#8b949e] uppercase tracking-wide'>Party Size</span>
              <p className='text-sm text-[#e6edf3] font-medium mt-0.5 flex items-center gap-1'>
                <Users className='w-3 h-3 text-[#8b949e]' />{party} pax
              </p>
            </div>
            <div>
              <span className='text-xs text-[#8b949e] uppercase tracking-wide'>Dates</span>
              <p className='text-sm text-[#e6edf3] font-medium mt-0.5 flex items-center gap-1'>
                <Calendar className='w-3 h-3 text-[#8b949e]' />{dateWindow}
              </p>
            </div>
            <div>
              <span className='text-xs text-[#8b949e] uppercase tracking-wide'>Budget</span>
              <p className='text-sm text-[#e6edf3] font-medium mt-0.5 flex items-center gap-1'>
                <Wallet className='w-3 h-3 text-[#3fb950]' />{budget}
              </p>
            </div>
            <div>
              <span className='text-xs text-[#8b949e] uppercase tracking-wide'>Reference</span>
              <p className='text-sm text-[#e6edf3] font-mono mt-0.5'>{tripId}</p>
            </div>
          </div>
        ) : (
          <p className='text-sm text-[#8b949e]'>
            No trip loaded for ID: {tripId}. Select a trip from the inbox or dashboard to view its details.
          </p>
        )}
      </div>

      <div className='grid grid-cols-1 lg:grid-cols-2 gap-6'>
        <div className='bg-[#161b22] border border-[#30363d] rounded-xl p-4'>
          <div className='flex items-center gap-2 mb-3'>
            <FileText className='w-4 h-4 text-[#8b949e]' />
            <label className='text-sm font-medium text-[#e6edf3]'>
              Customer Message
            </label>
          </div>
          <textarea
            value={input_raw_note}
            onChange={(e) => setInputRawNote(e.target.value)}
            placeholder='Paste the incoming traveler note here...'
            rows={6}
            className='w-full px-3 py-2 bg-[#0f1115] border border-[#30363d] rounded-lg text-sm text-[#e6edf3] placeholder:text-[#8b949e] focus:outline-none focus:border-[#58a6ff] resize-none font-mono'
          />
        </div>

        <div className='bg-[#161b22] border border-[#30363d] rounded-xl p-4'>
          <div className='flex items-center gap-2 mb-3'>
            <User className='w-4 h-4 text-[#58a6ff]' />
            <label className='text-sm font-medium text-[#e6edf3]'>
              Agent Notes
            </label>
          </div>
          <textarea
            value={input_owner_note}
            onChange={(e) => setInputOwnerNote(e.target.value)}
            placeholder="Add owner's comments or clarifications..."
            rows={6}
            className='w-full px-3 py-2 bg-[#0f1115] border border-[#30363d] rounded-lg text-sm text-[#e6edf3] placeholder:text-[#8b949e] focus:outline-none focus:border-[#58a6ff] resize-none'
          />
        </div>
      </div>

      <div className='bg-[#161b22] border border-[#30363d] rounded-xl p-4'>
        <h3 className='text-sm font-semibold text-[#e6edf3] mb-4 flex items-center gap-2'>
          <Settings className='w-4 h-4 text-[#8b949e]' />
          Configuration
        </h3>
        <div className='grid grid-cols-1 sm:grid-cols-2 gap-4'>
          <div>
            <label className='block text-sm font-medium text-[#8b949e] mb-2'>
              Stage
            </label>
            <div className='relative'>
              <select
                value={stage}
                onChange={(e) => {
                  const v = e.target.value;
                  if (VALID_STAGES.has(v as SpineStage)) setStage(v as SpineStage);
                }}
                className='w-full px-3 py-2 bg-[#0f1115] border border-[#30363d] rounded-lg text-sm text-[#e6edf3] focus:outline-none focus:border-[#58a6ff] appearance-none'
              >
                {stages.map((s) => (
                  <option key={s.value} value={s.value}>
                    {s.label}
                  </option>
                ))}
              </select>
              <ChevronDown className='absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#8b949e] pointer-events-none' />
            </div>
          </div>
          <div>
            <label className='block text-sm font-medium text-[#8b949e] mb-2'>
              Request Type
            </label>
            <div className='relative'>
              <select
                value={operating_mode}
                onChange={(e) => {
                  const v = e.target.value;
                  if (VALID_MODES.has(v as OperatingMode)) setOperatingMode(v as OperatingMode);
                }}
                className='w-full px-3 py-2 bg-[#0f1115] border border-[#30363d] rounded-lg text-sm text-[#e6edf3] focus:outline-none focus:border-[#58a6ff] appearance-none'
              >
                {modes.map((m) => (
                  <option key={m.value} value={m.value}>
                    {m.label}
                  </option>
                ))}
              </select>
              <ChevronDown className='absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#8b949e] pointer-events-none' />
            </div>
          </div>
        </div>
      </div>

      <div className='flex items-center justify-between pt-4 border-t border-[#30363d]'>
        <div className='flex items-center gap-4 text-sm text-[#8b949e] flex-wrap'>
          <div className='flex items-center gap-2'>
            <div className='w-2 h-2 rounded-full bg-[#3fb950]'></div>
            <span>System Ready</span>
          </div>
          {runError && (
            <div className='flex items-center gap-2 px-3 py-1.5 bg-[#f85149]/10 border border-[#f85149]/30 rounded-lg text-xs text-[#f85149]'>
              <AlertTriangle className='w-3 h-3' />
              <span className='max-w-xs truncate'>{runError}</span>
            </div>
          )}
          {runSuccess && (
            <div className='flex items-center gap-2 px-3 py-1.5 bg-[#3fb950]/10 border border-[#3fb950]/30 rounded-lg text-xs text-[#3fb950]'>
              <CheckCircle className='w-3 h-3' />
              Processed successfully
            </div>
          )}
          {saveSuccess && (
            <div className='flex items-center gap-2 px-3 py-1.5 bg-[#3fb950]/10 border border-[#3fb950]/30 rounded-lg text-xs text-[#3fb950]'>
              <CheckCircle className='w-3 h-3' />
              Saved
            </div>
          )}
          {saveError && (
            <div className='flex items-center gap-2 px-3 py-1.5 bg-[#f85149]/10 border border-[#f85149]/30 rounded-lg text-xs text-[#f85149]'>
              <AlertTriangle className='w-3 h-3' />
              <span className='max-w-xs truncate'>{saveError}</span>
            </div>
          )}
        </div>
        <div className='flex items-center gap-3'>
          <button
            type='button'
            onClick={handleSave}
            disabled={isSaving || !tripId}
            className='flex items-center gap-2 px-3 py-2 bg-[#161b22] text-[#e6edf3] border border-[#30363d] rounded-lg text-sm font-medium hover:bg-[#21262d] disabled:opacity-50 disabled:cursor-not-allowed transition-colors'
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
            onClick={handleProcessTrip}
            disabled={isRunning || isSpineRunning || (!input_raw_note && !input_owner_note)}
            className='flex items-center gap-2 px-4 py-2 bg-[#58a6ff] text-[#0d1117] rounded-lg text-sm font-medium hover:bg-[#6eb5ff] disabled:opacity-50 disabled:cursor-not-allowed transition-colors'
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
        </div>
      </div>
    </div>
  );
}
