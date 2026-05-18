import type { Trip } from '@/lib/api-client';
import { formatDateWindowDisplay, formatLeadTitle } from '@/lib/lead-display';
import type { InboxTrip, TripReview } from '@/types/governance';

export type ActionRequiredPriority = 'urgent' | 'high' | 'normal' | 'low';

export type ActionRequiredItem = {
  id: string;
  priority: ActionRequiredPriority;
  source: 'quote' | 'lead' | 'trip';
  title: string;
  subtitle: string;
  meta?: string;
  reason: string;
  href: string;
  ctaLabel: string;
};

export interface BuildActionRequiredItemsInput {
  workspaceTrips: Trip[];
  pendingReviews: TripReview[];
  inboxTrips: InboxTrip[];
}

const DAY_MS = 24 * 60 * 60 * 1000;
const MONTH_INDEX: Record<string, number> = {
  jan: 0,
  january: 0,
  feb: 1,
  february: 1,
  mar: 2,
  march: 2,
  apr: 3,
  april: 3,
  may: 4,
  jun: 5,
  june: 5,
  jul: 6,
  july: 6,
  aug: 7,
  august: 7,
  sep: 8,
  sept: 8,
  september: 8,
  oct: 9,
  october: 9,
  nov: 10,
  november: 10,
  dec: 11,
  december: 11,
};

function compareNullableNumbersAsc(a: number | null, b: number | null): number {
  if (a === null && b === null) return 0;
  if (a === null) return 1;
  if (b === null) return -1;
  return a - b;
}

function parseTimestamp(value?: string | null): number | null {
  if (!value) return null;
  const parsed = Date.parse(value);
  return Number.isNaN(parsed) ? null : parsed;
}

function parseExplicitTravelStart(dateWindow?: string | null): number | null {
  if (!dateWindow) return null;
  const value = dateWindow.trim();

  const monthDayYearMatch = value.match(
    /\b([A-Za-z]{3,9})\s+(\d{1,2})(?:st|nd|rd|th)?(?:\s*(?:-|–|to)\s*\d{1,2}(?:st|nd|rd|th)?)?(?:,)?\s+(\d{4})\b/i
  );
  if (monthDayYearMatch) {
    const month = MONTH_INDEX[monthDayYearMatch[1]!.toLowerCase()];
    const day = Number(monthDayYearMatch[2]);
    const year = Number(monthDayYearMatch[3]);
    if (month !== undefined) return Date.UTC(year, month, day);
  }

  const dayMonthYearMatch = value.match(
    /\b(\d{1,2})(?:st|nd|rd|th)?(?:\s*(?:-|–|to)\s*\d{1,2}(?:st|nd|rd|th)?)?\s+([A-Za-z]{3,9})\s+(\d{4})\b/i
  );
  if (dayMonthYearMatch) {
    const month = MONTH_INDEX[dayMonthYearMatch[2]!.toLowerCase()];
    const day = Number(dayMonthYearMatch[1]);
    const year = Number(dayMonthYearMatch[3]);
    if (month !== undefined) return Date.UTC(year, month, day);
  }

  const monthYearMatch = value.match(/\b([A-Za-z]{3,9})\s+(\d{4})\b/i);
  if (monthYearMatch) {
    const month = MONTH_INDEX[monthYearMatch[1]!.toLowerCase()];
    const year = Number(monthYearMatch[2]);
    if (month !== undefined) return Date.UTC(year, month, 1);
  }

  return null;
}

function tripTitle(trip: Trip): string {
  return trip.overdue ? 'Trip is overdue' : 'Trip needs review';
}

function tripSubtitle(trip: Trip): string {
  return formatLeadTitle(trip.destination, trip.type);
}

function tripMeta(trip: Trip): string | undefined {
  if (!trip.dateWindow?.trim()) return undefined;
  return `Travel ${formatDateWindowDisplay(trip.dateWindow)}`;
}

function tripReason(trip: Trip): string {
  const action = trip.action?.trim();
  if (action) return action;
  if (trip.overdue) return 'This trip is overdue and needs attention in planning.';
  return 'This trip is marked for attention in planning.';
}

function reviewSubtitle(review: TripReview): string {
  return formatLeadTitle(review.destination, review.tripType);
}

function formatCalendarDate(value?: string | null): string | null {
  if (!value) return null;
  const timestamp = Date.parse(value);
  if (Number.isNaN(timestamp)) return null;
  return new Intl.DateTimeFormat('en-GB', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    timeZone: 'UTC',
  }).format(new Date(timestamp));
}

function reviewMeta(review: TripReview): string | undefined {
  const submitted = formatCalendarDate(review.submittedAt);
  return submitted ? `Submitted ${submitted}` : undefined;
}

function reviewReason(review: TripReview): string {
  return review.reason?.trim() || 'Review before sending to the customer.';
}

function enquirySubtitle(enquiry: InboxTrip): string {
  const tripTitle = formatLeadTitle(enquiry.destination, enquiry.tripType);
  const customerName = enquiry.customerName?.trim();
  return customerName ? `${customerName} · ${tripTitle}` : tripTitle;
}

function enquiryMeta(enquiry: InboxTrip): string | undefined {
  const submitted = formatCalendarDate(enquiry.submittedAt);
  return submitted ? `Received ${submitted}` : undefined;
}

function enquiryReason(enquiry: InboxTrip): string {
  if (enquiry.slaStatus === 'breached') return 'This enquiry is overdue for qualification.';
  if (enquiry.slaStatus === 'at_risk') return 'This enquiry is nearing its SLA and needs action.';
  if (!enquiry.assignedTo) return 'Needs qualification or assignment.';
  return 'Needs follow-up in the enquiry queue.';
}

function getTripRank(trip: Trip, referenceNow: number): number {
  let rank = trip.overdue ? 100 : 80;
  const travelStart = parseExplicitTravelStart(trip.dateWindow);
  if (travelStart !== null) {
    const daysUntil = Math.floor((travelStart - referenceNow) / DAY_MS);
    if (daysUntil <= 7) rank += 40;
    else if (daysUntil <= 14) rank += 25;
    else if (daysUntil <= 30) rank += 10;
  }
  return rank;
}

function getEnquiryRank(enquiry: InboxTrip): number {
  let rank = 50;
  if (enquiry.slaStatus === 'breached') rank += 30;
  else if (enquiry.slaStatus === 'at_risk') rank += 15;
  return rank;
}

type RankedItem = ActionRequiredItem & {
  rank: number;
  sortTimestamp: number | null;
};

export function buildActionRequiredItems({
  workspaceTrips,
  pendingReviews,
  inboxTrips,
}: BuildActionRequiredItemsInput): ActionRequiredItem[] {
  const referenceNow = Date.now();
  const rankedItems: RankedItem[] = [];

  const tripAttentionCandidates = workspaceTrips
    .filter((trip) => trip.overdue === true || trip.state === 'red')
    .sort((a, b) => {
      if (a.overdue !== b.overdue) return a.overdue ? -1 : 1;
      const dateCompare = compareNullableNumbersAsc(
        parseExplicitTravelStart(a.dateWindow),
        parseExplicitTravelStart(b.dateWindow),
      );
      if (dateCompare !== 0) return dateCompare;
      return compareNullableNumbersAsc(parseTimestamp(a.updatedAt), parseTimestamp(b.updatedAt));
    });

  for (const trip of tripAttentionCandidates) {
    rankedItems.push({
      id: `trip-${trip.id}`,
      priority: 'high',
      source: 'trip',
      title: tripTitle(trip),
      subtitle: tripSubtitle(trip),
      meta: tripMeta(trip),
      reason: tripReason(trip),
      href: `/trips/${trip.id}`,
      ctaLabel: 'Open trip',
      rank: getTripRank(trip, referenceNow),
      sortTimestamp: parseExplicitTravelStart(trip.dateWindow),
    });
  }

  const sortedReviews = [...pendingReviews].sort((a, b) =>
    compareNullableNumbersAsc(parseTimestamp(a.submittedAt), parseTimestamp(b.submittedAt))
  );
  for (const review of sortedReviews) {
    rankedItems.push({
      id: `quote-${review.id}`,
      priority: 'high',
      source: 'quote',
      title: 'Quote needs review',
      subtitle: reviewSubtitle(review),
      meta: reviewMeta(review),
      reason: reviewReason(review),
      href: '/reviews',
      ctaLabel: 'Review quote',
      rank: 70,
      sortTimestamp: parseTimestamp(review.submittedAt),
    });
  }

  const sortedEnquiries = [...inboxTrips].sort((a, b) => {
    const scoreDiff = getEnquiryRank(b) - getEnquiryRank(a);
    if (scoreDiff !== 0) return scoreDiff;
    return compareNullableNumbersAsc(parseTimestamp(a.submittedAt), parseTimestamp(b.submittedAt));
  });
  for (const enquiry of sortedEnquiries) {
    rankedItems.push({
      id: `lead-${enquiry.id}`,
      priority: enquiry.slaStatus === 'breached' ? 'high' : 'normal',
      source: 'lead',
      title: 'New enquiry waiting',
      subtitle: enquirySubtitle(enquiry),
      meta: enquiryMeta(enquiry),
      reason: enquiryReason(enquiry),
      href: '/inbox',
      ctaLabel: 'Open enquiry',
      rank: getEnquiryRank(enquiry),
      sortTimestamp: parseTimestamp(enquiry.submittedAt),
    });
  }

  return rankedItems
    .sort((a, b) => {
      if (b.rank !== a.rank) return b.rank - a.rank;
      return compareNullableNumbersAsc(a.sortTimestamp, b.sortTimestamp);
    })
    .slice(0, 5)
    .map(({ rank: _rank, sortTimestamp: _sortTimestamp, ...item }) => item);
}
