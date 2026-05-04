/**
 * Governance Types
 *
 * Re-exports analytics types from the generated backend contract.
 * Frontend-only types (reviews, team management, inbox triage, settings)
 * remain here as they represent UI presentation concerns.
 *
 * DO NOT manually define types that exist in the generated file.
 * To regenerate: uv run python scripts/generate_types.py
 */

// Re-export generated analytics/contract types
export type {
  InsightsSummary,
  PipelineVelocity,
  StageMetrics,
  TeamMemberMetrics,
  BottleneckAnalysis,
  BottleneckCause,
  RevenueMetrics,
  MonthlyRevenue,
  OperationalAlert,
  AnalyticsPayload,
} from '@/types/generated/spine-api';

// ============================================================================
// REVIEWS & APPROVALS (frontend-only presentation)
// ============================================================================

export type ReviewStatus = 'pending' | 'approved' | 'rejected' | 'escalated' | 'revision_needed';

export interface TripReview {
  id: string;
  tripId: string;
  tripReference: string;
  destination: string;
  tripType: string;
  partySize: number;
  dateWindow: string;
  value: number;
  currency: string;
  agentId: string;
  agentName: string;
  submittedAt: string;
  status: ReviewStatus;
  reason: string;
  agentNotes?: string;
  ownerNotes?: string;
  reviewedAt?: string;
  reviewedBy?: string;
  riskFlags: RiskFlag[];
  feedbackSeverity?: 'low' | 'medium' | 'high' | 'critical';
  followupNeeded?: boolean;
  recoveryStatus?: 'PENDING_NOTIFY' | 'IN_RECOVERY' | 'RESOLVED';
  recoveryStartedAt?: string;
  recoveryDeadline?: string;
  isEscalated?: boolean;
  slaStatus?: 'on_track' | 'at_risk' | 'breached';
}

export type RiskFlag =
  | 'high_value'
  | 'unusual_destination'
  | 'tight_deadline'
  | 'complex_itinerary'
  | 'visa_required'
  | 'supplier_delay';

export interface ReviewFilters {
  status?: ReviewStatus;
  minValue?: number;
  maxValue?: number;
  agentId?: string;
  riskFlags?: RiskFlag[];
  submittedAfter?: string;
  submittedBefore?: string;
}

export interface ReviewActionRequest {
  reviewId: string;
  action: 'approve' | 'reject' | 'escalate' | 'request_changes' | 'resolve';
  notes?: string;
  reassignTo?: string;
}

// ============================================================================
// TIME RANGE (frontend-only filter concern)
// ============================================================================

export type TimeRange = '7d' | '30d' | '90d' | 'mtd' | 'ytd' | 'custom';

// ============================================================================
// TEAM MANAGEMENT (frontend-only presentation)
// ============================================================================

export type UserRole = 'owner' | 'admin' | 'senior_agent' | 'junior_agent' | 'viewer';

export interface TeamMember {
  id: string;
  user_id: string;
  name: string;
  email: string;
  role: UserRole;
  capacity: number;
  status: string;
  specializations: string[];
  created_at: string;
  updated_at?: string | null;
}

export interface WorkloadDistribution {
  memberId: string;
  name: string;
  role: UserRole;
  capacity: number;
  assigned: number;
  available: number;
  loadPercentage: number;
  status: 'under' | 'optimal' | 'near_limit' | 'over_capacity';
}

export interface AssignmentRequest {
  tripIds: string[];
  assignTo: string;
  reason?: string;
  notifyAssignee: boolean;
}

export interface ReassignmentRequest {
  tripId: string;
  fromUserId: string;
  toUserId: string;
  reason: string;
}

// ============================================================================
// INBOX & TRIAGE (frontend-only presentation)
// ============================================================================

export type TripPriority = 'low' | 'medium' | 'high' | 'critical';

export interface InboxTrip {
  id: string;
  reference: string;
  destination: string;
  tripType: string;
  partySize: number;
  dateWindow: string;
  value: number;
  priority: TripPriority;
  priorityScore: number;
  stage: string;
  stageNumber: number;
  assignedTo?: string;
  assignedToName?: string;
  submittedAt: string;
  lastUpdated: string;
  daysInCurrentStage: number;
  slaStatus: 'on_track' | 'at_risk' | 'breached';
  customerName: string;
  flags: string[];
}

export interface InboxFilters {
  priority?: readonly TripPriority[];
  stage?: readonly string[];
  assignedTo?: readonly string[];
  slaStatus?: readonly ('on_track' | 'at_risk' | 'breached')[];
  dateRange?: { from: string; to: string };
  minValue?: number;
  maxValue?: number;
  filterTab?: 'all' | 'at_risk' | 'incomplete' | 'unassigned';
}

export interface BulkActionRequest {
  tripIds: string[];
  action: 'assign' | 'snooze' | 'export' | 'update_stage' | 'add_tag';
  params: Record<string, unknown>;
}

// ============================================================================
// AUDIT & COMPLIANCE (frontend-only presentation)
// ============================================================================

export type AuditEventType =
  | 'trip_created'
  | 'trip_updated'
  | 'trip_assigned'
  | 'trip_approved'
  | 'trip_rejected'
  | 'trip_completed'
  | 'user_invited'
  | 'user_removed'
  | 'settings_changed'
  | 'review_submitted';

export interface AuditEvent {
  id: string;
  type: AuditEventType;
  userId: string;
  userName: string;
  timestamp: string;
  details: Record<string, unknown>;
  ipAddress?: string;
  userAgent?: string;
}

// ============================================================================
// SETTINGS & CONFIGURATION (frontend-only presentation)
// ============================================================================

export interface PipelineStage {
  id: string;
  name: string;
  description: string;
  order: number;
  isActive: boolean;
  requiredFields: string[];
  autoAdvanceRules?: AutoAdvanceRule[];
  slaHours: number;
}

export interface AutoAdvanceRule {
  id: string;
  condition: string;
  action: 'advance' | 'notify' | 'alert';
  targetStageId?: string;
}

export interface ApprovalThreshold {
  id: string;
  name: string;
  minValue?: number;
  maxValue?: number;
  tripTypes?: string[];
  destinations?: string[];
  riskFlags?: RiskFlag[];
  requiresApproval: boolean;
  approverRole: 'owner' | 'admin' | 'senior_agent';
}

export interface NotificationTemplate {
  id: string;
  event: string;
  subject: string;
  body: string;
  isActive: boolean;
}

export interface ConversionFunnel {
  stage: string;
  count: number;
  conversionRate: number;
  dropOffRate: number;
  avgTimeToConvert: number;
}

export interface EscalationHeatmap {
  date: string;
  escalationCount: number;
  avgResolutionTime: number;
}
