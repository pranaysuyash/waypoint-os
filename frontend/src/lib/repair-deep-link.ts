/**
 * D-09 repair deep-link helper (frontend honesty batch, 2026-09-02).
 *
 * Canonical param: `?repair=<field>` on the trip intake route
 * (/trips/{tripId}/intake → IntakePanel). It auto-opens the named field's
 * editor, scrolls it into view, and focuses it (keyboard-reachable; the input
 * keeps its visible focus ring).
 *
 * `?field=<...>` is accepted as a legacy alias for the same behavior. It was
 * the previous param name used by PacketPanel / PlanningTripCard links;
 * internal links have been migrated to `?repair=`, but old URLs keep working.
 *
 * Machine packet-unknown names (e.g. `date_window`, `party_size`) are mapped
 * onto the intake editor ids so the workbench blocked-run banner can link
 * operators straight to the first missing field's editor.
 */

export const INTAKE_PLANNING_FIELD_IDS = [
  'budget',
  'customerName',
  'origin',
  'destination',
  'priorities',
  'flexibility',
] as const;

export const INTAKE_INLINE_FIELD_IDS = ['type', 'dateWindow', 'party'] as const;

export type IntakeRepairFieldId =
  | (typeof INTAKE_PLANNING_FIELD_IDS)[number]
  | (typeof INTAKE_INLINE_FIELD_IDS)[number];

const PLANNING_FIELD_ID_SET: ReadonlySet<string> = new Set(INTAKE_PLANNING_FIELD_IDS);
const INLINE_FIELD_ID_SET: ReadonlySet<string> = new Set(INTAKE_INLINE_FIELD_IDS);

/**
 * Machine packet-unknown / validation field names → intake editor ids.
 * Mirrors FIELD_LABELS naming from src/lib/label-maps.ts.
 */
const MACHINE_FIELD_TO_REPAIR_ID: Record<string, IntakeRepairFieldId> = {
  budget: 'budget',
  budget_raw_text: 'budget',
  origin: 'origin',
  origin_city: 'origin',
  destination: 'destination',
  destination_candidates: 'destination',
  dates: 'dateWindow',
  date_window: 'dateWindow',
  date_start: 'dateWindow',
  date_end: 'dateWindow',
  party: 'party',
  party_size: 'party',
  party_composition: 'party',
  contact_name: 'customerName',
  customername: 'customerName',
  priorities: 'priorities',
  trip_priorities: 'priorities',
  hard_constraints: 'priorities',
  flexibility: 'flexibility',
  date_flexibility: 'flexibility',
};

/** Resolve a deep-link param value (canonical `repair` or legacy `field`). */
export function resolveRepairDeepLinkField(
  raw: string | null | undefined,
): IntakeRepairFieldId | null {
  const normalized = raw?.trim();
  if (!normalized) return null;

  if (PLANNING_FIELD_ID_SET.has(normalized)) {
    return normalized as IntakeRepairFieldId;
  }
  if (INLINE_FIELD_ID_SET.has(normalized)) {
    return normalized as IntakeRepairFieldId;
  }
  return MACHINE_FIELD_TO_REPAIR_ID[normalized.toLowerCase()] ?? null;
}

/**
 * First machine missing-field name (from packet unknowns / validation
 * missing-field lists) that maps to an intake editor. Returns the original
 * machine name so callers can pass it to buildRepairDeepLinkHref.
 */
export function getFirstRepairableFieldName(missingFields: string[] | null | undefined): string | null {
  for (const name of missingFields ?? []) {
    if (typeof name === 'string' && name && resolveRepairDeepLinkField(name)) {
      return name;
    }
  }
  return null;
}

/** Build the intake deep-link href for a machine field name on a trip. */
export function buildRepairDeepLinkHref(tripId: string, machineFieldName: string): string {
  const field = resolveRepairDeepLinkField(machineFieldName);
  if (!field) return `/trips/${tripId}/intake`;
  return `/trips/${tripId}/intake?repair=${encodeURIComponent(field)}`;
}
