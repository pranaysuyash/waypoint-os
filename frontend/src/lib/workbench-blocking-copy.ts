import type { RunStatusResponse, ValidationReport } from '@/types/spine';

export type WorkbenchBlockCopy = {
  title: string;
  summary: string;
  details: string[];
  actionLabel: string;
};

function humanizeReason(raw: string): string {
  const trimmed = raw.trim();
  if (!trimmed) return '';

  const normalized = trimmed.replace(/_/g, ' ').replace(/\s+/g, ' ').trim();
  const lowered = normalized.toLowerCase();

  if (lowered.includes('mvb missing') || lowered.includes('missing key trip details')) {
    return 'Some key trip details are missing';
  }

  if (lowered.includes('numeric budget required')) {
    return 'Budget details are needed for this request type';
  }

  if (lowered.includes('structural validation')) {
    return 'Trip details are incomplete';
  }

  if (lowered.includes('validation failed')) {
    return 'Validation failed';
  }

  if (lowered.includes('needs attention')) {
    return normalized;
  }

  return normalized;
}

function collectReasons(validation?: ValidationReport | null, runState?: RunStatusResponse | null): string[] {
  const reasons: string[] = [];
  const activeValidation = validation ?? runState?.validation ?? null;

  for (const reason of activeValidation?.reasons ?? []) {
    const text = humanizeReason(reason);
    if (text) reasons.push(text);
  }

  for (const error of activeValidation?.errors ?? []) {
    const text = `${error.field ? `${error.field}: ` : ''}${error.message}`.trim();
    if (text) reasons.push(humanizeReason(text));
  }

  if (runState?.block_reason) {
    const text = humanizeReason(runState.block_reason);
    if (text) reasons.push(text);
  }

  if (runState?.error_message) {
    const text = humanizeReason(runState.error_message);
    if (text) reasons.push(text);
  }

  return Array.from(new Set(reasons));
}

function needsTripDetailsLanguage(validation?: ValidationReport | null, reasons: string[] = []): boolean {
  const gate = `${validation?.gate ?? ''} ${validation?.stage ?? ''} ${validation?.legacy_gate ?? ''}`.toLowerCase();
  if (gate.includes('intake') || gate.includes('trip details')) return true;
  return reasons.some((reason) => /missing|incomplete|details|budget|dates|traveler|customer/i.test(reason));
}

export function getWorkbenchBlockCopy(args: {
  validation?: ValidationReport | null;
  runState?: RunStatusResponse | null;
}): WorkbenchBlockCopy {
  const reasons = collectReasons(args.validation, args.runState);
  const hasReasons = reasons.length > 0;
  const needsDetails = needsTripDetailsLanguage(args.validation, reasons);

  const title = needsDetails
    ? 'Trip Details Need Your Input'
    : args.validation?.status === 'BLOCKED' || args.runState?.state === 'blocked'
      ? 'Processing is blocked'
      : 'This run needs attention';

  const summary = hasReasons
    ? reasons[0]!
    : needsDetails
      ? 'This run is blocked until the missing trip details are filled in.'
      : 'This run is blocked until the next issue is resolved.';

  return {
    title,
    summary,
    details: hasReasons ? reasons : [],
    actionLabel: needsDetails ? 'Review Missing Fields' : 'Open Trip Details',
  };
}

export function formatWorkbenchBlockReasonList(reasons: string[] = []): string {
  return reasons.map(humanizeReason).filter(Boolean).join('; ');
}
