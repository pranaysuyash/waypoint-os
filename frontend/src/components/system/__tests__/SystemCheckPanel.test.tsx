import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import SystemCheckPanel from '../SystemCheckPanel';

vi.mock('@/hooks/useIntegrityIssues', () => ({
  useIntegrityIssues: vi.fn(),
}));

import { useIntegrityIssues } from '@/hooks/useIntegrityIssues';

describe('SystemCheckPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.stubGlobal('fetch', vi.fn());

    vi.mocked(useIntegrityIssues).mockReturnValue({
      data: [
        {
          id: 'integrity_orphaned_record_trip_orphan_1',
          entity_id: 'trip_orphan_1',
          entity_type: 'unknown',
          issue_type: 'orphaned_record',
          severity: 'medium',
          reason: 'Record is detached from normal inbox/workspace routing.',
          current_status: 'unknown',
          created_at: '2026-04-30T00:00:00Z',
          detected_at: '2026-04-30T00:05:00Z',
          allowed_actions: [],
        },
      ],
      total: 1,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
  });

  it('renders a read-only system check without status reset copy or repair calls', () => {
    render(<SystemCheckPanel open onClose={vi.fn()} />);

    expect(screen.getByRole('heading', { name: /system check/i })).toBeInTheDocument();
    expect(screen.getByText('Routing issue')).toBeInTheDocument();
    expect(screen.getAllByText('trip_orphan_1').length).toBeGreaterThan(0);
    expect(screen.getByText(/this record is detached from the normal workflow\./i)).toBeInTheDocument();
    expect(screen.getAllByText(/manual review required/i).length).toBeGreaterThan(0);
    expect(screen.queryByText(/resets.*new status/i)).not.toBeInTheDocument();
    expect(fetch).not.toHaveBeenCalledWith(
      expect.stringContaining('/api/trips/'),
      expect.objectContaining({
        method: 'PATCH',
      })
    );
  });
});
