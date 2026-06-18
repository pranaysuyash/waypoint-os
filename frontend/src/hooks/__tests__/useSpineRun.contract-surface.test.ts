import { act, renderHook } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';
import { useSpineRun } from '../useSpineRun';
import * as apiClient from '@/lib/api-client';
import type { SpineRunRequest } from '@/types/spine';

vi.mock('@/lib/api-client');

describe('useSpineRun contract surface', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('preserves frontier_result from polled run status into hook state', async () => {
    vi.useFakeTimers();

    const request: SpineRunRequest = {
      raw_note: 'Need a trip to Lisbon',
      owner_note: null,
      structured_json: null,
      itinerary_text: null,
      stage: 'discovery',
      operating_mode: 'normal_intake',
      strict_leakage: false,
      scenario_id: null,
      draft_id: undefined,
      retention_consent: true,
    };

    vi.mocked(apiClient.api.post).mockResolvedValue({
      run_id: 'run-123',
      state: 'running',
    });

    vi.mocked(apiClient.api.get).mockResolvedValue({
      run_id: 'run-123',
      state: 'completed',
      trip_id: 'trip-999',
      stage: 'discovery',
      operating_mode: 'normal_intake',
      agency_id: null,
      started_at: '2026-06-17T10:00:00.000Z',
      completed_at: '2026-06-17T10:00:03.000Z',
      total_ms: 3000,
      created_at: '2026-06-17T10:00:00.000Z',
      steps_completed: ['packet', 'validation', 'decision'],
      events: [],
      validation: null,
      packet: null,
      frontier_result: {
        ghost_triggered: true,
        ghost_workflow_id: 'fw-7',
        sentiment_score: 0.91,
        anxiety_alert: false,
      },
    });

    const { result } = renderHook(() => useSpineRun());

    const runPromise = act(async () => {
      await result.current.execute(request);
    });

    await vi.advanceTimersByTimeAsync(2000);
    await runPromise;

    expect(result.current.state).toEqual(expect.objectContaining({
      state: 'completed',
      frontier_result: expect.objectContaining({
        ghost_triggered: true,
        ghost_workflow_id: 'fw-7',
        sentiment_score: 0.91,
      }),
    }));
    expect(vi.mocked(apiClient.api.post)).toHaveBeenCalledWith('/api/spine/run', request, expect.any(Object));
    expect(vi.mocked(apiClient.api.get)).toHaveBeenCalledWith('/api/runs/run-123');
  });
});
