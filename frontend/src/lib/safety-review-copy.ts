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

export function getSafetyReviewStatusCopy(safety: SafetyResult | null | undefined): {
  heading: string;
  body: string;
} {
  if (safety?.leakage_passed) {
    return {
      heading: 'Ready for customer review',
      body: 'The current reply is free of internal notes and system-only language.',
    };
  }

  const leakageCount = getLeakageCount(safety);

  return {
    heading: 'Rewrite customer message before sending',
    body: `We found ${formatLeakageCount(leakageCount)} in the outgoing customer reply. Clean up the wording and run review again before sending.`,
  };
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
