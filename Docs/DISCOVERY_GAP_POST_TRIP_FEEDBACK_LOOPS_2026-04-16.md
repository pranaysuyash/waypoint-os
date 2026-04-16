# Discovery Gap Analysis: Post-Trip/Feedback/Learning Loops

**Date**: 2026-04-16
**Gap Register**: #11 (P2 — post-booking lifecycle)
**Scope**: Feedback collection, supplier scoring, review solicitation, repeat booking triggers, learning loops. NOT: customer lifecycle state machine (#06), analytics KPIs (#12).

---

## 1. Executive Summary

There is a `post_trip` operating mode defined and scoring signals that reference post-trip concepts (`positive_feedback`, `positive_review`, `no_feedback_captured`), but **zero implementation** of any post-trip workflow. No feedback forms, no CSAT rating, no review collection, no supplier scoring, no repeat booking trigger. The system can detect "I just got back from my trip" in text, but cannot ask "how was it?", record the answer, learn from it, or use it to improve future trips.

---

## 2. Evidence Inventory

### What's Documented

| Doc | What | Location |
|-----|------|----------|
| `INDUSTRY_PROCESS_GAP_ANALYSIS` L145-155 | 6 missing post-trip processes: feedback collection (D+3 to D+5), supplier feedback, referral ask, review solicitation, repeat trigger, anniversary marketing | Docs/ |
| `INDUSTRY_PROCESS_GAP_ANALYSIS` L187 | Agent CSAT tracking — "directly affects agent incentives" | Docs/ |
| `INDUSTRY_PROCESS_GAP_ANALYSIS` L311, L333 | Post-trip feedback collection and supplier quality loop as top-15 dealbreakers | Docs/ |
| `PERSONA_PROCESS_GAP_ANALYSIS` L56, L155 | S1: "Sharmas returned — send review request"; S2: "Rate 1-5" — no implementation | Docs/ |
| `PERSONA_PROCESS_GAP_ANALYSIS` L214-215 | Post-trip & Retention: 6 documented workflows, 0 implemented | Docs/ |
| `LEAD_LIFECYCLE_AND_RETENTION.md` L142, L148-150 | `no_feedback_captured` +0.20 churn risk; `positive_review` -0.25; `referral_made` -0.20 | Docs/ |
| `LEAD_LIFECYCLE_AND_RETENTION.md` L193-202 | 9 KPIs including post-trip metrics | Docs/ |
| `DISCOVERY_GAP_CUSTOMER_LIFECYCLE` | Lifecycle transitions: TRIP_COMPLETED → REVIEW_PENDING → RETENTION_WINDOW | #06 deep-dive |

### What's Implemented

| Code | What | Status |
|------|------|--------|
| `packet_models.py` L206 | `REVIEW_PENDING` and `RETENTION_WINDOW` lifecycle states | Literal type only, no transitions |
| `extractors.py` L604-605 | `"feedback"` / `"review request"` → `"post_trip"` mode detection | **Working** — keyword detection |
| `decision.py` L1251-1252 | `positive_feedback`/`positive_review` signals boost repeat likelihood +0.15 | Empty data — never populated |
| `decision.py` L1282 | `no_feedback_captured` signal adds +0.20 churn risk | Empty data — never populated |
| `decision.py` L1404-1406 | `post_trip` mode skips blocker logic | **Working** — mode routing |

### What's NOT Implemented

- No feedback collection form/API
- No CSAT rating input or storage
- No supplier quality scoring
- No review solicitation (Google, TripAdvisor links)
- No referral request trigger
- No repeat booking trigger from retention window
- No anniversary/birthday marketing
- No learning loop (past trip satisfaction → future recommendations)
- No post-trip lifecycle transitions (TRIP_COMPLETED → REVIEW_PENDING → RETENTION_WINDOW)

---

## 3-4. Gap Taxonomy & Data Model

### Structural Gaps

| Gap ID | Concept | Implementation | Blocks |
|--------|---------|----------------|--------|
| **PT-01** | Feedback collection form | None | CSAT, supplier scoring, learning loops |
| **PT-02** | Supplier quality scoring | None | Supplier selection improvement, margin optimization |
| **PT-03** | Review solicitation | None | Online reputation, social proof |
| **PT-04** | Repeat booking trigger | None | Retention, lifetime value |
| **PT-05** | Learning loop (feedback → recommendations) | None | Continuous improvement |

```python
@dataclass
class TripFeedback:
    trip_id: str
    customer_id: str
    overall_rating: int          # 1-5
    would_recommend: bool
    would_book_again: bool
    supplier_ratings: List[SupplierRating] = field(default_factory=list)
    high_points: List[str] = field(default_factory=list)
    low_points: List[str] = field(default_factory=list)
    free_text: str = ""
    collected_at: str = field(default_factory=lambda: datetime.now().isoformat())
    collected_via: str = ""       # "whatsapp", "email", "portal", "agent_call"

@dataclass
class SupplierRating:
    supplier_name: str
    component: str                 # "hotel", "transfer", "activity"
    rating: int                    # 1-5
    issue_category: str = ""      # "cleanliness", "service", "location", "value"
    issue_detail: str = ""
```

---

## 5-8. Phase-In, Decisions, Risks, Out of Scope

### Phase 1: Feedback Collection (P2, ~2 days, blocked by #02, #06)

1. Add `TripFeedback` data model
2. Add post-trip CSAT collection via WhatsApp (simple 1-5 rating + optional comment)
3. Wire `positive_feedback` and `no_feedback_captured` signals to real data
4. Store feedback in trip record

**Acceptance**: Agent sends feedback link after trip. Customer rates 1-5. Rating stored in trip record. `no_feedback_captured` flag set if no response after 5 days.

### Phase 2: Supplier Scoring + Review Solicitation (P2, ~2 days, blocked by #01)

1. Add per-supplier rating aggregation
2. Add review link generation (Google, TripAdvisor)
3. Add referral request trigger after positive feedback

**Acceptance**: Agent sees "Taj Mumbai: 4.2/5 from 12 trips". After 5-star rating, system suggests asking for Google review.

### Phase 3: Learning Loop + Repeat Trigger (P3, ~3 days, blocked by #06, #07)

1. Use feedback data to influence recommendations (prefer high-rated suppliers)
2. Auto-trigger retention window messages based on seasonal patterns
3. Wire repeat likelihood scoring to real feedback data

**Acceptance**: Previous 4-star Goa trip preferences inform next recommendation. Retention message sent automatically at 30-day mark.

| Decision | Options | Recommendation |
|----------|---------|----------------|
| Feedback channel | (a) WhatsApp only, (b) Email only, (c) Both + portal | **(a) WhatsApp for MVP** — primary channel in Indian agency context |
| CSAT format | (a) 1-5 rating, (b) NPS (0-10), (c) Binary satisfied/unsatisfied | **(a) 1-5 rating** — simple, familiar, matches `overall_rating` field |
| When to collect | (a) D+1, (b) D+3, (c) D+7 | **(b) D+3** — fresh enough to be accurate, not so soon as to feel intrusive |

| Risk | Severity | Mitigation |
|------|----------|------------|
| Low response rate | High | Make feedback one-click. Send reminder after 3 days. Agent personal follow-up for no-response. |
| Negative feedback not actionable | Medium | Route negative ratings to owner immediately. Tag for supplier review. |

**Out of Scope**: Automated survey forms, sentiment analysis on free text, social media review monitoring, competitor benchmarking, agent commission adjustment from CSAT.