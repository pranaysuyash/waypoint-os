'use client';

import { useState, useEffect, useCallback } from 'react';
import { useWorkbenchStore } from '@/stores/workbench';
import { ClientDateTime } from '@/hooks/useClientDate';
import {
  type Trip,
  type BookingData,
  type BookingTraveler,
  type PaymentStatus,
  type PaymentTracking,
  type RefundStatus,
  type CollectionLinkInfo,
  type CollectionLinkStatus,
  type PendingBookingDataResponse,
  type BookingDocument,
  getBookingData,
  updateBookingData,
  generateCollectionLink,
  getCollectionLink,
  revokeCollectionLink,
  getPendingBookingData,
  acceptPendingBookingData,
  rejectPendingBookingData,
  getDocuments,
  uploadDocument,
  acceptDocument,
  rejectDocument,
  deleteDocument,
  getDocumentDownloadUrl,
  type ExtractionResponse,
  extractDocument,
  getExtraction,
  applyExtraction,
  rejectExtraction,
} from '@/lib/api-client';
import { ExtractionHistoryPanel } from '@/components/workspace/panels/ExtractionHistoryPanel';
import BookingExecutionPanel from '@/components/workspace/panels/BookingExecutionPanel';
import ConfirmationPanel from '@/components/workspace/panels/ConfirmationPanel';
import ExecutionTimelinePanel from '@/components/workspace/panels/ExecutionTimelinePanel';
import type { ReadinessAssessment } from '@/types/spine';

interface OpsPanelProps {
  trip?: Trip | null;
  mode?: 'full' | 'documents';
}

function emptyTraveler(): BookingTraveler {
  return { traveler_id: '', full_name: '', date_of_birth: '' };
}

type PaymentTrackingDraft = {
  agreed_amount: string;
  currency: string;
  amount_paid: string;
  payment_status: PaymentStatus;
  payment_method: string;
  payment_reference: string;
  payment_proof_url: string;
  refund_status: RefundStatus;
  refund_amount_agreed: string;
  refund_method: string;
  refund_reference: string;
  refund_paid_by_agency: boolean;
  notes: string;
};

const EMPTY_PAYMENT_DRAFT: PaymentTrackingDraft = {
  agreed_amount: '',
  currency: 'INR',
  amount_paid: '',
  payment_status: 'unknown',
  payment_method: '',
  payment_reference: '',
  payment_proof_url: '',
  refund_status: 'not_applicable',
  refund_amount_agreed: '',
  refund_method: '',
  refund_reference: '',
  refund_paid_by_agency: false,
  notes: '',
};

const PAYMENT_STATUSES: PaymentStatus[] = [
  'unknown',
  'not_started',
  'deposit_paid',
  'partially_paid',
  'paid',
  'overdue',
  'waived',
  'refunded',
];

const REFUND_STATUSES: RefundStatus[] = [
  'not_applicable',
  'not_requested',
  'pending_review',
  'approved',
  'processing',
  'paid',
  'rejected',
  'cancelled',
];

function formatLabel(value: string): string {
  return value.replaceAll('_', ' ');
}

function formatMoney(amount?: number | null, currency = 'INR'): string {
  if (amount == null || Number.isNaN(amount)) return '-';
  return `${currency} ${amount.toLocaleString('en-IN', { maximumFractionDigits: 2 })}`;
}

function paymentTrackingToDraft(payment?: PaymentTracking | null): PaymentTrackingDraft {
  if (!payment) return { ...EMPTY_PAYMENT_DRAFT };
  return {
    agreed_amount: payment.agreed_amount == null ? '' : String(payment.agreed_amount),
    currency: payment.currency || 'INR',
    amount_paid: payment.amount_paid == null ? '' : String(payment.amount_paid),
    payment_status: payment.payment_status || 'unknown',
    payment_method: payment.payment_method || '',
    payment_reference: payment.payment_reference || '',
    payment_proof_url: payment.payment_proof_url || '',
    refund_status: payment.refund_status || 'not_applicable',
    refund_amount_agreed: payment.refund_amount_agreed == null ? '' : String(payment.refund_amount_agreed),
    refund_method: payment.refund_method || '',
    refund_reference: payment.refund_reference || '',
    refund_paid_by_agency: Boolean(payment.refund_paid_by_agency),
    notes: payment.notes || '',
  };
}

function parseAmount(value: string): number | null {
  if (!value.trim()) return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function hasPaymentDraft(draft: PaymentTrackingDraft): boolean {
  return Boolean(
    draft.agreed_amount.trim() ||
    draft.amount_paid.trim() ||
    draft.payment_status !== 'unknown' ||
    draft.payment_method.trim() ||
    draft.payment_reference.trim() ||
    draft.payment_proof_url.trim() ||
    draft.refund_status !== 'not_applicable' ||
    draft.refund_amount_agreed.trim() ||
    draft.refund_method.trim() ||
    draft.refund_reference.trim() ||
    draft.refund_paid_by_agency ||
    draft.notes.trim(),
  );
}

function paymentDraftToTracking(draft: PaymentTrackingDraft): PaymentTracking | null {
  if (!hasPaymentDraft(draft)) return null;
  return {
    agreed_amount: parseAmount(draft.agreed_amount),
    currency: draft.currency.trim().toUpperCase() || 'INR',
    amount_paid: parseAmount(draft.amount_paid),
    payment_status: draft.payment_status,
    payment_method: draft.payment_method.trim() || null,
    payment_reference: draft.payment_reference.trim() || null,
    payment_proof_url: draft.payment_proof_url.trim() || null,
    refund_status: draft.refund_status,
    refund_amount_agreed: parseAmount(draft.refund_amount_agreed),
    refund_method: draft.refund_method.trim() || null,
    refund_reference: draft.refund_reference.trim() || null,
    refund_paid_by_agency: draft.refund_paid_by_agency,
    notes: draft.notes.trim() || null,
    tracking_only: true,
  };
}

// react-doctor-disable-next-line react-doctor/prefer-useReducer — 34+ state vars are independent slices; useReducer would add complexity without benefit
export default function OpsPanel({ trip, mode = 'full' }: OpsPanelProps) {
  const documentsOnly = mode === 'documents';
  const { result_validation } = useWorkbenchStore();

  const readiness: ReadinessAssessment | undefined =
    (result_validation as { readiness?: ReadinessAssessment } | null)?.readiness ??
    (trip?.validation as { readiness?: ReadinessAssessment } | null)?.readiness;

  // Booking data - local state only, not in global store
  const [bookingData, setBookingData] = useState<BookingData | null>(null);
  const [updatedAt, setUpdatedAt] = useState<string | null>(null);
  const [bookingDataSource, setBookingDataSource] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [conflict, setConflict] = useState(false);
  const [editing, setEditing] = useState(false);
  const [editTravelers, setEditTravelers] = useState<BookingTraveler[]>([emptyTraveler()]);
  const [editPayerName, setEditPayerName] = useState('');
  const [editPaymentTracking, setEditPaymentTracking] = useState<PaymentTrackingDraft>(EMPTY_PAYMENT_DRAFT);

  // Collection link state
  const [linkStatus, setLinkStatus] = useState<CollectionLinkStatus | null>(null);
  const [linkInfo, setLinkInfo] = useState<CollectionLinkInfo | null>(null);
  const [linkLoading, setLinkLoading] = useState(false);
  const [linkGenerating, setLinkGenerating] = useState(false);
  const [linkCopied, setLinkCopied] = useState(false);
  const [linkError, setLinkError] = useState<string | null>(null);

  // Pending booking data state
  const [pendingData, setPendingData] = useState<BookingData | null>(null);
  const [pendingLoading, setPendingLoading] = useState(false);
  const [accepting, setAccepting] = useState(false);
  const [rejecting, setRejecting] = useState(false);
  const [pendingError, setPendingError] = useState<string | null>(null);

  // Document state (Phase 4B)
  const [documents, setDocuments] = useState<BookingDocument[]>([]);
  const [docsLoading, setDocsLoading] = useState(false);
  const [docUploading, setDocUploading] = useState(false);
  const [docError, setDocError] = useState<string | null>(null);
  const [uploadDocType, setUploadDocType] = useState<string>('passport');
  const [docActionLoading, setDocActionLoading] = useState<string | null>(null);

  // Extraction state (Phase 4C)
  const [extractions, setExtractions] = useState<Record<string, ExtractionResponse>>({});
  const [extractingDocId, setExtractingDocId] = useState<string | null>(null);
  const [extractionAction, setExtractionAction] = useState<string | null>(null);
  const [extractionError, setExtractionError] = useState<string | null>(null);
  // Per-extraction apply selections
  const [extractionSelections, setExtractionSelections] = useState<Record<string, {
    travelerId: string;
    selectedFields: string[];
  }>>({});
  // Conflict state - shown until user confirms overwrite
  const [extractionConflicts, setExtractionConflicts] = useState<Record<string, Array<{
    field_name: string;
    existing_value: string;
    extracted_value: string;
  }>>>({});

  // Lazy fetch booking data
  const fetchBookingData = useCallback(async () => {
    if (!trip?.id) return;
    setLoading(true);
    setError(null);
    try {
      const resp = await getBookingData(trip.id);
      setBookingData(resp.booking_data);
      setUpdatedAt(resp.updated_at);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load booking data');
    } finally {
      setLoading(false);
    }
  }, [trip?.id]);

  useEffect(() => {
    if (trip?.id) fetchBookingData();
  }, [trip?.id, fetchBookingData]);

  // Lazy fetch collection link + pending data at proposal/booking stage
  const stage = trip?.stage;
  const canGenerateLink = stage === 'proposal' || stage === 'booking';

  // react-doctor-disable-next-line react-doctor/no-cascading-set-state — independent state updates for unrelated UI concerns
  useEffect(() => {
    if (!trip?.id || !canGenerateLink) return;

    let cancelled = false;
    (async () => {
      // Fetch link status (no URL - just has_active_token + expires_at)
      setLinkLoading(true);
      try {
        const status = await getCollectionLink(trip.id);
        if (!cancelled) setLinkStatus(status);
      } catch {
        // No active link is fine - 404 expected
      } finally {
        if (!cancelled) setLinkLoading(false);
      }

      // Fetch pending data
      setPendingLoading(true);
      try {
        const resp = await getPendingBookingData(trip.id);
        if (!cancelled) {
          setPendingData(resp.pending_booking_data);
          setBookingDataSource(resp.booking_data_source);
        }
      } catch {
        // No pending data is fine
      } finally {
        if (!cancelled) setPendingLoading(false);
      }
    })();

    return () => { cancelled = true; };
  }, [trip?.id, canGenerateLink]);

  // Fetch documents
  const fetchDocuments = useCallback(async () => {
    if (!trip?.id) return;
    setDocsLoading(true);
    try {
      const resp = await getDocuments(trip.id);
      setDocuments(resp.documents);
    } catch {
      // No documents is fine
    } finally {
      setDocsLoading(false);
    }
  }, [trip?.id]);

  useEffect(() => {
    if (trip?.id) fetchDocuments();
  }, [trip?.id, fetchDocuments]);

  // Start editing
  const startEdit = useCallback(() => {
    if (bookingData) {
      setEditTravelers(bookingData.travelers.map((t) => ({ ...t })));
      setEditPayerName(bookingData.payer?.name ?? '');
      setEditPaymentTracking(paymentTrackingToDraft(bookingData.payment_tracking));
    } else {
      setEditTravelers([emptyTraveler()]);
      setEditPayerName('');
      setEditPaymentTracking({ ...EMPTY_PAYMENT_DRAFT });
    }
    setEditing(true);
    setConflict(false);
    setError(null);
  }, [bookingData]);

  // Save
  const handleSave = useCallback(async () => {
    if (!trip?.id) return;
    const data: BookingData = {
      travelers: editTravelers,
      payer: editPayerName ? { name: editPayerName } : null,
      special_requirements: bookingData?.special_requirements ?? null,
      booking_notes: bookingData?.booking_notes ?? null,
      payment_tracking: paymentDraftToTracking(editPaymentTracking),
    };
    setSaving(true);
    setError(null);
    setConflict(false);
    try {
      const resp = await updateBookingData(trip.id, data, undefined, updatedAt ?? undefined);
      setBookingData(resp.booking_data);
      setUpdatedAt(resp.updated_at);
      setBookingDataSource('agent');
      setEditing(false);
    } catch (e: unknown) {
      if (e instanceof Error && 'status' in e && (e as { status?: number }).status === 409) {
        setConflict(true);
      } else {
        setError(e instanceof Error ? e.message : 'Failed to save booking data');
      }
    } finally {
      setSaving(false);
    }
  }, [trip?.id, editTravelers, editPayerName, bookingData, editPaymentTracking, updatedAt]);

  // Generate collection link (always creates new, revokes old active)
  const handleGenerateLink = useCallback(async () => {
    if (!trip?.id) return;
    setLinkGenerating(true);
    setLinkError(null);
    try {
      const info = await generateCollectionLink(trip.id);
      setLinkInfo(info);
      setLinkStatus({
        has_active_token: true,
        token_id: info.token_id,
        expires_at: info.expires_at,
        status: info.status,
        has_pending_submission: false,
      });
    } catch (e) {
      setLinkError(e instanceof Error ? e.message : 'Failed to generate link');
    } finally {
      setLinkGenerating(false);
    }
  }, [trip?.id]);

  // Revoke collection link
  const handleRevokeLink = useCallback(async () => {
    if (!trip?.id) return;
    setLinkError(null);
    try {
      await revokeCollectionLink(trip.id);
      setLinkInfo(null);
      setLinkStatus(null);
    } catch (e) {
      setLinkError(e instanceof Error ? e.message : 'Failed to revoke link');
    }
  }, [trip?.id]);

  // Copy link
  const handleCopyLink = useCallback(() => {
    if (!linkInfo?.collection_url) return;
    navigator.clipboard.writeText(linkInfo.collection_url).then(() => {
      setLinkCopied(true);
      setTimeout(() => setLinkCopied(false), 2000);
    });
  }, [linkInfo?.collection_url]);

  // Accept pending
  const handleAccept = useCallback(async () => {
    if (!trip?.id) return;
    setAccepting(true);
    setPendingError(null);
    try {
      await acceptPendingBookingData(trip.id);
      setPendingData(null);
      setBookingDataSource('customer_accepted');
      await fetchBookingData();
    } catch (e) {
      setPendingError(e instanceof Error ? e.message : 'Failed to accept');
    } finally {
      setAccepting(false);
    }
  }, [trip?.id, fetchBookingData]);

  // Reject pending
  const handleReject = useCallback(async () => {
    if (!trip?.id) return;
    setRejecting(true);
    setPendingError(null);
    try {
      await rejectPendingBookingData(trip.id);
      setPendingData(null);
    } catch (e) {
      setPendingError(e instanceof Error ? e.message : 'Failed to reject');
    } finally {
      setRejecting(false);
    }
  }, [trip?.id]);

  // Document upload handler
  const handleDocUpload = useCallback(async () => {
    if (!trip?.id) return;
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.pdf,.jpg,.jpeg,.png';
    input.onchange = async (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (!file) return;
      setDocUploading(true);
      setDocError(null);
      try {
        await uploadDocument(trip.id, file, uploadDocType);
        await fetchDocuments();
      } catch (e) {
        setDocError(e instanceof Error ? e.message : 'Upload failed');
      } finally {
        setDocUploading(false);
      }
    };
    input.click();
  }, [trip?.id, uploadDocType, fetchDocuments]);

  // Document download handler
  const handleDocDownload = useCallback(async (docId: string) => {
    if (!trip?.id) return;
    try {
      const { url } = await getDocumentDownloadUrl(trip.id, docId);
      const fullUrl = url.startsWith('/') ? `${window.location.origin}${url}` : url;
      window.open(fullUrl, '_blank');
    } catch {
      setDocError('Failed to get download URL');
    }
  }, [trip?.id]);

  // Document accept/reject/delete handlers
  const handleDocAccept = useCallback(async (docId: string) => {
    if (!trip?.id) return;
    setDocActionLoading(docId);
    try {
      await acceptDocument(trip.id, docId);
      await fetchDocuments();
    } catch (e) {
      setDocError(e instanceof Error ? e.message : 'Accept failed');
    } finally {
      setDocActionLoading(null);
    }
  }, [trip?.id, fetchDocuments]);

  const handleDocReject = useCallback(async (docId: string) => {
    if (!trip?.id) return;
    setDocActionLoading(docId);
    try {
      await rejectDocument(trip.id, docId);
      await fetchDocuments();
    } catch (e) {
      setDocError(e instanceof Error ? e.message : 'Reject failed');
    } finally {
      setDocActionLoading(null);
    }
  }, [trip?.id, fetchDocuments]);

  const handleDocDelete = useCallback(async (docId: string) => {
    if (!trip?.id) return;
    setDocActionLoading(docId);
    try {
      await deleteDocument(trip.id, docId);
      await fetchDocuments();
    } catch (e) {
      setDocError(e instanceof Error ? e.message : 'Delete failed');
    } finally {
      setDocActionLoading(null);
    }
  }, [trip?.id, fetchDocuments]);

  // Phase 4C: Extraction handlers
  const handleExtract = useCallback(async (docId: string) => {
    if (!trip?.id) return;
    setExtractingDocId(docId);
    setExtractionError(null);
    try {
      const resp = await extractDocument(trip.id, docId);
      setExtractions((prev) => ({ ...prev, [docId]: resp }));
    } catch (e) {
      setExtractionError(e instanceof Error ? e.message : 'Extraction failed');
    } finally {
      setExtractingDocId(null);
    }
  }, [trip?.id]);

  const handleApplyExtraction = useCallback(async (docId: string, travelerId: string, fields: string[], allowOverwrite = false) => {
    if (!trip?.id) return;
    setExtractionAction(docId);
    setExtractionError(null);
    try {
      const resp = await applyExtraction(trip.id, docId, {
        traveler_id: travelerId,
        fields_to_apply: fields,
        allow_overwrite: allowOverwrite,
      });
      if (resp.applied) {
        if (resp.extraction) {
          setExtractions((prev) => ({ ...prev, [docId]: resp.extraction! }));
        }
        setExtractionConflicts((prev) => { const n = { ...prev }; delete n[docId]; return n; });
      } else if (resp.conflicts.length > 0) {
        setExtractionConflicts((prev) => ({ ...prev, [docId]: resp.conflicts }));
      }
    } catch (e) {
      setExtractionError(e instanceof Error ? e.message : 'Apply failed');
    } finally {
      setExtractionAction(null);
    }
  }, [trip?.id]);

  const handleRejectExtraction = useCallback(async (docId: string) => {
    if (!trip?.id) return;
    setExtractionAction(docId);
    setExtractionError(null);
    try {
      const resp = await rejectExtraction(trip.id, docId);
      setExtractions((prev) => ({ ...prev, [docId]: resp }));
    } catch (e) {
      setExtractionError(e instanceof Error ? e.message : 'Reject failed');
    } finally {
      setExtractionAction(null);
    }
  }, [trip?.id]);

  if (!documentsOnly && !readiness) {
    return (
      <div data-testid="ops-panel-empty" className="text-sm text-[#8b949e]">
        No readiness data available. Run the pipeline to generate a readiness assessment.
      </div>
    );
  }

  const tiers = readiness?.tiers ?? {};
  const tierEntries = Object.entries(tiers);
  const signals = readiness?.signals;
  const signalRecord =
    signals && typeof signals === "object" && !Array.isArray(signals)
      ? (signals as Record<string, unknown>)
      : null;

  return (
    <div data-testid="ops-panel" className="space-y-6">
      {/* Highest tier summary */}
      {!documentsOnly && (
        <div className="flex items-center gap-3">
          <span className="text-sm text-[#8b949e]">Highest ready tier:</span>
          <span
            data-testid="ops-highest-tier"
            className="text-sm font-medium text-[#e6edf3]"
          >
            {readiness?.highest_ready_tier ?? 'none'}
          </span>
        </div>
      )}

      {/* Tier details */}
      {!documentsOnly && tierEntries.length > 0 && (
        <div data-testid="ops-tiers" className="space-y-4">
          <h3 className="text-sm font-medium text-[#e6edf3]">Booking Readiness Tiers</h3>
          {tierEntries.map((entry) => {
            const [name, tier] = entry;
            return (
            <div
              key={name}
              data-testid={`ops-tier-${name}`}
              className="border border-[#30363d] rounded-lg p-4"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-[#e6edf3]">
                  {name.replace(/_/g, ' ')}
                </span>
                <span
                  className={`text-xs px-2 py-0.5 rounded ${
                    tier.ready
                      ? 'bg-emerald-900/50 text-emerald-400'
                      : 'bg-red-900/50 text-red-400'
                  }`}
                >
                  {tier.ready ? 'Ready' : 'Not ready'}
                </span>
              </div>
              {tier.met.length > 0 && (
                <div className="mb-1">
                  <span className="text-xs text-[#8b949e]">Met: </span>
                  <span className="text-xs text-emerald-400">{tier.met.join(', ')}</span>
                </div>
              )}
              {tier.unmet.length > 0 && (
                <div>
                  <span className="text-xs text-[#8b949e]">Missing: </span>
                  <span className="text-xs text-red-400">{tier.unmet.join(', ')}</span>
                </div>
              )}
            </div>
          );
          })}
        </div>
      )}

      {/* Missing for next stage */}
      {!documentsOnly && readiness?.missing_for_next.length && readiness.missing_for_next.length > 0 && (
        <div data-testid="ops-missing" className="border border-[#30363d] rounded-lg p-4">
          <span className="text-xs text-[#8b949e]">Fields blocking next tier: </span>
          <span className="text-xs text-amber-400">
            {readiness.missing_for_next.join(', ')}
          </span>
        </div>
      )}

      {/* Auxiliary signals */}
      {!documentsOnly && signalRecord && Object.keys(signalRecord).length > 0 && (
        <div data-testid="ops-signals" className="border border-[#30363d] rounded-lg p-4">
          <h4 className="text-sm font-medium text-[#e6edf3] mb-2">Signals</h4>
          {signalRecord.visa_concerns_present === true && (
            <div
              data-testid="ops-signal-visa-concern"
              className="flex items-center gap-2 text-sm"
            >
              <span className="text-amber-400">Visa/Passport concern detected</span>
              <span className="text-xs text-[#8b949e]">
                Traveler input mentions visa or passport topics. Review may be needed.
              </span>
            </div>
          )}
        </div>
      )}

      {/* Pending submission review - shown when customer has submitted data */}
      {!documentsOnly && pendingLoading && (
        <div data-testid="ops-pending-loading" className="border border-[#30363d] rounded-lg p-4">
          <span className="text-xs text-[#8b949e]">Checking for customer submissions…</span>
        </div>
      )}

      {!documentsOnly && !pendingLoading && pendingData && (
        <div data-testid="ops-pending-review" className="border border-amber-800/50 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-3">
            <h4 className="text-sm font-medium text-[#e6edf3]">Customer Submission</h4>
            <span className="text-xs px-2 py-0.5 rounded bg-amber-900/50 text-amber-400">
              Submitted by customer
            </span>
          </div>

          {pendingError && (
            <div data-testid="ops-pending-error" className="mb-3 text-xs text-red-400">{pendingError}</div>
          )}

          <table className="w-full text-xs mb-3">
            <thead>
              <tr className="text-[#8b949e]">
                <th className="text-left py-1">ID</th>
                <th className="text-left py-1">Name</th>
                <th className="text-left py-1">DOB</th>
                <th className="text-left py-1">Passport</th>
              </tr>
            </thead>
            <tbody>
              {pendingData.travelers.map((t) => (
                <tr key={t.traveler_id} className="text-[#e6edf3]">
                  <td className="py-1">{t.traveler_id}</td>
                  <td className="py-1">{t.full_name}</td>
                  <td className="py-1">{t.date_of_birth}</td>
                  <td className="py-1">{t.passport_number || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {pendingData.payer && (
            <div className="mb-3 text-xs text-[#8b949e]">
              Payer: <span className="text-[#e6edf3]">{pendingData.payer.name}</span>
            </div>
          )}

          <div className="flex gap-2">
            <button
              data-testid="ops-accept-btn"
              className="text-xs px-3 py-1 rounded bg-emerald-900/50 text-emerald-300 hover:bg-emerald-800/50 disabled:opacity-50"
              onClick={handleAccept}
              disabled={accepting}
            >
              {accepting ? 'Accepting…' : 'Accept'}
            </button>
            <button
              data-testid="ops-reject-btn"
              className="text-xs px-3 py-1 rounded bg-red-900/50 text-red-300 hover:bg-red-800/50 disabled:opacity-50"
              onClick={handleReject}
              disabled={rejecting}
            >
              {rejecting ? 'Rejecting…' : 'Reject'}
            </button>
          </div>
        </div>
      )}

      {/* Booking data section */}
      {!documentsOnly && (
      <div data-testid="ops-booking-data" className="border border-[#30363d] rounded-lg p-4">
        <div className="flex items-center gap-2 mb-3">
          <h4 className="text-sm font-medium text-[#e6edf3]">Booking Details</h4>
          {bookingDataSource && (
            <span
              data-testid="ops-source-badge"
              className={`text-xs px-2 py-0.5 rounded ${
                bookingDataSource === 'customer_accepted'
                  ? 'bg-blue-900/50 text-blue-300'
                  : 'bg-[#30363d] text-[#8b949e]'
              }`}
            >
              {bookingDataSource === 'customer_accepted' ? 'Customer (verified)' : 'Agent'}
            </span>
          )}
        </div>

        {loading && <span className="text-xs text-[#8b949e]">Loading…</span>}

        {conflict && (
          <div data-testid="ops-conflict" className="mb-3 text-xs text-amber-400">
            This data was updated by another session.{' '}
            <button
              className="underline"
              onClick={() => { setConflict(false); fetchBookingData(); }}
            >
              Reload
            </button>
          </div>
        )}

        {error && !conflict && (
          <div data-testid="ops-error" className="mb-3 text-xs text-red-400">{error}</div>
        )}

        {!loading && !editing && bookingData && (
          <div data-testid="ops-traveler-table">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-[#8b949e]">
                  <th className="text-left py-1">ID</th>
                  <th className="text-left py-1">Name</th>
                  <th className="text-left py-1">DOB</th>
                  <th className="text-left py-1">Passport</th>
                </tr>
              </thead>
              <tbody>
                {bookingData.travelers.map((t) => (
                  <tr key={t.traveler_id} className="text-[#e6edf3]">
                    <td className="py-1">{t.traveler_id}</td>
                    <td className="py-1">{t.full_name}</td>
                    <td className="py-1">{t.date_of_birth}</td>
                    <td className="py-1">{t.passport_number || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {bookingData.payer && (
              <div className="mt-2 text-xs text-[#8b949e]">
                Payer: <span className="text-[#e6edf3]">{bookingData.payer.name}</span>
              </div>
            )}
            {bookingData.payment_tracking && (
              <div
                data-testid="ops-payment-tracking"
                className="mt-3 border border-[#30363d] rounded p-3 text-xs"
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="font-medium text-[#e6edf3]">Payment & refund tracking</span>
                  <span className="rounded bg-blue-950/40 px-2 py-0.5 text-blue-300">Status-only tracking</span>
                </div>
                <div className="mt-3 grid grid-cols-2 gap-2 text-[#8b949e] sm:grid-cols-4">
                  <div>
                    <div>Agreed</div>
                    <div className="text-[#e6edf3]">
                      {formatMoney(bookingData.payment_tracking.agreed_amount, bookingData.payment_tracking.currency || 'INR')}
                    </div>
                  </div>
                  <div>
                    <div>Paid</div>
                    <div className="text-[#e6edf3]">
                      {formatMoney(bookingData.payment_tracking.amount_paid, bookingData.payment_tracking.currency || 'INR')}
                    </div>
                  </div>
                  <div>
                    <div>Balance due</div>
                    <div className="text-[#e6edf3]">
                      {formatMoney(bookingData.payment_tracking.balance_due, bookingData.payment_tracking.currency || 'INR')}
                    </div>
                  </div>
                  <div>
                    <div>Status</div>
                    <div className="text-[#e6edf3]">{formatLabel(bookingData.payment_tracking.payment_status || 'unknown')}</div>
                  </div>
                </div>
                <div className="mt-2 text-[#8b949e]">
                  Refund: <span className="text-[#e6edf3]">{formatLabel(bookingData.payment_tracking.refund_status || 'not_applicable')}</span>
                </div>
              </div>
            )}
            <button
              data-testid="ops-edit-btn"
              className="mt-3 text-xs px-3 py-1 rounded bg-[#30363d] text-[#e6edf3] hover:bg-[#484f58]"
              onClick={startEdit}
            >
              Edit
            </button>
          </div>
        )}

        {!loading && !editing && !bookingData && (
          <div data-testid="ops-booking-empty">
            <span className="text-xs text-[#8b949e]">Not yet collected.</span>
            <button
              data-testid="ops-add-btn"
              className="ml-3 text-xs px-3 py-1 rounded bg-blue-900/50 text-blue-300 hover:bg-blue-800/50"
              onClick={startEdit}
            >
              Add booking details
            </button>
          </div>
        )}

        {editing && (
          <div data-testid="ops-booking-editor" className="space-y-3">
            {editTravelers.map((t, i) => (
              <div key={`traveler-${t.traveler_id || i}`} className="border border-[#30363d] rounded p-3 space-y-2">
                <div className="text-xs text-[#8b949e]">Traveler {i + 1}</div>
                <div className="grid grid-cols-2 gap-2">
                  <input
                    placeholder="Traveler ID (e.g. adult_1)"
                    className="bg-[#0d1117] border border-[#30363d] rounded px-2 py-1 text-xs text-[#e6edf3]"
                    value={t.traveler_id}
                    onChange={(e) => {
                      const next = [...editTravelers];
                      next[i] = { ...next[i], traveler_id: e.target.value };
                      setEditTravelers(next);
                    }}
                  />
                  <input
                    placeholder="Full name *"
                    className="bg-[#0d1117] border border-[#30363d] rounded px-2 py-1 text-xs text-[#e6edf3]"
                    value={t.full_name}
                    onChange={(e) => {
                      const next = [...editTravelers];
                      next[i] = { ...next[i], full_name: e.target.value };
                      setEditTravelers(next);
                    }}
                  />
                  <input
                    placeholder="Date of birth *"
                    className="bg-[#0d1117] border border-[#30363d] rounded px-2 py-1 text-xs text-[#e6edf3]"
                    value={t.date_of_birth}
                    onChange={(e) => {
                      const next = [...editTravelers];
                      next[i] = { ...next[i], date_of_birth: e.target.value };
                      setEditTravelers(next);
                    }}
                  />
                  <input
                    placeholder="Passport number"
                    className="bg-[#0d1117] border border-[#30363d] rounded px-2 py-1 text-xs text-[#e6edf3]"
                    value={t.passport_number ?? ''}
                    onChange={(e) => {
                      const next = [...editTravelers];
                      next[i] = { ...next[i], passport_number: e.target.value || null };
                      setEditTravelers(next);
                    }}
                  />
                </div>
                {editTravelers.length > 1 && (
                  <button
                    className="text-xs text-red-400"
                    onClick={() => setEditTravelers(editTravelers.filter((_, j) => j !== i))}
                  >
                    Remove
                  </button>
                )}
              </div>
            ))}
            <button
              className="text-xs text-blue-300"
              onClick={() => setEditTravelers((prev) => [...prev, emptyTraveler()])}
            >
              + Add traveler
            </button>
            <input
              placeholder="Payer name"
              className="w-full bg-[#0d1117] border border-[#30363d] rounded px-2 py-1 text-xs text-[#e6edf3]"
              value={editPayerName}
              onChange={(e) => setEditPayerName(e.target.value)}
            />
            <div className="border border-[#30363d] rounded p-3 space-y-3">
              <div className="flex items-center justify-between gap-2">
                <div className="text-xs font-medium text-[#e6edf3]">Payment & refund tracking</div>
                <div className="text-xs text-blue-300">Status-only tracking</div>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <input
                  data-testid="ops-payment-agreed-amount"
                  inputMode="decimal"
                  placeholder="Agreed amount"
                  className="bg-[#0d1117] border border-[#30363d] rounded px-2 py-1 text-xs text-[#e6edf3]"
                  value={editPaymentTracking.agreed_amount}
                  onChange={(e) => setEditPaymentTracking((prev) => ({ ...prev, agreed_amount: e.target.value }))}
                />
                <input
                  data-testid="ops-payment-amount-paid"
                  inputMode="decimal"
                  placeholder="Amount paid"
                  className="bg-[#0d1117] border border-[#30363d] rounded px-2 py-1 text-xs text-[#e6edf3]"
                  value={editPaymentTracking.amount_paid}
                  onChange={(e) => setEditPaymentTracking((prev) => ({ ...prev, amount_paid: e.target.value }))}
                />
                <input
                  data-testid="ops-payment-currency"
                  placeholder="Currency"
                  className="bg-[#0d1117] border border-[#30363d] rounded px-2 py-1 text-xs text-[#e6edf3]"
                  value={editPaymentTracking.currency}
                  onChange={(e) => setEditPaymentTracking((prev) => ({ ...prev, currency: e.target.value }))}
                />
                <select
                  data-testid="ops-payment-status"
                  className="bg-[#0d1117] border border-[#30363d] rounded px-2 py-1 text-xs text-[#e6edf3]"
                  value={editPaymentTracking.payment_status}
                  onChange={(e) => setEditPaymentTracking((prev) => ({ ...prev, payment_status: e.target.value as PaymentStatus }))}
                >
                  {PAYMENT_STATUSES.map((status) => (
                    <option key={status} value={status}>{formatLabel(status)}</option>
                  ))}
                </select>
                <input
                  placeholder="Payment method"
                  className="bg-[#0d1117] border border-[#30363d] rounded px-2 py-1 text-xs text-[#e6edf3]"
                  value={editPaymentTracking.payment_method}
                  onChange={(e) => setEditPaymentTracking((prev) => ({ ...prev, payment_method: e.target.value }))}
                />
                <input
                  placeholder="Payment reference"
                  className="bg-[#0d1117] border border-[#30363d] rounded px-2 py-1 text-xs text-[#e6edf3]"
                  value={editPaymentTracking.payment_reference}
                  onChange={(e) => setEditPaymentTracking((prev) => ({ ...prev, payment_reference: e.target.value }))}
                />
                <select
                  className="bg-[#0d1117] border border-[#30363d] rounded px-2 py-1 text-xs text-[#e6edf3]"
                  value={editPaymentTracking.refund_status}
                  onChange={(e) => setEditPaymentTracking((prev) => ({ ...prev, refund_status: e.target.value as RefundStatus }))}
                >
                  {REFUND_STATUSES.map((status) => (
                    <option key={status} value={status}>{formatLabel(status)}</option>
                  ))}
                </select>
                <input
                  placeholder="Refund amount agreed"
                  inputMode="decimal"
                  className="bg-[#0d1117] border border-[#30363d] rounded px-2 py-1 text-xs text-[#e6edf3]"
                  value={editPaymentTracking.refund_amount_agreed}
                  onChange={(e) => setEditPaymentTracking((prev) => ({ ...prev, refund_amount_agreed: e.target.value }))}
                />
              </div>
              <textarea
                placeholder="Internal payment/refund notes"
                className="w-full bg-[#0d1117] border border-[#30363d] rounded px-2 py-1 text-xs text-[#e6edf3]"
                value={editPaymentTracking.notes}
                onChange={(e) => setEditPaymentTracking((prev) => ({ ...prev, notes: e.target.value }))}
              />
            </div>
            <div className="flex gap-2">
              <button
                data-testid="ops-save-btn"
                className="text-xs px-3 py-1 rounded bg-emerald-900/50 text-emerald-300 hover:bg-emerald-800/50"
                onClick={handleSave}
                disabled={saving}
              >
                {saving ? 'Saving…' : 'Save'}
              </button>
              <button
                className="text-xs px-3 py-1 rounded bg-[#30363d] text-[#e6edf3] hover:bg-[#484f58]"
                onClick={() => setEditing(false)}
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </div>
      )}

      {/* Collection link generator - only at proposal/booking stage */}
      {!documentsOnly && canGenerateLink && (
        <div data-testid="ops-collection-link" className="border border-[#30363d] rounded-lg p-4">
          <h4 className="text-sm font-medium text-[#e6edf3] mb-3">Customer Collection Link</h4>

          {linkError && (
            <div data-testid="ops-link-error" className="mb-3 text-xs text-red-400">{linkError}</div>
          )}

          {linkLoading && (
            <span className="text-xs text-[#8b949e]">Loading…</span>
          )}

          {/* No URL available - show generate button (or "active link exists" indicator) */}
          {!linkLoading && !linkInfo && (
            <div>
              {linkStatus?.has_active_token && (
                <div data-testid="ops-link-active-hint" className="mb-3 text-xs text-[#8b949e]">
                  Active link exists (expires {linkStatus.expires_at ? <ClientDateTime value={linkStatus.expires_at} /> : 'unknown'}).
                  Generating a new link will revoke the old one.
                </div>
              )}
              <button
                data-testid="ops-generate-link-btn"
                className="text-xs px-3 py-1 rounded bg-blue-900/50 text-blue-300 hover:bg-blue-800/50 disabled:opacity-50"
                onClick={handleGenerateLink}
                disabled={linkGenerating}
              >
                {linkGenerating ? 'Generating…' : 'Generate New Customer Link'}
              </button>
            </div>
          )}

          {/* URL available after generate */}
          {!linkLoading && linkInfo && (
            <div data-testid="ops-link-info">
              <div className="flex items-center gap-2 mb-2">
                <input
                  readOnly
                  data-testid="ops-link-url"
                  className="flex-1 bg-[#0d1117] border border-[#30363d] rounded px-2 py-1 text-xs text-[#e6edf3] font-mono"
                  value={linkInfo.collection_url}
                  onClick={(e) => (e.target as HTMLInputElement).select()}
                />
                <button
                  data-testid="ops-copy-link-btn"
                  className="text-xs px-3 py-1 rounded bg-[#30363d] text-[#e6edf3] hover:bg-[#484f58]"
                  onClick={handleCopyLink}
                >
                  {linkCopied ? 'Copied!' : 'Copy'}
                </button>
              </div>
              <div className="text-xs text-[#8b949e] mb-3">
                Expires: <ClientDateTime value={linkInfo.expires_at} />
              </div>
              <div className="flex gap-2">
                <button
                  data-testid="ops-revoke-link-btn"
                  className="text-xs px-3 py-1 rounded bg-red-900/50 text-red-300 hover:bg-red-800/50"
                  onClick={handleRevokeLink}
                >
                  Revoke Link
                </button>
                <button
                  data-testid="ops-regenerate-link-btn"
                  className="text-xs px-3 py-1 rounded bg-blue-900/50 text-blue-300 hover:bg-blue-800/50 disabled:opacity-50"
                  onClick={handleGenerateLink}
                  disabled={linkGenerating}
                >
                  Generate New Link
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Documents section (Phase 4B) */}
      <div data-testid="ops-documents" className="border border-[#30363d] rounded-lg p-4">
        <div className="flex items-center justify-between mb-3">
          <h4 className="text-sm font-medium text-[#e6edf3]">Documents</h4>
          {canGenerateLink && (
            <div className="flex items-center gap-2">
              <select
                value={uploadDocType}
                onChange={(e) => setUploadDocType(e.target.value)}
                className="bg-[#0d1117] border border-[#30363d] rounded px-2 py-1 text-xs text-[#e6edf3]"
              >
                <option value="passport">Passport</option>
                <option value="visa">Visa</option>
                <option value="insurance">Insurance</option>
                <option value="flight_ticket">Flight Ticket</option>
                <option value="hotel_confirmation">Hotel Confirmation</option>
                <option value="other">Other</option>
              </select>
              <button
                data-testid="ops-document-upload-btn"
                className="text-xs px-3 py-1 rounded bg-blue-900/50 text-blue-300 hover:bg-blue-800/50 disabled:opacity-50"
                onClick={handleDocUpload}
                disabled={docUploading}
              >
                {docUploading ? 'Uploading…' : 'Upload'}
              </button>
            </div>
          )}
        </div>
        <div
          data-testid="ops-documents-canonical-path-hint"
          className="mb-3 rounded border border-blue-900/40 bg-blue-950/20 px-3 py-2 text-xs text-blue-200"
        >
          Canonical workflow: use this Ops panel for document upload, review, extraction, and apply.
          The dedicated <code>/documents</code> module remains staged and disabled until rollout readiness.
        </div>

        {docError && (
          <div className="mb-3 text-xs text-red-400">{docError}</div>
        )}

        {docsLoading && (
          <span className="text-xs text-[#8b949e]">Loading documents…</span>
        )}

        {!docsLoading && documents.length === 0 && (
          <span className="text-xs text-[#8b949e]">No documents uploaded yet.</span>
        )}

        {!docsLoading && documents.length > 0 && (
          <div data-testid="ops-document-list" className="space-y-2">
            {documents.map((doc) => (
              <div
                key={doc.id}
                data-testid={`ops-document-${doc.id}`}
                className="flex items-center justify-between py-2 px-3 rounded border border-[#30363d]"
              >
                <div className="flex items-center gap-3">
                  <span className="text-xs font-medium text-[#e6edf3]">
                    {doc.document_type.replace('_', ' ')}
                  </span>
                  <span className="text-xs text-[#8b949e]">
                    {doc.filename_ext} · {(doc.size_bytes / 1024).toFixed(0)}KB
                  </span>
                  <span
                    className={`text-xs px-2 py-0.5 rounded ${
                      doc.status === 'pending_review'
                        ? 'bg-amber-900/50 text-amber-300'
                        : doc.status === 'accepted'
                          ? 'bg-emerald-900/50 text-emerald-300'
                          : doc.status === 'rejected'
                            ? 'bg-red-900/50 text-red-300'
                            : 'bg-[#30363d] text-[#8b949e]'
                    }`}
                  >
                    {doc.status.replace('_', ' ')}
                  </span>
                  {doc.uploaded_by_type === 'customer' && (
                    <span className="text-xs px-2 py-0.5 rounded bg-blue-900/50 text-blue-300">
                      Customer
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-1">
                  {doc.status === 'pending_review' && (
                    <>
                      <button
                        data-testid={`ops-document-${doc.id}-accept-btn`}
                        className="text-xs px-2 py-1 rounded bg-emerald-900/50 text-emerald-300 hover:bg-emerald-800/50 disabled:opacity-50"
                        onClick={() => handleDocAccept(doc.id)}
                        disabled={docActionLoading === doc.id}
                      >
                        Accept
                      </button>
                      <button
                        data-testid={`ops-document-${doc.id}-reject-btn`}
                        className="text-xs px-2 py-1 rounded bg-red-900/50 text-red-300 hover:bg-red-800/50 disabled:opacity-50"
                        onClick={() => handleDocReject(doc.id)}
                        disabled={docActionLoading === doc.id}
                      >
                        Reject
                      </button>
                    </>
                  )}
                  {doc.status === 'accepted' && (
                    <>
                      <button
                        data-testid={`ops-document-${doc.id}-download-btn`}
                        className="text-xs px-2 py-1 rounded bg-[#30363d] text-[#e6edf3] hover:bg-[#484f58]"
                        onClick={() => handleDocDownload(doc.id)}
                      >
                        Download
                      </button>
                      <button
                        data-testid={`ops-document-${doc.id}-delete-btn`}
                        className="text-xs px-2 py-1 rounded bg-red-900/50 text-red-300 hover:bg-red-800/50 disabled:opacity-50"
                        onClick={() => handleDocDelete(doc.id)}
                        disabled={docActionLoading === doc.id}
                      >
                        Delete
                      </button>
                    </>
                  )}
                  {doc.status === 'rejected' && (
                    <button
                      data-testid={`ops-document-${doc.id}-delete-btn`}
                      className="text-xs px-2 py-1 rounded bg-red-900/50 text-red-300 hover:bg-red-800/50 disabled:opacity-50"
                      onClick={() => handleDocDelete(doc.id)}
                      disabled={docActionLoading === doc.id}
                    >
                      Delete
                    </button>
                  )}
                  {/* Phase 4C: Extract button (pending_review or accepted) */}
                  {(doc.status === 'pending_review' || doc.status === 'accepted') && !extractions[doc.id] && (
                    <button
                      data-testid={`ops-doc-extract-btn-${doc.id}`}
                      className="text-xs px-2 py-1 rounded bg-purple-900/50 text-purple-300 hover:bg-purple-800/50 disabled:opacity-50"
                      onClick={() => handleExtract(doc.id)}
                      disabled={extractingDocId === doc.id}
                    >
                      {extractingDocId === doc.id ? 'Extracting…' : 'Extract'}
                    </button>
                  )}
                </div>
                {/* Phase 4C: Extraction results */}
                {extractions[doc.id] && trip && (
                  <div data-testid={`ops-extraction-${doc.id}`} className="mt-2 border-t border-[#30363d] pt-2 space-y-2">
                    <div className="flex items-center gap-2 text-xs">
                      <span className="text-[#8b949e]">Extraction:</span>
                      <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${
                        extractions[doc.id].status === 'applied' ? 'bg-emerald-900/50 text-emerald-300' :
                        extractions[doc.id].status === 'rejected' ? 'bg-red-900/50 text-red-300' :
                        'bg-yellow-900/50 text-yellow-300'
                      }`}>
                        {extractions[doc.id].status.replace('_', ' ')}
                      </span>
                      {extractions[doc.id].overall_confidence !== null && (
                        <span className="text-[#8b949e]">
                          confidence: {Math.round(extractions[doc.id].overall_confidence! * 100)}%
                        </span>
                      )}
                    </div>
                    <div data-testid={`ops-extraction-fields-${doc.id}`} className="space-y-1">
                      {extractions[doc.id].fields.flatMap((f) => f.present ? [(
                        <div key={f.field_name} className="flex items-center gap-2 text-xs">
                          {extractions[doc.id].status === 'pending_review' && (
                            <input
                              type="checkbox"
                              data-testid={`ops-extraction-field-cb-${doc.id}-${f.field_name}`}
                              checked={extractionSelections[doc.id]?.selectedFields.includes(f.field_name) ?? false}
                              onChange={(e) => {
                              setExtractionSelections((prev) => {
                                const cur = prev[doc.id] ?? { travelerId: '', selectedFields: [] };
                                const fields = e.target.checked
                                  ? [...cur.selectedFields, f.field_name]
                                  : cur.selectedFields.filter((s) => s !== f.field_name);
                                return { ...prev, [doc.id]: { ...cur, selectedFields: fields } };
                              });
                            }}
                            className="accent-purple-400"
                          />
                          )}
                          <span className="text-[#8b949e] w-32">{f.field_name.replace(/_/g, ' ')}:</span>
                          <span className="text-[#e6edf3]">{f.value ?? '-'}</span>
                          <span className={`text-[10px] px-1 rounded ${
                            f.confidence >= 0.9 ? 'text-emerald-400' :
                            f.confidence >= 0.7 ? 'text-yellow-400' :
                            'text-red-400'
                          }`}>
                            {Math.round(f.confidence * 100)}%
                          </span>
                        </div>
                      )] : [])}
                    </div>
                    {extractions[doc.id].status === 'pending_review' && (
                      <div className="space-y-2">
                        {/* Traveler selector */}
                        <div className="flex items-center gap-2 text-xs">
                          <span className="text-[#8b949e]">Apply to:</span>
                          <select
                            data-testid={`ops-extraction-traveler-select-${doc.id}`}
                            value={extractionSelections[doc.id]?.travelerId ?? ''}
                            onChange={(e) => {
                              setExtractionSelections((prev) => {
                                const cur = prev[doc.id] ?? { travelerId: '', selectedFields: [] };
                                return { ...prev, [doc.id]: { ...cur, travelerId: e.target.value } };
                              });
                            }}
                            className="bg-[#0d1117] border border-[#30363d] rounded text-[#e6edf3] px-2 py-1 text-xs"
                          >
                            <option value="">Select traveler</option>
                            {(bookingData?.travelers ?? []).map((t) => (
                              <option key={t.traveler_id} value={t.traveler_id}>
                                {t.traveler_id}{t.full_name ? ` - ${t.full_name}` : ''}
                              </option>
                            ))}
                          </select>
                        </div>
                        {/* Conflict display */}
                        {extractionConflicts[doc.id] && extractionConflicts[doc.id].length > 0 && (
                          <div data-testid={`ops-extraction-conflicts-${doc.id}`} className="text-xs space-y-1 bg-yellow-900/20 border border-yellow-800/30 rounded p-2">
                            <div className="text-yellow-300 font-medium">Conflicts detected:</div>
                            {extractionConflicts[doc.id].map((c) => (
                              <div key={c.field_name} className="text-yellow-200">
                                {c.field_name.replace(/_/g, ' ')}: {c.existing_value} → {c.extracted_value}
                              </div>
                            ))}
                            <button
                              data-testid={`ops-extraction-overwrite-btn-${doc.id}`}
                              className="text-xs px-2 py-1 rounded bg-yellow-900/50 text-yellow-300 hover:bg-yellow-800/50 mt-1"
                              onClick={() => {
                                const sel = extractionSelections[doc.id];
                                if (sel && sel.travelerId && sel.selectedFields.length > 0) {
                                  handleApplyExtraction(doc.id, sel.travelerId, sel.selectedFields, true);
                                }
                              }}
                              disabled={extractionAction === doc.id}
                            >
                              {extractionAction === doc.id ? 'Overwriting…' : 'Apply with overwrite'}
                            </button>
                          </div>
                        )}
                        {/* Apply / Reject buttons */}
                        <div className="flex items-center gap-2">
                          <button
                            data-testid={`ops-extraction-apply-btn-${doc.id}`}
                            className="text-xs px-2 py-1 rounded bg-emerald-900/50 text-emerald-300 hover:bg-emerald-800/50 disabled:opacity-50"
                            onClick={() => {
                              const sel = extractionSelections[doc.id];
                              if (sel?.travelerId && sel.selectedFields.length > 0) {
                                handleApplyExtraction(doc.id, sel.travelerId, sel.selectedFields, false);
                              }
                            }}
                            disabled={
                              extractionAction === doc.id ||
                              !extractionSelections[doc.id]?.travelerId ||
                              !(extractionSelections[doc.id]?.selectedFields.length > 0)
                            }
                          >
                            {extractionAction === doc.id ? 'Applying…' : 'Apply selected'}
                          </button>
                          <button
                            data-testid={`ops-extraction-reject-btn-${doc.id}`}
                            className="text-xs px-2 py-1 rounded bg-red-900/50 text-red-300 hover:bg-red-800/50 disabled:opacity-50"
                            onClick={() => handleRejectExtraction(doc.id)}
                            disabled={extractionAction === doc.id}
                          >
                            Reject
                          </button>
                        </div>
                      </div>
                    )}
                    {extractionError && extractionAction === doc.id && (
                      <div className="text-xs text-red-400">{extractionError}</div>
                    )}
                  </div>
                )}
                {extractions[doc.id] && (
                  <ExtractionHistoryPanel
                    tripId={trip!.id}
                    documentId={doc.id}
                    extraction={extractions[doc.id]}
                    onRetryComplete={(updated) => {
                      setExtractions((prev) => ({ ...prev, [doc.id]: updated }));
                    }}
                  />
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Booking execution tasks (Phase 5A) */}
      {!documentsOnly && trip?.id && <BookingExecutionPanel tripId={trip.id} stage={stage ?? undefined} />}
      {!documentsOnly && trip?.id && <ConfirmationPanel tripId={trip.id} />}
      {!documentsOnly && trip?.id && <ExecutionTimelinePanel tripId={trip.id} />}
    </div>
  );
}
