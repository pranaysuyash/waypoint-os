import { describe, expect, it, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { ChangeHistoryPanel } from '../ChangeHistoryPanel';
import { useAuthStore } from '@/stores/auth';

vi.mock('@/stores/auth', () => ({
  useAuthStore: vi.fn(),
}));

function createAuthState(role: 'owner' | 'viewer' | null = 'owner') {
  const baseState = {
    user: null,
    agency: null,
    membership: role ? { role, isPrimary: true } : null,
    isAuthenticated: Boolean(role),
    isLoading: false,
    error: null,
    setAuth: vi.fn(),
    logout: vi.fn(),
    hydrate: vi.fn(),
    clearError: vi.fn(),
  };

  vi.mocked(useAuthStore).mockImplementation((selector) => selector(baseState as never));
}

const storedAuditLog = {
  tripId: 'trip-1',
  version: 1,
  lastModified: '2026-05-11T00:00:00.000Z',
  changes: [
    {
      id: 'change-1',
      tripId: 'trip-1',
      field: 'destination',
      changeType: 'update',
      previousValue: 'Paris',
      newValue: 'Rome',
      changedBy: 'user-1',
      changedByName: 'Asha',
      timestamp: '2026-05-11T00:00:00.000Z',
      reason: 'Traveler changed plans',
    },
  ],
};

describe('ChangeHistoryPanel', () => {
  beforeEach(() => {
    localStorage.clear();
    createAuthState('owner');
  });

  it('renders an empty-state audit trail for trips without changes', async () => {
    render(<ChangeHistoryPanel tripId='trip-empty' />);

    await waitFor(() => {
      expect(screen.getByText('No changes yet')).toBeInTheDocument();
    });
  });

  it('renders stored field changes with human-readable copy', async () => {
    localStorage.setItem('trip_audit:v1:trip-1', JSON.stringify(storedAuditLog));

    render(<ChangeHistoryPanel tripId='trip-1' />);

    await waitFor(() => {
      expect(screen.getByText('Change History')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Export/i })).toBeInTheDocument();
      expect(screen.getByText(/Changed Destination from "Paris" to "Rome"/)).toBeInTheDocument();
      expect(screen.getAllByText('Asha').length).toBeGreaterThan(0);
    });
  });

  it('hides export for viewer role', async () => {
    localStorage.setItem('trip_audit:v1:trip-1', JSON.stringify(storedAuditLog));
    createAuthState('viewer');

    render(<ChangeHistoryPanel tripId='trip-1' />);

    await waitFor(() => {
      expect(screen.getByText('Change History')).toBeInTheDocument();
      expect(screen.queryByRole('button', { name: /Export/i })).not.toBeInTheDocument();
    });
  });
});
