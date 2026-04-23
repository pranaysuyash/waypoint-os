'use client';

import { useState, useCallback, useMemo, useDeferredValue } from 'react';
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
} from 'lucide-react';
import type { Trip } from '@/lib/api-client';
import { updateTrip, ApiException } from '@/lib/api-client';
import { useWorkbenchStore } from '@/stores/workbench';
import { useSpineRun } from '@/hooks/useSpineRun';
import { useUpdateTrip } from '@/hooks/useTrips';
import { getTripRoute } from '@/lib/routes';
import type { SpineStage, OperatingMode, SpineRunRequest, ValidationReport, DecisionOutput, StrategyOutput, SafetyResult, FeeCalculationResult } from '@/types/spine';
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

  const deferredRawNote = useDeferredValue(input_raw_note);
  const deferredOwnerNote = useDeferredValue(input_owner_note);

  const router = useRouter();
  const [isRunning, setIsRunning] = useState(false);
  const [runError, setRunError] = useState<string | null>(null);
  const [runSuccess, setRunSuccess] = useState(false);
  const { execute: executeSpineRun, isLoading: isSpineRunning } = useSpineRun();

  const { mutate: saveTrip, isSaving } = useUpdateTrip();
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [isMarkingReady, setIsMarkingReady] = useState(false);
  const [readySuccess, setReadySuccess] = useState(false);
  const [readyError, setReadyError] = useState<string | null>(null);

  // Audit log for tracking field changes
  const { logChange, getLatestChangeForField } = useFieldAuditLog({
    tripId,
    userId: 'agent', // In production, get from auth context
    userName: 'Agent', // In production, get from auth context
  });

  // Budget state with currency
  const [budgetAmount, setBudgetAmount] = useState('');
  const [budgetCurrency, setBudgetCurrency] = useState<SupportedCurrency>('INR');

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
      if (result.validation) store.setResultValidation(result.validation as unknown as ValidationReport);
      if (result.decision) store.setResultDecision(result.decision as unknown as DecisionOutput);
      if (result.strategy) store.setResultStrategy(result.strategy as unknown as StrategyOutput);
      if (result.internal_bundle) store.setResultInternalBundle(result.internal_bundle);
      if (result.traveler_bundle) store.setResultTravelerBundle(result.traveler_bundle);
      if (result.safety) store.setResultSafety(result.safety as unknown as SafetyResult);
      if (result.fees) store.setResultFees(result.fees as unknown as FeeCalculationResult);
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
        <div className='bg-[#0f1115] border border-[#58a6ff] rounded-lg p-2 -m-1'>
          <div className='flex items-center justify-between gap-1'>
            <span className='text-[10px] text-[#58a6ff] uppercase tracking-wide'>{label}</span>
            <div className='flex items-center gap-1'>
              <button
                onClick={() => saveFieldEdit(field)}
                className='p-1 bg-[#3fb950] text-[#0d1117] rounded hover:bg-[#2ea043]'
                title='Save'
                aria-label='Save trip type'
              >
                <CheckCircle className='w-3 h-3' />
              </button>
              <button
                onClick={cancelEditing}
                className='p-1 bg-[#f85149] text-[#0d1117] rounded hover:bg-[#da3633]'
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
        <div className='bg-[#0f1115] border border-[#58a6ff] rounded-lg p-2 -m-1'>
          <div className='flex items-center justify-between gap-1'>
            <span className='text-[10px] text-[#58a6ff] uppercase tracking-wide'>{label}</span>
            <div className='flex items-center gap-1'>
              <button
                onClick={() => saveFieldEdit(field)}
                className='p-1 bg-[#3fb950] text-[#0d1117] rounded hover:bg-[#2ea043]'
                title='Save'
                aria-label='Save destination'
              >
                <CheckCircle className='w-3 h-3' />
              </button>
              <button
                onClick={cancelEditing}
                className='p-1 bg-[#f85149] text-[#0d1117] rounded hover:bg-[#da3633]'
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
        <div className='bg-[#0f1115] border border-[#58a6ff] rounded-lg p-2 -m-1'>
          <div className='flex items-center gap-1 mb-1'>
            <span className='text-[10px] text-[#58a6ff] uppercase tracking-wide'>{label}</span>
          </div>
          <div className='flex items-center gap-1'>
            {type === 'select' && options ? (
              <select
                value={value}
                onChange={(e) => setEditValues(prev => ({ ...prev, [field]: e.target.value }))}
                className='flex-1 px-2 py-1 bg-[#161b22] border border-[#30363d] rounded text-xs text-[#e6edf3] focus:outline-none focus:border-[#58a6ff]'
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
                className='flex-1 px-2 py-1 bg-[#161b22] border border-[#30363d] rounded text-xs text-[#e6edf3] focus:outline-none focus:border-[#58a6ff]'
                autoFocus
              />
            )}
            <button
              onClick={() => saveFieldEdit(field)}
              className='p-1 bg-[#3fb950] text-[#0d1117] rounded hover:bg-[#2ea043]'
              title='Save'
              aria-label={`Save ${label}`}
            >
              <CheckCircle className='w-3 h-3' />
            </button>
            <button
              onClick={cancelEditing}
              className='p-1 bg-[#f85149] text-[#0d1117] rounded hover:bg-[#da3633]'
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
        <span className='text-xs text-[#8b949e] uppercase tracking-wide'>{label}</span>
        <p className='text-sm text-[#e6edf3] font-medium mt-0.5 flex items-center gap-1'>
          {Icon && <Icon className='w-3 h-3 text-[#8b949e]' />}
          {displayValue || value}
          <button
            onClick={() => startEditing(field, value)}
            className='ml-1 opacity-0 group-hover:opacity-100 transition-opacity'
            title={`Edit ${label}`}
            aria-label={`Edit ${label}`}
          >
            <Edit2 className='w-3 h-3 text-[#58a6ff]' />
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
        <div className='bg-[#0f1115] border border-[#58a6ff] rounded-lg p-2 -m-1'>
          <div className='flex items-center gap-1 mb-1'>
            <span className='text-[10px] text-[#58a6ff] uppercase tracking-wide'>Budget</span>
          </div>
          <div className='flex items-center gap-1'>
            <input
              type='number'
              value={budgetAmount}
              onChange={(e) => setBudgetAmount(e.target.value)}
              placeholder='Amount'
              className='flex-1 px-2 py-1 bg-[#161b22] border border-[#30363d] rounded text-xs text-[#e6edf3] focus:outline-none focus:border-[#58a6ff]'
              autoFocus
            />
            <select
              value={budgetCurrency}
              onChange={(e) => setBudgetCurrency(e.target.value as SupportedCurrency)}
              className='px-2 py-1 bg-[#161b22] border border-[#30363d] rounded text-xs text-[#e6edf3] focus:outline-none focus:border-[#58a6ff]'
            >
              {currencyOptions.map(opt => (
                <option key={opt.value} value={opt.value}>
                  {opt.flag} {opt.value}
                </option>
              ))}
            </select>
            <button
              onClick={() => saveFieldEdit('budget')}
              className='p-1 bg-[#3fb950] text-[#0d1117] rounded hover:bg-[#2ea043]'
              title='Save'
              aria-label='Save budget'
            >
              <CheckCircle className='w-3 h-3' />
            </button>
            <button
              onClick={cancelEditing}
              className='p-1 bg-[#f85149] text-[#0d1117] rounded hover:bg-[#da3633]'
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
        <span className='text-xs text-[#8b949e] uppercase tracking-wide'>Budget</span>
        <p className='text-sm text-[#e6edf3] font-medium mt-0.5 flex items-center gap-1'>
          <Wallet className='w-3 h-3 text-[#3fb950]' />
          {displayBudget}
          <button
            onClick={() => setEditingField('budget')}
            className='ml-1 opacity-0 group-hover:opacity-100 transition-opacity'
            title='Edit Budget'
            aria-label='Edit budget'
          >
            <Edit2 className='w-3 h-3 text-[#58a6ff]' />
          </button>
        </p>
      </div>
    );
  };

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
            value={deferredRawNote}
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
            value={deferredOwnerNote}
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
          {readySuccess && (
            <div className='flex items-center gap-2 px-3 py-1.5 bg-[#3fb950]/10 border border-[#3fb950]/30 rounded-lg text-xs text-[#3fb950]'>
              <CheckCircle className='w-3 h-3' />
              Ready state set
            </div>
          )}
          {readyError && (
            <div className='flex items-center gap-2 px-3 py-1.5 bg-[#f85149]/10 border border-[#f85149]/30 rounded-lg text-xs text-[#f85149]'>
              <AlertTriangle className='w-3 h-3' />
              <span className='max-w-[42rem] truncate'>{readyError}</span>
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
            onClick={handleMarkReady}
            disabled={isMarkingReady || !tripId}
            className='flex items-center gap-2 px-3 py-2 bg-[#2da44e] text-[#0d1117] rounded-lg text-sm font-medium hover:bg-[#3fb950] disabled:opacity-50 disabled:cursor-not-allowed transition-colors'
            aria-label={isMarkingReady ? 'Marking ready' : 'Mark ready'}
          >
            {isMarkingReady ? (
              <>
                <div
                  className='w-4 h-4 border-2 border-[#0d1117]/30 border-t-[#0d1117] rounded-full animate-spin'
                  aria-hidden='true'
                />
                Checking...
              </>
            ) : (
              <>
                <CheckCircle className='w-4 h-4' aria-hidden='true' />
                Mark Ready
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
