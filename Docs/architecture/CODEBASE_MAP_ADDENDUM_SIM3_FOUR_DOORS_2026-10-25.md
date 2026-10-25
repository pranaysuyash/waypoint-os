# Codebase Map Addendum — Sim #3 "Four Doors" surfaces (2026-10-25)

**Status:** addendum slice. The full map refresh (eleven doors, posture
matrix, persistence doors, BFF parity) remains Sim #4's queued U16 — this
document covers only the Sim #3 surfaces so the map is not blind to them
until U16 lands. Parent map:
`Docs/architecture/CODEBASE_FEATURES_FLOWS_LOOPS_MAP_2026-09-03.md` (+ drift
addendum 2026-09-06). Doctrine §9: maps stay current; discovery is recorded,
not chatted.

## Doors verified live in Sim #3 (all Tier-4 evidence, `Docs/sims/assets/sim3/`)

| Door | Entry seam | Backing stores | Honest notes |
|------|-----------|----------------|--------------|
| Draft intake → run | `POST /api/drafts` (file-backed `data/drafts/*.json`) → `POST /run {raw_note, draft_id}` → `PATCH /api/drafts/{id} {customer_message}` (server.py:2738 writes `raw_input.submission.raw_note`) | DraftStore = **file store** (plaintext — FND-0377); trips = SQL+RLS | `POST /run` without a draft_id creates an orphan run with no draft trail. Trip rows persist **no raw_note** (submission metadata + draft_id only). Reprocess trail = `audit_logs` (`trip_created` + one `spine_decision` per run); `/api/v1/trips/{id}/history` is checkpoint-based and empty unless an operator checkpoints. |
| Ask-traveler loop (T1) | `POST /followups/{trip}/send` mints signed token (proposals signing seam) → public `/a/{token}` (no auth) → `POST /api/public/asks/{token}/answers` (answers list validated against the trip's open questions) → answers recorded on trip | trips table (`traveler_asks`/`traveler_answers`) | Questions source = `decision.follow_up_questions`; blocked leads get them via the ESCALATE ask-floor (orchestration.py). Dispatch honest `NOT_CONFIGURED` without a provider. |
| Customer memory | `/api/v1/customers/remember` + `/memory` (GET) + `/hydrate-trip/{trip_id}` | `customer_memory_profiles` SQL (agency-scoped) + 5-tier MemoryStore + process-local fallback (THREE stores — U1) | `remember` had the db.refresh crash (fixed); hydrate is DISPLAY-ONLY by ADR-008 §7 (never enters the packet). |
| Claims / disruption | `/api/v1/passenger-rights/evaluate` + `/{trip}/generate-claim` + disposition GET/PATCH; ghost concierge via `PATCH /trips/{id} {flight_status_updates}` | trips + claim state; draft-only interventions | One framework authority: `spine_api/services/claim_framework.py` (EU261/UK261/US_DOT/NONE+Montreal Art. 19; national-regime name registry, amounts gated on citations). Disposition machine: 8 states, terminal CLOSED, transitions 409-rejected. Money boundary holds (outcome recorded-only). |

## Cross-door invariants discovered (map-worthy)

1. **Two privacy postures, one boundary gap** — the R-15 guard's mode matrix
   (`src/security/privacy_guard.py:546`) guards trip persistence only; the
   DraftStore file path persists full traveler notes in plaintext (FND-0377).
2. **Merge precedence stack** — extraction merge-with-provenance (extractors)
   → `_preserve_authoritative_facts` (persistence.py:3979, FND-0351) →
   `field_merge.resolve_field_merge` (optimistic-sync). Operator
   clear-destination + reprocess interplay = open owner call (FND-0376).
3. **Two required-fields vocabularies** — frontend planning gate (packet-fact
   canonical, FND-0332) vs backend `FIELD_REQUIRED_FOR`/structural validation
   (FND-0379 drift class).
4. **Session-level RLS GUC dies at commit** — post-commit `refresh()` on a
   pooled connection re-checks out GUC-less; use `refresh_or_reselect`
   (`spine_api/core/rls.py:295`) for every commit-then-refresh.
5. **One bridge loop** — `_run_async_blocking` runs on a process-wide
   background loop (FND-0367); never create per-call loops over the async
   engine.

**Correction (2026-10-25, FND-0377 retraction):** invariant 1 above was
written from stale legacy files. The DraftStore HAS encrypted at rest since
2026-10-23 (FND-0326 residual, `__encrypted_draft` v2 envelope) — the
original plaintext files were pre-fix legacy artifacts and have since been
migrated via `tools/migrate_legacy_drafts.py` (673 files, 0 plaintext
remain). Invariant 1 stands corrected: the draft lane is inside the
encryption boundary; the honest residual is only the dev-fallback key
enforcement (existing startup assertion).
