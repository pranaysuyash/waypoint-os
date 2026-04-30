import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import SettingsPanel from '../SettingsPanel';
import IntegrityMonitorPanel from '../IntegrityMonitorPanel';

vi.mock('@/stores/workbench', () => ({
  useWorkbenchStore: vi.fn(),
}));

vi.mock('@/hooks/useUnifiedState', () => ({
  useUnifiedState: vi.fn(),
}));

vi.mock('@/hooks/useIntegrityIssues', () => ({
  useIntegrityIssues: vi.fn(),
}));

import { useWorkbenchStore } from '@/stores/workbench';
import { useUnifiedState } from '@/hooks/useUnifiedState';
import { useIntegrityIssues } from '@/hooks/useIntegrityIssues';

describe('Workbench side panels', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.stubGlobal('fetch', vi.fn());

    vi.mocked(useWorkbenchStore).mockReturnValue({
      strict_leakage: false,
      setStrictLeakage: vi.fn(),
      debug_raw_json: false,
      setDebugRawJson: vi.fn(),
      enable_ghost_concierge: false,
      setEnableGhostConcierge: vi.fn(),
      enable_sentiment_analysis: false,
      setEnableSentimentAnalysis: vi.fn(),
      federated_intelligence_opt_in: false,
      setFederatedIntelligenceOptIn: vi.fn(),
      audit_confidence_threshold: 0.7,
      setAuditConfidenceThreshold: vi.fn(),
      enable_auto_negotiation: false,
      setEnableAutoNegotiation: vi.fn(),
      negotiation_margin_threshold: 0.1,
      setNegotiationMarginThreshold: vi.fn(),
    } as never);

    vi.mocked(useUnifiedState).mockReturnValue({
      state: null,
      loading: false,
      error: null,
      refresh: vi.fn(),
      isConsistent: true,
    });

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

  it('keeps settings focused on configuration only', () => {
    render(<SettingsPanel open onClose={vi.fn()} />);

    expect(screen.getByRole('heading', { name: /settings/i })).toBeInTheDocument();
    expect(screen.queryByText(/orphaned records/i)).not.toBeInTheDocument();
  });

  it('renders a read-only integrity monitor without status reset copy or repair calls', () => {
    render(<IntegrityMonitorPanel open onClose={vi.fn()} />);

    expect(screen.getByRole('heading', { name: /system check/i })).toBeInTheDocument();
    expect(screen.getByText('Routing issue')).toBeInTheDocument();
    expect(screen.getAllByText('trip_orphan_1').length).toBeGreaterThan(0);
    expect(screen.getByText(/this record is detached from the normal workflow\./i)).toBeInTheDocument();
    expect(screen.getAllByText(/manual review required/i).length).toBeGreaterThan(0);
    expect(screen.queryByText(/resets.*new status/i)).not.toBeInTheDocument();
    expect(vi.mocked(useUnifiedState)).not.toHaveBeenCalled();
    expect(fetch).not.toHaveBeenCalledWith(
      expect.stringContaining('/api/trips/'),
      expect.objectContaining({
        method: 'PATCH',
      })
    );
  });
});
