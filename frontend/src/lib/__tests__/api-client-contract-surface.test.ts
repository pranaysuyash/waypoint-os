import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
  acceptDocument,
  applyExtraction,
  createBookingTask,
  createSeasonalCampaign,
  deleteDocument,
  deleteSeasonalCampaign,
  extractDocument,
  getDocumentDownloadUrl,
  getDocuments,
  getIntegration,
  getIntegrations,
  getOverride,
  getOverrides,
  getPaymentsQueue,
  getSeasonalCampaign,
  listDrafts,
  listSeasonalCampaigns,
  rejectDocument,
  rejectExtraction,
  reassessTrip,
  preflightSeasonalCampaign,
  type AgencySettingsResponse,
  type CreateSeasonalCampaignRequest,
  type SeasonalCampaign,
  type SeasonalCampaignListResponse,
  simulateSeasonalCampaign,
  dispatchSeasonalCampaign,
  submitTripReviewAction,
  type UpdateSeasonalCampaignRequest,
  updateAgencyAutonomy,
  updateAgencyOperational,
  updateAgencySeasonal,
  updateSeasonalCampaign,
  uploadDocument,
  type AnalyticsPipelineStage,
  type ApiError,
  type ApplyConflict,
  type BookingPayer,
  type UpdateAgencyAutonomyRequest,
  type UpdateAgencyOperationalRequest,
  type UpdateAgencySeasonalRequest,
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

  it('keeps settings update endpoints wired to canonical paths and payloads', async () => {
    const fetchMock = vi.mocked(fetch);
    const operationalRequest: UpdateAgencyOperationalRequest = {
      agency_name: 'Updated Agency',
      target_margin_pct: 24.5,
      default_currency: 'USD',
      operating_hours_start: '08:00',
      operating_hours_end: '18:00',
      operating_days: ['monday'],
      preferred_channels: ['email'],
      brand_tone: 'warm',
    };
    const autonomyRequest: UpdateAgencyAutonomyRequest = {
      allow_explicit_reassess: false,
      approval_gates: { DRAFT: 'auto' },
    };
    const seasonalRequest: UpdateAgencySeasonalRequest = {
      quarterly_recalibration_enabled: false,
      weather_risk_threshold: 1.5,
    };
    const agencySettingsResponse: AgencySettingsResponse = {
      agency_id: 'waypoint-hq',
      tier: 'starter',
      profile: {
        agency_name: 'Updated Agency',
        sub_brand: '',
        plan_label: 'standard',
        contact_email: 'ops@waypoint.travel',
        contact_phone: '',
        logo_url: '',
        website: 'https://waypoint.travel',
      },
      operational: {
        target_margin_pct: 24.5,
        default_currency: 'USD',
        operating_hours: { start: '08:00', end: '18:00' },
        operating_days: ['monday'],
        preferred_channels: ['email'],
        brand_tone: 'warm',
      },
      autonomy: {
        approval_gates: {
          STOP_NEEDS_REVIEW: 'block',
          DRAFT: 'auto',
          PROPOSAL: 'review',
        },
        mode_overrides: {},
        auto_proceed_with_warnings: true,
        learn_from_overrides: false,
        auto_reprocess_on_edit: false,
        allow_explicit_reassess: false,
        auto_reprocess_stages: {
          discovery: true,
          shortlist: false,
          proposal: false,
          booking: true,
        },
        min_proceed_confidence: 0.72,
        min_draft_confidence: 0.64,
      },
      seasonal: {
        active_seasons_enabled: true,
        default_quarter_window_months: 6,
        channel_mix: { direct: 0.4, partner: 0.6 },
        weather_risk_threshold: 1.5,
        budget_guardrail_multiplier: 1.2,
        micro_seasonality_window_days: 90,
        quarterly_recalibration_enabled: false,
        prelaunch_blocklist: [],
      },
    };

    fetchMock.mockResolvedValueOnce(jsonResponse(agencySettingsResponse));
    await updateAgencyOperational(operationalRequest);
    expect(fetchMock).toHaveBeenLastCalledWith(
      '/api/settings/operational',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify(operationalRequest),
        credentials: 'include',
      }),
    );

    fetchMock.mockResolvedValueOnce(jsonResponse(agencySettingsResponse));
    await updateAgencyAutonomy(autonomyRequest);
    expect(fetchMock).toHaveBeenLastCalledWith(
      '/api/settings/autonomy',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify(autonomyRequest),
        credentials: 'include',
      }),
    );

    fetchMock.mockResolvedValueOnce(jsonResponse(agencySettingsResponse));
    await updateAgencySeasonal(seasonalRequest);
    expect(fetchMock).toHaveBeenLastCalledWith(
      '/api/settings/seasonal',
      expect.objectContaining({
        method: 'PUT',
        body: JSON.stringify(seasonalRequest),
        credentials: 'include',
      }),
    );
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

    await getPaymentsQueue({ limit: 25, offset: 10, queue_status: 'due_soon', payment_status: 'partially_paid', refund_status: 'not_applicable', due_bucket: 'due_4_7' });
    expect(fetchMock).toHaveBeenLastCalledWith(
      '/api/payments?limit=25&offset=10&queue_status=due_soon&payment_status=partially_paid&refund_status=not_applicable&due_bucket=due_4_7',
      expect.objectContaining({ method: 'GET', credentials: 'include' }),
    );

    await getIntegrations();
    expect(fetchMock).toHaveBeenLastCalledWith('/api/integrations', expect.objectContaining({ method: 'GET', credentials: 'include' }));

    await getIntegration('google_calendar');
    expect(fetchMock).toHaveBeenLastCalledWith('/api/integrations/google_calendar', expect.objectContaining({ method: 'GET', credentials: 'include' }));
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

  it('keeps seasonal campaign endpoints wired to canonical BFF paths and shapes', async () => {
    const fetchMock = vi.mocked(fetch);
    const createRequest: CreateSeasonalCampaignRequest = { name: 'Regression Campaign' };
    const campaign: SeasonalCampaign = {
      plan_id: 'campaign-1',
      name: 'Regression Campaign',
      status: 'draft',
      destination: null,
      campaign_window_start_month: null,
      campaign_window_end_month: null,
      channel_mix: {},
      target_budget_min: null,
      target_budget_max: null,
      notes: null,
      blocklist: [],
      created_by: null,
      is_recalibrated: false,
      score: null,
      created_at: null,
      updated_at: null,
    };
    const updateRequest: UpdateSeasonalCampaignRequest = { status: 'active', destination: 'Barcelona' };
    const listResponse: SeasonalCampaignListResponse = { items: [campaign], total: 1 };

    fetchMock.mockResolvedValueOnce(jsonResponse(campaign));
    await createSeasonalCampaign(createRequest);
    expect(fetchMock).toHaveBeenLastCalledWith(
      '/api/settings/seasonal/campaigns',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify(createRequest),
        credentials: 'include',
      }),
    );

    fetchMock.mockResolvedValueOnce(jsonResponse(listResponse));
    await listSeasonalCampaigns();
    expect(fetchMock).toHaveBeenLastCalledWith(
      '/api/settings/seasonal/campaigns',
      expect.objectContaining({ method: 'GET', credentials: 'include' }),
    );

    fetchMock.mockResolvedValueOnce(jsonResponse(campaign));
    await getSeasonalCampaign('campaign-1');
    expect(fetchMock).toHaveBeenLastCalledWith(
      '/api/settings/seasonal/campaigns/campaign-1',
      expect.objectContaining({ method: 'GET', credentials: 'include' }),
    );

    fetchMock.mockResolvedValueOnce(jsonResponse(campaign));
    await updateSeasonalCampaign('campaign-1', updateRequest);
    expect(fetchMock).toHaveBeenLastCalledWith(
      '/api/settings/seasonal/campaigns/campaign-1',
      expect.objectContaining({
        method: 'PUT',
        body: JSON.stringify(updateRequest),
        credentials: 'include',
      }),
    );

    fetchMock.mockResolvedValueOnce(jsonResponse({ ok: true, plan_id: 'campaign-1' }));
    await deleteSeasonalCampaign('campaign-1');
    expect(fetchMock).toHaveBeenLastCalledWith(
      '/api/settings/seasonal/campaigns/campaign-1',
      expect.objectContaining({ method: 'DELETE', credentials: 'include' }),
    );
  });

  it('keeps seasonal campaign control endpoints wired to canonical BFF paths', async () => {
    const fetchMock = vi.mocked(fetch);

    fetchMock.mockResolvedValueOnce(jsonResponse({ plan_id: 'campaign-1', projected_leads: 120, projected_bookings: 14, projected_margin_pct: 18.2, confidence: 0.81, scenario: 'baseline', notes: [] }));
    await simulateSeasonalCampaign('campaign-1', 'baseline');
    expect(fetchMock).toHaveBeenLastCalledWith(
      '/api/settings/seasonal/campaigns/campaign-1/simulate',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ scenario: 'baseline' }),
      }),
    );

    fetchMock.mockResolvedValueOnce(jsonResponse({ plan_id: 'campaign-1', ok: true, checks: [], risk_score: 0.22 }));
    await preflightSeasonalCampaign('campaign-1');
    expect(fetchMock).toHaveBeenLastCalledWith(
      '/api/settings/seasonal/campaigns/campaign-1/preflight',
      expect.objectContaining({
        method: 'POST',
        credentials: 'include',
      }),
    );

    fetchMock.mockResolvedValueOnce(jsonResponse({ plan_id: 'campaign-1', ok: false, dry_run: true, executed_at: '2026-06-17T00:00:00Z', dispatched_channels: ['email'] }));
    await dispatchSeasonalCampaign('campaign-1', false);
    expect(fetchMock).toHaveBeenLastCalledWith(
      '/api/settings/seasonal/campaigns/campaign-1/dispatch',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ dry_run: false }),
      }),
    );
  });

  it('passes escalation outcome through the trip review action client', async () => {
    const fetchMock = vi.mocked(fetch);

    await submitTripReviewAction(
      'trip-1',
      'escalate',
      'Needs owner review',
      'quality_issue',
      'false_escalation',
    );

    expect(fetchMock).toHaveBeenLastCalledWith(
      '/api/trips/trip-1/review/action',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          action: 'escalate',
          notes: 'Needs owner review',
          error_category: 'quality_issue',
          escalation_outcome: 'false_escalation',
        }),
      }),
    );
  });

  it('passes workflow unit id through the trip review action client', async () => {
    const fetchMock = vi.mocked(fetch);

    await submitTripReviewAction(
      'trip-1',
      'escalate',
      'Needs owner review',
      'quality_issue',
      'false_escalation',
      'unit-1',
    );

    expect(fetchMock).toHaveBeenLastCalledWith(
      '/api/trips/trip-1/review/action',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          action: 'escalate',
          notes: 'Needs owner review',
          error_category: 'quality_issue',
          escalation_outcome: 'false_escalation',
          review_workflow_unit_id: 'unit-1',
        }),
      }),
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
