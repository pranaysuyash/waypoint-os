'use client';

import { useState, useCallback, useMemo, useDeferredValue, useEffect, useRef } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import {
  ChevronDown,
  ChevronRight,
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
  parseBudgetString,
  getCurrencyOptions,
} from '@/lib/currency';
import { TRIP_TYPE_OPTIONS, DESTINATION_OPTIONS } from '@/lib/combobox';
import { formatBudgetDisplay, formatDateWindowDisplay, formatInquiryReference } from '@/lib/lead-display';
import {
  getPlanningBlockerBody,
  getPlanningBlockerTitle,
  getPlanningBriefStatus,
  getPlanningMissingDetails,
  getPlanningSuggestedNextMove,
  getRecommendedPlanningFields,
  hasPlanningBriefBlocker,
} from '@/lib/planning-status';
import { SmartCombobox } from '@/components/ui/SmartCombobox';
import { Button } from '@/components/ui/button';
import { useFieldAuditLog } from '@/hooks/useFieldAuditLog';
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

type PlanningDetailId = 'budget' | 'customerName' | 'dates' | 'destination' | 'origin' | 'priorities' | 'flexibility';

interface PlanningDetailRow {
  id: PlanningDetailId;
  label: string;
  requirement: 'Required' | 'Recommended';
  addLabel: string;
  askLabel: string;
  value: string | null;
}

const NOTE_DETAIL_PREFIX: Record<string, string> = {
  priorities: 'Trip priorities',
  flexibility: 'Date flexibility',
  customerName: 'Contact name',
};

function normalizePlanningDisplayValue(value?: string | null): string | null {
  const normalized = value?.trim();
  if (!normalized) return null;
  if (['tbd', 'to confirm', 'budget missing', 'unknown', '—'].includes(normalized.toLowerCase())) return null;
  return normalized;
}

function readTaggedNoteValue(note: string | undefined, prefix: string): string | null {
  if (!note) return null;

  const line = note
    .split('\n')
    .map((entry) => entry.trim())
    .find((entry) => entry.toLowerCase().startsWith(`${prefix.toLowerCase()}:`));

  if (!line) return null;
  const value = line.slice(prefix.length + 1).trim();
  return value || null;
}

function upsertTaggedNoteValue(note: string | undefined, prefix: string, nextValue: string): string {
  const cleaned = nextValue.trim();
  const lines = (note ?? '')
    .split('\n')
    .map((entry) => entry.trimEnd())
    .filter((entry) => entry.trim().length > 0 && !entry.toLowerCase().startsWith(`${prefix.toLowerCase()}:`));

  if (!cleaned) {
    return lines.join('\n');
  }

  lines.push(`${prefix}: ${cleaned}`);
  return lines.join('\n');
}

function joinHumanList(items: string[]): string {
  if (items.length <= 1) return items[0] ?? '';
  if (items.length === 2) return `${items[0]} and ${items[1]}`;
  return `${items.slice(0, -1).join(', ')}, and ${items.at(-1)}`;
}

function buildFollowUpDraftFromRows(rows: PlanningDetailRow[]): string {
  if (rows.length === 0) {
    return 'Hi, I have what I need to start planning. I will move ahead with building options and share the next update shortly.';
  }

  const prompts: Record<PlanningDetailId, string> = {
    budget: 'your approximate budget range',
    customerName: 'the primary contact name',
    dates: 'your preferred travel dates',
    destination: 'your destination city or country',
    origin: 'your departure city',
    priorities: 'any must-have activities, hotel preferences, or trip priorities',
    flexibility: 'how flexible your dates are',
  };

  const askFor = rows.map((row) => prompts[row.id]);
  return `Hi, to start planning properly, could you confirm ${joinHumanList(askFor)}?`;
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
  const searchParams = useSearchParams();
  const fieldParam = searchParams?.get('field');

  // Auto-open editor when deep-linked from Trip Details
  useEffect(() => {
    if (fieldParam == null) return;
    const planningEditFields: PlanningDetailId[] = ['budget', 'customerName', 'origin', 'destination', 'priorities', 'flexibility'];
    const inlineEditFields = ['type', 'dateWindow', 'party'];
    if (planningEditFields.includes(fieldParam as PlanningDetailId)) {
      openPlanningEditor(fieldParam as PlanningDetailId);
      router.replace(`/trips/${tripId}/intake`, { scroll: false });
    } else if (inlineEditFields.includes(fieldParam)) {
      setEditingField(fieldParam);
      router.replace(`/trips/${tripId}/intake`, { scroll: false });
    }
  }, [fieldParam, router, tripId]);

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
  const followUpTextareaRef = useRef<HTMLTextAreaElement | null>(null);

  // CaptureCallPanel state
  const [showCapturePanel, setShowCapturePanel] = useState(false);

  // Audit log for tracking field changes
  const { logChange } = useFieldAuditLog({
    tripId,
    userId: 'agent', // In production, get from auth context
    userName: 'Agent', // In production, get from auth context
  });

  // Budget state with currency
  const [budgetAmount, setBudgetAmount] = useState('');
  const [budgetCurrency, setBudgetCurrency] = useState<SupportedCurrency>('INR');
  const [followUpDraft, setFollowUpDraft] = useState('');
  const [activePlanningEditor, setActivePlanningEditor] = useState<PlanningDetailId | null>(null);
  const [planningEditorDrafts, setPlanningEditorDrafts] = useState<Record<PlanningDetailId, string>>({
    budget: '',
    customerName: '',
    dates: '',
    destination: '',
    origin: '',
    priorities: '',
    flexibility: '',
  });

  // Refs to the underlying textarea elements so typing remains stable (uncontrolled DOM)
  const planningEditorRefs = useRef<Record<PlanningDetailId, HTMLTextAreaElement | null>>({
    budget: null,
    customerName: null,
    dates: null,
    destination: null,
    origin: null,
    priorities: null,
    flexibility: null,
  } as any);

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
    origin: trip?.origin || '',
    budget: trip?.budget || '',
    budgetCurrency: budgetCurrency,
  });

  // Parse existing budget to get currency and amount
  useEffect(() => {
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
  const planningBriefBlocked = !isLeadReview && hasPlanningBriefBlocker(trip);
  const tripPriorities = normalizePlanningDisplayValue(
    readTaggedNoteValue(trip?.agentNotes, NOTE_DETAIL_PREFIX.priorities) ?? trip?.activityProvenance
  );
  const dateFlexibility = normalizePlanningDisplayValue(
    readTaggedNoteValue(trip?.agentNotes, NOTE_DETAIL_PREFIX.flexibility)
  );
  const planningDetails = useMemo<PlanningDetailRow[]>(() => {
    const budgetValue = normalizePlanningDisplayValue(formatBudgetDisplay(trip?.budget));
    const originValue = normalizePlanningDisplayValue(trip?.origin);
    const destinationValue = normalizePlanningDisplayValue(trip?.destination);
    const rows: PlanningDetailRow[] = [];

    if (!budgetValue) {
      rows.push({
        id: 'budget',
        label: 'Budget range',
        requirement: 'Required',
        addLabel: 'Add budget',
        askLabel: 'Ask traveler',
        value: null,
      });
    }

    if (!destinationValue && getPlanningMissingDetails(trip).some((detail) => detail.label === 'Destination')) {
      rows.push({
        id: 'destination',
        label: 'Destination',
        requirement: 'Required',
        addLabel: 'Add destination',
        askLabel: 'Ask traveler',
        value: null,
      });
    }

    if (!originValue && getPlanningMissingDetails(trip).some((detail) => detail.label === 'Origin city')) {
      rows.push({
        id: 'origin',
        label: 'Origin city',
        requirement: 'Required',
        addLabel: 'Add origin',
        askLabel: 'Ask traveler',
        value: null,
      });
    }

    if (getPlanningMissingDetails(trip).some((detail) => detail.label === 'Travel window')) {
      rows.push({
        id: 'dates',
        label: 'Travel window',
        requirement: 'Required',
        addLabel: 'Add dates',
        askLabel: 'Ask traveler',
        value: null,
      });
    }

    if (!tripPriorities) {
      rows.push({
        id: 'priorities',
        label: 'Trip priorities / must-haves',
        requirement: 'Recommended',
        addLabel: 'Add priorities',
        askLabel: 'Ask traveler',
        value: null,
      });
    }

    if ((!trip?.dateWindow || trip.dateWindow.toLowerCase().includes('around') || trip.dateWindow.toLowerCase().includes('flex')) && !dateFlexibility) {
      rows.push({
        id: 'flexibility',
        label: 'Date flexibility',
        requirement: 'Recommended',
        addLabel: 'Add flexibility',
        askLabel: 'Ask traveler',
        value: null,
      });
    }

    return rows;
  }, [dateFlexibility, trip, tripPriorities]);
  const requiredPlanningDetails = planningDetails.filter((detail) => detail.requirement === 'Required');
  const recommendedPlanningDetails = planningDetails.filter((detail) => detail.requirement === 'Recommended');
  const planningPanelVisible = Boolean(trip) && !isLeadReview && planningDetails.length > 0;
  const processButtonLabel = !trip
    ? 'Process Trip'
    : isLeadReview
    ? 'Process Trip'
    : requiredPlanningDetails.length > 0
      ? 'Draft follow-up'
      : trip?.status === 'in_progress'
        ? 'Build trip options'
        : 'Continue to options';
  const [notesExpanded, setNotesExpanded] = useState(!planningPanelVisible);

  useEffect(() => {
    setNotesExpanded(!planningPanelVisible);
  }, [planningPanelVisible, tripId]);

  useEffect(() => {
    setFollowUpDraft(buildFollowUpDraftFromRows(planningDetails));
  }, [planningDetails]);

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

  const handlePrepareFollowUp = useCallback(() => {
    setOperatingMode('follow_up');
    if (!input_raw_note.trim()) {
      setInputRawNote(followUpDraft);
    }
    setNotesExpanded(true);
    window.requestAnimationFrame(() => {
      followUpTextareaRef.current?.focus();
    });
  }, [followUpDraft, input_raw_note, setInputRawNote, setOperatingMode]);

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
        origin: trip.origin || '',
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
      case 'origin':
        previousValue = trip?.origin || null;
        newValue = editValues.origin.trim();
        updateData.origin = newValue || undefined;
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

  const getPlanningEditorInitialValue = useCallback((detailId: PlanningDetailId): string => {
    if (detailId === 'origin') {
      return normalizePlanningDisplayValue(trip?.origin) ?? '';
    }

    if (detailId === 'destination') {
      return normalizePlanningDisplayValue(trip?.destination) ?? '';
    }

    if (detailId === 'priorities') {
      return tripPriorities ?? '';
    }

    if (detailId === 'flexibility') {
      return dateFlexibility ?? '';
    }

    return '';
  }, [dateFlexibility, trip?.origin, trip?.destination, tripPriorities]);

  const setPlanningEditorDraft = useCallback((detailId: PlanningDetailId, value: string) => {
    setPlanningEditorDrafts((prev) => ({
      ...prev,
      [detailId]: value,
    }));
  }, []);

  const openPlanningEditor = useCallback((detailId: PlanningDetailId) => {
    setActivePlanningEditor(detailId);
    setEditingField(null);

    if (detailId === 'budget') {
      if (trip?.budget) {
        const parsed = parseBudgetString(trip.budget);
        if (parsed) {
          setBudgetAmount(parsed.amount.toString());
          setBudgetCurrency(parsed.currency);
        }
      }
      return;
    }

    setPlanningEditorDraft(detailId, getPlanningEditorInitialValue(detailId));
  }, [getPlanningEditorInitialValue, setPlanningEditorDraft, trip?.budget]);

  const closePlanningEditor = useCallback(() => {
    if (activePlanningEditor && activePlanningEditor !== 'budget') {
      setPlanningEditorDraft(activePlanningEditor, getPlanningEditorInitialValue(activePlanningEditor));
    }
    setActivePlanningEditor(null);
  }, [activePlanningEditor, getPlanningEditorInitialValue, setPlanningEditorDraft]);

  const handleAskTravelerForDetail = useCallback(() => {
    setOperatingMode('follow_up');
    setNotesExpanded(true);
    window.requestAnimationFrame(() => {
      followUpTextareaRef.current?.focus();
    });
  }, [setOperatingMode]);

  const savePlanningEditor = useCallback(async (detailId: PlanningDetailId) => {
    if (!tripId) return;
    setSaveError(null);

    let updateData: Partial<Trip> = {};
    let updatedOwnerNote = trip?.agentNotes ?? '';
    const domValue = planningEditorRefs.current[detailId]?.value;
    const draftValue = domValue !== undefined && domValue !== null ? domValue : (planningEditorDrafts[detailId] ?? '');

    if (detailId === 'budget') {
      updateData = {
        budget: budgetAmount ? `${formatMoney(parseFloat(budgetAmount), budgetCurrency)}` : undefined,
      };
    } else if (detailId === 'origin') {
      updateData = {
        origin: draftValue.trim() || undefined,
      };
    } else if (detailId === 'destination') {
      updateData = {
        destination: draftValue.trim() || undefined,
      };
    } else if (detailId === 'dates') {
      return;
    } else if (detailId === 'customerName') {
      updateData = {
        contactName: draftValue.trim() || undefined,
        agentNotes: upsertTaggedNoteValue(updatedOwnerNote, NOTE_DETAIL_PREFIX.customerName, draftValue),
      };
    } else {
      updatedOwnerNote = upsertTaggedNoteValue(
        updatedOwnerNote,
        NOTE_DETAIL_PREFIX[detailId],
        draftValue
      );
      updateData = { agentNotes: updatedOwnerNote };
    }

    const result = await saveTrip(tripId, updateData);
    if (result) {
      replaceTrip(result);
      if (Object.prototype.hasOwnProperty.call(updateData, 'agentNotes')) {
        setInputOwnerNote(updatedOwnerNote);
      }
      setSaveSuccess(true);
      closePlanningEditor();
      setTimeout(() => setSaveSuccess(false), 3000);
      return;
    }

    setSaveError('Failed to save. Check connection and try again.');
    setTimeout(() => setSaveError(null), 8000);
  }, [
    budgetAmount,
    budgetCurrency,
    closePlanningEditor,
    planningEditorDrafts,
    replaceTrip,
    saveTrip,
    setInputOwnerNote,
    trip?.agentNotes,
    tripId,
  ]);

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
    const displayBudget = formatBudgetDisplay(trip?.budget);

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

  const renderPlanningDetailEditor = (detailId: PlanningDetailId | null) => {
    if (activePlanningEditor !== detailId) return null;

    if (detailId === 'budget') {
      return (
        <div className='mt-3 rounded-lg border border-[var(--accent-blue)]/35 bg-[var(--bg-surface)] p-3'>
          <div className='flex flex-col gap-3 sm:flex-row'>
            <input
              type='number'
              value={budgetAmount}
              onChange={(e) => setBudgetAmount(e.target.value)}
              placeholder='Approximate budget'
              className='flex-1 rounded-lg border border-[var(--border-default)] bg-[var(--bg-elevated)] px-3 py-2 text-[var(--ui-text-sm)] text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-blue)]'
              autoFocus
            />
            <select
              value={budgetCurrency}
              onChange={(e) => setBudgetCurrency(e.target.value as SupportedCurrency)}
              className='rounded-lg border border-[var(--border-default)] bg-[var(--bg-elevated)] px-3 py-2 text-[var(--ui-text-sm)] text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-blue)]'
            >
              {currencyOptions.map(opt => (
                <option key={opt.value} value={opt.value}>
                  {opt.flag} {opt.value}
                </option>
              ))}
            </select>
          </div>
          <div className='mt-3 flex flex-wrap gap-2'>
            <Button type='button' size='sm' onClick={() => void savePlanningEditor(detailId)}>
              Save budget
            </Button>
            <Button type='button' variant='ghost' size='sm' onClick={closePlanningEditor}>
              Cancel
            </Button>
          </div>
        </div>
      );
    }

    return (
      <div className='mt-3 rounded-lg border border-[var(--accent-blue)]/35 bg-[var(--bg-surface)] p-3'>
        <textarea
          ref={(el) => { if (detailId) planningEditorRefs.current[detailId] = el; }}
          defaultValue={(detailId && planningEditorDrafts[detailId]) ?? ''}
          rows={3}
          className='w-full rounded-lg border border-[var(--border-default)] bg-[var(--bg-elevated)] px-3 py-2 text-[var(--ui-text-sm)] text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-blue)] resize-none'
          placeholder={detailId === 'origin' ? 'Add the departure city' : detailId === 'destination' ? 'Add the destination city or country' : detailId === 'priorities' ? 'Add must-haves or trip priorities' : 'Add how flexible the dates are'}
          dir={detailId === 'origin' || detailId === 'destination' ? 'ltr' : undefined}
          autoFocus
        />
        <div className='mt-3 flex flex-wrap gap-2'>
          <Button type='button' size='sm' onClick={() => detailId && void savePlanningEditor(detailId)}>
            Save {detailId === 'origin' ? 'origin' : detailId === 'destination' ? 'destination' : detailId === 'priorities' ? 'priorities' : 'flexibility'}
          </Button>
          <Button type='button' variant='ghost' size='sm' onClick={closePlanningEditor}>
            Cancel
          </Button>
        </div>
      </div>
    );
  };

  const PlanningDetailSection = ({
    title,
    tone,
    rows,
  }: {
    title: string;
    tone: 'required' | 'recommended';
    rows: PlanningDetailRow[];
  }) => {
    if (rows.length === 0) return null;

    const toneClasses = tone === 'required'
      ? 'border-[rgba(248,81,73,0.18)] bg-[rgba(248,81,73,0.04)]'
      : 'border-[rgba(88,166,255,0.16)] bg-[rgba(88,166,255,0.04)]';

    return (
      <div className={`rounded-xl border p-3 ${toneClasses}`}>
        <div className='mb-3 flex items-center justify-between gap-3'>
          <h4 className='text-[11px] font-semibold text-[var(--text-secondary)]'>
            {title}
          </h4>
          <span className='text-[var(--ui-text-xs)] text-[var(--text-secondary)]'>
            {rows.length} {rows.length === 1 ? 'field' : 'fields'}
          </span>
        </div>
        <div className='space-y-3'>
          {rows.map((detail) => (
            <div key={detail.id} className='rounded-xl border border-[var(--border-default)] bg-[var(--bg-surface)] p-3'>
              <div className='flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between'>
                <div>
                  <div className='flex flex-wrap items-center gap-2'>
                    <span className='text-[var(--ui-text-sm)] font-medium text-[var(--text-primary)]'>{detail.label}</span>
                    <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${detail.requirement === 'Required' ? 'bg-[rgba(248,81,73,0.12)] text-[var(--accent-red)]' : 'bg-[rgba(88,166,255,0.12)] text-[var(--accent-blue)]'}`}>
                      {detail.requirement}
                    </span>
                  </div>
                  <p className='mt-1 text-[var(--ui-text-xs)] text-[var(--text-secondary)]'>
                    {detail.requirement === 'Required'
                      ? 'Needed before the planner can build confident options.'
                      : 'Useful for improving option quality without blocking the next step.'}
                  </p>
                </div>
                <div className='flex flex-wrap gap-2'>
                  <Button type='button' variant='secondary' size='sm' onClick={() => {
                    if (detail.id === 'dates') {
                      setEditingField('dateWindow');
                    } else {
                      openPlanningEditor(detail.id);
                    }
                  }}>
                    {detail.addLabel}
                  </Button>
                  <Button type='button' variant='outline' size='sm' onClick={handleAskTravelerForDetail}>
                    {detail.askLabel}
                  </Button>
                </div>
              </div>
                {renderPlanningDetailEditor(detail.id)}
              </div>
            ))}
          </div>
        </div>
    );
  };

  // AI context cards derived from trip decision (if already processed)
  const decision = trip?.decision ?? null;
  const hardBlockers = decision?.hard_blockers ?? [];
  const softBlockers = decision?.soft_blockers ?? [];
  const decisionState = decision?.decision_state ?? null;
  const leadNeedsConfirmation = isLeadReview;
  const watchPointLabels = softBlockers.map((blocker) => blocker.replace(/_/g, ' '));

  return (
    <div className='space-y-6'>

      {/* Compact guidance strip */}
      <div className='grid grid-cols-1 gap-2 rounded-xl border border-[var(--border-default)] bg-[var(--bg-elevated)] p-3 md:grid-cols-3'>
        <div className='min-w-0 rounded-lg bg-[rgba(210,153,34,0.05)] px-3 py-2'>
          <p className='text-[11px] font-semibold uppercase tracking-[0.16em] text-[var(--accent-amber)]'>
            {getPlanningBlockerTitle(isLeadReview, trip)}
          </p>
          {hardBlockers.length > 0 ? (
            <p className='mt-1 text-[13px] leading-5 text-[var(--text-secondary)]'>
              {hardBlockers[0]}
            </p>
          ) : leadNeedsConfirmation ? (
            <p className='mt-1 text-[13px] leading-5 text-[var(--text-secondary)]'>
              {getPlanningBlockerBody(true, trip)}
            </p>
          ) : decisionState || trip ? (
            <p className='mt-1 text-[13px] leading-5 text-[var(--text-secondary)]'>
              {getPlanningBlockerBody(false, trip)}
            </p>
          ) : (
            <p className='mt-1 text-[13px] italic leading-5 text-[var(--text-placeholder)]'>Process trip to check for blockers</p>
          )}
          {!isLeadReview && hasPlanningBriefBlocker(trip) && !hardBlockers.length && requiredPlanningDetails.length > 0 && (
            <button
              type='button'
              onClick={() => openPlanningEditor(requiredPlanningDetails[0]!.id)}
              className='mt-2 inline-flex items-center gap-1 text-[12px] font-medium text-[var(--accent-blue)] hover:text-[var(--accent-blue-hover)] transition-colors'
            >
              Add {requiredPlanningDetails[0]!.label.toLowerCase()}
            </button>
          )}
          {!isLeadReview && !hasPlanningBriefBlocker(trip) && !hardBlockers.length && (
            <button
              type='button'
              onClick={() => router.push(`/trips/${tripId}/strategy`)}
              className='mt-2 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[var(--border-default)] text-[12px] font-medium text-[var(--text-primary)] hover:bg-elevated transition-colors'
            >
              Open options
            </button>
          )}
        </div>

        <div className='min-w-0 rounded-lg bg-[rgba(57,208,216,0.04)] px-3 py-2'>
          <p className='text-[11px] font-semibold uppercase tracking-[0.16em] text-[var(--accent-cyan)]'>
            {!isLeadReview && !hasPlanningBriefBlocker(trip) && !hasPlanningBriefBlocker(trip) ? "Next" : "Next"}
          </p>
          {isLeadReview ? (
            <p className='mt-1 text-[13px] leading-5 text-[var(--text-rationale)]'>
              {getPlanningSuggestedNextMove(true, trip)}
            </p>
          ) : decisionState || trip ? (
            <p className='mt-1 text-[13px] leading-5 text-[var(--text-rationale)]'>
              {getPlanningSuggestedNextMove(false, trip)}
            </p>
          ) : (
            <p className='mt-1 text-[13px] italic leading-5 text-[var(--text-placeholder)]'>Run AI to get next-step guidance</p>
          )}
          {!isLeadReview && hasPlanningBriefBlocker(trip) && (
            <button
              type='button'
              onClick={() => {
                if (requiredPlanningDetails.length > 0) {
                  openPlanningEditor(requiredPlanningDetails[0]!.id);
                } else {
                  handleAskTravelerForDetail();
                }
              }}
              className='mt-2 inline-flex items-center gap-1 px-3 py-1.5 rounded-lg border border-[var(--border-default)] text-[12px] font-medium text-[var(--text-primary)] hover:bg-elevated transition-colors'
            >
              Draft follow-up
            </button>
          )}
          {!isLeadReview && !hasPlanningBriefBlocker(trip) && (
            <button
              type='button'
              onClick={() => {
                const firstRecommended = recommendedPlanningDetails[0];
                if (firstRecommended) {
                  openPlanningEditor(firstRecommended.id);
                }
              }}
              className='mt-2 inline-flex items-center gap-1 px-3 py-1.5 rounded-lg border border-[var(--border-default)] text-[12px] font-medium text-[var(--text-primary)] hover:bg-elevated transition-colors'
            >
              {recommendedPlanningDetails.length > 0 ? `Add ${recommendedPlanningDetails[0]!.label.toLowerCase()}` : 'Continue to options'}
            </button>
          )}
        </div>

        <div className='min-w-0 rounded-lg bg-[rgba(88,166,255,0.04)] px-3 py-2'>
          <p className='text-[11px] font-semibold uppercase tracking-[0.16em] text-[var(--accent-blue)]'>Watch</p>
          {isLeadReview ? (
            <p className='mt-1 text-[13px] leading-5 text-[var(--text-secondary)]'>Incomplete intake.</p>
          ) : hasPlanningBriefBlocker(trip) ? (
            <p className='mt-1 text-[13px] leading-5 text-[var(--text-secondary)]'>Blocked by missing details.</p>
          ) : getPlanningBriefStatus(trip) === "missing_recommended_details" ? (
            <p className='mt-1 text-[13px] leading-5 text-[var(--text-secondary)]'>Recommended details missing: {getRecommendedPlanningFields(trip).join(", ")}.</p>
          ) : watchPointLabels.length > 0 ? (
            <p className='mt-1 text-[13px] leading-5 text-[var(--text-secondary)]'>
              {watchPointLabels.slice(0, 2).join(' · ')}
            </p>
          ) : (
            <p className='mt-1 text-[13px] leading-5 text-[var(--text-secondary)]'>No open issues.</p>
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
      {planningPanelVisible && (
        <div className='grid grid-cols-1 gap-4 xl:grid-cols-12'>
          <div className='bg-[var(--bg-elevated)] border border-[rgba(210,153,34,0.25)] rounded-xl p-4 xl:col-span-7'>
            <div className='mb-4'>
              <h3 className='text-[var(--ui-text-sm)] font-semibold text-[var(--text-primary)]'>Missing Customer Details</h3>
              <p className='mt-1 text-[var(--ui-text-xs)] text-[var(--text-secondary)]'>
                Each missing field can be fixed here or pushed into a traveler follow-up.
              </p>
            </div>
            <div className='space-y-3'>
              <PlanningDetailSection title='Required missing fields' tone='required' rows={requiredPlanningDetails} />
              <PlanningDetailSection title='Recommended details' tone='recommended' rows={recommendedPlanningDetails} />
            </div>
          </div>

          <div className='bg-[var(--bg-elevated)] border border-[rgba(57,208,216,0.25)] rounded-xl p-4 xl:col-span-5'>
            <div className='flex items-center justify-between gap-3 mb-3'>
              <div>
                <h3 className='text-[var(--ui-text-sm)] font-semibold text-[var(--text-primary)]'>Suggested Follow-up</h3>
                <p className='mt-1 text-[var(--ui-text-xs)] text-[var(--text-secondary)]'>
                  This draft only asks for the fields still unresolved.
                </p>
              </div>
              <Button
                type='button'
                onClick={() => {
                  setInputRawNote(followUpDraft);
                  setOperatingMode('follow_up');
                  void navigator.clipboard?.writeText(followUpDraft);
                }}
                variant='secondary'
                size='sm'
              >
                Copy message
              </Button>
            </div>
            <textarea
              ref={followUpTextareaRef}
              value={followUpDraft}
              onChange={(e) => setFollowUpDraft(e.target.value)}
              rows={5}
              className='w-full px-3 py-2 bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-lg text-[var(--ui-text-sm)] text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-blue)] resize-none'
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
          <div className='space-y-4'>
            <div className='grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-7 gap-3'>
              <EditableField
                label='Origin'
                value={editValues.origin}
                displayValue={normalizePlanningDisplayValue(trip.origin) ?? '—'}
                field='origin'
                icon={MapPin}
              />
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
                displayValue={formatDateWindowDisplay(trip.dateWindow)}
                field='dateWindow'
                icon={Calendar}
              />
              <BudgetField />
              <div>
                <span className='text-[var(--ui-text-xs)] text-[var(--text-secondary)] uppercase tracking-wide'>
                  Inquiry Ref
                </span>
                <p className='text-[var(--ui-text-sm)] text-[var(--text-primary)] font-mono mt-0.5'>
                  {formatInquiryReference(tripId)}
                </p>
              </div>
            </div>
            <div className='grid grid-cols-1 lg:grid-cols-2 gap-3'>
              <div className='rounded-xl border border-[var(--border-default)] bg-[var(--bg-surface)] p-3'>
                <div className='flex items-center justify-between gap-3'>
                  <div>
                    <p className='text-[var(--ui-text-xs)] uppercase tracking-[0.18em] text-[var(--text-secondary)]'>Must-haves</p>
                    <p className='mt-1 text-[var(--ui-text-sm)] text-[var(--text-primary)]'>
                      {tripPriorities ?? 'Not captured yet'}
                    </p>
                  </div>
                  <Button type='button' variant='ghost' size='sm' onClick={() => openPlanningEditor('priorities')}>
                    {tripPriorities ? 'Edit' : 'Add'}
                  </Button>
                </div>
              </div>
              <div className='rounded-xl border border-[var(--border-default)] bg-[var(--bg-surface)] p-3'>
                <div className='flex items-center justify-between gap-3'>
                  <div>
                    <p className='text-[var(--ui-text-xs)] uppercase tracking-[0.18em] text-[var(--text-secondary)]'>Date flexibility</p>
                    <p className='mt-1 text-[var(--ui-text-sm)] text-[var(--text-primary)]'>
                      {dateFlexibility ?? 'Not captured yet'}
                    </p>
                  </div>
                  <Button type='button' variant='ghost' size='sm' onClick={() => openPlanningEditor('flexibility')}>
                    {dateFlexibility ? 'Edit' : 'Add'}
                  </Button>
                </div>
              </div>
            </div>
            {(activePlanningEditor === 'priorities' || activePlanningEditor === 'flexibility') && (
              <div className='rounded-xl border border-[var(--border-default)] bg-[var(--bg-surface)] p-3'>
                {renderPlanningDetailEditor(activePlanningEditor)}
              </div>
            )}
          </div>
        ) : (
          <p className='text-[var(--ui-text-sm)] text-[var(--text-secondary)]'>
            No trip loaded for ID: {tripId}. Select a trip from the inbox or dashboard to view its details.
          </p>
        )}
      </div>

      <div className='rounded-xl border border-[var(--border-default)] bg-[var(--bg-elevated)] p-4'>
        <div className='flex items-center justify-between gap-3'>
          <div>
            <h3 className='text-[var(--ui-text-sm)] font-semibold text-[var(--text-primary)]'>Notes</h3>
            <p className='mt-1 text-[var(--ui-text-xs)] text-[var(--text-secondary)]'>
              Keep raw traveler context and internal clarifications here.
            </p>
          </div>
          {planningPanelVisible && (
            <Button type='button' variant='ghost' size='sm' onClick={() => setNotesExpanded((current) => !current)}>
              {notesExpanded ? 'Hide notes' : 'Open notes'}
            </Button>
          )}
        </div>
        {notesExpanded && (
          <div className='mt-4 grid grid-cols-1 lg:grid-cols-2 gap-6'>
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
        )}
      </div>

      <details className='bg-[var(--bg-elevated)] border border-[var(--border-default)] rounded-xl p-4'>
        <summary className='flex cursor-pointer list-none items-center gap-2 text-[var(--ui-text-sm)] font-semibold text-[var(--text-primary)]'>
          <Settings className='w-4 h-4 text-[var(--text-secondary)]' />
          Advanced configuration
        </summary>
        <div className='mt-4 grid grid-cols-1 sm:grid-cols-2 gap-4'>
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
      </details>

      <div className='flex flex-col gap-4 pt-4 border-t border-[var(--border-default)]'>
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
        <div className='flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between'>
          <div className='flex items-center'>
            <Button
              type='button'
              onClick={() => setShowCapturePanel(true)}
              variant='outline'
              size='sm'
              className='text-text-tertiary'
              aria-label='Capture call notes'
            >
              <Phone className='w-3.5 h-3.5' aria-hidden='true' />
              Capture call notes
            </Button>
          </div>
          <div className='flex flex-col gap-2 lg:items-end'>
            {isLeadReview && (
              <p className='text-[11px] text-[var(--text-secondary)] max-w-[22rem] lg:text-right'>
                Start planning will assign this lead and move it to Trips in Planning.
              </p>
            )}
            {!isLeadReview && requiredPlanningDetails.length === 0 && recommendedPlanningDetails.length > 0 && (
              <p className='text-[11px] text-[var(--text-secondary)] max-w-[24rem] lg:text-right'>
                Required fields are complete. You can continue now, or tighten the recommended details first for better options.
              </p>
            )}
            <div className='flex items-center gap-2'>
              <Button
                type='button'
                onClick={handleSave}
                disabled={isSaving || !tripId}
                variant='outline'
                size='sm'
                className='text-text-tertiary'
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
                    Save changes
                  </>
                )}
              </Button>
              {isLeadReview ? (
                <Button
                  type='button'
                  onClick={handleStartPlanning}
                  disabled={isStartingPlanning || !tripId}
                  variant='default'
                  size='touch'
                  className='font-semibold'
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
                      <ChevronRight className='w-4 h-4' aria-hidden='true' />
                    </>
                  )}
                </Button>
              ) : (
                  <>
                    {!planningPanelVisible && (
                      <Button
                        type='button'
                        onClick={handleMarkReady}
                        disabled={isMarkingReady || !tripId}
                        variant='secondary'
                        size='sm'
                        className='border-[rgba(63,185,80,0.25)] text-[var(--accent-green)] hover:bg-[rgba(63,185,80,0.08)]'
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
                      </Button>
                    )}

                    <Button
                      type='button'
                      onClick={planningPanelVisible && requiredPlanningDetails.length > 0 ? handlePrepareFollowUp : handleProcessTrip}
                      disabled={planningPanelVisible && requiredPlanningDetails.length > 0 ? !tripId : isRunning || isSpineRunning || (!input_raw_note && !input_owner_note)}
                      variant='default'
                      size='touch'
                      className='font-semibold'
                      aria-label={(!planningPanelVisible || requiredPlanningDetails.length === 0) && isRunning ? 'Processing trip' : processButtonLabel}
                    >
                      {(!planningPanelVisible || requiredPlanningDetails.length === 0) && isRunning ? (
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
                          {processButtonLabel}
                        </>
                      )}
                    </Button>
                  </>
                )}
            </div>
          </div>
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
