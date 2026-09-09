// @vitest-environment jsdom

import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

/**
 * RDA-2026-09-08 honesty sweep (random-doc-audit register FT-01/FT-02/FT-10):
 * the public checker surface must not render fabricated social proof or fake
 * success messaging, and must not carry dead share machinery. These are
 * source-level contract tests so the forbidden content cannot silently return.
 */

const pageClientSource = readFileSync(join(__dirname, '..', 'PageClient.tsx'), 'utf8');
const proxySource = readFileSync(join(__dirname, '..', '..', '..', '..', 'proxy.ts'), 'utf8');

describe('itinerary-checker honesty sweep (FT-01/FT-02/FT-10)', () => {
  it('renders no fabricated testimonials (LR-D08)', () => {
    expect(pageClientSource).not.toContain('Real feedback from real itineraries');
    expect(pageClientSource).not.toContain('What travelers say');
    expect(pageClientSource).not.toContain('Sarah K.');
    expect(pageClientSource).not.toContain('Marcus T.');
    expect(pageClientSource).not.toContain('Priya N.');
    expect(pageClientSource).not.toContain('TestimonialsSection');
  });

  it('renders no fake email-send success state (FT-02)', () => {
    expect(pageClientSource).not.toContain('Report sent!');
    expect(pageClientSource).not.toContain('Check your inbox for the full PDF');
  });

  it('share channel union only contains reachable channels (FT-10)', () => {
    expect(pageClientSource).not.toContain("'whatsapp'");
    expect(pageClientSource).not.toContain("shareChannel: 'email'");
  });

  it('proxy no longer public-allowlists dead shared-result routes (FT-10)', () => {
    expect(proxySource).not.toContain('/itinerary-checker/shared/');
    expect(proxySource).not.toContain('/itinerary/shared/');
  });

  it('renders the legal disclaimer on the surface (EX-05, WOBS P1)', () => {
    expect(pageClientSource).toContain('not legal, visa, or booking advice');
    // Mounted in both the result view and the upload footer.
    expect(pageClientSource.match(/{CHECKER_DISCLAIMER}/g)?.length ?? 0).toBeGreaterThanOrEqual(2);
  });

  it('consent copy makes no training claim (truthful storage framing)', () => {
    expect(pageClientSource).not.toContain('future training');
    expect(pageClientSource).toContain('nothing is kept');
  });

  it('score is demoted — dial is compact and retitled (Manifest rework)', () => {
    expect(pageClientSource).not.toContain('Itinerary Health Score');
    expect(pageClientSource).toContain('Health check');
    expect(pageClientSource).toContain('What your plan is missing');
  });
});
