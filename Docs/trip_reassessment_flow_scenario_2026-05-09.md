# Trip Reassessment Flow (Auto + Explicit) — Scenario Record

Date: 2026-05-09
Project: `/Users/pranay/Projects/travel_agency_agent`

## User Ask Captured

1. The system must re-review new data during the agentic lifecycle.
2. It must support both:
- auto re-runs when meaningful trip data changes
- explicit/manual re-runs triggered by the operator
3. Controls must be configurable in settings.
4. Behavior must stay coherent across settings, itinerary/trip updates, logging, and downstream pipeline stages.
5. Trip identity must remain stable across lifecycle:
- a trip that starts from a draft keeps the same `trip_id` through reprocessing and completion
- no new trip ID on every reassessment
6. Evaluation should follow first principles and real-world stakeholder outcomes, not only existing code patterns.

## Real-World Scenario

Example: Inquiry mentions Machu Picchu with a senior traveler.

1. Initial assessment flags risk because age/experience signals are incomplete.
2. Operator updates profile with corrected context (experienced professional climber).
3. System should:
- ingest the update
- re-run suitability/decision logic
- update trip state and recommendations
- show that change in timeline/audit/logging
- keep the same trip entity for continuity, accountability, and reporting

## Why This Matters

1. Operator trust:
- Re-evaluation must reflect newest truth, otherwise operators ignore system output.
2. Customer experience:
- Outdated risk posture causes wrong recommendations and unnecessary friction.
3. Commercial value:
- Faster recovery from incomplete/misleading initial intake improves conversion.
4. Governance:
- Decision changes must be auditable with clear trigger reason and actor path.
5. Lifecycle integrity:
- Stable `trip_id` keeps a single source of truth from draft to closure and feedback.

## Implemented Direction (This Session)

1. Policy surface:
- Added autonomy settings for `auto_reprocess_on_edit`, `allow_explicit_reassess`, and `auto_reprocess_stages`.
2. Triggering:
- Auto reassessment from meaningful edits on `PATCH /trips/{trip_id}` when enabled and stage-allowed.
- Explicit reassessment endpoint `POST /trips/{trip_id}/reassess`.
3. Identity preservation:
- Pipeline save path now supports preserving existing `trip_id` during reassessment.
4. Auditability:
- Reassess queue events logged with trigger type (`auto_edit` or `explicit`) and reason.
5. Frontend settings:
- UI controls added so ops can manage auto/manual behavior and per-stage enablement.

## Expansion Backlog (Planned)

1. Real-time push:
- WebSocket/SSE updates for reassess start/progress/complete to reduce polling latency.
2. Trigger precision:
- Move from static field list to semantic change detection (fact-level deltas + confidence impact).
3. SLA safeguards:
- Debounce and coalesce rapid edits to avoid noisy reruns.
4. Explainability:
- Diff view for "what changed in output and why" after reassessment.
5. Closure gate:
- Ensure reassessment logic remains active through trip closure + post-trip feedback windows where policy requires.
