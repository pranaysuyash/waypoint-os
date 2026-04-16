# Discovery Gap Analysis: Financial State Tracking

**Date**: 2026-04-16
**Gap Register**: #04 (P0 — agencies are financial intermediaries)
**Scope**: Quote/collected/pending/confirmed state tracking. NOT payment gateway, NOT reconciliation, NOT commission settlement. Agencies collect money wherever they want; system records the state.

---

## 1. Executive Summary

Agencies are financial intermediaries — they collect money, pay suppliers, keep the spread. The system captures budget as a raw number but cannot track: what was quoted, what was collected, what's pending, what's confirmed by supplier.

Per user direction: the system tracks **state**, not money flow. No payment gateway. No reconciliation engine. No commission settlement. Just: "quote was 3L, collected 1.5L, balance pending, supplier X confirmed at 2.6L net."

---

## 2. Evidence Inventory

### What's Documented

| Doc | What It Says | Location |
|-----|-------------|----------|
| `INDUSTRY_PROCESS_GAP_ANALYSIS` | 23 financial sub-processes: deposit collection, multi-party splits, payment reminders, refund processing, credit notes, commission reconciliation, TCS/GST/LRS/FEMA compliance | Docs/ |
| `LEAD_LIFECYCLE_AND_RETENTION.md` | `payment_stage` field: "none" / "token" / "partial" / "full". Commitment signals. | Docs/ |
| `UX_MULTI_CHANNEL_STRATEGY.md` | Payment link generation, `PaymentSection` component, payment reminder via all channels | Docs/ |
| `UX_AND_USER_EXPERIENCE.md` | Per-family payment tracking, dependency gating, automated reminders | Docs/ |
| `Master Product Spec` | Payment_method as booking-stage hard blocker | Docs/ |
| `NOTEBOOK_04_CONTRACT.md` | `PricingBreakdown`, `PriceComponent`, `PaymentMilestone`, `InternalQuoteSheet` with cost breakdowns and margins | Docs/research/ |

### What's Implemented

| Code | What It Does | Status |
|------|-------------|--------|
| `packet_models.py` L177, L223 | `payment_status`, `payment_stage` fields exist as dataclass attributes | Placeholder literals only: "none", "token", "partial", "full" |
| `decision.py` L169 | `payment_method` listed as booking-stage hard blocker field name | No logic follows — field presence check only |
| `decision.py` L1209, 1228, 1326 | Lifecycle scoring uses `requested_hold`, `asked_payment_plan`, `payment_stage` as signals | Scoring exists but no actual payment state drives it |

### What's NOT Implemented

- No quote amount storage (what was quoted to client)
- No collection tracking (what client paid)
- No balance tracking (what's still owed)
- No supplier cost tracking (what supplier confirmed at net rate)
- No payment milestone/schedule
- No multi-party split (Family A 3L, Family B 2.5L)
- No overdue detection or escalation
- No refund state tracking
- No credit note management

---

## 3. Gap Taxonomy

### Structural Gaps

| Gap ID | Concept | Implementation | Blocks |
|--------|---------|----------------|--------|
| **FN-01** | Quote amount entity | None — budget captured but not what was quoted | Proposal delivery, margin calculation |
| **FN-02** | Collection tracker | None — payment_stage is a placeholder string | Payment reminders, overdue detection |
| **FN-03** | Supplier cost confirmation | None — overlaps with G-01/G-03 from vendor gap | Margin calculation, booking readiness |
| **FN-04** | Payment milestone schedule | None — no deposit/balance/due-date concept | Escalation, deadline tracking |
| **FN-05** | Multi-party payment splits | None — no sub-group payment tracking | Group trip financial management |

### Computation Gaps

| Gap ID | What Needs Computing | Current State | Blocked By |
|--------|---------------------|---------------|------------|
| **FC-01** | Outstanding balance | Not computed — no quote or collection data | FN-01, FN-02 |
| **FC-02** | Overdue detection | Not computed — no due dates | FN-04 |
| **FC-03** | Payment readiness gate | `payment_method` field presence only — no amount check | FN-01, FN-02 |
| **FC-04** | Net margin estimate | Not computed — no supplier cost data | FN-03, #01 (vendor gap) |

---

## 4. Data Model (State Tracking Only)

```python
@dataclass
class FinancialState:
    """Trip-level financial state — NOT a payment gateway."""
    
    quote: Optional[QuoteRecord] = None
    collections: List[CollectionRecord] = field(default_factory=list)
    supplier_costs: List[SupplierCostRecord] = field(default_factory=list)
    milestones: List[PaymentMilestone] = field(default_factory=list)
    
    @property
    def total_quoted(self) -> Optional[Decimal]:
        """Total amount quoted to client."""
        
    @property
    def total_collected(self) -> Decimal:
        """Total amount collected from client."""
        
    @property
    def balance_pending(self) -> Optional[Decimal]:
        """Quote minus collected. None if no quote."""
        
    @property
    def total_supplier_cost(self) -> Decimal:
        """Total confirmed supplier costs (net)."""
        
    @property
    def estimated_margin(self) -> Optional[Decimal]:
        """Quote minus supplier cost. None if either missing."""

@dataclass
class QuoteRecord:
    """What was quoted to the client."""
    amount: Decimal
    currency: str = "INR"
    options: List[QuoteOption] = field(default_factory=list)
    valid_until: Optional[str] = None
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass  
class QuoteOption:
    """One option within a multi-option quote."""
    label: str
    amount: Decimal
    description: str = ""

@dataclass
class CollectionRecord:
    """A single payment collected from client."""
    amount: Decimal
    collected_at: str
    method: str = ""  # "cash", "bank_transfer", "upi", "cheque", etc.
    note: str = ""    # "Deposit from Sharma family"
    party: str = ""   # For group splits: "Family A", "Family B"

@dataclass
class SupplierCostRecord:
    """A confirmed supplier cost (net rate)."""
    supplier_name: str
    component: str    # "hotel", "flights", "transfer", "activity"
    cost: Decimal
    confirmed_at: Optional[str] = None
    reference: str = ""  # Booking ref, confirmation number

@dataclass
class PaymentMilestone:
    """Expected payment schedule."""
    label: str        # "30% Deposit", "Balance", "Final Payment"
    amount: Decimal
    due_date: Optional[str] = None
    status: str = "pending"  # "pending", "collected", "overdue", "waived"
```

---

## 5. Phase-In Recommendations

### Phase 1: Quote + Collection State (P0, ~2 days, blocked by #02)
1. Add `FinancialState` to trip persistence (JSONB column in trips table)
2. Add quote recording: when agent generates proposal, record quote amount(s)
3. Add collection entry: agent manually enters "received 30K from Sharma via UPI"
4. Compute balance_pending property
5. Show financial summary in trip workspace

**Acceptance**: Agent can see "Quoted 3L, Collected 1.5L, Pending 1.5L" per trip.

### Phase 2: Supplier Cost + Margin Estimate (P1, ~2 days, overlaps with #01)
1. Add supplier cost recording per component
2. Compute estimated_margin (quote - supplier costs)
3. Wire `margin_risk` signal to real margin data (replaces heuristic)
4. Show margin in internal-only view (already protected by safety.py)

**Acceptance**: Agent sees "Quoted 3L, Supplier Cost 2.4L, Margin 20%" in internal view.

### Phase 3: Milestones + Overdue Detection (P1, ~2 days, blocked by #03 for alerts)
1. Add payment milestone schedule (deposit, balance, due dates)
2. Compute overdue status from due dates
3. Wire overdue detection to notification engine
4. Add escalate-to-owner on overdue > 3 days

**Acceptance**: System flags "Balance of 1.5L overdue by 5 days" and alerts agent/owner.

### Phase 4: Multi-Party Splits (P2, ~1 day)
1. Add `party` field to CollectionRecord
2. Add per-party balance calculation
3. Show per-family breakdown in group trip view

**Acceptance**: Group trip shows "Family A: 3L quoted, 1.5L collected; Family B: 2.5L quoted, 2.5L collected."

---

## 6. Key Decisions Required

| Decision | Options | Recommendation | Impact |
|----------|---------|----------------|--------|
| Who enters collections? | (a) Agent manually, (b) Auto from payment gateway, (c) CSV import | **(a) Agent manually** — no gateway integration. System records state, not transactions. | Defines FN-02 input method |
| Track supplier costs or just client-side? | (a) Both sides, (b) Client-side only, (c) Supplier-side only | **(a) Both** — margin requires both quote and cost. Supplier costs entered manually. | Enables margin visibility |
| Currency handling? | (a) INR only, (b) Multi-currency with conversion, (c) Store as entered + display converted | **(a) INR only for MVP** — add forex later (gap #17 blind spot #14) | Simplicity |
| Overdue escalation path? | (a) Alert agent, (b) Alert owner, (c) Agent first then owner, (d) Configurable | **(d) Configurable** — owner sets escalation policy (links to #16 configuration) | Flexibility |

---

## 7. Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Agents don't enter collections manually | High | Make it one-click from WhatsApp context. Pre-fill amount from quote. Default to common amounts. |
| Financial data becomes stale — never updated after quote | High | Auto-nag: if quote exists but no collection after 3 days, prompt agent to update. |
| Margin visibility leaks to wrong people | Medium | Already mitigated by safety.py — `owner_margins`, `commission_rate`, `net_cost` are INTERNAL_ONLY. Extend to new fields. |
| No audit trail for financial changes | Medium | All financial state changes written to events table (gap #13). |

---

## 8. What's Out of Scope (Per User Direction)

- Payment gateway integration (Razorpay, PayU, Stripe)
- Commission reconciliation with suppliers
- Credit note management
- TCS/GST calculation and filing (separate gap #15)
- LRS/FEMA compliance tracking (separate gap #15)
- Accounting system integration (Tally/QuickBooks)
- Bank reconciliation
- Invoice generation (separate gap — may add in Phase 2)