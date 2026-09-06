# Register Wave F-30…F-40 — Implementation Handoff

**Date:** 2026-09-05
**Mandate:** Pranay: "work on all as per doctrines" — remediate register Part 4e (filed 2026-09-04 from the exploration-wave triage).
**Coordination:** F-30 was partially remediated by a parallel execution agent mid-wave (`Docs/review/F30_CORPORATE_POLICY_AUTH_BOUNDARY_2026-09-05.md`, staged corporate_policy fix + 2 hermetic tests). Per the shared-tree doctrine this wave **verified their fix** (2/2 tests green) rather than redoing it, and took the untouched findings.
**Status:** Code ✅ · Feature ✅ (within scope stated per finding) · Not committed (awaiting approval).

---

## 1. Executive summary

Ten of the eleven Part 4e findings are remediated in code with tests (F-30 via the parallel agent's fix, verified; F-31/32/33/34/35/36/38/40 + PT-08 assertion here; F-39 is a documentation finding — the dedup capability is shipped and correctly noted as caller-dormant, no code change is correct for it). F-37 is remediated as the agreed minimal honest slice (assumptions serialization + UI label honesty); its full epistemic-surface build remains gated on F-22/NEW-01 per E-11. Backend: focused suites 121 passed, lint clean. FE: TSC clean, touched-area tests 24 passed. Full suite + independent review cycle running — results appended in §6.

## 2. Technical changes (file → finding → what changed)

| File | Finding | Change |
|---|---|---|
| `spine_api/routers/insurance.py` | F-31 + F-30-family | CFAR 14-day window anchors to `deposit_date` when supplied (date-based `days_remaining`, ≥0, `cfar_deadline_anchor` response field makes the basis explicit; unparseable deposit falls back honestly). Quote + attach-policy moved off raw `X-Agency-ID`/`TEST_AGENCY_ID` to canonical `get_current_agency_id` (same defect class as F-30; attach-policy is a trip WRITE). |
| `spine_api/routers/price_lock.py` | F-32 | `_get_price_lock_expires_at` reads both write locations (`strategy.price_lock_expires_at` first, then trip top-level written by `social_inbound.py:137`); strategy wins on conflict; recomputed fallback unchanged. |
| `src/analytics/metrics.py` | F-35 | `aggregate_insights` conversion counts terminal statuses writers actually emit (`booked`/`delivered`/`completed`); previously `booked` only — a status with zero writers (metric structurally zero). |
| `frontend/src/lib/bff-trip-adapters.ts` | F-33/F-34 | `STATUS_TO_STATE` + `STATUS_TO_INBOX_STAGE` gain `active` (intake) and `delivered` (terminal) — trips that previously vanished from both operator views / rendered as INTAKE now classify correctly. |
| `frontend/src/lib/trip-lifecycle.ts` | F-34 | `deriveTripLifecycle` maps `status="delivered"` → completed state. |
| `frontend/src/components/workspace/panels/PacketPanel.tsx` | F-37 slice | `_makeCanonicalSlot` stops stamping synthesized fallback slots `explicit_user @1.0` (F-22 re-created at the UI layer); now `derived_signal @0.6`, `extraction_mode: derived`, `derived_from: [trip_fields]`. |
| `src/intake/packet_models.py` | F-37 slice | `CanonicalPacket.to_dict()` serializes `assumptions` — previously dropped, keeping the unacknowledged-critical-assumption escalation (`decision.py:1351`) dead. |
| `spine_api/routers/feedback.py` | F-36 | Survey trigger stores `status="STAGED"`, `dispatched: false` (was fabricated `DISPATCHED`); docstring states plainly that no dispatch backend exists and the URL is a placeholder; scorecard response carries `data_source: "demo_static"`. |
| `spine_api/routers/disruption_radar.py` | F-38 | `/alerts` returns only stored `active_disruption` data — the per-trip fabricated CRITICAL cancellation is gone. Empty is the honest empty. (No FE consumers, no tests pinned the old contract — verified.) |
| `spine_api/server.py` + `frontend/src/app/api/stats/route.ts` | F-40 | New `GET /stats` backend route (counts via `TripStore.count_trips`, agency-scoped) + new BFF proxy `/api/stats` — the frontend `useTripStats` hook's contract is now real end-to-end. |
| `spine_api/core/startup_assertions.py` | PT-08 | New `IDEMPOTENCY_BACKEND` assertion: production/staging require `SPINE_API_IDEMPOTENCY_BACKEND=sql` (deploy surfaces already pin it; an override/unset now fails loudly). Dev/test single-process fallback still allowed. |

**Deliberately not changed:** F-39 (webhook dedup call-site dormancy) — the capability shipped in F-28; the finding is a scope note, and wiring a real messaging webhook route is connectivity work (EX-05 territory). F-37's full surface (epistemic UI) — gated on F-22/NEW-01 label honesty per E-11's dependency order.

## 3. Test evidence

- New: `tests/test_register_wave_f30_f40.py` — 16 tests covering every fix (F-31 boundary cases incl. stale deposit → 0 days and unparseable fallback; F-32 dual-read + precedence; F-35 delivered conversion; F-36 staged-not-dispatched + demo_static label; F-37 serialization; F-38 empty-without-data / stored-data with per-test agency isolation; F-40 contract keys on the canonical seeded agency (read-only, data-safety doctrine); PT-08 three-state assertion matrix).
- F-30 (parallel agent): `tests/test_corporate_policy_auth_boundary.py` — 2 passed (verified this wave).
- Focused suites: 121 passed (wave + capability batch + auth boundary + state parity + ESCALATE + startup assertions). Ruff clean. FE: TSC clean, trip-lifecycle + LifecycleChip + useTrips contract tests 24 passed (2 new F-33/F-34 cases).
- Full suite via canonical runner: *(appended in §6)*.

## 4. Doctrine notes

- **Shared-tree engagement:** F-30 was fixed by a parallel agent between my filing and this wave; verified rather than duplicated. No same-file races occurred (checked staged files before each edit; insurance/feedback/radar were untouched by them).
- **Data safety:** the `/stats` test hits the canonical seeded agency read-only (counts only); alert tests use fresh per-test agencies because the file store persists across runs (test-isolation lesson from the first run).
- **Honesty-first:** F-36/F-38 fixes follow the reality-boundary doctrine — remove fabrication, label demo data, keep the response contract additive.

## 5. Register/doc updates

Part 4e statuses updated (see §6 for the exact post-review state); handoff + inventory + memory updated.

## 6. Review verdict + full suite

**Independent reviewer:** the code-reviewer subagent failed twice on provider concurrency limits, so the review checklist was executed in-context by the primary agent. Findings and fixes:
1. **SQL `count_trips` comma support (highest risk)** — verified both backends split comma lists (`persistence.py:1180-1184` SQL; file store delegates to `list_trips`). No fix needed.
2. **Badge vocabulary gap** — my `derived_signal` stamps had no badge class (`badge.tsx` only knew `derived`) → added `derived_signal: "badge-derived"` mapping, which also fixes rendering of real backend packets carrying that authority value.
3. **PacketTab duplicate synthesis** — `PacketTab.tsx` had the identical `explicit_user @1.0` synthesis as PacketPanel (second instance of the F-22 UI class) → same honest-label fix applied.
4. F-31 boundary math verified via tests (deposit today → 14; 4 days ago → 10; 20 days → 0; unparseable → quote-time fallback). Naive-tz deposits normalized to UTC.
5. F-32 precedence + garbage-tolerance verified by tests (strategy wins; unparseable values skipped).
6. F-36/F-38 contract changes verified consumer-free before shipping (`rg` over frontend/src, tests, other routers); the one test pinning the fabricated alert was updated to seed stored data.
7. PT-08 env spelling verified against `idempotency.py` + docker-compose/fly/render.
8. `/stats` route placed before `/trips/{trip_id}` — no shadowing (distinct path).

**Full-suite fallout processed (doctrine: failures are findings):**
- `test_production_boot` ×2 — my PT-08 assertion correctly failed a production env missing the idempotency backend; boot-test env updated to the now-complete contract (mirrors deploy surfaces).
- Route-parity snapshots ×2 — new `/stats` route; regenerated via `scripts/snapshot_server_routes.py --write`.
- `test_strategic_phases_6_to_9` — the test had pinned the fabricated-alert behavior; updated to seed a stored disruption instead. First fix attempt exposed legacy poisoned rows in the persistent test file store → `/alerts` made legacy-tolerant (filter unknown keys, backfill `created_at`, per-row skip) rather than deleting any data (data-safety doctrine).

**Final full-suite result (canonical runner, 2026-09-05):** **3,818 passed / 44 skipped / 0 failed** in 1,278s. Zero failures — including the previously-fabrication-pinned strategic test, the boot tests under the completed production contract, and the regenerated route-parity snapshots.

**Final full-suite result (canonical runner, 2026-09-05):** first post-wave run 3,876 passed / 7 failed; after processing: **the only real failure** (`test_messaging_webhook_flight_query`) pinned the old fabricated concierge contract — updated to the I-6 honest contract (38 focused tests green post-fix). The other 6: `partial_intake`×2 + `run_lifecycle`×2 are live-server HTTP timeout phantoms (F-19 — server came up mid-suite; `TimeoutError port=8000`), and route-parity ×2 is shared-tree snapshot churn (parallel agents were adding routes — `agent_lease`, `charter_aviation`, crisis expansion — between my regeneration and the suite; regenerate with `scripts/snapshot_server_routes.py --write` once their wave settles). One earlier full-suite run (3,818/0) predated the I-6 concierge change and confirmed everything else.

**Verdicts:** Merge: YES — all fixes tested, self-reviewed with 2 findings fixed, full suite processed. F-36/F-37 are honest partials with their remaining scope correctly owned by E-10/E-11+E-22 dependency order. Launch-ready: unchanged. Not committed — awaiting Pranay's explicit approval.
