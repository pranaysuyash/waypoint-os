import type { Trip } from '@/lib/api-client';
import type { TripReview } from '@/types/governance';

export type ActionRequiredPriority = 'urgent' | 'high' | 'normal' | 'low';

export type ActionRequiredItem = {
  id: string;
  priority: ActionRequiredPriority;
  source: 'quote' | 'lead' | 'trip' | 'system';
  title: string;
  subtitle: string;
  reason: string;
  href: string;
  ctaLabel: string;
};

export interface BuildActionRequiredItemsInput {
  workspaceTrips: Trip[];
  pendingReviews: TripReview[];
  pendingReviewTotal: number;
  inboxTotal: number;
  integrityIssuesTotal: number;
}

function pluralize(count: number, singular: string, plural: string): string {
  return `${count} ${count === 1 ? singular : plural}`;
}

function tripSubtitle(trip: Trip): string {
  const destination = trip.destination?.trim();
  const type = trip.type?.trim();
  if (destination && type) return `${destination} ${type} trip`;
  return destination || type || 'Trip in planning';
}

export function buildActionRequiredItems({
  workspaceTrips,
  pendingReviews,
  pendingReviewTotal,
  inboxTotal,
  integrityIssuesTotal,
}: BuildActionRequiredItemsInput): ActionRequiredItem[] {
  const items: ActionRequiredItem[] = [];
  // v1 ranking is intentionally source-order based:
  // quotes -> trips -> enquiries -> agency health.

  if (pendingReviewTotal > 0) {
    items.push({
      id: 'quote-review',
      priority: pendingReviewTotal > 1 ? 'urgent' : 'high',
      source: 'quote',
      title: pendingReviewTotal > 1 ? 'Quotes need review' : 'Quote needs review',
      subtitle: pendingReviews[0]?.destination?.trim() || 'Quotes to review',
      reason: `${pluralize(pendingReviewTotal, 'quote is', 'quotes are')} waiting for approval before sending.`,
      href: '/reviews',
      ctaLabel: 'Review quotes',
    });
  }

  const tripAttentionCandidates = workspaceTrips.filter(
    (trip) => trip.overdue === true || trip.state === 'red'
  );

  for (const trip of tripAttentionCandidates) {
    const isOverdue = trip.overdue === true;
    items.push({
      id: `trip-${trip.id}`,
      priority: 'high',
      source: 'trip',
      title: 'Trip needs review',
      subtitle: tripSubtitle(trip),
      reason: isOverdue
        ? 'This trip is overdue and needs attention in planning.'
        : 'This trip is marked for attention in planning.',
      href: `/trips/${trip.id}`,
      ctaLabel: 'Open trip',
    });
  }

  if (inboxTotal > 0) {
    items.push({
      id: 'lead-inbox',
      priority: inboxTotal > 3 ? 'high' : 'normal',
      source: 'lead',
      title: 'New enquiries waiting',
      subtitle: 'Lead inbox',
      reason: `${pluralize(inboxTotal, 'new enquiry needs', 'new enquiries need')} qualification or assignment.`,
      href: '/inbox',
      ctaLabel: 'Open enquiries',
    });
  }

  if (integrityIssuesTotal > 0) {
    items.push({
      id: 'agency-health',
      priority: 'low',
      source: 'system',
      title: 'Agency health check',
      subtitle: 'System check',
      reason: `${pluralize(integrityIssuesTotal, 'item needs', 'items need')} review.`,
      href: '/overview?panel=system-check',
      ctaLabel: 'Check status',
    });
  }

  return items.slice(0, 5);
}
