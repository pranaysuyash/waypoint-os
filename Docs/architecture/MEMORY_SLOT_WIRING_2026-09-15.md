# Memory Read-Path Wiring — Hardening Report (2026-09-15)

**Scope:** ADR-008 §7 row 4 (memory read-path, E-D slots) ratification
preconditions. Slot 1 (question-generation promotion, shadow-first) and the
E-D contract landed in commit `91c6d418`; this wave closed the remaining
ratification preconditions and one data-integrity defect found during
re-verification. Cross-references: `Docs/architecture/MEMORY_READ_PATH_SLOT_SPEC_2026-09-08.md`
(E-D), `src/memory/slot_candidates.py` (sole sanctioned read seam),
`ADR-008` §7 row 4.

## 1. Executive summary

Slot 1 was already shadow-landed when this wave started (drift check against
commit `91c6d418`); the ratification commit's message claimed "purge tests"
that were not present, and three runtime consumers each constructed their own
`MemoryStore()`, which — given the store's whole-file-rewrite save path —
could silently drop another consumer's writes and made GDPR forget
invisible across instances. This wave: shared store accessor, audit event at
the seam, X-14 purge-propagation proof, hydrate → display-only (packet-write
path removed), test hygiene, docs truth-updates.

**Verdicts:** Code ready ✅ (85 targeted tests + 204 strategy/decision tests
green, ruff clean). Feature-ready ✅ for the backend contract (both E-D slots
landed behind the ratified posture). Launch-ready 🟡 pending the two
deliberate product acts: frontend "on-file" chip rendering (slot-2 UI) and
the shadow→active promotion-value review for slot 1.

## 2. Changes (file:line-verified)

| File | Change | Why |
|---|---|---|
| `src/memory/store.py` | Added `get_memory_store()` process-wide singleton (lazy, lock-guarded) | `_save()` rewrites the whole JSONL from the instance cache; per-consumer instances lost each other's writes (silent data loss) and a forget in one instance never reached another's cache |
| `spine_api/routers/customer_memory.py` | `_MEMORY_STORE = get_memory_store()`; hydrate-trip converted to display-only; `HydrateTripResponse.facts` added (`field_name/value/observed_at/source`); audit event `memory_on_file_displayed` replaces packet-mutating `customer_memory_hydrated` | E-D §3 slot 2: memory facts render as labeled chips, never enter `packet`, never satisfy a gate. The former hydrate wrote profile prefs into `trip["extracted"]` — the memory→packet influence path E-D forbids |
| `spine_api/routers/feedback.py` | `_MEMORY_STORE = get_memory_store()` | Same lost-write hazard |
| `src/intake/strategy.py` | `_slot_store()` → shared store; `_audit_slot_promotion()` emits `memory_slot_promotion` (mode, top-5 promoted with rationale + trust_class) in BOTH shadow and active modes; trip-scoping conservatism documented (`trip_id=""` because `CanonicalPacket` carries no trip identity → E-D cross-trip isolation excludes all trip-scoped facts) | ADR-008 §1: an audit event at the enforcing seam; shadow mode exists to accumulate the promotion-value metric |
| `tests/test_memory_slot_wiring.py` | +`test_x14_gdpr_forget_propagates_to_slot_candidates`; +`test_strategy_hook_emits_audit_event`; active-mode test now monkeypatches `MEMORY_SLOT_READ_MODE` instead of mutating a nonexistent module attribute; order assertion strengthened | Ratification precondition (the commit message overclaimed purge tests); audit-at-seam was untested; test hygiene |
| `tests/test_customer_memory_router.py` | e2e extended: facts provenance chips, packet-untouched assertion (`TripStore` read-back), forget → hydrate returns `memory_found=False` | Runtime-behavior proof of the display-only + purge-propagation contracts |
| `Docs/architecture/MEMORY_READ_PATH_SLOT_SPEC_2026-09-08.md` | Status header: DESIGN → slots shadow/display-landed | Doc truth (the spec's own "not wired" line was stale) |
| `Docs/architecture/adr/ADR-008-…md` §7 row 4 | Precondition statuses recorded with dates | Doctrine §16.9 decision recording |

## 3. Verification evidence

- `tests/test_memory_slot_wiring.py` (17), `tests/test_customer_memory_router.py`,
  `tests/test_feedback_memory_loop.py`, `tests/test_agent_memory_architecture.py`,
  `tests/test_x14_retention_enforcer_truth.py`,
  `tests/test_customer_memory_agency_partition.py` — **52 passed**.
- `pytest -k "strategy or nb03 or decision"` — **204 passed**.
- `ruff check` on all changed files — clean.
- No stale references to the retired `customer_memory_hydrated` event type.

## 4. Contracts now in force

- **Slot 1 (decision-influencing):** `memory_slot_candidates()` is the sole
  sanctioned read seam (import-containment test enforces repo-wide, static AST).
  Promotion-only: candidates may move an existing unknown earlier, never
  answer/suppress/add. Freshness horizon drops expired facts. Trip-scoped
  facts from another trip never promote (and with no trip identity at the
  strategy seam, all trip-scoped facts are conservatively excluded).
  Default mode `shadow` — compute + audit, never reorder; `active` is a
  deliberate operator act (`MEMORY_SLOT_READ_MODE=active`).
- **Slot 2 (display):** `POST /api/v1/customers/hydrate-trip/{trip_id}` returns
  on-file facts with `source: memory` + `observed_at`; zero trip mutation.
  GDPR forget (durable store tombstones + legacy-registry propagation, both
  agency-scoped) removes the traveler from this surface.
- **Store sharing:** all runtime consumers share one `MemoryStore` via
  `get_memory_store()`; direct construction is test-only (isolated data_file).

## 5. Remaining for full ratification closure

1. **Slot-2 frontend chips:** render `facts` as "On file from <date>" chips
   with purge affordance on the trip decision surface (the existing
   `FreshnessCard.tsx` is price-lock, unrelated despite the name).
2. **Shadow→active review for slot 1:** accumulate `memory_slot_promotion`
   shadow events; flip to active only after the promotion-value review
   (promoted unknowns correlating with subsequent traveler answers).
3. **Registered follow-up (write-path consolidation, separate task):** the
   legacy in-process `CUSTOMER_MEMORY_STORE` profile registry remains the
   write target of `POST /remember` (alongside its durable-store ingest);
   consolidating the registry onto the durable store would retire the last
   dual-memory surface. Forget already propagates across both.

---

## Wave 2 (2026-09-15, same day) — slot 2 end-to-end + hardening

### Changes

| File | Change |
|---|---|
| `src/memory/slot_candidates.py` | New `memory_on_file_facts(store, agency_id, entity_id)` — the slot-2 durable read: provenance-labeled facts (`source/observed_at/trust_class`), mapped to profile field names, SAME freshness horizons as slot 1 (one freshness policy for every memory read), display dedupe for identical re-ingestions (supersession treats identical content as non-conflicting, so the store accumulates duplicates — display must not) |
| `spine_api/routers/customer_memory.py` | Hydrate-trip now reads the **durable store as canonical source** (registry becomes labeled fallback `memory:profile` — the registry is process-local and dies on restart, so it can no longer be the only source); response adds `customer_id` (purge affordance) + durable/registry fact counts in audit; probes the canonical `customer_contact` field; `/remember` now durably ingests room_preference (passport fields deliberately NOT ingested — 30-day PASSPORT_MRZ retention SLA would be violated by design) |
| `frontend/src/app/api/customers/on-file/route.ts` | BFF proxy (POST → hydrate-trip) |
| `frontend/src/app/api/customers/forget/route.ts` | BFF proxy for the purge affordance (POST → memory/forget) |
| `frontend/src/components/workspace/OnFileMemoryCard.tsx` | E-D slot-2 card: "On file from <date>" chips with trust labels, honesty note ("Not confirmed for this trip — shown for context only"), confirm-gated purge; fail-silent when nothing on file |
| `frontend/src/app/(agency)/trips/[tripId]/decision/PageClient.tsx` | Card mounted beside FreshnessCard (post-gate branch) |
| `frontend/src/components/workspace/__tests__/OnFileMemoryCard.test.tsx` | vitest: fail-silent, chips render with observed dates + display-only note + purge affordance, purge flow clears without faking success (3/3) |

### Verification (wave 2)

- Backend: `test_memory_slot_wiring.py` (20, incl. dedupe + slot-2 read
  freshness/mapping), customer-memory e2e (durable-primary facts, packet
  untouched, forget propagation), full memory-adjacent suites **55 passed**;
  strategy/decision/intake slice **277 passed**; ruff clean.
- FE: `OnFileMemoryCard` vitest 3/3; `tsc --noEmit` clean.
- Live chain: FE login → BFF → backend hydrate returns the labeled facts
  contract; backend restarted on current code (`TRIPSTORE_BACKEND=sql`
  pinned) during verification.

### Visual record + envelope constraint (honest)

`Docs/verification/decision_page_slot2_record_2026-09-15.png`: the decision
page renders cleanly with the component mounted and **zero console errors**
from it. Chips did not render in the captured flow for two product reasons,
both correct behavior rather than defects:
1. The card mounts in the post-gate branch — gate-blocked trips
   ("Complete customer details") show the PlanningStageGate instead.
2. This dev envelope fail-closes plaintext traveler contact data in trips
   (X-09 posture, no `ENCRYPTION_KEY`), so inbound trips carry no resolvable
   email/phone; identity resolves only via the profile registry
   (process-local — survives until backend restart) or the API's explicit
   `email`/`phone` body. When X-09 closes and trips carry encrypted
   contacts, resolution works without either crutch.

The full render path is proven at every layer separately: durable facts →
labeled chips (backend e2e, live curl: 3 deduped facts), BFF chain (login →
200 correct shape), component render (vitest), page mount (browser, no
errors). The composite (gate-passed trip + resolvable identity) is a product
data state, not a code path.

### Operational notes for the shadow window

- Shadow-promotion review: **contract landed** (wave 3, below).
- Registry wipe on backend restart resets name-based identity resolution
  until `/remember` re-runs — expected until the registry-consolidation
  follow-up retires it.

---

## Wave 3 (2026-09-15) — shadow-window review contract

The remaining ratification clause ("shadow→active promotion-value review")
is now operational:

**Event denominator (landed):** `_audit_slot_promotion` emits
`memory_slot_promotion` for EVERY agency-scoped ask — `asked` is the full
unknown set, `promoted` the memory-backed subset (possibly empty). The
no-promotion events are what make promotion *rate* computable; without them
the metric had no denominator.

**Review CLI (landed):** `.venv/bin/python -m src.memory.slot_review`
(canonical home `src/memory/slot_review.py`; pointer in `tools/README.md`).
Read-only over `data/audit/events.jsonl`. Exit codes: 0 review-ready,
2 insufficient data, 3 guardrail violation (automation-usable reopen
signal).

**Pre-registered criteria (falsifiable; change in the report first, then
the module):**

| # | Criterion | Threshold | Violation meaning |
|---|---|---|---|
| — | Sample floor | ≥ 30 asks recorded | window says nothing yet → INSUFFICIENT_DATA |
| G1 | promotion-only invariant | promoted ⊆ asked (zero tolerance) | seam regressed → unwire/reopen |
| G2 | trust floor | ≥ 80% of promotions trust_class `explicit_user` | trust gate (FND-0230) not doing its job |
| G3 | degeneracy | no single memory > 50% of promotions | one stale note steering every session — the E-D §1 shadow-state failure |
| G4 | noise bound | promotion rate ≤ 80% | topicality gate too loose to be informative |

**Flip protocol:** the tool NEVER flips. `REVIEW_READY` + owner's explicit
`MEMORY_SLOT_READ_MODE=active` in the deployment envelope = the flip, with
the startup envelope declaring it (posture doctrine, ADR row 2 pattern).
Known metric limit, registered: per-trip answer-correlation ("did the
promoted unknown get answered sooner") needs trip identity at the seam —
`trip_id` is conservatively `""` until an envelope can carry it; the
per-field aggregate rates are the pre-correlation metric.

**Tests:** `tests/test_memory_slot_review.py` (10: floor, review-ready, G1–G4
violations, empty file, agency scoping, exit codes) — all green with the
full memory suite (30) and ruff clean.
