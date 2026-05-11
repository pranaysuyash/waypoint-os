import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import SettingsPanel from '../SettingsPanel';

vi.mock('@/stores/workbench', () => ({
  useWorkbenchStore: vi.fn(),
}));

vi.mock('@/hooks/useUnifiedState', () => ({
  useUnifiedState: vi.fn(),
}));

import { useWorkbenchStore } from '@/stores/workbench';
import { useUnifiedState } from '@/hooks/useUnifiedState';

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
  });

  it('keeps settings focused on configuration only', () => {
    render(<SettingsPanel open onClose={vi.fn()} />);

    expect(screen.getByRole('heading', { name: /settings/i })).toBeInTheDocument();
    expect(screen.queryByText(/orphaned records/i)).not.toBeInTheDocument();
  });
});
