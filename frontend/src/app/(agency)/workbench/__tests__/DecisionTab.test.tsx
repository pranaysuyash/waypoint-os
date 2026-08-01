import { describe, expect, it, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import type { ReactNode } from 'react';
import DecisionTab from '../DecisionTab';

const mockStore = {
  result_decision: null,
  result_fees: null,
  debug_raw_json: false,
  setDebugRawJson: vi.fn(),
  acknowledged_suitability_flags: [],
  acknowledgeFlag: vi.fn(),
};

vi.mock('@/stores/workbench', () => ({
  useWorkbenchStore: () => mockStore,
}));

vi.mock('next/link', () => ({
  default: ({ children, href, ...props }: { children: ReactNode; href: string }) => (
    <a href={href} {...props}>
      {children}
    </a>
  ),
}));

vi.mock('@/components/workspace/panels/SuitabilitySignal', () => ({
  SuitabilitySignal: () => null,
}));

vi.mock('@/components/workbench/workbench.module.css', () => ({
  default: new Proxy(
    {},
    {
      get: (_: unknown, prop: string) => prop,
    },
  ),
}));

describe('DecisionTab', () => {
  beforeEach(() => {
    mockStore.result_decision = null;
    mockStore.result_fees = null;
    mockStore.debug_raw_json = false;
    mockStore.setDebugRawJson = vi.fn();
    mockStore.acknowledged_suitability_flags = [];
    mockStore.acknowledgeFlag = vi.fn();
  });

  it('routes missing decision data to the trip repair surface when a trip exists', () => {
    render(
      <DecisionTab
        trip={{
          id: 'trip-decision-repair',
          destination: 'Bali',
          type: 'family leisure',
          state: 'green',
          age: '1h',
          createdAt: '2026-05-27T00:00:00Z',
          updatedAt: '2026-05-27T00:00:00Z',
          origin: 'Mumbai',
          budget: '₹4L',
          dateWindow: 'Jul 2026',
          party: 4,
        } as never}
      />
    );

    expect(screen.getByText(/No quote status data yet/i)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Open Trip Details' })).toHaveAttribute(
      'href',
      '/trips/trip-decision-repair/intake',
    );
    expect(screen.queryByText(/New Inquiry/)).not.toBeInTheDocument();
  });
});
