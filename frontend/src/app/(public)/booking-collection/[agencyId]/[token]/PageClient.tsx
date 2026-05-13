'use client';

import { useReducer, useEffect, useCallback, useId, useMemo } from 'react';
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

type CollectionState = {
  agencyId: string | null;
  token: string | null;
  formState: FormState;
  invalidReason: string;
  tripSummary: TripSummary | null;
  submitError: string;
  submitting: boolean;
  uploadedDocs: CustomerDocumentResponse[];
  docUploading: boolean;
  docError: string;
  docType: string;
};

type CollectionAction =
  | { type: 'PARAMS_LOADED'; agencyId: string; token: string }
  | { type: 'FORM_INVALID'; reason: string }
  | { type: 'FORM_ALREADY_SUBMITTED' }
  | { type: 'FORM_ACTIVE'; tripSummary: TripSummary }
  | { type: 'SUBMIT_STARTED' }
  | { type: 'SUBMIT_SUCCEEDED' }
  | { type: 'SUBMIT_FAILED'; error: string }
  | { type: 'DOC_UPLOAD_STARTED' }
  | { type: 'DOC_UPLOAD_SUCCEEDED'; document: CustomerDocumentResponse }
  | { type: 'DOC_UPLOAD_FAILED'; error: string }
  | { type: 'SET_DOC_TYPE'; docType: string };

const initialCollectionState: CollectionState = {
  agencyId: null,
  token: null,
  formState: 'loading',
  invalidReason: '',
  tripSummary: null,
  submitError: '',
  submitting: false,
  uploadedDocs: [],
  docUploading: false,
  docError: '',
  docType: 'passport',
};

function collectionReducer(state: CollectionState, action: CollectionAction): CollectionState {
  switch (action.type) {
    case 'PARAMS_LOADED':
      return { ...state, agencyId: action.agencyId, token: action.token };
    case 'FORM_INVALID':
      return { ...state, formState: 'invalid', invalidReason: action.reason };
    case 'FORM_ALREADY_SUBMITTED':
      return { ...state, formState: 'already_submitted' };
    case 'FORM_ACTIVE':
      return { ...state, formState: 'active', tripSummary: action.tripSummary };
    case 'SUBMIT_STARTED':
      return { ...state, submitting: true, submitError: '' };
    case 'SUBMIT_SUCCEEDED':
      return { ...state, formState: 'success', submitting: false };
    case 'SUBMIT_FAILED':
      return { ...state, submitError: action.error, submitting: false };
    case 'DOC_UPLOAD_STARTED':
      return { ...state, docUploading: true, docError: '' };
    case 'DOC_UPLOAD_SUCCEEDED':
      return { ...state, docUploading: false, uploadedDocs: [...state.uploadedDocs, action.document] };
    case 'DOC_UPLOAD_FAILED':
      return { ...state, docUploading: false, docError: action.error };
    case 'SET_DOC_TYPE':
      return { ...state, docType: action.docType };
    default:
      return state;
  }
}

function CollectionStatusScreen({
  testId,
  title,
  message,
  tone,
}: {
  testId: string;
  title: string;
  message: string;
  tone: 'red' | 'emerald';
}) {
  const titleColor = tone === 'red' ? 'text-red-400' : 'text-emerald-400';

  return (
    <div data-testid={testId} className="min-h-screen flex items-center justify-center bg-[#0d1117]">
      <div className="max-w-md w-full p-8 text-center">
        <h1 className={`text-lg font-medium ${titleColor} mb-2`}>{title}</h1>
        <p className="text-sm text-[#8b949e]">{message}</p>
      </div>
    </div>
  );
}

function TripSummaryCard({ tripSummary }: { tripSummary: TripSummary | null }) {
  if (!tripSummary) {
    return null;
  }

  return (
    <div data-testid="trip-summary" className="border border-[#30363d] rounded-lg p-4 mb-6">
      <div className="text-xs text-[#8b949e] mb-1">Trip from {tripSummary.agency_name}</div>
      <div className="text-sm font-medium text-[#e6edf3] mb-2">{tripSummary.destination}</div>
      <div className="text-xs text-[#8b949e]">
        {tripSummary.departure_date} - {tripSummary.return_date}
        {' '}&middot; {tripSummary.traveler_count} traveler{tripSummary.traveler_count !== 1 ? 's' : ''}
      </div>
    </div>
  );
}

function TravelersSection({
  travelers,
  travelerKeys,
  travelerIdBase,
  dispatch,
}: {
  travelers: BookingTraveler[];
  travelerKeys: string[];
  travelerIdBase: string;
  dispatch: React.Dispatch<FormFieldsAction>;
}) {
  const updateTraveler = (
    index: number,
    patch: Partial<BookingTraveler>,
  ) => {
    const next = [...travelers];
    next[index] = { ...next[index], ...patch };
    dispatch({ type: 'SET_TRAVELERS', travelers: next });
  };

  return (
    <div className="space-y-4 mb-6">
      {travelers.map((traveler, index) => (
        <div key={travelerKeys[index]} data-testid={`collection-traveler-${index}`} className="border border-[#30363d] rounded-lg p-4 space-y-3">
          <div className="text-sm font-medium text-[#e6edf3]">Traveler {index + 1}</div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label htmlFor={travelerIdBase + '-' + index + '-tid'} className="block text-xs text-[#8b949e] mb-1">Traveler ID *</label>
              <input
                id={travelerIdBase + '-' + index + '-tid'}
                placeholder="e.g. adult_1"
                className="w-full bg-[#0d1117] border border-[#30363d] rounded px-3 py-2 text-sm text-[#e6edf3]"
                value={traveler.traveler_id}
                onChange={(event) => updateTraveler(index, { traveler_id: event.target.value })}
              />
            </div>
            <div>
              <label htmlFor={travelerIdBase + '-' + index + '-name'} className="block text-xs text-[#8b949e] mb-1">Full name *</label>
              <input
                id={travelerIdBase + '-' + index + '-name'}
                className="w-full bg-[#0d1117] border border-[#30363d] rounded px-3 py-2 text-sm text-[#e6edf3]"
                value={traveler.full_name}
                onChange={(event) => updateTraveler(index, { full_name: event.target.value })}
              />
            </div>
            <div>
              <label htmlFor={travelerIdBase + '-' + index + '-dob'} className="block text-xs text-[#8b949e] mb-1">Date of birth *</label>
              <input
                id={travelerIdBase + '-' + index + '-dob'}
                type="date"
                className="w-full bg-[#0d1117] border border-[#30363d] rounded px-3 py-2 text-sm text-[#e6edf3]"
                value={traveler.date_of_birth}
                onChange={(event) => updateTraveler(index, { date_of_birth: event.target.value })}
              />
            </div>
            <div>
              <label htmlFor={travelerIdBase + '-' + index + '-pp'} className="block text-xs text-[#8b949e] mb-1">Passport number</label>
              <input
                id={travelerIdBase + '-' + index + '-pp'}
                className="w-full bg-[#0d1117] border border-[#30363d] rounded px-3 py-2 text-sm text-[#e6edf3]"
                value={traveler.passport_number ?? ''}
                onChange={(event) => updateTraveler(index, { passport_number: event.target.value || null })}
              />
            </div>
          </div>
          {travelers.length > 1 && (
            <button
              className="text-xs text-red-400 hover:underline"
              onClick={() => dispatch({ type: 'SET_TRAVELERS', travelers: travelers.filter((_, travelerIndex) => travelerIndex !== index) })}
            >
              Remove traveler
            </button>
          )}
        </div>
      ))}
      <button
        className="text-sm text-blue-300 hover:underline"
        onClick={() => dispatch({ type: 'SET_TRAVELERS', travelers: [...travelers, emptyTraveler()] })}
      >
        + Add traveler
      </button>
    </div>
  );
}

function PayerSection({
  fields,
  dispatch,
  payerNameId,
  payerEmailId,
  payerPhoneId,
}: {
  fields: FormFieldsState;
  dispatch: React.Dispatch<FormFieldsAction>;
  payerNameId: string;
  payerEmailId: string;
  payerPhoneId: string;
}) {
  return (
    <div className="border border-[#30363d] rounded-lg p-4 mb-6 space-y-3">
      <div className="text-sm font-medium text-[#e6edf3]">Payer Details</div>
      <div>
        <label htmlFor={payerNameId} className="block text-xs text-[#8b949e] mb-1">Name *</label>
        <input
          id={payerNameId}
          className="w-full bg-[#0d1117] border border-[#30363d] rounded px-3 py-2 text-sm text-[#e6edf3]"
          value={fields.payerName}
          onChange={(event) => dispatch({ type: 'SET_PAYER_FIELD', field: 'payerName', value: event.target.value })}
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
            onChange={(event) => dispatch({ type: 'SET_PAYER_FIELD', field: 'payerEmail', value: event.target.value })}
          />
        </div>
        <div>
          <label htmlFor={payerPhoneId} className="block text-xs text-[#8b949e] mb-1">Phone</label>
          <input
            id={payerPhoneId}
            className="w-full bg-[#0d1117] border border-[#30363d] rounded px-3 py-2 text-sm text-[#e6edf3]"
            value={fields.payerPhone}
            onChange={(event) => dispatch({ type: 'SET_PAYER_FIELD', field: 'payerPhone', value: event.target.value })}
          />
        </div>
      </div>
    </div>
  );
}

function DocumentsSection({
  docType,
  docError,
  docUploading,
  uploadedDocs,
  dispatchCollection,
  onDocUpload,
}: {
  docType: string;
  docError: string;
  docUploading: boolean;
  uploadedDocs: CustomerDocumentResponse[];
  dispatchCollection: React.Dispatch<CollectionAction>;
  onDocUpload: () => void;
}) {
  return (
    <div data-testid="collection-documents" className="border border-[#30363d] rounded-lg p-4 mb-6 space-y-3">
      <div className="text-sm font-medium text-[#e6edf3]">Upload Documents</div>
      <div className="text-xs text-[#8b949e]">Upload travel documents (passports, visas, etc.) for review by the agency.</div>

      {docError && (
        <div className="text-xs text-red-400">{docError}</div>
      )}

      <div className="flex items-center gap-2">
        <select
          value={docType}
          onChange={(event) => dispatchCollection({ type: 'SET_DOC_TYPE', docType: event.target.value })}
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
          onClick={onDocUpload}
          disabled={docUploading}
        >
          {docUploading ? 'Uploading…' : 'Choose File'}
        </button>
      </div>

      {uploadedDocs.length > 0 && (
        <div className="space-y-1">
          {uploadedDocs.map((document, index) => (
            <div key={document.id} data-testid={`collection-doc-${index}`} className="flex items-center gap-2 text-xs">
              <span className="text-emerald-400">Uploaded</span>
              <span className="text-[#8b949e]">({document.status.replace('_', ' ')})</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function ActiveCollectionForm({
  fields,
  tripSummary,
  submitError,
  submitting,
  uploadedDocs,
  docUploading,
  docError,
  docType,
  travelerKeys,
  travelerIdBase,
  payerNameId,
  payerEmailId,
  payerPhoneId,
  specialReqsId,
  dispatchFields,
  dispatchCollection,
  onSubmit,
  onDocUpload,
}: {
  fields: FormFieldsState;
  tripSummary: TripSummary | null;
  submitError: string;
  submitting: boolean;
  uploadedDocs: CustomerDocumentResponse[];
  docUploading: boolean;
  docError: string;
  docType: string;
  travelerKeys: string[];
  travelerIdBase: string;
  payerNameId: string;
  payerEmailId: string;
  payerPhoneId: string;
  specialReqsId: string;
  dispatchFields: React.Dispatch<FormFieldsAction>;
  dispatchCollection: React.Dispatch<CollectionAction>;
  onSubmit: () => void;
  onDocUpload: () => void;
}) {
  return (
    <div data-testid="collection-form" className="min-h-screen bg-[#0d1117] text-[#e6edf3]">
      <div className="max-w-lg mx-auto px-4 py-8">
        <TripSummaryCard tripSummary={tripSummary} />

        <h1 className="text-lg font-medium text-[#e6edf3] mb-6">Enter Booking Details</h1>

        {submitError && (
          <div data-testid="collection-submit-error" className="mb-4 text-xs text-red-400 border border-red-900/50 rounded p-3">
            {submitError}
          </div>
        )}

        <TravelersSection
          travelers={fields.travelers}
          travelerKeys={travelerKeys}
          travelerIdBase={travelerIdBase}
          dispatch={dispatchFields}
        />

        <PayerSection
          fields={fields}
          dispatch={dispatchFields}
          payerNameId={payerNameId}
          payerEmailId={payerEmailId}
          payerPhoneId={payerPhoneId}
        />

        <div className="mb-6">
          <label htmlFor={specialReqsId} className="block text-xs text-[#8b949e] mb-1">Special requirements</label>
          <textarea
            id={specialReqsId}
            className="w-full bg-[#0d1117] border border-[#30363d] rounded px-3 py-2 text-sm text-[#e6edf3] h-20 resize-none"
            value={fields.specialReqs}
            onChange={(event) => dispatchFields({ type: 'SET_SPECIAL_REQS', value: event.target.value })}
          />
        </div>

        <DocumentsSection
          docType={docType}
          docError={docError}
          docUploading={docUploading}
          uploadedDocs={uploadedDocs}
          dispatchCollection={dispatchCollection}
          onDocUpload={onDocUpload}
        />

        <button
          data-testid="collection-submit-btn"
          className="w-full py-2 rounded bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
          onClick={onSubmit}
          disabled={submitting}
        >
          {submitting ? 'Submitting…' : 'Submit Booking Details'}
        </button>
      </div>
    </div>
  );
}

export default function BookingCollectionPage({
  params,
}: {
  params: Promise<{ agencyId: string; token: string }>;
}) {
  const [state, dispatchCollection] = useReducer(collectionReducer, initialCollectionState);
  const {
    agencyId,
    token,
    formState,
    invalidReason,
    tripSummary,
    submitError,
    submitting,
    uploadedDocs,
    docUploading,
    docError,
    docType,
  } = state;

  const [fields, dispatch] = useReducer(formFieldsReducer, { travelers: [emptyTraveler()], payerName: '', payerEmail: '', payerPhone: '', specialReqs: '' });

  const travelerIdBase = useId();
  const travelerKeys = useMemo(
    () => fields.travelers.map((_, index) => `${travelerIdBase}-traveler-${index + 1}`),
    [fields.travelers, travelerIdBase],
  );
  const payerNameId = useId();
  const payerEmailId = useId();
  const payerPhoneId = useId();
  const specialReqsId = useId();

  useEffect(() => {
    let cancelled = false;

    params.then((p) => {
      if (!cancelled) {
        dispatchCollection({ type: 'PARAMS_LOADED', agencyId: p.agencyId, token: p.token });
      }
    });

    return () => {
      cancelled = true;
    };
  }, [params]);

  useEffect(() => {
    if (!token || !agencyId) return;
    let cancelled = false;
    getPublicCollectionForm(agencyId, token)
      .then((ctx) => {
        if (cancelled) return;
        if (!ctx.valid) {
          dispatchCollection({ type: 'FORM_INVALID', reason: ctx.reason || 'This link is no longer valid.' });
          return;
        }
        if (ctx.already_submitted) {
          dispatchCollection({ type: 'FORM_ALREADY_SUBMITTED' });
          return;
        }
        const summary = ctx.trip_summary ?? {};
        dispatchCollection({
          type: 'FORM_ACTIVE',
          tripSummary: {
            destination: summary.destination ?? '',
            departure_date: summary.date_window ?? '',
            return_date: '',
            traveler_count: Number(summary.traveler_count ?? 1),
            agency_name: summary.agency_name ?? '',
          },
        });
      })
      .catch(() => {
        if (!cancelled) {
          dispatchCollection({ type: 'FORM_INVALID', reason: 'Failed to load form. Please try again later.' });
        }
      });
    return () => { cancelled = true; };
  }, [agencyId, token]);

  const handleSubmit = useCallback(async () => {
    if (!token || !agencyId) return;
    const data: BookingData = {
      travelers: fields.travelers,
      payer: fields.payerName ? { name: fields.payerName, email: fields.payerEmail || null, phone: fields.payerPhone || null } : null,
      special_requirements: fields.specialReqs || null,
    };
    dispatchCollection({ type: 'SUBMIT_STARTED' });
    try {
      await submitPublicBookingData(agencyId, token, data);
      dispatchCollection({ type: 'SUBMIT_SUCCEEDED' });
    } catch (e) {
      dispatchCollection({ type: 'SUBMIT_FAILED', error: e instanceof Error ? e.message : 'Submission failed' });
    }
  }, [agencyId, token, fields.travelers, fields.payerName, fields.payerEmail, fields.payerPhone, fields.specialReqs]);

  const handleDocUpload = useCallback(async () => {
    if (!token || !agencyId) return;
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.pdf,.jpg,.jpeg,.png';
    input.onchange = async (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (!file) return;
      dispatchCollection({ type: 'DOC_UPLOAD_STARTED' });
      try {
        const resp = await uploadPublicDocument(agencyId, token, file, docType);
        dispatchCollection({ type: 'DOC_UPLOAD_SUCCEEDED', document: resp });
      } catch (e) {
        dispatchCollection({ type: 'DOC_UPLOAD_FAILED', error: e instanceof Error ? e.message : 'Upload failed' });
      }
    };
    input.click();
  }, [agencyId, token, docType]);

  if (formState === 'loading') {
    return (
      <div data-testid="collection-loading" className="min-h-screen flex items-center justify-center bg-[#0d1117]">
        <span className="text-[#8b949e] text-sm">Loading…</span>
      </div>
    );
  }

  if (formState === 'invalid') {
    return (
      <CollectionStatusScreen
        testId="collection-invalid"
        title="Link Invalid"
        message={invalidReason}
        tone="red"
      />
    );
  }

  if (formState === 'already_submitted') {
    return (
      <CollectionStatusScreen
        testId="collection-already-submitted"
        title="Already Submitted"
        message="Your booking details have already been submitted. The agency will review them shortly."
        tone="emerald"
      />
    );
  }

  if (formState === 'success') {
    return (
      <CollectionStatusScreen
        testId="collection-success"
        title="Thank You!"
        message="Your booking details have been submitted successfully. The agency will review and confirm your trip details."
        tone="emerald"
      />
    );
  }

  if (formState === 'error') {
    return (
      <CollectionStatusScreen
        testId="collection-error"
        title="Error"
        message={submitError}
        tone="red"
      />
    );
  }

  return (
    <ActiveCollectionForm
      fields={fields}
      tripSummary={tripSummary}
      submitError={submitError}
      submitting={submitting}
      uploadedDocs={uploadedDocs}
      docUploading={docUploading}
      docError={docError}
      docType={docType}
      travelerKeys={travelerKeys}
      travelerIdBase={travelerIdBase}
      payerNameId={payerNameId}
      payerEmailId={payerEmailId}
      payerPhoneId={payerPhoneId}
      specialReqsId={specialReqsId}
      dispatchFields={dispatch}
      dispatchCollection={dispatchCollection}
      onSubmit={handleSubmit}
      onDocUpload={handleDocUpload}
    />
  );
}
