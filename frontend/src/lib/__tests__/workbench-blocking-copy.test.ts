import { describe, expect, it } from 'vitest';
import type { RunStatusResponse } from '@/types/spine';
import { getWorkbenchBlockCopy } from '../workbench-blocking-copy';

describe('getWorkbenchBlockCopy', () => {
  it('turns validation blockers into clear trip-detail copy', () => {
    const copy = getWorkbenchBlockCopy({
      validation: {
        is_valid: false,
        status: 'BLOCKED',
        gate: 'NB01',
        stage: 'intake_completion',
        reasons: ['MVB_MISSING', 'NUMERIC_BUDGET_REQUIRED'],
      },
    });

    expect(copy.title).toContain('Trip Details');
    expect(copy.summary).toMatch(/key trip details|Budget details/);
    expect(copy.details).toEqual([
      'Some key trip details are missing',
      'Budget details are needed for this request type',
    ]);
    expect(copy.actionLabel).toBe('Review Missing Fields');
  });

  it('uses run block reasons when validation is absent', () => {
    const copy = getWorkbenchBlockCopy({
      runState: {
        run_id: 'run_1',
        state: 'blocked',
        trip_id: null,
        stage: 'validation',
        operating_mode: 'normal_intake',
        agency_id: null,
        started_at: null,
        completed_at: null,
        total_ms: null,
        created_at: null,
        steps_completed: [],
        events: [],
        block_reason: 'Structural validation failed',
      } as RunStatusResponse,
    });

    expect(copy.title).toContain('Trip Details');
    expect(copy.summary).toBe('Trip details are incomplete');
    expect(copy.details).toEqual(['Trip details are incomplete']);
  });

  it('reads validation embedded on the run status payload', () => {
    const copy = getWorkbenchBlockCopy({
      runState: {
        run_id: 'run_2',
        state: 'blocked',
        trip_id: null,
        stage: 'validation',
        operating_mode: 'normal_intake',
        agency_id: null,
        started_at: null,
        completed_at: null,
        total_ms: null,
        created_at: null,
        steps_completed: [],
        events: [],
        validation: {
          is_valid: false,
          status: 'BLOCKED',
          gate: 'NB01',
          stage: 'intake_completion',
          reasons: ['MVB_MISSING'],
        },
      } as RunStatusResponse,
    });

    expect(copy.title).toContain('Trip Details');
    expect(copy.summary).toBe('Some key trip details are missing');
    expect(copy.details).toEqual(['Some key trip details are missing']);
  });
});
