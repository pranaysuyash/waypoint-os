# Findings & Tasks Register — PER-0443 Companion (2026-09-07)

**Status:** companion addendum; **NOT** a second lifecycle authority  
**Canonical status store:** `Docs/review/FINDINGS_REGISTER_2026-08-31.md`  
**Parent audit:** [PERSONA_AUDIT_PER0443_AGENTIC_TRAVEL_SYSTEMS_ARCHITECT_2026-09-07](PERSONA_AUDIT_PER0443_AGENTIC_TRAVEL_SYSTEMS_ARCHITECT_2026-09-07.md)  
**Plan:** [IMPLEMENTATION_PLAN_PER0443_2026-09-07](IMPLEMENTATION_PLAN_PER0443_2026-09-07.md)  
**Identity for new rows:** `persona-audit-per0443-2026-09-07::AT-nn`. Promote into the canonical register only by additive append with in-row evidence (findings lifecycle).

Action classes: **IMPLEMENT** · **EXPLORE** · **DECIDE** · **RECORD**.  
Alignment: **1P** first-principles · **LT** long-term · **DOC** doctrine (§2 truth / §11 engineering / §12 AI-output / §13 claim reality) — ✅ aligned · 🟡 partial · ❌ violated.

---

## Part A — New implicit findings (AT-01…AT-19)

### A.1 P0 — travel source of truth / traveler-facing claim reality

| ID | Finding | Evidence (Observed) | Implicit / explicit | Class | 1P / LT / DOC | Fix direction (and what “best” adds) |
|---|---|---|---|---|---|---|
| AT-01 | Journey graph is **not** canonical runtime state. `journey_graph_nodes` is read for hydration and written **only in tests**. Compiler returns a node *count*. Fulfillment builds an in-memory node and persists only `booking_confirmation`. | rg: writers = `tests/test_journey_graph_hydration.py`; reader `spine_api/routers/journey_graph.py:160`; `booking_fulfillment.py:250-277` | Implicit (docs treat JDG as OS) | IMPLEMENT | ❌/❌/❌ canonical path | Persist nodes+edges+confirmation codes on compile/fulfill. Trip status *derives* from graph. **Best:** one itinerary SSOT consumed by IROPS, companion, rights. **Extend** `src/schemas/journey_graph.py` — do not add a third graph store. Sharpens R-12. |
| AT-02 | Progressive commitment collapsed: no hold vs ticket. Sandbox `create_flight_order` returns ticketed; price-lock is preview-only; real `BookingConfirmation` SM unused. | `amadeus_sandbox_adapter.py` (TICKETED_CONFIRMED); `booking_fulfillment.py:243-277`; PA-06 preview | Implicit product claim of “fulfillment” | IMPLEMENT + DECIDE (when live GDS) | ❌/❌/❌ §12 | Node states `quoted \| held \| booked \| ticketed \| void`. Human R1 between hold and ticket. **Extend** confirmation SM + price-lock expiry fields. |
| AT-03 | Double-fulfillment: no refuse-if-`booking_confirmation` exists; lease is 60s fence, not once-booked; not on durable idempotency registry (PA-40). | `booking_fulfillment.py:109-329` — no existing-confirmation guard | Implicit | IMPLEMENT | ❌/❌/❌ §11 | 409 replay if confirmation exists; `Idempotency-Key` on fulfill. **Best:** unique `(trip_id, confirmation_type)`. |
| AT-05 | Traveler companion fabricates itinerary truth after PA-01 backend abstain. Fetch **without token**; fallbacks `'BA 178'`, `'006-2345678901'`, `'HTL-AMAN-88219'`, destination `'Tokyo & Kyoto'`, **ON TIME**; SOS is `setTimeout` 1.5s; any JSON 200 labeled live DAG. | `frontend/src/app/(traveler)/companion/page.tsx:92-181` | Implicit vs F-41 “fixed locally” | IMPLEMENT | ❌/❌/❌ §13 | Require token; render abstention; never invent PNR/status; SOS → durable event. **Extend** PA-01 public contract. |

### A.2 P1 — conflicting agents, wrong itinerary, authority

| ID | Finding | Evidence | I/E | Class | 1P/LT/DOC | Fix direction |
|---|---|---|---|---|---|---|
| AT-04 | Two confirmation truths: SQL `booking_confirmations` (void/evidence) vs trip JSON blob used by companion/fulfillment. | `confirmation_service.py` vs `booking_fulfillment.py:268-276` vs `companion/page.tsx:35-46` | Implicit | IMPLEMENT | ❌/❌/❌ | Fulfillment writes the table with `reality_tier`; blob is a projection. |
| AT-06 | IROPS does not operate on the traveler’s journey. Engine **builds BA178/DL490/Four Seasons** regardless of `trip_id`. Duplicate engine `src/logistics/irrops_healer.py` (tests only). `FlightStatusAgent` snapshots and does not call JDG. Router honesty is real — keep it. | `src/orchestration/irops_healer.py:70-80`; `spine_api/routers/irops_healer.py:61-129`; `runtime.py:2638-2706` | Implicit + explicit preview | IMPLEMENT + DECIDE (no auto-rebook) | ❌/❌/🟡 | One healer; input = persisted JDG; output = ripple + R1 tasks. Archive logistics healer via supersession. |
| AT-07 | `next_best_action` is CRM (`SEND_FOLLOWUP`, `CLOSE_LOST`). Nineteen agents stamp the same `operator_next_action`. Last supervisor pass wins. | `decision.py:1653-1682,2294`; `runtime.py` ~24 writes | Implicit (field name overclaims) | IMPLEMENT | ❌/❌/❌ | Derive NBTA from lifecycle + JDG + readiness + disruption, versioned. **Extend** BookingReadiness output + `trip-lifecycle` nextActions — one server projection. |
| AT-08 | Supervised “fleet” is a scan-and-stamp cron with excellent “do not book” contracts. RecoveryAgent is stuck-intake requeue, not IROPS. | `runtime.py:3233-3260`, `:2631`; `recovery_agent.py` header | Implicit naming | RECORD + DECIDE | ✅/🟡/🟡 | Ratify as R2 annotators in ADR-008. Keep contracts. Stop implying autonomous VCC/IROPS from this fleet. |
| AT-09 | Compile → accept → fulfill → void is not a chain of artifacts (compiler graph discarded; fulfill does not mint JDG or confirmation row; void unused). `holder_id` is free text. | AT-01 + `fulfillment` router holder_id | Implicit | IMPLEMENT | ❌/❌/🟡 | Artifact chain; R1; bind holder to agency principal. |
| AT-11 | Visa/docs not bound to the traveler. Radar uses `TEST_AGENCY_ID`, hardcodes `passport_expiry_date="2027-01-01"`, `travel_date="2026-09-01"`. DocumentReadinessAgent is honest (`legal_finality: False`) — keep. | `visa_radar.py:46-72`; `runtime.py:1029-1039` | Implicit | IMPLEMENT | ❌/❌/❌ | Checklist from real trip dates/nationality; block ready-for-booking as **operator tasks**. Do not ship a second radar. |
| AT-12 | Insurance is an internal agent pretending to be a carrier (formula 4.5/7.5/11.5% Allianz-class names; attach accepts typed `policy_number`). Persona forbids OrbitCover-as-Waypoint-agent. | Historical audit: `insurance.py:101-157`; September 8 correction: F-31 insurance research package | Implicit | DECIDE + IMPLEMENT honesty | ❌/❌/❌ | Corrected 2026-09-08: quote is an illustration; timing/eligibility remain unevaluated until adopted plan-specific rules and authoritative evidence exist. Attach should record canonical BookingConfirmation evidence with permissions and atomic audit/replay; a typed carrier ID is not carrier verification. Original blanket deposit-anchor and confirmation-ID prescription is superseded; see INSURANCE_TIMING_AND_ELIGIBILITY_CONTRACT_2026-09-05.md. |
| AT-13 | Loyalty balances fabricated (same UA 1K / Marriott Titanium / Hyatt Globalist, KTN, masked passport) for every `customer_id`. | `loyalty.py:102-137` | Implicit | IMPLEMENT + DECIDE | ❌/❌/❌ §13 + privacy | Fail-closed / badge sample; never invent FFN balances. |
| AT-15 | Money-path R1 unsigned. `SPINE_API_REQUIRE_PAYMENT_MANDATES` defaults `"0"`. ADR-008 unratified. | `booking_fulfillment.py:185-187`; ADR-008 §6 | Explicit proposed vs live | DECIDE then IMPLEMENT | 🟡/❌/❌ | Ratify ADR-008 rows 1 and 7; then default-on mandates. |
| AT-19 | `POST /evaluate` returns `"status": "success"` for client-posted DAGs; compiler still injects Blacklane/Belmond; request defaults `TRIP-LIVE-772` / IROPS `TRIP-LIVE-109`. | `journey_graph.py` evaluate; `proposal_compiler.py:21`; `irops_healer.py:106` | Implicit after honesty wave | IMPLEMENT | ❌/🟡/❌ | Evaluate loads stored graph; rename LIVE defaults; compiler must not name luxury inventory as real. Keep PA-25 share-token block. |

### A.3 P2 — composition, memory, entitlements

| ID | Finding | Evidence | Class | 1P/LT/DOC | Fix direction |
|---|---|---|---|---|---|
| AT-10 | Memory read-path is currently **safer than a naive wire**: stale preference must not auto-select inventory. ADR-008 §4.3 is correct **if** gated. | PA-18; `customer_memory.py` only consumer of `query_memories` | EXPLORE (E-D) | ✅ not wired / 🟡 / 🟡 | Memory may rank **questions**, never inventory. Write the slot spec before code. |
| AT-14 | Two group consensus engines; neither binds booking. `group_booking.py` is deposits, not preference. | `group_pareto` + `counterfactual.py` `/group-consensus` | DECIDE | 🟡/🟡/🟡 | One solver as decision support; per-pax accept is R0 on the proposal token. |
| AT-16 | Inventory freshness / fare hold never feeds the journey. TicketPriceWatchAgent alerts only. JDG `cancellation_deadline` unpopulated. | lifecycle contract; `runtime.py` TicketPriceWatch | IMPLEMENT after AT-01/02 | 🟡/❌/🟡 | Extend FreshnessCard + price-lock (already honest preview). |
| AT-17 | Passenger rights are a preview number, not a case. Router correctly nulls `amount_eur`; no R0 work item. | `irops_healer.py` sanitizer 77-80; `passenger_rights.py` unused by healer | IMPLEMENT | 🟡/❌/🟡 | Operator task from ripple; extend `passenger_rights_claims.py` + booking tasks. |
| AT-18 | Companion SOS and ON TIME badge replace durable ops state. | `companion/page.tsx:108-181` | IMPLEMENT | ❌/❌/❌ | SOS → durable crisis event + operator page. Notifications ≠ state. |

---

## Part B — Explicit (already-documented) findings: index

Not duplicated for status. Pointers for the next agent:

### B.1 PER-0700 still OPEN (do not re-discover)

PA-11 (P1 autoresearch) · PA-18 (memory write-only) · PA-19 (audit chain) · PA-22 (judge DECIDE) · PA-29…PA-37 · PA-39 · PA-40 · residual halves PA-13/15/20/21/23/08/12.

**Alignment of those residuals (this persona):** PA-11/19/21/34 violate “prove don’t assert”; PA-18 is travel-safe until E-D; PA-40 is the duplicate-booking enabler (pairs with AT-03); PA-35 theater pairs with AT-08.

### B.2 Owner-gated DECIDE (all open)

C-01 Frontier/Council · C-02 judge/orphans · C-03 router vs `routing_health` · C-04 SLM · D-01 duration · D-02 flights-inclusive · D-03 country vs city · inventory R-09 signup · inventory R-10 business model · inventory F-04 Git/commit split · ADR-008 §6 · PA-35/36/22.

### B.3 Launch blockers L1–L8

All still open (`Docs/LAUNCH_STATUS.md`). This persona’s AT-rows do **not** clear hosted/legal/backup gates.

### B.4 Explicit travel-domain rows already in the canonical register

| ID | How AT relates |
|---|---|
| R-12 IROPS trigger | AT-01/AT-06: trigger is missing *and* the healer uses a sample graph |
| F-41 / PA-01 | Backend abstain local; **AT-05** is the remaining traveler UI |
| F-42 / PA-25 | Panel honesty local; **AT-19** residual LIVE defaults + brand names |
| F-43 | Next rewrites vs BFF allowlist — still open; Wave 1 |
| F-21 / F-22 | Extraction/epistemic — Wave 2 product |
| F-04 payment mandates | Ledger local; default off = AT-15 |
| F-16 refunds | Still dead-end; R0 money |
| F-31 insurance | Honesty/auth; AT-12 is the fake-carrier overlay |

---

## Part C — Items that should be EXPLORED (research + document) before/instead of more code

| # | Exploration | Why 1P exploration precedes code | Produces |
|---|---|---|---|
| E-D | Memory read-path slot spec (still missing) | AT-10: wiring without a product answer makes preference into inventory | `Docs/architecture/MEMORY_READ_PATH_SLOT_SPEC_*.md` |
| E-E | Timeline-as-evidence ADR (still missing) | PA-04 emit landed without one id-space; PA-19/37 open | Observability ADR |
| E-G | Durable-store endgame (still missing) | File/in-memory substratum is the LT risk (L4) | SQL migration design |
| E-B-reconcile | Failure taxonomy design vs live 8-class enum | Contested; two taxonomies = change amplification | Ratified single enum |
| E-H | Adversarial lane **activation** | Corpus exists; reviewer illusion remains | First-run receipt |
| E-NBA | Next-best-travel-action projection spec | AT-07: 19 writers, no owner | **Written and coded 2026-09-07:** `Docs/architecture/TRAVEL_NEXT_ACTION_PROJECTION_2026-09-07.md` + `src/orchestration/travel_next_action.py` |
| E-commit | Progressive-commitment state model on JDG nodes | AT-02: hold vs ticket | **Written and coded 2026-09-07:** `Docs/architecture/PROGRESSIVE_COMMITMENT_JDG_2026-09-07.md` + `CommitmentStatus` on `JourneyNode` |
| D-01…D-03 | Duration / flights / country-city | Product contracts still unsigned | Ratification then extractor+API+UI together |

E-A (ADR-008), E-C (cost model), E-F (sim register) **exist** — ratify / apply, do not rewrite.

---

## Part D — IMPLEMENT list (canonical-path only)

Priority order is the plan. Do **not** start a parallel router.

| Slice | Findings | Extend |
|---|---|---|
| Persist JDG | AT-01, R-12 | `journey_graph` schema + trip update |
| Once-booked fulfill | AT-03, PA-40 | lease + idempotency registry + confirmation table |
| Companion honesty | AT-05, AT-18, F-41 | public journey-graph contract |
| IROPS on stored graph | AT-06 | `evaluate_disruption` + FlightStatusAgent + escalated queue |
| NBTA projection | AT-07 | BookingReadiness + lifecycle nextActions |
| Hybrid/docs drift | PA-03 residual | `.env.example`, `render.yaml` |
| F-43 BFF allowlist | F-43 | `next.config` rewrites |
| Visa bind | AT-11 | DocumentReadinessAgent |
| Insurance/loyalty honesty | AT-12, AT-13 | existing routers + badges |
| Counterfactual tier | AT-19 | load stored graph + RealityTier |

---

## Part E — What else can be done to make it the best (beyond defect fixes)

1. **Publish the autonomy ladder as an operator artifact** (ADR-008 rungs per action) — data already in `agency_settings` + gates.  
2. **One `verify_terminal(effect)` helper** (PER-0700 idea) used by fulfill, lead-save, and confirmation — environment-demonstrated completion.  
3. **NBTA in the operator UI next to decision rationale** — “do this next because rule Y, cost Z”.  
4. **Disruption cockpit:** stored-graph ripple + failure_class + escalated queue (not a new app).  
5. **Delete theater with supersession ADRs** (PA-35) so it cannot be reintroduced.  
6. **Memory trust-weighting at question-gen only** — gives GDPR machinery a purpose without booking from folklore.  
7. **Traveler companion as a read model of the JDG**, never a second itinerary author.

---

## Part F — Observed OS-layer unit (2026-09-07, uncommitted)

Authorized this conversation: start at the four OS-layer breaks (under-agentic JDG, over-agentic presentation, collapsed commitment, misnamed NBA). Owner gates still out of scope (ADR-008, Git, L1–L8, E-D memory, mandates default-on).

| ID | Local result | Evidence |
|---|---|---|
| AT-01 | Persist JDG on fulfill + compile; GET hydrates edges | `booking_fulfillment.py` `to_stored_payload`; `tests/test_booking_fulfillment_lifecycle.py` persist + `tests/test_proposal_compiler_e2e.py` quoted persist |
| AT-02 | Node `quoted\|held\|booked\|ticketed\|void`; compiler locked vs ticketed | `src/schemas/journey_graph.py`; compiler lock test |
| AT-03 | Once-booked replay, no second VCC | `idempotent_replay=True`; lifecycle replay test |
| AT-05 | Companion token + abstain; no BA 178 / ON TIME | `companion/page.tsx`; 3 honesty tests |
| AT-06 | IROPS stored graph or `ABSTAIN_NO_STORED_GRAPH` | `test_irops_healer_simulator.py`; fx IROPS abstain + stored preview |
| AT-07 | CRM vs travel NBA; priority merge | `tests/test_travel_next_action.py` weather cannot clobber disruption |
| AT-11/12/13/19 | Visa abstain; insurance/loyalty honesty; evaluate/counterfactual stored-or-abstain | capability batch + counterfactual tests |
| AT-04, AT-08, AT-10, AT-14–17, AT-15 | Unchanged | SQL confirmation, fleet RECORD, E-D, group DECIDE, mandates, freshness, rights |

S2 receipts (2026-09-07, local, not hosted): backend focused 43 passed (`test_travel_next_action`, fulfillment lifecycle, IROPS simulator, fx IROPS, counterfactual, compiler e2e, journey graph, capability batch, hydration) + 66 agent/decision contract; frontend honesty 5/5 (compiler + companion); ruff clean on touched OS-layer files. Full-suite baseline and Git remain unrun / unauthorized.

---

## Part F — Alignment roll-up

| Bucket | Count | Notes |
|---|---|---|
| New AT rows | 19 | 4 P0 · 11 P1 · 4 P2 |
| 1P ❌ | 14 | Journey/commitment/duplicate-book/companion/IROPS-target/NBA/visa/insurance/loyalty |
| 1P ✅ or 🟡 | 5 | Fleet contracts, memory-not-wired, IROPS sanitizer, rights-not-auto-paid, intake gates |
| LT ❌ | 12 | Nothing composes without persisted journey |
| DOC ❌ (§13) | Companion, loyalty, insurance, LIVE defaults, invented scores | Honesty wave did not finish traveler UI |

No AT row recommends a new duplicate system. Every IMPLEMENT line names an existing primitive to extend.

---

## Part G — Independent verification + AT-20 (2026-09-07, second session)

**Context:** owner asked for a fresh persona-driven audit pass with a stakeholder demo ("Ravi", proprietor travel agent) this week. This session did **not** redo Parts A–F; it independently verified them, audited the stakeholder demo path, and filed one new finding. Full trace: `Docs/review/SESSION_EVIDENCE_CONSOLIDATION_DEMO_READY_2026-09-07.md`. Demo plan: `Docs/review/RAVI_STAKEHOLDER_DEMO_PLAN_2026-09-07.md`.

### G.1 Verification of Part F receipts (Observed, rerun from a clean shell)

| Claim | Verdict | Evidence |
|---|---|---|
| Focused backend suites | ✅ 43 passed in 6.76s (dev-server-on-:8000 warning noted per F-19) | this session rerun |
| Frontend honesty vitest | ✅ 16 passed → **19 passed / 4 files** after AT-20 test added | this session rerun |
| C1 companion token + abstain, no fabricated fallbacks | CONFIRMED (caveats: SAMPLE-labeled demo mode content; demo SOS telemetry hardcodes Tokyo GPS `page.tsx:325`) | `companion/page.tsx:84-119,211-218,312-335`; backend gate `spine_api/routers/journey_graph.py:18-23,240-261` |
| C2 fulfill persist + once-booked replay | CONFIRMED | `booking_fulfillment.py:145-171` (AT-03 guard), `:281-334` (persist + read-back) |
| C3 CommitmentStatus + ticketed lock | CONFIRMED (nuance: `typing.Literal`, not an Enum) | `src/schemas/journey_graph.py:55,79,105-110`; `proposal_compiler.py:161-177` (all-or-nothing skip, not per-node merge) |
| C4 IROPS stored-graph-or-abstain | CONFIRMED | `src/orchestration/irops_healer.py:67-84`; router `:114-137` (`ABSTAIN_NO_STORED_GRAPH` in `PREVIEW_ONLY`) |
| C5 NBTA projection | CONFIRMED (nuance: zero `spine_api/` consumers — surfaces only via trip-record JSON) | `travel_next_action.py:12-48,113-176`; `decision.py:279-281,2296-2316`; `runtime.py:382` |
| C6 loyalty/insurance/counterfactual | CONFIRMED. visa_radar **PARTIAL**: `TEST_AGENCY_ID` fallback `:46`, `passport_country="US"` default `:42`, hardcoded 6-month validity `:102` | `loyalty.py:111-126`; `insurance.py:51,111-135,153,178,202`; `counterfactual.py:61,76,85` |
| C7 hybrid env `0` | CONFIRMED | `.env.example:67`; `render.yaml:27-28`; compose `:-0`; fly.toml unset |
| C8 `TRIP-LIVE` defaults | CLEAN (zero hits; only the honesty test asserting absence) | rg |
| AT-04 SQL BookingConfirmation | **OPEN** — no such table anywhere; blob write is the truth | `booking_fulfillment.py:305-312`; `persistence.py:698,100-104,708-716` |
| PA-40 Idempotency-Key→CAS on fulfill | **OPEN** — router accepts no header; replay guard + lease are the protection | `spine_api/routers/fulfillment.py:23-48`; registry wired only on `/spine/run` `server.py:1982-2068` |
| F-43 rewrites | **OPEN** | `next.config.mjs:17-29`; consumer `ProposalCompilerPanel.tsx:52`; auth skipped when `SPINE_API_DISABLE_AUTH` |
| 2.3b FlightStatusAgent→evaluate_disruption | **OPEN** (snapshot-only) | `runtime.py:2640-2700`; evaluate callers only `irops_healer.py:86`, `journey_graph.py:148` |
| 2.3c logistics healer supersession | **OPEN** (orphaned; BA178 at `:153`; only `tests/test_irrops_healer.py` imports) | `src/logistics/irrops_healer.py:153` |

### G.2 New finding AT-20 (P0 — traveler/stakeholder-facing §13) — **fixed this session**

Public proposal share page `frontend/src/app/p/[token]/page.tsx` fabricated a complete itinerary when the token was invalid/expired/unreachable: `?? 5030.0`, `?? 'Italian Grand Tour'`, `?? 'Italian Grand Tour: Rome, Florence & Amalfi'`, `?? 'Italy'`, `?? 8` Days / 7 Nights, `?? 'Our Valued Travelers'`, unearned "100% Verified & Protected" chip; fetch failure swallowed by an empty catch labeled "Fallback demo data if offline". Additionally the page used the Next 15/React 19 `use(params)` pattern against this repo's Next 14.2 + React 18.3.1 (`use` is not a function) — **the route crashed at runtime before rendering**, so the fabrication masked a crash. `rg 'use\(params\)' frontend/src` → no other callers (`booking-collection/[agencyId]/[token]` types `Promise<params>` but awaits — safe, cosmetic mis-typing to align opportunistically).

**Fix (uncommitted, this session):** honest abstention screen (`Proposal unavailable` + status-specific reason for 410/404/other/network + "ask your travel advisor for a fresh link"); all fabricated fallbacks removed; chip → "E-signature secured" (matches the real durable accept flow); Next-14 plain-object `params` signature restored. Test: `frontend/src/app/p/[token]/__tests__/public-proposal.honesty.test.tsx` (410-abstain, network-abstain, happy-path; asserts absence of every fabricated string). Evidence: honesty family 19/19 passed; `npx tsc --noEmit` clean.

### G.3 Stakeholder demo-path audit (Observed, source-level)

| Surface | Verdict |
|---|---|
| `/workbench` Proposal Compiler | LIVE deterministic engine, correctly badged (`deterministic_preview`, `provider_connected=false`, share link gated on real token, sample-data notice) — F-42 residual closed at UI level |
| Trip decision page | Abstains ("Build options first"); confidence only when finite; no hardcoded scores |
| Landing / login | Qualitative proof rail ("Fact-first / Human-gated / No theater"), no fabricated hero metrics; hero workbench mock is standard illustration |
| Persona Council simulators | Badged at panel level only; Journey Graph visualizer itself still renders BA178/Mandarin Oriental sample inside the tab; DocumentMRZ/Distribution panels hold sample PNR/passport — demo hygiene: don't open, or script the framing |
| Legacy routes `/v2`–`/v5` | Still routable — demo hygiene: don't navigate |
| a11y (code-level) | Companion SOS/day pills < 44px targets; pervasive `text-[10px]`; ProposalCompilerPanel has 2 unlabeled intake fields — polish wave, not demo-blocking |

### G.4 External input this session

- **Codex CLI 0.150.1** read-only review dispatched (`codex exec --sandbox read-only`, gpt-5.6-luna) — **blocked by account usage limit, resets 18:09 IST 2026-09-07**. Retry verbatim; file output as **Part H**.
- **Web research (domain):** small Indian proprietor agencies standard stack = consolidators (TBO, Mystifly) over direct GDS; WhatsApp-first CRM/quotation tools (Zoho, TravoByte, CRMtravel, TraviYo); top pains = payment collection/chasing, manual quote/invoice generation, slow inquiry turnaround. Sources logged in the session evidence doc §3. Maps to demo plan §5 discovery questions and DECIDE rows (provider connector, WhatsApp channel, India payment rails).

### G.5 Second implementation unit (2026-09-07, same session, uncommitted)

Owner directive: do not frame the work as "done for Ravi" (meeting unconfirmed; minimum bar = committed tree + L7 browser proof); keep executing open findings. Executed:

| Finding | Disposition | Evidence |
|---|---|---|
| **F-43** (P1) | **CLOSED (local).** Both next.config wildcard rewrites removed; every former rewrite consumer explicitly mapped in the BFF allowlist: `v1/logistics/assess-route`, `v1/group/token/{token}` (+`/pay-share`), `public/journey-graph/{trip_id}`, `public/proposals/{token}` (+`/calculate`, +`/accept`). Route-map tests added, incl. a denial assertion that the money-path fulfill endpoint stays browser-unreachable. | `frontend/next.config.mjs` (rewrites deleted with rationale comment); `frontend/src/lib/route-map.ts`; `frontend/src/lib/__tests__/route-map.test.ts` (2 new tests); vitest route-map+honesty 27 passed; tsc clean |
| **PA-40** (P1, fulfill half) | **CLOSED (local).** `POST /api/v1/fulfillment/proposals/fulfill` now accepts `Idempotency-Key`, scoped `(agency_id, trip_id, header)`, resolved against the durable registry (same CAS as `/run`): COMPLETED → replay original response + `idempotent_replay: true`; PENDING → 409; FAILED → retryable; all terminal failure paths mark failed so ratification retries aren't blocked. Engine once-booked guard (AT-03) remains the second layer. | `spine_api/routers/fulfillment.py`; new test `test_fulfillment_router_idempotency_key_replay` in `tests/test_booking_fulfillment_lifecycle.py`; 7/7 lifecycle + ruff clean |
| **AT-11 residual** (P1) | **CLOSED (local).** `TEST_AGENCY_ID` fallback removed (400 without `X-Agency-ID`); `passport_country` no longer defaults to `"US"` — resolved from trip packet/record or explicit query param; unknown inputs → abstention summary naming exactly what's missing instead of a legal determination. | `spine_api/routers/visa_radar.py`; capability batch 27 passed incl. visa cases |
| **AT-04** (P1) | Still open. `BookingConfirmation` model + state machine confirmed present (`spine_api/models/tenant.py:629`, `confirmation_service.py` `create/record/verify/void`); wiring fulfill→SQL machine needs the request-scoped AsyncSession/RLS decision (`Depends(get_rls_db)` pattern) + file-store parity contract. Next unit candidate. | this pass's inspection |
| **2.3c logistics healer** | **Disposition changed: not a plain delete.** `src/logistics/irrops_healer.py` carries unique statutory logic — `evaluate_statutory_compensation` implements EU261/UK261/US-DOT brackets + extraordinary-circumstance exemption (lines 90-128) — found nowhere else (`passenger_rights*` has no calculator). Call sites: `tests/test_irrops_healer.py` only. Correct sequence per supersession workflow: migrate the compensation calculator into the passenger-rights canonical path (AT-17 operator-case work), then retire the sample-graph shell. | rg + file inspection this pass |

**Receipts (this unit):** backend 27 (lifecycle 7 incl. new PA-40 test, capability batch, authority approvals, contract-drift guard) + ruff clean on touched files; frontend vitest 27 (route-map incl. 2 new F-43 tests + honesty) + `tsc --noEmit` clean. Not Git, not hosted, not L7.

---

## Part H — External review (codex, 2026-09-07) + triage

**Provenance:** `codex exec --sandbox read-only` (gpt-5.6-luna, reasoning effort high, ~233k tokens), automated retry after the earlier usage-limit block. Read-only: no files, Git state, caches, or processes modified by codex. Verbatim findings in H.1; this session's triage in H.2. **No product code was changed in response — these are queued for the next implementation pass per the findings lifecycle.**

### H.2 Triage (Observed, this session, file:line verified)

| Codex finding | Triage | Evidence / notes |
|---|---|---|
| **P0** Fulfillment not exactly-once across the side-effect boundary (guard before lease; 60s lease never renewed; VCC/PNR minted ~:259-278; durable confirmation only ~:302-334; crash-in-between → second VCC/PNR) | **CONFIRMED** (structural) | Guard-before-lease and mint-then-persist order verified in `booking_fulfillment.py` this session. Live-provider financial impact is inferred (adapters are simulated today) — same caveat codex itself states. This is the known Wave-2.1 residual (replay guard ≠ crash-safe exactly-once). |
| **P1** Partial confirmation state → second VCC (guard checks `pnr_locator` only) | **CONFIRMED** | Guard code reads only `pnr_locator` (`booking_fulfillment.py:145-148` region); replay returns stored fields even when empty strings. |
| **P1** Fulfillment destructively replaces the trip's persisted graph with a fresh single-flight-node graph | **CONFIRMED** — **highest-value catch of this review** | `booking_fulfillment.py` step 5: `graph = JourneyDependencyGraph(trip_id=trip_id)` builds a NEW graph, adds one FLIGHT node, and `updates["journey_graph_nodes"]=stored_graph[...]` overwrites the compiler's persisted quoted DAG (hotels/transfers/rail/return nodes lost). The 2026-09-07 OS-layer unit's "persist ticketed DAG" merged nothing. Fix direction: load existing stored graph, add/upgrade the flight node, preserve quoted siblings. |
| **P1** Companion renders simulator-generated PNR/e-ticket/voucher as traveler truth (no `provider_connected`/`commitment_status` gate; `Reality:` string cosmetic only) | **CONFIRMED** | rg: companion has `reality_tier?: string` + a `Reality: {tier}` line (`page.tsx:45,205`) but zero `provider_connected`/`commitment_status` references; PNR/e-ticket/wallet render unconditionally from stored data. §13 gap on **stored-but-simulated** data (AT-05 covered fabricated-from-nothing). |
| **P1** Public proposal page: `?? 0` renders "$0" on malformed payload; no runtime validation; gated demo path renders unbadged | **CONFIRMED** (severity nuance: demo path is token-gated, so exposure is bounded) | `page.tsx:173` `?? 0` introduced by the AT-20 fix as the lesser fallback; correct contract = treat missing price as unavailable. Demo-token unbadged rendering matches G.3 note. |
| **P1** NBTA read/compare/write race (no CAS on the read version; last-writer can erase a higher-priority action) | **CONFIRMED** (structural; sequential tests can't catch) | `travel_next_action.py:127-149,169-173` read-compare-write; `persistence.py:529-545` field merge without version assert. Fix direction: version/compare-and-set on the next-action write or merge inside the store lock. |
| **P2** Idempotency replay does not compare stored body hash; `mark_completed` bool ignored | **CONFIRMED** — corrects this session's PA-40 comment | Registry returns cached on COMPLETED without hash comparison (`idempotency.py:494-506`); the router comment "one key cannot silently alias different payloads" overclaims (hash is stored, not enforced). Also `mark_completed` return ignored at `fulfillment.py`. Fix next pass: compare hash → 422 on mismatch; surface stale-completion. |
| **P2** `JourneyNode.from_dict` strictness: `_parse_dt("")` throws on missing timestamps; unknown `node_type` silently coerced to FLIGHT | **CONFIRMED** | `schemas/journey_graph.py:58-62,102-127` read this session: `datetime.fromisoformat("")` raises; minimal stored nodes (e.g. hydration test fixtures) fail through `from_stored`; unknown types default to FLIGHT instead of abstaining. Introduced by today's OS-layer unit. |
| **P2** "A confirmation receipt has been emailed" — no email dispatch exists in the accept path | **CONFIRMED** | `p/[token]/page.tsx` accepted-state copy; accept path persists + audits only (consistent with communicator drafts-only doctrine). §13 claim-reality violation; reword next pass. |
| Idempotency gaps list (side-effect-start marker, provider idempotency key, lease renewal, optional header, TTL reclaim after possible success, no CAS assert-unfulfilled) | **CONFIRMED as known-open** | Consistent with plan 2.1 residual + P0 above; fold into the AT-04/fulfillment-durability unit. |
| Heuristic-label check: no unlabeled scores in the six files | **Consistent** | Matches earlier verification (counterfactual `score_basis="heuristic_hardcoded"`). |

**Net:** 0 refuted. Register additions implied: the destructive-graph P1 and companion sim-truth P1 belong with AT-01/AT-05 follow-ups; exactly-once P0 belongs with the fulfillment-durability unit (AT-04 + PA-40 residual); schema strictness P2 is a defect in the 2026-09-07 OS-layer unit itself.

---

## Part I — Durability + honesty implementation pass (2026-09-07 evening, uncommitted)

Owner directive: complete the Part-H follow-ups. Executed against every confirmed Part-H finding. All local; not Git, not hosted.

| Part-H finding | Fix | Evidence |
|---|---|---|
| **P0 exactly-once across side-effect boundary** | Provider-side idempotency: `fulfillment_provider_key(trip_id)` (sha256 of `fulfill:{trip_id}`) drives **deterministic instruments** in both sandbox adapters (same key → same PNR/e-ticket/VCC id — the live-GDS contract); durable `side_effects_started_at` marker written **before** any provider call; re-entry after marker re-issues with the same key and logs the reconciliation; authoritative confirmation **re-check inside the lease** (closes the two-requests-pass-the-fast-path window); lease **renewed** after each provider call, loss = fail-loud `RuntimeError` | `booking_fulfillment.py` (steps 2–4 + `_renew_lease`), `amadeus_sandbox_adapter.py`, `stripe_issuing_adapter.py`; test `test_amadeus_provider_idempotency_same_key_same_instruments` |
| **P1 partial confirmation → second VCC** | Marker + provider-key re-entry returns the same instruments; final confirmation blob retains `side_effects_started_at` + `fulfillment_provider_key` | same unit |
| **P1 destructive graph replace** | Fulfillment now loads the stored graph (`JourneyDependencyGraph.from_stored`) and **merges** the ticketed flight node (same `node_id` upgrades in place); quoted/held siblings survive | test `test_fulfillment_merges_confirmed_leg_into_existing_graph` |
| **P1 companion sim-truth** | `PREVIEW itinerary` gating: when `booking_confirmation.provider_connected === false` (or any node metadata / `reality_tier === 'deterministic_preview'`), the green "Stored itinerary" banner is replaced by an amber "Preview itinerary — deterministic previews, not live bookings" banner; wallet labels become "E-Ticket (preview)" / "Hotel Voucher (preview)" | `companion/page.tsx` + new honesty test |
| **P1 proposal `$0` + unvalidated payload + unlabeled demo** | `asProposal()` runtime validation (incomplete 200 → abstention screen, never `$0`); `reality_tier` added to `PublicProposalView` (`"demo"` on the gated demo fixture, `"persisted_observed"` on real data) with a **Demo content** badge in the hero; honest acceptance copy (durable record + advisor follow-up — no emailed-receipt claim) | `p/[token]/page.tsx`, `public_proposals.py`; tests: incomplete-payload abstain, demo badge |
| **P2 idempotency body-hash not enforced** | Router compares incoming request hash vs stored `request_hash` on COMPLETED replay → 409 `idempotency_key_payload_mismatch`; `mark_completed` False now logged (never silent) | `spine_api/routers/fulfillment.py`; test `test_fulfillment_router_idempotency_key_body_mismatch` |
| **P2 `JourneyNode.from_dict` strictness** | `_parse_dt` returns `None` on missing/unparseable times (hydration no longer crashes); unknown `node_type` **preserved verbatim** (no FLIGHT coercion); `start/end_time` now optional with consumers guarded honestly (`evaluate_disruption` raises "no scheduled end time — abstains", undated nodes skipped in ripple, sort puts undated last, `compute_cushion_variance` abstains) | `src/schemas/journey_graph.py`; test `test_from_dict_tolerates_undated_nodes_and_preserves_unknown_types` |
| **P1 NBTA race** | `NextActionAwareTripRepo.update_trip` now uses the canonical `update_trip_if_version` CAS with a bounded **verify-and-heal** loop (re-merges against fresh state, re-applies a lost high-priority action, max 3 attempts). Residual post-verify window documented in-code; full closure = store-level priority merge (E-G) | `travel_next_action.py`; test `test_cas_proxy_heals_stale_lower_priority_clobber` |
| P2 emailed-receipt claim | Reworded to the true behavior (see proposal row above) | same |

**Also this pass:** a parallel agent's route-inventory gate correctly removed my `v1/logistics/assess-route` mapping (no backend endpoint exists — accepted; my test now asserts the denial). Pre-existing defect recorded: `RouteMapStudio.tsx:47` still fetches that nonexistent route and will 404 — queued, not fixed here.

**Receipts:** backend pytest **79 passed** (lifecycle 9, journey graph + hydration, travel-next-action incl. race heal, irops simulator, fx/irops, compiler e2e, capability batch, authority approvals, contract-drift guard, pipeline boundaries, escalate-lead persistence) + ruff clean on all touched files; frontend vitest **43 passed** (proposal 5, companion 4, route-map, compiler, panels) + `tsc --noEmit` clean. Codex follow-up review of this pass: see Part J when filed.

---

## Part J — Codex re-review + same-session fixes (2026-09-07 evening)

**Provenance:** `codex exec --sandbox read-only` (gpt-5.6-luna, ~423k tokens), reviewing the Part-I diffs against the standing invariants. Codex verdict was honest: several Part-H fixes were partial, and it **reproduced a new defect** (naive/aware timezone crash) introduced by the tolerant parsing. All 10 findings triaged; the actionable set was fixed in this same session. Final state: **81 backend + 44 frontend tests passing, ruff + tsc clean.**

| # | Codex finding (severity) | Disposition |
|---|---|---|
| 1 | Provider key not bound to payload; Stripe sandbox aliases changed params; livemode ignores key (HIGH) | **Fixed.** Key now `sha256(fulfill:{trip_id}:{proposal_token})`; Stripe sandbox digest binds `amount_cents` + `currency`; livemode documented as requiring native Stripe Idempotency-Key header at integration time |
| 2 | Lease renewal post-call, not mid-flight (HIGH) | **Improved + honest residual.** Renewal now also fires immediately before the provider window; a true heartbeat DURING a long provider await needs adapter-side timeout/renewal design — recorded missing-for-upgrade below |
| 3 | SQL-confirmation failure reported as success; replay doesn't repair; no uniqueness constraint (HIGH) | **Mostly fixed.** Blob now carries `sql_confirmation` outcome; `_replay_and_repair` re-records a missing SQL confirmation on replay and heals the blob; outcome always surfaced on result + audit. **Open:** uniqueness constraint on the confirmation table needs an Alembic migration (A-20 custody) — duplicate-row window on crash-between-record-and-blob-update remains until then |
| 4 | Companion fails OPEN on missing provenance (HIGH) | **Fixed fail-closed.** `isLive` requires explicit `provider_connected: true` AND no node with false; missing/false/legacy provenance renders the Preview banner; test covers the legacy-shaped blob |
| 5 | Final graph write still non-CAS (MED-HIGH) | **Improved + honest residual.** Fulfillment persist now uses `update_trip_if_version` with per-attempt graph re-merge (3 attempts); plain-write fallback prioritizes booking durability and logs — residual clobber window documented |
| 6 | NBTA 3-attempt fallback reintroduces stale write (MED-HIGH) | **Fixed fail-closed.** After exhausted retries the action/priority fields are stripped and only contention-safe metadata is written — a stale priority clobber is now impossible via the proxy; test proves the stored action survives persistent contention |
| 7 | Mixed naive/aware datetime crash (MED) — reproduced by codex | **Fixed.** `_parse_dt` normalizes naive→UTC (storage canonical); test covers mixed-provenance topological sort |
| 8 | `/calculate` + `/accept` responses unvalidated (MED) | **Fixed.** Both run through `asProposal`; malformed recalculation is ignored, acceptance success only on a valid accepted payload |
| 9 | CTA/consent claims "lock reservations" (MED) | **Fixed.** Copy now says acceptance is recorded and a travel advisor will then secure reservations ("Accept Proposal", "Recording acceptance…") |
| 10 | Hash compare conditional on truthy stored hash (LOW-MED) | **Fixed.** Strict compare — a record without a matching stored hash cannot replay |

**Honest invariant status after this pass (source + test level, not browser/hosted):**

- **Invariant 1 (no second PNR/VCC):** materially stronger — provider-key determinism + marker + in-lease re-check + CAS write. Residual: crash windows require the SQL uniqueness constraint and live-provider idempotency integration; true mid-flight heartbeat open.
- **Invariant 2 (no simulated-as-live):** companion now fails closed on missing provenance; residual: the journey-graph router could attach a top-level provider attestation so clients need not infer from per-node metadata (queued).
- **Invariant 3 (heuristic labels):** clean in scope per codex.

**Open (deferred with reasons):** BookingConfirmation uniqueness migration (A-20 custody) · journey-graph top-level provider attestation · adapter heartbeat during long provider awaits · livemode Stripe Idempotency-Key header · `RouteMapStudio.tsx:47` dead fetch of nonexistent `/api/v1/logistics/assess-route` (404s; backend endpoint never existed) · hosted/browser (L7) proof of all of the above.

---

## Part K — Still-open items closed (2026-09-07 night, uncommitted)

Owner directive: "do the still open one(s)." Every Part-J deferred item addressed except the git commit (explicit owner go still required — the tree packages parallel agents' work).

| Open item | Disposition |
|---|---|
| **BookingConfirmation uniqueness** | **Closed.** Partial unique index `uq_bc_trip_type_active` on `(trip_id, confirmation_type) WHERE confirmation_status != 'voided'` — model-level (`spine_api/models/tenant.py`, converges with lazy `create_all`) AND alembic revision `bc_active_type_uniqueness` (head: `pa_wave2_authority_payouts_cost`; upgrade voids duplicate actives newest-kept via parameterized statements — nothing deleted — then creates the index). Tests: `tests/test_booking_confirmation_uniqueness.py` (duplicate rejected, void frees slot, cross-trip allowed) on in-memory SQLite; the duplicate-repair window is now structurally impossible. |
| **Journey-graph top-level provider attestation** | **Closed.** `_stored_graph_payload` now attests top-level `provider_connected` + `reality_tier`, derived FAIL-CLOSED (live only when the confirmation explicitly attests True and no node contradicts). Companion consumes the attestation (per-node inference kept as fallback for pre-change cached payloads). |
| **Adapter heartbeat during long awaits** | **Closed.** `lease_heartbeat` async CM in `src/orchestration/agent_lease.py`: renewal task runs while the provider window executes; a lost lease is re-raised on exit so the caller cannot persist under a fence it no longer holds. Engine wraps the VCC+GDS window (15s interval / 60s TTL). Tests: renews-during-body + fails-loud-on-loss. |
| **Livemode Stripe Idempotency-Key** | **Closed the honest way — fail-closed.** Under `sk_live_*` the adapter now REFUSES (`RuntimeError`) instead of returning a fixture labeled live (§13: a simulated instrument must never present as live). `missing_for_upgrade` now names the native Stripe Idempotency-Key header requirement. Test covers the refusal; sandbox determinism test unchanged and green. |
| **RouteMapStudio dead fetch** | **Closed at UI level.** The fabricated-savings fallback (hardcoded 12450/11120/10.7% presented as optimizer output, even in the `res.ok` path via `\|\| default` masking) is removed; missing/404/invalid payloads render an honest "backend endpoint does not exist yet" banner. Re-enabling the solver = ship the backend endpoint (route-inventory gate rule). |
| **L7-lite browser proof** | **Partial — executed this session.** Against the live dev servers (backend `/health` 200, frontend 200): `/p/invalid-token` renders the honest "Proposal unavailable" abstention (AT-20 fix browser-proven); `/companion` without token renders the signed-token-required abstention; landing renders clean with the qualitative proof rail and zero console errors. **Remaining L7 scope:** token-gated companion against a real fulfilled trip (preview banner), authenticated workbench walk, hosted evidence. |
| **Git commit** | **Not executed — requires the owner's explicit go.** The tree packages parallel agents' work (PER-0700 + PER-0443 waves) alongside this session's; the commit-gate protocol (motto attestation, hook refresh, trailers) applies. Everything is ruff-clean and test-verified for that gate when authorized. |

**Receipts:** backend pytest **88 passed** (adds uniqueness 3, heartbeat 2, livemode 1) + ruff clean across `src/`, `spine_api/`, `alembic/versions/bc_active_type_uniqueness.py`, `tests/`; frontend vitest **44 passed** + `tsc --noEmit` clean. Not Git, not hosted; browser evidence limited to the three abstention/landing surfaces named above.

---

## Part K addendum — AT-21: internal vocabulary leaking to traveler surfaces (P2, owner-caught)

**Finding (owner, live UI):** the abstention copy was engineer-voiced — *"A signed proposal share token is required (?token=)"* rendered on the traveler portal, plus raw reality-tier slugs (`deterministic_preview`) and dev terms ("Journey graph", "Provider not connected", "audit trail", "signed/time-limited") on traveler pages. The honesty wave fixed *fabrication* but wrote its banners in internal vocabulary — claim-reality done at the expense of audience.

**Fixed (same hour):** traveler surfaces now speak traveler language while keeping every honesty property —

- Companion token-required: *"This itinerary can only be opened through the private link your travel advisor sent you."*
- Companion no-graph: *"Your itinerary will appear here as your travel advisor confirms bookings."*
- Preview banner: *"Prepared with your travel advisor's planning tools. The references below are placeholders — they become real once your bookings are confirmed."* (raw tier slug no longer rendered; "Provider not connected"/"deterministic" gone)
- Live banner: *"Your trip to X. Booking reference: … · E-Ticket: …"* (no "Journey graph", no tier slug)
- `/p/[token]`: *"Proposal links are private and expire after a while…"*; success copy drops "audit trail"
- RouteMapStudio (operator surface): endpoint-name instruction removed; *"Route assessment isn't available yet — you'll see nothing here rather than made-up numbers."*

**Tests:** companion honesty suite asserts the new copy AND asserts `?token=`/`deterministic` never render; 44 FE tests + tsc clean; copy re-verified in the live browser.

**Follow-up (EXPLORE → implement):** full traveler-copy sweep of remaining traveler-facing surfaces (`itinerary-checker`, `booking-collection`, notifications, SOS flow) with a rule: internal vocab (tokens, tiers, endpoints, gates) stays in operator surfaces; traveler copy names the advisor, the itinerary, and the next step. Not blocking this week's demo.

### AT-21 codebase sweep (same session, Explore-audited + fixed)

Owner ruling applied: one caught leak = sweep the class. An Explore agent audited all five traveler surfaces (rendered strings, not code identifiers) plus agency panels. Results:

**FIXED — traveler surfaces (all rendered copy):**

- **companion**: the full "stored graph/nodes" family ("Stored flight", "Stored carrier", "Duration not in stored graph", "Not in stored graph" on TERMINAL/GATE, "No stored transfer/hotel node", "No stored activity for day N", "N stored nodes", "Companion does not invent day-by-day content without stored journey nodes", "Status: unavailable") → traveler voice ("being confirmed", "assigned at check-in", "Day N is not planned yet", "N days planned"); `ENCRYPTING PAYLOAD...` → "SECURING YOUR ALERT..."; `STATUS UNKNOWN`/`UNAVAILABLE` pill → "NOT CONFIRMED YET".
- **itinerary-checker**: "The live run did not return a result. Check the backend…" → honest retry line; "Export JSON" → "Download my saved report"; "No blockers returned yet…" → "No issues found yet…"; "Checking storage mode…/Storage mode could not be determined." → "Checking what we saved…/We couldn't confirm what was saved."; raw `Source signals:` list → "Checked against live data sources."; `Live source` label + raw slug → "Data checked: Live sources"; `Report ID: {id ?? 'pending'}` → "Reference: …"; unknown blocker-slug fallback (was `item.replaceAll('_',' ')`) → honest generic line; `reason` slug passthrough dropped ("— this detail is still missing."); slug-shaped backend validation messages (contain `_`) → safe fallback line.
- **g/[token]**: browser `err.message` (e.g. "Failed to fetch") leaked to the error screen → fixed honest line; "Failed to record payment notification" → "We could not reach your travel advisor just now. Please try again — nothing was charged."
- **booking-collection**: "Traveler ID \*" / `e.g. adult_1` → "Traveler name or reference \*" / "e.g. Sarah (lead traveler)"; rejected/deleted doc statuses mapped to traveler lines instead of raw enum.

**REGISTERED — agency raw-slug render points (batch copy pass, not blocking):** IROPSAutoHealerPanel `PREVIEW_ONLY`/`UNVERIFIED LOCAL INPUT` badges raw; ProposalCompilerPanel renders `reality_tier`/`provider connected` verbatim; DistributionPanel `PREVIEW_ONLY (no carrier submission)`; JourneyGraphVisualizer "Journey Dependency Graph (JDG)" heading unframed; FinancialSettlementPanel "issuance endpoint" in note; "fixture" vocabulary in ScenarioLab/DutyOfCareRadarPanel/bookings sourceLabel/suppliers; DecisionTab raw `risk_summary`; audit/trips/followups HTTP `status`/`statusText` in toasts; IVRBypassPanel + CrisisEvacuationPanel raw enum statuses.

**Coverage gaps (unguarded surfaces):** `g/[token]` and `itinerary-checker` (2,932 lines — largest traveler surface) have **zero test coverage**; `booking-collection` tests are functional-only with no copy assertions. Until render tests exist there, the sweep is evidence, not enforcement.

**Verification:** FULL frontend suite **1,333 tests / 177 files passing** + `tsc --noEmit` clean after the sweep (booking-collection test locator updated to the new placeholder; submitted API contract unchanged).

---

## Part L — Agency copy pass, coverage, L7 live proof + NEW data-loss catch (2026-09-07 night → 09-08 morning)

Owner directive: "do all open." Three remaining open fronts executed; the L7 execution **caught and fixed a live-SQL data-loss bug** that static passes had missed.

### L.1 Agency copy pass (11 panels humanized, honesty preserved)

IROPSAutoHealerPanel (`PREVIEW_ONLY`/`UNVERIFIED LOCAL INPUT` → "Preview only — nothing was sent to any carrier / Details need human verification") · ProposalCompilerPanel (raw `Reality tier: … provider connected: false` → "Preview compiled locally — no provider connected, so treat every price as an estimate") · DistributionPanel (`{status}` slug → "Preview — nothing sent to the airline") · JourneyGraphVisualizer (JDG heading → "Journey & Disruption Simulator (demo)") · FinancialSettlementPanel ("issuance endpoint" → business voice) · ScenarioLab (3× "fixture" → "saved scenarios/templates") · DutyOfCareRadarPanel ("Load sample threat fixtures" → "Load sample scenarios") · bookings sourceLabel 4× ("Sample itinerary fixture" → "Sample itinerary (demo data)") · suppliers ("fixture" → "(demo)") · DecisionTab (blank risk_summary → explicit no-notes line) · IVRBypassPanel + CrisisEvacuationPanel (raw enums → mapped phrases) · trips/[tripId] timeline `statusText` toast → human lines. Operator toasts in audit/ pages keep HTTP codes (operator-appropriate; registered as accepted).

### L.2 Coverage gaps closed

- `g/[token]`: NEW `group-invite-copy.test.tsx` — network-failure and invalid-invite render the fixed traveler line; browser `TypeError`/`Failed to fetch` never render (next/navigation mocked).
- `itinerary-checker`: NEW `blocker-copy.test.tsx` — `formatTravelerBlockerItem` (now exported) maps known slugs and never renders unknown slugs raw.
- **Honesty-test doctrine update:** three stale assertions pinned the OLD raw-slug copy (`PREVIEW_ONLY`, `Reality tier: deterministic_preview`, "issuance endpoint") — updated to assert the humanized copy AND the absence of the raw slug, so vocabulary improvement is now locked in, not just permitted.

### L.3 NEW P0-class catch + fix: SQL partial updates dropped `_extra` (AT-01-on-SQL data loss)

Executing the L7 live proof exposed what every static pass missed: on `TRIPSTORE_BACKEND=sql`, `SQLTripStore.update_trip` **replaced `analytics._extra` wholesale** on partial updates, so the AT-04 follow-up write (booking_confirmation) silently erased the `journey_graph_nodes`/`edges` the CAS persist had just written — the journey graph never reached the traveler on SQL (file-store tests couldn't see it). **Fix (root):** `SQLTripStore.update_trip` now calls the shared `_prepare_raw_update` deep-merge like every other write path. **Live regression proof:** fresh trip through accept → fulfill on real SQL: `GRAPH_NODES 1, ticketed`, blob `provider_connected: false`, and the dev server's public journey-graph route serves the full stored graph with top-level attestation (`provider_connected: false`, `reality_tier: deterministic_preview`).

### L.4 L7 browser proof (real data, real token, real browser)

Seeded an additive trip (`trip_l7_browser_smoke_20260907_b`, canonical test agency) through accept → fulfill → persist, then loaded `/companion?tripId=…&token=…` in the live in-app browser: **"Preview itinerary — Prepared with your travel advisor's planning tools. The references below are placeholders — they become real once your bookings are confirmed."**, real PNR `5DDB16` rendered as "E-Ticket (preview)", "Trip Sync: Tokyo", "NOT CONFIRMED YET", "Assigned at check-in", "1 days planned" — zero jargon, zero fabrication, traveler voice throughout. Note: dev backend must run TODAY'S code (restarted); the pre-fix server omitted the top-level attestation.

### L.5 Registered (open, with reasons)

- **AT-04 RLS nuance:** `try_record_fulfillment_confirmation` from background/script context hits `booking_confirmations` RLS (non-owner role) → honest `recorded: false` surfaced (as designed). Server request-context writes carry agency RLS and should succeed — verify during authenticated L7 walk. The uniqueness migration makes retries safe regardless.
- **`booking_confirmation` in `analytics._extra` is stored unencrypted on SQL** (file store too). It contains VCC ids — should join the encrypted fold or a dedicated encrypted column. Needs the encryption-migration lane (A-20 custody), not a hot patch.
- **Coverage still owed:** itinerary-checker full render test (2,932 lines), booking-collection copy assertions, authenticated workbench L7 walk, hosted evidence.

**Final receipts this pass:** frontend **1,337 tests / 179 files passing**, `tsc --noEmit` clean; backend **103 tests passing** (16 files incl. p1-hardening + pending-implementations waves), repo-wide ruff clean. Backend + frontend dev servers restarted on today's code and re-verified live.

### H.1 Verbatim codex findings

````text
Static review result: this change-set is not safe to accept against the stated invariants. The review is Tier 1, based on the live uncommitted checkout and static cross-file tracing. No files, Git state, caches, processes, or external services were modified.

## Defects

### P0. Fulfillment is not exactly-once across the side-effect boundary

`src/orchestration/booking_fulfillment.py:145-171` performs the "already fulfilled" check before acquiring the lease. The lease is acquired at `src/orchestration/booking_fulfillment.py:232-239`, but the lease is only 60 seconds and is never renewed. The VCC and PNR are then minted at `src/orchestration/booking_fulfillment.py:259-278`, while the durable confirmation is written only later at `src/orchestration/booking_fulfillment.py:302-334`.

Failure sequence:

1. Request A sees no `booking_confirmation`.
2. Request A acquires the lease.
3. VCC and PNR creation succeeds.
4. The worker crashes, the provider call stalls beyond 60 seconds, or persistence/read-back fails before line 320.
5. The lease expires.
6. Request B sees no persisted PNR and acquires a new lease.
7. Request B mints another VCC and PNR.

The optional router idempotency header does not close this gap. The header is optional at `spine_api/routers/fulfillment.py:54-60,93-103`, and a pending idempotency record is explicitly reclaimable after its 1,800-second TTL at `spine_api/routers/fulfillment.py:32-35`. A durable idempotency record without a provider-side idempotency key or a durable "side effect started" state cannot distinguish "failed before side effect" from "side effect succeeded but response was lost."

Current adapters are simulation-only, so the directly observed duplicate is a duplicate simulated instrument. The live-provider financial consequence is inferred, but it violates the required invariant and blocks production fulfillment.

### P1. Partial confirmation state can trigger a second VCC and overwrite the first booking state

The replay guard considers a trip fulfilled only when `booking_confirmation.pnr_locator` is non-empty: `src/orchestration/booking_fulfillment.py:145-148`.

If VCC issuance succeeds but PNR creation fails, or if persistence writes only part of the confirmation, the next attempt sees no PNR and executes the full VCC/PNR path again. Conversely, if a PNR exists but the e-ticket or VCC fields are missing, the code returns `FULFILLED_CONFIRMED` with empty fields at `src/orchestration/booking_fulfillment.py:155-170`.

The guard needs a durable execution state or atomic booking record, not a single-field PNR presence test.

### P1. Fulfillment destructively replaces the existing per-trip journey graph

The fulfillment path creates a new graph containing exactly one flight node at `src/orchestration/booking_fulfillment.py:280-300`, then writes its node and edge arrays at `src/orchestration/booking_fulfillment.py:302-315`.

`TripStore.update_trip` merges the supplied fields by replacing existing list values at `spine_api/persistence.py:535-545`. Therefore, any existing quoted or held hotel, transfer, rail, activity, or return-flight nodes and edges are discarded during fulfillment.

This is a per-trip persistence failure even though the resulting one-node graph is technically stored under the correct trip ID. It can also make the traveler companion lose previously persisted itinerary content.

### P1. The companion displays simulator-generated or merely stored identifiers as traveler-facing booking truth

The fulfillment engine writes simulator-generated PNR and e-ticket values into `booking_confirmation` and the graph while simultaneously setting `provider_connected: false`: `src/orchestration/booking_fulfillment.py:273-298,302-314`.

The journey-graph response returns stored nodes and `booking_confirmation` without propagating a reality/provider gate: `spine_api/routers/journey_graph.py:195-223`.

The companion decides that any non-empty node list is usable data at `frontend/src/app/(traveler)/companion/page.tsx:140-160`. It then renders:

- "Stored itinerary" plus PNR and e-ticket at `frontend/src/app/(traveler)/companion/page.tsx:198-205`
- provider, flight title, and PNR at `frontend/src/app/(traveler)/companion/page.tsx:227-259`
- stored hotel title/provider/voucher at `frontend/src/app/(traveler)/companion/page.tsx:394-408`
- e-ticket and hotel voucher in the wallet at `frontend/src/app/(traveler)/companion/page.tsx:446-460`

There is no check for `provider_connected`, `reality_tier`, or `commitment_status === "ticketed"`. Consequently, a deterministic-preview PNR, a quoted node with a confirmation-like code, or a stored synthetic hotel/flight title can be presented as a real traveler itinerary. The visible reality string, when present, does not repair the stronger "Stored itinerary" and PNR presentation.

This directly violates the no-fabricated-PNR, flight-number, hotel-name, and real-status invariant.

### P1. The public proposal page trusts any successful JSON payload and fabricates a zero price on missing data

The page casts any successful response directly to `ProposalData` without runtime validation at `frontend/src/app/p/[token]/page.tsx:56-68`.

It then applies a fabricated fallback:

```ts
const currentTotal = proposal.selected_total_price_usd ?? 0;
```

at `frontend/src/app/p/[token]/page.tsx:173`, and renders that value as "Total Package" at `frontend/src/app/p/[token]/page.tsx:192-197`.

A successful but incomplete, stale, or malformed response therefore renders `$0` as a package price instead of abstaining. The TypeScript interface does not validate runtime data.

There is also an explicitly gated demo backend path containing hardcoded prices and hotel descriptions at `spine_api/routers/public_proposals.py:443-496,523-529`. The page has no demo/reality field or visible sample label for a successful payload, so if that path is enabled it renders those values as a normal curated proposal.

The persisted-proposal backend path does reject missing destination, title, price, or dates at `spine_api/routers/public_proposals.py:583-610`, but the frontend still lacks a contract guard and cannot distinguish a real persisted quote from a demo or synthetic payload.

### P1. Travel next-action priority is subject to a read/compare/write race

`merge_next_action_updates` reads the current action and priority at `src/orchestration/travel_next_action.py:127-136`, decides whether the proposed action wins at `src/orchestration/travel_next_action.py:142-149`, and writes afterward through the proxy at `src/orchestration/travel_next_action.py:169-173`.

The underlying store update is separately locked but has no compare-and-set against the version that was read: `spine_api/persistence.py:529-545`.

Two concurrent agents can therefore both read `monitor_weather`, one calculate `review_flight_disruption`, and the other calculate a lower-priority weather action. If the lower-priority write lands last, it can erase the disruption action. The sequential tests do not exercise this interleaving.

The claim in `travel_next_action.py:118-122` that the trip retains the winning action is not true under concurrent writes.

### P2. Idempotency keys do not reject a different request body under the same key

The router says it includes a body hash to prevent aliasing at `spine_api/routers/fulfillment.py:96-103`, but the registry does not compare the incoming hash to the stored hash. For an existing completed key, it immediately returns the cached response at `src/agents/idempotency.py:494-506`.

A client can submit the same `Idempotency-Key` with a different `proposal_token` or `holder_id` and receive the first request's fulfillment response. This does not necessarily mint a second booking, but it violates request identity and can return a confirmation for a different request context.

The router also ignores the boolean result of `registry.mark_completed` at `spine_api/routers/fulfillment.py:212-218`, so a stale or reclaimed idempotency owner can still return success without establishing a replayable completion record.

### P2. `JourneyNode.from_dict` is not tolerant of existing stored graph records

The new parser requires valid timestamps because `_parse_dt` converts missing values to an empty string and calls `datetime.fromisoformat`: `src/schemas/journey_graph.py:58-62`.

`JourneyNode.from_dict` invokes that parser for every stored node at `src/schemas/journey_graph.py:102-125`. Existing stored graph fixtures and the public graph contract allow nodes with only identity/provider/confirmation fields, for example `tests/test_journey_graph_hydration.py:97-104`. Such records can be served raw by the router but fail when hydrated through `JourneyDependencyGraph.from_stored`.

The same parser silently converts unknown `node_type` values to `FLIGHT` at `src/schemas/journey_graph.py:102-105`, which can change the operational meaning of malformed or future node types instead of abstaining.

### P2. The public page claims an email receipt that the acceptance path does not send

The accepted state tells the traveler that "A confirmation receipt has been emailed" at `frontend/src/app/p/[token]/page.tsx:326-335`.

The corresponding backend acceptance path only persists the acceptance and writes an audit event at `spine_api/routers/public_proposals.py:719-768`. No email dispatch or receipt creation is present in that path. This is a customer-visible false claim.

## Idempotency gaps

The remaining gaps are:

- The engine's durable replay guard is outside the lease and only checks `pnr_locator`.
- No durable state records that VCC/PNR side effects have started before the provider calls.
- No provider idempotency key is derived from `trip_id` or a durable fulfillment operation ID.
- The 60-second lease is not renewed during provider calls.
- The router `Idempotency-Key` is optional, so callers without it depend entirely on the weaker engine guard.
- Pending/failed idempotency records can be reclaimed after timeout even when the previous provider call may have succeeded.
- Stored request hashes are not compared on replay.
- Successful completion does not verify that `mark_completed` returned true.
- Persistence uses ordinary update semantics rather than a compare-and-set that asserts the booking is still unfulfilled.

The existing tests cover sequential replay after a durable confirmation exists at `tests/test_booking_fulfillment_lifecycle.py:134-163` and exact-body header replay at `tests/test_booking_fulfillment_lifecycle.py:299-335`. They do not cover crash-after-provider-success, lease expiry, partial confirmation, concurrent workers, idempotency-key body mismatch, or stale fencing.

## Heuristic-label check

No heuristic or AI-derived score is visibly rendered in the six named files. The internal next-action priority values are not themselves displayed in the reviewed UI. I found no separate score-label defect in this scope.

## Single riskiest remaining path

`POST /api/v1/fulfillment/proposals/fulfill` -> 60-second lease -> VCC issuance -> GDS/PNR issuance -> `TripStore.update_trip`.

The riskiest state is a successful provider side effect followed by worker loss, timeout, lease expiry, or persistence failure before `booking_confirmation` is durably committed. The next attempt has no reliable way to know that the first side effect already happened, so it can mint a second VCC and PNR and then overwrite the trip's confirmation. This remains unresolved even when the request carries an `Idempotency-Key`.
````

## Part O — Mimosa full-scan remediation wave (2026-09-10, uncommitted)

Source: sealed Mimosa full scan `scan-2026-09-08T20-21-25.551Z-e94e3b61266f` (100 findings; English translation at `report_en.md` in the scan directory). Owner directive: work the findings per doctrine. Triage split findings into real production defects, hygiene fixes, and false-positive classes — each class handled below.

### O-1. Canonical SSRF guard (new module, all producer surfaces wired)

New `src/security/url_guard.py`: single choke point for outbound HTTP. Rejects non-http(s) schemes, embedded credentials, and hosts resolving to non-public addresses (loopback, RFC1918, link-local incl. cloud metadata, CGNAT 100.64/10, IPv4-mapped IPv6). Redirect handler re-validates every hop. Dev escape hatch `WAYPOINT_ALLOW_PRIVATE_URLS=1` (documented in `.env.example`).

Wired into: `spine_api/routers/settings_health.py` (webhook probe returns `status: "blocked"` on guard rejection), `src/agents/live_tools.py` (both `_get_json` fetchers — config-driven provider templates), `src/llm/alert_service.py` (webhook URLs from env; blocked URLs logged and skipped, never raised), `src/public_checker/entity_checks.py` (Nominatim base URL from env).

### O-2. Frontend BFF: canonical `spineUrl()` (21 files consolidated)

`frontend/src/lib/proxy-core.ts` now validates the backend base URL at module load (http(s)-only, no embedded credentials; fails loudly in production) and exports `spineUrl(path)`. All 16 API routes + `bff-auth.ts` + `server-auth.ts` + `(agency)/layout.tsx` converted off scattered `${process.env.SPINE_API_URL || ...}` construction; every fetch receives a hoisted named const (the Mimosa write-hook's accepted safe shape). `rg 'SPINE_API_URL' frontend/src` now matches only the canonical definition.

Deliberately NOT converted: `app/corporate/offsites/page.tsx` and `app/intake/fast/page.tsx` — they are `'use client'` components using `NEXT_PUBLIC_API_URL` (the deployed-stack variable). Importing server-only proxy-core into a client bundle is a build hazard; these two Mimosa findings are false positives of the client/server distinction.

### O-3. Analytics fabrication class (honesty defect beyond the scanner's read)

Mimosa flagged `random` usage in `src/analytics/metrics.py`; reading the code revealed the real defect was **fabricated metrics shown in production analytics**:

- `avgResponseTime` was `random.uniform(2.5, 6.0)` → now mean hours from `created_at` to the first durable `status_history` transition; `None` without evidence.
- Stage timings (`avgTimeInStage`/`exitRate`/`avgTimeToExit`) were `random.uniform(...)` → now computed from real status dwell samples (exited + censored); `None` without evidence.
- `PipelineVelocity` fallbacks (`or 1.2/2.4/4.1`, `9.3` average) → real per-status dwell in days; stages without writers stay `0.0` honestly.
- `pipelineValue = trips × $15,000` → sum of real trip budgets for non-terminal trips.
- CSAT baseline `4.5` with zero ratings → `None` until real feedback ratings exist.
- `compute_bottlenecks` returned a hardcoded fake bottleneck card (stage, 24.5h, fabricated cause at 45%/12 trips) → now reports the slowest real non-terminal stage by measured dwell (severity: >72h high, >24h medium, else low) with `primaryCauses=[]` — causes are never invented; empty list when no dwell evidence.

Contract changes (models regenerated via `scripts/generate_types.py`): `InsightsSummary.avgResponseTime`, `StageMetrics.{avgTimeInStage,exitRate,avgTimeToExit}`, `TeamMemberMetrics.customerSatisfaction` are now `Optional`. FE null-guards added (`insights/PageClient.tsx`, `TeamPerformanceChart.tsx` — 'N/A'/'—'/`?? 0` paths).

Hostile test coverage corrected: `tests/test_analytics_truth_hardening.py` previously asserted the fabrication as contract (`len(primaryCauses) > 0`, `>= 0.0` tolerances). Rewritten to assert real-or-None semantics with status_history fixtures (19 tests).

### O-4. Credentials, SQLi, path traversal

- Hardcoded test credentials (4): `scripts/verify_phase0.py` and `verify_phase1.py` now use obviously-synthetic named fixtures (hashed/discarded in-process, never authenticate); `tools/performance_benchmark_matrix.py` reads `WAYPOINT_TEST_PASSWORD` from env (documented in `.env.example`).
- SQLi (2): `src/llm/usage_store.py` PRAGMA f-strings → static literals with constants asserted equal (sqlite3 PRAGMA cannot be parameter-bound).
- Path traversal: new canonical `src/security/path_guard.py` (`safe_join`, `validate_filename`). Wired into `persistence._validate_trip_id` (defense-in-depth beneath the trip-ID regex), `draft_store._draft_path`, `decision/cache_storage._get_cache_file_path`, `decision/override_learning._rewrite_pattern_file`, `memory/store.__init__`.

### O-5. False-positive classes (documented, not churned)

- **Insecure randomness (27 minus metrics):** all in seed/scenario generators (`generate_scenario.py`, `seed_analytics_trips.py`, `backfill_feedback.py`) generating synthetic test data — destinations, party sizes, budgets. No tokens, secrets, or security-relevant identifiers minted with `random`.
- **Path traversal in `scripts/`/`tools/`/`tmp/`:** dev tooling taking explicit CLI path arguments — opening operator-specified files is the tool's job; no production exposure.
- **Taint flows (3):** `auth_service.refresh_access_token` / `confirm_password_reset` and `collection_service` use fully parameterized ORM constructs; the scanner flagged the `.execute` sink without resolving the parameterization.
- **Dev-tooling SSRF:** `capture_nav_screenshots.py`, `design-lab/inspect-app-dna.py`, `tools/dev_server_manager.py`, `singapore_scenario_regression.py` fetch explicit dev URLs by design.

### O-6. Verification receipts

- New unit tests: `tests/test_url_guard.py` (20 — scheme/shape/resolution/override + path guard containment incl. symlink escape), rewritten `tests/test_analytics_truth_hardening.py` (19), alert-service guard-seam tests updated + new blocked-URL skip test (24 total).
- Full frontend suite: 183 files / 1,374 tests passing; `tsc --noEmit` clean.
- Full backend suite: 4,341 passed / 44 skipped / 0 failed (first run showed 1 non-reproducible ERROR in `test_trip_history_scoping.py::test_undo_redo_return_payload_semantics` — passes in isolation and on full-suite rerun; ordering flake, not a regression from this wave).
- `ruff check` clean across all touched files; curated mypy 21 files clean.

### O-7. Post-fix verification scan (sealed)

Verification scan `scan-2026-09-10T06-37-00.460Z-ccf5089fff20` (seal `sha256:3a841578…bd94d7`): **100 → 74 findings**. Diff against the sealed baseline:

- **All 26 production-relevant findings cleared**: every BFF route SSRF (inbox ×2, auth/me, validate-code, followups, trips, stats, price-lock, bff-auth, server-auth, agency layout), all Python server-side SSRF (settings_health, live_tools ×2, alert_service, entity_checks), all 4 hardcoded credentials, both SQLi PRAGMA interpolations, and the analytics `random` fabrication sites.
- **The 17 "newly-raised" path findings are line-shifted duplicates**: identical `open(filepath)` call sites in persistence/draft_store/override_learning/memory re-flagged at new line numbers because the static analyzer cannot trace validation through `_validate_trip_id`/`safe_join` to the `open()` call. The validation exists and is unit-tested (`tests/test_url_guard.py`); contorting the call sites to satisfy the scanner's taint tracking would violate the no-hacks policy.
- **Residual 74 = documented noise floor**: 40 path (15 persistence re-flags + dev tooling/scripts/tmp with explicit CLI path args + geography module-level fixed paths), 23 random (seed/scenario generators producing synthetic test data by design), 8 SSRF (dev tooling: `capture_nav_screenshots.py`, `design-lab/inspect-app-dna.py` ×2, `dev_server_manager.py`, `singapore_scenario_regression.py`; client components: offsites/intake-fast using `NEXT_PUBLIC_API_URL`), 3 taint (parameterized ORM false positives in auth/collection services).

### O-8. Open items from this wave

- `WAYPOINT_ALLOW_PRIVATE_URLS` is read per-call (tests toggle it) — a deployment-hardening follow-up could pin it off in production startup assertions.
- The `random`-in-seeds false-positive class will re-fire on every Mimosa scan while the findings stay open; an upstream allowlist annotation mechanism (scanner-side) would remove the noise.
- `spineUrl()` covers server-side BFF routes only; a separate client-safe helper (`NEXT_PUBLIC_API_URL`) is future work if offsites/intake-fast ever need unified validation.

