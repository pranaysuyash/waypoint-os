import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@testing-library/react';
import type { ReactNode } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { useScenario } from '../useScenarios';
import { getScenario } from '@/lib/api-client';

vi.mock('@/lib/api-client', () => ({
  getScenarios: vi.fn(),
  getScenario: vi.fn(),
}));

function wrapper({ children }: { children: ReactNode }) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}

describe('useScenario', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('does not fetch without an id and fetches scenario details when enabled', async () => {
    const disabled = renderHook(() => useScenario(null), { wrapper });
    expect(disabled.result.current.data).toBeNull();
    expect(getScenario).not.toHaveBeenCalled();

    vi.mocked(getScenario).mockResolvedValueOnce({
      id: 'scenario-1',
      input: { raw_note: 'Need Bali', owner_note: null, structured_json: null, itinerary_text: null, stage: 'discovery', mode: 'normal_intake' },
      expected: { allowed_decision_states: ['PROCEED'], required_packet_fields: [], forbidden_traveler_terms: [], leakage_expected: false, assertions: [] },
    });

    const enabled = renderHook(() => useScenario('scenario-1'), { wrapper });
    await waitFor(() => expect(enabled.result.current.data?.id).toBe('scenario-1'));
    expect(getScenario).toHaveBeenCalledWith('scenario-1');
  });
});
