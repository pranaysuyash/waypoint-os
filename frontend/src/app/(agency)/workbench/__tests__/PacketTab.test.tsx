import { render, screen } from '@testing-library/react';
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
    expect(screen.getByText(/properties with long transfers \(internal only\)/)).toBeInTheDocument();
    expect(screen.getByText(/vegetarian food \(traveler safe transformable\)/)).toBeInTheDocument();
    expect(screen.getByText(/Value: family leisure; Source: message hints \(90%\)/)).toBeInTheDocument();
  });

  it('shows operator-friendly prompts for unknown fields', () => {
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
      result_validation: null,
      debug_raw_json: false,
      setDebugRawJson: vi.fn(),
    });

    render(<PacketTab />);

    expect(
      screen.getAllByText(/Prompt: Which city will the travelers depart from\?/).length,
    ).toBeGreaterThan(0);
  });
});
