// @vitest-environment jsdom

import { describe, expect, it } from 'vitest';
import { formatTravelerBlockerItem } from '../PageClient';

/**
 * Part-K AT-21: backend blocker slugs must never reach travelers raw.
 * Known slugs map to honest traveler lines; unknown slugs fall back to a
 * generic advisor line instead of `slug_with_underscores`.
 */

describe('itinerary-checker blocker copy (AT-21)', () => {
  it('maps known slugs to traveler-voiced lines', () => {
    expect(formatTravelerBlockerItem('extraction_quality')).toMatch(
      /could not confidently read/i,
    );
    expect(formatTravelerBlockerItem('incomplete_intake')).toMatch(
      /core intake details are still missing/i,
    );
  });

  it('never renders an unknown slug raw — falls back to the advisor line', () => {
    const out = formatTravelerBlockerItem('mystery_slug_from_backend');
    expect(out).not.toContain('_');
    expect(out).toMatch(/travel advisor can confirm the details/i);
  });
});
