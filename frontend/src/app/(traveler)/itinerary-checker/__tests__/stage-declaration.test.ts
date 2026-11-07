// @vitest-environment jsdom

import { describe, expect, it } from 'vitest';
import { stageForSubmittedPlan } from '../PageClient';

/**
 * RDA_EX07 rec-3 / FND-0399: travelers who declare the trip already booked
 * submit under stage="booking" so the booking-critical visa_not_applied /
 * document_risk checks fire for them. Everyone else stays at discovery.
 */

describe('itinerary-checker stage declaration (RDA_EX07 rec-3)', () => {
  it('maps declared-booked to the booking gate', () => {
    expect(stageForSubmittedPlan(true)).toBe('booking');
  });

  it('maps not-yet-booked to discovery', () => {
    expect(stageForSubmittedPlan(false)).toBe('discovery');
  });
});
