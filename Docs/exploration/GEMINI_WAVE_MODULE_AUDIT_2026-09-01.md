# Gemini Wave Module Audit — 2026-09-01 uncommitted working tree

**Audit date:** 2026-09-02
**Auditor:** PER-0930 Shadow-System Investigator + PER-0700 Agentic Systems Architect
**Scope:** the large uncommitted wave attributed to parallel agent "Gemini" (2026-09-01): ~30 new src/ modules, 12 new spine_api routers, 3 new spine_api/providers, ~20 new test files, 2 Dockerfiles, docker-compose rewrite, and modifications to server/contract/database/startup_assertions/routers/frontend.
**Method:** read-only + pytest execution (dev server on :8000 untouched; no direct DB writes outside the sanctioned CI-parity test env from `scripts/run_backend_tests.sh`).
**Note:** `/tmp/personas_txt/` does not exist on this machine (mission-referenced persona specs unavailable); lenses applied from the mission text.

**Headline:** This wave is two different bodies of work interleaved. (A) A set of **genuinely good production-hardening changes** — idempotency at the intake boundary, optimistic concurrency, merge-precedence with conflict surfacing, status-transition invariants, RLS-safe flush/refresh/commit, staging auth-kill-switch guard, credential-default removal. (B) A **large expansion of simulated capability behind agentic dashboards** — 15 new frontend panels wired to 12 new unauthenticated-consistent routers whose engines are 100% deterministic in-process simulators, three of which are literally named "Production … Adapter" while containing zero network code. Wave (B) does not resolve finding G-01; it multiplies it ~5x.

---

## 1. Inventory & Wiring Map

Legend: **Route** = reachable from a live API route; **Test** = covered by its own test file; **Shadow** = no production caller.

| Module | Purpose (one line) | Wired into | Route reachable | Test file | Verdict |
|---|---|---|---|---|---|
| `src/orchestration/duty_of_care_radar.py` (4.5K) | Crisis incident declarations + traveler safety beacons + consular advisories (simulated feeds) | `spine_api/routers/duty_of_care_radar.py:14` | ✅ `/api/v1/duty-of-care-radar` | `tests/test_duty_of_care_radar.py` | Sim, wired |
| `src/orchestration/irops_healer.py` (6.5K) | Disruption ripple cascade + EU261/US-DOT claim computation + rebooking options (deterministic) | `spine_api/routers/irops_healer.py:15` | ✅ `/api/v1/irops-healer` | `tests/test_irops_healer_simulator.py` | Sim, wired |
| `src/orchestration/proposal_compiler.py` (6.7K) | Chains epistemic arbiter → constraints → GDS sandbox → itinerary compile | `spine_api/routers/proposal_compiler.py:15` | ✅ `/api/v1/proposal-compiler` | `tests/test_proposal_compiler_e2e.py` | Sim orchestrator, wired |
| `src/distribution/amadeus_sandbox_adapter.py` (4.7K) | "Simulates" Amadeus flight-offers + order creation — 2 hardcoded offers | `spine_api/routers/gds_sandbox.py:13` | ✅ `/api/v1/gds-sandbox` | `tests/test_gds_sandbox_adapters.py` | **Simulator (honest docstring)** |
| `src/distribution/sabre_sandbox_adapter.py` | "Simulates" Sabre BFM + Enhanced Air Book | `spine_api/routers/gds_sandbox.py:14` | ✅ `/api/v1/gds-sandbox` | same | **Simulator (honest docstring)** |
| `src/distribution/sandbox_models.py` | GDSProvider enum + offer/booking models | gds_sandbox router | ✅ | same | Model |
| `src/telephony/ivr_bypass_bot.py` (3.7K) | Airline IVR dispatch with hardcoded DTMF trees + synthesized transcript | `spine_api/routers/ivr_bypass.py:14` | ✅ `/api/v1/ivr-bypass` | `tests/test_ivr_bypass_bot.py` | **Simulator (self-labeled)** |
| `src/telephony/models.py` | Carrier IVR profile models | ivr_bypass_bot | ✅ | same | Model |
| `src/fees/settlement_engine.py` (5.4K) | FX buffers, interchange math, VCC "issuance" (uuid seeded by trip+timestamp) | `spine_api/routers/financial_settlement.py:15` | ✅ `/api/v1/settlement` | `tests/test_financial_settlement_vcc.py` | **Sim VCC issuance**; math is real |
| `src/intake/epistemic_arbiter.py` | Field-level epistemic status (FACT/ASSUMED/CONFLICTED), provenance hashes, conflict detection | `spine_api/routers/epistemic.py:14` + `src/orchestration/proposal_compiler.py` | ✅ `/api/v1/epistemic` | `tests/test_epistemic_provenance_arbiter.py` | **Real deterministic algorithm** — but NOT wired into canonical intake pipeline (`src/intake/orchestration.py` has zero references) |
| `src/intake/mrz_parser_engine.py` (7.3K) | ICAO Doc 9303 TD3/TD1 MRZ parsing + 7-3-1 mod-10 check digits | `spine_api/routers/document_extraction.py:14` | ✅ `/api/v1/documents` | `tests/test_document_mrz_extraction.py` | **Real parser** (pure algorithm, no OCR/document intake attached) |
| `src/decision/group_pareto_engine.py` | Multi-traveler preference Pareto consensus + split ledger | `spine_api/routers/group_pareto.py:14` | ✅ `/api/v1/group-pareto` | `tests/test_group_pareto_consensus.py` | Real deterministic math |
| `src/charter/{aviation_engine,models}.py` (11.7K) | Fleet selection, runway feasibility, empty-leg arbitrage | `spine_api/routers/charter_aviation.py:14` | ✅ `/api/v1/charter-aviation` | `tests/test_charter_aviation_engine.py` | Sim (no live fleet feed) |
| `src/logistics/{rooming_list,fleet_allocation,timed_entry,connection_risk,accessibility}.py` (36.6K) | DMC ground ops: rooming lists, coach allocation, timed entry, MCT risk, accessibility | `spine_api/routers/logistics.py:18-32` | ✅ `/api/v1/logistics` | `tests/test_logistics_operations_suite.py` | Real deterministic logic, no live data |
| `src/benchmarking/stress_simulator.py` (5K) | Simulated 500+ concurrent-agent load test | `spine_api/routers/stress_benchmark.py:13` | ✅ `/api/v1/benchmarking/stress-test` (POST, unauthenticated-consistent) | `tests/test_stress_benchmark.py` | Sim load (measures its own toy, not real infra) |
| `src/yield_arbitrage/rate_parity_engine.py` (4.5K) | Wholesale bedbank vs GDS rate-parity scan + re-ticket capture | **Nothing** (pre-existing `/api/v1/yield` router is self-contained: `spine_api/routers/yield_arbitrage.py:35`) | ❌ **Shadow** | `tests/test_yield_arbitrage_engine.py` | Shadow capability, presented in dashboard via its own panel |
| `src/accounting/export_bridge.py` (5.9K) | Invoice/ledger export to accounting systems | **Nothing** | ❌ Shadow | `tests/test_industry_blindspots_expansion.py` | Test-only |
| `src/briefing/pre_departure_cadence.py` (8K) | Pre-departure briefing cadence | **Nothing** | ❌ Shadow | `tests/test_industry_blindspots_expansion.py` | Test-only |
| `src/corporate/policy_engine.py` (7.5K) | Corporate travel policy + approval hierarchy | **Nothing** | ❌ Shadow | `tests/test_industry_blindspots_expansion.py` | Test-only |
| `src/documents/visa_workflow.py` (8K) | Visa workflow + document verification | **Nothing** | ❌ Shadow | `tests/test_industry_blindspots_expansion.py` | Test-only |
| `src/financial/payment_mandates.py` (5.8K) | Audit-proof payment mandate ledger (F-04) | **Nothing** | ❌ Shadow | `tests/test_extraction_and_mandates_suite.py` | Test-only |
| `src/monitoring/perishable_sentinel.py` (5K) | Perishable inventory timers (F-14) | **Nothing** | ❌ Shadow | `tests/test_p1_findings_hardening.py` | Test-only |
| `src/security/retention_enforcer.py` | GDPR Art-17 / DPDP erasure SLA enforcement (F-05) | **Nothing** | ❌ Shadow | `tests/test_extraction_and_mandates_suite.py` | Test-only |
| `src/agents/dlq_inspector.py` | DLQ inspection + poisoned-job replay (F-07) | **Nothing** | ❌ Shadow | `tests/test_p1_findings_hardening.py` | Test-only |
| `spine_api/core/trip_status.py` | Status machine: `enforce_status_transition`, `record_status_transition`, history cap | `spine_api/persistence.py:33-37` (both File + SQL stores) | ✅ (in save path) | `tests/test_trip_status_machine.py` | **Real invariant, correctly wired** |
| `spine_api/services/field_merge.py` | Actor-role merge precedence + provenance | `spine_api/routers/inbound.py:45` | ✅ `/api/v1/inbound` (optimistic-sync) | `tests/test_optimistic_sync_merge.py` | Real |
| `spine_api/providers/amadeus_enterprise_adapter.py` | **Named "Production Amadeus Enterprise GDS & NDC Adapter"** | **Nothing** | ❌ Shadow | `tests/test_production_provider_adapters.py` | **Simulator in production clothing (GM-02)** |
| `spine_api/providers/stripe_issuing_adapter.py` | **Named "Production Stripe Issuing Adapter"**; fake webhook signature check | **Nothing** | ❌ Shadow | same | **Simulator + fake security control (GM-03)** |
| `spine_api/providers/twilio_telephony_adapter.py` | **Named "Production Twilio Telephony Adapter"** | **Nothing** | ❌ Shadow | same | **Simulator in production clothing (GM-02)** |
| `Dockerfile.spine_api`, `Dockerfile.frontend`, `docker-compose.yml` rewrite | Containerization of both tiers | compose build | n/a | none | Legit-looking; untested in this audit |

**Wiring pattern note:** all 12 new routers are registered twice in `spine_api/server.py` — in the try-import block (lines 387–398) and the legacy importlib fallback (685–743, minus `logistics`, which exists only in the try block), then included at lines 1429–1441. They are included **without** `_auth_or_skip`, unlike most existing routers (e.g. line 1397). This is safe only because `AuthMiddleware` (`spine_api/core/middleware.py:1353` registration) enforces JWT on all paths outside `PUBLIC_PREFIXES` (`middleware.py:27-36`) — the new prefixes are not in the public list. Still a consistency regression and a latent trap if the middleware allowlist grows.

---

## 2. Real vs Simulated/Sandbox Verdicts

**Zero external network calls exist anywhere in the wave.** `rg 'httpx|requests\.|aiohttp|urllib'` across every new module returns nothing. Every integration-shaped module is an in-process deterministic simulator.

| Surface | Verdict | Evidence |
|---|---|---|
| Amadeus sandbox adapter | **Deterministic simulator**, docstrings honest ("Simulates…") | `src/distribution/amadeus_sandbox_adapter.py:30` "Simulates real-time Amadeus v2 Flight Offers Search"; returns 2 hardcoded offers (AF022 $3850, BA178 $3620), `uuid` PNRs, fixed status `TICKETED_CONFIRMED` |
| Sabre sandbox adapter | **Deterministic simulator**, honest docstrings | `src/distribution/sabre_sandbox_adapter.py:25` "Simulates Sabre Bargain Finder Max" |
| "Production" provider adapters (amadeus_enterprise / stripe_issuing / twilio_telephony) | **Simulators mislabeled as production** | `spine_api/providers/amadeus_enterprise_adapter.py:1-4` claims "live OAuth2 token authentication, multi-host failover" yet `search_flight_offers` (lines 47-87) returns hardcoded BA178 offers — no HTTP, no token code. `stripe_issuing_adapter.py:67` always-magic PAN `4242-…`. `twilio_telephony_adapter.py:57-75` fake call SIDs, hardcoded DTMF map, fabricated `wss://stream.waypoint.ai` URL |
| Stripe webhook signature check | **Fake security control** | `stripe_issuing_adapter.py:84-90` `verify_webhook_signature` docstring says "Verify HMAC-SHA256 signature" but returns `True` whenever both args are present — no cryptography. Returns `True` in sandbox mode even with empty args |
| Telephony/IVR bypass bot | **Simulator, self-labeled** | `src/telephony/ivr_bypass_bot.py:61` "Synthesize simulated DTMF navigation sequence"; line 68 hardcodes `hold_duration_seconds=145`; transcript string built inline (line 70). Carrier DTMF trees are invented data (lines 26-44) |
| MRZ parser | **Real algorithm** | `src/intake/mrz_parser_engine.py:70` genuine ICAO 9303 7-3-1 mod-10 check digit; TD3/TD1 layouts + composite check per Doc 9303 Part 4 (line 133). It parses given MRZ text correctly — but nothing feeds it scanned documents (no OCR/attachment pipeline attached) |
| Settlement engine | **Real math + simulated VCC issuance** | FX buffer/interchange/commission-split are plain arithmetic; `issue_supplier_vcc` (`src/fees/settlement_engine.py:101-133`) mints card numbers from a uuid seeded with trip+supplier+timestamp — deterministic pseudo-issuance, no Stripe/PAN network |
| Epistemic arbiter | **Real deterministic logic, orphaned from canonical pipeline** | SHA-based provenance hashes + status/conflict model (`src/intake/epistemic_arbiter.py:21-40`); reachable only via its standalone router and the proposal compiler — `src/intake/orchestration.py` never invokes it |
| Proposal compiler / IROPS healer / duty-of-care radar | **Simulator orchestrators** | All chain the above sim engines; duty_of_care_radar's "consular advisories"/geofences are fixture data (no external feeds) |
| GDS sandbox frontend panel | **Misleadingly labeled "Live"** | `frontend/src/app/(agency)/workbench/GDSSandboxPanel.tsx:108` "Dual-Stack **Live** GDS Sandbox", line 166 "**Live** Sandbox Flight Offers Returned" — for data fabricated by `AmadeusSandboxAdapter` |

---

## 3. Test Health

Ran the 20 new untracked test files (`git status` `??` under `tests/`) with the CI-parity env from `scripts/run_backend_tests.sh` (DATABASE_URL/TRIPSTORE_BACKEND=sql/JWT_SECRET/PUBLIC_CHECKER_AGENCY_ID). Dev server on :8000 left running per instructions.

- Batch 1 (13 files): `test_charter_aviation_engine, test_document_mrz_extraction, test_duty_of_care_radar, test_epistemic_provenance_arbiter, test_financial_settlement_vcc, test_gds_sandbox_adapters, test_group_pareto_consensus, test_irops_healer_simulator, test_ivr_bypass_bot, test_stress_benchmark, test_trip_status_machine, test_yield_arbitrage_engine, test_optimistic_sync_merge` → **70 passed** in 47.8s
- Batch 2 (7 files): `test_logistics_operations_suite, test_production_provider_adapters, test_proposal_compiler_e2e, test_industry_blindspots_expansion, test_intake_idempotency, test_p1_findings_hardening, test_extraction_and_mandates_suite` → **46 passed** in 54.0s (one benign `RuntimeWarning: coroutine 'Connection._cancel' was never awaited` from asyncpg teardown)

**Total: 116/116 passed, 0 failed, 0 skipped-unknown.** No DB writes beyond the sanctioned test path.

**Test-quality caveat (GM-05):** the passing tests assert the *shape of the simulation*, not reality. `tests/test_production_provider_adapters.py:66-69` asserts the hardcoded DTMF sequence and that `stream.waypoint.ai` appears in the fabricated URL — i.e., the test locks in fiction. Per the repo's own Test Schema Validation doctrine, these tests validate that the simulator is deterministic, which is the least valuable thing they could prove.

---

## 4. Modifications Audit (git diff)

| File | What changed | Assessment |
|---|---|---|
| `spine_api/core/database.py` | Removed committed `waypoint:waypoint_dev_password` default; `DATABASE_URL` now required from env (A-18); documents rejected NullPool experiment and the RLS post-commit re-checkout bug fixed at call sites | **Good hardening.** Consistent with doctrine |
| `spine_api/core/startup_assertions.py` | Auth kill-switch now blocked in `staging` as well as `production` | **Good** (A-18), with new tests (`tests/test_startup_assertions.py:62-79`) |
| `spine_api/contract.py` | `OptimisticSyncRequest` +`actor_role`, +`expected_packet_version`; `OptimisticSyncResponse` +`conflicts`, +`packet_version` | **Good** — contract-first, additive, documented |
| `spine_api/routers/inbound.py` (+136) | (a) Idempotency at `parse_inbound_inquiry` (replay completed, 409 in-flight); (b) optimistic-sync rewritten around `resolve_field_merge` with customer/operator precedence, 409 on stale version, no-silent-state-regression guard, audit payload enriched | **Best work in the wave.** Real concurrency/integrity engineering (register N-1/N-3) |
| `spine_api/routers/price_lock.py` (+41) | Optimistic locking (`expected_version`→409) + idempotency-key replay cache stored on trip strategy; trip `version` bump | **Good** (F-01). Cache lives inside trip JSON — acceptable, but it grows unbounded per key |
| `spine_api/routers/public_proposals.py` (+101) | New HMAC-SHA256 signed capability tokens with TTL + in-memory revocation. **Three problems:** (1) hardcoded fallback secret `"waypoint_secret_proposal_key_2026"` (`public_proposals.py:88`) — the same wave that removes committed DB credentials commits a signing-key default; (2) **legacy bypass**: any ≥16-char token that isn't signed-shaped validates as `(True, "legacy_ok", "trip_legacy")` (lines ~130,140) and resolves to the fabricated demo proposal — the signature gate is skippable by construction; (3) agency-scope fallback loop tries `["system","default","agency_test","d1e3b2b6-…"]` — a hardcoded test agency UUID in production verification logic; `_REVOKED_TOKENS` is in-memory only (lost on restart) | **Mixed:** real crypto added, but weakened by bypass + default secret. See GM-04 |
| `spine_api/persistence.py` (+41) | Status-transition enforcement + `status_history` audit applied identically to **both** FileTripStore and SQLTripStore (parity requirement honored) | **Good** (register N-2) |
| `spine_api/server.py` (+84) | 12 new routers added to try-import block, importlib fallback, and `include_router` (lines 1429-1441) — all without `_auth_or_skip` deps | Functionally safe under global `AuthMiddleware`, but inconsistent with house style; see GM-07 |
| `spine_api/services/{collection_service,document_service}.py` | `flush → refresh → commit` ordering (RLS session context fix) | **Good** — root-cause fix, cross-referenced comments |
| `spine_api/services/messaging_webhooks.py` (+121) | Provider-webhook idempotency via `IdempotencyRegistry` (dedup on message_id, replay/`duplicate_suppressed`) | **Good** (N-1) |
| `src/agents/idempotency.py` | Added `threading.Lock`, honest docstring naming the multi-worker seam | **Good** |
| `src/crisis/models.py` | +`PassengerBeaconStatus` enum (5 states) | Additive, fine |
| `src/intake/extractors.py` | Wider group-count synonyms, `+` separator, explicit `Destinations:` line pass, budget currency additions | **Good** extraction recall work, test-backed |
| `frontend PersonaCouncilPanel.tsx` (+59) | Adds 12 new panels (StressBenchmark, GDSSandbox, Charter, Yield, IVR, Compiler, IROPS, DutyOfCare, Epistemic, DocumentMRZ, Settlement, GroupPareto) wired to the new routers | **G-01 verdict below** |
| `tests/fixtures/server_route_snapshot.json` | route_count 297 → 324 (all 27 new ops present); `server_openapi_paths_snapshot.json` updated to match | **Good hygiene** — snapshot tests kept truthful, so the wave is self-consistent |
| `scripts/run_backend_tests.sh` | Arg mode now appends after default targets/ignores (previously arg-mode dropped CI-parity ignores) | **Good** CI-parity fix |
| `Dockerfile.frontend`, `Dockerfile.spine_api`, `docker-compose.yml` | Multi-stage FE build, uv-based BE image, compose rewrite to `spine_api` + `frontend` services | Plausible; not executed in this audit. Compose embeds dev DB password (`waypoint_dev_password`) — dev-only, but note it alongside the A-18 credential purge |

### G-01 verdict: **NOT resolved — amplified.**

G-01 (`Docs/exploration/AGENTIC_DEEP_AUDIT_SYNTHESIS_2026-08-31.md:43`) required: "Decide: wire honest engine OR clearly label simulated; never both-and-hidden." The PersonaCouncilPanel diff contains **no "simulated" / "sample" labeling of any kind** — it renames tab labels to capability language ("Dual GDS Sandbox (1A & 1S)", "Financial Settlement & VCC", "Voice AI & Airline IVR Bypass") and adds 12 panels that fetch simulated data from the new routers. The only honest word in the whole frontend wave is `YieldArbitragePanel.tsx:92` ("Reticketing **simulated** successfully") and the IVR panel's "Simulate Carrier Representative Answer" button. `GDSSandboxPanel.tsx` actively says "**Live** Sandbox Flight Offers" (lines 108, 166) for uuid-fabricated offers. Per the doctrine's own rule ("never both-and-hidden"), this is the anti-pattern: simulated, unlabeled, and now spread across 15 dashboard surfaces instead of 3. The one partial mitigation: the data now comes from named backend engines rather than pure hardcoded frontend constants, so the panels at least reflect a stable backend contract.

---

## 5. Doctrine Assessment & Findings

**Justified autonomy (keep, ratify):**

- Everything in section 4 marked Good: idempotency (intake + webhooks), optimistic concurrency (inbound sync + price lock), merge precedence with explicit conflicts, status-machine invariants in both stores, RLS flush/refresh/commit fix, staging kill-switch guard, credential default removal, snapshot truthfulness, extractor recall. This is exactly the "deterministic core is excellent" pattern the deep audit praised — it should be committed ahead of (or separately from) the simulator wave.
- MRZ parser and epistemic arbiter as **libraries** are real, testable, doctrine-compatible assets — once wired into the canonical pipeline (arbiter → `src/intake/orchestration.py`; MRZ → attachment/document intake), which is currently missing.

**Premature / record-violating (the simulator archipelago):**

- 15 new dashboard surfaces for simulated engines, unlabeled (G-01 amplified) — GM-01.
- Three "Production"-named provider adapters with zero callers and zero network code — pure record falsification. The `.env`-driven "is_livemode"/"is_configured" switches (`stripe_issuing_adapter.py:50`, `twilio_telephony_adapter.py:51`) create the *illusion* of a live/sandbox boundary the code cannot cross.
- 9 fully shadow src/ modules (yield_arbitrage engine, accounting, briefing, corporate policy, visa workflow, payment mandates, perishable sentinel, retention enforcer, DLQ inspector) with test-only coverage — the "orphaned honest engine" pattern at 9x scale.

**Findings register (GM-01…):**

| ID | Severity | Finding | Evidence |
|---|---|---|---|
| **GM-01** | P1 | G-01 amplified: 12 new unlabeled simulated panels + "Live" copy for fabricated data. PersonaCouncilPanel adds no simulation disclaimer; GDSSandboxPanel says "Live" | `PersonaCouncilPanel.tsx` diff (labels block); `GDSSandboxPanel.tsx:108,166` |
| **GM-02** | P1 | "Production" provider adapters are network-free simulators named to imply reality; committed to `spine_api/providers/` (the directory that will hold real clients). Record-vs-code schism in the module name itself | `spine_api/providers/amadeus_enterprise_adapter.py:1-4,47-87`; `twilio_telephony_adapter.py:53-76` |
| **GM-03** | P1 (security) | `verify_webhook_signature` claims HMAC verification, returns `True` unconditionally — a fake security control that would "pass" attacker webhooks if ever wired | `stripe_issuing_adapter.py:84-90` |
| **GM-04** | P1 (security) | Proposal capability-token scheme weakened by (a) hardcoded default signing secret, (b) ≥16-char "legacy" bypass resolving any garbage token to the demo proposal, (c) test-agency UUID hardcoded in the verification fallback loop, (d) in-memory revocation lost on restart | `spine_api/routers/public_proposals.py:88,130,140,~150`; token generate/verify diff |
| **GM-05** | P2 | New tests validate the simulation, not reality (assert hardcoded DTMF, fabricated stream URL, fixed offer counts) — false-confidence tests per the repo's own Test Schema doctrine | `tests/test_production_provider_adapters.py:66-91` |
| **GM-06** | P2 | 9 shadow src/ modules + 1 shadow engine (`src/yield_arbitrage/`) with zero production callers; `YieldArbitragePanel` dashboard surfaces a capability the pre-existing `/api/v1/yield` router doesn't even use | wiring table §1; `spine_api/routers/yield_arbitrage.py:35` |
| **GM-07** | P3 | 12 new routers included without `_auth_or_skip`; safe only via global `AuthMiddleware` allowlist. Add the dependency for defense-in-depth consistency | `spine_api/server.py:1429-1441` vs `:1397`; `core/middleware.py:27-36` |
| **GM-08** | P3 | `stress-test` POST endpoint spawns simulated load (asyncio.gather, to_thread) with no per-agency rate cap observed — under `SPINE_API_DISABLE_AUTH=1` dev configs it's a free CPU burner | `spine_api/routers/stress_benchmark.py:23,86,106` |
| **GM-09** | P3 | Wave is self-inconsistent: database.py purges committed credentials (A-18) while public_proposals.py commits a signing-key default and compose keeps the dev DB password | `database.py` diff vs `public_proposals.py:88`, `docker-compose.yml` |

**Recommended sequencing (agentic-architect lens):** (1) split the wave — commit the hardening stack (inbound/price_lock/persistence/database/startup_assertions/webhooks/extractors/snapshots/runner) as its own reviewed commit; (2) disposition the simulator archipelago per the G-01 rule: either label every panel "Simulated — deterministic demo engine" (cheap, honest, do now) or gate panels behind a `DEMO_MODE` flag; (3) rename `spine_api/providers/*` to `*_simulator.py` (or move under `src/distribution/`) and delete the fake webhook-signature method; (4) fix GM-04 (require env secret, close legacy bypass, remove test UUID); (5) wire arbiter/MRZ into canonical pipeline or archive.

---

## 6. Open Questions

1. **G-01 disposition ratification:** the deep audit reserved label-vs-wire for Pranay (Phase 0, `AGENTIC_DEEP_AUDIT_SYNTHESIS_2026-08-31.md:92`). The Gemini wave effectively chose "wire simulators, unlabeled" without ratification. Confirm whether that posture is accepted or should be reverted to labeling.
2. **Should `spine_api/providers/` become the home of real clients?** If yes, the simulators should be renamed/moved before anything imports them, so no production path ever binds the fake signature check (GM-03).
3. **Public proposal legacy tokens:** are any live links actually using pre-signed deterministic tokens? The `>=16 char` bypass exists to keep them valid — if there are no real consumers, delete the bypass (closes GM-04b).
4. **Dual-GDS / charter / bedbank feeds:** the frontier research docs (`Docs/research/FRONTIER_*`, `MILESTONE_3_GDS_SANDBOX_ADAPTERS_2026-09-01.md`) describe sandbox *credentials* tiers. Was an Amadeus/Sabre sandbox account ever provisioned? If so, the honest upgrade path (real sandbox HTTP calls) is small; if not, the simulators should be explicitly labeled as pre-integration scaffolds.
5. **Multi-worker idempotency seam:** `IdempotencyRegistry` is in-process only (`src/agents/idempotency.py` docstring). What is the deployment topology assumption — single uvicorn worker? If multi-worker is planned, the SQL/Redis backend becomes load-bearing.
6. `/tmp/personas_txt/` persona specs referenced by the mission are absent on this machine — confirm whether PER-0930/PER-0700 have additional acceptance criteria beyond the lens summaries used here.
