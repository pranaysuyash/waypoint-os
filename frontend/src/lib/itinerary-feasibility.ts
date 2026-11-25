type ItineraryFinding = {
  id: string;
  title: string;
  message: string;
  context: string;
  ask: string | null;
  source: { url: string; label: string } | null;
};

const legacyFields = [
  ['overnight_hotel_arrival', 'Confirm late hotel arrival', 'public_checker_overnight_hotel_finding'],
  ['goa_day_pacing', 'Check whether all three stops fit', 'public_checker_day_pacing_finding'],
] as const;

const dudhsagarSource = 'https://www.goa.gov.in/places/dudhsagar-waterfalls/';
const sourceLabels = new Map([
  [dudhsagarSource, 'Government of Goa Dudhsagar guide'],
  ['https://www.eurostar.com/uk-en/travel-info/connecting-train', 'Eurostar connecting train guidance'],
  ['https://help.eurostar.com/faq/uk-en/question/What-happens-if-I-miss-my-connection-due-to-a-delay-or-cancellation', 'Eurostar missed connection conditions'],
]);

const findingContacts = new Map([
  ['overnight_hotel_arrival', 'the hotel reservations team'],
  ['goa_day_pacing', 'your travel agent or local tour operator'],
  ['hotel_terms', 'the hotel or booking agent'],
  ['helsinki_connection', 'the operating airline or ticketing agent'],
  ['overnight_rail_transfer', 'the transfer operator or rail ticketing agent'],
  ['eurostar_tgv_connection', 'Eurostar staff and the onward ticket office'],
  ['eurostar_rer_connection', 'rail staff'],
  ['vehicle_ferry_cutoff', 'the ferry operator'],
  ['vatican_admission', 'the venue or ticket seller'],
  ['shore_excursion_return', 'the excursion operator or cruise line'],
  ['step_free_transfer', 'the transfer operator'],
  ['rental_pickup', 'the rental branch'],
]);

function getFindingContact(id: unknown) {
  if (typeof id !== 'string') return null;
  const family = /^hotel_terms_[0-9a-f]{16}$/.test(id) ? 'hotel_terms' : id;
  return findingContacts.get(family) ?? null;
}

function getSource(url: unknown) {
  if (typeof url !== 'string') return null;
  const label = sourceLabels.get(url);
  return label ? { url, label } : null;
}

export function getItineraryFeasibilityEvidence(packet: unknown) {
  const record = packet && typeof packet === 'object' ? packet as Record<string, unknown> : {};
  return {
    returnDatePending: record.public_checker_return_date_pending === true,
    context: typeof record.itinerary_feasibility_context === 'string' ? record.itinerary_feasibility_context : null,
    question: typeof record.itinerary_feasibility_question === 'string' ? record.itinerary_feasibility_question : null,
    source: getSource(record.itinerary_feasibility_source_url),
    ask: getFindingContact(record.itinerary_feasibility_id),
  };
}

export function getItineraryFeasibilityFindings(packet: unknown): ItineraryFinding[] {
  if (!packet || typeof packet !== 'object') return [];
  const record = packet as Record<string, unknown>;
  if (Array.isArray(record.itinerary_feasibility_findings)) {
    return record.itinerary_feasibility_findings.flatMap((finding) => {
      const details = finding?.details;
      if (
        details?.authority !== 'advisory' || typeof details.title !== 'string' ||
        typeof finding.message !== 'string' || typeof finding.flag !== 'string'
      ) return [];
      return [{
        id: finding.flag,
        ask: getFindingContact(finding.flag),
        title: details.title,
        message: finding.message,
        context: typeof details.context === 'string' ? details.context : '',
        source: getSource(details.source_url),
      }];
    });
  }
  return legacyFields.flatMap(([id, title, key]) => {
    const message = record[key];
    return typeof message === 'string'
      ? [{ id, title, message, ask: getFindingContact(id), context: '', source: id === 'goa_day_pacing' ? getSource(dudhsagarSource) : null }]
      : [];
  });
}
