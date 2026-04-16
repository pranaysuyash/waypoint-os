/**
 * Governance Types
 * 
 * Type definitions for owner/management features:
 * - Reviews and approvals
 * - Analytics and insights
 * - Team management
 * - Audit logging
 */

// ============================================================================
// REVIEWS & APPROVALS
// ============================================================================

export type ReviewStatus = 'pending' | 'approved' | 'rejected' | 'escalated';

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
  reason: string; // Why it needs review
  agentNotes?: string;
  ownerNotes?: string;
  reviewedAt?: string;
  reviewedBy?: string;
  riskFlags: RiskFlag[];
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
  action: 'approve' | 'reject' | 'escalate' | 'request_changes';
  notes?: string;
  reassignTo?: string; // Agent ID for reassignment
}

// ============================================================================
// ANALYTICS & INSIGHTS
// ============================================================================

export type TimeRange = '7d' | '30d' | '90d' | 'mtd' | 'ytd' | 'custom';

export interface InsightsSummary {
  totalInquiries: number;
  convertedToBooked: number;
  conversionRate: number; // 0-100
  avgResponseTime: number; // in hours
  pipelineValue: number;
  pipelineVelocity: PipelineVelocity;
}

export interface PipelineVelocity {
  stage1To2: number; // days
  stage2To3: number;
  stage3To4: number;
  stage4To5: number;
  stage5ToBooked: number;
  averageTotal: number;
}

export interface StageMetrics {
  stageId: string;
  stageName: string;
  tripCount: number;
  avgTimeInStage: number; // hours
  exitRate: number; // % that proceed to next stage
  avgTimeToExit: number; // hours
}

export interface TeamMemberMetrics {
  userId: string;
  name: string;
  role: string;
  activeTrips: number;
  completedTrips: number;
  conversionRate: number;
  avgResponseTime: number; // hours
  customerSatisfaction: number; // 1-5
  currentWorkload: 'under' | 'optimal' | 'over' | 'critical';
  workloadScore: number; // 0-100
}

export interface BottleneckAnalysis {
  stageId: string;
  stageName: string;
  avgTimeInStage: number;
  isBottleneck: boolean;
  severity: 'low' | 'medium' | 'high' | 'critical';
  primaryCauses: BottleneckCause[];
}

export interface BottleneckCause {
  cause: string;
  percentage: number; // % of delays attributed to this cause
  affectedTrips: number;
  suggestedAction: string;
}

export interface RevenueMetrics {
  period: string;
  totalPipelineValue: number;
  bookedRevenue: number;
  projectedRevenue: number;
  avgTripValue: number;
  revenueByMonth: MonthlyRevenue[];
}

export interface MonthlyRevenue {
  month: string;
  inquiries: number;
  booked: number;
  revenue: number;
}

export interface EscalationHeatmap {
  date: string;
  escalationCount: number;
  avgResolutionTime: number;
}

export interface ConversionFunnel {
  stage: string;
  count: number;
  conversionRate: number; // from previous stage
  dropOffRate: number;
  avgTimeToConvert: number;
}

// ============================================================================
// TEAM MANAGEMENT
// ============================================================================

export type UserRole = 'owner' | 'manager' | 'agent' | 'viewer';

export interface TeamMember {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  avatarUrl?: string;
  isActive: boolean;
  joinedAt: string;
  lastActiveAt?: string;
  capacity: number; // max trips they can handle
  currentAssignments: number;
  expertise?: string[]; // e.g., ['luxury', 'corporate', 'adventure']
}

export interface WorkloadDistribution {
  userId: string;
  name: string;
  capacity: number;
  currentLoad: number;
  loadPercentage: number;
  status: 'under' | 'optimal' | 'near_limit' | 'over_capacity';
  trips: WorkloadTrip[];
}

export interface WorkloadTrip {
  tripId: string;
  destination: string;
  stage: string;
  urgency: 'low' | 'medium' | 'high' | 'critical';
  value: number;
}

export interface AssignmentRequest {
  tripIds: string[];
  assignTo: string; // userId
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
// INBOX & TRIAGE
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
  priorityScore: number; // 0-100
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
  priority?: TripPriority[];
  stage?: string[];
  assignedTo?: string[];
  slaStatus?: ('on_track' | 'at_risk' | 'breached')[];
  dateRange?: { from: string; to: string };
  minValue?: number;
  maxValue?: number;
}

export interface BulkActionRequest {
  tripIds: string[];
  action: 'assign' | 'snooze' | 'export' | 'update_stage' | 'add_tag';
  params: Record<string, unknown>;
}

// ============================================================================
// AUDIT & COMPLIANCE
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
// SETTINGS & CONFIGURATION
// ============================================================================

export interface PipelineStage {
  id: string;
  name: string;
  description: string;
  order: number;
  isActive: boolean;
  requiredFields: string[];
  autoAdvanceRules?: AutoAdvanceRule[];
  slaHours: number; // expected time in this stage
}

export interface AutoAdvanceRule {
  id: string;
  condition: string; // e.g., "all_fields_complete AND supplier_confirmed"
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
  approverRole: 'owner' | 'manager';
}

export interface NotificationTemplate {
  id: string;
  event: string;
  subject: string;
  body: string;
  isActive: boolean;
}
