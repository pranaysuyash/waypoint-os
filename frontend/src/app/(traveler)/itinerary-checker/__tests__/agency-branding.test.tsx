// @vitest-environment jsdom

import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import ItineraryCheckerPage, { AgencyBrandingContext } from '../PageClient';

describe('Itinerary Checker Agency Branding (Stream 1)', () => {
  it('renders default Waypoint header when no agency context is provided', () => {
    render(<ItineraryCheckerPage />);
    expect(screen.getByText('Waypoint')).toBeDefined();
    expect(screen.getByText('Travel plan checker')).toBeDefined();
    expect(screen.getByText('For agencies →')).toBeDefined();
  });

  it('renders agency-branded header when agencyContext is provided', () => {
    const mockAgency: AgencyBrandingContext = {
      agency_id: 'agency-aurora-777',
      slug: 'aurora-luxury-travel',
      display_name: 'Aurora Luxury Travel',
      blurb: 'Bespoke European and Nordic itineraries.',
      response_sla_hours: 12,
      places_covered: ['Iceland', 'Norway', 'Finland'],
    };

    render(<ItineraryCheckerPage agencyContext={mockAgency} />);
    expect(screen.getByText('Aurora Luxury Travel')).toBeDefined();
    expect(screen.getByText('Client Travel Plan Diagnostic · Powered by Waypoint')).toBeDefined();
    expect(screen.getByText('Complimentary Client Audit')).toBeDefined();
    expect(screen.getByText('Listed response time: 12h')).toBeDefined();
    // Default public link should NOT be shown
    expect(screen.queryByText('For agencies →')).toBeNull();
  });
});
