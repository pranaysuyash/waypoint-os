# Codebase Features, Flows & Loops Map — Drift Addendum (2026-09-06)

**Status:** additive drift addendum to [CODEBASE_FEATURES_FLOWS_LOOPS_MAP_2026-09-03.md](CODEBASE_FEATURES_FLOWS_LOOPS_MAP_2026-09-03.md) (the parent map remains the canonical whole-repo reference; corrections here supersede only the sections noted in §5).
**Date:** 2026-09-06
**Method:** read-only exploration — `git show`/`git diff` over commit `096ceba` (585 files, +73,770/−2,597, committed 2026-09-06) plus the full uncommitted working tree (13 modified + 4 new files), one Explore sweep of the commit's capability surface, direct reads of every uncommitted diff. No code changed.
**Epistemic status:** every claim below is verified read-only against the tree at HEAD `096ceba` + working tree, with file:line citations. No test suite was re-run in this pass; baseline references are cited from their owning docs.

---

## 1. What commit `096ceba` landed (deltas vs the parent map)

### 1.1 Trip lifecycle read-model (NEW capability chain)

- **Backend status machine** — `spine_api/core/trip_status.py`: `QUOTE_CAPABLE_STATUSES` (`:35`), `INTAKE_BLOCKED_STATUSES` (`:39-41`), `enforce_status_transition` (`:100-112`) blocking intake-blocked → quote-capable in one hop, wired at 5 `TripStore` write sites (`spine_api/persistence.py:60,77,433,990,1317`), plus `record_status_transition` appending capped `status_history` `{from,to,at}` (`:115-135`, cap 50). `escalated` is deliberately excluded from sync-promotable statuses — only a human resolve clears it. Unknown statuses pass through with a warning (additive-first, `:78-89`).
- **Terminal vocabulary is now two-tier** — `GET /stats` (`spine_api/server.py:2045-2068`) counts terminal as `booked, delivered, completed, cancelled`; `active = total − terminal`. Frontend status maps gained `active` (blue, intake-complete/pre-routing) and `delivered` (green, approved-terminal per `src/analytics/review.py:101`) in `frontend/src/lib/bff-trip-adapters.ts` — closing register F-33/F-34 (before this, `active`/`delivered` trips vanished from operator views or rendered as intake).
- **Frontend read-model** — `frontend/src/lib/trip-lifecycle.ts`: 9-state blueprint `intake → needs_information → feasibility → planning → awaiting_customer_approval → booked_side → in_trip → completed (+escalated)` (`:23-32`), derivation precedence `:188-219`. Derives: needs-information consolidator joining trip status + `decision_state=ASK_FOLLOWUP` + `analytics.follow_up_status` (`:129-157`), allowed/forbidden actions per state (`:164-180`), and blockers incl. recovery mode. `in_trip` is declared but **dormant** — no input signal feeds it yet (`:183-187`).
- **UI** — `LifecycleChip` (`frontend/src/components/workspace/LifecycleChip.tsx:22-56`) mounted on `frontend/src/app/(agency)/trips/[tripId]/layout.tsx` only. The escalated queue is a **client-side slice** over the workspace list with `?filter=escalated`; the backend `GET /api/v1/assignments/queue/escalated` did not exist at commit time.

### 1.2 Field-merge precedence with provenance (NEW — TPM N-3)

`spine_api/services/field_merge.py`: preference fields (`:39-56`) merge **customer > operator**; commercial/structured fields (`:59-82`) merge **operator > customer**; unknown fields default operator-conservative (`:84-95`). Provenance lives under reserved packet key `_field_provenance` (`:36`) as `{actor, actor_id, at, superseded}`; client submissions of that key are rejected as conflicts (`:160-173`). Nothing is silently lost — rejected updates return as `MergeConflict` with kept value + reason (`:109-130,181-196`). Pre-merge-system unattributed commercial values are treated as operator-owned (`:197-219`). Replaces blind last-write-wins in `/optimistic-sync` (docstring `:1-24`).

### 1.3 Idempotency hardening (closes PT-08 seam)

- `spine_api/models/idempotency.py:32-63`: durable `idempotency_keys` table, **PK on `key`** (cross-worker dedup via INSERT race), TTL reclaim, deliberately not RLS-protected (system-scoped).
- **Fencing tokens**: opaque `token_urlsafe(32)` per acquisition; `mark_completed`/`mark_failed` are compare-and-set on the token — a slow owner whose row was TTL-reclaimed cannot complete it. Migration `alembic/versions/add_idempotency_fencing_token.py` is introspective and backfills legacy rows.
- **Startup assertion**: prod/staging fail boot unless `SPINE_API_IDEMPOTENCY_BACKEND ∈ {sql, postgres, postgresql}` (`spine_api/core/startup_assertions.py`); docker-compose pins `=sql`. Same wave added the placeholder-blocking `PROPOSAL_SIGNING_KEY` check.

### 1.4 Platform auth + Product B scoped analytics (NEW authority plane)

`spine_api/core/platform_auth.py:12-39`: `PLATFORM_ROLES = none | support | ops_admin | super_admin`; `require_platform_role(*roles)` is independent of agency membership — tenant `owner`/`admin` never grants cross-workspace visibility. ADR-007 (note actual path: `Docs/architecture/adr/ADR-007-PRODUCT-B-SCOPED-ANALYTICS_2026-09-03.md`): two projections over one KPI engine — agency route stays workspace-scoped; new `GET /platform/admin/analytics/product-b/kpis` (`spine_api/routers/product_b_analytics.py:44-79`) gated `super_admin`, rate-limited, audit-logged, typed `scope: agency|global` contract. A missing workspace filter is never interpreted as permission to go global.

### 1.5 Strategic expansion — LIVE vs SIMULATED verdicts

| Surface | Verdict | Evidence |
|---|---|---|
| agent_lease | **WIRED, now durable** — SQL backend (`agent_leases` table, `SPINE_API_AGENT_LEASE_BACKEND=sql`) + router mounted | `spine_api/routers/agent_lease.py`, `src/orchestration/agent_lease.py` |
| fulfillment | **WIRED endpoint, SIMULATED effects** — StripeIssuing (simulated issuance, real HMAC webhook verify) + Amadeus sandbox PNR + journey-graph mint + lease; **no BFF route-map entry, no frontend caller** at commit time | `spine_api/routers/fulfillment.py`, `src/orchestration/booking_fulfillment.py` |
| itinerary_export | LIVE computation, **standalone** — deterministic HTML export, sample payload, no BFF mapping | `spine_api/routers/itinerary_export.py` |
| logistics | WIRED to UI (partial) — 8 deterministic endpoints; BFF maps only connection-risk + route-geometry → `RouteLogisticsPanel` | `spine_api/routers/logistics.py:118-368`, `frontend/src/lib/route-map.ts` |
| irops_healer | HONESTY-DOWNGRADED — router returns `RealityTier.DETERMINISTIC_PREVIEW`/`PREVIEW_ONLY`, strips effect artifacts; new `src/logistics/irrops_healer.py` has **zero consumers** (duplicate engine, tests only) | `spine_api/routers/irops_healer.py` |
| distribution | HONESTY-DOWNGRADED — all endpoints return `status: "PREVIEW_ONLY"` + `provider_connected: false` | `spine_api/routers/distribution.py` |
| providers/ | amadeus_enterprise + twilio **SIMULATED, zero consumers**; stripe_issuing simulated issuance with real signature verification, only consumer is the simulated fulfillment engine | `spine_api/providers/` |
| margin_engine, export_bridge, debate_council, concierge/messaging_router, pipeline_bridge | **LANDED, NOT WIRED** — zero non-test consumers | `src/financial/margin_engine.py`, `src/accounting/export_bridge.py`, `src/agents/debate_council.py` |
| model router | docs only (ADR-001, exploration) — no new code | `Docs/exploration/` |

### 1.6 Honesty regime became enforced

- `frontend/src/components/ui/SimulatedBadge.tsx` — canonical two-label marker (`Sample data` = hardcoded fixture; `Simulated` = deterministic backend simulator, docstring `:10-11`), adopted across ~20 workbench/insights panels.
- `simulated-panels-honesty.test.tsx` — CI-enforced ban list ("Live GDS Sandbox", "TRANSMITTED TO EMBASSY DESK", "LIVE TELEPHONY TRANSCRIPT", VCC issuance copy, Alex Morgan fixtures…). The parent map's §8 honesty claims are now test-enforced at the UI layer, and backend surfaces self-label via reality-tier metadata.

### 1.7 CI gains

Findings-register lifecycle gate (`scripts/check_findings_register.py`, +248: state column is sole lifecycle owner, duplicate IDs are errors, open findings must be recently verified) · generated-types drift gate (`generate_types.py` + `git diff --exit-code` on `spine-api.ts`) · backend tests now run with `USE_HYBRID_DECISION_ENGINE=1` and `PROPOSAL_SIGNING_KEY` set. **Not CI-wired:** `tools/status_vocabulary_report.py`, `tools/check_worktree_classification.py`.

### 1.8 BFF allowlist bypass (architectural — register F-43)

`frontend/next.config.mjs:17-29` rewrites `/api/v1/:path*` and `/api/public/:path*` directly to `${SPINE_API_URL}` (landed in `096ceba`). Next `afterFiles` rewrites outrank the `api/[...path]` catch-all, so **every browser call to those prefixes skips the BFF entirely**: all `route-map.ts` `v1/…` entries are dead, and the map's §4.3 enforcement point (allowlist, unknown → 404) no longer gates `/api/v1` or `/api/public`. Backend per-endpoint JWT remains the real boundary — auth is cookie-based end-to-end (`frontend/src/lib/api-client.ts:110,156`; cookie fallback `spine_api/core/auth.py:58-59`), so JWT-enforced endpoints stay protected — but every `_auth_or_skip` mount with no in-handler check is browser-reachable without login; concrete case: `POST /api/v1/fulfillment/proposals/fulfill` (`fulfillment.py:33-56` — no JWT, no tenant context, simulated effects).

### 1.9 Frontend commit deltas (second sweep, beyond the honesty regime)

- **Fabricated-success pages FIXED (launch-audit items):** `corporate/offsites` deleted the ~55-line fake duty-of-care/policy fallback → `role="alert"` "Corporate data unavailable… no traveler status or policy result is being inferred" + "Duty-of-Care status requires live data" badge; `intake/fast` deleted the fake `trip_fast_demo123` teaser/suitability-96/price-lock block → `ok:false` + "Your inquiry was not submitted" alert.
- **F-37 restamp:** PacketPanel `_makeCanonicalSlot` now synthesizes derived slots as `derived_signal @0.6` with `derived_from: ["trip_fields"]` (was `explicit_user @1.0`); `badge.tsx:16-18` adds the load-bearing `derived_signal` variant. MemorySettingsTab GDPR console relabeled "Not connected — no compliance action", certificates restamped `GDPR-CERT-SAMPLE`/`tombstones_created: 0`.
- **D-09 canonical repair deep-link:** `?repair=<field>` canonical (`?field=` legacy alias), machine packet names normalized via `lib/repair-deep-link.ts`, capped anchor/focus retry, URL cleanup preserves unrelated params (IntakePanel `:382-384`).
- **Sample-labeling sweep:** `proposals/[proposalId]` is now explicitly a local fixture ("Illustrative pricing · no hold active", "Simulate Proposal Acceptance", SimulatedBadge banner); bookings/suppliers pages assert honesty relabels ("No live GDS/DMC connection", "not evidence that a supplier contract exists").
- **Live Product-B surface:** `platform-admin/product-b` page (new) + `useGovernance`/`governance-api.ts` hooks → route-map proxies → `product_b_analytics.py`; reachable only via the link inside `ProductBKpiPanel` on `/insights` (no nav entry).
- **Misc:** `useOverviewSummary` prefers unified-state `inbox_lead_count` (live read-model reconciliation); WelcomeModal → `WelcomeCard` (a11y rename, alias kept); itinerary-checker pdfjs `disableWorker` (bundler fix); drawer/modal `useCallback` (trivial).

---

## 2. Uncommitted working-tree drift (as of 2026-09-06, on top of `096ceba`)

### 2.1 Legitimate closures

- **Escalated queue (register I-1)** — `GET /api/v1/assignments/queue/escalated` (`spine_api/routers/assignments.py:101`): server-side slice of `TripRoutingState.status == "escalated"`, oldest first, SLA per entry, tenant-scoped, limit-clamped 500. Fixes the committed client-side-only chip, which missed routing-escalated trips whose `trip.status` looked healthy. Contract test `tests/test_assignments_escalated_queue.py` (`require_postgres`). **No frontend consumer yet** — the committed chip still slices client-side.
- **Journey-graph hydration (authenticated)** — `GET /api/v1/journey-graph/{trip_id}` (`spine_api/routers/journey_graph.py:118`): tenant-scoped via `get_trip_for_agency` (F-30 defect class), returns stored `journey_graph_nodes` + `booking_confirmation` or synthesizes the canonical flight → transfer → hotel DAG. Test `tests/test_journey_graph_hydration.py`.
- **FreshnessCard (register I-2 / F-14 family)** — `frontend/src/components/workspace/FreshnessCard.tsx` + BFF `frontend/src/app/api/price-lock/opportunities/route.ts`: display + CTA only for price-lock 72h windows / rate drops; re-lock stays gated by F-01/F-14. Mounted on the trip decision page. Honest by construction.
- **Proposal compiler `share_token`** — `src/orchestration/proposal_compiler.py:38,57,161`: the compiled package now carries the share token end-to-end (supporting the panel work in §2.2).
- **`agent_lease.py:421`** — SQLAlchemy correctness fix (`is_active.is_(True)` instead of `== True`).

### 2.2 New findings (filed as F-41/F-42 in the register)

- **F-41 (P1)** — `GET /api/public/journey-graph/{trip_id}` (`spine_api/routers/journey_graph.py:229-237`, mounted public at `spine_api/server.py:1468`, browser-reachable via the `next.config.mjs` `/api/public` rewrite) calls `get_journey_graph(trip_id)` directly, so `agency_id` stays the unresolved `Depends` sentinel — `TripStore.get_trip_for_agency` can never match (`persistence.py:463-468,1047-1058`). Every unauthenticated request therefore returns the **synthesized demo DAG** and `booking_confirmation` is always null. No cross-tenant leak today (agency never matches), but arbitrary trip IDs are echoed back with fabricated Belmond/Blacklane itineraries, and the companion page then labels that data "Synchronized … from Journey Dependency Graph" (`frontend/src/app/(traveler)/companion/page.tsx:168`) while dropping its GM-01 sample-data banner — the "Confirmed Itinerary" branch (`:155`) is dead code in practice. The companion test asserts only the fallback path (`tests/test_journey_graph_hydration.py:23-36`).
- **F-42 (P1)** — `ProposalCompilerPanel.tsx` (uncommitted) trades the GM-01 honesty contract for fulfillment theater rendered as real: `SimulatedBadge label="Amadeus NDC & Stripe VCC"` (`:150`) abuses the badge's two-label vocabulary, "AUTONOMOUS PIPELINE" (`:151`) and "Booking Confirmed & VCC Settled" / "CONFIRMED" (`:253`) replace the removed "DEMO PIPELINE · SIM ENGINES (NO LIVE INVENTORY)" marking. The wiring is **live, not dead** — the `/api/v1` rewrite carries the call to the auth-free fulfillment endpoint (see F-43), whose adapters are simulated, and the panel renders CONFIRMED with PNR/e-ticket/VCC last4; it also auto-submits the traveler's e-sign acceptance with a fabricated signer identity. `simulated-panels-honesty.test.tsx` has **no ProposalCompilerPanel block** — the honesty gate passes.
- **F-43 (P1)** — the `next.config.mjs:17-29` rewrites dissolve the BFF route-map allowlist for `/api/v1/*` and `/api/public/*` (see §1.8): every `route-map.ts` `v1/…` entry is dead, and auth-optional `_auth_or_skip` mounts without in-handler checks become browser-reachable without login.

Full register rows with lifecycle status: `Docs/review/FINDINGS_REGISTER_2026-08-31.md` Part 4f.

### 2.3 Parallel-wave process artifacts (staged/unstaged docs, read-only)

- **Staged `Docs/reviews/motto_review.md`** — regenerated 2026-09-06T09:18Z with a full-suite receipt of **3,876 passed** ("after fallout processing"), register validator clean at 145 rows, F-30…F-40 remediated with F-36/F-37 honest partials, "I-1/I-2 remaining with anchors", and corporate_policy confirmed fixed by the parallel agent. The session-start staged hooks drift (`scripts/hooks/*`) no longer diffs against HEAD — no residual hook change.
- **Unstaged `Docs/review/TRAVEL_OS_ARCHITECTURAL_AUDIT_PER0442_2026-09-03.md` §5** — the parallel wave's closure claims for Options A–D. Caution: several claims overstate reality vs the verified adapters ("queries GDS/NDC inventory", "provisions single-use Stripe VCC", "tickets GDS PNR" — all simulated adapters with no network; the workbench "1-click execution" is the F-42 honesty regression). The test receipts (fulfillment lifecycle 100%, journey-graph 2/2, agent lease 7/7, ruff/tsc clean, both ports 200) are plausible but were not re-executed in this pass; treat §5 as the wave's own attestation, not independent verification.

---

## 3. Loops & cadences — no structural change

No new polling/worker/retry loops landed. The §6 loop table of the parent map remains accurate; the escalated-queue endpoint is poll-on-demand (no loop), and fulfillment is request-scoped. The nearest new *logical* loop is the needs-information consolidator, which is a derived read-model recompute, not a scheduler.

## 4. Test baseline (as-recorded, not re-run here)

Baselines on record, newest last: 3,206/10 (2026-08-30 CI-identical) → 3,760/10 (server-present, `Docs/review/EXECUTION_STATUS_2026-09-04.md`) → 3,818/0 (register wave, 2026-09-05) → **3,876 passed** (staged `motto_review.md` receipt, 2026-09-06, "after fallout processing"). The two new uncommitted test files are `require_postgres`-marked contract tests and were not executed in this read-only pass.

## 5. Corrections to apply to the parent map at its next revision

1. §2.3/§8: hybrid LLM decision engine is **default ON** now (`USE_HYBRID_DECISION_ENGINE=1` in Dockerfile:89, Dockerfile.spine_api:11, docker-compose.yml:21, .env.example:67, CI backend-tests) — "orphaned/default off" is stale.
   - **CORRECTION 2026-09-14 (ADR-008 §7 item 2 ratification supersedes this entry):** the ON posture above was itself the envelope accident (image-level ENV silently overrode the code default). Ratified posture is **declared-off in every serving envelope** (Dockerfile, Dockerfile.spine_api, fly.toml, compose, render all explicit `0`; CI keeps `1` as the deliberate eval envelope; startup rung log at `spine_api/server.py` records the effective mode + credential state). Opt-in is envelope-level review, never image-level; promotion to ON is gated on the X-09 PII-egress decision plus a KDD benchmark (champion F1 0.808, ₹0.09–0.28/run).
2. §3.1: startup assertions gain `SPINE_API_IDEMPOTENCY_BACKEND=sql` (prod/staging) and placeholder-blocking `PROPOSAL_SIGNING_KEY`; 83 router mounts (was 81); new mounted routers `logistics`, `fulfillment`, `itinerary_export`, durable `agent_lease`, plus `journey_graph.public_router`.
3. §3.4: key tables gain `idempotency_keys` (with `fencing_token`) and `agent_leases`; status-transition invariant + capped `status_history` now guard every trip write.
4. §3.2/§4.1: surfaces gain `(agency)/platform-admin/product-b`, `/api/stats` BFF route, LifecycleChip on trip layout, FreshnessCard on decision page (uncommitted), `/api/stats` backend route.
5. §5.3: money-flow surfaces (distribution, settlement, irops) return `PREVIEW_ONLY` reality-tier metadata with `provider_connected: false` — preview contract, not functional sandbox flows.
6. §7: CI adds findings-register lifecycle gate + generated-types drift gate; backend tests run with the hybrid engine env.
7. §5.1/§1: terminal vocabulary is `booked/delivered/completed/cancelled` with `active` as first-class intake-complete state (F-33/F-34 closed).
8. §8: honesty boundaries are now UI-test-enforced (`SimulatedBadge` + `simulated-panels-honesty.test.tsx`), with backend reality-tier self-labeling — but the gate has a hole: no ProposalCompilerPanel coverage (F-42).
9. §4.3: the BFF route-map allowlist no longer gates `/api/v1/*` or `/api/public/*` — `next.config.mjs:17-29` rewrites those prefixes straight to the backend (F-43); the allowlist only binds the remaining BFF paths (`/api/stats`, `/api/auth`, inbox, …). Auth is cookie-based end-to-end (`auth.py:58-59` cookie fallback), so JWT-enforced endpoints still authenticate on the rewrite path.
10. §7/§8: the launch-audit "fabricated success pages" are fixed in this commit — `corporate/offsites` and `intake/fast` now render explicit unavailable/no-submission alerts instead of fake data (`Docs/review/LAUNCH_READINESS_AUDIT_PER0100_2026-09-02.md` items partially addressed).

## 6. Pointers

- Parent map: [CODEBASE_FEATURES_FLOWS_LOOPS_MAP_2026-09-03.md](CODEBASE_FEATURES_FLOWS_LOOPS_MAP_2026-09-03.md) · Register: `Docs/review/FINDINGS_REGISTER_2026-08-31.md` (Part 4e remediation addendum 2026-09-05, new Part 4f 2026-09-06) · Lifecycle contracts: [TRIP_LIFECYCLE_STATE_CONTRACTS_2026-09-02.md](TRIP_LIFECYCLE_STATE_CONTRACTS_2026-09-02.md) · ADR-007: `Docs/architecture/adr/ADR-007-PRODUCT-B-SCOPED-ANALYTICS_2026-09-03.md` · Launch posture: `Docs/LAUNCH_STATUS.md` (NO-GO public / conditional invite-only pilot).
