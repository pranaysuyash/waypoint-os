import type { SafetyResult } from '@/types/spine';

const DEFAULT_CLEANUP_STEPS = [
  'Remove system labels, scores, and field names from the customer reply.',
  'Keep operator notes and planning rationale in internal comments only.',
  'Run message review again after rewriting the customer-facing text.',
] as const;

function getLeakageCount(safety: SafetyResult | null | undefined): number {
  return Array.isArray(safety?.leakage_errors) ? safety.leakage_errors.length : 0;
}

function formatLeakageCount(count: number): string {
  if (count <= 0) return 'internal-only language';
  return count === 1 ? '1 internal-only reference' : `${count} internal-only references`;
}

export type DraftCheckStatus = 'passed' | 'failed' | 'pending' | 'unchecked' | 'no-draft';

export function getDraftCheckStatus(
  safety: SafetyResult | null,
  bundle: unknown,
  decision?: string | null,
  stale = false,
): DraftCheckStatus {
  if (safety?.leakage_passed === false || safety?.draft_check?.status === 'failed') return 'failed';
  const text = bundle && typeof bundle === 'object' && 'user_message' in bundle ? bundle.user_message : null;
  if (typeof text !== 'string' || !text.trim() || decision === 'PROCEED_INTERNAL_DRAFT' || decision === 'STOP_NEEDS_REVIEW') {
    return 'no-draft';
  }
  const check = safety?.draft_check;
  return !stale && safety?.leakage_passed === true && check?.version === 2
    && check.status === 'passed' && /^[a-f0-9]{64}$/.test(check.digest_sha256) ? 'passed' : 'unchecked';
}

export const DRAFT_CHECK_LABELS: Record<DraftCheckStatus, string> = {
  passed: 'Draft language checked',
  failed: 'Review flagged language',
  pending: 'Reassessing inquiry',
  unchecked: 'Draft check unavailable',
  'no-draft': 'No traveler draft',
};

export function getSafetyReviewStatusCopy(status: DraftCheckStatus, safety: SafetyResult | null): {
  heading: string;
  body: string;
} {
  switch (status) {
    case 'passed':
      return {
        heading: 'Draft passed the internal-language check',
        body: 'The check found no internal-only language in the reviewed draft. Read the wording before sending.',
      };
    case 'failed':
      return {
        heading: 'Review flagged language',
        body: `The language check flagged ${formatLeakageCount(getLeakageCount(safety))}. Review the details before sharing a reply.`,
      };
    case 'no-draft':
      return {
        heading: 'No traveler draft',
        body: 'This inquiry has no traveler-facing draft to review.',
      };
    case 'pending':
      return {
        heading: 'Reassessing inquiry',
        body: 'The draft check will update when this run finishes.',
      };
    case 'unchecked':
      return {
        heading: 'Draft check unavailable',
        body: 'Use Process Inquiry to generate and check a draft for the current inquiry.',
      };
  }
}

export function getSafetyCleanupChecklist(): readonly string[] {
  return DEFAULT_CLEANUP_STEPS;
}

export function getSafetyCleanupSummary(safety: SafetyResult | null | undefined): string {
  const leakageCount = getLeakageCount(safety);

  if (leakageCount <= 0) {
    return 'Internal-only language was detected in the customer-facing reply.';
  }

  return leakageCount === 1
    ? '1 internal-only reference detected in the customer-facing reply.'
    : `${leakageCount} internal-only references detected in the customer-facing reply.`;
}
