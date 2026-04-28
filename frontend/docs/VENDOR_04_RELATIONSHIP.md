# Vendor Relationship Management — Partnerships & Growth

> Research document for managing supplier relationships, negotiations, and strategic partnerships.

---

## Key Questions

1. **How do we move transactional supplier relationships toward strategic partnerships?**
2. **What negotiation levers (rate, allotment, payment terms, marketing) create mutual value?**
3. **How do we handle disputes and service recovery with key suppliers?**
4. **What data should we share with suppliers to improve collaboration?**
5. **How do we manage supplier concentration risk (over-dependence on single supplier)?**
6. **What's the right cadence for supplier relationship reviews?**

---

## Research Areas

### Relationship Lifecycle

```typescript
type RelationshipPhase =
  | 'prospecting'     // Identifying potential suppliers
  | 'courting'        // Initial conversations, exploring fit
  | 'onboarding'      // Technical and commercial setup
  | 'honeymoon'       // First few months, high engagement
  | 'steady_state'    // Established, routine operations
  | 'growth'          // Expanding scope, volume, or geography
  | 'stress'          // Issues, disputes, or market pressure
  | 'renewal'         // Contract renewal decision point
  | 'decline'         // Reducing volume or scope
  | 'exit';           // Winding down the relationship

interface SupplierRelationship {
  supplierId: string;
  currentPhase: RelationshipPhase;
  phaseHistory: PhaseTransition[];
  relationshipManager: string;
  strategicImportance: 'critical' | 'important' | 'standard' | 'marginal';
  annualBookingVolume: number;
  annualRevenue: number;
  dependencyScore: number;       // 0-1, how much we rely on them
  exclusivityType: 'none' | 'preferred' | 'exclusive' | 'strategic';
  lastReviewDate: Date;
  nextReviewDate: Date;
  npsScore?: number;            // Internal NPS — would we recommend them?
}

interface PhaseTransition {
  from: RelationshipPhase;
  to: RelationshipPhase;
  date: Date;
  reason: string;
  triggeredBy: string;
}
```

### Negotiation Framework

**Common negotiation dimensions in travel:**

| Dimension | Supplier Perspective | Agency Perspective | Win-Win Opportunity |
|-----------|---------------------|-------------------|---------------------|
| Room/seat rates | Maximize RevPAR/yield | Competitive pricing for customers | Dynamic pricing with guaranteed minimum |
| Allotments | Committed inventory = revenue certainty | Guaranteed availability for customers | Flexible allotment with release periods |
| Payment terms | Faster payment, less credit risk | Longer terms, better cash flow | Early payment discounts |
| Commission | Higher commission on sales | Better margins | Tiered commission based on volume |
| Marketing | Featured placement, promotion | Differentiated offerings | Co-marketing with shared costs |
| Data sharing | Market insights, demand patterns | Performance data, customer feedback | Mutual analytics platform |
| Cancellation | Restrictive cancellation policies | Flexible changes for customers | Tiered cancellation with price points |

**Data model sketch:**

```typescript
interface NegotiationRecord {
  negotiationId: string;
  supplierId: string;
  type: 'rate_renewal' | 'new_contract' | 'dispute_resolution' | 'scope_expansion';
  status: 'preparation' | 'in_progress' | 'agreement' | 'deadlock' | 'cancelled';
  startedAt: Date;
  participants: NegotiationParticipant[];
  terms: NegotiationTerm[];
  outcome?: NegotiationOutcome;
}

interface NegotiationTerm {
  dimension: string;
  supplierPosition: string;
  agencyPosition: string;
  agreedValue?: string;
  priority: 'must_have' | 'important' | 'nice_to_have';
}
```

### Dispute Management

**Common dispute types:**
- Overbooking (supplier confirms but can't honor)
- Rate discrepancies (contracted vs. charged rate)
- Service quality failures (downgraded room, no-show transfer)
- Payment disputes (commission calculation differences)
- Cancellation penalties (disagreement on policy application)
- Inventory misrepresentation (property doesn't match listing)

```typescript
interface SupplierDispute {
  disputeId: string;
  supplierId: string;
  bookingId: string;
  category: DisputeCategory;
  priority: 'low' | 'medium' | 'high' | 'critical';
  status: DisputeStatus;
  reportedBy: string;
  reportedAt: Date;
  description: string;
  resolution?: DisputeResolution;
}

type DisputeCategory =
  | 'overbooking'
  | 'rate_mismatch'
  | 'quality_failure'
  | 'payment_issue'
  | 'cancellation_dispute'
  | 'misrepresentation'
  | 'non_performance'
  | 'other';

interface DisputeResolution {
  resolutionType: 'refund' | 'credit' | 'replacement' | 'waiver' | 'escalated' | 'unresolved';
  amount?: number;
  resolvedAt: Date;
  resolvedBy: string;
  customerImpact: 'none' | 'minor' | 'moderate' | 'severe';
  preventiveAction?: string;
}
```

### Supplier Concentration & Risk

**Risk indicators:**

```typescript
interface SupplierRiskProfile {
  supplierId: string;
  concentrationRisk: number;       // % of category bookings
  financialRisk: 'low' | 'medium' | 'high';
  operationalRisk: 'low' | 'medium' | 'high';
  geographicRisk: 'low' | 'medium' | 'high';
  singlePointOfFailure: boolean;
  backupSuppliers: string[];
  lastIncidentDate?: Date;
  incidentFrequency: number;       // Incidents per quarter
}
```

**Questions:**
- What concentration threshold triggers risk mitigation (e.g., >30% of hotel bookings via one chain)?
- How do we develop backup suppliers without cannibalizing preferred relationships?
- What's the contingency plan when a critical supplier suddenly fails?

### Data Sharing & Collaboration

**What data helps both parties:**

| Data Type | Shared By | Value |
|-----------|-----------|-------|
| Booking forecast | Agency → Supplier | Supplier can plan staffing/inventory |
| Customer feedback | Agency → Supplier | Quality improvement insights |
| Market pricing | Supplier → Agency | Competitive positioning |
| Availability updates | Supplier → Agency | Real-time inventory accuracy |
| Performance benchmarks | Agency → Supplier | Industry positioning |
| Demand patterns | Both | Joint capacity planning |

**Open questions:**
- How much data is too much to share (competitive sensitivity)?
- Should suppliers get a self-service analytics dashboard?
- What data formats and delivery mechanisms work for suppliers of different tech maturity?

---

## Open Problems

1. **Relationship at scale** — Managing relationships with 500+ suppliers requires different tools and cadences than managing 20. How to scale without losing the personal touch?

2. **Dispute-relationship tension** — Aggressive dispute resolution may save money on one booking but damage the relationship. How to balance short-term financial recovery with long-term partnership health?

3. **Rate parity enforcement** — Suppliers sometimes offer lower rates on other channels. How to detect and address this without becoming adversarial?

4. **Seasonal relationship dynamics** — In peak season, suppliers hold all the leverage. In low season, agencies do. How to build balanced relationships that weather seasonal power shifts?

5. **Supplier succession** — When a supplier's ownership changes (hotel sold, agency acquired), the relationship resets. How to maintain continuity?

---

## Next Steps

- [ ] Research supplier relationship management best practices in travel industry
- [ ] Design negotiation playbook templates for common scenarios
- [ ] Study dispute resolution workflows in OTA platforms
- [ ] Prototype supplier concentration risk dashboard
- [ ] Investigate supplier collaboration portal features
- [ ] Design relationship health scoring model
