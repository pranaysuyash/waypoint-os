import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import PacketTab from '../PacketTab';
import type { Trip } from '@/lib/api-client';

const mockStore = vi.fn();
const { resolveAssumptionsMock } = vi.hoisted(() => ({ resolveAssumptionsMock: vi.fn() }));

vi.mock('@/stores/workbench', () => ({
  useWorkbenchStore: () => mockStore(),
}));

vi.mock('@/lib/api-client', () => ({
  resolveTripAssumptions: resolveAssumptionsMock,
}));

function slot(value: unknown) {
  return {
    value,
    confidence: 0.9,
    authority_level: 'customer',
    extraction_mode: 'direct',
    derived_from: [],
  };
}

describe('PacketTab', () => {
  beforeEach(() => {
    mockStore.mockReturnValue({
      result_packet: null,
      result_validation: null,
      debug_raw_json: false,
      setDebugRawJson: vi.fn(),
    });
  });

  it('renders structured packet values without leaking object coercion text', () => {
    mockStore.mockReturnValue({
      result_packet: {
        facts: {
          destination_candidates: slot([
            { city: 'Bali', country: 'Indonesia', confidence: 0.86 },
          ]),
          owner_constraints: slot([
            { text: 'properties with long transfers', visibility: 'internal_only' },
            { text: 'vegetarian food', visibility: 'traveler_safe_transformable' },
          ]),
        },
        derived_signals: {
          trip_purpose: slot({ value: 'family leisure', source: 'message hints' }),
        },
        unknowns: [],
        ambiguities: [],
        contradictions: [],
      },
      result_validation: null,
      debug_raw_json: false,
      setDebugRawJson: vi.fn(),
    });

    render(<PacketTab />);

    expect(screen.queryByText(/\[object Object\]/)).not.toBeInTheDocument();
    expect(screen.getAllByText(/City: Bali; Country: Indonesia; Confidence: 0.86/).length).toBeGreaterThan(0);
    expect(screen.getByText('Purpose')).toBeInTheDocument();
    expect(screen.getAllByText(/Value: family leisure; Source: message hints/).length).toBeGreaterThan(0);
    expect(screen.getByText(/properties with long transfers \(internal only\)/)).toBeInTheDocument();
    expect(screen.getByText(/vegetarian food \(traveler safe transformable\)/)).toBeInTheDocument();
    expect(screen.getByText(/Value: family leisure; Source: message hints \(90%\)/)).toBeInTheDocument();
  });

  it('keeps verbose validation prompts behind the details toggle', () => {
    mockStore.mockReturnValue({
      result_packet: {
        facts: {
          destination_candidates: slot(['Bali']),
        },
        derived_signals: {},
        unknowns: [
          { field_name: 'origin_city', reason: 'missing', notes: null },
        ],
        ambiguities: [],
        contradictions: [],
      },
      result_validation: {
        is_valid: false,
        status: 'BLOCKED',
        gate: 'NB01',
        stage: 'intake_completion',
        reasons: ['MVB_MISSING'],
      },
      debug_raw_json: false,
      setDebugRawJson: vi.fn(),
    });

    render(<PacketTab />);

    expect(screen.getByText(/Missing fields: Origin City/)).toBeInTheDocument();
    expect(screen.queryByText(/Prompt: Which city will the travelers depart from\?/)).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /view details/i }));

    expect(screen.getByText(/Prompt: Which city will the travelers depart from\?/)).toBeInTheDocument();
  });

  it('offers a direct trip-details repair path when a trip exists', () => {
    mockStore.mockReturnValue({
      result_packet: {
        facts: {},
        derived_signals: {},
        unknowns: [
          { field_name: 'origin_city', reason: 'missing', notes: null },
        ],
        ambiguities: [],
        contradictions: [],
      },
      result_validation: null,
      debug_raw_json: false,
      setDebugRawJson: vi.fn(),
    });

    render(
      <PacketTab
        trip={{
          id: 'trip-workbench-cta',
          destination: 'Bali',
          type: 'family leisure',
          state: 'green',
          age: '1h',
          createdAt: '2026-05-27T00:00:00Z',
          updatedAt: '2026-05-27T00:00:00Z',
          origin: '',
          budget: '₹4L',
          dateWindow: 'Jul 2026',
          party: 4,
        } as Trip}
      />
    );

    expect(screen.getByRole('link', { name: /open trip details/i })).toHaveAttribute(
      'href',
      '/trips/trip-workbench-cta/intake',
    );
  });

  it('uses the trip repair surface when packet data is still missing', () => {
    render(
      <PacketTab
        trip={{
          id: 'trip-missing-packet',
          destination: 'Bali',
          type: 'family leisure',
          state: 'green',
          age: '1h',
          createdAt: '2026-05-27T00:00:00Z',
          updatedAt: '2026-05-27T00:00:00Z',
          origin: 'Mumbai',
          budget: '₹4L',
          dateWindow: 'Jul 2026',
          party: 4,
        } as Trip}
      />
    );

    expect(screen.getByText(/No booking request data yet/i)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /open trip details/i })).toHaveAttribute(
      'href',
      '/trips/trip-missing-packet/intake',
    );
    expect(screen.queryByText(/New Inquiry/)).not.toBeInTheDocument();
  });

  it('shows group logistics when rooming and procurement details are captured', () => {
    mockStore.mockReturnValue({
      result_packet: {
        facts: {
          rooming_list_count: slot(2),
          procurement_share_needed: slot(true),
        },
        derived_signals: {},
        unknowns: [],
        ambiguities: [],
        contradictions: [],
      },
      result_validation: null,
      debug_raw_json: false,
      setDebugRawJson: vi.fn(),
    });

    render(<PacketTab />);

    expect(screen.getByText('Group Logistics')).toBeInTheDocument();
    expect(screen.getByText(/2 rooming lists/)).toBeInTheDocument();
    expect(screen.getByText(/Shareable with procurement/)).toBeInTheDocument();
  });

  it('prefers repaired trip fields over stale packet unknowns', () => {
    mockStore.mockReturnValue({
      result_packet: {
        facts: {},
        derived_signals: {},
        unknowns: [
          { field_name: 'origin_city', reason: 'missing', notes: null },
          { field_name: 'budget_raw_text', reason: 'missing', notes: null },
        ],
        ambiguities: [],
        contradictions: [],
      },
      result_validation: null,
      debug_raw_json: false,
      setDebugRawJson: vi.fn(),
    });

    render(
      <PacketTab
        trip={{
          id: 'trip-repaired',
          destination: 'Singapore',
          type: 'family leisure',
          state: 'green',
          age: '1h',
          createdAt: '2026-05-27T00:00:00Z',
          updatedAt: '2026-05-27T00:00:00Z',
          origin: 'Mumbai',
          budget: '₹4L',
          dateWindow: 'Dec 2026',
          party: 4,
        } as Trip}
      />
    );

    expect(screen.getAllByText('Mumbai').length).toBeGreaterThan(0);
    expect(screen.getAllByText('₹4L').length).toBeGreaterThan(0);
    expect(screen.queryByText(/Missing fields:/)).not.toBeInTheDocument();
    expect(screen.queryByText(/Origin City/i)).toBeInTheDocument();
  });

  it('renders system-defaulted assumptions with criticality and rationale (FND-0124)', () => {
    mockStore.mockReturnValue({
      result_packet: {
        facts: {
          budget_currency: slot('USD'),
        },
        derived_signals: {},
        unknowns: [],
        ambiguities: [],
        contradictions: [],
        assumptions: [
          {
            slot_name: 'budget_currency',
            assumed_value: 'USD',
            rationale: 'Value defaulted by system business rules — no explicit traveler input for budget_currency.',
            criticality: 'critical',
          },
          {
            slot_name: 'budget_flexibility',
            assumed_value: 'soft',
            rationale: 'Value defaulted by system business rules — no explicit traveler input for budget_flexibility.',
            criticality: 'advisory',
          },
        ],
      },
      result_validation: null,
      debug_raw_json: false,
      setDebugRawJson: vi.fn(),
    });

    render(<PacketTab />);

    expect(screen.getByText('Assumptions')).toBeInTheDocument();
    expect(screen.getAllByText('Budget Currency').length).toBeGreaterThan(0);
    expect(screen.getAllByText(/= USD/).length).toBeGreaterThan(0);
    expect(screen.getByText('Budget Flexibility')).toBeInTheDocument();
    expect(screen.getAllByText(/= soft/).length).toBeGreaterThan(0);
    expect(screen.getAllByText('critical').length).toBeGreaterThan(0);
    expect(screen.getAllByText('advisory').length).toBeGreaterThan(0);
    expect(screen.getByText(/no explicit traveler input for budget_currency/)).toBeInTheDocument();
  });

  it('renders no assumptions section when the packet carries none (FND-0124)', () => {
    mockStore.mockReturnValue({
      result_packet: {
        facts: {
          destination_candidates: slot(['Bali']),
        },
        derived_signals: {},
        unknowns: [],
        ambiguities: [],
        contradictions: [],
        // assumptions key absent entirely — mirrors pre-FND-0124 packets
      },
      result_validation: null,
      debug_raw_json: false,
      setDebugRawJson: vi.fn(),
    });

    render(<PacketTab />);

    expect(screen.queryByText('Assumptions')).not.toBeInTheDocument();
    expect(screen.getByText('Destinations')).toBeInTheDocument();
  });

  const assumptionPacket = (entry: Record<string, unknown>) => ({
    facts: {},
    derived_signals: {},
    unknowns: [],
    ambiguities: [],
    contradictions: [],
    assumptions: [
      {
        slot_name: 'budget_currency',
        assumed_value: 'USD',
        rationale: 'Value defaulted by system business rules — no explicit traveler input.',
        criticality: 'critical',
        acknowledged_by_operator: false,
        ...entry,
      },
    ],
  });

  function tripWithId(): Trip {
    return {
      id: 'trip-assumptions',
      destination: 'Bali',
      type: 'family leisure',
      state: 'green',
      age: '1h',
      createdAt: '2026-09-01T00:00:00Z',
      updatedAt: '2026-09-01T00:00:00Z',
      origin: 'Mumbai',
      budget: '₹4L',
      dateWindow: 'Mar 2027',
      party: 4,
    } as Trip;
  }

  it('confirms an assumption via the canonical PATCH and swaps in the refreshed packet', async () => {
    resolveAssumptionsMock.mockResolvedValue({
      id: 'trip-assumptions',
      packet: assumptionPacket({ acknowledged_by_operator: true, operator_notes: 'Confirmed by operator.' }),
    });
    // Emulate the zustand store: setResultPacket swaps the display packet.
    const storeState: Record<string, unknown> = {
      result_packet: assumptionPacket({}),
      result_validation: null,
      debug_raw_json: false,
      setDebugRawJson: vi.fn(),
    };
    storeState.setResultPacket = (value: unknown) => { storeState.result_packet = value; };
    mockStore.mockImplementation(() => storeState);

    const view = render(<PacketTab trip={tripWithId()} />);

    fireEvent.click(screen.getByRole('button', { name: 'Confirm' }));

    await waitFor(() => {
      expect(resolveAssumptionsMock).toHaveBeenCalledWith('trip-assumptions', [
        { slot_name: 'budget_currency' },
      ]);
    });
    await waitFor(() => {
      expect(storeState.result_packet).toEqual(
        expect.objectContaining({
          assumptions: [expect.objectContaining({ acknowledged_by_operator: true })],
        }),
      );
    });
    view.rerender(<PacketTab trip={tripWithId()} />);

    expect(screen.getByText(/Confirmed by operator\./)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Confirm' })).not.toBeInTheDocument();
  });

  it('corrects an assumption with an operator-supplied value', async () => {
    const setResultPacket = vi.fn();
    resolveAssumptionsMock.mockResolvedValue({ id: 'trip-assumptions', packet: null });
    mockStore.mockReturnValue({
      result_packet: assumptionPacket({}),
      result_validation: null,
      debug_raw_json: false,
      setDebugRawJson: vi.fn(),
      setResultPacket,
    });

    render(<PacketTab trip={tripWithId()} />);

    fireEvent.click(screen.getByRole('button', { name: /correct/i }));
    const input = screen.getByPlaceholderText('Corrected value');
    fireEvent.change(input, { target: { value: 'INR' } });
    fireEvent.click(screen.getByRole('button', { name: /save correction/i }));

    await waitFor(() => {
      expect(resolveAssumptionsMock).toHaveBeenCalledWith('trip-assumptions', [
        { slot_name: 'budget_currency', corrected_value: 'INR' },
      ]);
    });
  });

  it('shows an error message when the resolution fails', async () => {
    resolveAssumptionsMock.mockRejectedValue(new Error('network down'));
    mockStore.mockReturnValue({
      result_packet: assumptionPacket({}),
      result_validation: null,
      debug_raw_json: false,
      setDebugRawJson: vi.fn(),
      setResultPacket: vi.fn(),
    });

    render(<PacketTab trip={tripWithId()} />);

    fireEvent.click(screen.getByRole('button', { name: 'Confirm' }));

    await waitFor(() => {
      expect(screen.getByText(/could not save the assumption resolution/i)).toBeInTheDocument();
    });
  });

  it('renders reviewed entries without action buttons', () => {
    mockStore.mockReturnValue({
      result_packet: assumptionPacket({
        acknowledged_by_operator: true,
        operator_notes: 'Superseded by manual field correction — operator asserted the true value.',
      }),
      result_validation: null,
      debug_raw_json: false,
      setDebugRawJson: vi.fn(),
      setResultPacket: vi.fn(),
    });

    render(<PacketTab trip={tripWithId()} />);

    expect(screen.getByText(/Superseded by manual field correction/)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Confirm' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /correct/i })).not.toBeInTheDocument();
  });
});
