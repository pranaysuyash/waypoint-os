import { describe, expect, it } from 'vitest';
import manifest from '../../../public/manifest.json';

describe('Companion install metadata', () => {
  it('describes the online itinerary and demonstration boundaries', () => {
    expect(manifest.description).toContain('Online itinerary access');
    expect(manifest.description).toContain('SOS demonstration');
    expect(manifest.description).not.toMatch(/Offline Itineraries|Live Flight Alerts|Crisis SOS/i);
    expect(manifest.start_url).toBe('/companion');
  });
});
