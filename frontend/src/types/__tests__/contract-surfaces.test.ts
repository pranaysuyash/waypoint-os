import { describe, expect, it } from 'vitest';
import type { OverviewStateKey } from '@/app/(agency)/overview/useOverviewSummary';
import type { FilterConfig } from '@/components/inbox/InboxFilterBar';
import type { UnifiedState } from '@/hooks/useUnifiedState';
import type { DevScenarioInput } from '@/lib/dev-scenario-generator';
import type { NavItem } from '@/lib/nav-modules';
import type { WorkbenchTab } from '@/lib/routes';
import type { ScenarioExpected, ScenarioFixture, ScenarioInputs } from '@/lib/scenario-loader';
import type { AuthAgency, AuthMembership, AuthUser } from '@/stores/auth';
import type {
  AnalyticsPayload as GovernanceAnalyticsPayload,
  AuditEventType,
  AutoAdvanceRule,
  BottleneckCause as GovernanceBottleneckCause,
  MonthlyRevenue as GovernanceMonthlyRevenue,
  NotificationTemplate,
  PipelineVelocity as GovernancePipelineVelocity,
  UserRole,
} from '@/types/governance';
import type {
  AssertionResult as SpineAssertionResult,
  AutonomyOutcome as SpineAutonomyOutcome,
  ConfidenceScorecard,
  DashboardStatsResponse as SpineDashboardStatsResponse,
  FeeBreakdown,
  HealthResponse as SpineHealthResponse,
  IntegrityMeta as SpineIntegrityMeta,
  OrphanTrip as SpineOrphanTrip,
  OverrideResponse as SpineOverrideResponse,
  RunAcceptedResponse as SpineRunAcceptedResponse,
  RunEvent,
  RunMeta as SpineRunMeta,
  SuitabilityFlagsResponse as SpineSuitabilityFlagsResponse,
  SuitabilitySignal as SpineSuitabilitySignal,
  SystemicError as SpineSystemicError,
  UnifiedStateResponse as SpineUnifiedStateResponse,
} from '@/types/spine';
import type {
  AnalyticsPayload,
  ApprovalThresholdConfig,
  AssertionResult,
  AutonomyOutcome,
  BottleneckCause,
  DashboardStatsResponse,
  ExportRequest,
  ExportResponse,
  FrontierOrchestrationResult,
  HealthResponse,
  IntegrityMeta,
  InviteTeamMemberRequest,
  MonthlyRevenue,
  NegotiationLog,
  OrphanTrip,
  OverrideRequest,
  OverrideResponse,
  PipelineStageConfig,
  PipelineVelocity,
  PublicCheckerArtifactManifest,
  PublicCheckerArtifactUpload,
  PublicCheckerDeleteResponse,
  PublicCheckerExportResponse,
  QualityScore,
  ReviewActionRequest,
  RunAcceptedResponse,
  RunMeta,
  RunStatusResponse,
  SnoozeRequest,
  SpecialtyKnowledgeHit,
  SuitabilityAcknowledgeRequest,
  SuitabilityFlagsResponse,
  SuitabilitySignal,
  SystemicError,
  TeamMember,
  TripListResponse,
  UnifiedStateResponse,
  UpdateAutonomyPolicy,
  UpdateOperationalSettings,
} from '@/types/generated/spine-api';

function contract<T>(name: string): string {
  return name satisfies string;
}

describe('public type contract surfaces', () => {
  it('keeps frontend-owned presentation types importable', () => {
    const names = [
      contract<OverviewStateKey>('OverviewStateKey'),
      contract<FilterConfig>('FilterConfig'),
      contract<UnifiedState>('UnifiedState'),
      contract<DevScenarioInput>('DevScenarioInput'),
      contract<NavItem>('NavItem'),
      contract<WorkbenchTab>('WorkbenchTab'),
      contract<ScenarioInputs>('ScenarioInputs'),
      contract<ScenarioExpected>('ScenarioExpected'),
      contract<ScenarioFixture>('ScenarioFixture'),
      contract<AuthUser>('AuthUser'),
      contract<AuthAgency>('AuthAgency'),
      contract<AuthMembership>('AuthMembership'),
      contract<UserRole>('UserRole'),
      contract<AuditEventType>('AuditEventType'),
      contract<AutoAdvanceRule>('AutoAdvanceRule'),
      contract<NotificationTemplate>('NotificationTemplate'),
      contract<GovernancePipelineVelocity>('GovernancePipelineVelocity'),
      contract<GovernanceBottleneckCause>('GovernanceBottleneckCause'),
      contract<GovernanceMonthlyRevenue>('GovernanceMonthlyRevenue'),
      contract<GovernanceAnalyticsPayload>('GovernanceAnalyticsPayload'),
    ];

    expect(names).toContain('WorkbenchTab');
  });

  it('keeps spine mirror and generated backend contracts importable', () => {
    const names = [
      contract<SpineAssertionResult>('SpineAssertionResult'),
      contract<SpineAutonomyOutcome>('SpineAutonomyOutcome'),
      contract<SpineRunMeta>('SpineRunMeta'),
      contract<SpineOverrideResponse>('SpineOverrideResponse'),
      contract<SpineHealthResponse>('SpineHealthResponse'),
      contract<SpineDashboardStatsResponse>('SpineDashboardStatsResponse'),
      contract<SpineUnifiedStateResponse>('SpineUnifiedStateResponse'),
      contract<SpineIntegrityMeta>('SpineIntegrityMeta'),
      contract<SpineSystemicError>('SpineSystemicError'),
      contract<SpineOrphanTrip>('SpineOrphanTrip'),
      contract<SpineSuitabilitySignal>('SpineSuitabilitySignal'),
      contract<SpineRunAcceptedResponse>('SpineRunAcceptedResponse'),
      contract<RunEvent>('RunEvent'),
      contract<ConfidenceScorecard>('ConfidenceScorecard'),
      contract<SpineSuitabilityFlagsResponse>('SpineSuitabilityFlagsResponse'),
      contract<FeeBreakdown>('FeeBreakdown'),
      contract<AnalyticsPayload>('AnalyticsPayload'),
      contract<ApprovalThresholdConfig>('ApprovalThresholdConfig'),
      contract<AssertionResult>('AssertionResult'),
      contract<AutonomyOutcome>('AutonomyOutcome'),
      contract<BottleneckCause>('BottleneckCause'),
      contract<DashboardStatsResponse>('DashboardStatsResponse'),
      contract<ExportRequest>('ExportRequest'),
      contract<ExportResponse>('ExportResponse'),
      contract<FrontierOrchestrationResult>('FrontierOrchestrationResult'),
      contract<SpecialtyKnowledgeHit>('SpecialtyKnowledgeHit'),
      contract<NegotiationLog>('NegotiationLog'),
      contract<HealthResponse>('HealthResponse'),
      contract<PipelineVelocity>('PipelineVelocity'),
      contract<IntegrityMeta>('IntegrityMeta'),
      contract<InviteTeamMemberRequest>('InviteTeamMemberRequest'),
      contract<MonthlyRevenue>('MonthlyRevenue'),
      contract<OrphanTrip>('OrphanTrip'),
      contract<OverrideRequest>('OverrideRequest'),
      contract<OverrideResponse>('OverrideResponse'),
      contract<PipelineStageConfig>('PipelineStageConfig'),
      contract<QualityScore>('QualityScore'),
      contract<ReviewActionRequest>('ReviewActionRequest'),
      contract<RunAcceptedResponse>('RunAcceptedResponse'),
      contract<RunMeta>('RunMeta'),
      contract<RunStatusResponse>('RunStatusResponse'),
      contract<PublicCheckerArtifactUpload>('PublicCheckerArtifactUpload'),
      contract<PublicCheckerArtifactManifest>('PublicCheckerArtifactManifest'),
      contract<PublicCheckerExportResponse>('PublicCheckerExportResponse'),
      contract<PublicCheckerDeleteResponse>('PublicCheckerDeleteResponse'),
      contract<SnoozeRequest>('SnoozeRequest'),
      contract<SuitabilityAcknowledgeRequest>('SuitabilityAcknowledgeRequest'),
      contract<SuitabilityFlagsResponse>('SuitabilityFlagsResponse'),
      contract<SuitabilitySignal>('SuitabilitySignal'),
      contract<SystemicError>('SystemicError'),
      contract<TeamMember>('TeamMember'),
      contract<TripListResponse>('TripListResponse'),
      contract<UnifiedStateResponse>('UnifiedStateResponse'),
      contract<UpdateAutonomyPolicy>('UpdateAutonomyPolicy'),
      contract<UpdateOperationalSettings>('UpdateOperationalSettings'),
    ];

    expect(names).toContain('RunStatusResponse');
  });
});
