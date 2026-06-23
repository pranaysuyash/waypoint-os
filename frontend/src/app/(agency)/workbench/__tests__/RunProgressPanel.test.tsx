import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { RunProgressPanel } from '../RunProgressPanel';

describe('RunProgressPanel', () => {
  it('shows the completed-state trip actions once each', () => {
    render(
      <RunProgressPanel
        runId="run_12345678"
        runState={{
          state: 'completed',
          trip_id: 'trip_123',
          steps_completed: ['packet', 'validation', 'decision', 'strategy', 'safety'],
          started_at: '2026-06-23T00:00:00.000Z',
          total_ms: 42,
          events: [],
        } as never}
        onRetry={vi.fn()}
        onViewTrip={vi.fn()}
        onViewFrontier={vi.fn()}
      />
    );

    expect(screen.getAllByRole('button', { name: 'View Trip' })).toHaveLength(1);
    expect(screen.getAllByRole('button', { name: 'View Frontier' })).toHaveLength(1);
    expect(screen.getByText('Processing Complete')).toBeInTheDocument();
  });
});
