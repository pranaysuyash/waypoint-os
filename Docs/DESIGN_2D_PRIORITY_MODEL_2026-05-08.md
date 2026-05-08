# 2D Trip Priority Model: Comprehensive Design Document

**Date:** 2026-05-08
**Status:** Design Proposal
**Trigger:** Random Document Audit of D-001/D-003 Implementation Plan
**Scope:** Replace 1D urgency-only priority with 2D urgency x importance model
**Author:** Audit Agent

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Background: Why This Matters](#2-background-why-this-matters)
3. [Current Codebase: Exhaustive Priority Code Path Map](#3-current-codebase-exhaustive-priority-code-path-map)
4. [Current Model: What It Actually Does](#4-current-model-what-it-actually-does)
5. [Bugs and Anti-Patterns Discovered](#5-bugs-and-anti-patterns-discovered)
6. [External Research: Design Systems](#6-external-research-design-systems)
7. [External Research: Priority Models in Operations Software](#7-external-research-priority-models-in-operations-software)
8. [External Research: CRM and Lead Scoring](#8-external-research-crm-and-lead-scoring)
9. [External Research: Travel Agency CRM Patterns](#9-external-research-travel-agency-crm-patterns)
10. [External Research: Dashboard UX Patterns](#10-external-research-dashboard-ux-patterns)
11. [First-Principles Priority Framework](#11-first-principles-priority-framework)
12. [2D Scoring Formulas](#12-2d-scoring-formulas)
13. [Visual Indicator Design](#13-visual-indicator-design)
14. [Component Architecture](#14-component-architecture)
15. [Implementation Plan](#15-implementation-plan)
16. [Operational Safety](#16-operational-safety)
17. [Appendices](#17-appendices)

---

## 1. Executive Summary

The current priority model is broken. It computes a single score from SLA breaches and validation failures. It cannot tell the difference between a $50,000 VIP trip and a $500 cold lead — both get `medium` priority if they have the same SLA days. The `low` priority label is defined but unreachable. The formula is duplicated in two places with a latent scale bug. The visual indicator (a colored left-border stripe) violates the project's own design system and is an AI-slop marker.

The fix is a 2D priority model that separates **urgency** (time pressure) from **importance** (business impact), computes both independently, and combines them into an actionable priority category.

This document synthesizes the full codebase audit and research from IBM Carbon, NN/G, Smashing Magazine, dashboard design pattern literature, ITIL/ITSM standards, Salesforce and HubSpot lead scoring, and travel agency CRM analysis to justify every design decision.

---

## 2. Background: Why This Matters

On 2026-04-23, D-001 removed `CardAccent` — a colored left-border bar on cards — as "AI slop pattern #8." The justification was that "status is already communicated via badge." The component was deleted. Tests passed. Everyone moved on.

But three things happened:

**First**, the same visual pattern re-emerged. The inbox `TripCard.tsx` was built with an inline `<div>` that draws a 3px colored left bar (`TripCard.tsx:336-341`). The sidebar nav (`Shell.tsx:201-207`) has a 2px active indicator. The overview page (`overview/page.tsx:130,242`) uses a red left border on error cards. The workbench CSS (`workbench.module.css:586`) has a 3px left border on review notes. The component was deleted but the pattern multiplied — now with inconsistent widths, colors, and no reusability.

**Second**, the `.impeccable.md` design system already bans this pattern. Rule #4: "No border-left stripes — absolute ban on border-left: 4px accent stripes." The codebase violates its own design system in four separate places.

**Third**, nobody asked what the bar was trying to communicate. The answer: trip priority. Operators scan 20-50 trips in their inbox and need to know which ones demand attention. The left bar was a visual crutch for a real information need: "what should I work on next?"

This audit traces priority through every code path, evaluates the model, researches alternatives, and proposes a replacement that actually solves the operator's problem.

---

## 3. Current Codebase: Exhaustive Priority Code Path Map

### 3.1 Backend: Priority Computation

**File: `spine_api/services/inbox_projection.py` (606 lines)**
**Date: 2026-05-04. Author: Agent. Canonical source of truth for inbox logic.**

| Lines | Element | Role |
|-------|---------|------|
| 36-55 | `_STATUS_TO_INBOX_STAGE` | Maps DB status to inbox stage names |
| 48-55 | `_STAGE_NUMBERS` | Stage ordering (intake=1, booking=5) |
| 57-59 | `_SLA_DAYS_*` | Thresholds: at_risk at 4d, breached at 7d |
| 61-66 | `_DEFAULT_PRIORITY_SCORE` | `{low:25, medium:50, high:75, critical:90}` |
| 130-158 | `_compute_days_in_current_stage()` | Days since creation or most recent event timestamp |
| 161-166 | `_compute_sla_status(days)` | `>7d → breached, >4d → at_risk, else on_track` |
| 220-233 | `_budget_value(source)` | Extracts budget from 7 candidate fields |
| 236-247 | `_date_window_value(source)` | Extracts date window from 5 candidate fields |
| 278-321 | `_extract_flags(source)` | Derives flags: incomplete, details_unclear, needs_clarification, unassigned, high_value |
| 328-606 | `InboxProjectionService` | Projection + filter + search + sort + paginate |
| 345-346 | `__init__(self, now)` | Injectable clock for testability |
| 351-353 | `project_all(trips)` | Projects list of raw dicts → list of InboxTripView |
| **355-421** | **_project_one(source)** | **Core priority computation** |
| 364-377 | Priority logic | See Section 4 for formula |
| 396-421 | Return dict | Fields: id, reference, destination, tripType, partySize, dateWindow, value, priority, priorityScore, stage, stageNumber, assignedTo, assignedToName, submittedAt, lastUpdated, daysInCurrentStage, slaStatus, customerName, flags |
| 426-435 | `apply_filter(filter_key)` | `all/at_risk/incomplete/unassigned` tab filters |
| 440-449 | `apply_search(query)` | Text matches customerName, destination, reference, id |
| 454-468 | `apply_sort(key, dir)` | Keys: priority, destination, value, party, dates, sla |
| 473-522 | `apply_multi_filters(**kwargs)` | Composable multi-select: priorities, sla_statuses, stages, assigned_to, min_value, max_value |
| 527-540 | `paginate(page, limit)` | Offset-based pagination with hasMore |
| 545-555 | `filter_counts(trips)` | Counts of all, at_risk, incomplete, unassigned over full dataset |
| 562-606 | `build_inbox_response()` | Orchestrator: project → filter → search → multi_filter → sort → paginate → counts |

**File: `spine_api/contract.py` (592 lines)**

| Lines | Model | Fields |
|-------|-------|--------|
| 460-462 | `TripListResponse` | items: List[Dict], total: int |
| 465-469 | `FilterCounts` | all, at_risk, incomplete, unassigned |
| **472-496** | **`InboxTripItem`** | id, reference, destination, tripType, partySize, dateWindow, value, **priority: Literal["low","medium","high","critical"]**, **priorityScore: int**, stage, stageNumber, assignedTo?, assignedToName?, submittedAt, lastUpdated, daysInCurrentStage, **slaStatus: Literal["on_track","at_risk","breached"]**, customerName, flags: List[str] |
| 499-504 | `InboxResponse` | items: List[InboxTripItem], total, hasMore, filterCounts |
| 507-511 | `InboxStatsResponse` | total, unassigned, critical (count of escalation_severity in {high,critical}), atRisk (count of sla_status=="at_risk"), onTrack |
| 70 | `SpecialtyKnowledgeHit` | urgency: str = "NORMAL" |
| 209-213 | `OverrideRequest` | new_severity, original_severity |
| 310 | `PipelineStageConfig` | sla_hours: Optional[int] |
| 399 | `IntegrityIssue` | severity: "low"\|"medium"\|"high"\|"critical" |
| 439 | `SuitabilitySignal` | severity: "low"\|"medium"\|"high"\|"critical" |
| 110-114 | `TripUpdateRequest` | escalation_severity (set on trip PATCH) |

**File: `spine_api/server.py`**

| Lines | Endpoint | Priority/SLA role |
|-------|----------|-------------------|
| 1418 | Module constant | `_INBOX_STATUSES = "new,incomplete,needs_followup,awaiting_customer_details,snoozed"` |
| 1420-1481 | `GET /inbox` | Query params: sort (default "priority"), dir (default "desc"), priority (comma-sep filter), slaStatus, stages, assignedTo, minValue, maxValue, q (search), limit, page |
| 1473-1474 | | Passes priority and slaStatus to `build_inbox_response()` |
| 1511-1533 | `GET /inbox/stats` | critical = trips where escalation_severity in {high, critical}; atRisk = trips where sla_status == "at_risk" |
| 3327-3337 | `GET /analytics/reviews` | Filters by `analytics.requires_review is True` |
| 3761-3839 | Override validation | Severity downgrade requires `new_severity < original_severity` |
| 4049-4067 | `GET /analytics/escalations` | Heatmap by `analytics.escalation_severity in {high, critical}` |

**File: `spine_api/services/sla_service.py`**

| Lines | Element | Notes |
|-------|---------|-------|
| 22-26 | Ownership SLA defaults | warn at 4h, breach at 24h |
| 52-108 | `compute_sla()` | Hour-based SLA — NOT used by inbox priority, which uses day-based thresholds |

**File: `spine_api/models/trips.py`**

| Lines | Field | Role |
|-------|-------|------|
| 33 | source | "unknown" by default |
| 34 | status | "new" by default |
| 35 | stage | "discovery" by default |
| 38-40 | follow_up_due_date | Optional[datetime] — custom follow-up promise |
| 41-47 | party_composition, pace_preference, date_year_confidence, lead_source, activity_provenance, trip_priorities, date_flexibility | Intake capture fields |
| 46 | **trip_priorities** | Optional[str] — free-text priority signals captured at intake, UNUSED in current priority computation |
| 65 | analytics | Optional[dict] — JSON blob with escalation_severity, sla_status, requires_review |
| 52-53 | validation, decision | JSON blobs used in priority computation (is_valid, confidence_score) |

### 3.2 Frontend: Priority Computation

**File: `frontend/src/lib/bff-trip-adapters.ts` (581 lines)**

| Lines | Element | Role |
|-------|---------|------|
| 7 | `type SlaStatus` | Alias for inbox slaStatus |
| 297-301 | `computeSlaStatus(days)` | `>7 → breached, >4 → at_risk, else on_track` — duplicate of BE logic |
| 326-358 | `extractFlags()` | Uses is_valid, confidence, hard_blockers |
| 360-497 | `transformSpineTripToTrip()` | Reads analytics.requires_review, analytics.escalation_severity |
| 514-569 | `transformSpineTripToInboxTrip()` | Calls computeSlaStatus, then priority formula |
| **529-543** | **Frontend priority computation** | **Section 4.2 below** |

**File: `frontend/src/lib/inbox-helpers.ts` (414 lines)**

| Lines | Element | Role |
|-------|---------|------|
| 39-46 | `SORT_OPTIONS` | `{key:'priority', label:'Priority', defaultDirection:'desc'}` plus 5 others |
| 55-95 | SLA computation | `computeSLAPercentage()` — (daysInCurrentStage * 24) / slaHours * 100 |
| 102-109 | `DEFAULT_STAGE_SLA_HOURS` | intake:24, details:72, options:72, review:48, booking:336 |
| 132-151 | `serializeFilters()` | Encodes priority, slaStatus to URL params |
| 156-193 | `deserializeFilters()` | Decodes priority, slaStatus from URL params |
| 199-204 | `priorityOrder` | `{low:0, medium:1, high:2, critical:3}` |
| 206-210 | `slaOrder` | `{breached:0, at_risk:1, on_track:2}` |
| 215-245 | `compareTrips()` | Priority sort: primary=priorityOrder, secondary=slaOrder |
| 348-355 | `METRIC_ROW_CONFIG` | teamLead shows: assignee, sla, days, priority; finance shows: value, stage, dates, priority |
| 390-414 | `MICRO_LABELS` | critical="needs human review", high="high attention", medium="standard priority", low="low priority" |

**File: `frontend/src/types/governance.ts` (262 lines)**

| Lines | Type | Definition |
|-------|------|-----------|
| 140 | `TripPriority` | `'low' \| 'medium' \| 'high' \| 'critical'` |
| 142-162 | `InboxTrip` | id, reference, destination, tripType, partySize, dateWindow, value, priority: TripPriority, priorityScore: number, stage, stageNumber, assignedTo?, assignedToName?, submittedAt, lastUpdated, daysInCurrentStage, slaStatus: 'on_track'\|'at_risk'\|'breached', customerName, flags: string[] |
| 164-173 | `InboxFilters` | priority?: readonly TripPriority[], slaStatus?: readonly slaStatus[], plus stage, assignedTo, dateRange, minValue, maxValue |
| 52-58 | `TripReview` | feedbackSeverity?, slaStatus?, recoveryStatus? |

**File: `frontend/src/types/generated/spine-api.ts`**

| Lines | Type | Priority-related fields |
|-------|------|----------------------|
| 26 | AnalyticsPayload | requires_review: boolean |
| 29 | AnalyticsPayload | feedback_severity?: ("low"\|"medium"\|"high"\|"critical") |
| 35 | AnalyticsPayload | sla_status?: ("on_track"\|"at_risk"\|"breached") |
| 37 | AnalyticsPayload | escalation_severity?: ("high"\|"critical") |
| 70 | BottleneckAnalysis | severity: "low"\|"medium"\|"high"\|"critical" |
| 158 | IntegrityIssue | severity |
| 195 | OperationalAlert | severity: "high"\|"critical" |
| 423 | SuitabilitySignal | severity |

### 3.3 Frontend: Priority Display

**File: `frontend/src/components/inbox/TripCard.tsx` (424 lines)**

| Lines | Element | Role |
|-------|---------|------|
| 32-37 | `PRIORITY_BAR` | `{critical:'#f85149', high:'#d29922', medium:'#58a6ff', low:'#8b949e'}` |
| 39-43 | `SLA_BADGE` | Colored bg/text/border for on_track (green), at_risk (amber), breached (red) |
| 45-52 | `STAGE_BG` | Per-stage colored badges |
| 63-75 | `METRIC_FORMATTERS.priority` | Capitalizes priority (e.g. "high" → "High") for display |
| 81-97 | `TripCardMetrics` | Role-dependent metrics: teamLead shows priority+sla, finance shows priority+value |
| 127-145 | `TripCardSLA` | Displays "N days · X% of SLA" with color badge |
| 306-422 | `TripCard` main | **Line 314**: accentColor = PRIORITY_BAR[trip.priority]; **Lines 336-341**: inline 3px left bar `<div className="absolute left-0 top-0 bottom-0 w-[3px]" style={{background:accentColor}} aria-hidden="true"/>` — this is the banned AI-slop pattern |
| 327-334 | | Inline mouseEnter/mouseLeave handlers for hover effect (bypasses the Card component's own hover handling) |

**File: `frontend/src/components/inbox/ComposableFilterBar.tsx` (432 lines)**

| Lines | Element | Role |
|-------|---------|------|
| 18-28 | `FILTER_GROUPS[0]` | Priority multi-select: critical, high, medium, low |
| 30-38 | `FILTER_GROUPS[1]` | SLA multi-select: breached, at_risk, on_track |
| 147-149 | `CHIP_LABELS` | Formats "Priority: Critical", "SLA: At Risk" for active filter chips |
| 227-233 | Preset "My Urgent" | priority: [critical, high], slaStatus: [breached, at_risk] |
| 236-240 | Preset "Needs Owner" | assignedTo: [unassigned], slaStatus: [breached] |

**File: `frontend/src/app/(agency)/inbox/page.tsx` (520 lines)**

| Lines | Element | Role |
|-------|---------|------|
| 24-27 | Imports | TripCard, ComposableFilterBar, ViewProfileToggle, InboxEmptyState from @/components/inbox/ |
| 29-30 | Imports | deserializeFilters, getSavedViewProfile, etc. from @/lib/inbox-helpers |
| 404-406 | Lead count display | Shows "{N} leads total" — uses "lead" language per inbox domain boundary |

### 3.4 Frontend: BFF Route

**File: `frontend/src/app/api/inbox/route.ts` (53 lines)**

| Lines | Element | Role |
|-------|---------|------|
| 26-28 | Comment | "Backend returns typed InboxTripItem[] directly — no transformation needed" |
| 15 | GET handler | Proxies to `${SPINE_API_URL}/inbox` with all query params |
| | **Key** | Pure pass-through from backend. Frontend gets priority pre-computed from backend. |

### 3.5 Frontend: API Client

**File: `frontend/src/lib/governance-api.ts`**

| Lines | Element | Role |
|-------|---------|------|
| 202-227 | `getInboxTrips()` | Serializes filters.priority, filters.slaStatus, filters.stage, etc. to URL params, calls `api.get('/api/inbox?${params}')` |

### 3.6 Data Flow Summary

```
Agency Operator opens /inbox
  → frontend/src/app/(agency)/inbox/page.tsx
  → useInboxTrips(filters, page, limit, sortBy, sortDir, query)
  → GET /api/inbox?sort=priority&filter=all&page=1&limit=20
  → BFF proxy: frontend/src/app/api/inbox/route.ts
  → GET http://127.0.0.1:8000/inbox?... (pass-through)
  → spine_api/server.py: get_inbox()
  → TripStore.list_trips(status=INBOX_STATUSES)
  → InboxProjectionService.project_all(raw_trips)
  → InboxProjectionService._project_one() for each trip
    → computes SLA days → slaStatus
    → reads analytics, validation, decision
    → computes priority and priorityScore
  → apply_filter → apply_search → apply_multi_filters → apply_sort → paginate
  → InboxResponse { items: InboxTripItem[], total, hasMore, filterCounts }
  → BFF returns as-is to frontend
  → TripCard receives { trip } with pre-computed priority
  → Renders PRORITY_BAR[priority] as 3px left colored bar
```

---

## 4. Current Model: What It Actually Does

### 4.1 The Formula

```
priority = "medium"
priorityScore = 50

IF (sla_status == "at_risk"
    OR analytics.requires_review == True
    OR validation.is_valid == False
    OR confidence_score < threshold):
    priority = "high"
    priorityScore = 75

IF (sla_status == "breached"
    OR analytics.escalation_severity == "critical"):
    priority = "critical"
    priorityScore = 90
```

Input signals:
| Signal | Source field | Values |
|--------|-------------|--------|
| sla_status | Computed from days in stage | on_track (<=4d), at_risk (5-7d), breached (>7d) |
| requires_review | analytics.requires_review | boolean |
| is_valid | validation.is_valid or validation.isValid | boolean |
| confidence | decision.confidence_score | integer (BE expects 0-100, FE expects 0-1) |
| escalation_severity | analytics.escalation_severity | "high" or "critical" |

Default score table:
| Label | Score |
|-------|-------|
| low | 25 |
| medium | 50 |
| high | 75 |
| critical | 90 |

### 4.2 What This Model Cannot Do

Every input feeds into a single 1D axis. The model has no concept of "importance" independent of "urgency."

Counterexamples:

| Trip | SLA | Value | Customer | What the model says | What it should say |
|------|-----|-------|----------|-------------------|--------------------|
| $50k VIP trip, 3 days in stage | on_track | $50,000 | VIP | medium (50) | high or critical (important) |
| $500 cold lead, 3 days in stage | on_track | $500 | New | medium (50) | medium or low |
| $50k VIP trip, 6 days in stage | at_risk | $50,000 | VIP | high (75) | critical |
| $500 cold lead, 6 days in stage | at_risk | $500 | New | high (75) | high or medium |
| $50k VIP trip, 8 days in stage | breached | $50,000 | VIP | critical (90) | critical |
| $500 cold lead, 8 days in stage | breached | $500 | New | critical (90) | high (shouldn't crowd out real criticals) |

The model treats rows 1+2 identically, rows 3+4 identically, and rows 5+6 identically. It literally cannot distinguish a high-stakes deal from a low-stakes inquiry.

---

## 5. Bugs and Anti-Patterns Discovered

### Bug 1: `low` priority is unreachable

Location: `inbox_projection.py:365` — `priority = "medium"`

Every trip starts at "medium." The only direction is up. No code path ever sets `priority = "low"`. The score table defines `low: 25` in `_DEFAULT_PRIORITY_SCORE:61-66`, making it dead code. A trip with 1 day in stage, no review needed, valid validation, high confidence, and no escalation is `medium (50)` forever — it never drops to `low (25)`.

Impact: The 4-tier priority UI (low/medium/high/critical) is effectively 3-tier. Filters and sorting that include "low" always return empty.

### Bug 2: Frontend/backend confidence score scale mismatch

Location: `inbox_projection.py:371` vs `bff-trip-adapters.ts:541`

| Side | Code | Scale |
|------|------|-------|
| Backend | `_as_int(decision.get("confidence_score"), 0) < 50` | Assumes 0-100 |
| Frontend | `confidence < 0.5` | Assumes 0-1 |

These are semantically the same boundary (50% of scale) ONLY if the stored value at the backend is 0-100. If the stored value is actually 0-1, the backend would treat `0.6` (60% confidence) as `< 50` and incorrectly escalate the trip to `high` priority.

Root cause: No type system enforces the scale. The field is `Any` or `int` in both places with no documented range.

### Bug 3: Duplicated priority computation

Two independent implementations of the same logic exist:

| Location | Lines | Status |
|----------|-------|--------|
| `spine_api/services/inbox_projection.py` | 364-377 | **Canonical** — used by GET /inbox |
| `frontend/src/lib/bff-trip-adapters.ts` | 529-543 | **Legacy** — used by /api/trips POST (old endpoint) |

Any change to the priority formula must be applied in both places or they will diverge. The BFF route for inbox (`frontend/src/app/api/inbox/route.ts`) is a pure pass-through so it doesn't need updating, but the `bff-trip-adapters.ts` code is still exported and could be called from other paths.

### Anti-pattern 1: Left-border accent bars everywhere

The `.impeccable.md` design system (Rule #4) bans `border-left` stripes. Four locations in the codebase violate this:

| Location | Lines | Element | What it does |
|----------|-------|---------|-------------|
| `TripCard.tsx` | 336-341 | Inline `<div>` 3px left bar | Priority indicator (colored by `PRIORITY_BAR`) |
| `Shell.tsx` | 201-207 | Inline `<span>` 2px left bar | Active nav item indicator |
| `overview/page.tsx` | 130, 242 | `borderLeft: 3px solid var(--accent-red)` | Error card marker |
| `workbench.module.css` | 586 | `border-left: 3px solid var(--color-primary)` | Review note marker |

The TripCard one is the most problematic: it's the exact same purpose as the deleted `CardAccent` component, just inlined with a div hack instead of a CSS border. The deletion of the component made the situation worse — now there's no single source of truth for the pattern.

Anti-pattern classification of the TripCard bar:
- Color-only indicator: fails WCAG (no shape, no text)
- `aria-hidden="true"`: hides from screen readers entirely
- Absolute positioning: fragile to layout changes, no CSS isolation
- Inline style: cannot be themed or overridden

### Anti-pattern 2: Inline mouse handlers in TripCard

| Lines | Code | Problem |
|-------|------|---------|
| 327-334 | `onMouseEnter/onMouseLeave` with direct DOM manipulation | Bypasses the Card component's variant system and CSS transitions. Duplicates hover logic already handled by CSS `:hover` |

---

## 6. External Research: Design Systems

### 6.1 IBM Carbon Design System — Status Indicator Pattern

**Source:** https://carbondesignsystem.com/patterns/status-indicator-pattern/
**Relevance:** Enterprise design system used by 100+ IBM products. Defines canonical patterns for status/priority communication.

**Key findings:**

Carbon defines five indicator variants:

| Variant | When to use | Elements |
|---------|------------|----------|
| Icon indicator | Ample space, maximum attention needed | Icon + shape + color + text label |
| **Shape indicator** | **Smaller spaces, scanning large datasets** | **Shape + color + text label** |
| Badge indicator (numbered) | Count of new/updated items | Number + color |
| Badge indicator (unnumbered) | New/updated items, count irrelevant | Dot + color |
| Differential indicator | Monitoring deltas in statistics | Arrow/caret + optional color + label |

**For our use case:** Shape indicators are the right pattern. Carbon explicitly says they help "prioritize tasks, like a red triangle for high-priority tasks" and "show the current phase of a component's lifecycle."

**WCAG compliance:** At least two of {color, shape, symbol, text} must be present. Carbon's recommendation: shape + color + text label. Shape-only is insufficient. Color-only is insufficient. The current left-bar accent uses color-only with `aria-hidden="true"` — it violates both WCAG and the Carbon pattern.

**Standard shapes and their meanings:**

| Shape | Meaning |
|-------|---------|
| Circle | Neutral/standard — most recognizable |
| Square | Structure/order |
| Diamond | Priority/importance |
| Triangle (up) | Caution/warning |
| Triangle (down) | Yield/decrease |

**Standard severity colors:**

| Color | Meaning |
|-------|---------|
| Red (#da1e28) | Error, critical, failed, requires immediate attention |
| Orange (#ff832b) | Warning, serious, medium severity |
| Yellow (#f1c21b) | Caution, minor warning |
| Green (#24A148) | Success, stable, normal |
| Blue (#0043ce) | Informational, in progress, active |
| Gray (#6f6f6f) | Draft, not started, unknown |

**Cognitive load rule:** "Avoid using status indicators when no user action is required or when the status information isn't significant enough to highlight. Having more than five or six indicators can overwhelm users."

**Accessibility rule:** "Shape indicators rely solely on shapes and colors, which might not provide enough accessibility for screen readers and individuals with low color vision. Therefore, using outlines and pairing text with shape indicators is essential."

### 6.2 Nielsen Norman Group — Indicators, Validations, Notifications

**Source:** https://www.nngroup.com/articles/indicators-validations-notifications/
**Relevance:** World's leading UX research firm. Defines the taxonomy of status communication.

**Key findings:**

NN/G distinguishes three communication methods:

| Method | What it is | When to use |
|--------|-----------|------------|
| Indicator | Makes a page element stand out to signal something special | Conditional: appears/changes based on certain conditions |
| Validation | Error messages related to user input | User just did something that needs correction |
| Notification | Informational messages about system occurrences | Event that may be of interest, not directly tied to user action |

**Indicators are:**
- **Contextual** — associated with a UI element, shown in close proximity
- **Conditional** — not always present, appear or change depending on conditions
- **Passive** — do not require user action, used as a communication tool
- **"Take up space"** — each indicator has a visual cost. Only use when important enough.

**Priority/priority indicators:** NN/G classifies task priority as a valid use of contextual indicators. The key question: "Is this worth taking up space on the page to inform the user?"

**Methods ranked by effectiveness:**
1. Icons (most recognizable)
2. Typography (bold, color — must pair with shape or text)
3. Size/Animation (less common, harder to standardize)

**Our current approach fails the NN/G test:** The accent bar is always present (not conditional), color-only (not paired with shape or text), and uses the weakest signal method.

---

## 7. External Research: Priority Models in Operations Software

### 7.1 ITIL/ITSM Ticket Priority Model

**Source:** ITIL v4 (IT Infrastructure Library), service management best practices
**Relevance:** Industry-standard model used by virtually every enterprise IT service desk. Battle-tested in high-volume ticket environments.

**Core model:**
```
Priority = f(Urgency, Impact)

Urgency = how quickly resolution is needed
  → SLA deadline proximity, time since creation, severity of impact on user
  → Typical levels: Critical (immediate), High (<4h), Medium (<24h), Low (<5d)

Impact = how much damage if unresolved
  → Number of users affected, revenue impact, security/compliance risk
  → Typical levels: Extensive/Widespread, Significant/Large, Moderate/Limited, Minor/Individual
```

**Standard 5x5 matrix → P1-P4:**

| Impact ↓ / Urgency → | Critical | High | Medium | Low |
|----------------------|----------|------|--------|-----|
| **Extensive** | P1 | P1 | P2 | P3 |
| **Significant** | P1 | P2 | P2 | P3 |
| **Moderate** | P2 | P2 | P3 | P4 |
| **Minor** | P3 | P3 | P4 | P4 |

**SLA breach risk as urgency multiplier:** Many ITIL implementations add breach probability to the urgency calculation. A ticket that will breach SLA in 2 hours gets higher urgency than one with 48 hours remaining, even if both currently have equal status.

**Automation patterns:**
- If priority X and unresolved for Y hours → auto-escalate to level above
- If priority X and assigned to absent agent → auto-reassign
- Priority overrides expire after N days (ticket re-evaluated on next cycle)

**Applicable to travel agency:** The ITIL model maps directly to our context:
- Urgency = departure proximity, follow-up promise date, SLA days
- Impact = trip revenue, client value, complexity risk
- The matrix provides a defensible, industry-standard framework for priority assignment

### 7.2 Zendesk/Freshdesk Service Desk Priority

**Source:** Zendesk admin documentation, Freshdesk help center
**Relevance:** Leading help desk software used by 160,000+ companies

**Zendesk approach:** No built-in scoring algorithm. Admins create trigger-based rules:
```
Trigger: ticket created AND custom_field.department = "Enterprise" AND custom_field.urgency = "High"
Action: set priority = urgent, set group = enterprise_support
```

**Freshdesk approach:** Explicit multi-factor priority:
- Factor 1: Issue type (account, technical, billing — each with default urgency)
- Factor 2: Customer tier (enterprise, premium, standard, free — maps to impact)
- Factor 3: SLA policy match (% of SLA consumed → urgency multiplier)
- Factor 4: Agent workload (agent capacity impacts auto-assignment, not priority)

**Key pattern:** Both tools let agents override the computed priority. The override is tracked. The system logs how often overrides happen.

---

## 8. External Research: CRM and Lead Scoring

### 8.1 Salesforce Lead Scoring

**Source:** Salesforce documentation, Trailhead, admin guides
**Relevance:** World's most used CRM. Processes millions of leads daily.

**Model: Fit + Interest + Engagement = Lead Score**

| Category | Signals | Example weights |
|----------|---------|----------------|
| Fit (demographic) | Title, company size, industry, geography, budget | C-level +15, VP +10, Enterprise company +15 |
| Interest (behavioral) | Website visits, content downloads, form fills, event attendance | Visited pricing +25, Downloaded whitepaper +10, Attended webinar +15 |
| Engagement (recency) | Email opens, clicks, reply rate | Opened email +5, Clicked link +10 |
| Negative signals | Unsubscribed, bounced email, job seeker title, competitor domain | Competitor domain -50, Unsubscribed -100 |

**Scoring buckets:**
- Hot (80-100): immediate sales follow-up
- Warm (40-79): nurture sequence
- Cold (0-39): long-term marketing

**Recency decay:** Score decreases over time without engagement. A lead scored 80 two weeks ago with no activity might drop to 65.

**Pipeline priority:** Salesforce separates stage (deal probability) from priority (urgency to act). Priority in the pipeline view = deal amount x stage probability / days until close date. This is weighted expected revenue velocity.

### 8.2 HubSpot Lead Scoring

**Source:** HubSpot documentation, Breeze AI documentation
**Relevance:** Second-largest CRM. Uses ML-based predictive scoring.

**HubSpot approach:**
- Manual scoring: Admin assigns points to properties and behaviors
- Predictive scoring: ML model trained on historical conversion data finds patterns
- Negative scoring: Explicit disinterest signals reduce score
- Score decay: Without engagement, score decreases over time

**Breeze AI (2025+):** Agentic scoring that recalculates in real-time, suggests next actions. "This lead's score dropped because they haven't opened the last 3 emails. Suggestion: send a different subject line."

**Key insight for travel agency:** The separation of fit (demographic) from interest (behavioral) from engagement (recency) maps directly to importance (fit + interest signals) vs urgency (engagement recency + time pressure).

---

## 9. External Research: Travel Agency CRM Patterns

### 9.1 TravelJoy

**Source:** Nutshell CRM comparison, user forums, TravelJoy feature page
**Type:** All-in-one CRM for travel advisors

**Priority model:**
- Lead scoring module: scores leads by engagement recency + trip value
- Client timeline with status indicators (Inquiry → Hold → Booked → In Progress → Completed)
- Visual badges for trip urgency (approaching dates, outstanding payments)
- **No computed priority score** — agent must visually scan list

**Gap:** TravelJoy has all the data (trip value, client history, dates) but doesn't combine them into a priority number. Agents rely on manual scanning.

### 9.2 Travefy

**Source:** mTrip comparison article, Travefy feature page
**Type:** Itinerary builder + basic CRM

**Priority model:**
- Itinerary-focused, not pipeline-focused
- Task tracking within each trip: incomplete tasks highlighted
- Status labels: Inquiry → Hold → Booked → In Progress → Completed
- **No priority computation at all** — purely status-based

**Gap:** Status labels show "where" a trip is but not "how important" or "how urgent."

### 9.3 Tern

**Source:** Tern feature page, user reviews
**Type:** Workflow automation for travel advisors

**Priority model:**
- Automated triggers: "If departure within 30 days and balance unpaid, flag red"
- Lead source tracking with revenue attribution
- Task lists with auto-due-dates based on trip type
- **Rule-based flags, not computed priority**

**Gap:** Tern's rules are better than nothing but are binary (red/not red). No graduated urgency or importance.

### 9.4 TourPaq CRM

**Source:** TourPaq blog
**Type:** Travel agency operations + CRM

**Priority model:**
- Pipeline stages with standard CRM lead management
- Task and payment reminder automation
- **No priority scoring** — relies on stage-based filtering

### 9.5 White Space Identified

**None of the major travel agency CRM tools implements a computed priority score.** Every tool provides status labels, stage filters, and task lists — all requiring the agent to scan visually and decide what matters. No tool answers the question "what should I work on next?" with a computed, data-driven answer.

This is the competitive white space our 2D model fills. A purpose-built priority scoring system that combines urgency and importance into an actionable rank is not available in any travel-specific tool on the market.

---

## 10. External Research: Dashboard UX Patterns

### 10.1 Smashing Magazine — UX Strategies for Real-Time Dashboards

**Source:** https://www.smashingmagazine.com/2025/09/ux-strategies-real-time-dashboards/
**Author:** Karan Rawal, operations dashboard specialist
**Relevance:** Practical UX strategies for decision-making dashboards in fleet management, healthcare, and hospitality

**Core thesis:** "Real-time dashboards are decision assistants, not passive displays."

**Key findings:**

**Design strategy 1: Delta indicators and trend sparklines**
- Show changes at a glance with arrows and small line charts
- Green up arrow + sparkline = improvement trend (positive)
- Red down arrow + flat sparkline = decline or danger

**Design strategy 2: Micro-animations for change detection**
- Soft pulse around changing metrics signals activity without distraction
- Count-up transitions for value updates
- Smooth slide (<300ms) when lists reorder
- Fade-in for new items in a grid

**Design strategy 3: Modular cards with sortable grid**
- Cards arranged in sortable grid, filterable by severity/recency/relevance
- Collapsible sections for dense information
- Consistent spacing and alignment per card type
- Role-based personalization (different metrics per viewer role)

**Design strategy 4: Reliability signals**
- Data freshness indicator: sync status, last updated time, manual refresh
- Auto-retry with exponential backoff for connectivity failures
- Cached snapshots when real-time data is unavailable
- Skeleton UIs instead of spinners for loading states

**Common dashboard UX failures:**
- Overcrowded interfaces: too many metrics competing for attention
- Flat visual hierarchy: critical data not distinguishable from normal data
- No explanation of changes: numbers update instantly with no context
- Excessive refresh rates: constant motion creates cognitive strain

**Key recommendation for our context:**
- "The best dashboards balance speed with calmness and clarity"
- "Design should drive conclusions, not just display data"
- "Trust requires clear system logic" — show why something is flagged, not just that it is

### 10.2 Dashboard Design Patterns Research

**Source:** https://dashboarddesignpatterns.github.io/types.html
**Type:** Academic research from University of Edinburgh
**Relevance:** Systematic taxonomy of dashboard types and design patterns

**Two macro categories:**
- **Curated dashboards** — highly selective, author-driven storytelling, single clear goal
- **Data collection dashboards** — broad information, reader-driven exploration, multiple goals

**Our application is a curated dashboard:** The inbox is a single-purpose view (what to work on next?) with computed, not raw, data.

**Design patterns applicable to our priority system:**

| Pattern | Description | Status in our app |
|---------|-------------|-------------------|
| Numbers + Trend Arrows | Compact metric display | Missing — we show values without trends |
| Signature Charts | Simplified visualizations for at-a-glance | Missing — we could add priority trend sparklines |
| Parameterized pages | URL-linked filter states | Present — inbox filters serialize to URL |
| Grid/Table layout switch | Toggle between card grid and data table | Present — D-003 added this for workspace |
| Navigation + Personalization | Role-based views | Partial — view profiles exist but are basic |
| Metadata emphasis | Data source, update info, disclaimers | Missing — no freshness indicator on inbox data |

---

## 11. First-Principles Priority Framework

### 11.1 What Priority Actually Means

The operator's question is: **"What should I work on next?"**

This is not a single question. It decomposes into:

**Question 1:** Is there a timer counting down on this trip? → URGENCY
**Question 2:** Does this trip matter to the business? → IMPORTANCE
**Question 3:** Is this trip blocked on someone else? → DEPENDENCY (future phase)

The current model collapses all three into one score. The right model separates them.

### 11.2 The Eisenhower Framework Applied

The Eisenhower Matrix (Urgent × Important) maps four quadrants to four actions:

| | Urgent | Not Urgent |
|---|---|---|
| **Important** | **DO FIRST** (act now) | **SCHEDULE** (plan to work on) |
| **Not Important** | **DELEGATE** (get it done quickly) | **ELIMINATE** (ignore or drop) |

Applied to travel operations:

| | Urgent (breached SLA, departing soon, escalation) | Not Urgent (within SLA, long lead time) |
|---|---|---|
| **Important** (high value, VIP, complex) | **FOCUS IMMEDIATELY** — $50k VIP trip with breached SLA | **PLAN CAREFULLY** — $50k VIP trip 3 months out, everything in order |
| **Not Important** (low value, cold lead) | **QUICK FIX** — resolve the SLA breach, then delegate | **MONITOR** — check occasionally, may not convert |

The risk of the current model: "Plan Carefully" (Important, Not Urgent) trips get `medium` priority and are neglected. These are the most dangerous to lose — high-value clients whose trips are going smoothly and get forgotten until suddenly they're urgent and it's too late.

### 11.3 Why 2D, Not 3D or More

Additional dimensions exist (complexity, dependency, sentiment) but:
- Complexity is a component of importance (complex trips have higher business impact if mishandled)
- Dependency (blocked on someone) is a workflow signal, not a priority signal — blocked trips need nudging, not re-prioritization
- Sentiment (frustrated client) feeds into urgency (client-initiated contact signal)

A 2D model captures the essential decision with minimal cognitive overhead. Three or more dimensions dilute the signal and complicate the UI.

---

## 12. 2D Scoring Formulas

### 12.1 Design Principles

1. **No magic constants without justification** — every weight and threshold has a rationale
2. **Graceful degradation** — missing data produces reasonable defaults, never crashes
3. **Testable** — every scoring function takes explicit inputs that can be mocked
4. **Explainable** — operator can see WHY a trip got its priority (urgency and importance breakdown)
5. **Overridable** — operator can adjust a trip's urgency or importance and the override persists

### 12.2 Urgency Score (0-100)

**Definition of urgency:** Probability and severity of negative outcome if not acted on soon.

| Factor | Signal source | Weight | Scoring | Rationale |
|--------|--------------|--------|---------|-----------|
| SLA breach risk | `days_in_stage` vs SLA thresholds | **0.30** | breached=100, at_risk=60, on_track=0 | Direct measure of time pressure. Highest weight because SLA breach is the most objective urgency signal. |
| Departure proximity | `dateWindow` field → parse to approx date | **0.25** | ≤7d=100, 30d=60, 90d=30, 180d=0, TBD=50 | Trip that departs next week needs different handling than trip in 6 months. Unknown date defaults to 50 (neutral) — doesn't incorrectly penalize or reward. |
| Client recency | `days_in_stage` (time since last action) | **0.20** | 14d=100, 0d=0 | Long silence = client may be frustrated or lost. Linear interpolation. |
| Client initiated contact | status field, escalation | **0.15** | needs_followup=80, awaiting_customer_details=80, critical_escalation=100, no_signal=0 | Client reaching out or waiting on us = active urgency. |
| Past-due actions | decision.pending_actions with due dates | **0.10** | 33 points per past-due action, capped at 100 | Concrete backlog of unfinished work. Capped to prevent runaway scores. |

**Normal scenario (5 days in stage, departure in 60 days, no escalation):**
```
urgency = (0 * 0.30) + (33 * 0.25) + (36 * 0.20) + (0 * 0.15) + (0 * 0.10)
        = 0 + 8.25 + 7.2 + 0 + 0
        = 15 (rounded)
```
Label: LOW urgency

**Critical scenario (12 days in stage, departure in 3 days, needs followup, 2 past-due actions):**
```
urgency = (100 * 0.30) + (97 * 0.25) + (86 * 0.20) + (80 * 0.15) + (66 * 0.10)
        = 30 + 24.25 + 17.2 + 12 + 6.6
        = 90 (rounded)
```
Label: CRITICAL urgency

### 12.3 Importance Score (0-100)

**Definition of importance:** Business value this trip represents to the agency.

| Factor | Signal source | Weight | Scoring | Rationale |
|--------|--------------|--------|---------|-----------|
| Revenue | `value`/`budget` field | **0.35** | Linear 0-50k USD → 0-100 | Direct business impact. Capped at $50k because marginal importance of additional $ beyond $50k is diminishing and we want to reserve headroom. |
| Client tier | `trip_priorities`, owner signals | **0.25** | VIP/urgent=100, high=70, some=50, none=30 | Captures what the agent knows about the client that raw data doesn't show. |
| Trip complexity | Count of multi_city, flights, hotels, activities, visa flags | **0.15** | 20 points per component, capped at 100 | Complex trips demand more attention, have higher risk of errors, and typically represent more revenue. |
| Referral potential | `lead_source` field | **0.15** | referral=100, repeat=70, social=40, web=30, other=20, unknown=30 | Referrals and repeats have higher lifetime value and lower acquisition cost. |
| Repeat client | `lead_source` field | **0.10** | repeat keywords found=100, none=0 | Repeat clients have proven value and lower risk. Binary signal with weight given to capture the distinction sharply. |

**Normal scenario ($5k trip, no special signals, web lead):**
```
importance = (10 * 0.35) + (30 * 0.25) + (20 * 0.15) + (30 * 0.15) + (0 * 0.10)
            = 3.5 + 7.5 + 3 + 4.5 + 0
            = 19 (rounded)
```
Label: LOW importance

**High-importance scenario ($40k trip, VIP signals, referral, multi-city, flights, hotels, activities):**
```
importance = (80 * 0.35) + (100 * 0.25) + (80 * 0.15) + (100 * 0.15) + (0 * 0.10)
            = 28 + 25 + 12 + 15 + 0
            = 80
```
Label: HIGH importance

### 12.4 Combined Priority

**Priority label** (the badge shown on the card):

```
if urgency >= 80 or (urgency >= 60 and importance >= 60):
    return "critical"
if urgency >= 60 or (urgency >= 30 and importance >= 60):
    return "high"
if urgency >= 20 or importance >= 20:
    return "medium"
return "low"
```

Rationale:
- **CRITICAL**: Extreme urgency OR both urgency AND importance are high
- **HIGH**: Significant urgency OR important trip with some urgency pressure
- **MEDIUM**: Any meaningful signal in either dimension
- **LOW**: Both signals are negligible — this tier is now REACHABLE unlike the current model

**Priority score** (for sort key):

```
combined_score = round(urgency * 0.5 + importance * 0.5)
```

Equal weight on both dimensions. The combined score is used for ordering within the same priority label. For example, two "high" priority trips are sorted by combined_score descending to surface the higher-stakes one first.

---

## 13. Visual Indicator Design

### 13.1 Pattern Selection: Shape Indicator

Based on IBM Carbon's shape indicator pattern (Section 6.1), our priority indicator uses:

**For urgency:** Filled circle with color + optional label
- Red circle = critical urgency
- Amber circle = high urgency
- Blue circle = normal urgency
- Gray circle = low urgency
- Shape: circle (most recognizable geometric form)
- Accessible: color + shape + text label = 3 of 4 required elements

**For importance:** Outlined diamond with color + optional label
- Red diamond outline = critical importance
- Gold diamond outline = high importance
- Blue diamond outline = normal importance
- Gray diamond outline = low importance
- Shape: diamond (conventionally associated with value/premium)
- Accessible: color + shape + text label

**Combined display (dual-axis badge):**
```
  ● red   ◆ red   CRITICAL
  │urgency│importance│
  └─── Priority ────┘
```

Two separate visual cues for two separate dimensions. The operator learns to read urgency (left dot) and importance (right diamond) as separable signals.

### 13.2 Component Design

```tsx
type UrgencyLevel = 'critical' | 'high' | 'normal' | 'low';
type ImportanceLevel = 'critical' | 'high' | 'normal' | 'low';

interface PriorityIndicatorProps {
  urgency: UrgencyLevel;
  importance: ImportanceLevel;
  variant?: 'dual-badge' | 'dot-only' | 'compact';
  showLabels?: boolean;
  size?: 'sm' | 'md';
  className?: string;
}
```

Variants:
- **dual-badge** (default for inbox cards): both indicators with labels
- **dot-only** (for dense table rows): urgency dot only, with priority label
- **compact** (for tight spaces): combined colored tag with highest-priority signal

Color tokens (from `.impeccable.md` design system):
```
--accent-red: #f85149     (critical urgency, critical importance)
--accent-amber: #d29922   (high urgency, high importance)
--accent-blue: #58a6ff    (normal urgency, normal importance)
--accent-gray: #8b949e    (low urgency, low importance)
```

These are existing design tokens in the project — no new colors needed.

### 13.3 WCAG Compliance

| Requirement | How we meet it |
|------------|---------------|
| Non-text contrast (3:1 minimum) | All indicator colors pass 3:1 against dark background (#0d1117) |
| Not color-only | Shape (circle vs diamond) differentiates urgency from importance |
| Text label | Optional label shows "HIGH URGENCY", "KEY CLIENT" etc. |
| Screen reader | `role="status"` + `aria-label` on indicator, e.g. "High urgency, High importance" |
| Dark theme | All indicators designed for dark mode (`.impeccable.md` requires dark mode) |

---

## 14. Component Architecture

### 14.1 Component Placement

In the inbox `TripCard`, the priority indicator replaces the inline accent bar:

**Before (current):**
```tsx
<Card>                                   
  {/* Left accent bar — AI slop */}
  <div className="absolute left-0 top-0 bottom-0 w-[3px]" 
       style={{ background: accentColor }} aria-hidden="true" />
  <div className="p-4 pl-5">
    {/* rest of card content */}
  </div>
</Card>
```

**After (proposed):**
```tsx
<Card>
  <div className="p-4">
    {/* Priority indicator in card header */}
    <div className="flex items-center justify-between mb-2">
      <div className="flex items-center gap-2">
        <span className="text-[15px] font-semibold">{title}</span>
      </div>
      <PriorityIndicator 
        urgency={trip.urgency}
        importance={trip.importance}
        variant="dual-badge"
        size="sm"
      />
    </div>
    {/* rest of card content */}
  </div>
</Card>
```

The indicator moves to the card's content area (not an absolute-positioned overlay), becomes part of the visual hierarchy, and communicates both dimensions.

### 14.2 Inbox Card Redesign Summary

The TripCard currently has these priority-related elements:

| Element | Current approach | Proposed approach |
|---------|-----------------|-------------------|
| Priority indicator | 3px left bar, inline div, aria-hidden | `PriorityIndicator` component in header |
| SLA badge | Colored pill with % consumed | Keep — it communicates different info (time pressure vs combined priority) |
| Stage badge | Colored pill per pipeline stage | Keep |
| Assignment badge | Colored pill with agent name | Keep |
| Flag badges | Colored pills per flag type | Keep |
| Metrics row | Role-dependent metrics | Add urgency + importance to all view profiles |
| Micro-labels | Contextual labels for new users | Keep — add micro-labels for urgency/importance |

The redundant accent bar is removed. The `PRIORITY_BAR` constant (`TripCard.tsx:32-37`) is replaced by the shared color tokens in the `PriorityIndicator` component.

---

## 15. Implementation Plan

### Phase 1: Backend Scoring Engine (~1 day)

**Files created:**
- `spine_api/scoring/__init__.py` — urgency scoring, importance scoring, combined priority
- `tests/test_scoring_priority.py` — 20+ tests covering all scoring functions

**Files modified:**
- `spine_api/contract.py` — add `urgency: int`, `importance: int`, `priorityLabel: str` to `InboxTripItem`
- `spine_api/services/inbox_projection.py` — call `score_trip()` in `_project_one()`, add urgency/importance sort keys, add urgency/importance multi-filters
- `spine_api/server.py` — accept urgency/importance query params in `/inbox` endpoint

**Feature flag:** `USE_2D_PRIORITY` env var. If false, use old 1D model.

### Phase 2: Frontend Types + BFF (~0.5 day)

**Files modified:**
- `frontend/src/types/governance.ts` — add urgency, importance to InboxTrip
- `frontend/src/types/generated/spine-api.ts` — regenerate from contract
- `frontend/src/lib/inbox-helpers.ts` — add urgency, importance sort keys, filter serialization
- `frontend/src/components/inbox/ComposableFilterBar.tsx` — add urgency, importance filter groups

### Phase 3: PriorityIndicator Component (~1 day)

**Files created:**
- `frontend/src/components/ui/PriorityIndicator.tsx` — reusable component
- `frontend/src/components/ui/__tests__/PriorityIndicator.test.tsx` — visual + accessibility tests

**Files modified:**
- `frontend/src/components/inbox/TripCard.tsx` — replace inline accent bar with PriorityIndicator
- `frontend/src/app/(agency)/inbox/page.tsx` — integrate urgency/importance in sort and filter UI

### Phase 4: Cleanup + Polish (~0.5 day)

**Files modified:**
- `Docs/DIRECTIVE_INBOX_INTELLIGENCE_LAYER_V2.md` — remove stale CardAccent references
- `frontend/src/lib/inbox-helpers.ts` — add try/catch to localStorage calls
- `.env.example` — document `USE_2D_PRIORITY` and `DISABLE_CALL_CAPTURE`

---

## 16. Operational Safety

### 16.1 Kill Switch

**Env var:** `USE_2D_PRIORITY=true|false`

When `false`:
- Backend uses old 1D formula in `_project_one()`
- `urgency` and `importance` fields are populated but `priority` and `priorityScore` use old computation
- Frontend PriorityIndicator component gracefully falls back to showing only the old priority label

### 16.2 Rollback Path

- Set `USE_2D_PRIORITY=false` → instant reversion to 1D model
- All new fields (urgency, importance, urgencyBreakdown, importanceBreakdown) are additive — the old `priority` and `priorityScore` fields persist unchanged
- No database migration needed — all fields are computed at projection time from existing data

### 16.3 Agent Override

- Operator can override urgency and/or importance on any trip
- Override is stored with timestamp and agent ID
- Override decays after one SLA cycle (7 days) — if the trip hasn't been worked, the override expires and scoring reverts to computed
- Override history is logged for audit

### 16.4 Monitoring

- Log the distribution of urgency and importance scores across all trips (histogram)
- Alert if >50% of trips are in the same priority label (model too flat)
- Alert if no trips hit "low" priority (model too narrow, same bug as current)

---

## 17. Appendices

### Appendix A: Current Codebase Bug Register

| ID | Bug | Location | Severity | Fix in this design |
|----|-----|----------|----------|-------------------|
| B1 | `low` priority unreachable | `inbox_projection.py:365` | Medium | 2D model properly reaches "low" when both urgency and importance are minimal |
| B2 | FE/BE confidence scale mismatch | `inbox_projection.py:371` vs `bff-trip-adapters.ts:541` | High | 2D model removes the confidence_score direct check; replaces with derived urgency components |
| B3 | Duplicated computation | FE + BE | Medium | Single source of truth in `spine_api/scoring/` |
| B4 | Left-bar AI slop x4 | Multiple files | Low | Replaced with `PriorityIndicator` component |
| B5 | Inline mouse handlers | `TripCard.tsx:327-334` | Low | Remove; CSS hover handles this |
| B6 | DISABLE_CALL_CAPTURE undocumented | Not in `.env.example` | Low | Document in `.env.example` |
| B7 | `localStorage` missing try/catch | `inbox-helpers.ts:284-300,370-380` | Medium | Add try/catch wrappers |

### Appendix B: Files Touched by This Design

| File | Phase | Change |
|------|-------|--------|
| `spine_api/scoring/__init__.py` | 1 | NEW — scoring engine |
| `tests/test_scoring_priority.py` | 1 | NEW — 20+ tests |
| `spine_api/contract.py` | 1 | MODIFY — InboxTripItem fields |
| `spine_api/services/inbox_projection.py` | 1 | MODIFY — integrate scoring, sort, filter |
| `spine_api/server.py` | 1 | MODIFY — query params |
| `frontend/src/types/governance.ts` | 2 | MODIFY — InboxTrip fields |
| `frontend/src/types/generated/spine-api.ts` | 2 | REGENERATE |
| `frontend/src/lib/inbox-helpers.ts` | 2 | MODIFY — sort keys, filters |
| `frontend/src/components/inbox/ComposableFilterBar.tsx` | 2 | MODIFY — filter groups |
| `frontend/src/components/ui/PriorityIndicator.tsx` | 3 | NEW |
| `frontend/src/components/ui/__tests__/PriorityIndicator.test.tsx` | 3 | NEW |
| `frontend/src/components/inbox/TripCard.tsx` | 3 | MODIFY — remove accent bar |
| `frontend/src/app/(agency)/inbox/page.tsx` | 3 | MODIFY — integrate |
| `Docs/DIRECTIVE_INBOX_INTELLIGENCE_LAYER_V2.md` | 4 | MODIFY — remove CardAccent refs |
| `frontend/src/lib/inbox-helpers.ts` | 4 | MODIFY — localStorage try/catch |
| `.env.example` | 4 | MODIFY — document env vars |
| `Docs/EXPLORATION_TOPICS.md` | 4 | MODIFY — add research topic |

### Appendix C: All Research Sources

| Source | URL | What it contributed |
|--------|-----|-------------------|
| IBM Carbon Status Indicators | https://carbondesignsystem.com/patterns/status-indicator-pattern/ | Shape + color + label pattern. WCAG rules. Severity levels. |
| NN/G Indicators | https://www.nngroup.com/articles/indicators-validations-notifications/ | Conditional indicators. Contextual. Passive. Space cost. |
| Smashing Magazine Dashboards | https://www.smashingmagazine.com/2025/09/ux-strategies-real-time-dashboards/ | Delta indicators. Sparklines. Micro-animations. Data freshness. |
| Dashboard Design Patterns | https://dashboarddesignpatterns.github.io/types.html | Dashboard taxonomy. Curated vs data collection patterns. |
| ITIL/ITSM Priority Model | ITIL v4 standard literature | 5x5 urgency x impact matrix. SLA breach probability. |
| Zendesk Priority Model | Zendesk admin docs | Trigger-based priority rules. Agent override logging. |
| Salesforce Lead Scoring | Salesforce Trailhead docs | Fit + interest + engagement model. Recency decay. |
| HubSpot Lead Scoring | HubSpot documentation, Breeze AI docs | Predictive scoring. Negative scoring. Decay. |
| TravelJoy CRM | Nutshell/blog reviews | Lead scoring module. Visual badges. No computed priority. |
| Travefy | mTrip comparison | Status labels. Task tracking. No priority computation. |
| Tern | Tern feature page | Automated triggers. Rule-based flags. No computed priority. |
| TourPaq | TourPaq blog | Pipeline stages. No priority scoring. |
| `.impeccable.md` | Project root | Dark mode. Accent color tokens. Border-left stripe ban. |
| Current codebase | `spine_api/`, `frontend/src/` | Full priority code path map (Section 3). |

### Appendix D: Companion Documents

| Document | Path | Purpose |
|----------|------|---------|
| Priority Signal Model Analysis | `Docs/PRIORITY_SIGNAL_MODEL_ANALYSIS_2026-05-08.md` | First-principles analysis of current model |
| Random Document Audit | (this session's audit) | Trigger for this work — D-001/D-003 audit |
| Exploration Topics | `Docs/EXPLORATION_TOPICS.md` | Research topic registry (update pending) |

### Appendix E: Decisions Log

| Decision | Options considered | Chosen | Rationale |
|----------|-------------------|--------|-----------|
| Model dimensionality | 1D, 2D, 3D+ | 2D | Captures essential tradeoff without diluting signal |
| Indicator pattern | Left bar, badge, dot, shape indicator | Shape indicator | WCAG compliant. IBM Carbon standard. Not AI slop. |
| Urgency scoring method | Ordinal buckets, continuous score | Continuous 0-100 | Graduated urgency captures nuance. Buckets lose information. |
| Importance scoring method | Revenue-only, multi-factor | Multi-factor weighted | Revenue alone misses client quality, relationships, complexity. |
| Urgency x importance combination | Multiplication, weighted sum, rule-based | Rule-based priority labels + weighted sum for sort | Labels = clear decision. Combined score = fine-grained ordering. |
| Override approach | Permanent, decaying, none | Decaying (7d) | Permanent overrides stale. No overrides ignores agent knowledge. |
| Kill switch | None, env var, feature flag | `USE_2D_PRIORITY` env var | Instant rollback. No deploy needed. |
| Component scope | Inline in each use, one shared component | One shared `PriorityIndicator` | Single source of truth. Consistent colors and shapes. |
