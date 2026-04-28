# Contract Renewals, Amendments & Termination

> Research document for contract modification, renewal management, and termination processes.

---

## Key Questions

1. **When should the system trigger renewal workflows — fixed period before expiry, milestone-based, or event-driven?**
2. **What are the common amendment types in travel contracts, and do they share a single workflow?**
3. **How do renewals differ for different contract types (customer, supplier, partner, employee)?**
4. **What termination rights exist, and how do notice periods vary by jurisdiction and contract type?**
5. **How do amendments affect existing bookings, invoicing, and commission calculations?**
6. **What's the retention policy for expired/terminated contracts?**

---

## Research Areas

### Renewal Management

**Renewal triggers:**

| Trigger Type | Description | Example |
|-------------|-------------|---------|
| Time-based | Fixed period before expiry | 90 days before contract end |
| Milestone | Linked to event completion | After 10th booking under contract |
| Usage-based | Volume threshold reached | After $50K in bookings |
| Manual | Agent-initiated renewal | Agent decides to renew based on relationship |
| Auto-renewal | Evergreen clause activation | Contract auto-renews unless cancelled |

**Data model sketch:**

```typescript
interface RenewalConfig {
  contractId: string;
  renewalType: 'automatic' | 'manual' | 'negotiated';
  noticePeriodDays: number;
  reminderSchedule: ReminderSchedule;
  renewalTerms?: RenewalTerms;
}

interface RenewalTerms {
  priceAdjustment?: PriceAdjustment;
  termExtension: string;       // e.g., "12 months"
  clauseChanges?: ClauseChange[];
  effectiveDate: Date;
}

interface PriceAdjustment {
  type: 'percentage' | 'fixed' | 'market_rate' | 'none';
  value?: number;
  cap?: number;                 // Maximum increase
  floor?: number;               // Minimum guaranteed
}

interface ReminderSchedule {
  reminders: Reminder[];
}

interface Reminder {
  daysBeforeExpiry: number;
  recipients: string[];         // Role-based or explicit
  channel: 'email' | 'in_app' | 'sms';
  templateId: string;
}
```

**Open questions:**
- What's the optimal renewal reminder cadence (90, 60, 30, 14 days)?
- Should auto-renewal be opt-in or opt-out for different contract types?
- How do we handle renewals where terms change (price increases, clause modifications)?

### Amendment Types & Workflows

**Common amendment categories in travel:**

| Amendment Type | Frequency | Complexity | Example |
|---------------|-----------|------------|---------|
| Price adjustment | High | Low | Seasonal rate changes |
| Scope change | Medium | Medium | Adding new destinations/properties |
| Term extension | Medium | Low | Extending contract duration |
| Clause modification | Low | High | Changing liability terms |
| Party change | Low | High | Adding/removing parties |
| Volume commitment | Medium | Medium | Adjusting minimum booking guarantees |
| Commission rate | Medium | Low | Changing commission percentages |

**Amendment workflow:**

```typescript
interface ContractAmendment {
  amendmentId: string;
  contractId: string;
  type: AmendmentType;
  status: AmendmentStatus;
  proposedBy: string;
  proposedAt: Date;
  changes: AmendmentChange[];
  justification: string;
  approvalWorkflow?: ApprovalWorkflow;
}

type AmendmentStatus =
  | 'proposed'
  | 'under_review'
  | 'approved'
  | 'rejected'
  | 'counter_proposed'
  | 'executed';

interface AmendmentChange {
  section: string;
  clauseId: string;
  currentText: string;
  proposedText: string;
  changeReason: string;
}
```

**Key research questions:**
- Do all amendments require the same approval chain as the original contract?
- Can minor amendments (e.g., price adjustments within a band) be auto-approved?
- How do amendments version the contract? New document vs. annotated supplement?

### Termination Processing

**Termination types:**

```typescript
type TerminationType =
  | 'natural_expiry'     // Contract reached end of term
  | 'mutual_agreement'   // Both parties agree to end early
  | 'breach'             // One party violated terms
  | 'convenience'        // One party exercises termination clause
  | 'force_majeure'      // Unforeseeable circumstances
  | 'insolvency'         // One party becomes insolvent
  | 'regulatory'         // Regulatory action forces termination
  | 'material_change'    // Material adverse change clause triggered;

interface TerminationRecord {
  terminationId: string;
  contractId: string;
  type: TerminationType;
  initiatedBy: string;
  effectiveDate: Date;
  noticeGivenDate: Date;
  noticePeriodDays: number;
  reason: string;
  outstandingObligations: Obligation[];
  settlementTerms?: SettlementTerms;
}

interface SettlementTerms {
  pendingPayments: number;
  pendingBookings: number;
  refundDue?: number;
  transitionPlan?: string;
  dataReturnRequired: boolean;
  confidentialitySurvival: boolean;
}
```

**Termination impact analysis:**

| Impact Area | Considerations |
|-------------|---------------|
| Active bookings | Do existing bookings honor old terms or transition? |
| Pending payments | Final settlement and reconciliation |
| Customer data | Data return/deletion per privacy obligations |
| Commission | Final commission calculation and payout |
| Inventory | Release of reserved allotments/rooms |
| Rebooking | Help customers rebook with alternative suppliers |
| Legal exposure | Post-termination liability window |

**Open problems:**
- **Bulk termination during crises** (pandemic, natural disaster): How to handle mass contract terminations while maintaining customer relationships?
- **Partial termination**: Can some services continue while others are terminated under a framework agreement?
- **Termination during amendment**: What if a termination notice arrives while an amendment is pending?

### Version Management

**Questions:**
- How do we represent contract versions? Full document snapshots or diff-based?
- How do downstream systems know which version applies to a given transaction?

```typescript
interface ContractVersion {
  versionId: string;
  contractId: string;
  version: number;
  effectiveDate: Date;
  supersededDate?: Date;
  changeType: 'original' | 'amendment' | 'renewal' | 'restatement';
  changeDescription: string;
  documentSnapshot: string;      // Full document at this version
  changesFrom?: string;          // Previous version ID
  applicableBookings: string[];  // Booking IDs governed by this version
}
```

---

## Open Problems

1. **Amendment cascading** — A supplier rate change may affect hundreds of active customer bookings. How to propagate amendments at scale?

2. **Renewal negotiation tracking** — When renewal terms are being negotiated, the contract continues under existing terms. How to track and time-box negotiations?

3. **Termination of framework agreements with active sub-agreements** — A master supplier agreement terminates but individual booking-level contracts continue. Managing this hierarchy is complex.

4. **Historical pricing disputes** — Customer claims they were charged rates from a terminated contract. How do we maintain easily accessible historical contract terms for dispute resolution?

5. **Regulatory termination rights** — Some jurisdictions grant unilateral termination rights to consumers (cooling-off periods). How to track and enforce these across markets?

6. **Automated vs. manual renewal decisions** — For low-value, high-volume contracts (standard booking T&Cs), auto-renewal makes sense. For high-value supplier agreements, manual review is essential. How to configure this per contract type?

---

## Next Steps

- [ ] Research common amendment patterns in travel industry contracts
- [ ] Design renewal reminder cadence and escalation rules
- [ ] Investigate termination impact on downstream systems (bookings, invoicing, CRM)
- [ ] Study bulk termination playbooks from travel industry crises
- [ ] Prototype version management data model with booking linkage
- [ ] Research jurisdiction-specific termination notice requirements
