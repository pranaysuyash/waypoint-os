# Data Capture Packet Namespacing — Discovery, Decision, and Implementation Plan

Date: 2026-04-29
Author/agent: Amp pair-programming session
Audited file: [Docs/research/DATA_CAPTURE_UI_UX_AUDIT_2026-04-27.md](DATA_CAPTURE_UI_UX_AUDIT_2026-04-27.md)
Trigger: User asked to revisit the 2026-04-27 data-capture audit and verify whether its P0/P1 capture-field claims still hold today.

## TL;DR

The 2026-04-27 audit asked for five new capture fields (`follow_up_due_date`, `pace_preference`, `lead_source`, `activity_provenance`, `date_year_confidence`) to be wired through the canonical spine. Between 2026-04-27 and 2026-04-29 the schema work shipped: contract, server envelope, extractor, persistence, BFF, frontend types, and UI all accept the fields. **But the pipeline does not consume four of them and only partially consumes the fifth.** The audit's "missing fields" diagnosis is stale; the corrected diagnosis is "fields are extracted and stored but several are dead-letter after packet ingestion."

The deeper problem that this discovery surfaced is **packet namespacing**: the five fields have heterogeneous semantics (operational SLA, traveler preference, CRM metadata, meta-information about other facts, extraction-confidence signal) but currently all live as flat siblings in `packet.facts`. That is acceptable as an ingestion bridge but wrong as a long-term canonical model.

Decision: **proceed with one safe end-to-end fix today (Option A — wire `pace_preference` into `SuitabilityContext`), document the corrected diagnosis, defer the other four field-consumer wirings until after a packet-shape migration to namespaced containers (`packet.facts` / `packet.lead_context` / `packet.provenance`).**

Doing all five field consumer wirings on the current flat `packet.facts` model would spread the wrong abstraction across composer, strategy, decision, and dashboards before the packet shape is correct. That is the trap.

## How this document relates to the audit

The 2026-04-27 audit is **not deleted, not rewritten, not superseded** per the AGENTS.md "Documentation Management" rule. It remains valid as the original product audit and UX direction. This document is an additive discovery layer that:

- corrects the "missing fields" diagnosis to "fields exist and are stored, but consumption is incomplete and namespacing is wrong",
- records the architectural review verdict on packet namespacing,
- specifies the smallest correct functional fix for today,
- defines the migration plan for the namespacing refactor,
- captures the decision rule for future capture fields,
- adds research/exploration items uncovered along the way.

A short correction stub is appended to the original audit pointing here.

## Evidence map (verified 2026-04-29)

### What the audit recommended

The 2026-04-27 audit at `Docs/research/DATA_CAPTURE_UI_UX_AUDIT_2026-04-27.md` (P0/P1 sections, lines 131–168) called out five missing structured fields: follow-up commitment, pace preference, lead/source provenance, party composition (already partially solved), date-year ambiguity, and activity provenance.

### What actually shipped between 2026-04-27 and 2026-04-29

Verified by direct grep across `spine_api/`, `src/`, `frontend/`, `tests/`, `Docs/`, `alembic/`:

| Layer | File / locator | Status |
|-------|----------------|--------|
| Spine contract | `spine_api/contract.py:96-112` (`SpineRunRequest`) | All 5 fields accepted with `Optional[str]` |
| Server envelope construction | `spine_api/server.py:516-558` (`build_envelopes`) | All 5 fields wrapped into one `SourceEnvelope.from_structured(extra_fields, "structured_import", "system")` envelope |
| Pipeline extractor | `src/intake/extractors.py:1318-1392` (`_extract_from_structured`) | All 5 fields mapped to `packet.facts[name]` via `packet.set_fact(...)` with `AuthorityLevel.IMPORTED_STRUCTURED` |
| Persistence model | `spine_api/models/trips.py:30-50` | All 5 fields have typed columns (DateTime, String, Text) |
| Persistence mapper | `spine_api/persistence.py:340-380, 524-549, 1027-1099` | All 5 fields stored, read, mapped on save/load |
| BFF route | `frontend/src/app/api/trips/route.ts:93-98` and `[id]/route.ts:51-56` (PATCHABLE_FIELDS) | All 5 fields accepted on POST and PATCH |
| Frontend types | `frontend/src/types/generated/spine-api.ts:229-233`, `frontend/src/lib/api-client.ts:421-426` | All 5 fields typed |
| Capture UI | `frontend/src/components/workspace/panels/CaptureCallPanel.tsx:71-76` | All 5 fields submitted |
| Frontend tests | `frontend/src/components/workspace/panels/__tests__/CaptureCallPanel.test.tsx` | 21 tests including dropdowns and submission round-trips |
| Backend tests | `tests/test_call_capture_phase2.py`, `tests/test_api_trips_post.py`, `tests/test_call_capture_e2e.py`, `tests/test_intake_pipeline_hardening.py:17,48` | Field acceptance, persistence, PATCH, extraction |

So the audit's P0/P1 "missing field" recommendations are no longer accurate. The fields are present.

### What is *not* yet wired — corrected gap analysis

A field can be "live" or "dead-letter" at three independent layers:

1. **Ingestion**: contract → envelope → extractor → `packet.facts`.
2. **Persistence**: stored on the trip record, returned by `GET`, mutable by `PATCH`.
3. **Pipeline consumption**: read by validation, decision, packet, strategy, composer, suitability, watchdog, or notifications during a run.

All five fields are live at layers 1 and 2. Layer 3 is where the corrected diagnosis lives:

| Field | Pipeline consumption today | Operational impact |
|-------|----------------------------|---------------------|
| `follow_up_due_date` | Partial. Read by `spine_api/notifications.py` for SLA queries and by snooze/extend endpoints. **No spine stage event consumes it.** | Operators see SLA breaches via the notification path, but the spine pipeline itself is unaware of follow-up commitments. |
| `pace_preference` | **Dead-letter.** `SuitabilityContext.pace_preference` exists at `src/suitability/models.py:74` but neither `SuitabilityContext()` construction site (`integration.py:159`, `integration.py:253`) wires `packet.facts["pace_preference"]` into it. | Ravi types "don't rush it," it lands in the packet, suitability scoring still ranks high-intensity activities the same way. The most operationally important capture field has no behavioral effect. |
| `lead_source` | **Dead-letter.** No code in `src/` reads `packet.facts["lead_source"]`. | Warm-referral signal stored but never used for prioritization, dashboards, or attribution. Lower priority for pipeline behavior, but stored value is at risk of leaking to traveler-facing output by virtue of sitting in `packet.facts`. |
| `activity_provenance` | Partial. Only the audit-report endpoint at `spine_api/server.py:2241-2250` reads it. **Composer/strategy/decision do not distinguish traveler-requested from agent-suggested activities.** | When Ravi notes "Universal Studios was my suggestion, not requested," the system later treats it identically to traveler-confirmed must-haves. This is exactly the failure the original audit's P1 finding warned about. |
| `date_year_confidence` | **Dead-letter.** No follow-up question generator, no UI confidence flag, no validation gate reads it. | The "Nov 2024 call → Jan/Feb 2025 inferred" trap from the original audit scenario is silently flattened. |

## The architectural question this surfaced

Is `packet.facts` the right home for these fields at all?

A trip-fact extractor that puts CRM metadata, operational SLAs, and meta-information about other facts into the same dict as `destination` and `party_size` is convenient but conceptually dirty. Concretely:

- `lead_source` ("warm referral via Divya, colleague of caller's wife") sits in `packet.facts` with the same authority level as `destination`. Any composer prompt, traveler-facing serializer, or audit export that iterates `packet.facts` is one mistake away from leaking referral details into traveler-visible output.
- `date_year_confidence` is metadata *about* `date_window`. Storing it as a sibling fact means every consumer must read both and keep them synchronized.
- `activity_provenance` is metadata *about* activities. Same issue.
- `follow_up_due_date` is operational metadata about the lead/run. The trip would be perfectly valid with this field null. It is not a trip property.
- `pace_preference` is the only one of the five that actually belongs near trip facts (it shapes itinerary generation), but it is also more nuanced than a primary fact — it can be traveler-stated, operator-assumed, or system-inferred.

## Architectural review verdict (2026-04-29)

The namespacing question was sent for external architectural review. The verdict received:

> The current all-in-`packet.facts` model is **acceptable as an ingestion bridge but architecturally wrong as the long-term canonical shape**. Move to namespaced containers before wiring further consumers. Do not implement all five downstream consumers on the current model — that spreads the wrong abstraction.

### Adopted target shape

```text
CanonicalPacket
├── facts                       # trip-shaping facts and preferences
│   ├── destination_candidates
│   ├── origin_city
│   ├── party_size
│   ├── party_composition
│   ├── child_ages
│   ├── budget_raw_text / budget_min / budget_max
│   ├── date_window
│   ├── traveler_constraints
│   └── pace_preference          # itinerary-affecting preference
│
├── lead_context                # internal CRM/operational metadata, never traveler-facing by default
│   ├── follow_up_due_date
│   ├── lead_source
│   ├── primary_contact
│   ├── referral_relationship
│   ├── call_date
│   ├── channel_origin
│   └── caller_consent_recorded
│
└── provenance                  # metadata about other facts; later promoted to slot-level
    ├── date_year_confidence    # later: metadata on date_window slot
    ├── activity_provenance     # later: metadata on activity slots
    ├── operator_assertions
    ├── system_inferences
    └── requires_traveler_confirmation
```

### Field-by-field placement (final)

| Field | Final home | Reason |
|-------|------------|--------|
| `pace_preference` | `packet.facts.pace_preference` (today's location is correct) | Affects itinerary and suitability scoring; legitimately a trip-shaping preference. |
| `follow_up_due_date` | `packet.lead_context.follow_up_due_date` | Operational SLA, not a trip property. |
| `lead_source` | `packet.lead_context.lead_source` | CRM/attribution; must not leak to traveler-facing output. |
| `activity_provenance` | `packet.provenance.activity_provenance` (today), later slot-level metadata on each activity | Modifies activity facts; not itself a primary fact. |
| `date_year_confidence` | `packet.provenance.date_year_confidence` (today), later metadata on `date_window` slot | Confidence about another fact; should not be a sibling. |

### Decision rule for future capture fields

A new capture field should ask itself, in order:

1. Does this describe the trip in a way the traveler would recognize? → `packet.facts`
2. Does this change itinerary generation or suitability? → `packet.facts` (or `packet.preferences` if we later split preferences out)
3. Is this about sales, CRM, SLA, channel, operator workflow, or compliance? → `packet.lead_context`
4. Is this about how we know something — source, confidence, or whether it needs confirmation? → `packet.provenance` now, slot-level metadata later
5. Could this be embarrassing, private, or irrelevant if shown to the traveler? → keep it outside `packet.facts`

Pre-classification of likely future fields:

| Future field | Home |
|--------------|------|
| `primary_contact` | `lead_context` |
| `referral_relationship` | `lead_context` |
| `call_date` | `lead_context` (or `capture_context` if introduced) |
| `channel_origin` | `lead_context` |
| `caller_consent_recorded` | `lead_context` (compliance) |
| `operator_notes` | `lead_context` (internal-only by default) |
| `traveler_constraints` | `facts` |
| `agent_assumptions` | `provenance` (operator assertions) |
| `budget_source` | `provenance` (later slot-level on budget) |
| `date_source` | `provenance` (later slot-level on date_window) |
| `urgency` | `lead_context` if operational, `facts` if traveler itinerary constraint |
| `special_occasion` | `facts` (traveler-relevant) |
| `internal_priority` | `lead_context` (internal-only) |

## What this discussion changes about today's work

### Immediate (today)

1. Wire `pace_preference` from `packet.facts["pace_preference"]` into `SuitabilityContext.pace_preference` at both construction sites in `src/suitability/integration.py`. Cleanest end-to-end fix; safe under any future namespacing because `pace_preference` stays in `facts` either way.
2. Document the corrected diagnosis (this file).
3. Append a correction stub to the 2026-04-27 audit pointing here.
4. Do **not** wire `lead_source`, `activity_provenance`, or `date_year_confidence` consumers yet. Their target homes are `lead_context` / `provenance`, not `facts`. Wiring them on the current shape would ossify the wrong abstraction.
5. Continue using `follow_up_due_date` from the existing notifications/snooze paths; do **not** treat it as a spine-stage trip fact.

### Vocabulary mismatch caught during implementation

The capture UI submits `pace_preference` values from the set `{rushed, normal, relaxed}` (per `Docs/PHASE2_CALL_CAPTURE_IMPLEMENTATION.md` and the BFF dropdown). The suitability model declares the literal set `{relaxed, balanced, packed}` (per `src/suitability/models.py:74`).

Per AGENTS.md "Data Loss Prevention Pattern" the implementation must:

- normalize known synonyms (`rushed` → `packed`, `normal` → `balanced`, `relaxed` → `relaxed`),
- log unknown values rather than silently dropping them,
- default unknown values to `balanced` (the natural midpoint) so the run still proceeds with a safe value.

This vocabulary unification is itself a follow-up worth tracking: the UI and the model should agree on a single canonical set in a future task. For now, the integration layer normalizes.

### Next architectural slice (separate task)

Slice the namespace migration into:

1. **Slice N1 — namespace introduction.** Add `lead_context` and `provenance` containers to `CanonicalPacket`. Move ingestion mapping for `follow_up_due_date`, `lead_source`, `activity_provenance`, `date_year_confidence` out of `packet.facts` into the new homes. Keep `pace_preference` in `packet.facts`.
2. **Slice N2 — traveler-safe serialization.** Add or verify `to_traveler_dict()` / `to_internal_dict()` / `to_audit_dict()` views. Traveler dict must exclude `lead_context` and raw `provenance` by construction. Add leakage-prevention tests.
3. **Slice N3 — consumer wiring on the new shape.** With namespaces in place, wire each remaining field into its proper consumer:
   - `follow_up_due_date` → spine stage events / watchdog (optional; current notifications path is sufficient for v1).
   - `lead_source` → internal dashboard / lead metadata view only.
   - `activity_provenance` → composer/strategy via traveler-safe interpretation (e.g., prioritize traveler-requested activities, demote agent-suggested unless confirmed).
   - `date_year_confidence` → follow-up question generator that asks the traveler to confirm the year.
4. **Slice N4 — slot-level metadata.** Promote `date_year_confidence` and `activity_provenance` to per-slot metadata once the slot model is mature.

## 11-dimension audit (this slice — Option A only)

| Dimension | Verdict | Note |
|-----------|---------|------|
| Code | ✅ | Two function bodies modified; `SuitabilityContext` already has the field; no schema change. |
| Operational | 🟡 | Operators will start seeing pace-preference-aware suitability scoring once Slice 4 of suitability scoring also reads it; this slice is necessary but not sufficient on its own. |
| User Experience | ✅ | Ravi's "don't rush it" now flows through to the suitability layer instead of being silently dropped. |
| Logical Consistency | ✅ | Vocabulary normalization documented and tested; no synchronization risk introduced. |
| Commercial | 🟡 | Foundational; commercial value lands when downstream scoring fully consumes it. |
| Data Integrity | ✅ | Clamping/normalization with logging per data-loss-prevention pattern. No silent drops. |
| Quality & Reliability | ✅ | New unit + integration tests; baseline 31 suitability tests still pass. |
| Compliance | ✅ | `pace_preference` is traveler-relevant; no leakage concern. |
| Operational Readiness | ✅ | Backward compatible; no migration; null-safe; no rollback needed. |
| Critical Path | ✅ | Smallest correct slice; does not lock in the namespacing decision. |
| Final Verdict | Merge: yes. Feature-ready: 🟡 partial (suitability scoring must also use the field for full value). Launch-ready: 🟡 same. |

## Research / exploration list (added by this discovery)

These are not in scope for today but should land on the project's research/exploration backlog:

1. **Packet namespacing migration** (Slices N1–N4 above). The architectural follow-up.
2. **Traveler-safe vs internal serialization audit.** Verify every existing serializer (`to_traveler_dict`, composer prompt builders, audit/export endpoints) does not leak `lead_context` or raw provenance.
3. **Capture vocabulary unification.** The `pace_preference` API/UI uses `{rushed, normal, relaxed}` but the suitability model uses `{relaxed, balanced, packed}`. Pick one canonical set; update API, UI, model, fixtures, tests, and docs in one pass.
4. **Confidence as slot property vs sibling fact.** Is the confidence-as-sibling-fact pattern a known anti-pattern in NLP/RAG extraction pipelines? Worth a short literature scan.
5. **Operator-stated vs traveler-stated preference.** Should `pace_preference` carry an actor label (`stated_by: traveler|operator|system`)? Same for `activity_provenance`. Touches D5 override-learning.
6. **Follow-up SLA → spine stage event integration.** Should breach of `follow_up_due_date` emit a stage event consumable by the watchdog?
7. **Lead-source attribution dashboard.** Marketing wants to know warm vs cold conversion ratios. Do we want a per-trip badge, an aggregate dashboard, or both?
8. **Date-year inference confirmation flow.** When `date_year_confidence` is `unsure`, the system should auto-add a follow-up question. Where does that live — packet ingestion, decision, or a UI prompt?
9. **Activity provenance taxonomy.** `traveler-requested` / `agent-suggested` / `system-inferred` is a starting set. Worth confirming with one more agency-owner interview before locking the schema.
10. **Capture-pipeline integration tests against real call recap text.** The Singapore-call scenario from the original audit should run as a fixture-driven integration test that asserts every field arrives, gets stored, gets read, and influences output where applicable.

## Files touched by today's slice

- `src/suitability/integration.py` — wired `pace_preference` from `packet.facts` into both `SuitabilityContext` constructions, with vocabulary normalization.
- `tests/test_pace_preference_wiring.py` — new test asserting end-to-end wiring.
- `Docs/research/DATA_CAPTURE_PACKET_NAMESPACING_DISCOVERY_2026-04-29.md` — this file.
- `Docs/research/DATA_CAPTURE_UI_UX_AUDIT_2026-04-27.md` — appended a correction stub pointing to this file.

## Verification

- 31 baseline suitability + intake-pipeline-hardening tests still pass after the change.
- New `tests/test_pace_preference_wiring.py` proves: structured-import of `pace_preference: "relaxed"` reaches `SuitabilityContext.pace_preference` as `"relaxed"`; `"rushed"` is normalized to `"packed"`; `"normal"` is normalized to `"balanced"`; an unknown value falls back to `"balanced"` and emits a warning log.
- Full `tests/test_suitability*.py` and `tests/test_intake_pipeline_hardening.py` continue to pass.

## Open questions that should not block today

These are noted explicitly so a future agent does not silently ignore them:

1. Should the API/UI vocabulary or the suitability vocabulary be the canonical one?
2. Should `pace_preference` eventually move out of `packet.facts` into `packet.preferences`?
3. Should the namespacing migration be one PR or four (one per slice)?
4. Who owns the marketing-attribution dashboard once `lead_source` is wired through?
