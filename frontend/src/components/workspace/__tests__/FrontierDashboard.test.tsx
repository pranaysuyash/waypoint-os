import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { FrontierDashboard } from '../FrontierDashboard';

let mockState: Record<string, unknown> = {};

vi.mock('@/stores/workbench', () => ({
  useWorkbenchStore: (selector: (state: Record<string, unknown>) => unknown) => selector(mockState),
}));

describe('FrontierDashboard', () => {
  it('renders a no-data state when frontier analysis is absent', () => {
    mockState = { result_frontier: null, result_packet: null };

    render(<FrontierDashboard packetId='packet-fallback' />);

    expect(screen.getByText('Ghost Concierge')).toBeInTheDocument();
    expect(screen.getByText('No frontier data - run a pipeline to populate')).toBeInTheDocument();
    expect(screen.getByText('NO DATA')).toBeInTheDocument();
  });

  it('renders live frontier intelligence from the workbench store', () => {
    mockState = {
      result_packet: { packet_id: 'packet-123' },
      result_frontier: {
        ghost_triggered: true,
        ghost_workflow_id: 'ghost-1',
        sentiment_score: 0.82,
        anxiety_alert: true,
        intelligence_hits: [{ message: 'Visa timing risk', source: 'ops', severity: 'high' }],
        mitigation_applied: true,
        requires_manual_audit: true,
        audit_reason: 'Supplier reliability check',
        negotiation_active: true,
      },
    };

    render(<FrontierDashboard />);

    expect(screen.getByText('ACTIVE')).toBeInTheDocument();
    expect(screen.getByText('82%')).toBeInTheDocument();
    expect(screen.getByText('Visa timing risk')).toBeInTheDocument();
    expect(screen.getByText('Reason: Supplier reliability check')).toBeInTheDocument();
    expect(screen.getByText('LIVE DATA')).toBeInTheDocument();
  });
});
