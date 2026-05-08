/**
 * Governance API Client
 *
 * Handles all API calls for owner/management features:
 * - Reviews and approvals
 * - Analytics and insights
 * - Team management
 * - Inbox operations
 */

import { api } from './api-client';
import type {
  TripReview,
  ReviewFilters,
  ReviewActionRequest,
  InsightsSummary,
  TimeRange,
  StageMetrics,
  TeamMemberMetrics,
  BottleneckAnalysis,
  RevenueMetrics,
  EscalationHeatmap,
  ConversionFunnel,
  TeamMember,
  WorkloadDistribution,
  AssignmentRequest,
  ReassignmentRequest,
  InboxTrip,
  InboxFilters,
  BulkActionRequest,
  AuditEvent,
  PipelineStage,
  ApprovalThreshold,
  OperationalAlert,
} from '@/types/governance';

// ============================================================================
// WORKSPACE API
// ============================================================================

export interface WorkspaceInfo {
  id: string;
  name: string;
  slug: string;
  email: string | null;
  phone: string | null;
  logo_url: string | null;
  plan: string | null;
  settings: Record<string, unknown>;
  workspace_code: string | null;
}

export async function getWorkspace(): Promise<WorkspaceInfo> {
  const res = await api.get<{ ok: boolean; workspace: WorkspaceInfo }>('/api/workspace');
  return res.workspace;
}

export async function generateWorkspaceCode(codeType: 'internal' | 'external' = 'internal'): Promise<string> {
  const res = await api.post<{ ok: boolean; code: string }>('/api/workspace/codes', { code_type: codeType });
  return res.code;
}

// ============================================================================
// REVIEWS API
// ============================================================================

export async function getReviews(
  filters?: ReviewFilters,
): Promise<{ items: TripReview[]; total: number }> {
  const params = new URLSearchParams();
  if (filters?.status) params.set('status', filters.status);
  if (filters?.minValue) params.set('minValue', filters.minValue.toString());
  if (filters?.maxValue) params.set('maxValue', filters.maxValue.toString());
  if (filters?.agentId) params.set('agentId', filters.agentId);
  if (filters?.submittedAfter)
    params.set('submittedAfter', filters.submittedAfter);
  if (filters?.submittedBefore)
    params.set('submittedBefore', filters.submittedBefore);

  const query = params.toString();
  return api.get(`/api/reviews${query ? `?${query}` : ''}`);
}

export async function getReviewById(id: string): Promise<TripReview> {
  return api.get(`/api/reviews/${id}`);
}

export async function submitReviewAction(
  request: ReviewActionRequest,
): Promise<{ success: boolean; review: TripReview }> {
  return api.post('/api/reviews/action', request);
}

export async function bulkReviewAction(
  requests: ReviewActionRequest[],
): Promise<{ success: boolean; processed: number; failed: number }> {
  return api.post('/api/reviews/bulk-action', { actions: requests });
}

// ============================================================================
// INSIGHTS API
// ============================================================================

export async function getInsightsSummary(
  timeRange: TimeRange = '30d',
): Promise<InsightsSummary> {
  return api.get(`/api/insights/summary?range=${timeRange}`);
}

export async function getPipelineMetrics(
  timeRange: TimeRange = '30d',
): Promise<StageMetrics[]> {
  return api.get(`/api/insights/pipeline?range=${timeRange}`);
}

export async function getTeamMetrics(
  timeRange: TimeRange = '30d',
): Promise<TeamMemberMetrics[]> {
  return api.get(`/api/insights/team?range=${timeRange}`);
}

export async function getBottleneckAnalysis(
  timeRange: TimeRange = '30d',
): Promise<BottleneckAnalysis[]> {
  return api.get(`/api/insights/bottlenecks?range=${timeRange}`);
}

export async function getRevenueMetrics(
  timeRange: TimeRange = '30d',
): Promise<RevenueMetrics> {
  return api.get(`/api/insights/revenue?range=${timeRange}`);
}

export async function getEscalationHeatmap(
  timeRange: TimeRange = '30d',
): Promise<EscalationHeatmap[]> {
  return api.get(`/api/insights/escalations?range=${timeRange}`);
}

export async function getConversionFunnel(
  timeRange: TimeRange = '30d',
): Promise<ConversionFunnel[]> {
  return api.get(`/api/insights/funnel?range=${timeRange}`);
}

export async function getOperationalAlerts(): Promise<OperationalAlert[]> {
  return api.get('/api/insights/alerts');
}

export async function dismissAlert(
  alertId: string,
): Promise<{ success: boolean }> {
  return api.post(`/api/insights/alerts/${alertId}/dismiss`);
}

// ============================================================================
// TEAM MANAGEMENT API
// ============================================================================

export async function getTeamMembers(): Promise<TeamMember[]> {
  const res = await api.get<{ items: TeamMember[]; total: number }>('/api/team/members');
  return res.items;
}

export async function getTeamMemberById(id: string): Promise<TeamMember> {
  return api.get(`/api/team/members/${id}`);
}

export async function inviteTeamMember(data: {
  email: string;
  name: string;
  role: string;
  capacity?: number;
}): Promise<{ success: boolean; member: TeamMember }> {
  return api.post('/api/team/invite', data);
}

export async function updateTeamMember(
  id: string,
  data: Partial<TeamMember>,
): Promise<TeamMember> {
  return api.patch(`/api/team/members/${id}`, data);
}

export async function deactivateTeamMember(
  id: string,
): Promise<{ success: boolean }> {
  return api.delete(`/api/team/members/${id}`);
}

export async function getWorkloadDistribution(): Promise<
  WorkloadDistribution[]
> {
  const res = await api.get<{ items: WorkloadDistribution[] }>('/api/team/workload');
  return res.items;
}

// ============================================================================
// INBOX API
// ============================================================================

export async function getInboxTrips(
  filters?: InboxFilters,
  page: number = 1,
  limit: number = 20,
  sortBy?: string,
  sortDir?: string,
  searchQuery?: string,
): Promise<{ items: InboxTrip[]; total: number; hasMore: boolean; filterCounts?: Record<string, number> }> {
  const params = new URLSearchParams();
  params.set('page', page.toString());
  params.set('limit', limit.toString());

  if (filters?.filterTab) params.set('filter', filters.filterTab);
  if (filters?.priority) params.set('priority', filters.priority.join(','));
  if (filters?.stage) params.set('stage', filters.stage.join(','));
  if (filters?.assignedTo)
    params.set('assignedTo', filters.assignedTo.join(','));
  if (filters?.slaStatus) params.set('slaStatus', filters.slaStatus.join(','));
  if (filters?.minValue) params.set('minValue', filters.minValue.toString());
  if (filters?.maxValue) params.set('maxValue', filters.maxValue.toString());
  if (sortBy) params.set('sort', sortBy);
  if (sortDir) params.set('dir', sortDir);
  if (searchQuery) params.set('q', searchQuery);

  return api.get(`/api/inbox?${params.toString()}`);
}

export async function assignTrips(
  request: AssignmentRequest,
): Promise<{ success: boolean; assigned: number }> {
  return api.post('/api/inbox/assign', request);
}

export async function reassignTrip(
  request: ReassignmentRequest,
): Promise<{ success: boolean }> {
  return api.post('/api/inbox/reassign', request);
}

export async function bulkInboxAction(
  request: BulkActionRequest,
): Promise<{ success: boolean; processed: number; failed: number }> {
  return api.post('/api/inbox/bulk', request);
}

export async function snoozeTrip(
  tripId: string,
  snoozeUntil: string,
): Promise<{ success: boolean }> {
  return api.post(`/api/inbox/${tripId}/snooze`, { snoozeUntil });
}

export async function getInboxStats(): Promise<{
  total: number;
  unassigned: number;
  critical: number;
  atRisk: number;
}> {
  return api.get('/api/inbox/stats');
}

// ============================================================================
// AUDIT LOG API
// ============================================================================

export async function getAuditEvents(
  page: number = 1,
  limit: number = 50,
): Promise<{ items: AuditEvent[]; total: number; hasMore: boolean }> {
  return api.get(`/api/audit?page=${page}&limit=${limit}`);
}

export async function getAuditEventsByTrip(
  tripId: string,
): Promise<AuditEvent[]> {
  return api.get(`/api/audit/trip/${tripId}`);
}

// ============================================================================
// SETTINGS API
// ============================================================================

export async function getPipelineStages(): Promise<PipelineStage[]> {
  return api.get('/api/settings/pipeline');
}

export async function updatePipelineStages(
  stages: PipelineStage[],
): Promise<{ success: boolean }> {
  return api.put('/api/settings/pipeline', { stages });
}

export async function getApprovalThresholds(): Promise<ApprovalThreshold[]> {
  return api.get('/api/settings/approvals');
}

export async function updateApprovalThresholds(
  thresholds: ApprovalThreshold[],
): Promise<{ success: boolean }> {
  return api.put('/api/settings/approvals', { thresholds });
}

// ============================================================================
// D1 AUTONOMY SETTINGS API
// ============================================================================

export interface AgencyAutonomyPolicy {
  approval_gates: Record<string, 'auto' | 'review' | 'block'>;
  mode_overrides: Record<string, Record<string, string>>;
  auto_proceed_with_warnings: boolean;
  learn_from_overrides: boolean;
  auto_reprocess_on_edit: boolean;
  allow_explicit_reassess: boolean;
  auto_reprocess_stages: Record<string, boolean>;
  min_proceed_confidence?: number;
  min_draft_confidence?: number;
}

export async function getAutonomyPolicy(
  agencyId?: string,
): Promise<AgencyAutonomyPolicy & { agency_id: string }> {
  const query = agencyId ? `?agency_id=${encodeURIComponent(agencyId)}` : '';
  return api.get(`/api/settings/autonomy${query}`);
}

export interface UpdateAutonomyPolicyRequest {
  approval_gates?: Record<string, 'auto' | 'review' | 'block'>;
  mode_overrides?: Record<string, Record<string, string>>;
  auto_proceed_with_warnings?: boolean;
  learn_from_overrides?: boolean;
  auto_reprocess_on_edit?: boolean;
  allow_explicit_reassess?: boolean;
  auto_reprocess_stages?: Record<string, boolean>;
}

export async function updateAutonomyPolicy(
  request: UpdateAutonomyPolicyRequest,
  agencyId?: string,
): Promise<AgencyAutonomyPolicy & { agency_id: string; changes: string[] }> {
  const query = agencyId ? `?agency_id=${encodeURIComponent(agencyId)}` : '';
  return api.post(`/api/settings/autonomy${query}`, request);
}

// ============================================================================
// EXPORT API
// ============================================================================

export async function exportInsights(
  timeRange: TimeRange,
  format: 'csv' | 'pdf' = 'csv',
): Promise<{ downloadUrl: string; expiresAt: string }> {
  return api.post('/api/insights/export', { timeRange, format });
}
