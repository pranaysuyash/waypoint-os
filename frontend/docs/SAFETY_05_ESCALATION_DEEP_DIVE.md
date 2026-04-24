# SAFETY_05_ESCALATION_DEEP_DIVE

> Part 5 of Safety & Risk Systems Deep Dive
>
> **Previous:** [SAFETY_04_COMPLIANCE_DEEP_DIVE](./SAFETY_04_COMPLIANCE_DEEP_DIVE.md)
>
> **Next:** [INTAKE_DEEP_DIVE_MASTER_INDEX](./INTAKE_DEEP_DIVE_MASTER_INDEX.md)

---

## Escalation & Resolution Workflows

When risks are detected, the system must have clear, predictable pathways for escalation, approval, and resolution. This document covers the complete workflow from risk detection to final resolution.

---

## Table of Contents

1. [Escalation Framework Overview](#1-escalation-framework-overview)
2. [Escalation Tiers & Triggers](#2-escalation-tiers--triggers)
3. [Owner Approval Workflows](#3-owner-approval-workflows)
4. [Resolution Pathways](#4-resolution-pathways)
5. [Audit Trail & Compliance](#5-audit-trail--compliance)
6. [Technical Implementation](#6-technical-implementation)
7. [Future Evolution](#7-future-evolution)

---

## 1. Escalation Framework Overview

### 1.1 Core Philosophy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ESCALATION FRAMEWORK PHILOSOPHY                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  🔹 AUTOMATIC ESCALATION                                                    │
│      └─ Critical risks auto-escalate to owners                              │
│      └─ No human intervention required for triggering                       │
│                                                                             │
│  🔹 CONTEXT-AWARE ROUTING                                                   │
│      └─ Risks route to appropriate owner based on trip type                 │
│      └─ Agency-level risks go to agency owners                              │
│                                                                             │
│  🔹 DEFERRED DECISIONS                                                      │
│      └─ Blocking risks pause workflow until resolved                        │
│      └─ Non-blocking risks allow work with warnings                         │
│                                                                             │
│  🔹 FULL AUDIT TRAIL                                                        │
│      └─ Every escalation, decision, and action is recorded                  │
│      └─ Traceable history for compliance and learning                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Escalation Flow Diagram

```
                        RISK DETECTED
                             │
                             ▼
                    ┌────────────────┐
                    │  Assess Risk   │
                    │    Severity    │
                    └───────┬────────┘
                            │
            ┌───────────────┼───────────────┐
            │               │               │
            ▼               ▼               ▼
      ┌─────────┐     ┌─────────┐     ┌─────────┐
      │  LOW    │     │ MEDIUM  │     │  HIGH   │
      │  INFO   │     │WARNING  │     │  BLOCK  │
      └────┬────┘     └────┬────┘     └────┬────┘
           │               │               │
           │               │               ▼
           │               │         ┌──────────┐
           │               │         │  ESCALATE│
           │               │         │  TO OWNER│
           │               │         └─────┬────┘
           │               │               │
           ▼               ▼               ▼
      ┌─────────┐     ┌─────────┐     ┌────────────┐
      │  LOG    │     │  SHOW   │     │  AWAIT     │
      │  ONLY   │     │  WARNING│     │  APPROVAL  │
      └─────────┘     └─────────┘     └─────┬──────┘
                                          │
                            ┌─────────────┼─────────────┐
                            │             │             │
                            ▼             ▼             ▼
                      ┌─────────┐   ┌─────────┐   ┌─────────┐
                      │APPROVE  │   │OVERRIDE │   │ REJECT  │
                      │         │   │WITH RISK│   │         │
                      └────┬────┘   └────┬────┘   └────┬────┘
                           │             │             │
                           └─────────────┼─────────────┘
                                         ▼
                                  ┌──────────────┐
                                  │   RESOLVE    │
                                  │   RECORD     │
                                  └──────────────┘
```

---

## 2. Escalation Tiers & Triggers

### 2.1 Severity-Based Escalation Matrix

| Risk Score | Severity | Action Required | Who Decides | Workflow Impact |
|------------|----------|-----------------|-------------|-----------------|
| 0-3 | **Low** | Log only | System | None |
| 4-6 | **Medium** | Warning | Agent (with option to escalate) | Continue with visibility |
| 7-8 | **High** | Owner approval required | Agency Owner | Blocking |
| 9-10 | **Critical** | Immediate escalation | Agency Owner | Blocking + high priority |

### 2.2 Automatic Escalation Triggers

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    AUTOMATIC ESCALATION TRIGGERS                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  FINANCIAL TRIGGERS                                                         │
│  ─────────────────                                                         │
│  🔹 Budget overage > 10%                    → ESCALATE                      │
│  🔹 Budget overage > 25%                    → CRITICAL ESCALATION           │
│  🔹 Payment required before approval         → BLOCK until approved          │
│  🔹 Supplier payment failure                 → ESCALATE + pause trip         │
│                                                                             │
│  COMPLIANCE TRIGGERS                                                        │
│  ─────────────────                                                         │
│  🔹 Missing required documentation               → ESCALATE                  │
│  🔹 Expired passport/visa                       → BLOCK until updated        │
│  🔹 Blacklisted destination                      → CRITICAL ESCALATION       │
│  🔹 Sanctioned entity match                      → CRITICAL + LEGAL REVIEW   │
│                                                                             │
│  OPERATIONAL TRIGGERS                                                      │
│  ─────────────────                                                         │
│  🔹 No availability within constraints           → ESCALATE                  │
│  🔹 Supplier integration failure                 → ESCALATE + flag           │
│  🔹 Booking failure after payment                → CRITICAL ESCALATION       │
│                                                                             │
│  CUSTOMER TRIGGERS                                                          │
│  ─────────────────                                                         │
│  🔹 First-time customer > $5000                 → ESCALATE                  │
│  🔹 Customer payment flag                        → BLOCK until resolved      │
│  🔹 VIP customer (any risk)                      → OWNER NOTIFICATION        │
│                                                                             │
│  AGENCY TRIGGERS                                                           │
│  ─────────────────                                                         │
│  🔹 Outside agency expertise region               → ESCALATE                  │
│  🔹 Agent permission level insufficient          → ESCALATE                  │
│  🔹 Commission below agency threshold            → ESCALATE                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.3 Escalation Tier Definitions

```typescript
/**
 * Escalation levels for risk resolution
 */
enum EscalationLevel {
  /** No action required - informational only */
  NONE = 'none',

  /** Agent can resolve with visibility */
  AGENT = 'agent',

  /** Requires agent + owner visibility */
  OWNER_REVIEW = 'owner_review',

  /** Requires explicit owner approval */
  OWNER_APPROVAL = 'owner_approval',

  /** Requires immediate owner attention */
  URGENT = 'urgent',

  /** Requires legal/compliance review */
  LEGAL = 'legal',

  /** Requires executive approval */
  EXECUTIVE = 'executive'
}

/**
 * Escalation tier configuration
 */
interface EscalationTier {
  level: EscalationLevel;
  name: string;
  description: string;
  requiresApproval: boolean;
  blocking: boolean;
  slaHours?: number; // Response SLA in hours
  canOverride: boolean; // Whether lower-level users can override
}

const ESCALATION_TIERS: Record<EscalationLevel, EscalationTier> = {
  [EscalationLevel.NONE]: {
    level: EscalationLevel.NONE,
    name: 'Informational',
    description: 'No action required',
    requiresApproval: false,
    blocking: false,
    canOverride: false
  },
  [EscalationLevel.AGENT]: {
    level: EscalationLevel.AGENT,
    name: 'Agent Level',
    description: 'Agent can acknowledge and proceed',
    requiresApproval: false,
    blocking: false,
    slaHours: 48,
    canOverride: false
  },
  [EscalationLevel.OWNER_REVIEW]: {
    level: EscalationLevel.OWNER_REVIEW,
    name: 'Owner Review',
    description: 'Owner should review, agent can proceed with awareness',
    requiresApproval: false,
    blocking: false,
    slaHours: 24,
    canOverride: true
  },
  [EscalationLevel.OWNER_APPROVAL]: {
    level: EscalationLevel.OWNER_APPROVAL,
    name: 'Owner Approval',
    description: 'Explicit owner approval required before proceeding',
    requiresApproval: true,
    blocking: true,
    slaHours: 8,
    canOverride: false
  },
  [EscalationLevel.URGENT]: {
    level: EscalationLevel.URGENT,
    name: 'Urgent',
    description: 'Immediate attention required',
    requiresApproval: true,
    blocking: true,
    slaHours: 2,
    canOverride: false
  },
  [EscalationLevel.LEGAL]: {
    level: EscalationLevel.LEGAL,
    name: 'Legal Review',
    description: 'Requires legal/compliance team review',
    requiresApproval: true,
    blocking: true,
    slaHours: 48,
    canOverride: false
  },
  [EscalationLevel.EXECUTIVE]: {
    level: EscalationLevel.EXECUTIVE,
    name: 'Executive Approval',
    description: 'Requires executive-level approval',
    requiresApproval: true,
    blocking: true,
    slaHours: 72,
    canOverride: false
  }
};
```

---

## 3. Owner Approval Workflows

### 3.1 Approval Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           OWNER APPROVAL FLOW                               │
└─────────────────────────────────────────────────────────────────────────────┘

    RISK DETECTED → ESCALATION TRIGGERED
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │      NOTIFICATION SENT TO OWNER        │
        │  ┌─────────────────────────────────┐  │
        │  │ • In-app notification           │  │
        │  │ • Email alert                   │  │
        │  │ • Slack/Teams message (opt-in)  │  │
        │  │ • SMS for urgent cases          │  │
        │  └─────────────────────────────────┘  │
        └───────────────┬───────────────────────┘
                        │
                        ▼
        ┌───────────────────────────────────────┐
        │         OWNER REVIEWS TRIP             │
        │  ┌─────────────────────────────────┐  │
        │  │ • View trip details             │  │
        │  │ • See flagged risks             │  │
        │  │ • Review agent notes            │  │
        │  │ • Check customer context        │  │
        │  └─────────────────────────────────┘  │
        └───────────────┬───────────────────────┘
                        │
                        ▼
        ┌───────────────────────────────────────┐
        │          OWNER DECISION                │
        └───────────────┬───────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
  ┌───────────┐   ┌───────────┐   ┌───────────┐
  │  APPROVE  │   │ CONDITIONAL│  │  REJECT   │
  │           │   │           │  │           │
  │Allow work │   │Approve    │  │Block work │
  │to proceed │   │with       │  │Require    │
  │           │   │conditions │  │changes    │
  └─────┬─────┘   └─────┬─────┘   └─────┬─────┘
        │               │               │
        ▼               ▼               ▼
  ┌───────────┐   ┌───────────┐   ┌───────────┐
  │ TRIP      │   │ TRIP      │   │ AGENT     │
  │ UNBLOCKED │   │ UNBLOCKED │   │ NOTIFIED  │
  │           │   │ +        │   │           │
  │           │   │ CONDITIONS│  │ TRIP      │
  │           │   │ ATTACHED  │  │ BLOCKED   │
  └───────────┘   └───────────┘   └───────────┘
```

### 3.2 Approval Decision Types

```typescript
/**
 * Types of approval decisions an owner can make
 */
enum ApprovalDecision {
  /** Full approval - proceed without restrictions */
  APPROVE = 'approve',

  /** Approve with specific conditions */
  CONDITIONAL = 'conditional',

  /** Reject - block progress */
  REJECT = 'reject',

  /** Defer to another owner/department */
  DEFER = 'defer',

  /** Request more information */
  REQUEST_INFO = 'request_info'
}

/**
 * Owner approval response
 */
interface OwnerApproval {
  id: string;
  escalationId: string;
  tripId: string;
  riskId: string;

  decision: ApprovalDecision;
  approverId: string;
  approverName: string;
  approvedAt: Date;

  // For conditional approvals
  conditions?: ApprovalCondition[];

  // For rejections
  rejectionReason?: string;
  requiredChanges?: string[];

  // For deferrals
  deferredTo?: string; // userId or role
  deferralReason?: string;

  // For info requests
  infoRequests?: string[];

  // Optional notes
  notes?: string;
}

/**
 * Conditions attached to a conditional approval
 */
interface ApprovalCondition {
  id: string;
  type: 'budget_limit' | 'documentation' | 'customer_action' | 'supplier_change' | 'other';
  description: string;
  mustCompleteBefore: 'booking' | 'payment' | 'confirmation' | 'custom';
  isMet: boolean;
  evidenceRequired?: boolean;
}
```

### 3.3 Conditional Approval Examples

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CONDITIONAL APPROVAL SCENARIOS                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  SCENARIO 1: Budget Overage Warning                                         │
│  ────────────────────────────                                              │
│  Risk: Trip is 8% over approved budget                                      │
│  Decision: CONDITIONAL                                                      │
│  Conditions:                                                                │
│    • Customer must confirm budget increase (before booking)                │
│    • Add "Budget Approved" note to trip                                     │
│    • Flag for final review before payment                                   │
│                                                                             │
│  SCENARIO 2: Near-Expiry Passport                                           │
│  ────────────────────────────                                              │
│  Risk: Passport expires in 4 months (requirement: 6)                       │
│  Decision: CONDITIONAL                                                      │
│  Conditions:                                                                │
│    • Customer must confirm passport validity at destination                 │
│    • Add waiver acknowledgment before booking                               │
│    • Document in trip notes                                                 │
│                                                                             │
│  SCENARIO 3: First-Time High-Value Customer                                  │
│  ────────────────────────────────                                          │
│  Risk: New customer, $12,000 trip                                           │
│  Decision: CONDITIONAL                                                      │
│  Conditions:                                                                │
│    • Payment must be confirmed before any bookings                          │
│    • Verify customer identity documents                                    │
│    • Pre-booking call required                                              │
│                                                                             │
│  SCENARIO 4: Supplier Change Required                                       │
│  ────────────────────────────────                                          │
│  Risk: Requested supplier has low reliability score                         │
│  Decision: CONDITIONAL                                                      │
│  Conditions:                                                                │
│    • Must use alternative supplier from approved list                       │
│    • Document why customer preferred original                               │
│    │                                                                         │
│  SCENARIO 5: Documentation Gap                                              │
│  ────────────────────────────                                              │
│  Risk: Visa requirements unclear for destination                             │
│  Decision: CONDITIONAL                                                      │
│  Conditions:                                                                │
│    • Customer confirms visa responsibility                                  │
│    • Add visa requirement warning to confirmation                           │
│    • Follow up 30 days before travel                                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.4 Approval UI Component Specification

```typescript
/**
 * Owner approval dialog component props
 */
interface OwnerApprovalDialogProps {
  /** The escalation requiring approval */
  escalation: RiskEscalation;

  /** The trip containing the risk */
  trip: Trip;

  /** Detected risks */
  risks: DetectedRisk[];

  /** Agent context */
  agentContext: {
    agentName: string;
    agentNotes?: string;
    agentSuggestion?: string;
  };

  /** Customer context */
  customerContext: {
    isNewCustomer: boolean;
    isVip: boolean;
    totalTrips: number;
    totalValue: number;
  };

  /** Callback when decision is made */
  onDecision: (decision: OwnerApproval) => Promise<void>;

  /** Available owners for deferral */
  availableOwners?: AgencyOwner[];
}

/**
 * Component structure
 */
const OwnerApprovalDialog = ({
  escalation,
  trip,
  risks,
  agentContext,
  customerContext,
  onDecision,
  availableOwners
}: OwnerApprovalDialogProps) => {
  return (
    <Dialog className="approval-dialog">
      <DialogHeader>
        <DialogTitle>
          <RiskBadge severity={escalation.severity} />
          Approval Required
        </DialogTitle>
      </DialogHeader>

      <DialogContent>
        {/* Trip Summary */}
        <TripSummaryCard trip={trip} />

        {/* Risk Details */}
        <RiskDetailsSection risks={risks} />

        {/* Agent Context */}
        <AgentContextSection agentContext={agentContext} />

        {/* Customer Context */}
        <CustomerContextSection customerContext={customerContext} />

        {/* Decision Tabs */}
        <DecisionTabs>
          <DecisionTab value="approve">
            <ApproveForm onSubmit={onDecision} />
          </DecisionTab>

          <DecisionTab value="conditional">
            <ConditionalForm
              conditions={availableConditions}
              onSubmit={onDecision}
            />
          </DecisionTab>

          <DecisionTab value="reject">
            <RejectForm
              requiredChanges={suggestedChanges}
              onSubmit={onDecision}
            />
          </DecisionTab>

          <DecisionTab value="defer">
            <DeferForm
              availableOwners={availableOwners}
              onSubmit={onDecision}
            />
          </DecisionTab>
        </DecisionTabs>
      </DialogContent>
    </Dialog>
  );
};
```

---

## 4. Resolution Pathways

### 4.1 Resolution State Machine

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          RESOLUTION STATE MACHINE                            │
└─────────────────────────────────────────────────────────────────────────────┘

                    [RISK DETECTED]
                          │
                          ▼
                    ┌──────────┐
                    │  PENDING │
                    │ ESCALATION
                    └─────┬────┘
                          │
            ┌─────────────┼─────────────┐
            │             │             │
            ▼             ▼             ▼
      ┌──────────┐  ┌──────────┐  ┌──────────┐
      │  AUTO    │  │  ESCALATE│  │  BLOCK   │
      │ RESOLVED │  │          │  │          │
      └──────────┘  └────┬─────┘  └────┬─────┘
                         │             │
                         ▼             ▼
                   ┌──────────┐  ┌──────────┐
                   │IN_REVIEW │  │ AWAITING │
                   │          │  │ APPROVAL │
                   └────┬─────┘  └────┬─────┘
                        │             │
                        ▼             │
                  ┌──────────┐        │
                  │ RESOLVED │◄───────┘
                  │          │
                  └────┬─────┘
                       │
         ┌─────────────┼─────────────┐
         │             │             │
         ▼             ▼             ▼
   ┌──────────┐  ┌──────────┐  ┌──────────┐
   │ APPROVED │  │CONDITIONAL│  │ REJECTED │
   │           │  │           │  │          │
   └────┬─────┘  └────┬─────┘  └────┬─────┘
        │             │             │
        ▼             ▼             ▼
   ┌──────────┐  ┌──────────┐  ┌──────────┐
   │ COMPLETE │  │ MONITOR  │  │ ESCALATE │
   │           │  │          │  │  AGAIN   │
   └──────────┘  └────┬─────┘  └──────────┘
                      │
                      ▼
                ┌──────────┐
                │ COMPLETE │
                └──────────┘
```

### 4.2 Resolution Type Definitions

```typescript
/**
 * Resolution status for a risk escalation
 */
enum ResolutionStatus {
  /** Initial state - risk detected, not yet processed */
  PENDING = 'pending',

  /** Automatically resolved by system */
  AUTO_RESOLVED = 'auto_resolved',

  /** Escalated and awaiting review */
  IN_REVIEW = 'in_review',

  /** Awaiting owner approval */
  AWAITING_APPROVAL = 'awaiting_approval',

  /** Approved and resolved */
  APPROVED = 'approved',

  /** Approved with conditions */
  CONDITIONAL = 'conditional',

  /** Rejected, changes required */
  REJECTED = 'rejected',

  /** Conditions being monitored */
  MONITORING = 'monitoring',

  /** Fully resolved and closed */
  COMPLETE = 'complete',

  /** Re-escalated */
  RE_ESCALATED = 're_escalated'
}

/**
 * Resolution outcome
 */
interface RiskResolution {
  id: string;
  escalationId: string;
  riskId: string;
  tripId: string;

  status: ResolutionStatus;
  resolvedBy?: string; // userId or 'system'
  resolvedAt?: Date;

  // For approvals
  approvalDecision?: ApprovalDecision;

  // For conditional resolutions
  conditions?: ApprovalCondition[];
  conditionsMetAt?: Date;

  // For rejections
  rejectionReason?: string;
  requiredChanges?: string[];

  // Resolution notes
  notes?: string;

  // Follow-up actions
  followUpRequired?: boolean;
  followUpDate?: Date;
  followUpActions?: string[];
}
```

### 4.3 Resolution Pathways by Risk Category

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      RESOLUTION PATHWAYS BY CATEGORY                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  FINANCIAL RISKS                                                           │
│  ────────────────                                                          │
│  Budget Overage < 10%  → Agent acknowledgment → Auto-resolve               │
│  Budget Overage 10-25% → Owner review → Conditional/Approve/Reject          │
│  Budget Overage > 25% → Owner approval → Block until resolved               │
│  Payment Required     → Escalate → Block until payment confirmed            │
│                                                                             │
│  COMPLIANCE RISKS                                                          │
│  ────────────────                                                          │
│  Missing Docs        → Escalate → Block until provided                      │
│  Expiry Warning      → Conditional → Waiver required                        │
│  Expired Doc         → Block → Must update to proceed                       │
│  Visa Requirement    → Conditional → Customer acknowledgment                │
│  Sanction Match      → Critical → Legal review required                     │
│                                                                             │
│  OPERATIONAL RISKS                                                        │
│  ────────────────                                                          │
│  No Availability      → Escalate → Suggest alternatives                     │
│  Supplier Issue       → Escalate → Switch supplier                          │
│  Booking Failure      → Critical → Investigate + rebook                     │
│  Integration Error    → Escalate → Technical team alert                     │
│                                                                             │
│  CUSTOMER RISKS                                                            │
│  ────────────────                                                          │
│  New Customer High    → Conditional → Payment verification                 │
│  Payment Flag         → Block → Clear payment to proceed                    │
│  VIP Customer         → Notify → Owner visibility                           │
│  History Issue        → Escalate → Owner review required                    │
│                                                                             │
│  AGENCY RISKS                                                              │
│  ────────────────                                                          │
│  Permission Gap       → Escalate → Assign to qualified agent                │
│  Region Gap          → Escalate → Assign to regional expert                 │
│  Commission Low       → Escalate → Owner decision                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.4 Re-Escalation Rules

```typescript
/**
 * Rules for when resolved risks can be re-escalated
 */
interface ReEscalationRule {
  /** Trigger for re-escalation */
  trigger: string;

  /** Whether re-escalation is allowed */
  allowed: boolean;

  /** Required escalation level for re-escalation */
  requiredLevel: EscalationLevel;

  /** Time limit after which re-escalation is not allowed */
  timeLimitHours?: number;
}

const RE_ESCALATION_RULES: ReEscalationRule[] = [
  {
    trigger: 'conditions_not_met',
    allowed: true,
    requiredLevel: EscalationLevel.OWNER_APPROVAL,
    timeLimitHours: 168 // 1 week
  },
  {
    trigger: 'new_information',
    allowed: true,
    requiredLevel: EscalationLevel.OWNER_REVIEW,
    timeLimitHours: 720 // 30 days
  },
  {
    trigger: 'resolution_ineffective',
    allowed: true,
    requiredLevel: EscalationLevel.OWNER_REVIEW,
    timeLimitHours: 168 // 1 week
  },
  {
    trigger: 'customer_changed_mind',
    allowed: true,
    requiredLevel: EscalationLevel.AGENT
  },
  {
    trigger: 'external_factor_change',
    allowed: true,
    requiredLevel: EscalationLevel.OWNER_REVIEW
  },
  {
    trigger: 'approval_mistake',
    allowed: true,
    requiredLevel: EscalationLevel.OWNER_APPROVAL,
    timeLimitHours: 24
  }
];
```

---

## 5. Audit Trail & Compliance

### 5.1 Audit Data Model

```typescript
/**
 * Complete audit trail for risk escalation and resolution
 */
interface EscalationAuditTrail {
  /** Unique audit ID */
  id: string;

  /** Associated records */
  escalationId: string;
  riskId: string;
  tripId: string;
  agencyId: string;

  /** Complete timeline of events */
  events: AuditEvent[];

  /** Final outcome */
  finalResolution?: RiskResolution;

  /** Compliance metadata */
  compliance: {
    createdAt: Date;
    createdBy: string;
    modifiedAt: Date;
    modifiedBy?: string;
    exportedAt?: Date;
    retentionUntil: Date;
  };
}

/**
 * Individual audit event
 */
interface AuditEvent {
  id: string;
  timestamp: Date;
  eventType: AuditEventType;
  actor: {
    id: string;
    name: string;
    role: string;
    type: 'user' | 'system' | 'api';
  };
  details: {
    from?: string; // Previous state
    to?: string; // New state
    reason?: string;
    metadata?: Record<string, any>;
  };
  ipAddress?: string;
  userAgent?: string;
}

/**
 * Types of audit events
 */
enum AuditEventType {
  // Risk events
  RISK_DETECTED = 'risk_detected',
  RISK_UPDATED = 'risk_updated',
  RISK_DISMISSED = 'risk_dismissed',

  // Escalation events
  ESCALATION_CREATED = 'escalation_created',
  ESCALATION_UPDATED = 'escalation_updated',
  ESCALATION_CANCELLED = 'escalation_cancelled',

  // Approval events
  APPROVAL_REQUESTED = 'approval_requested',
  APPROVAL_GRANTED = 'approval_granted',
  APPROVAL_DENIED = 'approval_denied',
  APPROVAL_CONDITIONAL = 'approval_conditional',

  // Resolution events
  RESOLUTION_AUTO = 'resolution_auto',
  RESOLUTION_MANUAL = 'resolution_manual',
  RESOLUTION_RE_ESCALATED = 'resolution_re_escalated',

  // Condition events
  CONDITION_ADDED = 'condition_added',
  CONDITION_MET = 'condition_met',
  CONDITION_FAILED = 'condition_failed',

  // Notification events
  NOTIFICATION_SENT = 'notification_sent',
  NOTIFICATION_READ = 'notification_read',

  // Override events
  OVERRIDE_REQUESTED = 'override_requested',
  OVERRIDE_GRANTED = 'override_granted',
  OVERRIDE_DENIED = 'override_denied'
}
```

### 5.2 Audit Trail Display

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        AUDIT TRAIL DISPLAY                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Trip: #2024-0847 | Risk: Budget Overage | Status: Resolved                  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │ 🕐 2024-04-15 14:32:15  │ RISK_DETECTED                               │ │
│  │                         │ Detected: Budget overage of 12%             │ │
│  │                         │ Severity: MEDIUM (6/10)                     │ │
│  │                         │ Actor: System (auto-detection)              │ │
│  ├───────────────────────────────────────────────────────────────────────┤ │
│  │ 🕐 2024-04-15 14:32:16  │ ESCALATION_CREATED                           │ │
│  │                         │ Escalated to: OWNER_REVIEW                  │ │
│  │                         │ Reason: Budget over 10% threshold           │ │
│  │                         │ Actor: System (auto-escalation)             │ │
│  ├───────────────────────────────────────────────────────────────────────┤ │
│  │ 🕐 2024-04-15 14:32:17  │ NOTIFICATION_SENT                            │ │
│  │                         │ To: agency-owner@example.com                 │ │
│  │                         │ Channel: Email + In-app                      │ │
│  │                         │ Actor: System                               │ │
│  ├───────────────────────────────────────────────────────────────────────┤ │
│  │ 🕐 2024-04-15 15:45:22  │ APPROVAL_CONDITIONAL                         │ │
│  │                         │ Decision: Conditional approval               │ │
│  │                         │ Conditions: Customer confirmation required   │ │
│  │                         │ Actor: Jane Smith (Owner)                    │ │
│  ├───────────────────────────────────────────────────────────────────────┤ │
│  │ 🕐 2024-04-15 16:20:08  │ CONDITION_ADDED                              │ │
│  │                         │ Condition: Budget increase confirmed         │ │
│  │                         │ Evidence: Customer email attached           │ │
│  │                         │ Actor: John Doe (Agent)                     │ │
│  ├───────────────────────────────────────────────────────────────────────┤ │
│  │ 🕐 2024-04-15 16:20:09  │ CONDITION_MET                                │ │
│  │                         │ All conditions satisfied                     │ │
│  │                         │ Actor: System                               │ │
│  ├───────────────────────────────────────────────────────────────────────┤ │
│  │ 🕐 2024-04-15 16:20:10  │ RESOLUTION_MANUAL                            │ │
│  │                         │ Final status: COMPLETE                       │ │
│  │                         │ Total time: 47m 55s                          │ │
│  │                         │ Actor: System (auto-closed)                  │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  [Export Audit Trail] [View Full Details]                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.3 Compliance Reporting

```typescript
/**
 * Compliance report for risk escalations
 */
interface ComplianceReport {
  reportId: string;
  agencyId: string;
  reportPeriod: {
    start: Date;
    end: Date;
  };

  metrics: {
    totalEscalations: number;
    bySeverity: Record<string, number>;
    byCategory: Record<string, number>;
    byOutcome: Record<string, number>;

    // SLA compliance
    averageResponseTime: number; // minutes
    slaBreaches: number;
    slaComplianceRate: number; // percentage

    // Resolution metrics
    autoResolutionRate: number;
    firstTimeResolutionRate: number;
    reEscalationRate: number;
  };

  // Top risks
  topRisks: {
    riskType: string;
    count: number;
    avgResolutionTime: number;
  }[];

  // Owner performance
  ownerPerformance: {
    ownerId: string;
    ownerName: string;
    totalApprovals: number;
    averageResponseTime: number;
    slaComplianceRate: number;
  }[];

  generatedAt: Date;
}
```

---

## 6. Technical Implementation

### 6.1 Escalation Service

```typescript
/**
 * Core escalation service
 */
class EscalationService {
  private escalationStore: EscalationStore;
  private notificationService: NotificationService;
  private auditService: AuditService;

  /**
   * Create a new escalation from a detected risk
   */
  async createEscalation(risk: DetectedRisk, trip: Trip): Promise<RiskEscalation> {
    // Determine escalation level based on risk
    const level = this.determineEscalationLevel(risk);

    // Create escalation record
    const escalation: RiskEscalation = {
      id: generateId(),
      riskId: risk.id,
      tripId: trip.id,
      agencyId: trip.agencyId,
      level,
      severity: risk.severity,
      status: level === EscalationLevel.NONE
        ? ResolutionStatus.AUTO_RESOLVED
        : ResolutionStatus.IN_REVIEW,
      createdAt: new Date(),
      updatedAt: new Date()
    };

    await this.escalationStore.save(escalation);

    // Log audit event
    await this.auditService.logEvent({
      eventType: AuditEventType.ESCALATION_CREATED,
      escalationId: escalation.id,
      actor: { type: 'system' }
    });

    // Send notifications if needed
    if (level !== EscalationLevel.NONE) {
      await this.sendNotifications(escalation, risk, trip);
    }

    return escalation;
  }

  /**
   * Determine escalation level from risk
   */
  private determineEscalationLevel(risk: DetectedRisk): EscalationLevel {
    const { score, category, severity } = risk;

    // Critical risks always require urgent escalation
    if (severity === RiskSeverity.CRITICAL) {
      return category === RiskCategory.COMPLIANCE
        ? EscalationLevel.LEGAL
        : EscalationLevel.URGENT;
    }

    // High risks require owner approval
    if (severity === RiskSeverity.HIGH) {
      return EscalationLevel.OWNER_APPROVAL;
    }

    // Medium risks require owner review
    if (severity === RiskSeverity.MEDIUM) {
      return EscalationLevel.OWNER_REVIEW;
    }

    // Low risks can be handled by agent
    return EscalationLevel.AGENT;
  }

  /**
   * Send notifications for escalation
   */
  private async sendNotifications(
    escalation: RiskEscalation,
    risk: DetectedRisk,
    trip: Trip
  ): Promise<void> {
    const recipients = await this.getRecipients(escalation, trip);

    for (const recipient of recipients) {
      await this.notificationService.send({
        type: this.getNotificationType(escalation.level),
        recipient,
        data: {
          escalationId: escalation.id,
          tripId: trip.id,
          tripName: trip.name,
          risk: {
            type: risk.type,
            severity: risk.severity,
            description: risk.description
          },
          slaDeadline: this.getSLADeadline(escalation)
        }
      });
    }
  }

  /**
   * Process owner approval decision
   */
  async processApproval(
    escalationId: string,
    decision: ApprovalDecision,
    approverId: string,
    options?: {
      conditions?: ApprovalCondition[];
      rejectionReason?: string;
      requiredChanges?: string[];
      notes?: string;
    }
  ): Promise<RiskResolution> {
    const escalation = await this.escalationStore.get(escalationId);
    if (!escalation) {
      throw new Error('Escalation not found');
    }

    // Create resolution
    const resolution: RiskResolution = {
      id: generateId(),
      escalationId,
      riskId: escalation.riskId,
      tripId: escalation.tripId,
      status: this.mapDecisionToStatus(decision),
      resolvedBy: approverId,
      resolvedAt: new Date(),
      approvalDecision: decision,
      conditions: options?.conditions,
      rejectionReason: options?.rejectionReason,
      requiredChanges: options?.requiredChanges,
      notes: options?.notes,
      followUpRequired: decision === ApprovalDecision.CONDITIONAL
    };

    // Update escalation
    escalation.status = resolution.status;
    escalation.updatedAt = new Date();
    escalation.resolution = resolution;

    await this.escalationStore.save(escalation);

    // Log audit events
    await this.auditService.logEvent({
      eventType: this.getApprovalEventType(decision),
      escalationId,
      actor: { type: 'user', id: approverId }
    });

    // If conditions, set up monitoring
    if (decision === ApprovalDecision.CONDITIONAL && options?.conditions) {
      await this.setupConditionMonitoring(escalationId, options.conditions);
    }

    // Send notifications
    await this.sendApprovalNotifications(escalation, resolution);

    return resolution;
  }

  /**
   * Check and update condition status
   */
  async checkConditions(escalationId: string): Promise<void> {
    const escalation = await this.escalationStore.get(escalationId);
    if (!escalation.resolution?.conditions) {
      return;
    }

    const conditions = escalation.resolution.conditions;
    let allMet = true;

    for (const condition of conditions) {
      if (!condition.isMet) {
        const met = await this.verifyCondition(condition);
        if (met && !condition.isMet) {
          condition.isMet = true;
          await this.auditService.logEvent({
            eventType: AuditEventType.CONDITION_MET,
            escalationId,
            details: { conditionId: condition.id }
          });
        }
        allMet = allMet && met;
      }
    }

    if (allMet && escalation.resolution.status === ResolutionStatus.CONDITIONAL) {
      escalation.resolution.status = ResolutionStatus.APPROVED;
      escalation.resolution.conditionsMetAt = new Date();
      await this.escalationStore.save(escalation);
    }
  }

  /**
   * Request re-escalation
   */
  async reEscalate(
    escalationId: string,
    requestorId: string,
    trigger: string,
    reason: string
  ): Promise<RiskEscalation> {
    const escalation = await this.escalationStore.get(escalationId);
    if (!escalation) {
      throw new Error('Escalation not found');
    }

    // Check if re-escalation is allowed
    const rule = RE_ESCALATION_RULES.find(r => r.trigger === trigger);
    if (!rule || !rule.allowed) {
      throw new Error('Re-escalation not allowed for this trigger');
    }

    // Create new escalation
    const newEscalation: RiskEscalation = {
      ...escalation,
      id: generateId(),
      level: rule.requiredLevel,
      status: ResolutionStatus.IN_REVIEW,
      previousEscalationId: escalationId,
      reEscalationReason: reason,
      createdAt: new Date(),
      updatedAt: new Date()
    };

    await this.escalationStore.save(newEscalation);

    // Update old escalation
    escalation.status = ResolutionStatus.RE_ESCALATED;
    escalation.reEscalatedTo = newEscalation.id;
    await this.escalationStore.save(escalation);

    // Log audit event
    await this.auditService.logEvent({
      eventType: AuditEventType.RESOLUTION_RE_ESCALATED,
      escalationId: newEscalation.id,
      actor: { type: 'user', id: requestorId },
      details: { previousEscalation: escalationId, trigger, reason }
    });

    return newEscalation;
  }

  // Private helpers
  private async getRecipients(escalation: RiskEscalation, trip: Trip): Promise<User[]> {
    // Implementation depends on user/role system
    return [];
  }

  private getNotificationType(level: EscalationLevel): NotificationType {
    switch (level) {
      case EscalationLevel.URGENT:
        return 'urgent_alert';
      case EscalationLevel.OWNER_APPROVAL:
        return 'approval_required';
      case EscalationLevel.OWNER_REVIEW:
        return 'review_required';
      default:
        return 'info';
    }
  }

  private getSLADeadline(escalation: RiskEscalation): Date {
    const tier = ESCALATION_TIERS[escalation.level];
    if (tier.slaHours) {
      return addHours(escalation.createdAt, tier.slaHours);
    }
    return null;
  }

  private mapDecisionToStatus(decision: ApprovalDecision): ResolutionStatus {
    switch (decision) {
      case ApprovalDecision.APPROVE:
        return ResolutionStatus.APPROVED;
      case ApprovalDecision.CONDITIONAL:
        return ResolutionStatus.CONDITIONAL;
      case ApprovalDecision.REJECT:
        return ResolutionStatus.REJECTED;
      case ApprovalDecision.DEFER:
        return ResolutionStatus.IN_REVIEW;
      case ApprovalDecision.REQUEST_INFO:
        return ResolutionStatus.IN_REVIEW;
      default:
        return ResolutionStatus.PENDING;
    }
  }

  private getApprovalEventType(decision: ApprovalDecision): AuditEventType {
    switch (decision) {
      case ApprovalDecision.APPROVE:
        return AuditEventType.APPROVAL_GRANTED;
      case ApprovalDecision.CONDITIONAL:
        return AuditEventType.APPROVAL_CONDITIONAL;
      case ApprovalDecision.REJECT:
        return AuditEventType.APPROVAL_DENIED;
      default:
        return AuditEventType.APPROVAL_REQUESTED;
    }
  }

  private async setupConditionMonitoring(
    escalationId: string,
    conditions: ApprovalCondition[]
  ): Promise<void> {
    // Set up monitoring for conditions
    // This could involve scheduled checks, webhooks, etc.
  }

  private async verifyCondition(condition: ApprovalCondition): Promise<boolean> {
    // Implementation depends on condition type
    return false;
  }

  private async sendApprovalNotifications(
    escalation: RiskEscalation,
    resolution: RiskResolution
  ): Promise<void> {
    // Notify relevant parties of the decision
  }
}
```

### 6.2 Escalation Store Interface

```typescript
/**
 * Escalation data store interface
 */
interface EscalationStore {
  /**
   * Save an escalation (create or update)
   */
  save(escalation: RiskEscalation): Promise<void>;

  /**
   * Get an escalation by ID
   */
  get(id: string): Promise<RiskEscalation | null>;

  /**
   * Get escalations for a trip
   */
  getByTrip(tripId: string): Promise<RiskEscalation[]>;

  /**
   * Get escalations for an agency
   */
  getByAgency(
    agencyId: string,
    options?: {
      status?: ResolutionStatus;
      level?: EscalationLevel;
      startDate?: Date;
      endDate?: Date;
    }
  ): Promise<RiskEscalation[]>;

  /**
   * Get pending escalations for an owner
   */
  getPendingForOwner(ownerId: string): Promise<RiskEscalation[]>;

  /**
   * Get escalations approaching SLA deadline
   */
  getApproachingSLA(hoursThreshold: number): Promise<RiskEscalation[]>;

  /**
   * Get escalations with breached SLA
   */
  getBreachedSLA(): Promise<RiskEscalation[]>;

  /**
   * Update escalation status
   */
  updateStatus(id: string, status: ResolutionStatus): Promise<void>;

  /**
   * Add resolution to escalation
   */
  addResolution(id: string, resolution: RiskResolution): Promise<void>;
}

/**
 * Risk escalation record
 */
interface RiskEscalation {
  id: string;
  riskId: string;
  tripId: string;
  agencyId: string;

  level: EscalationLevel;
  severity: RiskSeverity;
  status: ResolutionStatus;

  createdAt: Date;
  updatedAt: Date;

  // Resolution data
  resolution?: RiskResolution;

  // Re-escalation support
  previousEscalationId?: string;
  reEscalatedTo?: string;
  reEscalationReason?: string;

  // SLA tracking
  slaDeadline?: Date;
  slaBreached?: boolean;
}
```

### 6.3 Notification Service Integration

```typescript
/**
 * Notification configuration for escalations
 */
interface EscalationNotificationConfig {
  /** Enable email notifications */
  emailEnabled: boolean;

  /** Enable in-app notifications */
  inAppEnabled: boolean;

  /** Enable Slack notifications */
  slackEnabled: boolean;

  /** Enable SMS for urgent escalations */
  smsEnabled: boolean;

  /** Notification frequency */
  frequency: 'immediate' | 'hourly' | 'daily';

  /** SLA reminder settings */
  slaReminders: {
    /** Hours before SLA to send reminder */
    reminderHours: number[];
    /** Include escalations approaching SLA in summary */
    includeInSummary: boolean;
  };
}

/**
 * Notification payload for escalation
 */
interface EscalationNotification {
  type: 'approval_required' | 'review_required' | 'urgent_alert' | 'info';
  escalationId: string;
  tripId: string;
  tripName: string;
  risk: {
    type: string;
    severity: string;
    description: string;
  };
  slaDeadline?: Date;
  actionUrl: string;
}
```

---

## 7. Future Evolution

### 7.1 Enhanced Escalation Features

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      FUTURE ESCALATION CAPABILITIES                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PHASE 2: INTELLIGENT ROUTING                                               │
│  ──────────────────────────                                                 │
│  🔹 ML-based owner recommendation based on risk category                    │
│  🔹 Load balancing across multiple owners                                   │
│  🔹 Availability-aware routing (timezone, working hours)                    │
│  🔹 Expertise matching (regional, supplier, customer type)                  │
│                                                                             │
│  PHASE 3: PREDICTIVE ESCALATION                                             │
│  ──────────────────────────                                                 │
│  🔹 Predict likely escalations before trip creation                         │
│  🔹 Suggest risk mitigations proactively                                    │
│  🔹 Learn from resolution patterns                                          │
│  🔹 Auto-apply common conditional approvals                                  │
│                                                                             │
│  PHASE 4: COLLABORATIVE RESOLUTION                                          │
│  ────────────────────────────                                               │
│  🔹 Multi-owner approvals for complex risks                                 │
│  🔹 Comment threads on escalations                                          │
│  🔹 Tagging and @mentions                                                   │
│  🔹 Integration with external systems (legal, compliance)                   │
│                                                                             │
│  PHASE 5: AUTONOMOUS RESOLUTION                                             │
│  ──────────────────────────                                                 │
│  🔹 Auto-approve low-risk patterns after learning                           │
│  🔹 Auto-apply common conditions                                            │
│  🔹 Self-healing for common operational issues                              │
│  🔹 Robotic process automation for routine resolutions                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Integration Roadmap

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       ESCALATION INTEGRATION ROADMAP                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  INTERNAL INTEGRATIONS                                                      │
│  ────────────────────                                                      │
│  ✅ Timeline Integration — Escalations appear as events                     │
│  ✅ Output Panel Integration — Conditions shown in quotes                   │
│  ✅ Decision Engine Integration — Escalation affects workflow              │
│  ⏳ Analytics Integration — Resolution metrics dashboard                    │
│  ⏳ Communication Hub Integration — In-app messaging for escalations        │
│                                                                             │
│  EXTERNAL INTEGRATIONS                                                      │
│  ────────────────────                                                      │
│  ⏳ Slack/Teams — Real-time escalation notifications                        │
│  ⏳ Email Gateway — Rich HTML escalation emails                             │
│  ⏳ SMS Gateway — Urgent escalation alerts                                  │
│  ⏳ Legal/Compliance Tools — Case management integration                   │
│  ⏳ CRM Systems — Customer risk history                                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 7.3 Analytics & Insights

```typescript
/**
 * Escalation analytics metrics
 */
interface EscalationAnalytics {
  // Volume metrics
  totalEscalations: number;
  escalationsByLevel: Record<EscalationLevel, number>;
  escalationsByCategory: Record<RiskCategory, number>;
  escalationsOverTime: TimeSeriesData;

  // Resolution metrics
  averageResolutionTime: number; // minutes
  medianResolutionTime: number;
  resolutionTimeByLevel: Record<EscalationLevel, number>;
  firstTouchResolutionRate: number; // percentage

  // SLA metrics
  slaComplianceRate: number; // percentage
  slaBreachesByLevel: Record<EscalationLevel, number>;
  averageTimeToSLABreach: number; // minutes

  // Owner performance
  ownerMetrics: {
    ownerId: string;
    totalApprovals: number;
    averageResponseTime: number;
    approvalBreakdown: Record<ApprovalDecision, number>;
    slaComplianceRate: number;
  }[];

  // Risk patterns
  topEscalatingRisks: {
    riskType: string;
    count: number;
    percentage: number;
  }[];

  // Re-escalation analysis
  reEscalationRate: number; // percentage
  reEscalationReasons: Record<string, number>;

  // Conditional approval analysis
  conditionalApprovalRate: number;
  conditionCompletionRate: number;
  averageConditionsPerApproval: number;
}
```

---

## Appendix A: Escalation Checklist Reference

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      ESCALATION CHECKLIST REFERENCE                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  FOR AGENTS:                                                                │
│  ──────────────                                                             │
│  □ Review detected risks                                                    │
│  □ Understand risk severity and impact                                      │
│  □ Gather relevant context (customer, trip, constraints)                    │
│  □ Add agent notes if helpful                                               │
│  □ For non-blocking risks: Acknowledge and proceed                          │
│  □ For blocking risks: Wait for owner approval                              │
│  □ After conditional approval: Meet all conditions                          │
│  □ Monitor trip for new risks                                               │
│                                                                             │
│  FOR OWNERS:                                                                │
│  ──────────────                                                             │
│  □ Review escalation notification                                           │
│  □ Open trip and review full context                                        │
│  □ Read agent notes                                                         │
│  □ Check customer history                                                  │
│  □ Make decision (approve/conditional/reject/defer)                         │
│  □ If conditional: Specify clear conditions                                 │
│  □ If reject: Provide actionable feedback                                   │
│  □ Document decision reasoning                                              │
│  □ Monitor resolution completion                                            │
│                                                                             │
│  FOR SYSTEM:                                                                │
│  ──────────────                                                             │
│  □ Detect risks automatically                                              │
│  □ Calculate severity scores                                               │
│  □ Determine escalation level                                               │
│  □ Send notifications to appropriate parties                                │
│  □ Track SLA deadlines                                                     │
│  □ Send SLA reminders                                                      │
│  □ Log all actions to audit trail                                          │
│  □ Monitor condition status                                                 │
│  □ Auto-close when resolved                                                 │
│  □ Generate compliance reports                                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Summary

The Escalation & Resolution system provides:

- **Clear pathways** from risk detection to resolution
- **Automatic escalation** based on severity and category
- **Owner approval workflows** with approve/conditional/reject options
- **Full audit trail** for compliance and learning
- **SLA tracking** to ensure timely responses
- **Re-escalation support** for changing circumstances
- **Condition monitoring** for conditional approvals
- **Rich notifications** across multiple channels

This completes the **Safety & Risk Systems Deep Dive** series.

---

**Next:** [INTAKE_DEEP_DIVE_MASTER_INDEX](./INTAKE_DEEP_DIVE_MASTER_INDEX.md) — Packet Processing & Intake Deep Dives
