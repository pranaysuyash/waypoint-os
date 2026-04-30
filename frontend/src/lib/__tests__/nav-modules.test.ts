import { describe, expect, it } from 'vitest';
import { NAV_SECTIONS } from '../nav-modules';

describe('NAV_SECTIONS', () => {
  it('aligns shell labels with the agency-facing dashboard vocabulary', () => {
    expect(NAV_SECTIONS.find((section) => section.label === 'PLANNING')).toBeTruthy();

    const command = NAV_SECTIONS.find((section) => section.label === 'COMMAND');
    const planning = NAV_SECTIONS.find((section) => section.label === 'PLANNING');

    expect(command?.items.map((item) => item.label)).toContain('Quote Review');
    expect(command?.items.map((item) => item.label)).not.toContain('Approval Queue');
    expect(planning?.items.map((item) => item.label)).toContain('Trips in Planning');
    expect(planning?.items.map((item) => item.label)).not.toContain('Trips');
  });
});
