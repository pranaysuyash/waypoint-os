# Open Work Roadmap — consolidated implicit/explicit findings & tasks (2026-09-08)

**Purpose:** single navigator for everything still open, sorted by class (EXPLORE → research/document first · IMPLEMENT → canonical-path code · DECIDE → owner-gated) with priority and source citations. This file NAVIGATES; it does not replace the canonical status stores:
- `Docs/review/FINDINGS_REGISTER_2026-08-31.md` (canonical)
- `Docs/review/FINDINGS_TASKS_IMPLICIT_EXPLICIT_REGISTER_PER0443_2026-09-07.md` (Parts G–L: AT rows, verification, commit receipts)
- `Docs/review/IMPLEMENTATION_PLAN_PER0443_2026-09-07.md` (Waves 0–4)
- `Docs/LAUNCH_STATUS.md` (NO-GO public / conditional invite-only)

**Committed baseline:** `6c7c824` + `b1d706d` (durability, honesty-copy, AT-20/21, scope-gate fix). Everything below is OPEN as of this file's date.

**STATUS UPDATE (2026-09-08, later same day — most of this roadmap is now DONE):**
- Wave B: B1 E-D spec -> `Docs/architecture/MEMORY_READ_PATH_SLOT_SPEC_2026-09-08.md`; B2 E-E ADR -> `TIMELINE_AS_EVIDENCE_ADR_2026-09-08.md`; B3 E-G endgame -> `DURABLE_STORE_ENDGAME_2026-09-08.md`; B4 E-B reconcile -> `FAILURE_TAXONOMY_RECONCILIATION_2026-09-08.md` (live 8-class enum ratified, design doc superseded-vocab header added). B5 SOS copy was already humanized in Part K.
- Wave A: A1 DONE — FlightStatusAgent evaluates the stored graph's disruption ripple on medium/high risk and escalates high risk to the human-review queue (`review_status=escalated, escalation_reason=flight_disruption`); no stored graph -> abstains; 3 tests (`tests/test_flight_status_disruption.py`). A3 DONE — background confirmation writer now uses canonical `rls_session(agency_id)`; live-SQL proof `recorded: true`; **found+fixed a pre-existing bug**: record/verify/void emitted `emit_event(metadata=...)` instead of `event_metadata=` so those lifecycle events never fired. A5 RECLASSIFIED — price-lock is preview-only by design (persists nothing); idempotency applies only when a real rate source lands (no dead code added). **A6 DONE (2026-09-11)** — audit re-verification found negotiation/charter/yield/stress/logistics already fully tier-labeled; the single genuinely unlabeled surface (`yield_benchmark.py /benchmark/simulate`) now carries TierMetadata + a `yield_benchmark` FEATURE_REGISTRY entry (deterministic_preview). **A2 DONE (verified 2026-09-11)** — the legacy `src/logistics/irrops_healer.py` module + its test were removed in `0becb27` and the canonical calculator lives at `spine_api/services/passenger_rights_claims.py`; the remaining duplicate (inline `_calculate_eu261_compensation` + carrier-prefix math in `spine_api/routers/passenger_rights.py`) is now consolidated: the router delegates to canonical `evaluate_statutory_compensation` (contract-preserving, carrier set preserved exactly) and the inline arithmetic is deleted (`tests/test_a2_a4_canonical_consolidation.py`). **A4 DONE 2026-09-11 (data-minimization form)** — the fulfillment writer no longer persists `vcc_card_id`/`e_ticket_number` into the plaintext trip JSONB lane (durable encrypted copy already lives in `booking_confirmations` via `try_record_fulfillment_confirmation`); reader audit found zero readers of those fields on the trip lane; live check found **0 legacy affected rows** (trips table empty), so no migration was needed; guard tests in `tests/test_a2_a4_canonical_consolidation.py`. A7 remains open (sequenced per Wave 3).
- Wave B6/B7: orientation research -> `Docs/exploration/PROVIDER_CONNECTOR_AND_INDIA_PAYMENTS_RESEARCH_2026-09-08.md` (orientation tier — search quota exhausted mid-research; live vendor verification owed).
- **OPEN TASK B6/B7-upgrade (2026-09-09):** upgrade the orientation-tier research to a live-verified DECIDE package. Owner selected this as an open task. Scope: (1) live vendor verification — Mystifly sandbox onboarding + API contract probe (flight-order round-trip shape vs our adapter contract), TBO hotel+flight one-wallet economics; (2) India rails — Razorpay mandate/webhook contract vs PaymentMandateLedger CAS, GST invoicing requirement; (3) output: updated `Docs/exploration/PROVIDER_CONNECTOR_AND_INDIA_PAYMENTS_RESEARCH_2026-09-08.md` from "orientation" to "verified" tier + DECIDE package for Wave C. Blocked only by web-search quota (resets 2026-10-06) and owner/Ravi answers on corridors + volume + GST needs.
- Wave B8: blocked on Ravi's conversation.

### FOR LATER — research/exploration deferred (owner directive, 2026-09-09)

Research-type items are explicitly parked; implementation tasks proceed without them:

- **B6/B7-upgrade** (live vendor verification: Mystifly/TBO sandbox probes, Razorpay contract mapping) — FOR LATER until web-search quota resets (2026-10-06) and owner/Ravi answer corridors + volume + GST.
- **B8 stakeholder-requirements capture** — FOR LATER until the Ravi conversation is confirmed/held.
- **E-H adversarial lane activation** (A7 sub-item) — the activation design needs a research pass on corpus-to-lane wiring before code; parked with A7.
- **Hosted evidence (L8)** — FOR LATER until deploy authorization.

Everything in Wave A (A1–A7) and the L7-authenticated walk is implementation work and proceeds.
- Gates at close: 111 backend (focused expanded) + 1,371 frontend / 183 files tests passing; scoped mypy 21 files clean; ruff/tsc clean.

---

## Wave A — P0/P1 IMPLEMENT (real-world blockers, canonical paths, sized)

| # | Task | Findings | Size | Notes |
|---|---|---|---|---|
| A1 | FlightStatusAgent high-risk → `evaluate_disruption` on stored graph → escalated queue item (R2, no auto-rebook) | 2.3b, R-12 | M | `src/agents/runtime.py:2640-2700` is snapshot-only; engine + sanitizer already honest |
| A2 | Supersede `src/logistics/irrops_healer.py` AFTER migrating its unique EU261/UK261/US-DOT compensation calculator into the passenger-rights canonical path (AT-17 operator case) | 2.3c, AT-17 | M | calculator is the only one in the repo — merge before delete |
| A3 | AT-04 completion: fulfillment's SQL confirmation write works only in request context; background/script writers hit `booking_confirmations` RLS → recorded:false. Give the writer an agency-scoped session (or service role) and verify | AT-04, Part J #3 | M | honest-degradation path already proven live |
| A4 | Encrypt `booking_confirmation` at rest on SQL (currently plain inside `analytics._extra`; contains VCC ids) — encrypted fold or dedicated column + migration | Part L.5 | M-L | encryption-migration lane, A-20 custody |
| A5 | `Idempotency-Key` header also on price-lock persist-when-real and any remaining side-effectful router | PA-40 residual | S | pattern exists in fulfillment router |
| A6 | Wave 1.4: TierMetadata on negotiation/charter/yield/stress/logistics-export routers | E-F leftovers | M | per SIM_SURFACE_DISPOSITION_REGISTER |
| A7 | Wave 3 eval/observability batch: audit-chain verify + re-anchor + one `/api/audit` store (PA-19, needs E-E); `usage_events` rollup (PA-20, needs E-C); autoresearch live-or-labeled lineage (PA-11); closed-loop real fixture re-execution (PA-21); eval cost/latency/human dims (PA-34); adversarial lane activation (E-H — corpus already seeded) | Wave 3 | L total, each S-M | sequenced in IMPLEMENTATION_PLAN_PER0443 Wave 3 |

## Wave B — EXPLORE (research + document BEFORE code)

| # | Exploration | Produces | Blocks |
|---|---|---|---|
| B1 | **E-D memory read-path slot spec** — where preferences may rank QUESTIONS, never inventory | `Docs/architecture/MEMORY_READ_PATH_SLOT_SPEC_*.md` | PA-18 wiring |
| B2 | **E-E timeline-as-evidence ADR** — one id-space for the decision stream | observability ADR | PA-19 audit-chain, operator UI |
| B3 | **E-G durable-store endgame** — SQL-only migration design retiring the file store; also closes the NBTA residual window and the fulfillment graph-clobber window via store-level priority merge | SQL migration design | L4, AT-04 completion, NBTA full closure |
| B4 | **E-B reconcile** — 7-class design vs shipped 8-class `FailureClass` enum | one ratified enum | recovery routing |
| B5 | **AT-21 residual traveler-copy sweep** — SOS/notifications surfaces, `itinerary-checker` full render test, `booking-collection` copy assertions | copy test coverage on all 5 traveler surfaces | AT-21 enforcement |
| B6 | **Provider-connector research** (consolidator/GDS: TBO, Mystifly, Amadeus self-service) — which single integration unblocks real quotes for a proprietor agency | connector decision doc feeding R-09/R-10 DECIDEs | real inventory (demo endpoint exists) |
| B7 | **India payment rails research** (Razorpay/UPI vs Stripe) for `financial_ops` + mandate model | India-path DECIDE doc | AT-15 mandates default-on |
| B8 | **Stakeholder-requirements capture** — log Ravi's answers (demo plan §5 questions) into `Docs/exploration/` mapped to DECIDE rows | requirements note | D-01..03, WhatsApp channel, commission model realism |
| B9 | **Live competitor refresh for the wedge-fate decision** (RDA EX-01 research debt, kept open for later per Pranay 2026-09-09) — BLOCKED: web-search quota exhausted on both backends until **2026-10-06 17:07 IST**; retry then with: "AI itinerary checker app" · "travel plan risk checker tool" · "trip stress test tool" · "Spotinga" · "Fortrip". Merge findings into `Docs/review/WEDGE_FATE_DECISION_PACK_RDA_2026-09-08.md` §Research-debt | refreshed competitive table annexed to the decision pack | sharpens C7 (wedge fate) before any public commitment |

### Training-session source register (2026-09-09) — TS-01…TS-06 — **EXECUTED same day**

From the owner's ChatGPT systems-training session (evidence-mapped register + raw transcript at `Docs/exploration/CHATGPT_SYSTEMS_TRAINING_SESSION_FINDINGS_2026-09-09.md`). All concepts were verified against code before registering; 14 of ~20 taught concepts are already implemented (register §2). **Execution receipt (2026-09-09, uncommitted): TS-01 + TS-04 implemented with tests and 4 review cycles (P0 + 3×P1 found and fixed — see `Docs/review/TS_REGISTER_EXECUTION_HANDOFF_2026-09-09.md`); owner confirmed the layover policy → `LONG_LAYOVER_NO_HOTEL_` soft operator suggestion implemented (never a block); TS-02/03/05/06 exploration docs delivered; full backend suite green 4,250/0 (44 skipped), scoped mypy clean, repo ruff clean; route-parity snapshots regenerated for the parallel checker-wave routes.**

| # | Class | Item | Status |
|---|---|---|---|
| TS-01 | IMPLEMENT | Hard itinerary-feasibility validators in `src/decision/constraint_engine.py`: ground-access transfer buffer (hard w/ explicit requirement, advisory w/ heuristic default), uncovered-first-night (interval coverage + return-leg/transit discriminators), long-layover soft advisory (owner-confirmed), hotel occupancy vs party (first `CAPACITY_ROOMING` producer), ticket-pax mismatch, product age rules — all abstain without declared data | **DONE** — `tests/test_constraint_engine_feasibility.py` (17 tests) |
| TS-02 | EXPLORE (park w/ B6/B7) | Quote-freshness / recheck-before-execution contract | **DOC DONE** — `Docs/exploration/TS02_QUOTE_FRESHNESS_CONTRACT_2026-09-09.md`; recheck engine deferred to live-provider lane |
| TS-03 | EXPLORE → IMPLEMENT | Multi-modal intake completion (customer-path images/PDF via existing vision lane, voice ASR DECIDE, SSRF-gated URL) | **S1 DONE 2026-09-10** — attachment envelope + storage-lane persistence + trip manifest (8 tests); S2 extraction-merge + S3 injection fixtures deferred to marketplace lane (seams named in register) |
| TS-04 | IMPLEMENT | Per-field provenance actor vocabulary: operator/customer/system/tool/provider; commercial precedence provider>operator>tool>customer; client-claimed internal roles fold to operator | **DONE** — `tests/test_field_merge_actor_vocabulary.py` (16 tests incl. trust-boundary guard) |
| TS-05 | EXPLORE (park) | Pipeline parallel orchestration / speculative execution design note | **DOC DONE (parked)** — `Docs/exploration/TS05_PARALLEL_ORCHESTRATION_DESIGN_NOTE_2026-09-09.md`; unpark trigger = live provider >2s latency |
| TS-06 | EXPLORE | Candidate route-structure generation + incremental refinement (gap confirmed: plan-candidate is a single snapshot; `BRANCH_OPTIONS` has no producer) | **DONE 2026-09-10** — `src/decision/route_structures.py` enumerator + open-jaw scoring + decision.py Phase-12 enrichment (additive; state unchanged) + DecisionTab dual-shape render fix (14 tests) |
| TS-07 | EXPLORE | Operation-keyed field requiredness (`required_for` + `blocked_operation` — beyond the two-tier INTAKE_MINIMUM/QUOTE_READY model) | **DONE 2026-09-10** — FIELD_REQUIRED_FOR + classifier + question_priority_order; consumer: prioritized/annotated follow-up questions (9 tests) |
| TS-08 | EXPLORE (feeds E-8) | Component-state aggregation (`BOOKED` / `BOOKING_EXCEPTION` trip verdict over journey-node commitment_status) + explicit `UNKNOWN` idempotency outcome (timeout ≠ failed; safety machinery exists, vocabulary absent — `idempotency.py:44-48`, `fulfillment.py:224-229`) | **DONE 2026-09-10** — UNKNOWN status/resolve/TTL-exemption both backends + fulfillment 504/409 classification + aggregate_commitment + `commitment_verdict` on JG GET (20 tests); E-8 persisted-state wiring remains |
| TS-09 | EXPLORE (fold into B6/B7) | Operation retry-safety registry (`SAFE_RETRY / IDEMPOTENT_KEY_REQUIRED / MANUAL_ONLY` on tool/provider contracts; today free-text prose only, `runtime.py:182`) | OPEN — vocabulary lands with live providers |

Owner-learning (not agent work): TS-L1 **CLOSED 2026-09-10** — tutor exercise answered (8/10); corrected four-question contracts for NEEDS_INFORMATION / BOOKING_IN_PROGRESS promoted as a dated addendum to `TRIP_LIFECYCLE_STATE_CONTRACTS_2026-09-02.md` (E-8 spec input); TS-L2 open (next tutoring module: queues/orchestrator/HTTP semantics — repo artifacts as worked examples).

**Second-session register (2026-09-10; transcript `Docs/exploration/CHATGPT_SYSTEMS_TRAINING_TRANSCRIPT_2026-09-10_RAW.md`, register §6):** V-15..V-18 validated (idempotency marker/replay machinery, two-tier stage validation, retry/queue machinery all exist); new gaps:

> **De-duplication note (2026-09-11, FND-0266):** TS-07/TS-08/TS-09 below are the SAME items as the first-session register above, restated from the second transcript's gap list. Status authority is the first-session register: TS-07 **DONE 2026-09-10**, TS-08 **DONE 2026-09-10** (E-8 persisted-state wiring remains), TS-09 **OPEN**. Do not re-execute from this table.

| # | Class | Item | Size | Note |
|---|---|---|---|---|
| TS-07 | EXPLORE | Operation-keyed field requiredness (`required_for` + `blocked_operation` — beyond the two-tier INTAKE_MINIMUM/QUOTE_READY model) | S-M | doubles as the E-D question-priority ranking input. **Superseded by first-session row: DONE 2026-09-10** |
| TS-08 | EXPLORE (feeds E-8) | Component-state aggregation (`BOOKED` / `BOOKING_EXCEPTION` trip verdict over journey-node commitment_status) + explicit `UNKNOWN` idempotency outcome (timeout ≠ failed; safety machinery exists, vocabulary absent — `idempotency.py:44-48`, `fulfillment.py:224-229`) | M | promotes dormant BOOKING_IN_PROGRESS; contracts-doc addendum 2026-09-10 is the spec. **Superseded by first-session row: DONE 2026-09-10** |
| TS-09 | EXPLORE (fold into B6/B7) | Operation retry-safety registry (`SAFE_RETRY / IDEMPOTENT_KEY_REQUIRED / MANUAL_ONLY` on tool/provider contracts; today free-text prose only, `runtime.py:182`) | S | enforcement lands with live providers |

## Wave C — DECIDE (owner-gated; research exists or probes ready)

| # | Decision | Source |
|---|---|---|
| C1 | ADR-008 §6 ratification (autonomy rungs; hybrid default-off; mandates stay off until ratified) | Wave 0.1 |
| C2 | D-01 duration / D-02 flights-inclusive / D-03 country-vs-city product contracts | probes ready (2026-09-04) |
| C3 | Inventory model: R-09 signup posture, R-10 business model | inventory register |
| C4 | C-01 Frontier/Council label-vs-wire · C-02 judge/orphans · C-03 router-vs-`routing_health` implement-or-rename · C-04 SLM waits on E-C | PER-0700 |
| C5 | WhatsApp channel + invoice/GST + commission-model realism (from Ravi discovery) | demo plan §5 |
| C6 | E-B vs live enum ratification (see B4) | contested since 09-07 |
| C7 | **RDOC wedge decisions — DECIDED 2026-09-09** (WOBS Part 3.2): build the full open verifier + marketplace ("we build it"); **nothing gates on Ravi meetings** (Ravi = first receiver when available; demand-capture replaces acceptance-first); dream-shelf structural items pulled into the build (structured findings, content-addressed reports, server-seal, declare-radio attribution); Atlas publishes when corpus volume exists; Warranty Layer waits for multiple parties. Phased build (P1 Verifier / P2 Marketplace interaction / P3 Compounding) in WOBS Part 3.2. B9 competitor refresh remains as sharpening, not a gate. | `Docs/exploration/WOBS_AGENCY_BRANDED_CHECKER_2026-09-09.md` Parts 0–3.2 |

## Wave D — Launch envelope (owns L1–L8; do not mix with product waves)

Sequence per launch plan: E-G → SQL projection (L4) → platform choice (L1) → backup/restore drill (L2) → remaining sim/provider surfaces (L3) → legal (L6) → browser smoke including companion + authenticated workbench walk (L7 — partially proven 09-07/08) → authorized snapshot (L8). Public/paid remains NO-GO.

## Residuals consciously accepted (documented, not lost)

- NBTA verify-and-heal loop: post-verify clobber window heals on next writer; full closure needs store-level priority merge (B3).
- Fulfillment graph CAS fallback: plain-write after bounded contention prioritizes booking durability; window documented (Part J #5).
- PA-40 on fulfill is belt(braces): engine marker + provider-key determinism close crash windows; live Stripe needs native Idempotency-Key header at integration time.
- `motto_review.md` self-refreshes and trails one commit by design.
- Codex usage-limit retry automation (one-shot) already fired; Parts H/J filed.

---

**Rule of thumb for the next agent:** pick from Wave A top-down; if a task says "needs E-*", do the Wave B item first. Never start a parallel router/store/healer — extend the canonical path. Verify with `scripts/run_backend_tests.sh` + scoped mypy + frontend vitest before claiming done.


### Mimosa L3 commit-block findings (2026-09-09, registered — commit bd1c371+ gated)

The workspace security scanner hard-blocked the staged Wave-A receipts commit (referred to below as "Wave-A2/A6/A8"; **correction 2026-09-11: "A8" is not a defined Wave-A item — the Wave A table ends at A7. The reference meant the staged A2/A6 receipt batch from Part M**):

| Finding | Severity | Disposition |
|---|---|---|
| Hardcoded credential-shaped literals in auth test fixtures (`proxy.test.ts`, `api-client.auth.test.ts`) | high (scanner) | **FIXED in working tree** — literals replaced with named synthetic constants (FIXTURE_ACCESS_TOKEN/FIXTURE_REFRESH_TOKEN); 18 auth tests pass; staged, awaiting gate-pass |
| SSRF: `frontend/src/app/api/inbox/route.ts:17,52` | high | OPEN — route fetches `SPINE_API_URL` + user query; server-side allowlist needed. P1 (same-origin admin surface, but URL is env-derived + query passthrough) |
| SSRF: `frontend/src/app/corporate/offsites/page.tsx:17-18` | high | OPEN — server component fetches `NEXT_PUBLIC_API_URL` + hardcoded company_id; P2 (env-derived, no user input in URL path shown) but needs verification |
| SSRF: `frontend/design-lab/inspect-app-dna.py:266` | high | OPEN — dev-only design-lab script; exclude from production scan scope or fix |
| Remaining Mimosa highs (of 30 flagged) | mixed | full re-scan required after fixes; do not treat this list as exhaustive |

**Gate status:** commit blocked until the two SSRF surfaces are remediated (allowlist/URL-construction hardening) and the scanner re-run passes. The scanner's own caveat stands: this coverage was incomplete — run the full Mimosa audit per its recommendation before next release claim.

**Wave A2/A6 execution receipts are complete and tested** (see Part M / roadmap progress) but sat uncommitted behind this gate together with the rest of the staged tree. (2026-09-11: A6 is now also re-verified DONE in-tree — see the STATUS UPDATE above.)
---

## Addendum (2026-09-09) — Visa & Immigration document audit (random seed 20260909)

Random-document audit of `Docs/personas_scenarios/AREA_DEEP_DIVE_VISA_IMMIGRATION.md` → canonical store: `Docs/reviews/VISA_IMMIGRATION_DOCUMENT_AUDIT_2026-09-09.md`. Navigator summary:

- **IMPLEMENT — DONE same session (all tests green, full suite 4,161/0):** VA-01 US-default removal on visa radar request, VA-02 honesty rebadge ("Real-Time"→heuristic scope), VA-03 `registry_match` fallback flag, VA-04 corpus seeds SC-960/SC-961 (+`tests/test_visa_scenario_seeds.py`), VA-05 vaccination category marked dormant, **VA-06 visa-extractor negation inversion (both directions wrong — found during execution)**, **VA-07 "No"-as-destination leak (GeoNames city collision)**.
- **EXPLORE — DONE (docs):** VE-01 data-source landscape (`Docs/exploration/VISA_DATA_SOURCE_LANDSCAPE_2026-09-09.md`), VE-02 transit-visa design (blocked on VD-02), VE-04 scenario-graduation protocol (**owner decision requested**), VE-05 passport-PII flow audit.
- **DECIDE — open:** VD-01 `visa_workflow.py` orphan (badge PREVIEW_ONLY recommended), VD-02 live visa data source, VD-03 invitation-letter workflow, VD-04 courier/embassy manifest. All deferred off the marketplace-pilot critical path per PER-0100 lens.

---

## Addendum (2026-09-10) — Mimosa full-scan remediation wave COMPLETE (closes the scanner gate above)

Full receipts in the PER-0443 register **Part O**. The 2026-09-09 gate table's OPEN rows are now closed:

- **inbox route SSRF (P1): CLOSED** — all 16 BFF API routes + `bff-auth.ts` + `server-auth.ts` + agency layout now build URLs through the canonical validated `spineUrl()` from `proxy-core.ts` (http(s)-only, no embedded credentials, fails loudly in production).
- **offsites page SSRF (P2): FALSE POSITIVE, closed with reasoning** — `'use client'` component using `NEXT_PUBLIC_API_URL` (the deployed-stack variable); importing server-only proxy-core into a client bundle is a build hazard. A client-safe helper is registered as future work.
- **design-lab SSRF: FALSE POSITIVE class** — dev-only tooling fetching explicit dev URLs.
- **Credential-shaped test literals: already fixed** (prior session) and the 4 remaining script credentials fixed this wave (synthetic fixtures + `WAYPOINT_TEST_PASSWORD` env).
- **Beyond the gate table:** canonical SSRF guard (`src/security/url_guard.py`) wired into settings_health/live_tools/alert_service/entity_checks; canonical path guard (`src/security/path_guard.py`) wired into persistence/draft/cache/override/memory stores; **analytics fabrication class eliminated** (random.uniform response times, invented stage timings, 4.5 CSAT baseline, trips×$15k pipeline value, hardcoded fake bottleneck — all now real-or-None with FE 'N/A' guards; hostile test coverage rewritten); usage_store PRAGMA interpolation removed.

Verification: FE 183 files / 1,374 tests + tsc clean; BE full suite green (receipt in Part O); ruff + scoped mypy clean. Post-fix Mimosa verification scan pending — run before the next commit gate claim.
