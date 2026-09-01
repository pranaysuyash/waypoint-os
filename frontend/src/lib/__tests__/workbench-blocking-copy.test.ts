import { describe, expect, it } from 'vitest';
import type { RunStatusResponse } from '@/types/spine';
import { getWorkbenchBlockCopy, formatWorkbenchMissingFields } from '../workbench-blocking-copy';

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
    expect(copy.actionLabel).toBe('Open Trip Details');
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

describe('formatWorkbenchMissingFields', () => {
  it('derives missing fields from packet unknowns for the banner', () => {
    const copy = getWorkbenchBlockCopy({
      validation: { status: 'ESCALATED', reasons: ['Trip details are incomplete'] },
      packet: {
        unknowns: [
          { field_name: 'date_window' },
          { field_name: 'trip_purpose' },
        ],
      },
    });

    expect(copy.missingFields).toEqual(['date_window', 'trip_purpose']);
  });

  it('returns no missing fields without a packet', () => {
    const copy = getWorkbenchBlockCopy({
      validation: { status: 'ESCALATED', reasons: ['Trip details are incomplete'] },
    });
    expect(copy.missingFields).toEqual([]);
  });
});

describe('formatWorkbenchMissingFields', () => {
  it('labels fields and caps at 3 with overflow', () => {
    expect(formatWorkbenchMissingFields(['date_window', 'trip_purpose'])).toBe('Travel Dates, Trip Purpose');
    expect(formatWorkbenchMissingFields(['date_window', 'trip_purpose', 'party_size', 'origin_city'])).toBe(
      'Travel Dates, Trip Purpose, Party Size +1 more',
    );
    expect(formatWorkbenchMissingFields([])).toBe('');
  });
});
