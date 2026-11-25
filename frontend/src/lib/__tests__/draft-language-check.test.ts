import { describe, expect, it } from 'vitest';
import { getDraftCheckStatus } from '../safety-review-copy';
import type { SafetyResult } from '@/types/spine';

const draft = { user_message: 'Which date works for the return flight?' };
const check: NonNullable<SafetyResult['draft_check']> = {
  version: 2, status: 'passed', digest_sha256: 'a'.repeat(64),
};
const safety: SafetyResult = { leakage_passed: true, draft_check: check };

describe('draft language status', () => {
  it('requires an explicit, recognized check and a current traveler draft', () => {
    expect(getDraftCheckStatus(safety, draft, 'ASK_FOLLOWUP')).toBe('passed');
    expect(getDraftCheckStatus(safety, draft, 'ASK_FOLLOWUP', true)).toBe('unchecked');
    expect(getDraftCheckStatus({ leakage_passed: true }, draft)).toBe('unchecked');
    expect(getDraftCheckStatus({ ...safety, draft_check: { ...check, digest_sha256: '' } }, draft)).toBe('unchecked');
    expect(getDraftCheckStatus(null, draft)).toBe('unchecked');
    const historical = { ...safety, draft_check: { ...check, version: 1 } } as unknown as SafetyResult;
    expect(getDraftCheckStatus(historical, draft)).toBe('unchecked');
  });

  it('keeps internal-only and missing drafts neutral', () => {
    expect(getDraftCheckStatus(safety, draft, 'PROCEED_INTERNAL_DRAFT')).toBe('no-draft');
    expect(getDraftCheckStatus(safety, draft, 'STOP_NEEDS_REVIEW')).toBe('no-draft');
    expect(getDraftCheckStatus(safety, { user_message: '  ' })).toBe('no-draft');
  });

  it('prioritizes a recorded issue over a pass or suppressed draft', () => {
    expect(getDraftCheckStatus({ ...safety, leakage_passed: false }, null)).toBe('failed');
    expect(getDraftCheckStatus({ ...safety, draft_check: { ...check, status: 'failed' } }, draft)).toBe('failed');
  });
});
