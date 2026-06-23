import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import AuditPage from '../PageClient';

vi.mock('@/hooks/useClientDate', () => ({
  ClientDateTime: ({ value }: { value: string }) => <span>{value}</span>,
}));

describe('AuditPage', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders audit events from the entries contract returned by the backend', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          ok: true,
          entries: [
            {
              id: 'audit-1',
              type: 'trip.stage.changed',
              user_id: 'agent-1',
              timestamp: '2026-06-23T02:00:00.000Z',
              details: { from: 'intake', to: 'strategy' },
            },
          ],
        }),
      } as Response)
    );

    render(<AuditPage />);

    await waitFor(() => expect(screen.getByText('trip.stage.changed')).toBeInTheDocument());
    expect(screen.getByText('2026-06-23T02:00:00.000Z')).toBeInTheDocument();
    expect(screen.getByText(/"from":"intake"/)).toBeInTheDocument();
    expect(screen.getByText(/"to":"strategy"/)).toBeInTheDocument();
  });

  it('shows the empty state when the backend returns no entries', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ ok: true, entries: [] }),
      } as Response)
    );

    render(<AuditPage />);

    await waitFor(() => expect(screen.getByText('No audit events recorded yet.')).toBeInTheDocument());
  });
});
