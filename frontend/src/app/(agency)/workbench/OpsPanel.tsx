'use client';

import { useState, useEffect, useCallback } from 'react';
import { useWorkbenchStore } from '@/stores/workbench';
import {
  type Trip,
  type BookingData,
  type BookingTraveler,
  type CollectionLinkInfo,
  type PendingBookingDataResponse,
  getBookingData,
  updateBookingData,
  generateCollectionLink,
  getCollectionLink,
  revokeCollectionLink,
  getPendingBookingData,
  acceptPendingBookingData,
  rejectPendingBookingData,
} from '@/lib/api-client';
import type { ReadinessAssessment } from '@/types/spine';

interface OpsPanelProps {
  trip?: Trip | null;
}

function emptyTraveler(): BookingTraveler {
  return { traveler_id: '', full_name: '', date_of_birth: '' };
}

export default function OpsPanel({ trip }: OpsPanelProps) {
  const { result_validation } = useWorkbenchStore();

  const readiness: ReadinessAssessment | undefined =
    (result_validation as { readiness?: ReadinessAssessment } | null)?.readiness ??
    (trip?.validation as { readiness?: ReadinessAssessment } | null)?.readiness;

  // Booking data — local state only, not in global store
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

  // Collection link state
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

  useEffect(() => {
    if (!trip?.id || !canGenerateLink) return;

    let cancelled = false;
    (async () => {
      // Fetch link status
      setLinkLoading(true);
      try {
        const info = await getCollectionLink(trip.id);
        if (!cancelled) setLinkInfo(info);
      } catch {
        // No active link is fine — 404 expected
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

  // Start editing
  const startEdit = useCallback(() => {
    if (bookingData) {
      setEditTravelers(bookingData.travelers.map((t) => ({ ...t })));
      setEditPayerName(bookingData.payer?.name ?? '');
    } else {
      setEditTravelers([emptyTraveler()]);
      setEditPayerName('');
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
  }, [trip?.id, editTravelers, editPayerName, updatedAt]);

  // Generate collection link
  const handleGenerateLink = useCallback(async () => {
    if (!trip?.id) return;
    setLinkGenerating(true);
    setLinkError(null);
    try {
      const info = await generateCollectionLink(trip.id);
      setLinkInfo(info);
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

  if (!readiness) {
    return (
      <div data-testid="ops-panel-empty" className="text-sm text-[#8b949e]">
        No readiness data available. Run the pipeline to generate a readiness assessment.
      </div>
    );
  }

  const tiers = readiness.tiers ?? {};
  const tierEntries = Object.entries(tiers);
  const signals = readiness.signals;

  return (
    <div data-testid="ops-panel" className="space-y-6">
      {/* Highest tier summary */}
      <div className="flex items-center gap-3">
        <span className="text-sm text-[#8b949e]">Highest ready tier:</span>
        <span
          data-testid="ops-highest-tier"
          className="text-sm font-medium text-[#e6edf3]"
        >
          {readiness.highest_ready_tier ?? 'none'}
        </span>
      </div>

      {/* Tier details */}
      {tierEntries.length > 0 && (
        <div data-testid="ops-tiers" className="space-y-4">
          <h3 className="text-sm font-medium text-[#e6edf3]">Booking Readiness Tiers</h3>
          {tierEntries.map(([name, tier]) => (
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
          ))}
        </div>
      )}

      {/* Missing for next stage */}
      {readiness.missing_for_next.length > 0 && (
        <div data-testid="ops-missing" className="border border-[#30363d] rounded-lg p-4">
          <span className="text-xs text-[#8b949e]">Fields blocking next tier: </span>
          <span className="text-xs text-amber-400">
            {readiness.missing_for_next.join(', ')}
          </span>
        </div>
      )}

      {/* Auxiliary signals */}
      {signals && Object.keys(signals).length > 0 && (
        <div data-testid="ops-signals" className="border border-[#30363d] rounded-lg p-4">
          <h4 className="text-sm font-medium text-[#e6edf3] mb-2">Signals</h4>
          {signals.visa_concerns_present === true && (
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

      {/* Pending submission review — shown when customer has submitted data */}
      {pendingLoading && (
        <div data-testid="ops-pending-loading" className="border border-[#30363d] rounded-lg p-4">
          <span className="text-xs text-[#8b949e]">Checking for customer submissions...</span>
        </div>
      )}

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
              {pendingData.travelers.map((t, i) => (
                <tr key={i} className="text-[#e6edf3]">
                  <td className="py-1">{t.traveler_id}</td>
                  <td className="py-1">{t.full_name}</td>
                  <td className="py-1">{t.date_of_birth}</td>
                  <td className="py-1">{t.passport_number || '—'}</td>
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
              {accepting ? 'Accepting...' : 'Accept'}
            </button>
            <button
              data-testid="ops-reject-btn"
              className="text-xs px-3 py-1 rounded bg-red-900/50 text-red-300 hover:bg-red-800/50 disabled:opacity-50"
              onClick={handleReject}
              disabled={rejecting}
            >
              {rejecting ? 'Rejecting...' : 'Reject'}
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

        {loading && <span className="text-xs text-[#8b949e]">Loading...</span>}

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
                {bookingData.travelers.map((t, i) => (
                  <tr key={i} className="text-[#e6edf3]">
                    <td className="py-1">{t.traveler_id}</td>
                    <td className="py-1">{t.full_name}</td>
                    <td className="py-1">{t.date_of_birth}</td>
                    <td className="py-1">{t.passport_number || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {bookingData.payer && (
              <div className="mt-2 text-xs text-[#8b949e]">
                Payer: <span className="text-[#e6edf3]">{bookingData.payer.name}</span>
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
              <div key={i} className="border border-[#30363d] rounded p-3 space-y-2">
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
              onClick={() => setEditTravelers([...editTravelers, emptyTraveler()])}
            >
              + Add traveler
            </button>
            <input
              placeholder="Payer name"
              className="w-full bg-[#0d1117] border border-[#30363d] rounded px-2 py-1 text-xs text-[#e6edf3]"
              value={editPayerName}
              onChange={(e) => setEditPayerName(e.target.value)}
            />
            <div className="flex gap-2">
              <button
                data-testid="ops-save-btn"
                className="text-xs px-3 py-1 rounded bg-emerald-900/50 text-emerald-300 hover:bg-emerald-800/50"
                onClick={handleSave}
                disabled={saving}
              >
                {saving ? 'Saving...' : 'Save'}
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
            <span className="text-xs text-[#8b949e]">Loading...</span>
          )}

          {!linkLoading && !linkInfo && (
            <button
              data-testid="ops-generate-link-btn"
              className="text-xs px-3 py-1 rounded bg-blue-900/50 text-blue-300 hover:bg-blue-800/50 disabled:opacity-50"
              onClick={handleGenerateLink}
              disabled={linkGenerating}
            >
              {linkGenerating ? 'Generating...' : 'Generate Customer Link'}
            </button>
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
                Expires: {new Date(linkInfo.expires_at).toLocaleString()}
              </div>
              <button
                data-testid="ops-revoke-link-btn"
                className="text-xs px-3 py-1 rounded bg-red-900/50 text-red-300 hover:bg-red-800/50"
                onClick={handleRevokeLink}
              >
                Revoke Link
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
