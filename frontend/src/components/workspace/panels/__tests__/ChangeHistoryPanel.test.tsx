import { describe, expect, it, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { ChangeHistoryPanel } from '../ChangeHistoryPanel';

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
      expect(screen.getByText(/Changed Destination from "Paris" to "Rome"/)).toBeInTheDocument();
      expect(screen.getAllByText('Asha').length).toBeGreaterThan(0);
    });
  });
});
