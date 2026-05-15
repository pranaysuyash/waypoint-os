'use client';

import { useState, useEffect, useCallback } from 'react';
import { ClientDateTime } from '@/hooks/useClientDate';
import {
  type BookingData,
  type BookingTraveler,
  type PaymentStatus,
  type PaymentTracking,
  type RefundStatus,
  type CollectionLinkInfo,
  type CollectionLinkStatus,
  getBookingData,
  updateBookingData,
  generateCollectionLink,
  getCollectionLink,
  revokeCollectionLink,
  getPendingBookingData,
  acceptPendingBookingData,
  rejectPendingBookingData,
} from '@/lib/api-client';
import PaymentTrackingCard from './PaymentTrackingCard';

interface DataIntakeZoneProps {
  tripId: string;
  canGenerateLink: boolean;
  onPendingDataChange?: (data: BookingData | null) => void;
  onTravelersChange?: (travelers: BookingTraveler[]) => void;
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

// react-doctor-disable-next-line react-doctor/prefer-useReducer — 22+ state vars are independent slices; useReducer would add complexity without benefit
export default function DataIntakeZone({
  tripId,
  canGenerateLink,
  onPendingDataChange,
  onTravelersChange,
}: DataIntakeZoneProps) {
  // Booking data
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

  // Collection link
  const [linkStatus, setLinkStatus] = useState<CollectionLinkStatus | null>(null);
  const [linkInfo, setLinkInfo] = useState<CollectionLinkInfo | null>(null);
  const [linkLoading, setLinkLoading] = useState(false);
  const [linkGenerating, setLinkGenerating] = useState(false);
  const [linkCopied, setLinkCopied] = useState(false);
  const [linkError, setLinkError] = useState<string | null>(null);

  // Pending booking data
  const [pendingData, setPendingData] = useState<BookingData | null>(null);
  const [pendingLoading, setPendingLoading] = useState(false);
  const [accepting, setAccepting] = useState(false);
  const [rejecting, setRejecting] = useState(false);
  const [pendingError, setPendingError] = useState<string | null>(null);

  const fetchBookingData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await getBookingData(tripId);
      setBookingData(resp.booking_data);
      setUpdatedAt(resp.updated_at);
      onTravelersChange?.(resp.booking_data?.travelers ?? []);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load booking data');
    } finally {
      setLoading(false);
    }
  }, [tripId, onTravelersChange]);

  useEffect(() => {
    fetchBookingData();
  }, [fetchBookingData]);

  // react-doctor-disable-next-line react-doctor/no-cascading-set-state — independent state updates for unrelated UI concerns
  useEffect(() => {
    if (!canGenerateLink) return;

    let cancelled = false;
    (async () => {
      setLinkLoading(true);
      try {
        const status = await getCollectionLink(tripId);
        if (!cancelled) setLinkStatus(status);
      } catch {
        // No active link is fine
      } finally {
        if (!cancelled) setLinkLoading(false);
      }

      setPendingLoading(true);
      try {
        const resp = await getPendingBookingData(tripId);
        if (!cancelled) {
          setPendingData(resp.pending_booking_data);
          setBookingDataSource(resp.booking_data_source);
          onPendingDataChange?.(resp.pending_booking_data);
        }
      } catch {
        // No pending data is fine
      } finally {
        if (!cancelled) setPendingLoading(false);
      }
    })();

    return () => { cancelled = true; };
  }, [tripId, canGenerateLink, onPendingDataChange]);

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

  const handleSave = useCallback(async () => {
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
      const resp = await updateBookingData(tripId, data, undefined, updatedAt ?? undefined);
      setBookingData(resp.booking_data);
      setUpdatedAt(resp.updated_at);
      setBookingDataSource('agent');
      setEditing(false);
      onTravelersChange?.(resp.booking_data?.travelers ?? []);
    } catch (e: unknown) {
      if (e instanceof Error && 'status' in e && (e as { status?: number }).status === 409) {
        setConflict(true);
      } else {
        setError(e instanceof Error ? e.message : 'Failed to save booking data');
      }
    } finally {
      setSaving(false);
    }
  }, [tripId, editTravelers, editPayerName, bookingData, editPaymentTracking, updatedAt, onTravelersChange]);

  const handleGenerateLink = useCallback(async () => {
    setLinkGenerating(true);
    setLinkError(null);
    try {
      const info = await generateCollectionLink(tripId);
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
  }, [tripId]);

  const handleRevokeLink = useCallback(async () => {
    setLinkError(null);
    try {
      await revokeCollectionLink(tripId);
      setLinkInfo(null);
      setLinkStatus(null);
    } catch (e) {
      setLinkError(e instanceof Error ? e.message : 'Failed to revoke link');
    }
  }, [tripId]);

  const handleCopyLink = useCallback(() => {
    if (!linkInfo?.collection_url) return;
    navigator.clipboard.writeText(linkInfo.collection_url).then(() => {
      setLinkCopied(true);
      setTimeout(() => setLinkCopied(false), 2000);
    });
  }, [linkInfo?.collection_url]);

  const handleAccept = useCallback(async () => {
    setAccepting(true);
    setPendingError(null);
    try {
      await acceptPendingBookingData(tripId);
      setPendingData(null);
      setBookingDataSource('customer_accepted');
      onPendingDataChange?.(null);
      await fetchBookingData();
    } catch (e) {
      setPendingError(e instanceof Error ? e.message : 'Failed to accept');
    } finally {
      setAccepting(false);
    }
  }, [tripId, fetchBookingData, onPendingDataChange]);

  const handleReject = useCallback(async () => {
    setRejecting(true);
    setPendingError(null);
    try {
      await rejectPendingBookingData(tripId);
      setPendingData(null);
      onPendingDataChange?.(null);
    } catch (e) {
      setPendingError(e instanceof Error ? e.message : 'Failed to reject');
    } finally {
      setRejecting(false);
    }
  }, [tripId, onPendingDataChange]);

  return (
    <>
      {/* Pending submission loading */}
      {pendingLoading && (
        <div data-testid="ops-pending-loading" className="border border-[#30363d] rounded-lg p-4">
          <span className="text-xs text-[#8b949e]">Checking for customer submissions…</span>
        </div>
      )}

      {/* Pending submission review */}
      {!pendingLoading && pendingData && (
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
              <PaymentTrackingCard paymentTracking={bookingData.payment_tracking} />
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

      {/* Collection link generator — only at proposal/booking stage */}
      {canGenerateLink && (
        <div data-testid="ops-collection-link" className="border border-[#30363d] rounded-lg p-4">
          <h4 className="text-sm font-medium text-[#e6edf3] mb-3">Customer Collection Link</h4>

          {linkError && (
            <div data-testid="ops-link-error" className="mb-3 text-xs text-red-400">{linkError}</div>
          )}

          {linkLoading && (
            <span className="text-xs text-[#8b949e]">Loading…</span>
          )}

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
    </>
  );
}
