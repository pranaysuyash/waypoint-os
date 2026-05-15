import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import NextActionBanner, { computeNextAction } from '../NextActionBanner';
import type { BookingDocument } from '@/lib/api-client';
import type { ReadinessAssessment } from '@/types/spine';

let _docIdx = 0;
function doc(status: BookingDocument['status']): BookingDocument {
  return {
    id: `doc_${++_docIdx}`,
    trip_id: 'trip_1',
    traveler_id: null,
    uploaded_by_type: 'agent',
    document_type: 'passport',
    filename_present: true,
    filename_ext: 'pdf',
    mime_type: 'application/pdf',
    size_bytes: 1024,
    status,
    scan_status: 'clean',
    review_notes_present: false,
    created_at: '2026-05-14T00:00:00Z',
    updated_at: '2026-05-14T00:00:00Z',
    reviewed_at: null,
    reviewed_by: null,
  };
}

const NO_DOCS: BookingDocument[] = [];
const NO_READINESS = null;

const readinessWithMissing: ReadinessAssessment = {
  highest_ready_tier: 'intake_minimum',
  suggested_next_stage: 'booking',
  should_auto_advance_stage: false,
  missing_for_next: ['passport_number', 'date_of_birth'],
};

const readinessClean: ReadinessAssessment = {
  highest_ready_tier: 'proposal_ready',
  suggested_next_stage: '',
  should_auto_advance_stage: false,
  missing_for_next: [],
};

// ── computeNextAction unit tests ──────────────────────────────────────────────

describe('computeNextAction', () => {
  it('returns null when nothing needs attention', () => {
    expect(computeNextAction(null, NO_DOCS, readinessClean)).toBeNull();
  });

  it('returns null with undefined readiness and no docs', () => {
    expect(computeNextAction(null, NO_DOCS, undefined)).toBeNull();
  });

  it('returns urgent when pendingData is present', () => {
    const result = computeNextAction({ travelers: [] }, NO_DOCS, readinessClean);
    expect(result?.priority).toBe('urgent');
    expect(result?.message).toContain('submitted booking data');
  });

  it('pendingData takes priority over pending_review documents', () => {
    const result = computeNextAction(
      { travelers: [] },
      [doc('pending_review')],
      readinessClean,
    );
    expect(result?.priority).toBe('urgent');
  });

  it('returns attention for one pending_review document', () => {
    const result = computeNextAction(null, [doc('pending_review')], readinessClean);
    expect(result?.priority).toBe('attention');
    expect(result?.message).toContain('1 document awaiting review');
  });

  it('returns attention for multiple pending_review documents', () => {
    const result = computeNextAction(null, [doc('pending_review'), doc('pending_review')], readinessClean);
    expect(result?.priority).toBe('attention');
    expect(result?.message).toContain('2 documents awaiting review');
  });

  it('ignores accepted/rejected documents for attention rule', () => {
    const result = computeNextAction(
      null,
      [doc('accepted'), doc('rejected')],
      readinessClean,
    );
    expect(result).toBeNull();
  });

  it('returns info when missing_for_next is non-empty', () => {
    const result = computeNextAction(null, NO_DOCS, readinessWithMissing);
    expect(result?.priority).toBe('info');
    expect(result?.message).toContain('passport_number');
    expect(result?.message).toContain('date_of_birth');
  });

  it('pending_review documents take priority over missing_for_next', () => {
    const result = computeNextAction(null, [doc('pending_review')], readinessWithMissing);
    expect(result?.priority).toBe('attention');
  });

  it('returns null when missing_for_next is empty array', () => {
    expect(computeNextAction(null, NO_DOCS, readinessClean)).toBeNull();
  });
});

// ── NextActionBanner render tests ─────────────────────────────────────────────

describe('NextActionBanner', () => {
  it('shows fallback when no action needed', () => {
    render(<NextActionBanner pendingData={null} documents={NO_DOCS} readiness={readinessClean} />);
    const banner = screen.getByTestId('ops-next-action-banner');
    expect(banner).toBeInTheDocument();
    expect(banner).toHaveAttribute('data-priority', 'none');
    expect(banner.textContent).toContain('No urgent Ops action detected from available data');
  });

  it('renders urgent priority for pending submission', () => {
    render(
      <NextActionBanner
        pendingData={{ travelers: [] }}
        documents={NO_DOCS}
        readiness={readinessClean}
      />,
    );
    const banner = screen.getByTestId('ops-next-action-banner');
    expect(banner).toHaveAttribute('data-priority', 'urgent');
    expect(banner.textContent).toContain('Review and accept or reject');
  });

  it('renders attention priority for pending_review document', () => {
    render(
      <NextActionBanner
        pendingData={null}
        documents={[doc('pending_review')]}
        readiness={readinessClean}
      />,
    );
    const banner = screen.getByTestId('ops-next-action-banner');
    expect(banner).toHaveAttribute('data-priority', 'attention');
  });

  it('renders info priority for missing fields', () => {
    render(
      <NextActionBanner
        pendingData={null}
        documents={NO_DOCS}
        readiness={readinessWithMissing}
      />,
    );
    const banner = screen.getByTestId('ops-next-action-banner');
    expect(banner).toHaveAttribute('data-priority', 'info');
    expect(banner.textContent).toContain('passport_number');
  });
});
