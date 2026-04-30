const MONTH_MAP: Record<string, string> = {
  jan: 'Jan',
  january: 'Jan',
  feb: 'Feb',
  february: 'Feb',
  mar: 'Mar',
  march: 'Mar',
  apr: 'Apr',
  april: 'Apr',
  may: 'May',
  jun: 'Jun',
  june: 'Jun',
  jul: 'Jul',
  july: 'Jul',
  aug: 'Aug',
  august: 'Aug',
  sep: 'Sep',
  sept: 'Sep',
  september: 'Sep',
  oct: 'Oct',
  october: 'Oct',
  nov: 'Nov',
  november: 'Nov',
  dec: 'Dec',
  december: 'Dec',
};

function normalizeMonth(value: string): string {
  return MONTH_MAP[value.trim().toLowerCase()] ?? value.trim();
}

function formatSimpleDateRange(value: string): string | null {
  const match = value.match(
    /^(?:dates\s+)?(?:around\s+)?(\d{1,2})(?:st|nd|rd|th)?\s+to\s+(\d{1,2})(?:st|nd|rd|th)?\s+([a-z]+)$/i
  );

  if (!match) return null;

  const [, start, end, month] = match;
  return `Around ${normalizeMonth(month)} ${Number(start)}–${Number(end)}`;
}

export function formatLeadTitle(destination?: string | null, tripType?: string | null): string {
  const cleanDestination = destination?.trim();
  const cleanType = tripType?.trim();

  if (cleanDestination && cleanType) {
    const normalizedType = cleanType.toLowerCase().endsWith('trip')
      ? cleanType.toLowerCase()
      : `${cleanType.toLowerCase()} trip`;
    return `${cleanDestination} ${normalizedType}`;
  }

  return cleanDestination || cleanType || 'Lead review';
}

export function formatInquiryReference(value?: string | null): string {
  if (!value) return '—';
  const normalized = value.replace(/^trip_/i, '').trim();
  const shortId = normalized.slice(0, 4).toUpperCase();
  return shortId || normalized;
}

export function formatBudgetDisplay(value?: string | null): string {
  if (!value) return 'Budget missing';
  const trimmed = value.trim();
  return trimmed === '$0' || trimmed === '0' ? 'Budget missing' : trimmed;
}

export function formatPartySizeDisplay(value?: number | null, fallback = 'Party to confirm'): string {
  if (!value || value <= 0) return fallback;
  return `${value} pax`;
}

export function formatCustomerDisplay(rawInput?: unknown, fallback = 'Customer to confirm'): string {
  const fixtureId =
    typeof rawInput === 'object' &&
    rawInput !== null &&
    'fixture_id' in rawInput &&
    typeof rawInput.fixture_id === 'string'
      ? rawInput.fixture_id.trim()
      : '';
  if (!fixtureId) return fallback;
  return `Customer ${fixtureId}`;
}

export function formatDateWindowDisplay(value?: string | null, fallback = 'Dates to confirm'): string {
  if (!value) return fallback;

  const trimmed = value.replace(/^dates\s+/i, '').trim();
  const formattedRange = formatSimpleDateRange(trimmed);
  if (formattedRange) return formattedRange;

  return trimmed.replace(/\b([a-z]{3,9})\b/gi, (month) => normalizeMonth(month));
}
