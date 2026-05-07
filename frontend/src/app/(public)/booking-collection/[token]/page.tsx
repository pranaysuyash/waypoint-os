'use client';

import { useState, useEffect, useCallback } from 'react';
import {
  type BookingTraveler,
  type BookingData,
  type CustomerDocumentResponse,
  getPublicCollectionForm,
  submitPublicBookingData,
  uploadPublicDocument,
} from '@/lib/api-client';

type FormState = 'loading' | 'invalid' | 'already_submitted' | 'active' | 'success' | 'error';

interface TripSummary {
  destination: string;
  departure_date: string;
  return_date: string;
  traveler_count: number;
  agency_name: string;
}

function emptyTraveler(): BookingTraveler {
  return { traveler_id: '', full_name: '', date_of_birth: '' };
}

export default function BookingCollectionPage({
  params,
}: {
  params: Promise<{ token: string }>;
}) {
  const [token, setToken] = useState<string | null>(null);
  const [formState, setFormState] = useState<FormState>('loading');
  const [invalidReason, setInvalidReason] = useState('');
  const [tripSummary, setTripSummary] = useState<TripSummary | null>(null);
  const [submitError, setSubmitError] = useState('');

  const [travelers, setTravelers] = useState<BookingTraveler[]>([emptyTraveler()]);
  const [payerName, setPayerName] = useState('');
  const [payerEmail, setPayerEmail] = useState('');
  const [payerPhone, setPayerPhone] = useState('');
  const [specialReqs, setSpecialReqs] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // Document upload state
  const [uploadedDocs, setUploadedDocs] = useState<CustomerDocumentResponse[]>([]);
  const [docUploading, setDocUploading] = useState(false);
  const [docError, setDocError] = useState('');
  const [docType, setDocType] = useState('passport');

  useEffect(() => {
    params.then((p) => setToken(p.token));
  }, [params]);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    getPublicCollectionForm(token)
      .then((ctx) => {
        if (cancelled) return;
        if (!ctx.valid) {
          setInvalidReason(ctx.reason || 'This link is no longer valid.');
          setFormState('invalid');
          return;
        }
        if (ctx.already_submitted) {
          setFormState('already_submitted');
          return;
        }
        const summary = ctx.trip_summary ?? {};
        setTripSummary({
          destination: summary.destination ?? '',
          departure_date: summary.date_window ?? '',
          return_date: '',
          traveler_count: Number(summary.traveler_count ?? 1),
          agency_name: summary.agency_name ?? '',
        });
        setFormState('active');
      })
      .catch(() => {
        if (!cancelled) {
          setInvalidReason('Failed to load form. Please try again later.');
          setFormState('invalid');
        }
      });
    return () => { cancelled = true; };
  }, [token]);

  const handleSubmit = useCallback(async () => {
    if (!token) return;
    const data: BookingData = {
      travelers,
      payer: payerName ? { name: payerName, email: payerEmail || null, phone: payerPhone || null } : null,
      special_requirements: specialReqs || null,
    };
    setSubmitting(true);
    setSubmitError('');
    try {
      await submitPublicBookingData(token, data);
      setFormState('success');
    } catch (e) {
      setSubmitError(e instanceof Error ? e.message : 'Submission failed');
    } finally {
      setSubmitting(false);
    }
  }, [token, travelers, payerName, payerEmail, payerPhone, specialReqs]);

  const handleDocUpload = useCallback(async () => {
    if (!token) return;
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.pdf,.jpg,.jpeg,.png';
    input.onchange = async (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (!file) return;
      setDocUploading(true);
      setDocError('');
      try {
        const resp = await uploadPublicDocument(token, file, docType);
        setUploadedDocs((prev) => [...prev, resp]);
      } catch (e) {
        setDocError(e instanceof Error ? e.message : 'Upload failed');
      } finally {
        setDocUploading(false);
      }
    };
    input.click();
  }, [token, docType]);

  if (formState === 'loading') {
    return (
      <div data-testid="collection-loading" className="min-h-screen flex items-center justify-center bg-[#0d1117]">
        <span className="text-[#8b949e] text-sm">Loading...</span>
      </div>
    );
  }

  if (formState === 'invalid') {
    return (
      <div data-testid="collection-invalid" className="min-h-screen flex items-center justify-center bg-[#0d1117]">
        <div className="max-w-md w-full p-8 text-center">
          <h1 className="text-lg font-medium text-red-400 mb-2">Link Invalid</h1>
          <p className="text-sm text-[#8b949e]">{invalidReason}</p>
        </div>
      </div>
    );
  }

  if (formState === 'already_submitted') {
    return (
      <div data-testid="collection-already-submitted" className="min-h-screen flex items-center justify-center bg-[#0d1117]">
        <div className="max-w-md w-full p-8 text-center">
          <h1 className="text-lg font-medium text-emerald-400 mb-2">Already Submitted</h1>
          <p className="text-sm text-[#8b949e]">Your booking details have already been submitted. The agency will review them shortly.</p>
        </div>
      </div>
    );
  }

  if (formState === 'success') {
    return (
      <div data-testid="collection-success" className="min-h-screen flex items-center justify-center bg-[#0d1117]">
        <div className="max-w-md w-full p-8 text-center">
          <h1 className="text-lg font-medium text-emerald-400 mb-2">Thank You!</h1>
          <p className="text-sm text-[#8b949e]">Your booking details have been submitted successfully. The agency will review and confirm your trip details.</p>
        </div>
      </div>
    );
  }

  if (formState === 'error') {
    return (
      <div data-testid="collection-error" className="min-h-screen flex items-center justify-center bg-[#0d1117]">
        <div className="max-w-md w-full p-8 text-center">
          <h1 className="text-lg font-medium text-red-400 mb-2">Error</h1>
          <p className="text-sm text-[#8b949e]">{submitError}</p>
        </div>
      </div>
    );
  }

  // Active form
  return (
    <div data-testid="collection-form" className="min-h-screen bg-[#0d1117] text-[#e6edf3]">
      <div className="max-w-lg mx-auto px-4 py-8">
        {tripSummary && (
          <div data-testid="trip-summary" className="border border-[#30363d] rounded-lg p-4 mb-6">
            <div className="text-xs text-[#8b949e] mb-1">Trip from {tripSummary.agency_name}</div>
            <div className="text-sm font-medium text-[#e6edf3] mb-2">{tripSummary.destination}</div>
            <div className="text-xs text-[#8b949e]">
              {tripSummary.departure_date} — {tripSummary.return_date}
              {' '}&middot; {tripSummary.traveler_count} traveler{tripSummary.traveler_count !== 1 ? 's' : ''}
            </div>
          </div>
        )}

        <h1 className="text-lg font-medium text-[#e6edf3] mb-6">Enter Booking Details</h1>

        {submitError && (
          <div data-testid="collection-submit-error" className="mb-4 text-xs text-red-400 border border-red-900/50 rounded p-3">
            {submitError}
          </div>
        )}

        {/* Travelers */}
        <div className="space-y-4 mb-6">
          {travelers.map((t, i) => (
            <div key={i} data-testid={`collection-traveler-${i}`} className="border border-[#30363d] rounded-lg p-4 space-y-3">
              <div className="text-sm font-medium text-[#e6edf3]">Traveler {i + 1}</div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-[#8b949e] mb-1">Traveler ID *</label>
                  <input
                    placeholder="e.g. adult_1"
                    className="w-full bg-[#0d1117] border border-[#30363d] rounded px-3 py-2 text-sm text-[#e6edf3]"
                    value={t.traveler_id}
                    onChange={(e) => {
                      const next = [...travelers];
                      next[i] = { ...next[i], traveler_id: e.target.value };
                      setTravelers(next);
                    }}
                  />
                </div>
                <div>
                  <label className="block text-xs text-[#8b949e] mb-1">Full name *</label>
                  <input
                    className="w-full bg-[#0d1117] border border-[#30363d] rounded px-3 py-2 text-sm text-[#e6edf3]"
                    value={t.full_name}
                    onChange={(e) => {
                      const next = [...travelers];
                      next[i] = { ...next[i], full_name: e.target.value };
                      setTravelers(next);
                    }}
                  />
                </div>
                <div>
                  <label className="block text-xs text-[#8b949e] mb-1">Date of birth *</label>
                  <input
                    type="date"
                    className="w-full bg-[#0d1117] border border-[#30363d] rounded px-3 py-2 text-sm text-[#e6edf3]"
                    value={t.date_of_birth}
                    onChange={(e) => {
                      const next = [...travelers];
                      next[i] = { ...next[i], date_of_birth: e.target.value };
                      setTravelers(next);
                    }}
                  />
                </div>
                <div>
                  <label className="block text-xs text-[#8b949e] mb-1">Passport number</label>
                  <input
                    className="w-full bg-[#0d1117] border border-[#30363d] rounded px-3 py-2 text-sm text-[#e6edf3]"
                    value={t.passport_number ?? ''}
                    onChange={(e) => {
                      const next = [...travelers];
                      next[i] = { ...next[i], passport_number: e.target.value || null };
                      setTravelers(next);
                    }}
                  />
                </div>
              </div>
              {travelers.length > 1 && (
                <button
                  className="text-xs text-red-400 hover:underline"
                  onClick={() => setTravelers(travelers.filter((_, j) => j !== i))}
                >
                  Remove traveler
                </button>
              )}
            </div>
          ))}
          <button
            className="text-sm text-blue-300 hover:underline"
            onClick={() => setTravelers([...travelers, emptyTraveler()])}
          >
            + Add traveler
          </button>
        </div>

        {/* Payer */}
        <div className="border border-[#30363d] rounded-lg p-4 mb-6 space-y-3">
          <div className="text-sm font-medium text-[#e6edf3]">Payer Details</div>
          <div>
            <label className="block text-xs text-[#8b949e] mb-1">Name *</label>
            <input
              className="w-full bg-[#0d1117] border border-[#30363d] rounded px-3 py-2 text-sm text-[#e6edf3]"
              value={payerName}
              onChange={(e) => setPayerName(e.target.value)}
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-[#8b949e] mb-1">Email</label>
              <input
                type="email"
                className="w-full bg-[#0d1117] border border-[#30363d] rounded px-3 py-2 text-sm text-[#e6edf3]"
                value={payerEmail}
                onChange={(e) => setPayerEmail(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-xs text-[#8b949e] mb-1">Phone</label>
              <input
                className="w-full bg-[#0d1117] border border-[#30363d] rounded px-3 py-2 text-sm text-[#e6edf3]"
                value={payerPhone}
                onChange={(e) => setPayerPhone(e.target.value)}
              />
            </div>
          </div>
        </div>

        {/* Special requirements */}
        <div className="mb-6">
          <label className="block text-xs text-[#8b949e] mb-1">Special requirements</label>
          <textarea
            className="w-full bg-[#0d1117] border border-[#30363d] rounded px-3 py-2 text-sm text-[#e6edf3] h-20 resize-none"
            value={specialReqs}
            onChange={(e) => setSpecialReqs(e.target.value)}
          />
        </div>

        {/* Document upload (Phase 4B) */}
        <div data-testid="collection-documents" className="border border-[#30363d] rounded-lg p-4 mb-6 space-y-3">
          <div className="text-sm font-medium text-[#e6edf3]">Upload Documents</div>
          <div className="text-xs text-[#8b949e]">Upload travel documents (passports, visas, etc.) for review by the agency.</div>

          {docError && (
            <div className="text-xs text-red-400">{docError}</div>
          )}

          <div className="flex items-center gap-2">
            <select
              value={docType}
              onChange={(e) => setDocType(e.target.value)}
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
              data-testid="collection-doc-upload-btn"
              className="text-xs px-3 py-1 rounded bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
              onClick={handleDocUpload}
              disabled={docUploading}
            >
              {docUploading ? 'Uploading...' : 'Choose File'}
            </button>
          </div>

          {uploadedDocs.length > 0 && (
            <div className="space-y-1">
              {uploadedDocs.map((d, i) => (
                <div key={d.id} data-testid={`collection-doc-${i}`} className="flex items-center gap-2 text-xs">
                  <span className="text-emerald-400">Uploaded</span>
                  <span className="text-[#8b949e]">({d.status.replace('_', ' ')})</span>
                </div>
              ))}
            </div>
          )}
        </div>

        <button
          data-testid="collection-submit-btn"
          className="w-full py-2 rounded bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
          onClick={handleSubmit}
          disabled={submitting}
        >
          {submitting ? 'Submitting...' : 'Submit Booking Details'}
        </button>
      </div>
    </div>
  );
}
