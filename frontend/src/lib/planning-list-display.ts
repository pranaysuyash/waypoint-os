import type { Trip } from '@/lib/api-client';
import {
  formatBudgetDisplay,
  formatInquiryReference,
} from '@/lib/lead-display';
import {
  getPlanningBriefStatus,
  getPlanningHeaderTitle,
  getPlanningIdentityLine,
  getPlanningNextAction,
  getPlanningRecencyLabel,
  getPlanningStatusLabel,
  getPlanningStatusTone,
  getRequiredPlanningFields,
} from '@/lib/planning-status';
import { getTripRoute } from '@/lib/routes';

type PlanningStateKey = 'green' | 'amber' | 'red' | 'blue';

export interface PlanningListStateMeta {
  fg: string;
  bg: string;
  border: string;
}

export const PLANNING_LIST_STATE_META: Record<PlanningStateKey, PlanningListStateMeta> = {
  green: {
    fg: '#3fb950',
    bg: 'rgba(63,185,80,0.10)',
    border: 'rgba(63,185,80,0.25)',
  },
  amber: {
    fg: '#d29922',
    bg: 'rgba(210,153,34,0.10)',
    border: 'rgba(210,153,34,0.25)',
  },
  red: {
    fg: '#f85149',
    bg: 'rgba(248,81,73,0.10)',
    border: 'rgba(248,81,73,0.25)',
  },
  blue: {
    fg: '#58a6ff',
    bg: 'rgba(88,166,255,0.10)',
    border: 'rgba(88,166,255,0.25)',
  },
};

function formatMissingDetailBadge(field: string): string {
  switch (field) {
    case 'Budget range':
      return 'Budget missing';
    case 'Origin city':
      return 'Origin missing';
    default:
      return `${field} missing`;
  }
}

function getPlanningAssignmentLabel(trip?: Trip | null): string {
  if (trip?.status === 'in_progress') return 'In progress';
  if (trip?.status === 'completed') return 'Completed';
  return 'In planning';
}

export function getPlanningStageLabel(trip?: Trip | null): string {
  const briefStatus = getPlanningBriefStatus(trip);
  if (briefStatus === "missing_required_details") return "Intake";
  if (trip?.status === "ready_to_quote" || trip?.status === "ready_to_book") return "Quote Review";
  if (trip?.status === "in_progress") return "Options";
  if (briefStatus === "missing_recommended_details" || briefStatus === "complete") return "Options";
  return "Details";
}

function getPlanningStageProgress(trip?: Trip | null): string[] {
  const allStages = ["Intake", "Details", "Options", "Quote Review", "Output"];
  const current = getPlanningStageLabel(trip);
  const currentIdx = allStages.indexOf(current);
  return allStages.map((stage, i) =>
    i < currentIdx ? `${stage} ✓` : stage === current ? `${stage} →` : stage
  );
}

export function getPlanningStageProgressItems(trip?: Trip | null): Array<{ label: string; color: string }> {
  const allStages = ["Intake", "Details", "Options", "Quote Review", "Output"];
  const current = getPlanningStageLabel(trip);
  const currentIdx = allStages.indexOf(current);
  const briefStatus = getPlanningBriefStatus(trip);

  return allStages.map((stage, i) => {
    if (i < currentIdx) return { label: `${stage} ✓`, color: '#3fb950' };
    if (stage === current) {
      if (briefStatus === "missing_required_details") return { label: `${stage} →`, color: '#f85149' };
      if (briefStatus === "missing_recommended_details") return { label: `${stage} →`, color: '#d29922' };
      return { label: `${stage} →`, color: '#58a6ff' };
    }
    return { label: stage, color: '#484f58' };
  });
}

export function getTripFreshnessLabel(trip?: Trip | null): { label: string; tone: string; detail: string } {
  const age = trip?.age?.trim().toLowerCase() || "";
  const isToday = age === "today";
  const isYesterday = age === "yesterday";
  const daysIdle = isToday ? 0 : isYesterday ? 1 : 2;

  const hasRequiredBlockers = getPlanningBriefStatus(trip) === "missing_required_details";
  const isOptionsReady = getPlanningBriefStatus(trip) === "missing_recommended_details" || getPlanningBriefStatus(trip) === "complete";
  const isQuoteReview = trip?.status === "ready_to_quote" || trip?.status === "ready_to_book";

  if (isQuoteReview) return { label: "Waiting on review", tone: "blue", detail: isToday ? "Updated today" : `${daysIdle} day${daysIdle > 1 ? 's' : ''} idle` };
  if (hasRequiredBlockers) {
    if (daysIdle >= 3) return { label: "Delayed", tone: "red", detail: `${daysIdle} days idle` };
    if (daysIdle >= 2) return { label: "Needs action", tone: "amber", detail: `${daysIdle} days idle` };
    return { label: "Waiting on customer", tone: "blue", detail: isToday ? "Updated today" : `${daysIdle} day idle` };
  }
  if (isOptionsReady) {
    if (daysIdle >= 3) return { label: "Delayed", tone: "red", detail: `${daysIdle} days idle` };
    if (daysIdle >= 2) return { label: "Needs action", tone: "amber", detail: `${daysIdle} days idle` };
    return { label: "Options pending", tone: "blue", detail: isToday ? "Updated today" : `${daysIdle} day idle` };
  }

  if (isToday) return { label: "In progress", tone: "neutral", detail: "Updated today" };
  return { label: "In progress", tone: "neutral", detail: `Updated ${trip?.age || "recently"}` };
}

function getPlanningListAction(trip?: Trip | null): { label: string; href: string } {
  const href = getTripRoute(trip?.id, 'intake');

  if (getPlanningBriefStatus(trip) === 'missing_required_details') {
    return { label: 'Open missing details', href };
  }

  if (trip?.status === 'ready_to_quote' || trip?.status === 'ready_to_book') {
    return { label: 'Review quote', href: getTripRoute(trip?.id, 'decision') };
  }

  return { label: 'Open options', href: getTripRoute(trip?.id, 'strategy') };
}

export function getPlanningListSummary(trip: Trip) {
  const requiredFields = getRequiredPlanningFields(trip);
  const missingBadges = requiredFields.map(formatMissingDetailBadge);
  const stage = getPlanningStageLabel(trip);
  const progress = getPlanningStageProgress(trip);

  return {
    title: getPlanningHeaderTitle(trip),
    subtitle: getPlanningIdentityLine(trip),
    statusLabel: getPlanningStatusLabel(trip),
    statusTone: getPlanningStatusTone(trip),
    budgetLabel: formatBudgetDisplay(trip.budget),
    assignmentLabel: getPlanningAssignmentLabel(trip),
    nextAction: getPlanningNextAction(trip),
    recencyLabel: getPlanningRecencyLabel(trip.age),
    inquiryReference: formatInquiryReference(trip.id),
    missingFields: requiredFields,
    missingBadges,
    action: getPlanningListAction(trip),
    stage,
    progress,
  };
}
