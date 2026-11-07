'use client';

import ItineraryCheckerPage, { AgencyBrandingContext } from '../../itinerary-checker/PageClient';

export default function ClientWrapper({
  agencyContext,
}: {
  agencyContext: AgencyBrandingContext | null;
}) {
  return <ItineraryCheckerPage agencyContext={agencyContext} />;
}
