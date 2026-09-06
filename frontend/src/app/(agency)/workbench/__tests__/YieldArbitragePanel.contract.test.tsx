// @vitest-environment jsdom

import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import YieldArbitragePanel from '../YieldArbitragePanel';

const { mockGet, mockPost } = vi.hoisted(() => ({
  mockGet: vi.fn(),
  mockPost: vi.fn(),
}));

vi.mock('@/lib/api-client', () => ({
  api: {
    get: mockGet,
    post: mockPost,
  },
}));

describe('YieldArbitragePanel canonical contract', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('requires a real workbench trip and does not call a demo resource', () => {
    render(<YieldArbitragePanel />);

    expect(screen.getByRole('status')).toHaveTextContent(/select a trip/i);
    expect(mockGet).not.toHaveBeenCalled();
    expect(screen.queryByText(/trip_demo|BKG-|Hotelbeds|WebBeds/i)).toBeNull();
  });

  it('loads the canonical agency-scoped endpoint and posts the canonical swap shape', async () => {
    mockGet.mockResolvedValue({
      ok: true,
      trip_id: 'trip_contract_123',
      data_sufficient: true,
      supplier_options: [
        {
          supplier_name: 'Uploaded DMC Contract',
          supplier_type: 'direct_contract',
          base_cost: 1500,
          commission_pct: 20,
          net_margin: 500,
          bonus_override_eligible: true,
          suitability_score: 95,
        },
        {
          supplier_name: 'Alternative Contract',
          supplier_type: 'direct_contract',
          base_cost: 1600,
          commission_pct: 15,
          net_margin: 400,
          bonus_override_eligible: false,
          suitability_score: 90,
        },
      ],
      optimal_supplier: 'Uploaded DMC Contract',
      potential_margin_gain: 100,
      generated_at: '2026-09-04T00:00:00Z',
    });
    mockPost.mockResolvedValue({
      ok: true,
      trip_id: 'trip_contract_123',
      selected_supplier: 'Alternative Contract',
      message: 'Supplier selection saved.',
    });

    render(<YieldArbitragePanel tripId="trip_contract_123" />);

    await waitFor(() => {
      expect(mockGet).toHaveBeenCalledWith('/api/v1/yield/arbitrage/trip_contract_123');
    });
    expect(screen.getByText('Uploaded DMC Contract')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /select supplier/i }));
    await waitFor(() => {
      expect(mockPost).toHaveBeenCalledWith('/api/v1/yield/swap-supplier', {
        trip_id: 'trip_contract_123',
        supplier_name: 'Alternative Contract',
      });
    });
    expect(await screen.findByRole('status')).toHaveTextContent(/supplier selection saved/i);
  });
});
