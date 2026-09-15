# Findings — Live View (GENERATED — DO NOT EDIT)

**Generated:** 2026-09-14T18:06:22+00:00 by `scripts/findings.py render` — this file is a projection of the
append-only event store `Docs/review/FINDINGS_STORE.jsonl`. **The store is canonical;**
edit state only through the CLI (`open` / `close` / `defer` / `reverify` / `import`).

**Counts:** 290 findings — closed 192 · deferred 5 · open 93 · stale open (> 45d): 0

## Open

| ID | Aliases | Pri | Title | Last verified |
|----|---------|-----|-------|---------------|
| FND-0012 | R-12 | P2 | No Journey Dependency Graph for IROPS | 2026-08-31 |
| FND-0014 | R-14 | P3 | Two-generation styling (literal-hex ∥ primitives) | 2026-08-31 |
| FND-0026 | A-10 | P2 | IDEA pad no longer reflects shipped reality | 2026-08-31 |
| FND-0027 | A-11 | P2 | Four concurrent marketing generations live | 2026-08-31 |
| FND-0031 | A-15 | P2 | Frontend debt is undocumented, not absent | 2026-08-31 |
| FND-0033 | A-17 | P3 | `WelcomeModal` name overstated modal semantics | 2026-09-04 |
| FND-0036 | A-20 | P2 | Frontier migration and model/schema ownership drift | 2026-09-05 |
| FND-0054 | F-17 | P2 | partial 2026-09-08 — companion URL/request lifecycle, stale-response/token-reset, explicit request states and  | 2026-09-08 |
| FND-0056 | F-19 | P2 | open 2026-09-08 — execution status records nine failures/37 setup errors with observed ENOSPC and PostgreSQL r | 2026-09-08 |
| FND-0061 | F-24 | P3 | DEMO-05: `/inbox` renderer crash — verdict: dev-noise, not product defect | 2026-08-31 |
| FND-0062 | F-25 | P2 | DEMO-06/09: Repair-surface UX no-op; banner lacks missing-field names | 2026-08-31 |
| FND-0063 | F-26 | P3 | DEMO-07: Copy/label drift (WORK EMAIL / <you@agency.com> / Waypoint HQ / runtime chip) | 2026-08-31 |
| FND-0067 | G-01 | P1 | open 2026-09-02 — disposition still unratified; wave amplified it (see GM-01) | 2026-09-02 |
| FND-0068 | G-02 | P1 | open 2026-09-02 | 2026-09-02 |
| FND-0069 | G-03 | P2 | open 2026-09-02 — ratify wire-vs-archive | 2026-09-02 |
| FND-0080 | G-14 | P2 | open 2026-09-02 | 2026-09-02 |
| FND-0081 | G-15 | P2 | open 2026-09-02 | 2026-09-02 |
| FND-0083 | G-17 | P3 | open 2026-09-02 | 2026-09-02 |
| FND-0087 | GM-02 | P1 | ⚠️ PARTIAL 2026-09-02 (in-flight) — docstrings now honest ("Sandbox Amadeus/Stripe/Twilio … Adapter", "SIMULAT | 2026-09-02 |
| FND-0090 | GM-05 | P2 | open 2026-09-02 — `tests/test_production_provider_adapters.py` unchanged in this respect | 2026-09-02 |
| FND-0091 | GM-06 | P2 | open 2026-09-02 — re-verified by rg: payment_mandates, perishable_sentinel, retention_enforcer, dlq_inspector, | 2026-09-02 |
| FND-0093 | GM-08 | P3 | open 2026-09-02 — `spine_api/routers/stress_benchmark.py` has no limiter (rg 2026-09-02) | 2026-09-02 |
| FND-0107 | GF-04 | P3 | open 2026-09-02 — zero-settings render unverified | 2026-09-02 |
| FND-0114 | REC-1 | P1 | open 2026-09-02 — chronicle title discloses simulation, but the per-case-study simulator-caveat annotation pas | 2026-09-02 |
| FND-0126 | F-39 | P3 | Webhook dedup call-site dormant. `process_inbound_traveler_message` (F-28's deduped path) is reached by no pro | 2026-08-31 |
| FND-0127 | F-40 | P2 | open (verify first) | 2026-08-31 |
| FND-0130 | F-43 | P1 | open 2026-09-06 — exposure materially narrowed 2026-09-07: the fulfillment endpoint now requires a signed prop | 2026-09-07 |
| FND-0157 | PA-18 | P2 | Memory write-only AND forgetting never executes (decay/GDPR/eligibility zero callers) | 2026-08-31 |
| FND-0158 | PA-19 | P2 | Audit chain never verified in prod; trim breaks predecessor chain; `/api/audit` split store | 2026-08-31 |
| FND-0159 | PA-22 | P2 | LLM-as-judge default scores output shape; uncalibrated; no prod consumer | 2026-08-31 |
| FND-0160 | PA-29 | P3 | Lease/requeue terminal rows never expire | 2026-08-31 |
| FND-0161 | PA-30 | P3 | Checkpoint/DLQ in-memory, zero callers; DLQ replay flips status without executing | 2026-08-31 |
| FND-0162 | PA-31 | P3 | RetentionEnforcer declared-only (purges nothing) | 2026-08-31 |
| FND-0163 | PA-32 | P3 | Memory `verify_integrity` dead code; epistemic `ProvenanceSlot` write-only (memory authority weights ARE consu | 2026-08-31 |
| FND-0164 | PA-33 | P3 | RAG groundedness lexical-overlap; echo-hallucinations pass | 2026-08-31 |
| FND-0165 | PA-34 | P3 | Evals measure accuracy only; no cost/latency/human-intervention dims | 2026-08-31 |
| FND-0166 | PA-35 | P2 | Agency-boundary | 2026-08-31 |
| FND-0167 | PA-36 | P3 | Agency-boundary | 2026-08-31 |
| FND-0168 | PA-37 | P3 | Watchdog detects only dashboard-sum drift | 2026-08-31 |
| FND-0169 | PA-39 | P3 | Draft promote bypasses optimistic-version support; second promote overwrites linkage | 2026-08-31 |
| FND-0170 | PA-40 | P3 | Durable idempotency CAS wired to only 2 ingress paths (run now wired via PA-13; price-lock/fulfillment/promote | 2026-08-31 |
| FND-0178 | AT-08 | P2 | Supervised fleet is scan-and-stamp, not auto-IROPS | 2026-08-31 |
| FND-0180 | AT-10 | P2 | Memory must not auto-select inventory | 2026-08-31 |
| FND-0184 | AT-14 | P2 | Two consensus engines, neither binds booking | 2026-08-31 |
| FND-0186 | AT-16 | P2 | Fare hold never feeds JDG | 2026-08-31 |
| FND-0187 | AT-17 | P2 | EU261 preview number, not a case | 2026-08-31 |
| FND-0188 | AT-18 | P2 | Companion SOS is `setTimeout` demo | 2026-09-08 |
| FND-0191 | EV-02 | P1 | partial 2026-09-05 — all 15 master-inventory F/R collisions have reviewed source-qualified relationships in FI | 2026-09-05 |
| FND-0192 | EV-03 | P1 | partial 2026-09-05 — bounded independent review corrected A-06/A-20/F-17 descriptions and lease follow-up pros | 2026-09-05 |
| FND-0193 | EV-04 | P1 | open 2026-09-05 | 2026-09-05 |
| FND-0194 | EV-05 | P2 | open 2026-09-05 | 2026-09-05 |
| FND-0197 | EV-08 | P1 | open 2026-09-05 | 2026-09-05 |
| FND-0199 | EV-10 | P2 | partial 2026-09-05 — correction recorded in request trace; wider stale overlays remain under EV-03 | 2026-09-05 |
| FND-0200 | EV-11 | P1 | open 2026-09-05 | 2026-09-05 |
| FND-0201 | A-04@FINDINGS_TASKS_CONSOLIDATED_2026-08-30 | P1 | Consolidate 9 duplicate/shadow systems (audit stores, dual auth decode, audit_bridge deletion, membership, sco | 2026-09-14 |
| FND-0204 | A-07@FINDINGS_TASKS_CONSOLIDATED_2026-08-30 | P1 | Doc-tree consolidation (`Docs/` vs `frontend/docs/`), inode collision fix, CHANGELOG backfill | 2026-09-14 |
| FND-0205 | A-10@FINDINGS_TASKS_CONSOLIDATED_2026-08-30 | P2 | Reconcile IDEA_PAD against git (mark IDEA-120/122/123/124 done; re-date WIP registry) | 2026-08-30 |
| FND-0206 | A-11@FINDINGS_TASKS_CONSOLIDATED_2026-08-30 | P2 | One marketing surface (retire `app/v2`–`v4`, keep `v5`) | 2026-08-30 |
| FND-0207 | A-12@FINDINGS_TASKS_CONSOLIDATED_2026-08-30 | P1 | Resolve inert `src/proxy.ts`: restore real `middleware.ts` or delete; resolve Next 16/14 version skew (ADR the | 2026-09-14 |
| FND-0208 | A-08@FINDINGS_TASKS_CONSOLIDATED_2026-08-30 | P2 | Repoint 18 `motto_v4.md` references at `FIRST_PRINCIPLES_MOTTO_V4_DOCTRINE.md`; CI dangling-reference check | 2026-09-14 |
| FND-0209 | A-16@FINDINGS_TASKS_CONSOLIDATED_2026-08-30 | P2 | Ratcheting vitest coverage thresholds; first booking-path smoke e2e (zero e2e exist) | 2026-08-30 |
| FND-0210 | A-15@FINDINGS_TASKS_CONSOLIDATED_2026-08-30 | P2 | Reduce 65 `any` in prod code (hotspot `DecisionTab.tsx`); justify the 4 `eslint-disable`s | 2026-08-30 |
| FND-0211 | A-17@FINDINGS_TASKS_CONSOLIDATED_2026-08-30 | P3 | Fix `WelcomeModal` a11y (no `role="dialog"`/`aria-modal`; hand-rolled toast-sheet) | 2026-08-30 |
| FND-0213 | R-11@FINDINGS_TASKS_CONSOLIDATED_2026-08-30 | P2 | Implement durable agent lease per design: heartbeat refresh, fencing token, STALE sweep, agency scoping (`Exec | 2026-08-30 |
| FND-0214 | R-16@FINDINGS_TASKS_CONSOLIDATED_2026-08-30 | P2 | OTel trace-correlation reader + CI event-flow assertion (spans exist, no consumer) | 2026-08-30 |
| FND-0215 | R-14@FINDINGS_TASKS_CONSOLIDATED_2026-08-30 | P3 | Frontend styling unification per design doc | 2026-08-30 |
| FND-0216 | R-13@FINDINGS_TASKS_CONSOLIDATED_2026-08-30 | P2 | Nav rollout-gate drift (`nav-modules.ts` `complete: false` vs "14/14 active" claim) — needs product decision f | 2026-08-30 |
| FND-0217 | R-10@FINDINGS_TASKS_CONSOLIDATED_2026-08-30 | P2 | Server decomposition per plan (`create_app()` factory; rejects microservices); single audit store decision (re | 2026-08-30 |
| FND-0222 | F-05@FINDINGS_TASKS_CONSOLIDATED_2026-08-30 | P1 | `src/security/jurisdiction_policy.py` declares retention/erasure/residency/breach SLAs; zero enforcement wirin | 2026-09-14 |
| FND-0223 | F-06@FINDINGS_TASKS_CONSOLIDATED_2026-08-30 | P2 | Audit-chain evidence gaps: file hash-chain unsigned/unanchored; run-ledger step files entirely outside the cha | 2026-08-30 |
| FND-0225 | F-08@FINDINGS_TASKS_CONSOLIDATED_2026-08-30 | P2 | `core/locking.py` silently falls back to in-process asyncio locks when not on Postgres → dev/tests/misconfigur | 2026-08-30 |
| FND-0226 | F-09@FINDINGS_TASKS_CONSOLIDATED_2026-08-30 | P2 | `run_ledger.py` checkpoints only to local disk while state is SQL-backed → rolling deploys orphan RUNNING runs | 2026-08-30 |
| FND-0227 | F-10@FINDINGS_TASKS_CONSOLIDATED_2026-08-30 | P2 | `agent_work_coordinator.py` leases have no pipeline-version check → a deploy splits a run across two code gene | 2026-08-30 |
| FND-0228 | F-11@FINDINGS_TASKS_CONSOLIDATED_2026-08-30 | P2 | `usage_guard` meters spend at call time only: no auto-quiesce when a tenant goes berserk; no parent→child spen | 2026-08-30 |
| FND-0229 | F-12@FINDINGS_TASKS_CONSOLIDATED_2026-08-30 | P2 | SSE fan-out (`run_events.py`, `run_status.py`) has no per-tenant connection cap, heartbeat, or eviction | 2026-08-30 |
| FND-0231 | F-14@FINDINGS_TASKS_CONSOLIDATED_2026-08-30 | P1 | Dated perishables (visas, quote TTLs, insurance windows, payment deadlines, ticketing limits) tracked per-arti | 2026-09-14 |
| FND-0232 | F-15@FINDINGS_TASKS_CONSOLIDATED_2026-08-30 | P2 | `confirmation_service.py` treats every defective supplier confirmation (missing segments, mismatched names) as | 2026-08-30 |
| FND-0233 | F-16@FINDINGS_TASKS_CONSOLIDATED_2026-08-30 | P2 | Refund/compensation pipeline dead-ends (`passenger_rights_claims.py` + payment refund constants); no dispositi | 2026-08-30 |
| FND-0234 | EX-07 | P3 | Cross-dock EDIFACT/NDC payloads straight into trip documents (src: L1) | 2026-08-30 |
| FND-0235 | EX-08 | P3 | Forward-loaded capacity planning: departure-date demand vs lease capacity (src: L5) | 2026-08-30 |
| FND-0236 | EX-09 | P3 | AI-decision explanation dossier: replayable hashed evidence bundle per trip (src: R4) | 2026-08-30 |
| FND-0237 | EX-10 | P3 | Quarantine follow-ons: auto-classifier, unified ledger, dry-run + batch replay (src: O2 children) | 2026-08-30 |
| FND-0240 | F-17@FINDINGS_TASKS_CONSOLIDATED_2026-08-30 | P2 | Frontend suite debt (from RQ-06): TimelinePanel test races its async fetch (asserts before `Loading timeline…` | 2026-08-30 |
| FND-0244 | EX-02 | P2 | Epistemic status as product surface — what does the UI do when a belief is ASSUMED/UNKNOWN; operator experienc | 2026-08-30 |
| FND-0245 | EX-03 | P2 | Retirement as a first-class primitive — the repo's dominant failure mode is "built the replacement, never reti | 2026-08-30 |
| FND-0246 | EX-05 | P2 | Negative-space map — deliberately absent capabilities: payment execution, ticketing/GDS, supplier contracts, r | 2026-08-30 |
| FND-0248 | EX-14 | P2 | `TemporalObligation` primitive (ADHD provocation) — every deadline in the system (visa, price lock, payment, i | 2026-08-30 |
| FND-0250 | EX-12 | P2 | Standing travel-intent subscriptions: warm plan shelf, trips materialize on trigger (src: A3) | 2026-08-30 |
| FND-0251 | EX-13 | P2 | Git-like itinerary branch-and-merge with constraint re-validation on merge (src: A4) | 2026-08-30 |
| FND-0278 | — | P2 | Workbench: URL-vs-store stage/mode/scenario divergence (two sources of truth; hydrateFromDraft writes store, r | 2026-09-12 |
| FND-0281 | — | P3 | Workbench: dead code cluster — MemoryArchitectPanel/OutputPanel/FeedbackPanel dynamic imports never rendered;  | 2026-09-12 |
| FND-0283 | — | P3 | Workbench: whole-store zustand subscription re-renders entire 930-line component on any store change (no selec | 2026-09-12 |
| FND-0289 | — | P2 | LeadStage enum in src/intake/lifecycle.py is a third duplicate lead/status vocabulary — supersede into relatio | 2026-09-13 |

## Deferred

- **FND-0060** DEMO-04: Alex Morgan card hardcoded + unconditional + fake-facts injection; legacy `CUSTOMER_MEMORY_ — reopen when: Customer memory gains a durable, agency-scoped backing store (TripStore/SQL) or the legacy dict is removed; then close the residual as fixed or split into a fresh scoped finding.
- **FND-0082** deferred 2026-09-02 — parked behind golden-set SLM benchmark + telemetry gate per synthesis Phase 0/ — reopen when: Golden-set SLM benchmark and telemetry gate exist per synthesis Phase 0/4 (ADR_EDGE_SLM_ONNX_OFFLINE_INFERENCE track); revisit integration then.
- **FND-0249** Veto-window governance (src: A2) — dispatch-then-veto inside a time-boxed window feeding the overrid — reopen when: AT-track consensus/mandate dispatch lanes land (from FND-0185 ADR-008 ratification onward) or owner ratifies veto-window semantics as an immediate priority.
- **FND-0268** Quote margin gate uses modeled base-18% heuristic; fee_matrix real retail-minus-wholesale engine orp — reopen when: First real wholesale-cost producer lands (B6/B7 provider-connector lane) OR owner selects Option C (hard send-block) after ADR-008 §6 ratification (roadmap C1)
- **FND-0280** Workbench: NaN confidences synthesized into DecisionOutput (JSON-unsafe, poisons downstream comparis — reopen when: a numeric consumer of synthesized decision confidence appears, or spine types regenerate with nullable confidence fields

## Closed (recent 25)

- **FND-0260** [fixed] (agency)/quotes page renders fully fabricated pricing (hardcoded base 4200, fake tiers/status sent,  — evidence: frontend/src/app/(agency)/quotes/PageClient.tsx: SimulatedBadge + illustrative-model banner, statuses sent/under_review->draft, dead waypoint.agency link removed, share buttons disabled; honesty tests in quotes/__tests__/page.test.tsx 3/3 green
- **FND-0261** [fixed] FEATURE_LIST_V3 LIVE rows misstate wiring: G01/D09/E08 orphaned (no serving-path caller), I08 is dev — evidence: Docs/status/FEATURE_LIST_V3_2026-09-10.md: C02/D09/E08/E14/F01/F02/G01/G02/I08 corrected with orphan/preview/gate evidence; Method item 4 wiring-evidence rule; derived json/csv regenerated via tools/feature_list_generate.py (117 = 94/14/6/2/1)
- **FND-0262** [fixed] ENCRYPTION_KEY silently falls back to committed dev Fernet key outside DATA_PRIVACY_MODE=production; — evidence: spine_api/core/startup_assertions.py _check_encryption_key (prod/staging require DATA_PRIVACY_MODE=production + real Fernet key, committed dev key rejected); docker-compose ENCRYPTION_KEY fail-fast passthrough; fly.toml DATA_PRIVACY_MODE=production; 7 tests in test_startup_assertions.py
- **FND-0263** [fixed] .env.example omits required runtime vars (CAPABILITY_TOKEN_SECRET, REDIS_URL, WHATSAPP_*, TWILIO_*,  — evidence: .env.example new 'Required-by-assertion runtime variables' section: ENCRYPTION_KEY, DATA_PRIVACY_MODE, CAPABILITY_TOKEN_SECRET, REDIS_URL, WHATSAPP_*, TWILIO_*, STRIPE_* with honest placeholders + generation commands
- **FND-0264** [fixed] Suite-count receipts irreproducible (3718/4250/4350 across docs vs 4231 static); green total auto-sk — evidence: tools/test_inventory.py + tools/README.md: reproducible receipt (2026-09-11: 4563 collected / 4278 static / 10 skip-marked files / 32 markers / 2 CI-excluded); receipts now cite receipt+timestamp instead of bare totals
- **FND-0265** [fixed] LAUNCH_STATUS evidence snapshot stale: findings 183 rows (2026-09-04) vs store 258; test counts two  — evidence: Docs/LAUNCH_STATUS.md Evidence snapshot refreshed 2026-09-11: dated rows for backend suite (4,506/56/1 + inventory receipt 4,563), frontend (184 files/1,382), ruff, feature inventory (94/14/6/2/1), findings counts post-wave; verdict/blockers unchanged
- **FND-0266** [fixed] OPEN_WORK_ROADMAP self-contradictions (A2/A6 open vs receipt-complete; undefined A8; duplicate TS ro — evidence: Docs/review/OPEN_WORK_ROADMAP_2026-09-08.md: A6 marked DONE 2026-09-11, undefined A8 corrected, TS-07/08/09 duplicate rows de-duplicated with status-authority note; Docs/review/MIMOSA_HIGH_RESIDUAL_TRIAGE_2026-09-11.md disposes all 59 HIGH per-cluster with file:line evidence and keeps FND-0117 explicitly open
- **FND-0267** [fixed] TS-03 attachment surface gaps: privacy guard zero coverage of attachment bytes/filenames, soft-delet — evidence: spine_api/contract.py: 3MiB per-file + 3.5MiB total caps aligned to 5MB middleware + magic-byte verification; document_storage.py tombstone delete + purge_tombstoned_documents; privacy_guard _FREEFORM_FIELD_NAMES += filename; byte-content scanning explicitly deferred to TS-03 S2 seam (documented); tests/test_fnd0267_attachment_hardening.py 11 tests
- **FND-0269** [fixed] No GMV metric exists anywhere; POST /analytics/export returns fabricated download-URL stub — evidence: src/analytics/models.py InsightsSummary.gmv + aggregate_insights terminal-budget sum (real-or-0); FE insights GMV card; types regenerated via scripts/generate_types.py; tests in test_analytics_truth_hardening.py 14/14
- **FND-0270** [fixed] Review queue exposes state not history: reviewed_by/at/outcome only on trip page; Rejected/Revision- — evidence: frontend reviews/PageClient.tsx: decision-history line (reviewedBy/reviewedAt/ownerNotes) on queue cards + Rejected/Revision-Needed filter tabs (backend trip_to_review already supplied the fields)
- **FND-0271** [fixed] Duplicate ICAO MRZ 7-3-1 check-digit implementations (mrz.py canonical vs mrz_parser_engine.py priva — evidence: src/intake/mrz_parser_engine.py calculate_check_digit now delegates to canonical src/intake/mrz.py compute_mrz_check_digit; single ICAO 7-3-1 source; engine API unchanged; 6 mrz tests green
- **FND-0272** [fixed] P0: UI-path blocked run does not persist incomplete lead (IMP-01 regression; lead absent from Lead I — evidence: Verification error, not a product defect. Retracted: all six Sim #2 leads WERE persisted (waypoint_os.trips, status=incomplete: trip_8e33059fa847..trip_2550fdb82576). Initial check saw 0 rows because (a) trips has enforced RLS keyed on app.current_agency_id — direct queries without the session GUC see nothing (asyncpg autocommit also negates transaction-local set_config); (b) raw_input is encrypted at rest so inbox content search cannot match 'japan'/'organising'. Verified via session-scoped GUC: 6/6 rows found. Lesson recorded: verify through the service path (GET /trips/{id} via cookie auth) or set the session GUC; API-green vs UI-behavior still needs the E2E companion test (A14).
- **FND-0273** [fixed] P1: cross-voice appended messages overwrite packet fields last-writer-wins (Budget Scope total->per_ — evidence: Both halves landed and verified: (1) scope half — Phase 1 amount-scoped guard (commit before 5454458, 8 tests in test_extraction_scope_guard.py); (2) origin half — Phase 2 side-trip cue-guard (commit 5454458, 8 tests incl. verbatim Sim #2 thread). Live acceptance replay confirmed scope=total preserved and origin=None on the full Sim #2 thread. Closed as fixed.
- **FND-0274** [fixed] P1: channel transcript fragments leak into packet fields (Constraints/Soft Preferences contain chat  — evidence: Fixed in commit 881493c: _prepare_extraction_text now strips [speaker]: prefixes from chat-dump lines, keeping only content. Live acceptance confirmed: no transcript fragments in constraints or soft_preferences fields. Attribution module uses envelope.content (RAW text) for its own speaker identification, so the two concerns are cleanly separated.
- **FND-0275** [fixed] P1: safety-critical per-traveler constraints dropped in multi-voice thread (no-heights stated twice  — evidence: Per-traveler binding landed (Phase 3b, commit b19bf95): travelers[] fact with per-speaker constraint bundles; Meera carries jain/no-onion-garlic/cable-cars/fear-of-heights/anniversary-april-14th. Decision layer emits traveler_safety_constraint + traveler_occasion_anchor risk flags (3 tests in test_extraction_phase3b_travelers.py TestDecisionDownstream). Asymmetric containment dedup keeps more-informative constraints.
- **FND-0276** [fixed] P2: missing-fields list unstable across reprocesses (Origin silently disappears once a wrong value e — evidence: Realignment Phases 4a-4c (2026-09-13/14, commits 5f5b19f + 7af2616 + 9f52fb0): (1) D-02 v2 — explicit 'including/excluding flights' assertions now assert budget scope as a fact and short-circuit the ambiguity; unresolved phrasings still fire; multi-clause threads resolve if ANY clause asserts (Sim #2 organizer clause wins over friend chatter). (2) flights_inclusiveness ownership — the budget_flexibility full-text scan was adding D-02 ambiguities bypassing the gate; type-ownership filter landed. (3) Ambiguity raw quotes verbatim-or-labeled — synthesized renderings prefixed 'derived from extracted candidates:'; case-insensitive verbatim invariant pinned. Acceptance replay: scope=total, origin=None, D-02 silent, 4 travelers, all raws verbatim-or-labeled. Residual: raw quotes from the lowercased scan are case-flattened (cosmetic); missing-flag rendering now flows from open questions per ontology v2 (tracked in T-O2).
- **FND-0277** [fixed] Workbench: triplicated draft-payload construction + 3x 409-conflict handling (ensureDraftSaved/handl — evidence: consolidation landed in useWorkbenchDraftPersistence.ts: single buildDraftPayload + isConflictError shared by all three persistence strategies; flow shapes (setTimeout(0) deferral, 3 URL-write mechanisms, toasts) deliberately NOT unified; pinned by page-characterization T3/T4/T7 (127 route tests green)
- **FND-0279** [fixed] Workbench: spurious autosave ~5s after every draft load when scenario_id null (init contentKey uses  — evidence: init contentKey now derives stage/mode/scenario from the same URL params the save payload writes (useWorkbenchDraftPersistence.ts init effect); T6 characterization test RED before fix, GREEN after (S2)
- **FND-0282** [fixed] Workbench: uncleaned toast timers (3s/8s setTimeout fire-and-forget in handleProcessTrip + handleSav — evidence: useTransientTimers hook (frontend/src/hooks/useTransientTimers.ts) with unmount cleanup; 6 toast-timer sites across PageClient + useWorkbenchDraftPersistence converted; typecheck/eslint/dir-suite green; no observable-behavior test possible (lost updates on unmounted component are silent in React 18) — hygiene fix recorded in commit
- **FND-0284** [fixed] P1: draft-reprocess creates duplicate leads — reprocess resolution used ContextVar-based RLS get_tri — evidence: Fixed in spine_api/services/pipeline_execution_service.py _resolve_draft_reprocess_target: resolves via get_trip_for_agency(trip_id, draft.agency_id) — explicit RLS session instead of ContextVar-based get_trip (which sees an RLS-filtered empty set in the pipeline executor). 3 structural regression tests (tests/test_fnd0277_reprocess_resolution.py) incl. the RLS-filtered-store shape and legacy fallback. Live verification post-fix: two draft-linked /run reprocesses (draft_fc41208ed551) -> linked_trip_ids length 1, pass-2 meta trip_id == pass-1 (preserved, no duplicate). Committed.
- **FND-0285** [fixed] P2: trips.raw_input encrypted at rest makes inbox search unable to match note content (search only m — evidence: Trade-off accepted: raw_input is encrypted at rest by design (privacy guard). Inbox search matches customer-ref/derived-fields only. Extracted-field search index tracked as exploration item B2 in the Sim #2 inventory. Not a defect — a deliberate encryption-vs-searchability trade-off.
- **FND-0286** [fixed] P0: destination extraction fails on 21/24 real-world casual/Hinglish/GenZ phrasings — pipeline only  — evidence: Closed by guard-wave + gates 2026-09-13: (1) KDD note-level gate records_sweepguard2.jsonl — B-gpt-4.1-nano and B-gpt-5.4-nano F1 0.808 vs 0.800 grades-of-record (records_ladder2.jsonl), recall 0.833->0.875, precision 0.750 vs 0.769 (within single-run variance), +1 TP (colloq_party_of_n_001 visa_timeline_risk); gate caught and fixed 48 GeoNames prose/amenity collision stop words ('any time' swept village of Time -> fabricated destination -> visa FP nudge; 'resort with a pool' -> Pool UK; grader receipt data/experiments/hybrid_kdd_v1/grading_receipt.json). (2) Fresh acceptance 9/9 GREEN via new reusable tools/sim2_acceptance_probe.py — all Sim #2 defect classes dead (origin=None, scope=total stable, D-02 fact, Meera attribution, anniversary survives trades, chat-dump binding) plus new contracts live (direction intent open, VFR India+family_visit, past-trip memory -> history-informed ask, memories never suggested as values). (3) 1,236 tests green across extraction/decision/adversarial/gate/lifecycle families; ruff clean.
- **FND-0287** [fixed] P1: party_size extraction fails on informal phrasings — 'my gf' (implies 2), '4 log' (Hindi), 'me n  — evidence: tests/test_extraction_fixes.py::TestPartySizeInformalHinglish (all cases pass), 329/329 extraction tests pass, ruff clean
- **FND-0288** [fixed] P1: origin_city not extracted from Hinglish/route patterns — 'yahan se', 'mumbai se goa' (se = from) — evidence: tests/test_extraction_fixes.py::TestOriginCityHinglishAndRoutePatterns (all cases pass), 329/329 extraction tests pass, ruff clean
- **FND-0290** [fixed] Residual TEST_AGENCY_ID fallbacks in production tenant attribution: group_booking.py invite redempti — evidence: Removed both production TEST_AGENCY_ID fallbacks. spine_api/routers/group_booking.py pay-share redemption now 409s when the matched trip lacks agency_id (fail-closed, record unmutated); spine_api/services/commission_reconciliation.py get_or_create_advisor_ledger + process_advisor_payout_authorization raise ValueError without agency_id on the durable SQL path (memory dev path unchanged). Tests: tests/test_group_booking_router.py legacy-trip 409 regression; tests/test_pa_wave2_payout_ledger_sql.py SQL-guard x3; tests/test_pa_payout_ledger_honesty.py production zero-seed tests aligned to explicit agency attribution (read-only _sql_ledger, property unchanged). Suites green: 50 passed (7 commission/payout/group suites) + 36 passed (gap_closure/router_mount). ruff clean.
