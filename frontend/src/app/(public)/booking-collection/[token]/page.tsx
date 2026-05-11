'use client';

import { useState, useReducer, useEffect, useCallback, useId, useMemo, useRef } from 'react';
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

type FormFieldsState = { travelers: BookingTraveler[]; payerName: string; payerEmail: string; payerPhone: string; specialReqs: string };
type FormFieldsAction =
  | { type: 'SET_TRAVELERS'; travelers: BookingTraveler[] }
  | { type: 'SET_PAYER_FIELD'; field: 'payerName' | 'payerEmail' | 'payerPhone'; value: string }
  | { type: 'SET_SPECIAL_REQS'; value: string };
function formFieldsReducer(state: FormFieldsState, action: FormFieldsAction): FormFieldsState {
  switch (action.type) {
    case 'SET_TRAVELERS': return { ...state, travelers: action.travelers };
    case 'SET_PAYER_FIELD': return { ...state, [action.field]: action.value };
    case 'SET_SPECIAL_REQS': return { ...state, specialReqs: action.value };
    default: return state;
  }
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
  const [submitting, setSubmitting] = useState(false);

  const [fields, dispatch] = useReducer(formFieldsReducer, { travelers: [emptyTraveler()], payerName: '', payerEmail: '', payerPhone: '', specialReqs: '' });

  const travelerIdBase = useId();
  const travelerKeys = useMemo(
    () => fields.travelers.map((_, index) => `${travelerIdBase}-traveler-${index + 1}`),
    [fields.travelers.length, travelerIdBase],
  );
  const payerNameId = useId();
  const payerEmailId = useId();
  const payerPhoneId = useId();
  const specialReqsId = useId();

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
      travelers: fields.travelers,
      payer: fields.payerName ? { name: fields.payerName, email: fields.payerEmail || null, phone: fields.payerPhone || null } : null,
      special_requirements: fields.specialReqs || null,
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
  }, [token, fields.travelers, fields.payerName, fields.payerEmail, fields.payerPhone, fields.specialReqs]);

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
        <span className="text-[#8b949e] text-sm">Loading…</span>
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
              {tripSummary.departure_date} - {tripSummary.return_date}
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
          {fields.travelers.map((t, i) => (
            <div key={travelerKeys[i]} data-testid={`collection-traveler-${i}`} className="border border-[#30363d] rounded-lg p-4 space-y-3">
              <div className="text-sm font-medium text-[#e6edf3]">Traveler {i + 1}</div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label htmlFor={travelerIdBase + '-' + i + '-tid'} className="block text-xs text-[#8b949e] mb-1">Traveler ID *</label>
                  <input
                    id={travelerIdBase + '-' + i + '-tid'}
                    placeholder="e.g. adult_1"
                    className="w-full bg-[#0d1117] border border-[#30363d] rounded px-3 py-2 text-sm text-[#e6edf3]"
                    value={t.traveler_id}
                    onChange={(e) => {
                      const next = [...fields.travelers];
                      next[i] = { ...next[i], traveler_id: e.target.value };
                      dispatch({ type: 'SET_TRAVELERS', travelers: next });
                    }}
                  />
                </div>
                <div>
                  <label htmlFor={travelerIdBase + '-' + i + '-name'} className="block text-xs text-[#8b949e] mb-1">Full name *</label>
                  <input
                    id={travelerIdBase + '-' + i + '-name'}
                    className="w-full bg-[#0d1117] border border-[#30363d] rounded px-3 py-2 text-sm text-[#e6edf3]"
                    value={t.full_name}
                    onChange={(e) => {
                      const next = [...fields.travelers];
                      next[i] = { ...next[i], full_name: e.target.value };
                      dispatch({ type: 'SET_TRAVELERS', travelers: next });
                    }}
                  />
                </div>
                <div>
                  <label htmlFor={travelerIdBase + '-' + i + '-dob'} className="block text-xs text-[#8b949e] mb-1">Date of birth *</label>
                  <input
                    id={travelerIdBase + '-' + i + '-dob'}
                    type="date"
                    className="w-full bg-[#0d1117] border border-[#30363d] rounded px-3 py-2 text-sm text-[#e6edf3]"
                    value={t.date_of_birth}
                    onChange={(e) => {
                      const next = [...fields.travelers];
                      next[i] = { ...next[i], date_of_birth: e.target.value };
                      dispatch({ type: 'SET_TRAVELERS', travelers: next });
                    }}
                  />
                </div>
                <div>
                  <label htmlFor={travelerIdBase + '-' + i + '-pp'} className="block text-xs text-[#8b949e] mb-1">Passport number</label>
                  <input
                    id={travelerIdBase + '-' + i + '-pp'}
                    className="w-full bg-[#0d1117] border border-[#30363d] rounded px-3 py-2 text-sm text-[#e6edf3]"
                    value={t.passport_number ?? ''}
                    onChange={(e) => {
                      const next = [...fields.travelers];
                      next[i] = { ...next[i], passport_number: e.target.value || null };
                      dispatch({ type: 'SET_TRAVELERS', travelers: next });
                    }}
                  />
                </div>
              </div>
              {fields.travelers.length > 1 && (
                <button
                  className="text-xs text-red-400 hover:underline"
                    onClick={() => dispatch({ type: 'SET_TRAVELERS', travelers: fields.travelers.filter((_, j) => j !== i) })}
                  >
                    Remove traveler
                  </button>
                )}
            </div>
            ))}
          <button
            className="text-sm text-blue-300 hover:underline"
            onClick={() => dispatch({ type: 'SET_TRAVELERS', travelers: [...fields.travelers, emptyTraveler()] })}
          >
            + Add traveler
          </button>
        </div>

        {/* Payer */}
        <div className="border border-[#30363d] rounded-lg p-4 mb-6 space-y-3">
          <div className="text-sm font-medium text-[#e6edf3]">Payer Details</div>
          <div>
            <label htmlFor={payerNameId} className="block text-xs text-[#8b949e] mb-1">Name *</label>
            <input
              id={payerNameId}
              className="w-full bg-[#0d1117] border border-[#30363d] rounded px-3 py-2 text-sm text-[#e6edf3]"
               value={fields.payerName}
               onChange={(e) => dispatch({ type: 'SET_PAYER_FIELD', field: 'payerName', value: e.target.value })}
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label htmlFor={payerEmailId} className="block text-xs text-[#8b949e] mb-1">Email</label>
              <input
                id={payerEmailId}
                type="email"
                className="w-full bg-[#0d1117] border border-[#30363d] rounded px-3 py-2 text-sm text-[#e6edf3]"
                value={fields.payerEmail}
                onChange={(e) => dispatch({ type: 'SET_PAYER_FIELD', field: 'payerEmail', value: e.target.value })}
              />
            </div>
            <div>
              <label htmlFor={payerPhoneId} className="block text-xs text-[#8b949e] mb-1">Phone</label>
              <input
                id={payerPhoneId}
                className="w-full bg-[#0d1117] border border-[#30363d] rounded px-3 py-2 text-sm text-[#e6edf3]"
                value={fields.payerPhone}
                onChange={(e) => dispatch({ type: 'SET_PAYER_FIELD', field: 'payerPhone', value: e.target.value })}
              />
            </div>
          </div>
        </div>

        {/* Special requirements */}
        <div className="mb-6">
          <label htmlFor={specialReqsId} className="block text-xs text-[#8b949e] mb-1">Special requirements</label>
          <textarea
            id={specialReqsId}
            className="w-full bg-[#0d1117] border border-[#30363d] rounded px-3 py-2 text-sm text-[#e6edf3] h-20 resize-none"
            value={fields.specialReqs}
            onChange={(e) => dispatch({ type: 'SET_SPECIAL_REQS', value: e.target.value })}
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
              {docUploading ? 'Uploading…' : 'Choose File'}
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
          {submitting ? 'Submitting…' : 'Submit Booking Details'}
        </button>
      </div>
    </div>
  );
}
