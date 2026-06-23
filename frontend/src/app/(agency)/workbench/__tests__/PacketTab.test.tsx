import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import PacketTab from '../PacketTab';

const mockStore = vi.fn();

vi.mock('@/stores/workbench', () => ({
  useWorkbenchStore: () => mockStore(),
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
});
