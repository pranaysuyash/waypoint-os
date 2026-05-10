'use client';

import { useState, useCallback, useMemo, useDeferredValue, useEffect, useRef, useId } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import {
  ChevronDown,
  ChevronRight,
  FileText,
  User,
  MapPin,
  Calendar,
  Users,
  Settings,
  Plane,
  Play,
  Save,
  CheckCircle,
  AlertTriangle,
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
import { Button } from '@/components/ui/button';
import { useFieldAuditLog } from '@/hooks/useFieldAuditLog';
import CaptureCallPanel from './CaptureCallPanel';
import { EditableField, BudgetField, PlanningDetailSection } from './IntakeFieldComponents';

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

export type PlanningDetailId = 'budget' | 'customerName' | 'dates' | 'destination' | 'origin' | 'priorities' | 'flexibility';

export interface PlanningDetailRow {
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
  if (['tbd', 'to confirm', 'budget missing', 'unknown', '-'].includes(normalized.toLowerCase())) return null;
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
  const lines: string[] = [];
  for (const entry of (note ?? '').split('\n')) {
    const trimmed = entry.trimEnd();
    if (trimmed.trim().length > 0 && !trimmed.toLowerCase().startsWith(`${prefix.toLowerCase()}:`)) {
      lines.push(trimmed);
    }
  }

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

  const { push } = useRouter();
  const searchParams = useSearchParams();
  const getSearchParam = searchParams.get.bind(searchParams);
  const fieldParam = getSearchParam('field');

  // Auto-open editor when deep-linked from Trip Details
  useEffect(() => {
    if (fieldParam == null) return;
    const planningEditFields: PlanningDetailId[] = ['budget', 'customerName', 'origin', 'destination', 'priorities', 'flexibility'];
    const inlineEditFields = ['type', 'dateWindow', 'party'];
    if (planningEditFields.includes(fieldParam as PlanningDetailId)) {
      openPlanningEditor(fieldParam as PlanningDetailId);
      window.history.replaceState(null, '', `/trips/${tripId}/intake`);
    } else if (inlineEditFields.includes(fieldParam)) {
      setEditingField(fieldParam);
      window.history.replaceState(null, '', `/trips/${tripId}/intake`);
    }
  }, [fieldParam, tripId]);

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
    trip?.tripPriorities ?? readTaggedNoteValue(trip?.agentNotes, NOTE_DETAIL_PREFIX.priorities) ?? trip?.activityProvenance
  );
  const dateFlexibility = normalizePlanningDisplayValue(
    trip?.dateFlexibility ?? readTaggedNoteValue(trip?.agentNotes, NOTE_DETAIL_PREFIX.flexibility)
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
  const planningPanelVisible = Boolean(trip) && planningDetails.length > 0;
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
  const notesId = useId();
  const agentNotesId = useId();
  const stageId = useId();
  const requestTypeId = useId();

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
        // retention_consent=true preserves the raw input text in the trip
        // metadata for the agency's own audit trail. Agency consent to us is
        // governed by ToS/Privacy Policy at signup (same as any B2B SaaS).
        // The public checker handles consent via its own checkbox because
        // there's no agency intermediary in that flow.
        retention_consent: true,
      };

      const completedRun = await executeSpineRun(request);

      // After async completion, the trip is saved on the backend.
      // Refresh data by navigating - workspace will re-fetch from API.
      store.setResultRunTs(new Date().toISOString());
      setRunSuccess(true);
      setTimeout(() => setRunSuccess(false), 3000);
      const targetTripId = completedRun?.trip_id || tripId;
      if (targetTripId) {
        push(getTripRoute(targetTripId, 'packet'));
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

    if (tripPriorities) updateData.tripPriorities = tripPriorities;
    if (dateFlexibility) updateData.dateFlexibility = dateFlexibility;

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
  }, [tripId, saveTrip, store.input_raw_note, store.input_owner_note, editingField, editValues, budgetAmount, budgetCurrency, tripPriorities, dateFlexibility]);

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
    push(getTripRoute(newTrip.id, 'packet'));
  }, [push]);

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
    } else if (detailId === 'priorities') {
      updateData = {
        tripPriorities: draftValue.trim() || undefined,
        agentNotes: upsertTaggedNoteValue(updatedOwnerNote, NOTE_DETAIL_PREFIX.priorities, draftValue),
      };
    } else if (detailId === 'flexibility') {
      updateData = {
        dateFlexibility: draftValue.trim() || undefined,
        agentNotes: upsertTaggedNoteValue(updatedOwnerNote, NOTE_DETAIL_PREFIX.flexibility, draftValue),
      };
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
          <p className='text-[12px] font-semibold uppercase tracking-[0.16em] text-[var(--accent-amber)]'>
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
          {hasPlanningBriefBlocker(trip) && !hardBlockers.length && requiredPlanningDetails.length > 0 && (
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
               onClick={() => push(`/trips/${tripId}/strategy`)}
               className='mt-2 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[var(--border-default)] text-[12px] font-medium text-[var(--text-primary)] hover:bg-elevated transition-colors'
             >
               Open options
             </button>
           )}
        </div>

        <div className='min-w-0 rounded-lg bg-[rgba(57,208,216,0.04)] px-3 py-2'>
          <p className='text-[12px] font-semibold uppercase tracking-[0.16em] text-[var(--accent-cyan)]'>
            {!isLeadReview && !hasPlanningBriefBlocker(trip) ? "Next Steps" : "Suggested Next Move"}
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
          <p className='text-[12px] font-semibold uppercase tracking-[0.16em] text-[var(--accent-blue)]'>Watch</p>
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
                className='mt-1 size-4 rounded-full border-2 border-[var(--accent-blue)]/30 border-t-[var(--accent-blue)] animate-spin'
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
              <PlanningDetailSection title='Required missing fields' tone='required' rows={requiredPlanningDetails} onOpenEditor={(id) => { if (id === 'dates') { setEditingField('dateWindow'); } else { openPlanningEditor(id); } }} onAskTraveler={handleAskTravelerForDetail} renderEditor={renderPlanningDetailEditor} />
              <PlanningDetailSection title='Recommended details' tone='recommended' rows={recommendedPlanningDetails} onOpenEditor={(id) => { if (id === 'dates') { setEditingField('dateWindow'); } else { openPlanningEditor(id); } }} onAskTraveler={handleAskTravelerForDetail} renderEditor={renderPlanningDetailEditor} />
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
          <Plane className='size-4 text-[var(--accent-blue)]' />
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
                displayValue={normalizePlanningDisplayValue(trip.origin) ?? '-'}
                field='origin'
                icon={MapPin}
                isEditing={editingField === 'origin'}
                onStartEdit={startEditing}
                onSaveEdit={saveFieldEdit}
                onCancelEdit={cancelEditing}
                onEditValueChange={(f, v) => setEditValues(prev => ({ ...prev, [f]: v }))}
              />
              <EditableField
                label='Destination'
                value={editValues.destination}
                displayValue={trip.destination}
                field='destination'
                icon={MapPin}
                isEditing={editingField === 'destination'}
                onStartEdit={startEditing}
                onSaveEdit={saveFieldEdit}
                onCancelEdit={cancelEditing}
                onEditValueChange={(f, v) => setEditValues(prev => ({ ...prev, [f]: v }))}
              />
              <EditableField
                label='Type'
                value={editValues.type}
                displayValue={trip.type}
                field='type'
                isEditing={editingField === 'type'}
                onStartEdit={startEditing}
                onSaveEdit={saveFieldEdit}
                onCancelEdit={cancelEditing}
                onEditValueChange={(f, v) => setEditValues(prev => ({ ...prev, [f]: v }))}
              />
              <EditableField
                label='Party Size'
                value={editValues.party}
                displayValue={trip.party ? `${trip.party} pax` : '-'}
                field='party'
                icon={Users}
                type='number'
                isEditing={editingField === 'party'}
                onStartEdit={startEditing}
                onSaveEdit={saveFieldEdit}
                onCancelEdit={cancelEditing}
                onEditValueChange={(f, v) => setEditValues(prev => ({ ...prev, [f]: v }))}
              />
              <EditableField
                label='Dates'
                value={editValues.dateWindow}
                displayValue={formatDateWindowDisplay(trip.dateWindow)}
                field='dateWindow'
                icon={Calendar}
                isEditing={editingField === 'dateWindow'}
                onStartEdit={startEditing}
                onSaveEdit={saveFieldEdit}
                onCancelEdit={cancelEditing}
                onEditValueChange={(f, v) => setEditValues(prev => ({ ...prev, [f]: v }))}
              />
              <BudgetField
                budget={trip.budget}
                budgetAmount={budgetAmount}
                budgetCurrency={budgetCurrency}
                isEditing={editingField === 'budget'}
                currencyOptions={currencyOptions}
                onStartEdit={() => setEditingField('budget')}
                onSaveEdit={() => saveFieldEdit('budget')}
                onCancelEdit={cancelEditing}
                onAmountChange={setBudgetAmount}
                onCurrencyChange={setBudgetCurrency}
              />
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
                <FileText className='size-4 text-[var(--text-secondary)]' />
                <label htmlFor={notesId} className='text-[var(--ui-text-sm)] font-medium text-[var(--text-primary)]'>
                  Customer Message
                </label>
              </div>
              <textarea
                id={notesId}
                value={deferredRawNote}
                onChange={(e) => setInputRawNote(e.target.value)}
                placeholder='Paste the incoming traveler note here…'
                rows={6}
                className='w-full px-3 py-2 bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-lg text-[var(--ui-text-sm)] text-[var(--text-primary)] placeholder:text-[var(--text-secondary)] focus:outline-none focus:border-[var(--accent-blue)] resize-none font-mono'
              />
            </div>

            <div className='bg-[var(--bg-elevated)] border border-[var(--border-default)] rounded-xl p-4'>
              <div className='flex items-center gap-2 mb-3'>
                <User className='size-4 text-[var(--accent-blue)]' />
                <label htmlFor={agentNotesId} className='text-[var(--ui-text-sm)] font-medium text-[var(--text-primary)]'>
                  Agent Notes
                </label>
              </div>
              <textarea
                id={agentNotesId}
                value={deferredOwnerNote}
                onChange={(e) => setInputOwnerNote(e.target.value)}
                placeholder="Add owner's comments or clarifications…"
                rows={6}
                className='w-full px-3 py-2 bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-lg text-[var(--ui-text-sm)] text-[var(--text-primary)] placeholder:text-[var(--text-secondary)] focus:outline-none focus:border-[var(--accent-blue)] resize-none'
              />
            </div>
          </div>
        )}
      </div>

      <details className='bg-[var(--bg-elevated)] border border-[var(--border-default)] rounded-xl p-4'>
        <summary className='flex cursor-pointer list-none items-center gap-2 text-[var(--ui-text-sm)] font-semibold text-[var(--text-primary)]'>
          <Settings className='size-4 text-[var(--text-secondary)]' />
          Advanced configuration
        </summary>
        <div className='mt-4 grid grid-cols-1 sm:grid-cols-2 gap-4'>
          <div>
            <label htmlFor={stageId} className='block text-[var(--ui-text-sm)] font-medium text-[var(--text-secondary)] mb-2'>
              Stage
            </label>
            <div className='relative'>
              <select
                id={stageId}
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
              <ChevronDown className='absolute right-3 top-1/2 -translate-y-1/2 size-4 text-[var(--text-secondary)] pointer-events-none' />
            </div>
          </div>
          <div>
            <label htmlFor={requestTypeId} className='block text-[var(--ui-text-sm)] font-medium text-[var(--text-secondary)] mb-2'>
              Request Type
            </label>
            <div className='relative'>
              <select
                id={requestTypeId}
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
              <ChevronDown className='absolute right-3 top-1/2 -translate-y-1/2 size-4 text-[var(--text-secondary)] pointer-events-none' />
            </div>
          </div>
        </div>
      </details>

      <div className='flex flex-col gap-4 pt-4 border-t border-[var(--border-default)]'>
        <div className='flex items-center gap-4 text-[var(--ui-text-sm)] text-[var(--text-secondary)] flex-wrap'>
          <div className='flex items-center gap-2'>
            <div className='size-2 rounded-full bg-[var(--accent-green)]'></div>
            <span>System Ready</span>
          </div>
          {runError && (
            <div className='flex items-center gap-2 px-3 py-1.5 bg-[var(--accent-red)]/10 border border-[var(--accent-red)]/30 rounded-lg text-[var(--ui-text-xs)] text-[var(--accent-red)]'>
              <AlertTriangle className='size-3' />
              <span className='max-w-[42rem]'>{runError}</span>
            </div>
          )}
          {runSuccess && (
            <div className='flex items-center gap-2 px-3 py-1.5 bg-[var(--accent-green)]/10 border border-[var(--accent-green)]/30 rounded-lg text-[var(--ui-text-xs)] text-[var(--accent-green)]'>
              <CheckCircle className='size-3' />
              Processed successfully
            </div>
          )}
          {saveSuccess && (
            <div className='flex items-center gap-2 px-3 py-1.5 bg-[var(--accent-green)]/10 border border-[var(--accent-green)]/30 rounded-lg text-[var(--ui-text-xs)] text-[var(--accent-green)]'>
              <CheckCircle className='size-3' />
              Saved
            </div>
          )}
          {saveError && (
            <div className='flex items-center gap-2 px-3 py-1.5 bg-[var(--accent-red)]/10 border border-[var(--accent-red)]/30 rounded-lg text-[var(--ui-text-xs)] text-[var(--accent-red)]'>
              <AlertTriangle className='size-3' />
              <span className='max-w-xs truncate'>{saveError}</span>
            </div>
          )}
          {startPlanningSuccess && (
            <div className='flex items-center gap-2 px-3 py-1.5 bg-[var(--accent-green)]/10 border border-[var(--accent-green)]/30 rounded-lg text-[var(--ui-text-xs)] text-[var(--accent-green)]'>
              <CheckCircle className='size-3' />
              Planning started
            </div>
          )}
          {startPlanningError && (
            <div className='flex items-center gap-2 px-3 py-1.5 bg-[var(--accent-red)]/10 border border-[var(--accent-red)]/30 rounded-lg text-[var(--ui-text-xs)] text-[var(--accent-red)]'>
              <AlertTriangle className='size-3' />
              <span className='max-w-[42rem] truncate'>{startPlanningError}</span>
            </div>
          )}
          {readySuccess && (
            <div className='flex items-center gap-2 px-3 py-1.5 bg-[var(--accent-green)]/10 border border-[var(--accent-green)]/30 rounded-lg text-[var(--ui-text-xs)] text-[var(--accent-green)]'>
              <CheckCircle className='size-3' />
              Ready state set
            </div>
          )}
          {readyError && (
            <div className='flex items-center gap-2 px-3 py-1.5 bg-[var(--accent-red)]/10 border border-[var(--accent-red)]/30 rounded-lg text-[var(--ui-text-xs)] text-[var(--accent-red)]'>
              <AlertTriangle className='size-3' />
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
              <Phone className='size-3.5' aria-hidden='true' />
              Capture call notes
            </Button>
          </div>
          <div className='flex flex-col gap-2 lg:items-end'>
            {isLeadReview && (
              <p className='text-[12px] text-[var(--text-secondary)] max-w-[22rem] lg:text-right'>
                Start planning will assign this lead and move it to Trips in Planning.
              </p>
            )}
            {!isLeadReview && requiredPlanningDetails.length === 0 && recommendedPlanningDetails.length > 0 && (
              <p className='text-[12px] text-[var(--text-secondary)] max-w-[24rem] lg:text-right'>
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
                      className='size-3.5 border-2 border-text-tertiary/30 border-t-text-tertiary rounded-full animate-spin'
                      aria-hidden='true'
                    />
                    Saving…
                  </>
                ) : (
                  <>
                    <Save className='size-3.5' aria-hidden='true' />
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
                        className='size-4 border-2 border-text-on-accent/30 border-t-text-on-accent rounded-full animate-spin'
                        aria-hidden='true'
                      />
                      <span>Starting planning…</span>
                    </>
                  ) : (
                    <>
                      <Play className='size-4' aria-hidden='true' />
                      Start Planning
                      <ChevronRight className='size-4' aria-hidden='true' />
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
                              className='size-3.5 border-2 border-[var(--accent-green)]/30 border-t-[var(--accent-green)] rounded-full animate-spin'
                              aria-hidden='true'
                            />
                            Checking…
                          </>
                        ) : (
                          <>
                            <CheckCircle className='size-3.5' aria-hidden='true' />
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
                            className='size-4 border-2 border-text-on-accent/30 border-t-text-on-accent rounded-full animate-spin'
                            aria-hidden='true'
                          />
                          <span>Processing {formatElapsedTime(runElapsedSeconds)}</span>
                        </>
                      ) : (
                        <>
                          <Play className='size-4' aria-hidden='true' />
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
