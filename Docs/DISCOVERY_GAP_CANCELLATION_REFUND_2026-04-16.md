# Discovery Gap Analysis: Cancellation/Refund Policy Engine

**Date**: 2026-04-16
**Gap Register**: #05 (P1 — agencies handle cancellations daily)
**Scope**: Cancellation mode detection, policy engine, refund eligibility, reason categorization, rebooking alternatives, supplier cancellation terms. NOT: payment gateway, commission reconciliation, insurance claims processing.

---

## 1. Executive Summary

The system detects cancellation mode from text ("cancel", "refund") and routes it correctly — but that's where it stops. The insertion of `"pending_policy_lookup"` as a placeholder contradiction is the honest admission: there is no policy engine, no refund calculation, no reason categorization, no supplier terms, and no rebooking logic. The system can say "this is a cancellation" but cannot answer "what is the customer owed?" or "what are their options?"

Agencies handle cancellations daily. This is not a rare edge case — it's a core operational workflow that currently requires the agent to manually compute everything off-system.

---

## 2. Evidence Inventory

### What's Documented

| Doc | What It Says | Location |
|-----|-------------|----------|
| `ADDITIONAL_SCENARIOS_21_25.md` L418-508 | **Scenario #26: Last-Minute Cancellation** — most detailed design. Input facts (reason, notice period, prepaid amounts), NB02 policy engine process (reason category, insurance check, financial impact), 4 output options with cost/timeline/message, recommendation logic | Docs/personas_scenarios/ |
| `NB02_V02_SPEC.md` L161 | Cancellation mode: "Run policy engine: refund eligibility, insurance check, alternative paths" | notebooks/ |
| `NB03_V02_SPEC.md` L77 | Cancellation mode in each decision state: ASK_FOLLOWUP="Policy questions", PROCEED="Cancellation summary with options", STOP="Policy briefing" | notebooks/ |
| `INDUSTRY_PROCESS_GAP_ANALYSIS` L32-33 | Refund processing: "calculate refund per supplier cancellation policy → track completion"; Credit note management: "supplier issues credit note → agency tracks → applies to future booking" | Docs/ |
| `INDUSTRY_PROCESS_GAP_ANALYSIS` L69 | Fare rules awareness: "non-refundable vs refundable, change fees, name change rules, baggage allowance, vary by fare class" | Docs/ |
| `INDUSTRY_PROCESS_GAP_ANALYSIS` L73 | Reissue/rebooking: "flight change → reissue ticket → calculate fare difference → collect/refund difference" | Docs/ |
| `LEAD_LIFECYCLE_AND_RETENTION.md` L131 | `cancellation_dispute` signal: -0.20 to repeat_likelihood score | Docs/ |
| `UX_AND_USER_EXPERIENCE.md` L558-560 | Cancellation Mode: "Agent sees policy engine, refund calculator, insurance status. Traveler receives clear options with financial implications." | Docs/ |
| `NOTEBOOK_04_CONTRACT.md` L143 | `PricingBreakdown` includes `cancellation_policy: str` field | Docs/research/ |
| `V02_GOVERNING_PRINCIPLES.md` L30-32 | Cancellation is P2 concern, treated as packet field or derived signal | Docs/ |

### What's Implemented

| Code | What It Does | Status |
|------|-------------|--------|
| `extractors.py` L598-599 | Keyword classifier: `"cancel"/"cancellation"/"refund"` → `"cancellation"` mode | **Working** — mode detection is functional |
| `packet_models.py` L288-291 | `"cancellation"` as valid `operating_mode` literal | **Working** — data structure supports it |
| `decision.py` L1392-1402 | Cancellation mode routing: suppress soft blockers, add `cancellation_policy` contradiction with value `"pending_policy_lookup"` | **Stub** — placeholder only |
| `decision.py` L1264-1265 | `cancellation_dispute` lifecycle signal: -0.20 to repeat_likelihood | **Working** — single scoring adjustment |
| `strategy.py` L268,285,302,322,334,349 | Mode-specific strategy text: 6 hardcoded strings for cancellation across decision states | **Working** — display only, no computation |
| `safety.py` L189,199-200 | `"refund"` → `"Please review cancellation and refund policies."` text sanitization | **Working** — defensive, not computational |
| `test_e2e_freeze_pack.py` L314-345 | Scenario 5: tests mode detection + traveler-safe output | **Partial** — tests mode only, not policy engine |

### What's NOT Implemented

- No cancellation policy engine
- No refund eligibility calculation (medical/personal/force majeure categories)
- No reason categorization
- No insurance coverage check
- No financial impact options (full refund, partial refund, reschedule, insurance claim)
- No supplier cancellation terms model (hotel non-refundable, flight penalties, activity partial)
- No rebooking/alternative suggestion logic
- No credit note tracking
- No fare rules awareness

---

## 3. Gap Taxonomy

### Structural Gaps

| Gap ID | Concept | Implementation | Blocks |
|--------|---------|----------------|--------|
| **CN-01** | Cancellation policy engine | `decision.py` inserts `"pending_policy_lookup"` placeholder | Refund calculation, option generation |
| **CN-02** | Cancellation reason categories | None — all cancellations treated identically | Insurance check, policy application |
| **CN-03** | Supplier cancellation terms model | None — no supplier entity, no per-component refund rules | Per-component refund calculation |
| **CN-04** | Refund eligibility calculator | None — no quote/collection/supplier data to compute from | Financial impact options |
| **CN-05** | Rebooking/alternative path logic | None — no date-change workflow, no alternative search | Zero-loss option delivery |

### Computation Gaps

| Gap ID | What Needs Computing | Current State | Blocked By |
|--------|---------------------|---------------|------------|
| **CC-01** | Refund amount per component (hotel non-refundable, flight penalty, activity partial) | Not computable — no supplier terms, no financial state | CN-03, #04 (financial state) |
| **CC-02** | Total refund eligibility based on reason + timing + insurance | Not computable — no reason category, no timing data | CN-02, CN-01 |
| **CC-03** | Financial impact options (4 options per Scenario #26) | Not computable — no cost data | CC-01, CC-02 |
| **CC-04** | Rebooking cost (fare difference + date change fee) | Not computable — no fare rules | CN-03, #01 (vendor data) |

### Integration Gaps

| Gap ID | Connection | Status | Blocked By |
|--------|-----------|--------|------------|
| **CN-06** | Cancellation mode → Policy engine | Mode detected, routing placeholder `"pending_policy_lookup"` | CN-01 |
| **CN-07** | Policy engine → Financial state | No financial state to read | #04 (financial state) |
| **CN-08** | Policy engine → Supplier terms | No supplier data | #01 (vendor/cost) |
| **CN-09** | Policy engine → Insurance check | No insurance data model | New model needed |
| **CN-10** | Cancellation result → Lifecycle | `cancellation_dispute` signal exists but no computed refund data feeds it | CN-01 |

---

## 4. Data Model

```python
from dataclasses import dataclass, field
from typing import Optional, List, Literal
from decimal import Decimal
from datetime import datetime

@dataclass
class CancellationRequest:
    """Input to the policy engine."""
    trip_id: str
    requested_at: str = field(default_factory=lambda: datetime.now().isoformat())
    reason_category: Optional[str] = None  # "medical", "personal", "force_majeure", "change_of_plans"
    reason_detail: str = ""
    notice_period_days: Optional[int] = None  # How many days before trip
    requested_by: str = "traveler"  # "traveler" | "agent" | "supplier"
    
@dataclass
class ComponentRefundPolicy:
    """Per-component cancellation terms from supplier."""
    component_type: str  # "hotel", "flight", "transfer", "activity", "visa"
    supplier_name: str
    cancellation_window_hours: int  # Free cancellation within X hours of booking
    refund_percentage: Decimal  # e.g., 0.0 = non-refundable, 1.0 = full refund
    penalty_flat: Decimal = Decimal("0")  # Fixed penalty amount
    credit_note_eligible: bool = False  # Supplier offers credit instead of cash
    fare_class: str = ""  # For flights: "economy_non_refundable", "economy_flexible", "business"
    
@dataclass
class RefundOption:
    """One option presented to the customer."""
    label: str  # "Full Refund", "Partial Refund", "Reschedule", "Insurance Claim"
    description: str
    refund_amount: Decimal
    customer_pays: Decimal
    timeline: str  # "7-10 business days", "Immediate credit"
    conditions: List[str] = field(default_factory=list)
    recommendation_score: float = 0.0  # 0.0-1.0, higher = more recommended
    
@dataclass
class CancellationResult:
    """Output from the policy engine."""
    request: CancellationRequest
    component_policies: List[ComponentRefundPolicy] = field(default_factory=list)
    total_paid: Decimal = Decimal("0")
    total_refundable: Decimal = Decimal("0")
    total_non_refundable: Decimal = Decimal("0")
    options: List[RefundOption] = field(default_factory=list)
    recommended_option: Optional[str] = None
    insurance_applicable: bool = False
    insurance_claim_amount: Decimal = Decimal("0")
    credit_notes_available: List[str] = field(default_factory=list)
    requires_owner_approval: bool = False  # High-value refunds need owner sign-off
```

---

## 5. Phase-In Recommendations

### Phase 1: Mode Detection + Reason Capture (P0, ~1-2 days, unblocked)

1. Extract cancellation reason from text (keyword + future LLM enhancement)
2. Categorize reason: medical, personal, force_majeure, change_of_plans
3. Compute notice_period_days from trip dates
4. Replace `"pending_policy_lookup"` placeholder with real `CancellationRequest` dataclass
5. Wire `cancellation_dispute` signal to include reason category

**Acceptance**: When a customer says "I need to cancel because my mother is in hospital, trip is in 3 days", system extracts reason=medical, notice=3 days, and routes to cancellation mode with structured data.

### Phase 2: Basic Policy Engine + Manual Terms (P1, ~3-4 days, blocked by #04 financial state)

1. Create `ComponentRefundPolicy` dataclass
2. Agent manually enters supplier cancellation terms per component (hotel non-refundable, flight 80% refund, etc.)
3. Compute refund eligibility per component based on:
   - Notice period vs. cancellation window (full refund if >X days, partial if >Y, none if <Z)
   - Reason category (medical may override standard terms)
4. Generate `RefundOption` list with costs and timelines
5. Show "Refund Estimate" in internal agent view

**Acceptance**: Agent enters "hotel non-refundable, flight 80% refundable, transfer 100% refundable" and system computes: "Total paid: 3L. Refundable: 1.8L. Non-refundable: 1.2L."

### Phase 3: Insurance Check + Rebooking (P2, ~3-4 days, blocked by #01 vendor data)

1. Add insurance coverage check (manual entry for MVP: "yes, covered for medical")
2. Add rebooking option: reissue flights, modify hotel dates, adjust transfers
3. Add `requires_owner_approval` flag for refunds > threshold
4. Wire to notification engine (gap #03) for owner escalation on high-value refunds
5. Add credit note tracking (supplier offers credit instead of cash refund)

**Acceptance**: System presents 4 options: full refund (if eligible), partial refund with breakdown, reschedule with new dates, file insurance claim. Owner gets notified for refunds >50% of trip value.

### Phase 4: Automated Terms + Fare Rules (P3, blocked by #01 vendor data maturity)

1. Auto-populate supplier cancellation terms from vendor database
2. Add flight fare rules awareness (non-refundable vs flexible, change fees)
3. Add cascading rebooking: flight change → auto-update hotel check-in, transfer pickup
4. Add cancellation analytics: track reasons, refund rates, agent handling time

**Acceptance**: When customer cancels a Goa trip, system auto-looks up: "Hotel Taj: non-refundable. SpiceJet: Rs.2,500 change fee. Transfer: 100% refundable." and computes options automatically.

---

## 6. Key Decisions Required

| Decision | Options | Recommendation | Impact |
|----------|---------|----------------|--------|
| Who enters supplier cancellation terms? | (a) Agent manually per trip, (b) Auto from vendor database, (c) Default templates by component type | **(a) Manual per trip for MVP**, migrate to (b) when vendor DB exists | CN-03 input method |
| Refund approval threshold? | (a) No approval needed, (b) Owner approval above X amount, (c) Agent can approve up to Y, owner above Y | **(c) Agent up to 25% of trip value, owner above** | Business rule, not technical |
| Insurance integration? | (a) Manual yes/no entry, (b) Insurance provider API, (c) Not for MVP | **(a) Manual yes/no for MVP** — system doesn't process insurance claims, just flags applicability | Insurance scope |
| Cancellation reason classification? | (a) Keyword-based, (b) LLM classification, (c) Agent selects from dropdown | **(c) Agent selects from dropdown** — most reliable, simplest to implement | CN-02 input method |
| Credit notes vs. cash refunds? | (a) Cash only, (b) Credit notes only, (c) Both tracked separately | **(c) Both tracked separately** — some suppliers offer only credit notes | Financial tracking |

---

## 7. Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Agent enters wrong cancellation terms | High | Default templates by component type (hotel non-refundable, flight partial). Audit trail for all manual entries. |
| Refund calculation errors cause financial disputes | High | Show "estimate, not final" disclaimer. Owner approval for high-value refunds. Audit trail. |
| Policy is too rigid for real-world nuance | Medium | Always present manual override option for agent. System recommends, agent decides. |
| Medical/emergency cancellations have different legal requirements | Medium | Reason category drives different policy paths. Medical has higher refund potential. Document legal requirements per jurisdiction. |
| Customer dissatisfaction with non-refundable components | Medium | Show refund breakdown clearly (what's refundable, what's not, why). Offer alternatives (reschedule, credit note). |

---

## 8. What's Out of Scope

- Insurance claims processing (system flags applicability, doesn't process claims)
- Automated supplier cancellation communication (agent calls/emails supplier)
- Legal compliance for refund timelines (jurisdiction-specific)
- Payment gateway for refund execution (system tracks state, money moves off-system)
- Commission adjustment on cancellations (separate financial tracking concern)
- Flight rebooking API integration (agent handles rebooking manually for MVP)