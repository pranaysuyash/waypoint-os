'use client';

import { useState, useCallback, useMemo, useDeferredValue, useEffect } from 'react';
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
  Edit2,
  X,
  Globe,
  Phone,
} from 'lucide-react';
import type { Trip } from '@/lib/api-client';
import { updateTrip, ApiException } from '@/lib/api-client';
import { useAuthStore } from '@/stores/auth';
import { useWorkbenchStore } from '@/stores/workbench';
import { useSpineRun } from '@/hooks/useSpineRun';
import { useStartPlanning, useUpdateTrip } from '@/hooks/useTrips';
import { useTripContext } from '@/contexts/TripContext';
import { getTripRoute } from '@/lib/routes';
import type { SpineStage, OperatingMode, SpineRunRequest } from '@/types/spine';
import {
  CURRENCY_CONFIG,
  type SupportedCurrency,
  formatMoney,
  formatMoneyCompact,
  parseBudgetString,
  getCurrencyOptions,
} from '@/lib/currency';
import { TRIP_TYPE_OPTIONS, DESTINATION_OPTIONS } from '@/lib/combobox';
import { SmartCombobox } from '@/components/ui/SmartCombobox';
import { useFieldAuditLog } from '@/hooks/useFieldAuditLog';
import { getChangeDescription } from '@/types/audit';
import CaptureCallPanel from './CaptureCallPanel';

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

const SPINE_PROGRESS_STAGES = [
  { afterSeconds: 0, label: 'Reading notes', detail: 'Parsing the customer message and internal notes.' },
  { afterSeconds: 8, label: 'Extracting trip facts', detail: 'Finding destination, dates, party, pace, budget, and constraints.' },
  { afterSeconds: 18, label: 'Checking missing details', detail: 'Looking for blockers, ambiguity, and follow-up questions.' },
  { afterSeconds: 32, label: 'Evaluating feasibility', detail: 'Checking suitability, risk, leakage, and budget signals.' },
  { afterSeconds: 48, label: 'Preparing workspace output', detail: 'Building trip details, quote assessment, options, and ready-for-customer message.' },
  { afterSeconds: 75, label: 'Still working', detail: 'This run is taking longer than usual. Keep this page open.' },
];

function formatElapsedTime(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  if (mins === 0) return `${secs}s`;
  return `${mins}m ${secs.toString().padStart(2, '0')}s`;
}

function getSpineProgressStage(elapsedSeconds: number) {
  return [...SPINE_PROGRESS_STAGES]
    .reverse()
    .find((stage) => elapsedSeconds >= stage.afterSeconds) ?? SPINE_PROGRESS_STAGES[0];
}

interface IntakePanelProps {
  tripId: string;
  trip?: Trip | null;
}

export function IntakePanel({ tripId, trip }: IntakePanelProps) {
  const store = useWorkbenchStore();
  const currentUser = useAuthStore((state) => state.user);
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

  const deferredRawNote = useDeferredValue(input_raw_note);
  const deferredOwnerNote = useDeferredValue(input_owner_note);

  const router = useRouter();
  const [isRunning, setIsRunning] = useState(false);
  const [runError, setRunError] = useState<string | null>(null);
  const [runSuccess, setRunSuccess] = useState(false);
  const [runStartedAt, setRunStartedAt] = useState<number | null>(null);
  const [runElapsedSeconds, setRunElapsedSeconds] = useState(0);
  const { execute: executeSpineRun, isLoading: isSpineRunning } = useSpineRun();

  const { mutate: saveTrip, isSaving } = useUpdateTrip();
  const { mutate: startPlanning, isStarting: isStartingPlanning } = useStartPlanning();
  const { replaceTrip, refetchTrip } = useTripContext();
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [startPlanningSuccess, setStartPlanningSuccess] = useState(false);
  const [startPlanningError, setStartPlanningError] = useState<string | null>(null);
  const [isMarkingReady, setIsMarkingReady] = useState(false);
  const [readySuccess, setReadySuccess] = useState(false);
  const [readyError, setReadyError] = useState<string | null>(null);

  // CaptureCallPanel state
  const [showCapturePanel, setShowCapturePanel] = useState(false);

  // Audit log for tracking field changes
  const { logChange, getLatestChangeForField } = useFieldAuditLog({
    tripId,
    userId: 'agent', // In production, get from auth context
    userName: 'Agent', // In production, get from auth context
  });

  // Budget state with currency
  const [budgetAmount, setBudgetAmount] = useState('');
  const [budgetCurrency, setBudgetCurrency] = useState<SupportedCurrency>('INR');

  useEffect(() => {
    if (!runStartedAt) {
      setRunElapsedSeconds(0);
      return;
    }

    const updateElapsed = () => {
      setRunElapsedSeconds(Math.floor((Date.now() - runStartedAt) / 1000));
    };

    updateElapsed();
    const timer = window.setInterval(updateElapsed, 1000);
    return () => window.clearInterval(timer);
  }, [runStartedAt]);

  // Editable trip details state
  const [editingField, setEditingField] = useState<string | null>(null);
  const [editValues, setEditValues] = useState({
    destination: trip?.destination || '',
    type: trip?.type || '',
    party: trip?.party?.toString() || '',
    dateWindow: trip?.dateWindow || '',
    budget: trip?.budget || '',
    budgetCurrency: budgetCurrency,
  });

  // Parse existing budget to get currency and amount
  useMemo(() => {
    if (trip?.budget) {
      const parsed = parseBudgetString(trip.budget);
      if (parsed) {
        setBudgetAmount(parsed.amount.toString());
        setBudgetCurrency(parsed.currency);
      }
    }
  }, [trip?.budget]);

  const currencyOptions = getCurrencyOptions();
  const isLeadReview = trip?.status === 'new' || trip?.status === 'incomplete';

  const handleProcessTrip = useCallback(async () => {
    if (!store.input_raw_note && !store.input_owner_note) return;
    setIsRunning(true);
    setRunError(null);
    setRunSuccess(false);
    setRunStartedAt(Date.now());

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

      const completedRun = await executeSpineRun(request);

      // After async completion, the trip is saved on the backend.
      // Refresh data by navigating — workspace will re-fetch from API.
      store.setResultRunTs(new Date().toISOString());
      setRunSuccess(true);
      setTimeout(() => setRunSuccess(false), 3000);
      const targetTripId = completedRun?.trip_id || tripId;
      if (targetTripId) {
        router.push(getTripRoute(targetTripId, 'packet'));
      } else {
        setRunError('Processing completed but no trip workspace was saved. Check the run status and retry.');
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Processing failed. Please try again or contact support if the issue persists.';
      const isTimeout = message.toLowerCase().includes('timeout') || message.includes('504');
      setRunError(
        isTimeout
          ? 'Processing timed out before the AI run finished. The request is too long for a blocking web call; retry once, then switch this flow to run status polling.'
          : message
      );
      setTimeout(() => setRunError(null), 15000);
    } finally {
      setIsRunning(false);
      setRunStartedAt(null);
    }
  }, [store, executeSpineRun, router, tripId]);

  const handleSave = useCallback(async () => {
    if (!tripId) return;
    setSaveError(null);

    // Prepare update data with editable fields
    const updateData: Partial<Trip> = {
      customerMessage: store.input_raw_note,
      agentNotes: store.input_owner_note,
    };

    // Include trip detail edits
    if (editingField) {
      if (editValues.destination) updateData.destination = editValues.destination;
      if (editValues.type) updateData.type = editValues.type;
      if (editValues.party) updateData.party = parseInt(editValues.party, 10) || undefined;
      if (editValues.dateWindow) updateData.dateWindow = editValues.dateWindow;
      if (budgetAmount) {
        updateData.budget = `${formatMoney(parseFloat(budgetAmount), budgetCurrency)}`;
      }
    }

    const result = await saveTrip(tripId, updateData);
    if (result) {
      replaceTrip(result);
      setSaveSuccess(true);
      setEditingField(null);
      setTimeout(() => setSaveSuccess(false), 3000);
    } else {
      setSaveError('Failed to save. Check connection and try again.');
      setTimeout(() => setSaveError(null), 8000);
    }
  }, [tripId, saveTrip, store.input_raw_note, store.input_owner_note, editingField, editValues, budgetAmount, budgetCurrency]);

  const handleMarkReady = useCallback(async () => {
    if (!tripId) return;
    setReadyError(null);
    setReadySuccess(false);
    setIsMarkingReady(true);
    try {
      await updateTrip(tripId, { status: 'completed' } as Partial<Trip>);
      refetchTrip();
      setReadySuccess(true);
      setTimeout(() => setReadySuccess(false), 4000);
    } catch (err) {
      if (err instanceof ApiException) {
        const failures = Array.isArray(err.details) ? err.details.filter((x) => typeof x === 'string') as string[] : [];
        if (failures.length > 0) {
          setReadyError(`Ready blocked: ${failures.join(' | ')}`);
        } else {
          setReadyError(err.message || 'Ready gate failed.');
        }
      } else if (err instanceof Error) {
        setReadyError(err.message);
      } else {
        setReadyError('Failed to mark ready.');
      }
      setTimeout(() => setReadyError(null), 10000);
    } finally {
      setIsMarkingReady(false);
    }
  }, [tripId]);

  const handleStartPlanning = useCallback(async () => {
    if (!tripId) return;

    const agentId = currentUser?.id;
    const agentName = currentUser?.name || currentUser?.email || currentUser?.id;

    if (!agentId || !agentName) {
      setStartPlanningError('Your session is missing agent details. Sign in again before starting planning.');
      return;
    }

    setStartPlanningError(null);
    setStartPlanningSuccess(false);

    try {
      await startPlanning(tripId, agentId, agentName);
      await refetchTrip();
      setStartPlanningSuccess(true);
      setTimeout(() => setStartPlanningSuccess(false), 4000);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to start planning.';
      setStartPlanningError(message);
      setTimeout(() => setStartPlanningError(null), 8000);
    }
  }, [currentUser?.email, currentUser?.id, currentUser?.name, refetchTrip, startPlanning, tripId]);

  const startEditing = useCallback((field: string, currentValue: string) => {
    setEditValues(prev => ({ ...prev, [field]: currentValue }));
    setEditingField(field);
  }, []);

  const cancelEditing = useCallback(() => {
    setEditingField(null);
    // Reset edit values to current trip values
    if (trip) {
      setEditValues({
        destination: trip.destination || '',
        type: trip.type || '',
        party: trip.party?.toString() || '',
        dateWindow: trip.dateWindow || '',
        budget: trip.budget || '',
        budgetCurrency: budgetCurrency,
      });
    }
  }, [trip, budgetCurrency]);

  const saveFieldEdit = useCallback(async (field: string) => {
    if (!tripId) return;
    setSaveError(null);

    const updateData: Partial<Trip> = {};
    let previousValue: string | number | null = null;
    let newValue: string | number | null = null;

    switch (field) {
      case 'destination':
        previousValue = trip?.destination || null;
        newValue = editValues.destination;
        updateData.destination = editValues.destination;
        break;
      case 'type':
        previousValue = trip?.type || null;
        newValue = editValues.type;
        updateData.type = editValues.type;
        break;
      case 'party':
        previousValue = trip?.party || null;
        newValue = parseInt(editValues.party, 10);
        updateData.party = Number.isNaN(newValue) ? undefined : newValue;
        break;
      case 'dateWindow':
        previousValue = trip?.dateWindow || null;
        newValue = editValues.dateWindow;
        updateData.dateWindow = editValues.dateWindow;
        break;
      case 'budget':
        previousValue = trip?.budget || null;
        newValue = budgetAmount ? `${CURRENCY_CONFIG[budgetCurrency].symbol}${budgetAmount}` : null;
        updateData.budget = newValue ?? undefined;
        break;
    }

    const result = await saveTrip(tripId, updateData);
    if (result) {
      replaceTrip(result);
      // Log the change to audit trail
      if (previousValue !== newValue) {
        logChange(
          field as any,
          'update',
          previousValue,
          newValue,
          'Field edited from workspace'
        );
      }

      setSaveSuccess(true);
      setEditingField(null);
      setTimeout(() => setSaveSuccess(false), 3000);
    } else {
      setSaveError('Failed to save. Check connection and try again.');
      setTimeout(() => setSaveError(null), 8000);
    }
  }, [tripId, trip, saveTrip, editValues, budgetAmount, budgetCurrency, logChange]);

  const handleCaptureCallSave = useCallback((newTrip: Trip) => {
    setShowCapturePanel(false);
    // Refresh the trip list by navigating to the new trip's workspace
    router.push(getTripRoute(newTrip.id, 'packet'));
  }, [router]);

  const handleCaptureCallCancel = useCallback(() => {
    setShowCapturePanel(false);
  }, []);

  // Editable field component
  const EditableField = ({
    label,
    value,
    displayValue,
    field,
    icon: Icon,
    type = 'text',
    options,
  }: {
    label: string;
    value: string;
    displayValue?: string;
    field: string;
    icon?: React.ComponentType<{ className?: string }>;
    type?: 'text' | 'select' | 'number' | 'combobox';
    options?: Array<{ value: string; label: string; symbol?: string; flag?: string }>;
  }) => {
    const isEditing = editingField === field;

    // For combobox fields (trip type, destination), use SmartCombobox
    if (field === 'type' && isEditing) {
      return (
        <div className='bg-[var(--bg-surface)] border border-[var(--accent-blue)] rounded-lg p-2 -m-1'>
          <div className='flex items-center justify-between gap-1'>
            <span className='text-[var(--ui-text-xs)] text-[var(--accent-blue)] uppercase tracking-wide'>{label}</span>
            <div className='flex items-center gap-1'>
              <button
                onClick={() => saveFieldEdit(field)}
                className='p-1 bg-[var(--accent-green)] text-[var(--text-on-accent)] rounded hover:opacity-80'
                title='Save'
                aria-label='Save trip type'
              >
                <CheckCircle className='w-3 h-3' />
              </button>
              <button
                onClick={cancelEditing}
                className='p-1 bg-[var(--accent-red)] text-[var(--text-on-accent)] rounded hover:opacity-80'
                title='Cancel'
                aria-label='Cancel editing'
              >
                <X className='w-3 h-3' />
              </button>
            </div>
          </div>
          <SmartCombobox
            value={value}
            onChange={(val) => setEditValues(prev => ({ ...prev, [field]: val }))}
            options={TRIP_TYPE_OPTIONS}
            placeholder='Select or type trip type...'
            allowCustom={true}
          />
        </div>
      );
    }

    if (field === 'destination' && isEditing) {
      return (
        <div className='bg-[var(--bg-surface)] border border-[var(--accent-blue)] rounded-lg p-2 -m-1'>
          <div className='flex items-center justify-between gap-1'>
            <span className='text-[var(--ui-text-xs)] text-[var(--accent-blue)] uppercase tracking-wide'>{label}</span>
            <div className='flex items-center gap-1'>
              <button
                onClick={() => saveFieldEdit(field)}
                className='p-1 bg-[var(--accent-green)] text-[var(--text-on-accent)] rounded hover:opacity-80'
                title='Save'
                aria-label='Save destination'
              >
                <CheckCircle className='w-3 h-3' />
              </button>
              <button
                onClick={cancelEditing}
                className='p-1 bg-[var(--accent-red)] text-[var(--text-on-accent)] rounded hover:opacity-80'
                title='Cancel'
                aria-label='Cancel editing'
              >
                <X className='w-3 h-3' />
              </button>
            </div>
          </div>
          <SmartCombobox
            value={value}
            onChange={(val) => setEditValues(prev => ({ ...prev, [field]: val }))}
            options={DESTINATION_OPTIONS}
            placeholder='Select or type destination...'
            allowCustom={true}
          />
        </div>
      );
    }

    if (isEditing) {
      return (
        <div className='bg-[var(--bg-surface)] border border-[var(--accent-blue)] rounded-lg p-2 -m-1'>
          <div className='flex items-center gap-1 mb-1'>
            <span className='text-[var(--ui-text-xs)] text-[var(--accent-blue)] uppercase tracking-wide'>{label}</span>
          </div>
          <div className='flex items-center gap-1'>
            {type === 'select' && options ? (
              <select
                value={value}
                onChange={(e) => setEditValues(prev => ({ ...prev, [field]: e.target.value }))}
                className='flex-1 px-2 py-1 bg-[var(--bg-elevated)] border border-[var(--border-default)] rounded text-[var(--ui-text-xs)] text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-blue)]'
              >
                {options.map(opt => (
                  <option key={opt.value} value={opt.value}>
                    {opt.flag} {opt.label}
                  </option>
                ))}
              </select>
            ) : (
              <input
                type={type === 'number' ? 'number' : 'text'}
                value={value}
                onChange={(e) => setEditValues(prev => ({ ...prev, [field]: e.target.value }))}
                className='flex-1 px-2 py-1 bg-[var(--bg-elevated)] border border-[var(--border-default)] rounded text-[var(--ui-text-xs)] text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-blue)]'
                autoFocus
              />
            )}
            <button
              onClick={() => saveFieldEdit(field)}
              className='p-1 bg-[var(--accent-green)] text-[var(--text-on-accent)] rounded hover:opacity-80'
              title='Save'
              aria-label={`Save ${label}`}
            >
              <CheckCircle className='w-3 h-3' />
            </button>
            <button
              onClick={cancelEditing}
              className='p-1 bg-[var(--accent-red)] text-[var(--text-on-accent)] rounded hover:opacity-80'
              title='Cancel'
              aria-label='Cancel editing'
            >
              <X className='w-3 h-3' />
            </button>
          </div>
        </div>
      );
    }

    return (
      <div className='group relative'>
        <span className='text-[var(--ui-text-xs)] text-[var(--text-secondary)] uppercase tracking-wide'>{label}</span>
        <p className='text-[var(--ui-text-sm)] text-[var(--text-primary)] font-medium mt-0.5 flex items-center gap-1'>
          {Icon && <Icon className='w-3 h-3 text-[var(--text-secondary)]' />}
          {displayValue || value}
          <button
            onClick={() => startEditing(field, value)}
            className='ml-1 opacity-0 group-hover:opacity-100 transition-opacity'
            title={`Edit ${label}`}
            aria-label={`Edit ${label}`}
          >
            <Edit2 className='w-3 h-3 text-[var(--accent-blue)]' />
          </button>
        </p>
      </div>
    );
  };

  // Budget edit component with currency selector
  const BudgetField = () => {
    const isEditing = editingField === 'budget';
    const displayBudget = trip?.budget || '—';

    if (isEditing) {
      return (
        <div className='bg-[var(--bg-surface)] border border-[var(--accent-blue)] rounded-lg p-2 -m-1'>
          <div className='flex items-center gap-1 mb-1'>
            <span className='text-[var(--ui-text-xs)] text-[var(--accent-blue)] uppercase tracking-wide'>Budget</span>
          </div>
          <div className='flex items-center gap-1'>
            <input
              type='number'
              value={budgetAmount}
              onChange={(e) => setBudgetAmount(e.target.value)}
              placeholder='Amount'
              className='flex-1 px-2 py-1 bg-[var(--bg-elevated)] border border-[var(--border-default)] rounded text-[var(--ui-text-xs)] text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-blue)]'
              autoFocus
            />
            <select
              value={budgetCurrency}
              onChange={(e) => setBudgetCurrency(e.target.value as SupportedCurrency)}
              className='px-2 py-1 bg-[var(--bg-elevated)] border border-[var(--border-default)] rounded text-[var(--ui-text-xs)] text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-blue)]'
            >
              {currencyOptions.map(opt => (
                <option key={opt.value} value={opt.value}>
                  {opt.flag} {opt.value}
                </option>
              ))}
            </select>
            <button
              onClick={() => saveFieldEdit('budget')}
              className='p-1 bg-[var(--accent-green)] text-[var(--text-on-accent)] rounded hover:opacity-80'
              title='Save'
              aria-label='Save budget'
            >
              <CheckCircle className='w-3 h-3' />
            </button>
            <button
              onClick={cancelEditing}
              className='p-1 bg-[var(--accent-red)] text-[var(--text-on-accent)] rounded hover:opacity-80'
              title='Cancel'
              aria-label='Cancel editing'
            >
              <X className='w-3 h-3' />
            </button>
          </div>
        </div>
      );
    }

    return (
      <div className='group relative'>
        <span className='text-[var(--ui-text-xs)] text-[var(--text-secondary)] uppercase tracking-wide'>Budget</span>
        <p className='text-[var(--ui-text-sm)] text-[var(--text-primary)] font-medium mt-0.5 flex items-center gap-1'>
          <Wallet className='w-3 h-3 text-[var(--accent-green)]' />
          {displayBudget}
          <button
            onClick={() => setEditingField('budget')}
            className='ml-1 opacity-0 group-hover:opacity-100 transition-opacity'
            title='Edit Budget'
            aria-label='Edit budget'
          >
            <Edit2 className='w-3 h-3 text-[var(--accent-blue)]' />
          </button>
        </p>
      </div>
    );
  };

  // AI context cards derived from trip decision (if already processed)
  const decision = trip?.decision ?? null;
  const hardBlockers = decision?.hard_blockers ?? [];
  const softBlockers = decision?.soft_blockers ?? [];
  const decisionState = decision?.decision_state ?? null;

  return (
    <div className='space-y-6'>

      {/* AI context cards — quick situational awareness at top */}
      <div className='grid grid-cols-1 sm:grid-cols-3 gap-3'>
        {/* Missing before quote */}
        <div className='rounded-xl border border-[rgba(210,153,34,0.3)] bg-[rgba(210,153,34,0.05)] p-3'>
          <div className='text-[var(--ui-text-xs)] font-bold uppercase tracking-widest text-[var(--accent-amber)] mb-1.5'>Missing before quote</div>
          {hardBlockers.length > 0 ? (
            <ul className='space-y-1'>
              {hardBlockers.slice(0, 2).map((b, i) => (
                <li key={i} className='text-[var(--ui-text-xs)] text-[var(--accent-amber)] leading-tight truncate'>• {b}</li>
              ))}
              {hardBlockers.length > 2 && (
                <li className='text-[var(--ui-text-xs)] text-[var(--accent-amber)]/60'>+{hardBlockers.length - 2} more</li>
              )}
            </ul>
          ) : decisionState ? (
            <p className='text-[var(--ui-text-xs)] text-[var(--text-secondary)]'>No hard blockers — clear to quote.</p>
          ) : (
            <p className='text-[var(--ui-text-xs)] text-[var(--text-placeholder)] italic'>Process trip to check for blockers</p>
          )}
        </div>

        {/* Suggested next move */}
        <div className='rounded-xl border border-[rgba(57,208,216,0.25)] bg-[rgba(57,208,216,0.04)] p-3'>
          <div className='text-[var(--ui-text-xs)] font-bold uppercase tracking-widest text-[var(--accent-cyan)] mb-1.5'>Suggested next move</div>
          {decisionState ? (
            <p className='text-[var(--ui-text-xs)] text-[var(--text-rationale)] leading-tight'>
              {decisionState === 'PROCEED_TRAVELER_SAFE' && 'Send quote to traveler.'}
              {decisionState === 'PROCEED_INTERNAL_DRAFT' && 'Finalize internal draft before sending.'}
              {decisionState === 'BRANCH_OPTIONS' && 'Prepare multiple options for traveler.'}
              {(decisionState === 'STOP_NEEDS_REVIEW' || decisionState === 'STOP_REVIEW') && 'Resolve blockers before proceeding.'}
              {decisionState === 'ASK_FOLLOWUP' && 'Follow up with traveler for more info.'}
              {!['PROCEED_TRAVELER_SAFE','PROCEED_INTERNAL_DRAFT','BRANCH_OPTIONS','STOP_NEEDS_REVIEW','STOP_REVIEW','ASK_FOLLOWUP'].includes(decisionState) && 'Review assessment output.'}
            </p>
          ) : (
            <p className='text-[var(--ui-text-xs)] text-[var(--text-placeholder)] italic'>Run AI to get next-step guidance</p>
          )}
        </div>

        {/* Owner check required */}
        <div className='rounded-xl border border-[rgba(88,166,255,0.2)] bg-[rgba(88,166,255,0.04)] p-3'>
          <div className='text-[var(--ui-text-xs)] font-bold uppercase tracking-widest text-[var(--accent-blue)] mb-1.5'>Watch points</div>
          {softBlockers.length > 0 ? (
            <ul className='space-y-1'>
              {softBlockers.slice(0, 2).map((b, i) => (
                <li key={i} className='text-[var(--ui-text-xs)] text-[var(--text-secondary)] leading-tight truncate'>• {b}</li>
              ))}
              {softBlockers.length > 2 && (
                <li className='text-[var(--ui-text-xs)] text-[var(--text-secondary)]/60'>+{softBlockers.length - 2} more</li>
              )}
            </ul>
          ) : decisionState ? (
            <p className='text-[var(--ui-text-xs)] text-[var(--text-secondary)]'>No soft blockers flagged.</p>
          ) : (
            <p className='text-[var(--ui-text-xs)] text-[var(--text-placeholder)] italic'>Process trip to surface watch points</p>
          )}
        </div>
      </div>

      {isRunning && (
        <div
          className='bg-elevated border border-[var(--accent-blue)]/40 rounded-xl p-4 shadow-[0_0_0_1px_rgba(88,166,255,0.08)]'
          role='status'
          aria-live='polite'
          aria-busy='true'
        >
          <div className='flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between'>
            <div className='flex items-start gap-3'>
              <div
                className='mt-1 h-4 w-4 rounded-full border-2 border-[var(--accent-blue)]/30 border-t-[var(--accent-blue)] animate-spin'
                aria-hidden='true'
              />
              <div>
                <p className='text-[var(--ui-text-sm)] font-semibold text-[var(--text-primary)]'>
                  {getSpineProgressStage(runElapsedSeconds).label}
                </p>
                <p className='mt-1 text-[var(--ui-text-xs)] text-[var(--text-secondary)] max-w-2xl'>
                  {getSpineProgressStage(runElapsedSeconds).detail}
                </p>
              </div>
            </div>
            <div className='text-left sm:text-right'>
              <p className='text-[var(--ui-text-xs)] font-medium text-[var(--text-primary)]'>
                Elapsed {formatElapsedTime(runElapsedSeconds)}
              </p>
              <p className='mt-1 text-[var(--ui-text-xs)] text-[var(--text-secondary)]'>
                Typical runs take 30-90 seconds.
              </p>
            </div>
          </div>
          <div className='mt-4 h-1.5 overflow-hidden rounded-full bg-[var(--bg-count-badge)]'>
            <div
              className='h-full rounded-full bg-[var(--accent-blue)] transition-all duration-500'
              style={{ width: `${Math.min(92, 12 + runElapsedSeconds)}%` }}
            />
          </div>
        </div>
      )}
      <div className='bg-[var(--bg-elevated)] border border-[var(--border-default)] rounded-xl p-4'>
        <div className='flex items-center gap-2 mb-4'>
          <Plane className='w-4 h-4 text-[var(--accent-blue)]' />
          <h3 className='text-[var(--ui-text-sm)] font-semibold text-[var(--text-primary)]'>
            Trip Details
          </h3>
        </div>
        {trip ? (
          <div className='grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3'>
            <EditableField
              label='Destination'
              value={editValues.destination}
              displayValue={trip.destination}
              field='destination'
              icon={MapPin}
            />
            <EditableField
              label='Type'
              value={editValues.type}
              displayValue={trip.type}
              field='type'
            />
            <EditableField
              label='Party Size'
              value={editValues.party}
              displayValue={trip.party ? `${trip.party} pax` : '—'}
              field='party'
              icon={Users}
              type='number'
            />
            <EditableField
              label='Dates'
              value={editValues.dateWindow}
              displayValue={trip.dateWindow || '—'}
              field='dateWindow'
              icon={Calendar}
            />
            <BudgetField />
            <div>
              <span className='text-[var(--ui-text-xs)] text-[var(--text-secondary)] uppercase tracking-wide'>Reference</span>
              <p className='text-[var(--ui-text-sm)] text-[var(--text-primary)] font-mono mt-0.5'>{tripId}</p>
            </div>
          </div>
        ) : (
          <p className='text-[var(--ui-text-sm)] text-[var(--text-secondary)]'>
            No trip loaded for ID: {tripId}. Select a trip from the inbox or dashboard to view its details.
          </p>
        )}
      </div>

      <div className='grid grid-cols-1 lg:grid-cols-2 gap-6'>
        <div className='bg-[var(--bg-elevated)] border border-[var(--border-default)] rounded-xl p-4'>
          <div className='flex items-center gap-2 mb-3'>
            <FileText className='w-4 h-4 text-[var(--text-secondary)]' />
            <label className='text-[var(--ui-text-sm)] font-medium text-[var(--text-primary)]'>
              Customer Message
            </label>
          </div>
          <textarea
            value={deferredRawNote}
            onChange={(e) => setInputRawNote(e.target.value)}
            placeholder='Paste the incoming traveler note here...'
            rows={6}
            className='w-full px-3 py-2 bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-lg text-[var(--ui-text-sm)] text-[var(--text-primary)] placeholder:text-[var(--text-secondary)] focus:outline-none focus:border-[var(--accent-blue)] resize-none font-mono'
          />
        </div>

        <div className='bg-[var(--bg-elevated)] border border-[var(--border-default)] rounded-xl p-4'>
          <div className='flex items-center gap-2 mb-3'>
            <User className='w-4 h-4 text-[var(--accent-blue)]' />
            <label className='text-[var(--ui-text-sm)] font-medium text-[var(--text-primary)]'>
              Agent Notes
            </label>
          </div>
          <textarea
            value={deferredOwnerNote}
            onChange={(e) => setInputOwnerNote(e.target.value)}
            placeholder="Add owner's comments or clarifications..."
            rows={6}
            className='w-full px-3 py-2 bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-lg text-[var(--ui-text-sm)] text-[var(--text-primary)] placeholder:text-[var(--text-secondary)] focus:outline-none focus:border-[var(--accent-blue)] resize-none'
          />
        </div>
      </div>

      <div className='bg-[var(--bg-elevated)] border border-[var(--border-default)] rounded-xl p-4'>
        <h3 className='text-[var(--ui-text-sm)] font-semibold text-[var(--text-primary)] mb-4 flex items-center gap-2'>
          <Settings className='w-4 h-4 text-[var(--text-secondary)]' />
          Configuration
        </h3>
        <div className='grid grid-cols-1 sm:grid-cols-2 gap-4'>
          <div>
            <label className='block text-[var(--ui-text-sm)] font-medium text-[var(--text-secondary)] mb-2'>
              Stage
            </label>
            <div className='relative'>
              <select
                value={stage}
                onChange={(e) => {
                  const v = e.target.value;
                  if (VALID_STAGES.has(v as SpineStage)) setStage(v as SpineStage);
                }}
                className='w-full px-3 py-2 bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-lg text-[var(--ui-text-sm)] text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-blue)] appearance-none'
              >
                {stages.map((s) => (
                  <option key={s.value} value={s.value}>
                    {s.label}
                  </option>
                ))}
              </select>
              <ChevronDown className='absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-secondary)] pointer-events-none' />
            </div>
          </div>
          <div>
            <label className='block text-[var(--ui-text-sm)] font-medium text-[var(--text-secondary)] mb-2'>
              Request Type
            </label>
            <div className='relative'>
              <select
                value={operating_mode}
                onChange={(e) => {
                  const v = e.target.value;
                  if (VALID_MODES.has(v as OperatingMode)) setOperatingMode(v as OperatingMode);
                }}
                className='w-full px-3 py-2 bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-lg text-[var(--ui-text-sm)] text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-blue)] appearance-none'
              >
                {modes.map((m) => (
                  <option key={m.value} value={m.value}>
                    {m.label}
                  </option>
                ))}
              </select>
              <ChevronDown className='absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-secondary)] pointer-events-none' />
            </div>
          </div>
        </div>
      </div>

      <div className='flex items-center justify-between pt-4 border-t border-[var(--border-default)]'>
        <div className='flex items-center gap-4 text-[var(--ui-text-sm)] text-[var(--text-secondary)] flex-wrap'>
          <div className='flex items-center gap-2'>
            <div className='w-2 h-2 rounded-full bg-[var(--accent-green)]'></div>
            <span>System Ready</span>
          </div>
          {runError && (
            <div className='flex items-center gap-2 px-3 py-1.5 bg-[var(--accent-red)]/10 border border-[var(--accent-red)]/30 rounded-lg text-[var(--ui-text-xs)] text-[var(--accent-red)]'>
              <AlertTriangle className='w-3 h-3' />
              <span className='max-w-[42rem]'>{runError}</span>
            </div>
          )}
          {runSuccess && (
            <div className='flex items-center gap-2 px-3 py-1.5 bg-[var(--accent-green)]/10 border border-[var(--accent-green)]/30 rounded-lg text-[var(--ui-text-xs)] text-[var(--accent-green)]'>
              <CheckCircle className='w-3 h-3' />
              Processed successfully
            </div>
          )}
          {saveSuccess && (
            <div className='flex items-center gap-2 px-3 py-1.5 bg-[var(--accent-green)]/10 border border-[var(--accent-green)]/30 rounded-lg text-[var(--ui-text-xs)] text-[var(--accent-green)]'>
              <CheckCircle className='w-3 h-3' />
              Saved
            </div>
          )}
          {saveError && (
            <div className='flex items-center gap-2 px-3 py-1.5 bg-[var(--accent-red)]/10 border border-[var(--accent-red)]/30 rounded-lg text-[var(--ui-text-xs)] text-[var(--accent-red)]'>
              <AlertTriangle className='w-3 h-3' />
              <span className='max-w-xs truncate'>{saveError}</span>
            </div>
          )}
          {startPlanningSuccess && (
            <div className='flex items-center gap-2 px-3 py-1.5 bg-[var(--accent-green)]/10 border border-[var(--accent-green)]/30 rounded-lg text-[var(--ui-text-xs)] text-[var(--accent-green)]'>
              <CheckCircle className='w-3 h-3' />
              Planning started
            </div>
          )}
          {startPlanningError && (
            <div className='flex items-center gap-2 px-3 py-1.5 bg-[var(--accent-red)]/10 border border-[var(--accent-red)]/30 rounded-lg text-[var(--ui-text-xs)] text-[var(--accent-red)]'>
              <AlertTriangle className='w-3 h-3' />
              <span className='max-w-[42rem] truncate'>{startPlanningError}</span>
            </div>
          )}
          {readySuccess && (
            <div className='flex items-center gap-2 px-3 py-1.5 bg-[var(--accent-green)]/10 border border-[var(--accent-green)]/30 rounded-lg text-[var(--ui-text-xs)] text-[var(--accent-green)]'>
              <CheckCircle className='w-3 h-3' />
              Ready state set
            </div>
          )}
          {readyError && (
            <div className='flex items-center gap-2 px-3 py-1.5 bg-[var(--accent-red)]/10 border border-[var(--accent-red)]/30 rounded-lg text-[var(--ui-text-xs)] text-[var(--accent-red)]'>
              <AlertTriangle className='w-3 h-3' />
              <span className='max-w-[42rem] truncate'>{readyError}</span>
            </div>
          )}
        </div>
        <div className='flex items-center gap-2'>
          {/* Secondary actions — low visual weight */}
          <button
            type='button'
            onClick={() => setShowCapturePanel(true)}
            className='flex items-center gap-1.5 px-3 py-1.5 bg-transparent text-text-tertiary border border-[var(--bg-count-badge)] rounded-lg text-[var(--ui-text-xs)] font-medium hover:text-[var(--text-secondary)] hover:border-[var(--border-default)] transition-colors'
            aria-label='Capture call'
          >
            <Phone className='w-3.5 h-3.5' aria-hidden='true' />
            Capture Call
          </button>
          <button
            type='button'
            onClick={handleSave}
            disabled={isSaving || !tripId}
            className='flex items-center gap-1.5 px-3 py-1.5 bg-transparent text-text-tertiary border border-[var(--bg-count-badge)] rounded-lg text-[var(--ui-text-xs)] font-medium hover:text-[var(--text-secondary)] hover:border-[var(--border-default)] disabled:opacity-40 disabled:cursor-not-allowed transition-colors'
            aria-label='Save changes'
          >
            {isSaving ? (
              <>
                <div
                  className='w-3.5 h-3.5 border-2 border-text-tertiary/30 border-t-text-tertiary rounded-full animate-spin'
                  aria-hidden='true'
                />
                Saving...
              </>
            ) : (
              <>
                <Save className='w-3.5 h-3.5' aria-hidden='true' />
                Save
              </>
            )}
          </button>
          {isLeadReview ? (
            <button
              type='button'
              onClick={handleStartPlanning}
              disabled={isStartingPlanning || !tripId}
              className='flex items-center gap-2 px-5 py-2 rounded-lg text-[var(--ui-text-sm)] font-bold text-text-on-accent disabled:opacity-40 disabled:cursor-not-allowed transition-all'
              style={{
                background: isStartingPlanning
                  ? 'rgba(88,166,255,0.5)'
                  : 'linear-gradient(135deg, #7ab9ff 0%, #57e0ef 50%, var(--accent-cyan) 100%)',
                boxShadow: isStartingPlanning ? 'none' : '0 0 20px rgba(57,208,216,0.3), 0 2px 8px rgba(88,166,255,0.2)',
              }}
              aria-label={isStartingPlanning ? 'Starting planning' : 'Start planning'}
            >
              {isStartingPlanning ? (
                <>
                  <div
                    className='w-4 h-4 border-2 border-text-on-accent/30 border-t-text-on-accent rounded-full animate-spin'
                    aria-hidden='true'
                  />
                  <span>Starting planning...</span>
                </>
              ) : (
                <>
                  <Play className='w-4 h-4' aria-hidden='true' />
                  Start Planning
                </>
              )}
            </button>
          ) : (
            <>
              <button
                type='button'
                onClick={handleMarkReady}
                disabled={isMarkingReady || !tripId}
                className='flex items-center gap-1.5 px-3 py-1.5 bg-[var(--bg-elevated)] text-[var(--accent-green)] border border-[rgba(63,185,80,0.25)] rounded-lg text-[var(--ui-text-xs)] font-medium hover:bg-[rgba(63,185,80,0.08)] disabled:opacity-40 disabled:cursor-not-allowed transition-colors'
                aria-label={isMarkingReady ? 'Marking ready' : 'Mark ready'}
              >
                {isMarkingReady ? (
                  <>
                    <div
                      className='w-3.5 h-3.5 border-2 border-[var(--accent-green)]/30 border-t-[var(--accent-green)] rounded-full animate-spin'
                      aria-hidden='true'
                    />
                    Checking...
                  </>
                ) : (
                  <>
                    <CheckCircle className='w-3.5 h-3.5' aria-hidden='true' />
                    Mark Ready
                  </>
                )}
              </button>

              <button
                type='button'
                onClick={handleProcessTrip}
                disabled={isRunning || isSpineRunning || (!input_raw_note && !input_owner_note)}
                className='flex items-center gap-2 px-5 py-2 rounded-lg text-[var(--ui-text-sm)] font-bold text-text-on-accent disabled:opacity-40 disabled:cursor-not-allowed transition-all'
                style={{
                  background: isRunning
                    ? 'rgba(88,166,255,0.5)'
                    : 'linear-gradient(135deg, #7ab9ff 0%, #57e0ef 50%, var(--accent-cyan) 100%)',
                  boxShadow: isRunning ? 'none' : '0 0 20px rgba(57,208,216,0.3), 0 2px 8px rgba(88,166,255,0.2)',
                }}
                aria-label={isRunning ? 'Processing trip' : 'Process trip'}
              >
                {isRunning ? (
                  <>
                    <div
                      className='w-4 h-4 border-2 border-text-on-accent/30 border-t-text-on-accent rounded-full animate-spin'
                      aria-hidden='true'
                    />
                    <span>Processing {formatElapsedTime(runElapsedSeconds)}</span>
                  </>
                ) : (
                  <>
                    <Play className='w-4 h-4' aria-hidden='true' />
                    Process Trip
                  </>
                )}
              </button>
            </>
          )}
        </div>
      </div>

      {/* CaptureCallPanel Sidebar */}
      {showCapturePanel && (
        <div className='fixed right-0 top-0 h-full w-96 shadow-lg z-50'>
          <CaptureCallPanel
            onSave={handleCaptureCallSave}
            onCancel={handleCaptureCallCancel}
          />
        </div>
      )}
    </div>
  );
}
