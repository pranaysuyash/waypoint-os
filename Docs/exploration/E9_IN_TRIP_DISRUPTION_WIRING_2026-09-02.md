# E-9 Exploration — IN_TRIP / Disruption Wiring (v2, code-verified)

**Date:** 2026-09-02 (rewritten 2026-09-04 after full-code verification pass; supersedes the v1 compact draft in place)
**Candidate:** E-9 (P3, 24-mo horizon).
**Question:** What input signal should flip a trip into IN_TRIP, what does IN_TRIP unlock, and what is the smallest *honest* wiring given there are no live booking rails?
**Evidence convention (per E-11):** **[VERIFIED]** = read directly from code in this repo on 2026-09-04. **[INFERRED]** = reasoned conclusion from verified facts.
**v1 corrections found by this pass:** (1) the packet does NOT carry `start_date`/`duration_nights` as v1 claimed — the canonical facts are `date_start`/`date_end`/`date_window` under `trip["extracted"]`, and their presence is not guaranteed; (2) feedback's "48h auto-trigger" is docstring fiction — nothing fires it; (3) `in_trip` already exists as a *declared but dormant* frontend lifecycle state.

---

## 1. Current machinery inventory (with honesty labels)

### 1.1 Disruption radar — `spine_api/routers/disruption_radar.py` [VERIFIED, read in full]

Header docstring: "no connected flight or booking provider... returns deterministic previews and refuses to mutate booking state." Three endpoints, all under `/api/v1/disruptions`:

| Endpoint | Input | What it actually does |
|---|---|---|
| `GET /alerts` | `X-Agency-ID` header only | Loops **every trip in the agency**. For each: replays stored `trip["active_disruption"]` if present, else **fabricates** a simulated alert (`dis_{trip_id[:8]}`, type CANCELLED, urgency CRITICAL, delay 240min, flight "BA178" default from `packet.get("flight_number")`). **No date check, no scoping** — a dateless discovery-stage trip gets the same "your flight is cancelled" alert as anything else (:82-108). |
| `GET /{trip_id}/rebook-options` | path trip_id + header | Already trip-scoped. Returns **two hardcoded options** (BA182 now+3h, VS020 now+6h, price deltas $0/$150) with `TierMetadata.missing_for_upgrade = ["connected flight provider", "fresh availability", "fare quote", "booking reference"]` (:124-166). |
| `POST /{trip_id}/rebook` | `ReBookRequest{trip_id, disruption_id, chosen_option_id, advisor_note}` | Calls `assert_tier_capability(DETERMINISTIC_PREVIEW, "can_mutate_booking_state")` which **always raises** (capability not in the DETERMINISTIC_PREVIEW grant map, `spine_api/core/reality_tier.py:60-67`). The response below the raise is defensively unreachable. (:169-203) |

Every response model carries `reality_tier = DETERMINISTIC_PREVIEW` + `provider_connected = False` (:31,45,65,104).

**Concrete meaning of "trip-scoped scan":** today `GET /alerts` is an unprompted global feed that simulates a disruption for *all* trips. A scope param would (a) filter the loop to trips whose window contains `now`, and (b) stop fabricating alerts for out-of-window/dateless trips. Nothing about the preview tier changes. [VERIFIED mechanics; INFERRED design]

### 1.2 Crisis ops — `spine_api/routers/crisis_ops.py` [VERIFIED, read in full]

Five endpoints, all under `/api/v1/crisis`, all `PREVIEW_ONLY` with a shared `_preview_metadata()` contract (line 25-57): `reality_tier: deterministic_preview`, `simulation: true`, `provider_connected: false`, `external_action: false`, `operational_write: false`, plus `TierMetadata.missing_for_upgrade`. Preview IDs are visibly non-operational: `PREVIEW-DRV-{sha256[:10]}` (:60-63).

| Endpoint | Input | Trip-awareness today |
|---|---|---|
| `POST /incidents/declare` | `GeofenceAlertRequest{incident_id, headline, severity, lat/lng/radius_km/country/region}` (defaults: Tokyo 35.6762/139.6503, 150km, JP) | **`affected_trips=[]` hardcoded** — comment: "No trip or passenger registry is connected to this preview route" (:129-130). Sets `evidence_status = "UNVERIFIED_LOCAL_INPUT"` (:136). |
| `POST /evacuation/plan` | `EvacuationPlanRequest{incident_id, trip_id, passengers: List[str], current_location, safe_destination="LHR", severity}` | Takes a `trip_id` but **passengers are caller-supplied strings**, never resolved from any registry (:77-84, :163). All legs get `carrier="UNVERIFIED_PROVIDER_PREVIEW"`, `status="PREVIEW_ONLY"`; `is_charter_confirmed=False` (:180-182). |
| `POST /ground/dispatch` | `{passenger_name, pickup/dropoff, vehicle_type}` | `emergency_contact_notified=False`, `notification_status="NOT_SENT"` (:207-220). |
| `POST /beacon/check-in` | `{trip_id, passenger_name, status, gps, battery}` | `check_in_recorded=False`, `duty_of_care_acknowledged=False`, nothing persisted (:238-251). |
| `POST /consular/step-manifest` | `{incident_id, country, affected_passengers[]}` | `DRAFT_NOT_TRANSMITTED`, `submission_status="NOT_SUBMITTED"` (:275-287). |

**Concrete trip-scoped change:** `incidents/declare` could intersect the geofence against in-window trips' destinations, and `evacuation/plan` could resolve `passengers` from the trip record instead of trusting the payload. Both are exactly the "durable trip record / trip-passenger registry" items already listed in `missing_for_upgrade`. Still preview-tier throughout. [INFERRED design, grounded on verified missing_for_upgrade entries]

### 1.3 Journey disruption model

`src/schemas/journey_graph.py` — transfer minimums, disruption propagation across legs. Real *domain model* feeding the preview surfaces; no live data source. [VERIFIED existence; consistent with v1]

### 1.4 The `in_trip` state itself already exists — declared but dormant [VERIFIED]

`frontend/src/lib/trip-lifecycle.ts` — `TripLifecycleState` includes `"in_trip"` in the blueprint lifecycle (`intake → … → booked_side → in_trip → completed`), and the docstring says it explicitly: *"in_trip is declared but has no input signal yet (no disruption/crisis field feeds it today) — documented dormant."* No branch of `deriveTripLifecycle` (:114-160) ever assigns it. Labels and next-actions for `in_trip` ("Monitor disruptions") already exist.

Backend alignment: `spine_api/services/trip_lifecycle_service.py:19` — `VALID_STAGES = {"discovery", "shortlist", "proposal", "booking"}` — `in_trip` is **not** a stage; `spine_api/core/trip_status.py` is a *normalizer* for freeform statuses (never a strict enum, never bricks on unknown values). So a persisted `in_trip` flip would need a new producer, a validator, and a stage-vocabulary migration; a derived read-model flip needs none of these. [VERIFIED]

---

## 2. "Trip started" data — exact field inventory [VERIFIED]

### 2.1 What does NOT exist (v1 claim, now confirmed with precision)

- **`spine_api/models/trips.py` (Trip SQLAlchemy model):** no `start_date`, `departure`, `starts_at`, `end_date`, `return_date`, or `duration_nights` column. The only date-ish columns are intake metadata: `follow_up_due_date`, `date_flexibility` (string), `date_year_confidence` (string). Travel facts live in JSON columns: `extracted` (canonical packet), `validation`, `decision`, `strategy`, `booking_data`, `pending_booking_data`.
- **`spine_api/contract.py`:** no trip-level ISO departure anchor. Closest fields: `date_window: Optional[str]` (free-text, alias `dateWindow`, :1038), `date_flexibility`, `date_year_confidence`, `follow_up_due_date`. `rg` for `start_date|departure|duration_nights` returns nothing.

### 2.2 What DOES exist — the canonical packet date facts [VERIFIED]

`spine_api/persistence.py:_build_processed_trip` writes the extraction output as `"extracted": packet` (:2157). `src/intake/extractors.py` (`_extract_dates`, :1180; writer block :2490-2520) produces:

| Slot | Value | Confidence | Notes |
|---|---|---|---|
| `date_window` | raw phrase ("June-July 2026", "March or April") | 0.8 | Always the canonical fact; "no ISO ends are extracted" for window-shaped phrases (comment :259-260) |
| `date_start` | ISO `YYYY-MM-DD` | 0.95 | Only when the phrase parses to a start: month+day ranges, day ranges ("9th to 14th Feb" → "tentative"), "after July 10" → start-only, "flexible_after" |
| `date_end` | ISO `YYYY-MM-DD` | 0.95 | Only when the phrase parses to an end |
| `date_confidence` | `"tentative" \| "window" \| "flexible" \| "flexible_after"` | 0.9 | Quality label from the parse |
| `date_year_status` | year classification | 0.95 | `DERIVED_SIGNAL`, `extraction_mode="derived", maturity="verified"` |

**Critical caveat [VERIFIED via E-11 runtime check]:** E-11 §1.2 ran the production `ExtractionPipeline` on "around Oct 5" and control "Oct 5" — **no `date_*` slots were produced at all**. Absence is common, not exceptional: hedge phrasing and plain specific dates can both yield nothing. `resolve_trip_window` must treat "no window" as a first-class outcome.

**Existing consumers of these facts [VERIFIED]:**

- `spine_api/routers/social_inbound.py:141-143` — `start_date = facts["date_start"] ?? facts["date_window"]`, `end_date = facts["date_end"]`. **This is the in-repo precedent for `resolve_trip_window`.**
- `src/intake/normalizer.py:337` — `compute_urgency(date_end_str)` returns `{level: high|medium|low, days_until, confidence}` (past-date → high/0.9, ≤7d high, ≤21d medium, else low). The *return-date* urgency logic already exists; `in_trip` is its natural sibling (`days_until <= 0` is "in window" territory).
- `src/intake/decision.py:356-357` — `date_start`/`date_end` map to `date_conflict`; `strategy.py:244` — display order 7/8.
- E-11 L4 [VERIFIED]: `frontend/src/lib/bff-trip-adapters.ts:503` passes the whole `trip.extracted` through as `packet`, so `facts.date_start/date_end` already reach the frontend payload today.

### 2.3 The phantom `start_date` appearances (v1 was too coarse here) [VERIFIED]

`start_date`/`duration_nights` exist as *names* in four places, none of which is a producer:

1. **`spine_api/services/field_merge.py:60-79`** — `COMMERCIAL_FIELDS` includes `start_date`, `end_date`, `dates`, `duration_nights` (operator-corrected values outrank customer restatements). The merge layer *anticipates* these field names; the extractor never writes them under those names. This is a ready-made hook: an operator-corrected ISO start/end would flow through existing precedence (actor-based) and be attributable via `_field_provenance` (E-11 §1.1).
2. **`spine_api/persistence.py:1757-1760`** — `get_trip_for_public_access` *reads* `trip["packet"]["start_date"/"end_date"]`. That flat `trip["packet"]` shape is **legacy/parallel** — `_build_processed_trip` writes the canonical packet to `trip["extracted"]`, and no code path found constructs a flat `trip["packet"]` with `start_date`. Read-only consumer of a possibly-absent key.
3. **`spine_api/server.py:2543` / `spine_api/services/payment_queue_service.py:197`** — `start_date = trip.get("start_date") or booking_data.get("start_date")`: reads top-level/booking_data keys that nothing in the intake pipeline writes. Payment-queue rows will show `start_date=None` for intake-sourced trips unless data arrived out-of-band.
4. **`src/public_checker/live_checks.py:193,287`** — `start_date/end_date` here are *climate-API month windows* derived from the date phrase, not trip anchors.

### 2.4 Other candidate window sources — checked and mostly empty [VERIFIED]

- **`spine_api/services/confirmation_service.py`** — `ConfirmationSummary`/`ConfirmationDetail` carry only process timestamps (`recorded_at/verified_at/voided_at/created_at`), `supplier_name`, `confirmation_number`, and opaque `evidence_refs: list[dict]`. **No travel dates.** A verified confirmation proves *a booking exists*, not *when travel happens*; any window use would require reading dates out of evidence-ref payloads (unstructured today).
- **Quotes/proposals** — `src/intake/plan_candidate.py:91,258` carries `date_window: Optional[str]` (the same free-text phrase) into plan candidates; no ISO quote dates found in the proposal/quote layer.
- **`trip["booking_data"]`** — shape is not producer-defined anywhere in the intake pipeline; `payment_queue_service` reads `booking_data.get("start_date")` defensively. Treat as "may contain dates only when an out-of-band writer created it."

**Net:** the only *durable, pipeline-produced* window evidence today is `trip["extracted"].facts.{date_start, date_end, date_window, date_confidence}`. There is no trip-level departure anchor. [VERIFIED]

---

## 3. Signal design — derived vs persisted

| | Option (a): persisted mode flip | Option (b): derived window (recommended) |
|---|---|---|
| Producer | **None exists.** No ticketing, no boarding event, no check-in feed. A write would fabricate evidence. | `starts_at/ends_at` resolved from best available grade each read. |
| Validator discipline | Violates "name a state only when a validator exists for entering it." | Read-model projection; no new state to validate on write. |
| Backend fit | `in_trip` is not in `VALID_STAGES`; `trip_status.py` is a normalizer — a new status needs migration + transition rules. | Zero backend state change; `resolve_trip_window(trip)` + one contract field. |
| Frontend fit | `deriveTripLifecycle` already declares dormant `in_trip` — a persisted flip arrives as an unfamiliar status value. | `deriveTripLifecycle` consumes the window exactly as designed; dormant state wakes up. |
| Failure mode | Stale flip: trip stays `in_trip` forever after return (no exit producer either). | Window arithmetic can be recomputed/repaired anytime. |
| Reversibility | State writes need cleanup migrations. | Basis re-grades (extracted → verified) are pure function changes. |

**Recommendation: (b), explicitly two-stage.** [INFERRED, grounded on verified §1.4 constraints]

- **Stage 1 (now):** backend `resolve_trip_window(trip) -> TripWindow(starts_at|None, ends_at|None, basis, phrase)` following the `social_inbound.py:141` precedent (`date_start ?? date_window`); expose `trip_window` + `in_trip` + `in_trip_basis` on the trip contract; `deriveTripLifecycle` flips `in_trip` when `starts_at ≤ now < ends_at`. Dateless trips are never in-window — honest by construction. The urgency ladder in `normalizer.compute_urgency` generalizes naturally (same arithmetic, past-date branch = in/after window).
- **Stage 2 (when rails/feeds exist):** basis upgrades to provider-verified (booking_data + confirmation `verified_at`); only then may consumers *act* on `in_trip` beyond display (§5 guardrails).

Note the frontend already receives `trip.extracted` (E-11 L4), so a client-side-only prototype is possible — but the canonical resolution must be a backend contract field per the repo's contract-driven verification rule, so all consumers (radar scope, feedback trigger, crisis geofence intersect) share one definition. [INFERRED]

---

## 4. Evidence-grade ladder for the window (aligned to E-11 vocabulary)

E-11 establishes the trust vocabulary: packet-layer `EpistemicStatus = FACT | INFERRED | ASSUMED | UNKNOWN` (canonical), arbiter's divergent enum pending unification (E-11 Decision 3), and warns (F-22) that `explicit_user` authority is currently stamped `FACT` too eagerly. Grade the window basis against that ladder:

| Grade | Source (exact path) | Exists today? | Epistemic mapping |
|---|---|---|---|
| **G0 none** | no `date_*` slots (dateless trips; also the E-11 extraction gap for "around Oct 5"-class phrases) | ✅ common | `UNKNOWN` — never in-window |
| **G1 phrase** | `extracted.facts.date_window` only, no ISO ends ("June-July", "March") | ✅ | Display-only fuzzy window; cannot compute the boolean without inventing ends. Basis `extracted_phrase`. |
| **G2 extracted ISO** | `extracted.facts.date_start` / `date_end` (conf 0.95, label "tentative") | ✅ | Extracted by NLP → `INFERRED` at best. Caveat: today's authority mapping would stamp `explicit_user`→`FACT` (F-22) — **do not let the window badge inherit that laundering**; grade from the extraction mode/label ("tentative"), not the default mapping. |
| **G3 corrected** | operator/customer-corrected `start_date`/`end_date` via `field_merge.COMMERCIAL_FIELDS` + `_field_provenance` | ⚠️ names reserved, no ISO producer yet | Verified-customer/verified-operator. Requires only: add ISO date fields to the operator-correct path (or map corrections onto `date_start`/`date_end` facts). Smallest upgrade path. |
| **G4 provider** | `booking_data` + `confirmation_service` `verified_at` | ❌ | Verified-provider. Today `booking_data` has no defined producer and confirmations carry no travel dates (§2.4). |

**Key implication:** Stage 1 ships G0-G2 (derived, display-only, basis-badged). G3 is the first *trust* upgrade and is small (merge layer already anticipates the names). G4 waits for rails (NG/EX-05). [VERIFIED availability; INFERRED grading]

---

## 5. What IN_TRIP unlocks (per consumer, with today's mechanics)

| Consumer | Unlock when in_trip | Gated on |
|---|---|---|
| Disruption radar | `GET /alerts` loop filters to in-window trips instead of fabricating an alert for every agency trip; optional `?trip_id=` single-trip scope. Alerts stay `DETERMINISTIC_PREVIEW`-badged. | G1/G2 basis is fine for *displaying* relevance; acting on alerts stays preview (`assert_tier_capability` seam already enforces). |
| Crisis ops | `incidents/declare` intersects geofence with in-window destinations (today: `affected_trips=[]` hardcoded); `evacuation/plan` resolves passengers from the trip record instead of trusting the payload (today: caller-supplied strings). | Both changes are exactly the verified `missing_for_upgrade` items ("trip/passenger registry", "durable trip record"). G2 display; escalation actions stay human. |
| Lifecycle read-model | Dormant `in_trip` state wakes up for dateful trips; operator console separates "pre-trip pipeline" from "guests currently traveling". | none — pure derivation |
| Urgency re-weighting | `normalizer.compute_urgency`'s `days_until ≤ 0` branch already encodes "past end date → high": an in-trip disruption outranks planning-stage regardless of lifecycle stage. Urgency is **orthogonal to lifecycle** — a score input, not a status. | Stage-1 (G2 basis) |
| Feedback loop (E-10) | See §6 — the "48h post-return" trigger currently has no anchor and no fire mechanism. | Stage-1; needs the sweep/invocation seam |

---

## 6. Feedback 48h trigger — what actually fires it today: **nothing** [VERIFIED]

`spine_api/routers/feedback.py` docstring claims "Auto-triggers client NPS feedback surveys 48 hours after trip return." Reality:

- **`POST /{trip_id}/trigger-survey`** — manual operator call only. Writes `trip["post_trip_feedback"] = {survey_id, status: "DISPATCHED", delivery_channel, dispatched_at}`, logs audit event `post_trip_feedback_triggered`, and returns `survey_url = https://feedback.waypointos.com/s/{survey_id}` — a **hardcoded external domain; nothing is sent anywhere**. `survey_id = srv_{trip_id[:8]}_{HHMMSS}` (minute+second only — collision-prone).
- **`GET /supplier-scorecard`** — 100% hardcoded static entries (Four Seasons 4.95/94-NPS, Belmond, A&K, Emirates; total 156, avg NPS 89). There is no feedback-submission store anywhere in `spine_api`; the scorecard's inputs do not exist.
- **No scheduler** references post-trip feedback anywhere. The only background loop is `spine_api/watchdog.py` `IntegrityWatchdog` (threading, 600s default, dashboard-SSOT drift only). `spine_api/notifications.py:489` explicitly notes delivery "should be called by a scheduler (e.g., APScheduler, Celery Beat)" — the seam is anticipated, not installed.

So the E-9 contribution is precise: **the trigger needs two things — a window-derived return date, and an invocation seam.** Return date = `ends_at` from `resolve_trip_window` (G2). Invocation candidates: extend watchdog-style background thread with a post-return sweep, or an operator-facing "due for survey" list derived on read (no scheduler, still honest). The v1 phrasing ("replacing the manual trigger-survey call") was right but understated: today the 48h logic is pure docstring fiction. [VERIFIED]

---

## 7. Honesty guardrails (binding)

1. `in_trip` derived from G2 *extracted* dates is an inference, not a fact — it must carry `in_trip_basis` and ride the E-11 epistemic labeling; **do not** let the default `explicit_user→FACT` mapping (F-22) grade the badge. Never gate money or duty-of-care actions until basis ≥ G3, hard-required at G4.
2. Radar/crisis responses keep `reality_tier` + `provider_connected` badges — IN_TRIP wiring adds **no** new simulation authority; the `assert_tier_capability` mutation seam stays.
3. No persistence of `in_trip` as a lifecycle *status* in this stage (it is not in `VALID_STAGES`; E-8 may record `in_trip_basis` history, not a state write).
4. Fabricated radar alerts (§1.1) must not become *trip-scoped* fabrications without keeping the badge — scoping changes *who* sees previews, never *what tier* they are.

---

## 8. Smallest honest slice (sized)

1. **E9.1 (S):** `resolve_trip_window(trip)` read-model helper — `extracted.facts.date_start/date_end` → `date_window` phrase fallback (`social_inbound.py:141` precedent); returns `(starts_at|None, ends_at|None, basis, phrase)`; grades G0-G2 per §4. Unit tests must include: dateless, phrase-only, start-only ("after July 10"), both-ISO, and the E-11 gap case (specific date phrase yielding nothing).
2. **E9.2 (S):** expose `trip_window`/`in_trip`/`in_trip_basis` on the trip contract (single canonical field set; extend existing response models — no new route), and wake the dormant `in_trip` branch in `deriveTripLifecycle` with basis on the chip tooltip. Verify against the real API shape per the API Contract Verification rule.
3. **E9.3 (M):** `GET /disruptions/alerts` accepts optional in-window scope (and/or `?trip_id=`); scoped mode stops fabricating alerts for out-of-window trips; badges unchanged.
4. **E9.4 (M):** feedback auto-trigger v1 — derive "due for survey" (`now ≥ ends_at + 48h`) from the window behind a read endpoint or watchdog-style sweep; keep the manual trigger; survey delivery stays out of scope until a sender exists (fix the hardcoded `feedback.waypointos.com` URL claim separately).

---

## Decision needed

1. **Ratify derived-window (b) over persisted mode flip (a)** — recommendation: yes; (a) has no producer, violates the validator discipline, and `in_trip` is deliberately absent from `VALID_STAGES`.
2. **Stage-1 display on extracted (G2) basis:** flip the `in_trip` chip with a visible basis badge, or hold the chip until G3? (Recommend: flip with badge — display is recoverable, and hiding the dormant state's only plausible input delays operator familiarity. But this interacts with F-22: the badge must grade from extraction mode, not the laundered default.)
3. **Feedback invocation seam:** on-read "due for survey" list (no scheduler, simplest honest) vs. watchdog-style background sweep (real automation, new thread surface)? Needed before E9.4; recommend on-read first, sweep when E-10's loop design lands.
4. **Radar scoping default:** keep today's unscoped fabricated feed for demo continuity, or make in-window scoping the default once the window exists? (Recommend: default in-window + explicit `?all=true` escape hatch — the current all-trips fabrication is the strongest dishonesty in the file.)
