import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { StrategyPanel } from '../StrategyPanel';

vi.mock('@/contexts/TripContext', () => ({
  useTripContext: vi.fn(() => ({ trip: null })),
}));

vi.mock('@/stores/workbench', () => ({
  useWorkbenchStore: vi.fn(() => ({
    result_strategy: null,
    debug_raw_json: false,
    setDebugRawJson: vi.fn(),
  })),
}));

vi.mock('@/lib/privacy-controls', () => ({
  isDebugJsonAllowed: () => false,
}));

describe('StrategyPanel empty state', () => {
  it('uses product-friendly loading copy instead of placeholder language', () => {
    render(<StrategyPanel tripId="trip-1" />);

    expect(screen.getByText('Ready to build trip options')).toBeInTheDocument();
    expect(screen.getByText(/show a concrete options brief/i)).toBeInTheDocument();
    expect(screen.queryByText(/dead stub/i)).not.toBeInTheDocument();
  });
});
