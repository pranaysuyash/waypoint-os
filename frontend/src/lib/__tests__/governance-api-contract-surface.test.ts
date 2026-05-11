import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
  exportInsights,
  getApprovalThresholds,
  getAuditEvents,
  getAuditEventsByTrip,
  getAutonomyPolicy,
  getConversionFunnel,
  getEscalationHeatmap,
  getPipelineStages,
  getReviewById,
  getTeamMemberById,
  reassignTrip,
  updateApprovalThresholds,
  updateAutonomyPolicy,
  updatePipelineStages,
  type AgencyAutonomyPolicy,
  type UpdateAutonomyPolicyRequest,
} from '../governance-api';

const jsonResponse = (body: unknown) => new Response(JSON.stringify(body), {
  status: 200,
  headers: { 'Content-Type': 'application/json' },
});

describe('governance-api public contract surface', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn(async () => jsonResponse({ ok: true, items: [], total: 0, hasMore: false })));
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('keeps review, insight, team, audit, settings, and export endpoints stable', async () => {
    const fetchMock = vi.mocked(fetch);

    await getReviewById('review-1');
    expect(fetchMock).toHaveBeenLastCalledWith('/api/reviews/review-1', expect.objectContaining({ method: 'GET' }));

    await getEscalationHeatmap('7d');
    expect(fetchMock).toHaveBeenLastCalledWith('/api/insights/escalations?range=7d', expect.objectContaining({ method: 'GET' }));

    await getConversionFunnel('90d');
    expect(fetchMock).toHaveBeenLastCalledWith('/api/insights/funnel?range=90d', expect.objectContaining({ method: 'GET' }));

    await getTeamMemberById('member-1');
    expect(fetchMock).toHaveBeenLastCalledWith('/api/team/members/member-1', expect.objectContaining({ method: 'GET' }));

    await reassignTrip({ tripId: 'trip-1', fromUserId: 'agent-a', toUserId: 'agent-b', reason: 'coverage' });
    expect(fetchMock).toHaveBeenLastCalledWith('/api/inbox/reassign', expect.objectContaining({ method: 'POST' }));

    await getAuditEvents(2, 25);
    expect(fetchMock).toHaveBeenLastCalledWith('/api/audit?page=2&limit=25', expect.objectContaining({ method: 'GET' }));

    await getAuditEventsByTrip('trip-1');
    expect(fetchMock).toHaveBeenLastCalledWith('/api/audit/trip/trip-1', expect.objectContaining({ method: 'GET' }));

    await getPipelineStages();
    expect(fetchMock).toHaveBeenLastCalledWith('/api/settings/pipeline', expect.objectContaining({ method: 'GET' }));

    await updatePipelineStages([]);
    expect(fetchMock).toHaveBeenLastCalledWith('/api/settings/pipeline', expect.objectContaining({ method: 'PUT', body: JSON.stringify({ stages: [] }) }));

    await getApprovalThresholds();
    expect(fetchMock).toHaveBeenLastCalledWith('/api/settings/approvals', expect.objectContaining({ method: 'GET' }));

    await updateApprovalThresholds([]);
    expect(fetchMock).toHaveBeenLastCalledWith('/api/settings/approvals', expect.objectContaining({ method: 'PUT', body: JSON.stringify({ thresholds: [] }) }));

    await getAutonomyPolicy('agency-1');
    expect(fetchMock).toHaveBeenLastCalledWith('/api/settings/autonomy?agency_id=agency-1', expect.objectContaining({ method: 'GET' }));

    const autonomyRequest: UpdateAutonomyPolicyRequest = { allow_explicit_reassess: true };
    await updateAutonomyPolicy(autonomyRequest, 'agency-1');
    expect(fetchMock).toHaveBeenLastCalledWith('/api/settings/autonomy?agency_id=agency-1', expect.objectContaining({
      method: 'POST',
      body: JSON.stringify(autonomyRequest),
    }));

    await exportInsights('30d', 'csv');
    expect(fetchMock).toHaveBeenLastCalledWith('/api/insights/export', expect.objectContaining({
      method: 'POST',
      body: JSON.stringify({ timeRange: '30d', format: 'csv' }),
    }));
  });

  it('keeps autonomy policy types importable for settings consumers', () => {
    const policy: AgencyAutonomyPolicy = {
      approval_gates: { proposal: 'review' },
      mode_overrides: { proposal: { expensive_trip: 'review' } },
      auto_proceed_with_warnings: false,
      learn_from_overrides: true,
      auto_reprocess_on_edit: true,
      allow_explicit_reassess: true,
      auto_reprocess_stages: { proposal: true },
      min_proceed_confidence: 0.8,
      min_draft_confidence: 0.6,
    };

    expect(policy.approval_gates.proposal).toBe('review');
  });
});
