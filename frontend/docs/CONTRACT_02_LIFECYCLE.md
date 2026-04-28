# Contract Lifecycle — Creation, Approval & Execution

> Research document for the contract lifecycle from drafting through execution.

---

## Key Questions

1. **What stages does a contract move through from draft to executed?**
2. **Who are the approvers at each stage, and how do approval chains compose?**
3. **How do we handle parallel vs. sequential approval workflows?**
4. **What happens when a contract is rejected or needs revision?**
5. **How do executed contracts link to downstream systems (bookings, invoices, CRM)?**
6. **What audit trail requirements exist for regulated travel contracts?**

---

## Lifecycle State Machine

```
DRAFT → INTERNAL_REVIEW → PENDING_APPROVAL → APPROVED
                                              ↘ REJECTED → REVISION → DRAFT
APPROVED → SENT_FOR_SIGNATURE → PARTIALLY_SIGNED → EXECUTED
                                              ↘ EXPIRED
                                              ↘ CANCELLED
EXECUTED → ACTIVE → AMENDMENT_PENDING → AMENDED → ACTIVE
                                      ↘ TERMINATION_PENDING → TERMINATED
ACTIVE → RENEWAL_PENDING → RENEWED → ACTIVE
                          ↘ EXPIRED
```

### State Definitions

| State | Description | Transitions To |
|-------|-------------|----------------|
| `DRAFT` | Initial creation, editing allowed | `INTERNAL_REVIEW`, `CANCELLED` |
| `INTERNAL_REVIEW` | Legal/team review | `PENDING_APPROVAL`, `DRAFT` (revision) |
| `PENDING_APPROVAL` | Awaiting authorized approver | `APPROVED`, `REJECTED` |
| `APPROVED` | Internally approved, ready for signatures | `SENT_FOR_SIGNATURE`, `CANCELLED` |
| `SENT_FOR_SIGNATURE` | Out for signing by counterparty | `PARTIALLY_SIGNED`, `EXPIRED` |
| `PARTIALLY_SIGNED` | Some parties signed, others pending | `EXECUTED` |
| `EXECUTED` | All parties signed, contract live | `ACTIVE` |
| `ACTIVE` | In effect, obligations being met | `AMENDMENT_PENDING`, `RENEWAL_PENDING`, `TERMINATION_PENDING` |
| `AMENDMENT_PENDING` | Change request in process | `AMENDED`, `ACTIVE` (rejected) |
| `AMENDED` | Modified while active | `ACTIVE` |
| `TERMINATION_PENDING` | Termination initiated | `TERMINATED`, `ACTIVE` (rescinded) |
| `TERMINATED` | Contract ended before natural expiry | — (terminal) |
| `RENEWAL_PENDING` | Approaching expiry, renewal in process | `RENEWED`, `EXPIRED` |
| `RENEWED` | Successfully renewed | `ACTIVE` |
| `EXPIRED` | Natural end of term | — (terminal) |
| `CANCELLED` | Voided before execution | — (terminal) |

---

## Research Areas

### Approval Workflow Design

**Open questions:**
- Should approval chains be role-based, amount-based, or risk-based?
- Can we use dynamic routing (e.g., high-value contracts need CFO + Legal)?
- What's the maximum acceptable turnaround time for each approval stage?

**Potential patterns:**

```typescript
interface ApprovalWorkflow {
  workflowId: string;
  contractType: ContractType;
  stages: ApprovalStage[];
}

interface ApprovalStage {
  stageOrder: number;
  approverRole: ApproverRole;
  approvalType: 'any_of' | 'all_of' | 'majority';
  timeoutHours: number;
  escalationTo?: ApproverRole;
}

type ApproverRole =
  | 'agent'           // Travel agent who created
  | 'team_lead'       // Team lead review
  | 'operations'      // Operations manager
  | 'finance'         // Finance review (revenue impact)
  | 'legal'           // Legal review
  | 'compliance'      // Regulatory compliance
  | 'senior_manager'  // Senior management
  | 'director'        // Director/VP level
```

**Research needed:**
- What approval thresholds make sense for travel contracts?
- How do OTAs handle contract approval workflows?
- What are industry-standard SLA targets for contract turnaround?

### Drafting & Collaboration

**Questions:**
- Do agents draft contracts from templates, or does the system auto-generate from booking data?
- How do multiple stakeholders collaborate on a single draft?
- What version control model works best (linear, branching)?

**Research areas:**
- Collaborative editing patterns (Google Docs-style vs. turn-based)
- Auto-generation from booking/trip data
- Clause library selection during drafting
- Variable/merge field population from CRM + booking data

### Execution & Counterparty Management

**Questions:**
- How do we track which counterparties have signed?
- What constitutes a valid electronic signature in each jurisdiction?
- How do we handle wet-ink signatures for jurisdictions that require them?

**Data model sketch:**

```typescript
interface ContractExecution {
  executionId: string;
  contractId: string;
  signatories: Signatory[];
  executionDate?: Date;
  effectiveDate?: Date;
  expiryDate?: Date;
}

interface Signatory {
  partyId: string;
  partyName: string;
  partyRole: 'customer' | 'supplier' | 'partner' | 'agency';
  signStatus: 'pending' | 'signed' | 'declined';
  signedAt?: Date;
  signatureMethod: 'electronic' | 'wet_ink' | 'digital_certificate';
  ipAddress?: string;
  documentHash?: string;
}
```

### Post-Execution Integration

**Research needed:**
- How does an executed contract trigger downstream workflows?
- What data flows from contract to booking/invoicing systems?
- How do we handle contract obligations tracking (milestones, deliverables)?

---

## Open Problems

1. **Parallel approvals with dependencies** — Some contracts may need both Legal AND Finance approval, but Finance should only see it after Legal clears. Need a flexible DAG-based approval engine.

2. **Approval timeouts and escalations** — What happens when an approver is unavailable? Auto-escalation vs. delegation vs. blocking the pipeline.

3. **Contract-version-to-booking linkage** — When a contract is amended, how do existing bookings reference the old vs. new terms?

4. **Multi-jurisdiction execution validity** — A contract between an Indian agency and a European supplier may need to satisfy both jurisdictions' signature requirements.

5. **High-volume low-value contracts** — For simple bookings, a full approval pipeline is overkill. Need a fast-track path with post-hoc audit capability.

---

## Next Steps

- [ ] Research industry-standard contract approval SLAs
- [ ] Investigate approval workflow engines (Camunda, Temporal, custom)
- [ ] Study e-signature jurisdiction requirements for key markets
- [ ] Design fast-track vs. full-review routing rules
- [ ] Prototype contract-to-booking linkage data model
