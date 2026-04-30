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

export function getPlanningAssignmentLabel(trip?: Trip | null): string {
  if (trip?.status === 'in_progress') return 'In progress';
  return 'Assigned';
}

export function getPlanningListAction(trip?: Trip | null): { label: string; href: string } {
  const href = getTripRoute(trip?.id, 'intake');

  if (getPlanningBriefStatus(trip) === 'missing_required_details') {
    return { label: 'Open missing details', href };
  }

  return { label: 'Continue planning', href };
}

export function getPlanningListSummary(trip: Trip) {
  const requiredFields = getRequiredPlanningFields(trip);
  const missingBadges = requiredFields.map(formatMissingDetailBadge);

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
  };
}
