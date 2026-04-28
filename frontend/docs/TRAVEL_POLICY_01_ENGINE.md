# Travel Policy & Duty of Care — Policy Engine

> Research document for corporate travel policy rule engine, approval workflows, spending limits, preferred supplier mandates, and policy configuration.

---

## Key Questions

1. **How do we model corporate travel policies as executable rules?**
2. **What approval workflows are needed for policy exceptions?**
3. **How do spending limits work across hotels, flights, and meals?**
4. **What are preferred supplier mandates and how are they enforced?**
5. **How do policies differ by traveler seniority and trip purpose?**

---

## Research Areas

### Travel Policy Rule Engine

```typescript
interface TravelPolicyEngine {
  policies: TravelPolicy[];
  rules: PolicyRule[];
  evaluation: PolicyEvaluation;
  exceptions: ExceptionWorkflow;
}

interface TravelPolicy {
  id: string;
  companyId: string;                   // Corporate customer ID
  name: string;                        // "Standard Travel Policy"
  version: number;                     // Policy version for audit trail
  effectiveFrom: Date;
  effectiveTo?: Date;
  status: 'draft' | 'active' | 'archived';
  rules: PolicyRuleRef[];
  approvers: ApproverConfig[];
  travelerTiers: TravelerTier[];
}

interface TravelerTier {
  name: string;                        // "Junior", "Senior", "Director", "C-Suite"
  level: number;                       // 1-4 (higher = more flexibility)
  limits: SpendingLimit[];
  approvals: ApprovalRequirement[];
  benefits: TierBenefit[];
}

// Traveler tier hierarchy:
// Level 1 (Junior / Employee):
//   Flight: Economy only, max ₹15,000 domestic, ₹50,000 international
//   Hotel: Max ₹5,000/night, 3-star maximum
//   Meals: Max ₹1,500/day
//   Transport: Public transport, standard taxi (no luxury)
//   Approval: Manager approval for all bookings
//
// Level 2 (Senior / Manager):
//   Flight: Economy or Premium Economy, max ₹25,000 domestic, ₹80,000 international
//   Hotel: Max ₹8,000/night, 4-star maximum
//   Meals: Max ₹2,500/day
//   Transport: Cab, standard sedan
//   Approval: Auto-approved within limits, manager for exceptions
//
// Level 3 (Director / VP):
//   Flight: Business class for international, economy for domestic
//   Hotel: Max ₹15,000/night, 5-star allowed
//   Meals: Max ₹5,000/day
//   Transport: Premium cab, self-drive option
//   Approval: Auto-approved within limits, HR for international
//
// Level 4 (C-Suite / Founder):
//   Flight: Business class all routes
//   Hotel: No limit (within reason)
//   Meals: No limit
//   Transport: Chauffeur, premium vehicles
//   Approval: Auto-approved, admin notification only

interface PolicyRule {
  id: string;
  category: PolicyCategory;
  condition: PolicyCondition;
  action: PolicyAction;
  severity: PolicySeverity;
  message: string;                     // Human-readable explanation
}

type PolicyCategory =
  | 'flight'                           // Air travel rules
  | 'hotel'                            // Accommodation rules
  | 'transport'                        // Ground transport rules
  | 'meal'                             // Dining and entertainment
  | 'advance_booking'                  // Booking lead time requirements
  | 'destination'                      // Destination restrictions/approvals
  | 'supplier'                         // Preferred supplier mandates
  | 'expense'                          // General expense rules
  | 'documentation'                    // Visa, insurance, documentation requirements
  | 'compliance';                      // Legal/compliance requirements

type PolicySeverity =
  | 'hard_block'                       // Cannot proceed, must get exception
  | 'soft_warning'                     // Can proceed, but flagged for review
  | 'informational'                    // Just a note, no action required
  | 'hidden';                          // Internal tracking, not shown to traveler

// Rule examples:
//
// FLIGHT RULES:
// 1. Economy class only for domestic flights under 4 hours (hard_block)
//    Condition: flight.type = domestic AND flight.duration < 4h
//    Action: Block business/first class selection
//
// 2. 14-day advance booking for domestic flights (soft_warning)
//    Condition: flight.type = domestic AND booking.leadTime < 14 days
//    Action: Allow but flag for manager review
//
// 3. Maximum flight cost ₹25,000 domestic, ₹80,000 international (hard_block)
//    Condition: flight.price > tier.limits.maxFlight
//    Action: Block, require exception approval
//
// HOTEL RULES:
// 4. Maximum 3-star hotel for junior employees (hard_block)
//    Condition: traveler.tier = 1 AND hotel.starRating > 3
//    Action: Block, suggest alternatives within policy
//
// 5. Maximum ₹5,000/night hotel rate (hard_block)
//    Condition: hotel.rate > tier.limits.maxHotelRate
//    Action: Block, show policy-compliant alternatives
//
// 6. Same hotel chain for entire trip (soft_warning)
//    Condition: trip.hotels.differentChain
//    Action: Warn, suggest staying at same chain for loyalty benefits
//
// ADVANCE BOOKING RULES:
// 7. Book flights 14 days in advance for domestic (soft_warning)
// 8. Book hotels 7 days in advance (informational)
// 9. No bookings less than 3 days before travel (hard_block, requires VP approval)
//
// DESTINATION RULES:
// 10. High-risk destinations require security team approval (hard_block)
//     Condition: destination.riskLevel = "high"
//     Action: Block, route to security team approval
// 11. International travel requires passport copy upload (hard_block)
// 12. Travel to certain countries requires health insurance (hard_block)

interface PolicyCondition {
  field: string;                       // "flight.price", "hotel.starRating"
  operator: 'eq' | 'neq' | 'gt' | 'gte' | 'lt' | 'lte' | 'in' | 'not_in' | 'between';
  value: any;
  AND?: PolicyCondition[];
  OR?: PolicyCondition[];
}

// Complex condition example:
// "Block if international flight AND (business class OR first class)
//  AND traveler tier < 3 AND trip purpose != client_meeting"
// {
//   AND: [
//     { field: "flight.type", operator: "eq", value: "international" },
//     { field: "flight.cabin", operator: "in", value: ["business", "first"] },
//     { field: "traveler.tier", operator: "lt", value: 3 },
//     { field: "trip.purpose", operator: "neq", value: "client_meeting" }
//   ]
// }

interface PolicyAction {
  type: 'block' | 'warn' | 'redirect' | 'require_approval' | 'suggest_alternative';
  redirectTo?: string;                 // Approval workflow ID
  alternatives?: AlternativeConfig;
  approvalLevel?: number;              // 1=manager, 2=VP, 3=CFO, 4=CEO
}

interface SpendingLimit {
  category: string;                    // "flight_domestic", "hotel_per_night"
  period: 'per_trip' | 'per_day' | 'per_booking' | 'per_month' | 'per_quarter' | 'per_year';
  amount: number;
  currency: string;
  overage: 'block' | 'warn' | 'auto_approve_with_reason';
}

// Spending limit examples:
// Flight domestic: ₹25,000 per booking, block on overage
// Flight international: ₹80,000 per booking, warn on overage (allow with justification)
// Hotel: ₹5,000 per night, block on overage
// Meals: ₹1,500 per day, warn on overage
// Transport: ₹2,000 per day, block on overage
// Total trip: ₹1,50,000 per trip, warn on overage
// Monthly total: ₹3,00,000 per month, block on overage
```

### Approval Workflow Engine

```typescript
interface ApprovalWorkflow {
  id: string;
  name: string;                        // "Standard Exception Approval"
  triggers: ApprovalTrigger[];
  steps: ApprovalStep[];
  escalation: EscalationConfig;
  sla: SLAConfig;
}

interface ApprovalTrigger {
  rule: string;                        // Policy rule ID that triggers this
  autoRoute: boolean;                  // Auto-assign based on traveler's reporting chain
}

interface ApprovalStep {
  order: number;
  approverType: ApproverType;
  approver?: string;                   // Specific person ID
  role?: string;                       // "traveler.manager"
  timeout: number;                     // Hours before escalation
  actions: ApprovalAction[];
}

type ApproverType =
  | 'direct_manager'                   // Traveler's reporting manager
  | 'department_head'                  // Department head / VP
  | 'travel_admin'                     // Travel administrator
  | 'finance'                          // Finance team
  | 'security'                         // Security team (high-risk destinations)
  | 'hr'                               // HR (extended travel, relocation)
  | 'ceo';                             // CEO (very high value)

// Approval workflow example — Policy exception for over-budget flight:
// Step 1: Direct Manager (4h timeout)
//   Can: Approve, Reject, Request more info
//   If timeout: Auto-escalate to Step 2
//
// Step 2: Department Head (8h timeout)
//   Can: Approve, Reject, Request more info
//   If timeout: Auto-escalate to Step 3
//
// Step 3: Travel Admin + Finance (24h timeout)
//   Can: Approve, Reject, Send back for revision
//   If timeout: Auto-reject (traveler must re-submit)
//
// SLA for approvals:
// Standard exception: 24 hours total
// High-value exception (>$1 lakh): 48 hours total
// Emergency travel: 2 hours (call-based approval)
// International trip: 72 hours (multiple approvals needed)

// Exception request model:
interface PolicyException {
  id: string;
  travelerId: string;
  tripId: string;
  policyRuleId: string;
  reason: string;                      // Why the exception is needed
  justification: string;               // Business justification
  requestedValue: any;                 // What the traveler wants
  policyValue: any;                    // What the policy allows
  variance: number;                    // % over limit
  status: ExceptionStatus;
  approval: Approval[];
}

type ExceptionStatus =
  | 'pending' | 'approved' | 'rejected' | 'cancelled' | 'expired';

// Exception statistics for company dashboard:
// Total exceptions this month: 47
// Approval rate: 72%
// Average processing time: 8.2 hours
// Most common exception: Hotel rate overage (32%)
// Most rejected: Flight class upgrade without client meeting (85% rejection)
// Cost of approved exceptions: ₹3.2 lakh this month
```

### Preferred Supplier Program

```typescript
interface PreferredSupplierProgram {
  suppliers: PreferredSupplier[];
  mandates: SupplierMandate[];
  negotiation: NegotiationData;
  compliance: SupplierCompliance;
}

interface PreferredSupplier {
  id: string;
  name: string;                        // "Taj Hotels"
  category: 'airline' | 'hotel' | 'car_rental' | 'travel_insurance';
  tier: 'gold' | 'silver' | 'bronze';
  negotiatedRate: NegotiatedRate;
  corporateAccount: string;            // Corporate account number
  benefits: string[];                  // "Free breakfast", "Late checkout"
  contractExpiry: Date;
}

interface NegotiatedRate {
  discount: number;                    // % off public rate
  guaranteedRate?: number;             // Fixed rate (if negotiated)
  blackoutDates: DateRange[];          // When corporate rate doesn't apply
  minimumSpend?: number;               // Annual minimum for rate validity
}

// Preferred supplier tiers:
// Gold (must-use when available):
//   - 25-40% discount on public rates
//   - Guaranteed availability (last room/space)
//   - Dedicated support line
//   - Complimentary upgrades when available
//
// Silver (preferred):
//   - 15-25% discount on public rates
//   - Priority booking
//   - Loyalty points bonus
//
// Bronze (approved):
//   - 10-15% discount
//   - Standard terms
//   - Used when Gold/Silver not available at destination

interface SupplierMandate {
  id: string;
  category: string;
  mandate: 'must_use' | 'preferred' | 'approved_only' | 'any';
  suppliers: string[];                 // Supplier IDs
  exceptions: string[];                // When mandate can be overridden
}

// Supplier mandate examples:
// Domestic flights: Must use Air India or Vistara (gold), IndiGo (silver)
//   Exception: If gold/silver not available at required time
// Hotels in metro cities: Must use Taj, Oberoi, ITC (gold), Marriott (silver)
//   Exception: Client-recommended hotel, conference venue hotel
// Car rental: Must use Meru or Savaari (gold)
//   Exception: Client-arranged transport
// Travel insurance: Must use ICICI Lombard (gold)
//   No exception — mandatory for all international travel
//
// Supplier compliance tracking:
// Booking compliance rate: % of bookings at preferred suppliers
// Target: 85%+ compliance for gold mandates
// Savings tracking: ₹ saved vs. public rates
// Quarter review: Are we meeting minimum spend commitments?
```

---

## Open Problems

1. **Policy complexity vs. usability** — Corporate travel policies can have 100+ rules. Presenting relevant policy guidance without overwhelming travelers requires context-aware, just-in-time rule surfacing.

2. **Multi-company policy management** — A travel agency serves multiple corporate clients, each with unique policies. Maintaining accurate, versioned policies for 50+ companies requires robust policy management infrastructure.

3. **Real-time policy evaluation** — Policies must be evaluated as travelers browse options (not just at checkout). Real-time policy checking against live pricing and availability adds latency to search results.

4. **Policy harmonization across geographies** — Global companies have different policies per country (per diem rates, hotel classes, transport). A single trip spanning multiple countries may need to harmonize multiple policy rules.

5. **Exception approval bottlenecks** — Managers are slow to approve exceptions. The average 8-hour approval time can delay urgent travel. Building smart auto-approval for low-risk exceptions (within 10% of limit) balances control with speed.

---

## Next Steps

- [ ] Design travel policy rule engine with versioned policy management
- [ ] Build approval workflow engine with multi-level escalation
- [ ] Create spending limit enforcement with real-time evaluation
- [ ] Implement preferred supplier program with compliance tracking
- [ ] Study corporate travel policy platforms (SAP Concur, Navan, TripActions, TravelPerk)
