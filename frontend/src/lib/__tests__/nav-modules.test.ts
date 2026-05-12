import { describe, expect, it } from 'vitest';
import { DOCUMENTS_MODULE_ROLLOUT_GATES, NAV_SECTIONS, isDocumentsModuleEnabled } from '../nav-modules';

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

  it('enables Documents module when all rollout gates are complete', () => {
    expect(isDocumentsModuleEnabled()).toBe(true);
    expect(DOCUMENTS_MODULE_ROLLOUT_GATES.every((gate) => gate.complete === true)).toBe(true);

    const operations = NAV_SECTIONS.find((section) => section.label === 'OPERATIONS');
    const documents = operations?.items.find((item) => item.href === '/documents');
    expect(documents?.enabled).toBe(true);
  });
});
