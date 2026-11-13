import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import SuppliersPage from '../PageClient';

const mockUploadContract = vi.fn();
const mockCreateSoftHold = vi.fn();

vi.mock('next/navigation', () => ({
  useSearchParams: () => new URLSearchParams(),
}));

vi.mock('@/hooks/useTrips', () => ({
  useTrips: () => ({
    data: [
      {
        id: 'trip_sup_1',
        destination: 'Amalfi Coast',
        stage: 'booking',
        status: 'in_progress',
        type: 'custom',
        state: 'blue',
        age: '2d',
        updated_at: '2026-11-11T00:00:00Z',
      },
    ],
    total: 1,
    isLoading: false,
  }),
  useTrip: (id: string | null) => ({
    data: id
      ? {
          id,
          agentOperations: {
            supplierRiskLevel: 'medium',
            supplierIntelligenceSnapshot: { suppliers: ['Fast Lodge DMC'] },
          },
        }
      : null,
  }),
}));

vi.mock('@/hooks/useSuppliers', () => ({
  useSupplierLedger: () => ({
    contracts: [
      {
        contract_id: 'contract_demo1',
        agency_id: 'agency_1',
        supplier_name: 'Amalfi Luxury DMC',
        destination: 'Amalfi Coast',
        currency: 'EUR',
        rate_table: [
          {
            room_type: 'Sea View Terrace Suite',
            net_rate_per_night: 450,
            rack_rate_per_night: 650,
          },
        ],
        uploaded_at: '2026-11-11T00:00:00Z',
        status: 'ACTIVE',
      },
    ],
    holds: [],
    isLoading: false,
    error: null,
    refresh: vi.fn(),
    uploadContract: mockUploadContract,
    createSoftHold: mockCreateSoftHold,
  }),
}));

describe('Suppliers operator rate-sheet & 48h soft-hold workflows', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUploadContract.mockResolvedValue({
      contract_id: 'contract_new1',
      supplier_name: 'Kyoto Boutique DMC',
      destination: 'Kyoto, Japan',
      total_rates_ingested: 1,
      uploaded_at: '2026-11-11T00:00:00Z',
      status: 'INGESTED',
    });
    mockCreateSoftHold.mockResolvedValue({
      hold_id: 'hold_abc12345',
      contract_id: 'contract_demo1',
      supplier_name: 'Amalfi Luxury DMC',
      room_type: 'Sea View Terrace Suite',
      net_rate_total: 1800,
      rack_rate_total: 2600,
      estimated_agency_margin: 800,
      expires_at: '2026-11-13T00:00:00Z',
      status: 'SOFT_HOLD_ACTIVE',
    });
  });

  it('submits a new wholesale rate sheet via modal and preserves honesty fixtures', async () => {
    render(<SuppliersPage />);

    expect(screen.getByText('Amalfi Luxury DMC')).toBeInTheDocument();
    expect(screen.getByTestId('simulated-badge')).toHaveTextContent('Sample data');

    fireEvent.click(screen.getByTestId('open-upload-contract-btn'));
    expect(screen.getByTestId('upload-contract-modal')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText(/Supplier \/ DMC name/i), {
      target: { value: 'Kyoto Boutique DMC' },
    });
    fireEvent.change(screen.getByLabelText(/Supplier category/i), {
      target: { value: 'airline' },
    });
    fireEvent.change(screen.getByLabelText(/^Destination$/i), {
      target: { value: 'Kyoto, Japan' },
    });

    fireEvent.click(screen.getByRole('button', { name: /Save Rate Sheet/i }));

    await waitFor(() => {
      expect(mockUploadContract).toHaveBeenCalledWith(
        expect.objectContaining({
          supplier_name: 'Kyoto Boutique DMC',
          supplier_category: 'airline',
          destination: 'Kyoto, Japan',
          currency: 'INR',
        })
      );
    });
  });

  it('submits a 48h soft-hold against a recorded contract', async () => {
    render(<SuppliersPage />);

    fireEvent.click(screen.getByRole('button', { name: /Reserve 48h Hold/i }));
    expect(screen.getByTestId('soft-hold-modal')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText(/Lead traveler name/i), {
      target: { value: 'Priya Sharma' },
    });
    fireEvent.change(screen.getByLabelText(/Check-in/i), {
      target: { value: '2026-12-10' },
    });
    fireEvent.change(screen.getByLabelText(/Check-out/i), {
      target: { value: '2026-12-14' },
    });

    fireEvent.click(screen.getByRole('button', { name: /Confirm 48h Soft-Hold/i }));

    await waitFor(() => {
      expect(mockCreateSoftHold).toHaveBeenCalledWith({
        contract_id: 'contract_demo1',
        room_type: 'Sea View Terrace Suite',
        guest_name: 'Priya Sharma',
        check_in: '2026-12-10',
        check_out: '2026-12-14',
      });
    });
  });
});
