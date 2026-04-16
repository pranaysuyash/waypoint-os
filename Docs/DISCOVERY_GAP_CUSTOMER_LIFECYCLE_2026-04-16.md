# Discovery Gap Analysis: Customer Lifecycle & Cross-Trip Memory

**Date**: 2026-04-16
**Gap Register**: #06 (P1 — repeat customers are agency lifeblood)
**Scope**: Customer entity, lifecycle state machine, cross-trip memory, engagement tracking, repeat detection, lifecycle scoring, commercial action routing, retention/churn.

---

## 1. Executive Summary

The system has a well-specified 16-state lifecycle machine (`LEAD_LIFECYCLE_AND_RETENTION.md`, 224 lines) and fully deterministic scoring logic (4 scoring functions in `decision.py`). The data structure (`LifecycleInfo`) faithfully implements the doc's schema. **But all of it operates on ephemeral, empty-by-default data.** There is no customer database, no trip history, no session persistence, and no code that populates engagement fields from real events. The scoring heuristics will always produce 0.0 in production because LifecycleInfo is never fed real data.

The honest state: the lifecycle machine is a `Literal` type annotation and a set of mathematically correct scoring functions that have nothing to score.

---

## 2. Evidence Inventory

### What's Documented

| Doc | What It Says | Location |
|-----|-------------|----------|
| `LEAD_LIFECYCLE_AND_RETENTION.md` (224 lines) | 16-state lifecycle machine, loss_reason/win_reason dimensions, engagement metrics, 4 deterministic scoring heuristics with exact weights/thresholds, 7-action `COMMERCIAL_DECISION` family, 4 intervention playbooks, 9 KPIs | Docs/ |
| `NB01_V02_SPEC.md` L75-77, L176-179 | `customer_id` as fact, `is_repeat_customer` as derived signal ONLY, `past_trips` as fact list, `_check_repeat_customer()` stub | notebooks/ |
| `15_MISSING_CONCEPTS.md` L72-86 | "Repeat-Customer Memory" — current: `source_envelope_ids` exists but no `customer_id` or `trip_history`. MVP-now: `customer_id` fact, `is_repeat_customer` derived. Later: `past_trips`, `preference_consistency` | notebooks/ |
| `DATA_STRATEGY.md` L101, L144 | PostgreSQL schema: `customers` table, `trips` table with `customer_id` foreign key, customer analytics queries | Docs/research/ |
| `INDUSTRY_PROCESS_GAP_ANALYSIS` L146-155 | 6 missing post-trip processes: feedback, supplier loop, referral ask, review solicitation, repeat trigger, anniversary marketing | Docs/ |
| `INDUSTRY_PROCESS_GAP_ANALYSIS` L179-189 | 7 missing agent KPIs including repeat customer rate, lead-to-booking conversion | Docs/ |
| `INDUSTRY_PROCESS_GAP_ANALYSIS` L307 | "Customer recognition on repeat inquiry" is a top-15 dealbreaker | Docs/ |
| `PERSONA_PROCESS_GAP_ANALYSIS` L44 | "No `customer_id`, no history lookup, no repeat detection" — P0 gap | Docs/ |
| `DISCOVERY_GAP_DATA_PERSISTENCE_2026-04-16.md` L97 | PC-02: "Customer lookup / repeat detection" — keyword-based, no DB | Docs/ |

### What's Implemented

| Code | What It Does | Status |
|------|-------------|--------|
| `packet_models.py` L185-231 | `LifecycleInfo` dataclass — 17+ fields including all engagement metrics | **Data structure only** — never populated from real data |
| `decision.py` L1190-1297 | 4 scoring functions: `score_ghost_risk()`, `score_window_shopper_risk()`, `score_repeat_likelihood()`, `score_churn_risk()` | **Correct logic, empty inputs** — will always produce 0.0 without populated LifecycleInfo |
| `decision.py` L1310-1339 | `decide_commercial_action()` — 7-action routing with thresholds | **Works in tests, produces `NONE` in production** |
| `decision.py` L1264-1265 | `cancellation_dispute` signal: -0.20 to repeat_likelihood | **Working** — single adjustment |
| `extractors.py` L552-555 | `customer_id` regex extraction from text patterns | **Keyword-based** — no DB lookup |
| `extractors.py` L1178-1193 | `is_repeat_customer` keyword detection ("past", "previous", "repeat", "returning") | **Heuristic** — no persistent history |
| `extractors.py` L1041-1048 | `past_trips` regex hook — captures unstructured context string | **Minimal** — `{"context": "past trip to singapore"}`, confidence 0.6 |
| `safety.py` L189, L199-200 | `"refund"` text sanitization | **Working** — not lifecycle-related |
| `test_lifecycle_retention.py` (86 lines) | 5 tests for lifecycle scoring and action routing | **Tests work with manually injected data** |
| `validation.py` L28 | `"is_repeat_customer"` in derived_signals validation set | **Correct** — stays in derived_signals only |

### What's NOT Implemented

- No customer entity / database
- No lifecycle state transition engine (16 states defined, no valid transition logic)
- No engagement event tracking (quote opens, link clicks, response times)
- No session persistence (LifecycleInfo defaults to None/empty on every run)
- No `customer_id` DB lookup (regex text extraction only)
- No `past_trips` structured data (unstructured regex hook only)
- No repeat detection from database (keyword heuristic only)
- No intervention playbook execution
- No KPI tracking (9 metrics defined, 0 tracked)
- No post-booking lifecycle stages (WON through DORMANT = 9 states, zero implementation)

---

## 3. Gap Taxonomy

### Structural Gaps

| Gap ID | Concept | Implementation | Blocks |
|--------|---------|----------------|--------|
| **LC-01** | Customer entity (database) | No `customers` table, no customer lookup, no CRM | All lifecycle features, repeat detection, cross-trip memory |
| **LC-02** | Lifecycle state transition engine | Literal type only, no transition validation, no state machine | Lead progression from NEW_LEAD to WON and beyond |
| **LC-03** | Engagement event tracking | LifecycleInfo fields exist but never populated from real events | Ghost risk, window shopper detection, churn scoring |
| **LC-04** | Cross-trip memory (past_trips) | Regex hook captures `"past trip to singapore"` only | Preference consistency, repeat personalization |
| **LC-05** | Post-booking lifecycle stages | 9 states defined (WON→DORMANT), zero implementation | Booking-to-completion pipeline |

### Computation Gaps

| Gap ID | What Needs Computing | Current State | Blocked By |
|--------|---------------------|---------------|------------|
| **LC-06** | Ghost risk score from real engagement data | Scoring function exists, produces 0.0 (no `days_since_last_reply`, no `quote_opened`) | LC-03 |
| **LC-07** | Window shopper score from real behavior data | Scoring function exists, produces 0.0 (no `revision_count`, no `options_viewed_count`) | LC-03 |
| **LC-08** | Repeat likelihood from real trip history | Scoring function exists, produces 0.0 (no `repeat_trip_count`, no `last_trip_completed_at`) | LC-01, LC-04 |
| **LC-09** | Churn risk from real retention signals | Scoring function exists, produces 0.0 (no prior trip data) | LC-01, LC-04 |
| **LC-10** | Commercial decision from real scores | Routing function exists, produces `NONE` (all scores 0.0) | LC-06 through LC-09 |

---

## 4. Dependency Graph

```
#02 Data Persistence ─── blocks LC-01 (customer entity), LC-02 (lifecycle state store), LC-03 (events)
│
├── LC-01 (Customer Entity)
│   ├── blocks LC-04 (past_trips needs customer to link trips)
│   ├── blocks LC-08 (repeat likelihood needs trip count)
│   └── blocks LC-09 (churn risk needs prior trip data)
│
├── LC-02 (State Transition Engine)
│   └── blocks lead progression from NEW_LEAD to any later state
│
├── LC-03 (Engagement Tracking)
│   ├── blocks LC-06 (ghost risk needs engagement data)
│   └── blocks LC-07 (window shopper needs behavior data)
│
└── #03 Communication Channels ─── blocks LC-03 (engagement events come from messages, emails, portal)
```

**Key insight**: LC-01 (customer entity) is the #1 blocker. Without persistent customer records, no lifecycle feature works. This is blocked by #02 (data persistence).

---

## 5. Data Model

```python
from dataclasses import dataclass, field
from typing import Optional, List, Literal
from datetime import datetime
from enum import Enum

class LifecycleState(str, Enum):
    NEW_LEAD = "NEW_LEAD"
    ACTIVE_DISCOVERY = "ACTIVE_DISCOVERY"
    QUOTE_IN_PROGRESS = "QUOTE_IN_PROGRESS"
    QUOTE_SENT = "QUOTE_SENT"
    ENGAGED_AFTER_QUOTE = "ENGAGED_AFTER_QUOTE"
    GHOST_RISK = "GHOST_RISK"
    WON = "WON"
    BOOKING_IN_PROGRESS = "BOOKING_IN_PROGRESS"
    TRIP_CONFIRMED = "TRIP_CONFIRMED"
    TRIP_ACTIVE = "TRIP_ACTIVE"
    TRIP_COMPLETED = "TRIP_COMPLETED"
    REVIEW_PENDING = "REVIEW_PENDING"
    RETENTION_WINDOW = "RETENTION_WINDOW"
    REPEAT_BOOKED = "REPEAT_BOOKED"
    DORMANT = "DORMANT"
    LOST = "LOST"

VALID_TRANSITIONS = {
    "NEW_LEAD": ["ACTIVE_DISCOVERY", "LOST"],
    "ACTIVE_DISCOVERY": ["QUOTE_IN_PROGRESS", "GHOST_RISK", "LOST"],
    "QUOTE_IN_PROGRESS": ["QUOTE_SENT", "GHOST_RISK", "LOST"],
    "QUOTE_SENT": ["ENGAGED_AFTER_QUOTE", "GHOST_RISK", "LOST"],
    "ENGAGED_AFTER_QUOTE": ["WON", "GHOST_RISK", "LOST"],
    "GHOST_RISK": ["ENGAGED_AFTER_QUOTE", "DORMANT", "LOST"],
    "WON": ["BOOKING_IN_PROGRESS", "LOST"],
    "BOOKING_IN_PROGRESS": ["TRIP_CONFIRMED", "LOST"],
    "TRIP_CONFIRMED": ["TRIP_ACTIVE", "LOST"],
    "TRIP_ACTIVE": ["TRIP_COMPLETED"],
    "TRIP_COMPLETED": ["REVIEW_PENDING"],
    "REVIEW_PENDING": ["RETENTION_WINDOW"],
    "RETENTION_WINDOW": ["REPEAT_BOOKED", "DORMANT"],
    "REPEAT_BOOKED": ["TRIP_CONFIRMED", "LOST"],
    "DORMANT": ["REPEAT_BOOKED", "LOST"],
    "LOST": [],  # Terminal state
}

@dataclass
class Customer:
    """Customer entity — the persistent record that doesn't exist yet."""
    id: str
    agency_id: str
    name: str = ""
    phone: str = ""
    email: str = ""
    notes: str = ""
    first_seen_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_interaction_at: Optional[str] = None
    total_trips_completed: int = 0
    total_revenue: float = 0.0
    avg_trip_value: float = 0.0
    
@dataclass
class CustomerTrip:
    """Cross-trip memory — one trip per customer."""
    id: str
    customer_id: str
    destination: str
    travel_dates: str
    trip_type: str  # "family", "couple", "adventure", etc.
    budget_band: str
    outcome: str  # "completed", "cancelled", "postponed"
    satisfaction: Optional[float] = None  # 1-5 rating
    issues: List[str] = field(default_factory=list)  # ["late_flight", "hotel_downgrade"]
    would_recommend: Optional[bool] = None
    completed_at: Optional[str] = None

@dataclass
class EngagementEvent:
    """Tracks customer interactions — populates LifecycleInfo fields."""
    id: str
    customer_id: str
    trip_thread_id: str
    event_type: str  # "message_sent", "quote_opened", "link_clicked", "docs_shared", "payment_made"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict = field(default_factory=dict)
```

---

## 6. Phase-In Recommendations

### Phase 1: Customer Entity + State Machine (P0, ~3-4 days, blocked by #02)

1. Create `customers` table (id, agency_id, phone, email, name, notes, timestamps)
2. Create `trips` table with `customer_id` foreign key
3. Implement lifecycle state transition engine with `VALID_TRANSITIONS` validation
4. Wire `customer_id` lookup in NB01 extractor to DB query (replace regex heuristic)
5. Store lifecycle state on trip entity, persist across sessions

**Acceptance**: A repeat customer's phone number triggers a DB lookup. System shows: "Welcome back, Sharma family! Last trip: Goa, Jan 2025." Lifecycle state persists between sessions.

### Phase 2: Engagement Tracking + Scoring Population (P1, ~2-3 days, blocked by #03)

1. Create `engagement_events` table
2. Record events: message sent/received, quote opened, link clicked, document shared, payment made
3. Populate `LifecycleInfo` fields from real engagement data: `days_since_last_reply`, `quote_open_count`, `revision_count`
4. Wire scoring functions to real data instead of empty defaults

**Acceptance**: Ghost risk score computes from actual `days_since_last_reply` and `quote_open_count`. Commercial action routing produces meaningful recommendations instead of `NONE`.

### Phase 3: Cross-Trip Memory + Repeat Personalization (P1, ~2-3 days, blocked by #02)

1. Create `customer_trips` table storing structured trip history
2. Replace `is_repeat_customer` keyword heuristic with DB lookup: `SELECT COUNT(*) FROM trips WHERE customer_id = ? AND outcome = 'completed'`
3. Build `past_trips` fact from DB instead of regex
4. Add preference consistency signal: compare current trip preferences against past trip patterns
5. Wire `repeat_trip_count` and `last_trip_completed_at` from real data

**Acceptance**: Returning customer automatically gets: "Based on your Goa trip, you enjoyed beach destinations with adventure activities." No re-asking preferences already captured.

### Phase 4: Post-Trip Lifecycle (P2, ~3-4 days, blocked by #03, #11)

1. Implement post-booking lifecycle states: WON → BOOKING_IN_PROGRESS → TRIP_CONFIRMED → TRIP_ACTIVE → TRIP_COMPLETED
2. Add review request trigger at TRIP_COMPLETED (transition to REVIEW_PENDING)
3. Add retention window at RETENTION_WINDOW (automated follow-ups, seasonal offers)
4. Add repeat detection: if customer returns in retention window, transition to REPEAT_BOOKED
5. Add dormancy: if no engagement in retention window, transition to DORMANT
6. Track 9 KPIs from LEAD_LIFECYCLE doc

**Acceptance**: Lead lifecycle progresses automatically through states based on events. Agent dashboard shows lifecycle stage per customer. Churn risk flags appear for DORMANT customers.

---

## 7. Key Decisions Required

| Decision | Options | Recommendation | Impact |
|----------|---------|----------------|--------|
| Customer identifier? | (a) Phone number, (b) Email, (c) Auto-generated ID, (d) Phone+Email composite | **(a) Phone number for MVP** — primary identifier in Indian travel agencies. Email as secondary. | LC-01 design |
| Lifecycle state storage? | (a) On trip entity, (b) On customer entity, (c) Separate state table | **(b) On customer entity** — lifecycle belongs to the customer-relationship, not individual trips | LC-02 design |
| Engagement event granularity? | (a) Full event stream, (b) Aggregated counters only, (c) Hybrid | **(c) Hybrid** — store full stream, maintain aggregated counters for fast scoring | LC-03 performance |
| How to detect repeat customers in MVP? | (a) Phone number lookup, (b) WhatsApp number matching, (c) Manual agent selection | **(a) Phone number lookup** — most reliable, matches Indian travel agency workflow | LC-01 MVP |
| Past trip data entry? | (a) Manual by agent, (b) Auto from completed trips, (c) Both | **(c) Both** — auto-populate from completed trips, manual for pre-system history | LC-04 completeness |

---

## 8. Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Customer data quality — phone numbers with/without country code | High | Normalize phone numbers on input. Support multiple formats. Allow manual merge of duplicate records. |
| Lifecycle states become stale — state not updated for days | Medium | Event-driven transitions: state updates trigger from real events. Auto-detect GHOST_RISK from `days_since_last_reply`. |
| Engagement events overwhelm — too many events per customer | Medium | Aggregate counters for scoring, store raw events for analytics. TTL on raw events. |
| Multiple phone numbers per customer | Medium | Allow multiple contact methods per customer. Primary phone + secondary. |
| Cross-trip memory spookiness — customer feels surveilled | Medium | Only surface relevant past trip preferences, not all data. Frame as "Based on your preferences..." not "I know you went to Goa last January..." |

---

## 9. What's Out of Scope

- Marketing automation (email campaigns, drip sequences) — retention window identifies opportunity, execution is manual
- CRM integration with external tools (HubSpot, Zoho) — MVP uses built-in customer entity
- Predictive churn ML models — deterministic scoring heuristics for MVP, ML layer later
- Customer portal self-service — ShareToken access only (gap #08)
- Social media monitoring for engagement — manual agent input only