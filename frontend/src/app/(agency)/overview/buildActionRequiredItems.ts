import type { Trip } from '@/lib/api-client';
import { formatDateWindowDisplay, formatLeadTitle } from '@/lib/lead-display';
import { getTripRoute } from '@/lib/routes';
import type { InboxTrip, RiskFlag, TripReview } from '@/types/governance';

export type ActionRequiredPriority = 'urgent' | 'high' | 'normal' | 'low';

export type ActionRequiredItem = {
  id: string;
  priority: ActionRequiredPriority;
  source: 'quote' | 'lead' | 'trip';
  label: 'Quote' | 'Enquiry' | 'Trip';
  variant?: 'record' | 'group';
  title: string;
  subtitle: string;
  meta?: string;
  reason: string;
  reference?: string;
  href: string;
  ctaLabel: string;
  secondaryHref?: string;
  secondaryCtaLabel?: string;
  itemCount?: number;
  examples?: ActionRequiredExample[];
  hidePriorityBadge?: boolean;
  criticalityLabel?: string;
  pendingActions?: string[];
  nextAction?: string;
};

export type ActionRequiredExample = {
  id: string;
  title: string;
  detail: string;
  href: string;
};

export interface BuildActionRequiredItemsInput {
  workspaceTrips: Trip[];
  pendingReviews: TripReview[];
  inboxTrips: InboxTrip[];
  inboxTotal?: number;
  inboxStats?: OverviewInboxStats;
}

export type OverviewInboxStats = {
  total: number;
  unassigned: number;
  critical: number;
  atRisk: number;
  breached?: number;
  incomplete?: number;
  missingCustomer?: number;
  missingTripBasics?: number;
  oldestWaitingDays?: number | null;
  oldestUnassignedWaitingDays?: number | null;
  statsCoverage?: number;
};

const DAY_MS = 24 * 60 * 60 * 1000;
const OLD_ENQUIRY_DAYS = 7;
const OLD_QUOTE_DAYS = 3;
const NEAR_TRAVEL_DAYS = 14;

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

function daysSince(value: string | undefined | null, referenceNow: number): number | null {
  const timestamp = parseTimestamp(value);
  if (timestamp === null) return null;
  return Math.max(0, Math.floor((referenceNow - timestamp) / DAY_MS));
}

function daysUntil(value: string | undefined | null, referenceNow: number): number | null {
  const timestamp = parseExplicitTravelStart(value);
  if (timestamp === null) return null;
  return Math.floor((timestamp - referenceNow) / DAY_MS);
}

function formatShortCalendarDate(value?: string | null): string | null {
  if (!value) return null;
  const timestamp = Date.parse(value);
  if (Number.isNaN(timestamp)) return null;
  return new Intl.DateTimeFormat('en-GB', {
    day: 'numeric',
    month: 'short',
    timeZone: 'UTC',
  }).format(new Date(timestamp));
}

function formatWaitingAge(days: number | null): string | null {
  if (days === null) return null;
  if (days === 0) return 'today';
  if (days === 1) return '1d waiting';
  return `${days}d waiting`;
}

function formatStatsWaitingAge(days?: number | null): string | null {
  return typeof days === 'number' ? formatWaitingAge(days) : null;
}

function compactTiming(prefix: 'Received' | 'Submitted', value: string | undefined | null, referenceNow: number): string | undefined {
  const date = formatShortCalendarDate(value);
  const waiting = formatWaitingAge(daysSince(value, referenceNow));
  if (date && waiting) return `${prefix} ${date} · ${waiting}`;
  if (date) return `${prefix} ${date}`;
  return waiting ?? undefined;
}

function displayTripKind(kind?: string | null, fallback = 'Trip'): string {
  const cleaned = kind?.trim();
  if (!cleaned) return fallback;
  return cleaned.toLowerCase().endsWith('trip') ? cleaned.slice(0, -4).trim() || fallback : cleaned;
}

function enquiryTitle(enquiry: InboxTrip): string {
  const cleanDestination = enquiry.destination?.trim();
  const destinationKnown = cleanDestination && !['tbd', 'to confirm', 'unknown', 'not set', 'n/a', '-'].includes(cleanDestination.toLowerCase());
  const kind = displayTripKind(enquiry.tripType, 'Leisure');

  if (destinationKnown) return `${cleanDestination} ${kind.toLowerCase()} enquiry`;
  return `${kind.charAt(0).toUpperCase()}${kind.slice(1).toLowerCase()} enquiry`;
}

function quoteTitle(review: TripReview): string {
  const base = formatLeadTitle(review.destination, review.tripType);
  if (base === 'Trip details incomplete') return 'Quote review';
  return `${base.replace(/\s+trip$/i, '')} quote`;
}

function tripTitle(trip: Trip): string {
  return formatLeadTitle(trip.destination, trip.type);
}

function isInternalLookingName(value?: string | null): boolean {
  const name = value?.trim();
  if (!name) return true;
  return (
    /^test[_-]?fixture[_-]/i.test(name) ||
    /^sc-\d+/i.test(name) ||
    /^client\s+[a-f0-9]{4,}$/i.test(name) ||
    /^(test|fixture|sample|demo)[_-]/i.test(name) ||
    /^[a-f0-9]{8,}$/i.test(name)
  );
}

function formatReference(value?: string | null): string | undefined {
  const reference = value?.trim();
  if (!reference) return undefined;
  return `Ref ${reference}`;
}

function formatPax(value?: number | null): string {
  return value && value > 0 ? `${value} pax` : 'Party to confirm';
}

function formatTravel(value?: string | null): string {
  return `Travel ${formatDateWindowDisplay(value, 'TBD')}`;
}

function hasKnownValue(value?: string | null): boolean {
  const cleaned = value?.trim();
  if (!cleaned) return false;
  return !['tbd', 'to confirm', 'unknown', 'not set', 'n/a', '-'].includes(cleaned.toLowerCase());
}

function addUnique(target: string[], value: string): void {
  if (!target.includes(value)) target.push(value);
}

function enquiryPendingActions(enquiry: InboxTrip, referenceNow: number): string[] {
  const actions = ['Qualify'];
  const waiting = formatWaitingAge(daysSince(enquiry.submittedAt, referenceNow));
  if (!enquiry.assignedTo) actions.push(waiting ? `Assign owner (${waiting})` : 'Assign owner');
  if (isInternalLookingName(enquiry.customerName)) actions.push('Identify customer');
  if (!hasKnownValue(enquiry.destination) || !hasKnownValue(enquiry.dateWindow)) {
    actions.push('Confirm basics');
  }
  return actions;
}

function enquiryCriticality(enquiry: InboxTrip, referenceNow: number): string {
  const waiting = formatWaitingAge(daysSince(enquiry.submittedAt, referenceNow));
  if (enquiry.slaStatus === 'breached') return joinParts(['Breached SLA', waiting]);
  if (enquiry.slaStatus === 'at_risk') return joinParts(['Approaching SLA limit', waiting]);
  return joinParts(['Waiting for qualification', waiting]);
}

function enquiryNextAction(enquiry: InboxTrip): string {
  if (!enquiry.assignedTo) return 'Open oldest, assign, qualify.';
  return 'Qualify and save usable details.';
}

function reviewPendingActions(review: TripReview): string[] {
  const actions = ['Review quote'];
  if ((review.riskFlags ?? []).includes('tight_deadline')) actions.push('Check deadline');
  if ((review.riskFlags ?? []).includes('high_value')) actions.push('Confirm approval');
  if ((review.riskFlags ?? []).includes('complex_itinerary')) actions.push('Check itinerary risk');
  return actions;
}

function reviewCriticality(review: TripReview, referenceNow: number): string {
  const waiting = formatWaitingAge(daysSince(review.submittedAt, referenceNow));
  if (review.feedbackSeverity === 'critical') return joinParts(['Critical feedback', waiting]);
  if (review.feedbackSeverity === 'high') return joinParts(['High-risk feedback', waiting]);
  if ((review.riskFlags ?? []).length) return joinParts(['Risk flags present', waiting]);
  return joinParts(['Awaiting approval', waiting]);
}

function tripPendingActions(trip: Trip): string[] {
  const actions: string[] = [];
  if (trip.action?.trim()) actions.push(trip.action.trim());
  if (trip.overdue) addUnique(actions, 'Clear overdue planning');
  if (trip.state === 'red') addUnique(actions, 'Resolve red status');
  if (!hasKnownValue(trip.dateWindow)) addUnique(actions, 'Confirm travel window');
  if (!hasKnownValue(trip.destination)) addUnique(actions, 'Confirm destination');
  if (!actions.length) actions.push('Review trip');
  return actions.slice(0, 4);
}

function tripCriticality(trip: Trip, referenceNow: number): string {
  const travelDays = daysUntil(trip.dateWindow, referenceNow);
  const parts = [trip.overdue ? 'Planning overdue' : trip.state === 'red' ? 'Red status' : 'Needs attention'];
  if (travelDays !== null) {
    parts.push(travelDays < 0 ? 'travel date passed' : `${travelDays}d to travel`);
  }
  return joinParts(parts);
}

function joinParts(parts: Array<string | undefined | null | false>): string {
  return parts.filter((part): part is string => Boolean(part)).join(' · ');
}

function tripSubtitle(trip: Trip): string {
  return joinParts([formatTravel(trip.dateWindow), trip.state === 'red' ? 'Red status' : undefined]);
}

function tripReason(trip: Trip): string {
  const action = trip.action?.trim();
  if (action) return action;
  if (trip.overdue) return 'Planning overdue';
  return 'Needs planning attention';
}

function reviewSubtitle(review: TripReview): string {
  return joinParts([formatPax(review.partySize), formatTravel(review.dateWindow), review.agentName ? `Owner ${review.agentName}` : undefined]);
}

function reviewReason(review: TripReview): string {
  if (review.feedbackSeverity === 'critical') return 'Critical quote review';
  if (review.feedbackSeverity === 'high') return 'High-risk quote review';
  if ((review.riskFlags ?? []).includes('tight_deadline')) return 'Tight deadline before sending';
  if ((review.riskFlags ?? []).includes('high_value')) return 'High-value quote needs approval';
  return review.reason?.trim() || 'Quote approval needed';
}

function slugIdPart(value: unknown): string {
  const normalized = String(value ?? '').trim().toLowerCase();
  if (!normalized) return '';
  return normalized
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '');
}

function buildStableId(prefix: string, parts: Array<unknown>, fallback: string): string {
  const slugParts = parts.map(slugIdPart).filter(Boolean);
  return `${prefix}-${slugParts.join('-') || fallback}`;
}

function buildExampleId(groupKey: string, index: number, example: RankedItem): string {
  return buildStableId(
    'example',
    [groupKey, index, example.id, example.title, example.subtitle, example.reference, example.meta],
    `item-${index + 1}`,
  );
}

function enquirySubtitle(enquiry: InboxTrip): string {
  const customer = isInternalLookingName(enquiry.customerName) ? 'Unnamed customer' : enquiry.customerName.trim();
  return joinParts([customer, formatPax(enquiry.partySize), formatTravel(enquiry.dateWindow), enquiry.assignedTo ? undefined : 'Not assigned']);
}

function enquiryReason(enquiry: InboxTrip): string {
  if (enquiry.slaStatus === 'breached') return 'Qualification overdue';
  if (enquiry.slaStatus === 'at_risk') return 'Qualification due soon';
  if (!enquiry.assignedTo) return 'Needs qualification or assignment';
  return 'Needs enquiry follow-up';
}

function isSevereReview(review: TripReview): boolean {
  const severeFeedback = review.feedbackSeverity === 'critical' || review.feedbackSeverity === 'high';
  const severeRisk: RiskFlag[] = ['high_value', 'tight_deadline', 'complex_itinerary'];
  return severeFeedback || (review.riskFlags ?? []).some((flag) => severeRisk.includes(flag));
}

function getTripRank(trip: Trip, referenceNow: number): number {
  let rank = trip.overdue ? 120 : 90;
  const travelDays = daysUntil(trip.dateWindow, referenceNow);
  if (travelDays !== null) {
    if (travelDays <= 7) rank += 40;
    else if (travelDays <= NEAR_TRAVEL_DAYS) rank += 25;
    else if (travelDays <= 30) rank += 10;
  }
  return rank;
}

function getReviewRank(review: TripReview, referenceNow: number): number {
  const waitingDays = daysSince(review.submittedAt, referenceNow) ?? 0;
  return 70 + Math.min(waitingDays, 30) + (isSevereReview(review) ? 20 : 0);
}

function getEnquiryRank(enquiry: InboxTrip, referenceNow: number): number {
  const waitingDays = daysSince(enquiry.submittedAt, referenceNow) ?? 0;
  let rank = 45 + Math.min(waitingDays, 30);
  if (enquiry.slaStatus === 'breached') rank += 35;
  else if (enquiry.slaStatus === 'at_risk') rank += 20;
  return rank;
}

function tripPriority(trip: Trip, referenceNow: number): ActionRequiredPriority {
  const travelDays = daysUntil(trip.dateWindow, referenceNow);
  if (trip.overdue && (travelDays === null || travelDays <= NEAR_TRAVEL_DAYS)) return 'urgent';
  return 'high';
}

function reviewPriority(review: TripReview, referenceNow: number): ActionRequiredPriority {
  const waitingDays = daysSince(review.submittedAt, referenceNow) ?? 0;
  if (isSevereReview(review) || waitingDays >= OLD_QUOTE_DAYS) return 'high';
  return 'normal';
}

function enquiryPriority(enquiry: InboxTrip, referenceNow: number): ActionRequiredPriority {
  const waitingDays = daysSince(enquiry.submittedAt, referenceNow) ?? 0;
  if (enquiry.slaStatus === 'breached' && waitingDays >= OLD_ENQUIRY_DAYS) return 'urgent';
  if (enquiry.slaStatus === 'breached' || enquiry.slaStatus === 'at_risk') return 'high';
  return 'normal';
}

type RankedItem = ActionRequiredItem & {
  rank: number;
  sortTimestamp: number | null;
  groupKey: string;
};

export function buildActionRequiredItems({
  workspaceTrips,
  pendingReviews,
  inboxTrips,
  inboxTotal,
  inboxStats,
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
      priority: tripPriority(trip, referenceNow),
      source: 'trip',
      label: 'Trip',
      title: tripTitle(trip),
      subtitle: tripSubtitle(trip),
      meta: trip.overdue ? 'Planning overdue' : 'Red status',
      reason: tripReason(trip),
      href: getTripRoute(trip.id, 'intake'),
      ctaLabel: 'Open trip',
      criticalityLabel: tripCriticality(trip, referenceNow),
      pendingActions: tripPendingActions(trip),
      nextAction: 'Open trip, clear blocker.',
      rank: getTripRank(trip, referenceNow),
      sortTimestamp: parseExplicitTravelStart(trip.dateWindow),
      groupKey: `trip:${tripReason(trip)}:${tripPriority(trip, referenceNow)}`,
    });
  }

  const sortedReviews = [...pendingReviews].sort((a, b) => {
    const severeDiff = Number(isSevereReview(b)) - Number(isSevereReview(a));
    if (severeDiff !== 0) return severeDiff;
    return compareNullableNumbersAsc(parseTimestamp(a.submittedAt), parseTimestamp(b.submittedAt));
  });
  for (const review of sortedReviews) {
    const stableId = buildStableId('quote', [
      review.id,
      review.tripReference,
      review.tripId,
      review.submittedAt,
      review.reason,
    ], `review-${rankedItems.length + 1}`);

    rankedItems.push({
      id: stableId,
      priority: reviewPriority(review, referenceNow),
      source: 'quote',
      label: 'Quote',
      title: quoteTitle(review),
      subtitle: reviewSubtitle(review),
      meta: compactTiming('Submitted', review.submittedAt, referenceNow),
      reason: reviewReason(review),
      reference: formatReference(review.tripReference),
      href: '/reviews',
      ctaLabel: 'Review quote',
      criticalityLabel: reviewCriticality(review, referenceNow),
      pendingActions: reviewPendingActions(review),
      nextAction: 'Review risk, approve or return.',
      rank: getReviewRank(review, referenceNow),
      sortTimestamp: parseTimestamp(review.submittedAt),
      groupKey: `quote:${reviewReason(review)}:${reviewPriority(review, referenceNow)}`,
    });
  }

  const sortedEnquiries = [...inboxTrips].sort((a, b) => {
    const scoreDiff = getEnquiryRank(b, referenceNow) - getEnquiryRank(a, referenceNow);
    if (scoreDiff !== 0) return scoreDiff;
    return compareNullableNumbersAsc(parseTimestamp(a.submittedAt), parseTimestamp(b.submittedAt));
  });
  for (const enquiry of sortedEnquiries) {
    rankedItems.push({
      id: `lead-${enquiry.id}`,
      priority: enquiryPriority(enquiry, referenceNow),
      source: 'lead',
      label: 'Enquiry',
      title: enquiryTitle(enquiry),
      subtitle: enquirySubtitle(enquiry),
      meta: compactTiming('Received', enquiry.submittedAt, referenceNow),
      reason: enquiryReason(enquiry),
      reference: isInternalLookingName(enquiry.customerName) ? formatReference(enquiry.reference) : undefined,
      href: '/inbox',
      ctaLabel: 'Open enquiry',
      criticalityLabel: enquiryCriticality(enquiry, referenceNow),
      pendingActions: enquiryPendingActions(enquiry, referenceNow),
      nextAction: enquiryNextAction(enquiry),
      rank: getEnquiryRank(enquiry, referenceNow),
      sortTimestamp: parseTimestamp(enquiry.submittedAt),
      groupKey: `lead:${enquiryReason(enquiry)}:${enquiryPriority(enquiry, referenceNow)}`,
    });
  }

  const ranked = rankedItems
    .sort((a, b) => {
      if (b.rank !== a.rank) return b.rank - a.rank;
      return compareNullableNumbersAsc(a.sortTimestamp, b.sortTimestamp);
    });

  return collapseRepeatedWork(ranked, {
    inboxTotal,
    inboxStats,
    maxGroups: 5,
    maxExamples: 2,
  });
}

function collapseRepeatedWork(
  rankedItems: RankedItem[],
  {
    inboxTotal,
    inboxStats,
    maxGroups,
    maxExamples,
  }: {
    inboxTotal?: number;
    inboxStats?: OverviewInboxStats;
    maxGroups: number;
    maxExamples: number;
  }
): ActionRequiredItem[] {
  const groups = new Map<string, RankedItem[]>();
  const orderedGroupKeys: string[] = [];

  for (const item of rankedItems) {
    if (!groups.has(item.groupKey)) {
      groups.set(item.groupKey, []);
      orderedGroupKeys.push(item.groupKey);
    }
    groups.get(item.groupKey)!.push(item);
  }

  return orderedGroupKeys.slice(0, maxGroups).map((key) => {
    const groupItems = groups.get(key)!;
    if (groupItems.length === 1) {
      const [{ rank: _rank, sortTimestamp: _sortTimestamp, groupKey: _groupKey, ...item }] = groupItems;
      return item;
    }

    const [first] = groupItems;
    const visibleCount = first.source === 'lead' ? Math.max(inboxStats?.total ?? inboxTotal ?? 0, groupItems.length) : groupItems.length;
    const oldestWaiting = first.source === 'lead'
      ? formatStatsWaitingAge(inboxStats?.oldestWaitingDays) ?? extractWaitingLabel(first.meta)
      : null;
    const oldestUnassignedWaiting = first.source === 'lead'
      ? formatStatsWaitingAge(inboxStats?.oldestUnassignedWaitingDays)
      : null;
    const pendingActions = first.source === 'lead' && inboxStats
      ? summarizeLeadStatsPendingActions(inboxStats, groupItems)
      : summarizePendingActions(groupItems);
    const examples: ActionRequiredExample[] = [];
    const seenExampleKeys = new Set<string>();
    for (const item of groupItems) {
      if (examples.length >= maxExamples) break;
      const waitingLabel = extractWaitingLabel(item.meta);
      const example = {
        title: first.source === 'lead' ? waitingLabel ?? item.title : item.title,
        detail: joinParts([
          first.source === 'lead' ? null : item.title,
          item.subtitle,
          first.source === 'lead' ? null : waitingLabel,
          item.reference,
        ]),
        href: item.href,
      };
      const exampleKey = `${example.title}::${example.detail}::${example.href}`;
      if (seenExampleKeys.has(exampleKey)) continue;
      seenExampleKeys.add(exampleKey);
      examples.push({
        id: buildExampleId(key, examples.length, item),
        ...example,
      });
    }

    const title =
      first.source === 'lead'
        ? first.reason === 'Qualification overdue'
          ? 'Overdue enquiries'
          : 'Enquiries needing review'
        : first.source === 'quote'
          ? 'Quotes to review'
          : 'Trips needing review';

    const subtitle =
      first.source === 'lead'
        ? joinParts([
            `${visibleCount.toLocaleString('en-IN')} ${visibleCount === 1 ? 'enquiry needs' : 'enquiries need'} qualification`,
            oldestWaiting ? `oldest ${oldestWaiting}` : null,
          ])
        : `${visibleCount.toLocaleString('en-IN')} ${first.label.toLowerCase()} ${visibleCount === 1 ? 'needs' : 'items need'} attention`;

    const { rank: _rank, sortTimestamp: _sortTimestamp, groupKey: _groupKey, ...baseItem } = first;

    return {
      ...baseItem,
      id: `group-${key}`,
      variant: 'group',
      title,
      subtitle: first.source === 'lead' && inboxStats ? summarizeLeadStatsSubtitle(inboxStats, visibleCount, oldestWaiting) : subtitle,
      meta: oldestWaiting ?? first.meta,
      reference: undefined,
      reason: first.reason,
      ctaLabel: first.source === 'lead' ? 'Open oldest enquiry' : first.ctaLabel,
      secondaryHref: first.source === 'lead' ? '/inbox' : undefined,
      secondaryCtaLabel: first.source === 'lead' ? 'Open all enquiries' : undefined,
      itemCount: visibleCount,
      examples,
      hidePriorityBadge: true,
      criticalityLabel: summarizeCriticality(first, groupItems, oldestWaiting, oldestUnassignedWaiting, inboxStats),
      pendingActions,
      nextAction: summarizeNextAction(first),
    };
  });
}

function extractWaitingLabel(value?: string): string | null {
  if (!value) return null;
  const match = value.match(/(\d+d waiting|today)$/);
  return match?.[1] ?? null;
}

function summarizePendingActions(items: RankedItem[]): string[] {
  const actions: string[] = [];
  for (const item of items) {
    for (const action of item.pendingActions ?? []) {
      addUnique(actions, action);
    }
  }
  return actions.slice(0, 4);
}

function summarizeLeadStatsSubtitle(stats: OverviewInboxStats, visibleCount: number, oldestWaiting: string | null): string {
  return joinParts([
    `${visibleCount.toLocaleString('en-IN')} ${visibleCount === 1 ? 'enquiry' : 'enquiries'} in queue`,
    stats.unassigned > 0 ? `${stats.unassigned.toLocaleString('en-IN')} unassigned` : null,
    oldestWaiting ? `oldest ${oldestWaiting}` : null,
  ]);
}

function summarizeLeadStatsPendingActions(stats: OverviewInboxStats, fallbackItems: RankedItem[]): string[] {
  const actions: string[] = ['Qualify'];
  const oldestUnassigned = formatStatsWaitingAge(stats.oldestUnassignedWaitingDays);
  if (stats.unassigned > 0) {
    actions.push(oldestUnassigned ? `Assign ${stats.unassigned.toLocaleString('en-IN')} unowned (${oldestUnassigned})` : `Assign ${stats.unassigned.toLocaleString('en-IN')} unowned`);
  }
  if ((stats.missingCustomer ?? 0) > 0) {
    actions.push(`Identify ${stats.missingCustomer!.toLocaleString('en-IN')} customers`);
  }
  if ((stats.missingTripBasics ?? 0) > 0) {
    actions.push(`Complete ${stats.missingTripBasics!.toLocaleString('en-IN')} basics`);
  }
  return actions.length > 1 ? actions.slice(0, 4) : summarizePendingActions(fallbackItems);
}

function summarizeCriticality(
  first: RankedItem,
  items: RankedItem[],
  oldestWaiting: string | null,
  oldestUnassignedWaiting: string | null,
  inboxStats?: OverviewInboxStats,
): string {
  if (first.source === 'lead') {
    const hasUnassigned = items.some((item) => item.subtitle.includes('Not assigned'));
    const assignmentRisk =
      (inboxStats?.unassigned ?? 0) > 0 && oldestUnassignedWaiting
        ? `unassigned oldest ${oldestUnassignedWaiting}`
        : hasUnassigned && oldestWaiting
          ? `unassigned oldest ${oldestWaiting}`
          : null;
    return joinParts([
      first.reason === 'Qualification overdue' ? 'Breached SLA' : 'Qualification queue',
      inboxStats?.breached ? `${inboxStats.breached.toLocaleString('en-IN')} breached` : null,
      assignmentRisk,
    ]);
  }
  if (first.source === 'quote') return 'Multiple quotes need approval';
  return 'Multiple trips have planning blockers';
}

function summarizeNextAction(first: RankedItem): string {
  if (first.source === 'lead') {
    return 'Open oldest, clear basics, continue by age.';
  }
  if (first.source === 'quote') {
    return 'Review riskiest quote first.';
  }
  return 'Open highest-risk trip first.';
}
