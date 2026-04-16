/**
 * Governance API Client
 * 
 * Handles all API calls for owner/management features:
 * - Reviews and approvals
 * - Analytics and insights
 * - Team management
 * - Inbox operations
 */

import { api } from "./api-client";
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
} from "@/types/governance";

// ============================================================================
// REVIEWS API
// ============================================================================

export async function getReviews(
  filters?: ReviewFilters
): Promise<{ items: TripReview[]; total: number }> {
  const params = new URLSearchParams();
  if (filters?.status) params.set("status", filters.status);
  if (filters?.minValue) params.set("minValue", filters.minValue.toString());
  if (filters?.maxValue) params.set("maxValue", filters.maxValue.toString());
  if (filters?.agentId) params.set("agentId", filters.agentId);
  if (filters?.submittedAfter) params.set("submittedAfter", filters.submittedAfter);
  if (filters?.submittedBefore) params.set("submittedBefore", filters.submittedBefore);
  
  const query = params.toString();
  return api.get(`/api/reviews${query ? `?${query}` : ""}`);
}

export async function getReviewById(id: string): Promise<TripReview> {
  return api.get(`/api/reviews/${id}`);
}

export async function submitReviewAction(
  request: ReviewActionRequest
): Promise<{ success: boolean; review: TripReview }> {
  return api.post("/api/reviews/action", request);
}

export async function bulkReviewAction(
  requests: ReviewActionRequest[]
): Promise<{ success: boolean; processed: number; failed: number }> {
  return api.post("/api/reviews/bulk-action", { actions: requests });
}

// ============================================================================
// INSIGHTS API
// ============================================================================

export async function getInsightsSummary(
  timeRange: TimeRange = "30d"
): Promise<InsightsSummary> {
  return api.get(`/api/insights/summary?range=${timeRange}`);
}

export async function getPipelineMetrics(
  timeRange: TimeRange = "30d"
): Promise<StageMetrics[]> {
  return api.get(`/api/insights/pipeline?range=${timeRange}`);
}

export async function getTeamMetrics(
  timeRange: TimeRange = "30d"
): Promise<TeamMemberMetrics[]> {
  return api.get(`/api/insights/team?range=${timeRange}`);
}

export async function getBottleneckAnalysis(
  timeRange: TimeRange = "30d"
): Promise<BottleneckAnalysis[]> {
  return api.get(`/api/insights/bottlenecks?range=${timeRange}`);
}

export async function getRevenueMetrics(
  timeRange: TimeRange = "30d"
): Promise<RevenueMetrics> {
  return api.get(`/api/insights/revenue?range=${timeRange}`);
}

export async function getEscalationHeatmap(
  timeRange: TimeRange = "30d"
): Promise<EscalationHeatmap[]> {
  return api.get(`/api/insights/escalations?range=${timeRange}`);
}

export async function getConversionFunnel(
  timeRange: TimeRange = "30d"
): Promise<ConversionFunnel[]> {
  return api.get(`/api/insights/funnel?range=${timeRange}`);
}

// ============================================================================
// TEAM MANAGEMENT API
// ============================================================================

export async function getTeamMembers(): Promise<TeamMember[]> {
  return api.get("/api/team/members");
}

export async function getTeamMemberById(id: string): Promise<TeamMember> {
  return api.get(`/api/team/members/${id}`);
}

export async function inviteTeamMember(data: {
  email: string;
  name: string;
  role: string;
  capacity?: number;
}): Promise<{ success: boolean; invitationSent: boolean }> {
  return api.post("/api/team/invite", data);
}

export async function updateTeamMember(
  id: string,
  data: Partial<TeamMember>
): Promise<TeamMember> {
  return api.patch(`/api/team/members/${id}`, data);
}

export async function deactivateTeamMember(
  id: string
): Promise<{ success: boolean }> {
  return api.delete(`/api/team/members/${id}`);
}

export async function getWorkloadDistribution(): Promise<WorkloadDistribution[]> {
  return api.get("/api/team/workload");
}

// ============================================================================
// INBOX API
// ============================================================================

export async function getInboxTrips(
  filters?: InboxFilters,
  page: number = 1,
  limit: number = 20
): Promise<{ items: InboxTrip[]; total: number; hasMore: boolean }> {
  const params = new URLSearchParams();
  params.set("page", page.toString());
  params.set("limit", limit.toString());
  
  if (filters?.priority) params.set("priority", filters.priority.join(","));
  if (filters?.stage) params.set("stage", filters.stage.join(","));
  if (filters?.assignedTo) params.set("assignedTo", filters.assignedTo.join(","));
  if (filters?.slaStatus) params.set("slaStatus", filters.slaStatus.join(","));
  if (filters?.minValue) params.set("minValue", filters.minValue.toString());
  if (filters?.maxValue) params.set("maxValue", filters.maxValue.toString());
  
  return api.get(`/api/inbox?${params.toString()}`);
}

export async function assignTrips(
  request: AssignmentRequest
): Promise<{ success: boolean; assigned: number }> {
  return api.post("/api/inbox/assign", request);
}

export async function reassignTrip(
  request: ReassignmentRequest
): Promise<{ success: boolean }> {
  return api.post("/api/inbox/reassign", request);
}

export async function bulkInboxAction(
  request: BulkActionRequest
): Promise<{ success: boolean; processed: number; failed: number }> {
  return api.post("/api/inbox/bulk", request);
}

export async function snoozeTrip(
  tripId: string,
  snoozeUntil: string
): Promise<{ success: boolean }> {
  return api.post(`/api/inbox/${tripId}/snooze`, { snoozeUntil });
}

export async function getInboxStats(): Promise<{
  total: number;
  unassigned: number;
  critical: number;
  atRisk: number;
}> {
  return api.get("/api/inbox/stats");
}

// ============================================================================
// AUDIT LOG API
// ============================================================================

export async function getAuditEvents(
  page: number = 1,
  limit: number = 50
): Promise<{ items: AuditEvent[]; total: number; hasMore: boolean }> {
  return api.get(`/api/audit?page=${page}&limit=${limit}`);
}

export async function getAuditEventsByTrip(
  tripId: string
): Promise<AuditEvent[]> {
  return api.get(`/api/audit/trip/${tripId}`);
}

// ============================================================================
// SETTINGS API
// ============================================================================

export async function getPipelineStages(): Promise<PipelineStage[]> {
  return api.get("/api/settings/pipeline");
}

export async function updatePipelineStages(
  stages: PipelineStage[]
): Promise<{ success: boolean }> {
  return api.put("/api/settings/pipeline", { stages });
}

export async function getApprovalThresholds(): Promise<ApprovalThreshold[]> {
  return api.get("/api/settings/approvals");
}

export async function updateApprovalThresholds(
  thresholds: ApprovalThreshold[]
): Promise<{ success: boolean }> {
  return api.put("/api/settings/approvals", { thresholds });
}

// ============================================================================
// EXPORT API
// ============================================================================

export async function exportInsights(
  timeRange: TimeRange,
  format: 'csv' | 'pdf' = 'csv'
): Promise<{ downloadUrl: string; expiresAt: string }> {
  return api.post("/api/insights/export", { timeRange, format });
}
