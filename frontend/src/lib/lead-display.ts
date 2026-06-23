import { formatMoney, formatMoneyCompact, parseBudgetString } from "@/lib/currency";

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
  const destinationKnown = cleanDestination && !['tbd', 'to confirm', 'unknown', 'not set', 'n/a', '-', '-'].includes(cleanDestination.toLowerCase());

  if (destinationKnown && cleanType) {
    const normalizedType = cleanType.toLowerCase().endsWith('trip')
      ? cleanType.toLowerCase()
      : `${cleanType.toLowerCase()} trip`;
    return `${cleanDestination} ${normalizedType}`;
  }

  if (destinationKnown) {
    return cleanDestination;
  }

  if (cleanType) {
    return cleanType;
  }

  return 'Trip details incomplete';
}

export function formatInquiryReference(value?: string | null): string {
  if (!value) return '-';
  const normalized = value.replace(/^trip_/i, '').trim();
  const shortId = normalized.slice(0, 4).toUpperCase();
  return shortId || normalized;
}

export function formatBudgetDisplay(value?: string | null): string {
  if (!value) return 'Budget missing';
  const trimmed = value.trim();
  if (trimmed === '$0' || trimmed === '0' || trimmed === '₹0' || trimmed === '€0' || trimmed === '£0') return 'Budget missing';
  if (/^\D*0(\.0+)?\D*$/.test(trimmed)) return 'Budget missing';

  const rangeMatch = trimmed.match(
    /^(?:budget\s*[:\-]?\s*)?(?:(?<currency>USD|INR|EUR|GBP|AED|NGN|ZAR|SGD|THB|AUD|CAD|JPY|KES|GHS|R|\$|₹|€|£|₦)\s*)?(?<low>\d[\d,]*(?:\.\d+)?)\s*(?<lowUnit>L|K|M|MN|MILLION|MILLIONS|LAC|LAKH|LAKHS|CRORE|CRORES|CR|BN|B|BILLION|BILLIONS|THOUSAND)?\s*(?:-|–|—|\bto\b)\s*(?<high>\d[\d,]*(?:\.\d+)?)(?<highUnit>L|K|M|MN|MILLION|MILLIONS|LAC|LAKH|LAKHS|CRORE|CRORES|CR|BN|B|BILLION|BILLIONS|THOUSAND)?$/i
  );
  if (rangeMatch?.groups) {
    const unit = (rangeMatch.groups.lowUnit ?? rangeMatch.groups.highUnit ?? '').toLowerCase();
    const currencyToken = rangeMatch.groups.currency;
    const low = Number(rangeMatch.groups.low.replace(/,/g, ''));
    const high = Number(rangeMatch.groups.high.replace(/,/g, ''));
    if (!Number.isNaN(low) && !Number.isNaN(high)) {
      const currency = (() => {
        const token = (currencyToken ?? '').trim().toUpperCase();
        switch (token) {
          case 'USD':
          case '$':
            return 'USD';
          case 'EUR':
          case '€':
            return 'EUR';
          case 'GBP':
          case '£':
            return 'GBP';
          case 'AED':
            return 'AED';
          case 'NGN':
          case '₦':
            return 'NGN';
          case 'ZAR':
          case 'R':
            return 'ZAR';
          case 'SGD':
            return 'SGD';
          case 'THB':
            return 'THB';
          case 'AUD':
            return 'AUD';
          case 'CAD':
            return 'CAD';
          case 'JPY':
            return 'JPY';
          case 'INR':
          case '₹':
          default:
            return 'INR';
        }
      })();
      const scale = unit === 'l' || unit === 'lac' || unit === 'lakh' || unit === 'lakhs'
        ? 100000
        : unit === 'k' || unit === 'thousand'
          ? 1000
          : unit === 'm' || unit === 'mn' || unit === 'million' || unit === 'millions'
            ? 1000000
            : unit === 'cr' || unit === 'crore' || unit === 'crores'
              ? 10000000
              : unit === 'b' || unit === 'bn' || unit === 'billion' || unit === 'billions'
                ? 1000000000
                : 1;
      const formatAmount = (amount: number) => (
        currency === 'INR' && amount >= 100000
          ? formatMoneyCompact(amount, currency)
          : formatMoney(amount, currency)
      );
      return `${formatAmount(low * scale)} - ${formatAmount(high * scale)}`;
    }
  }

  const parsed = parseBudgetString(trimmed);
  if (parsed && parsed.amount > 0) {
    if (parsed.currency === 'INR' && parsed.amount >= 100000) {
      return formatMoneyCompact(parsed.amount, parsed.currency);
    }
    return formatMoney(parsed.amount, parsed.currency);
  }
  return trimmed;
}

export function formatPartySizeDisplay(value?: number | null, fallback = 'Party to confirm'): string {
  if (!value || value <= 0) return fallback;
  return `${value} pax`;
}

export function formatCustomerDisplay(rawInput?: unknown, fallback = ''): string {
  const fixtureId =
    typeof rawInput === 'object' &&
    rawInput !== null &&
    'fixture_id' in rawInput &&
    typeof rawInput.fixture_id === 'string'
      ? rawInput.fixture_id.trim()
      : '';
  if (!fixtureId) return fallback;
  return '';
}

export function hasCustomerName(rawInput?: unknown, agentNotes?: string, contactName?: string): boolean {
  if (contactName?.trim()) return true;
  if (agentNotes) {
    const tagPrefix = 'Contact name';
    const line = agentNotes.split('\n')
      .map(e => e.trim())
      .find(e => e.toLowerCase().startsWith(`${tagPrefix.toLowerCase()}:`));
    if (line) {
      const value = line.slice(tagPrefix.length + 1).trim();
      if (value) return true;
    }
  }
  return false;
}

export function readCustomerName(agentNotes?: string, contactName?: string): string | null {
  if (contactName?.trim()) return contactName.trim();
  if (!agentNotes) return null;
  const tagPrefix = 'Contact name';
  const line = agentNotes.split('\n')
    .map(e => e.trim())
    .find(e => e.toLowerCase().startsWith(`${tagPrefix.toLowerCase()}:`));
  if (!line) return null;
  const value = line.slice(tagPrefix.length + 1).trim();
  return value || null;
}

export function formatDateWindowDisplay(value?: string | null, fallback = 'Dates to confirm'): string {
  if (!value) return fallback;

  const trimmed = value.replace(/^dates\s+/i, '').trim();
  if (['tbd', 'to confirm', 'unknown', 'not set', 'n/a', '-'].includes(trimmed.toLowerCase())) {
    return fallback;
  }
  const formattedRange = formatSimpleDateRange(trimmed);
  if (formattedRange) return formattedRange;

  return trimmed.replace(/\b([a-z]{3,9})\b/gi, (month) => normalizeMonth(month));
}
