# E-E — Timeline-as-Evidence ADR (2026-09-08)

**Exploration package E-E (PER-0700)** — unblocks PA-19 (audit-chain verify), PA-04 (decision stream), operator rationale UI. Status: **PROPOSED**.

## Context

Three timelines exist today, each partial, none authoritative end-to-end:

1. `execution_events` table (`spine_api/models/tenant.py:707`) — durable, agency-scoped, event-sourced; written by `confirmation_service` and `execution_event_service`. **This is the only append-only, per-agency evidence ledger.**
2. `TripMutationHistoryStack` timeline (`spine_api/routers/trip_history.py:152`) — trip-mutation view.
3. The run ledger + file `analytics._extra.status_history` — status transitions (audited merge added in `6c7c824`).

PA-04's complaint ("production timeline blind to decisions") and PA-19's ("audit chain unverifiable") share one root: decisions are persisted in trip JSON but never anchored into an append-only evidence stream with a verifiable predecessor hash.

## Decision

**One evidence stream: `execution_events` becomes the canonical timeline.** Everything else is a projection.

1. **One id-space:** every state-changing actor (pipeline stages, decisions, gates, fulfillment, confirmation lifecycle, IROPS previews that matter) emits an `ExecutionEvent` via the existing `execution_event_service.emit_event` — the single choke point. Event kinds are enums, not free text.
2. **Anchor chain:** `execution_events` gains `prev_hash` + `hash` columns (same construction as the F-06 audit chain: hash = SHA-256(prev_hash ‖ canonical_payload_json)). A nightly + on-demand verifier walks the chain per agency and reports first-break. Reuse F-06's cross-process critical section pattern for appends.
3. **Projections, not sources:** trip-history timeline, operator "why" panels, and D6 fixtures all READ `execution_events`. `analytics._extra.status_history` remains written (compat) but is demoted to a cache; docs mark it `projection`.
4. **Decision events:** when the hybrid/deterministic engine picks a decision, emit `decision_made` with `rationale_ref` (pointer to rationale payload), `reality_tier`, `cost_estimate` (E-C correlation), and `input_fingerprint`. This is the PA-04 fix: the production timeline can finally answer "why did the system do this on <date>".
5. **Retention:** events are never deleted; erasure requests (X-14/GDPR) tokenize payloads via the existing private-field encryption, never drop rows (the chain must stay continuous).

## Consequences

- PA-19 verify/re-anchor reduces to chain-walk + one re-anchor endpoint (operator, auth'd).
- Operator NBTA/rationale UI (roadmap item) reads one table.
- Cost attribution (E-C) gets a durable join key: every `decision_made` carries run/trip/stage.
- Migration is additive: two nullable columns + backfill script (A-20 custody rules apply; backfill is offline, re-anchoring from genesis, one agency at a time).

## Rejection note

Extending the F-06 file audit chain to carry application events was rejected: it is process-level and tamper-evident but not agency-scoped or queryable; the DB chain gives both, and F-06 remains the meta-evidence layer for the evidence system itself.

## Sequencing

1. Add `prev_hash`/`hash` columns + append choke-point enforcement (S).
2. Emit `decision_made` from the pipeline decision stage (M).
3. Verifier endpoint + nightly loop (S).
4. Re-point trip-history timeline at `execution_events` (M).
5. Backfill/re-anchor migration under A-20 custody (owner-gated).
