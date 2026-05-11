import { describe, expect, it } from 'vitest';
import { checkContrast, contrastRatio, ensureContrast, luminance, passesAA, passesAAA, validateTokenColors, WCAG } from '../contrast-utils';

describe('contrast utilities', () => {
  it('calculates luminance and contrast ratios for WCAG checks', () => {
    expect(luminance('#000000')).toBe(0);
    expect(contrastRatio('#000000', '#ffffff')).toBeCloseTo(21, 0);
    expect(passesAA(WCAG.AA_NORMAL)).toBe(true);
    expect(passesAAA(WCAG.AAA_NORMAL)).toBe(true);
  });

  it('returns structured contrast compliance details', () => {
    const result = checkContrast('#000000', '#ffffff');

    expect(result.ratio).toBeCloseTo(21, 0);
    expect(result.passesAA).toBe(true);
    expect(result.passesAAA).toBe(true);
  });

  it('lightens a text color until contrast is sufficient', () => {
    const adjusted = ensureContrast('#111111', '#111111');

    expect(adjusted).not.toBe('#111111');
    expect(checkContrast(adjusted, '#111111').passesAA).toBe(true);
  });

  it('validates token color combinations for design QA tooling', () => {
    const results = validateTokenColors();

    expect(results.length).toBeGreaterThan(0);
    expect(results[0]).toHaveProperty('ratio');
  });
});
