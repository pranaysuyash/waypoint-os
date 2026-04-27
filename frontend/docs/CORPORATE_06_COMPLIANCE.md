# Corporate Travel 06: Policy Compliance

> Enforcing and measuring corporate travel policy compliance

---

## Document Overview

**Focus**: Travel policy compliance management
**Status**: Research Exploration
**Last Updated**: 2026-04-27

---

## Key Questions to Answer

### 1. Policy Enforcement
- How do we enforce travel policies?
- What are the enforcement points?
- How do we handle exceptions?
- What about grace periods?

### 2. Compliance Measurement
- How do we measure compliance?
- What are the key metrics?
- How do we track violations?
- What about trend analysis?

### 3. Exception Management
- What constitutes a valid exception?
- How do we handle repeat offenders?
- What about escalation?
- How do we communicate policy?

### 4. Policy Optimization
- How do we know if a policy is working?
- What metrics inform policy changes?
- How do we test policy changes?
- What about A/B testing?

---

## Research Areas

### A. Enforcement Points

**Enforcement Timing:**

| Point | Mechanism | Strictness | Research Needed |
|-------|-----------|------------|-----------------|
| **Search time** | Show compliant options first | Soft | ? |
| **Selection time** | Warn on non-compliant choice | Medium | ? |
| **Booking time** | Block or require approval | Hard | ? |
| **Post-booking** | Review and flag | Retroactive | ? |
| **Expense time** | Reject or require justification | Hard | ? |

**Enforcement Methods:**

| Method | Description | Use Case | Research Needed |
|--------|-------------|----------|-----------------|
| **Hard block** | Cannot book outside policy | Strict policies | ? |
| **Soft block** | Warning, allow with justification | Flexible policies | ? |
| **Approval required** | Need approval to proceed | Exceptions | ? |
| **Post-trip review** | Review after booking | Measurement, retroactive | ? |

### B. Compliance Measurement

**Compliance Metrics:**

| Metric | Formula | Target | Research Needed |
|--------|---------|--------|-----------------|
| **Bookings within policy** | Compliant bookings / Total bookings | >90% | ? |
| **Spend within policy** | Compliant spend / Total spend | >95% | ? |
| **Advance booking rate** | Booked X+ days ahead / Total | >80% | ? |
| **Preferred supplier rate** | Preferred bookings / Total | >70% | ? |
| **Approval rate** | Approved / Submitted | >95% | ? |

**Violation Types:**

| Violation | Severity | Action | Research Needed |
|-----------|----------|--------|-----------------|
| **Booked outside policy (no approval)** | High | Coaching, possible non-reimbursement | ? |
| **Exceeds cost limit** | Medium | Approval required, flag | ? |
| **Wrong class of service** | Medium | Approval required, flag | ? |
| **Wrong hotel category** | Low | Flag, monitor | ? |
| **Last-minute booking** | Low | Flag, review | ? |

**Trend Analysis:**

| Analysis | Description | Action | Research Needed |
|----------|-------------|--------|-----------------|
| **Repeat violators** | Employees with multiple violations | Coaching, training | ? |
| **Violation patterns** | Common violation types | Policy refinement | ? |
| **Cost center patterns** | Departments with high violations | Targeted communication | ? |
| **Seasonal patterns** | Time-based violations | Adjusted enforcement | ? |

### C. Exception Management

**Valid Exception Reasons:**

| Reason | Documentation Required | Approval | Research Needed |
|--------|------------------------|----------|-----------------|
| **Emergency** | Situation description | Manager | ? |
| **Client meeting** | Client name, meeting details | Manager | ? |
| **Availability** | No compliant options available | Travel admin | ? |
| **Health/safety** | Medical or safety reason | HR + Travel admin | ? |
| **Executive exception** | C-level override | Self-approved | ? |

**Escalation Process:**

| Violation Count | Action | Research Needed |
|----------------|--------|-----------------|
| **1st** | Warning, education | ? |
| **2nd** | Manager notification | ? |
| **3rd** | HR notification, possible restriction | ? |
| **Chronic** | Loss of booking privileges, central booking | ? |

**Communication:**

| Trigger | Communication | Research Needed |
|----------|---------------|-----------------|
| **Policy change** | Email, in-app notification | ? |
| **Violation** | Email to traveler, manager | ? |
| **Reminder** | Periodic policy refreshers | ? |
| **Training** | Onboarding, annual training | ? |

### D. Policy Optimization

**Policy Testing:**

| Method | Description | Research Needed |
|--------|-------------|-----------------|
| **Pilot** | Test with small group | ? |
| **A/B test** | Test two policies | ? |
| **Phased rollout** | Roll out gradually | ? |
| **Feedback loop** | Gather user feedback | ? |

**Policy Change Signals:**

| Signal | Indicates | Action | Research Needed |
|--------|-----------|--------|-----------------|
| **High violation rate** | Policy too strict or unclear | Review, clarify | ? |
| **Low preferred usage** | Suppliers not meeting needs | Review suppliers | ? |
| **Consistent exceptions** | Policy doesn't fit reality | Revise policy | ? |
| **User feedback** | Pain points | Investigate | ? |

---

## Data Model Sketch

```typescript
interface PolicyCompliance {
  companyId: string;
  period: DateRange;

  // Metrics
  complianceRate: number; // % of bookings within policy
  violationCount: number;
  violationRate: number; // % of bookings outside policy

  // By category
  complianceByCategory: Map<string, number>;

  // By cost center
  complianceByCostCenter: Map<string, number>;

  // By employee
  complianceByEmployee: Map<string, EmployeeCompliance>;

  // Violations
  violations: PolicyViolation[];

  // Trends
  trends: ComplianceTrend[];
}

interface PolicyViolation {
  id: string;
  companyId: string;
  bookingId: string;
  employeeId: string;

  // Violation details
  violationType: ViolationType;
  severity: 'low' | 'medium' | 'high';
  description: string;

  // Exception
  hasException: boolean;
  exceptionReason?: string;
  exceptionApprovedBy?: string;

  // Resolution
  actionTaken?: ViolationAction;
  resolved: boolean;

  // Timestamp
  detectedAt: Date;
  resolvedAt?: Date;
}

type ViolationType =
  | 'outside_policy'
  | 'exceeds_cost_limit'
  | 'wrong_class_of_service'
  | 'wrong_hotel_category'
  | 'no_approval'
  | 'late_booking'
  | 'non_preferred_supplier';

type ViolationAction =
  | 'warning_issued'
  | 'coaching_required'
  | 'restricted'
  | 'reimbursement_denied'
  | 'no_action';

interface EmployeeCompliance {
  employeeId: string;

  // Metrics
  totalBookings: number;
  compliantBookings: number;
  violationCount: number;
  complianceRate: number;

  // Violations
  violations: PolicyViolation[];

  // Status
  status: 'compliant' | 'warning' | 'probation' | 'restricted';

  // Coaching
  lastCoachingDate?: Date;
  requiredTraining: boolean;
}

interface PolicyConfig {
  companyId: string;

  // Rules
  rules: PolicyRule[];

  // Enforcement
  enforcementLevel: 'strict' | 'moderate' | 'flexible';
  blockOutsidePolicy: boolean;

  // Exceptions
  allowExceptions: boolean;
  exceptionWorkflow: string[];

  // Communication
  violationNotifications: boolean;
  reminderFrequency: number; // days

  // Review
  reviewSchedule: Date[];
  lastReviewed: Date;
  nextReview: Date;
}

interface PolicyRule {
  id: string;
  name: string;
  type: RuleType;
  condition: RuleCondition;
  action: RuleAction;
  severity: 'low' | 'medium' | 'high';
}

type RuleType =
  | 'advance_booking'
  | 'cost_limit'
  | 'class_of_service'
  | 'hotel_category'
  | 'preferred_supplier';

interface RuleCondition {
  field: string;
  operator: 'less_than' | 'greater_than' | 'equals' | 'not_equals';
  value: any;
}

type RuleAction =
  | 'allow'
  | 'warn'
  | 'block'
  | 'require_approval';
```

---

## Compliance Workflow

**Real-Time Enforcement:**

```
1. Traveler searches
   → System applies policy rules
   → Shows compliant options first
   → Flags non-compliant options

2. Traveler selects option
   → System checks compliance
   → If compliant: proceed
   → If not compliant: show warning, require justification

3. Booking submitted
   → System final compliance check
   → If requires approval: route to approver
   → If blocked: prevent booking
   → If allowed: proceed with violation flag
```

**Post-Booking Review:**

```
1. Booking completed
   → System logs compliance status
   → If violation: flag for review

2. Compliance review (batch)
   → Travel manager reviews violations
   → Determines if exception valid
   → Takes action if needed

3. Employee notification
   → If violation: notify employee
   → If chronic violation: escalate
```

---

## Open Problems

### 1. Policy Clarity
**Challenge**: Policies are often complex and unclear

**Options**:
- Plain language summaries
- Contextual help
- Examples
- Training

### 2. Enforcement vs. Adoption
**Challenge**: Strict enforcement may reduce adoption

**Options**:
- Balanced approach
- Phased enforcement
- Feedback loops
- Manager discretion

### 3. Global Policies
**Challenge**: One policy doesn't fit all regions

**Options**:
- Regional policy variants
- Base policy + local addendums
- Currency considerations
- Local compliance requirements

### 4. Change Management
**Challenge**: Policy changes face resistance

**Options**:
- Clear communication
- Phased rollout
- Pilot programs
- Feedback channels

---

## Competitor Research Needed

| Competitor | Compliance Features | Notable Patterns |
|------------|---------------------|------------------|
| **Concur** | ? | ? |
| **TravelPerk** | ? | ? |
| **Navan** | ? | ? |

---

## Next Steps

1. Design policy engine
2. Build compliance tracking
3. Create violation workflows
4. Implement reporting
5. Develop policy testing framework

---

**Status**: Research Phase — Compliance patterns unknown

**Last Updated**: 2026-04-27