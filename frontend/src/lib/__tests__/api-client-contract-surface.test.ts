import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
  acceptDocument,
  applyExtraction,
  createBookingTask,
  deleteDocument,
  extractDocument,
  getDocumentDownloadUrl,
  getDocuments,
  getOverride,
  getOverrides,
  listDrafts,
  rejectDocument,
  rejectExtraction,
  reassessTrip,
  uploadDocument,
  type AnalyticsPipelineStage,
  type ApiError,
  type ApplyConflict,
  type BookingPayer,
  type BookingTaskCreateRequest,
  type DraftSummary,
  type ExplicitReassessRequest,
  type ExplicitReassessResponse,
  type ExtractionFieldView,
  type ReconciliationEntry,
  type RequestOptions,
} from '../api-client';

const jsonResponse = (body: unknown) => new Response(JSON.stringify(body), {
  status: 200,
  headers: { 'Content-Type': 'application/json' },
});

describe('api-client public contract surface', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn(async () => jsonResponse({ ok: true, items: [], total: 0 })));
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('keeps override, reassessment, draft, and booking-task endpoints wired to canonical BFF paths', async () => {
    const fetchMock = vi.mocked(fetch);

    await getOverrides('trip-1');
    expect(fetchMock).toHaveBeenLastCalledWith('/api/trips/trip-1/overrides', expect.objectContaining({ method: 'GET', credentials: 'include' }));

    const reassessRequest: ExplicitReassessRequest = { reason: 'operator requested', stage: 'proposal' };
    fetchMock.mockResolvedValueOnce(jsonResponse({ ok: true, trip_id: 'trip-1', run_id: 'run-1', state: 'queued', trigger: 'explicit' }));
    const reassessResponse: ExplicitReassessResponse = await reassessTrip('trip-1', reassessRequest);
    expect(reassessResponse.run_id).toBe('run-1');
    expect(fetchMock).toHaveBeenLastCalledWith('/api/trips/trip-1/reassess', expect.objectContaining({
      method: 'POST',
      body: JSON.stringify(reassessRequest),
    }));

    await getOverride('override-1');
    expect(fetchMock).toHaveBeenLastCalledWith('/api/overrides/override-1', expect.objectContaining({ method: 'GET' }));

    await listDrafts({ status: 'open', limit: 2 });
    expect(fetchMock).toHaveBeenLastCalledWith('/api/drafts?status=open&limit=2', expect.objectContaining({ method: 'GET' }));

    const taskRequest: BookingTaskCreateRequest = { task_type: 'call_supplier', title: 'Call hotel', priority: 'high' };
    await createBookingTask('trip-1', taskRequest);
    expect(fetchMock).toHaveBeenLastCalledWith('/api/booking-tasks/trip-1', expect.objectContaining({
      method: 'POST',
      body: JSON.stringify(taskRequest),
    }));
  });

  it('keeps document upload/review/extract/apply endpoints wired to canonical BFF paths', async () => {
    const fetchMock = vi.mocked(fetch);
    const file = new File(['passport-image'], 'passport.jpg', { type: 'image/jpeg' });

    await uploadDocument('trip-1', file, 'passport', 'adult_1');
    expect(fetchMock).toHaveBeenLastCalledWith(
      '/api/trips/trip-1/documents',
      expect.objectContaining({
        method: 'POST',
        credentials: 'include',
        body: expect.any(FormData),
      }),
    );

    await getDocuments('trip-1');
    expect(fetchMock).toHaveBeenLastCalledWith(
      '/api/trips/trip-1/documents',
      expect.objectContaining({ method: 'GET', credentials: 'include' }),
    );

    await getDocumentDownloadUrl('trip-1', 'doc-1');
    expect(fetchMock).toHaveBeenLastCalledWith(
      '/api/trips/trip-1/documents/doc-1/download-url',
      expect.objectContaining({ method: 'GET', credentials: 'include' }),
    );

    await acceptDocument('trip-1', 'doc-1', true);
    expect(fetchMock).toHaveBeenLastCalledWith(
      '/api/trips/trip-1/documents/doc-1/accept',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ notes_present: true }),
      }),
    );

    await rejectDocument('trip-1', 'doc-1', false);
    expect(fetchMock).toHaveBeenLastCalledWith(
      '/api/trips/trip-1/documents/doc-1/reject',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ notes_present: false }),
      }),
    );

    await deleteDocument('trip-1', 'doc-1');
    expect(fetchMock).toHaveBeenLastCalledWith(
      '/api/trips/trip-1/documents/doc-1',
      expect.objectContaining({ method: 'DELETE', credentials: 'include' }),
    );

    await extractDocument('trip-1', 'doc-1');
    expect(fetchMock).toHaveBeenLastCalledWith(
      '/api/trips/trip-1/documents/doc-1/extract',
      expect.objectContaining({ method: 'POST' }),
    );

    await applyExtraction('trip-1', 'doc-1', {
      traveler_id: 'adult_1',
      fields_to_apply: ['passport_number'],
      allow_overwrite: false,
    });
    expect(fetchMock).toHaveBeenLastCalledWith(
      '/api/trips/trip-1/documents/doc-1/extraction/apply',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          traveler_id: 'adult_1',
          fields_to_apply: ['passport_number'],
          allow_overwrite: false,
        }),
      }),
    );

    await rejectExtraction('trip-1', 'doc-1');
    expect(fetchMock).toHaveBeenLastCalledWith(
      '/api/trips/trip-1/documents/doc-1/extraction/reject',
      expect.objectContaining({ method: 'POST' }),
    );
  });

  it('keeps type-only API contracts importable for integration consumers', () => {
    const apiError: ApiError = { message: 'Bad request', status: 400, details: [{ field: 'budget' }] };
    const options: RequestOptions = { timeout: 1000, retry: 1, retryDelay: 10 };
    const pipelineStage: AnalyticsPipelineStage = { stageId: 'proposal', tripCount: 4, exitRate: 0.2, avgTimeInStage: 3 };
    const draft: DraftSummary = {
      draft_id: 'draft-1',
      name: 'Draft',
      status: 'open',
      stage: 'intake',
      operating_mode: 'assist',
      last_run_state: null,
      promoted_trip_id: null,
      created_at: '2026-05-11T00:00:00.000Z',
      updated_at: '2026-05-11T00:00:00.000Z',
      created_by: 'operator',
    };
    const payer: BookingPayer = { name: 'Asha', email: 'asha@example.com' };
    const extractionField: ExtractionFieldView = { field_name: 'passport_number', value: null, confidence: 0.4, present: false };
    const conflict: ApplyConflict = { field_name: 'passport_number', existing_value: 'old', extracted_value: 'new' };
    const reconciliation: ReconciliationEntry = { task_id: 'task-1', old_status: 'blocked', new_status: 'ready' };

    expect(apiError.status).toBe(400);
    expect(options.retry).toBe(1);
    expect(pipelineStage.stageId).toBe('proposal');
    expect(draft.draft_id).toBe('draft-1');
    expect(payer.name).toBe('Asha');
    expect(extractionField.present).toBe(false);
    expect(conflict.extracted_value).toBe('new');
    expect(reconciliation.new_status).toBe('ready');
  });
});
