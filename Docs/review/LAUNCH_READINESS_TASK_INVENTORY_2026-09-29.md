# Launch-Readiness Task Inventory — 2026-09-29

**Provenance:** derived from the launch-readiness product council
([COUNCIL_LAUNCH_READINESS_PRODUCT_2026-09-29.md](COUNCIL_LAUNCH_READINESS_PRODUCT_2026-09-29.md)) +
owner direction ("list all inferred/identified/implicit/explicit findings/tasks; assess first-principles/doctrine
alignment; document everything; make it the best"). Full-launch basis — no MVP/pilot scoping (owner rule,
memory `no-scoping-reduction`).
**Corrected baseline:** findings store, latest-event dedup = **19 open (0 P0 / 0 P1 / 2 P2 / 17 P3)**; FND-0185
closed 2026-09-14. New council findings registered this session: **FND-0301…0306**.
**Goal:** close the ranked launch gaps from the council verdict, in gap order.

## Implementation status (updated 2026-09-29, end of build session)

| Task | Status |
|---|---|
| T1 ask-traveler loop (FND-0301) | **SHIPPED**: `message_dispatch.py` (WhatsApp/SendGrid adapters, honest NOT_CONFIGURED), `public_asks.py` router (token-gated GET + append-only explicit_user write-back, unasked-field injection blocked), `followups/{id}/send` (compose + dispatch + ask ledger), FE `/a/[token]` answer page, route-map entries, `.env.example` template. 17 BE tests + route parity + tsc + ruff green. |
| T3 review reason capture (FND-0302) | **SHIPPED** — closed. |
| T8 proposal trust render | **SHIPPED** (constraints-honored via `stated_requirements`, de-attributed, 45/45 tests). D05 "why this option" = residual. |
| T11a parked-toggle defaults | **SHIPPED** (`enable_ghost_concierge`/sentiment/federated default false per PARKED comment + ADR-008 §7). |
| E1 channel research | **DONE** ([E1](../exploration/E1_ASK_TRAVELER_CHANNEL_2026-09-29.md)); rates unverified until 10-06. |
| E2 Jev probe | **EXECUTED 2026-10-13 — BOTH GATES PASS** (`E2` + `scripts/benchmark_jev_ask_loop.py`): Probe 1 rendering-grading defect detection 1.000 (role corrected: Jev grades ladder variants, cannot generate); Probe 2 free-text reply routing 1.000 / zero wrong-field / zero silent drops incl. Hinglish + implicit answers → Option D in-thread WhatsApp parsing buildable. **Outcomes wired same day** (`src/intake/ask_reply_router.py`, `src/intake/question_render_selector.py`, `JEV_ASK_LOOP_ENABLED` default-off; 12 contract tests; live-verified) — serving-path integration stays unwired until G2. Same sweep found+fixed dead Jev paths in failure-triage (422) and NL-policy (400 + false-clearing fallback) — FND-0322 closed. |
| T2 unify intake + provenance | **SHIPPED** — FND-0304 closed. Full Supersession executed: DecisionTab's five unique sections (follow-ups, contradictions, risk flags, budget table, repair empty-state) merged into canonical DecisionPanel first (ordering contract preserved); DecisionTab.tsx + test + themeStore dead entry deleted; workbench gains a 'Decision' tab (gated like Trip Details) mounting DecisionPanel — provenance in the primary flow; `/workbench` → `/inquiries/new` query-preserving redirect (nav canonical). Verification: tsc clean, panels 417/417, workbench 132/132. FND-0236 dossier substrate = follow-up (provenance is now at least surfaced in-flow). |
| T5 cleanliness cluster (FND-0306) | **LARGELY SHIPPED (tranche 6)** — A1 (breadcrumb/sidebar truth), A2 (all live /workbench navigations → /inquiries/new; 9 files + 6 test-pin files), A5 (WelcomeCard transient: auto-dismiss on first navigation; canonical-route suppression), A7 (sidebar trip card suppressed in-trip, new contract test). FND-0289 CLOSED (supersession verified complete). OPEN remainder: A6 (trip-header stage encodings), A8 (breadcrumb devices), A9 (mobile bar), A10 (hygiene). FE gate: 168 files / 1,333 tests green, tsc clean. |
| T6 message/attachment consumption UI (FND-0305) | **SHIPPED** — FND-0305 closed. Root cause verified in source: the webhook never persisted traveler messages at all. Built: durable per-agency JSONL message store (message_store.py, run-ledger pattern, phone-matched trip linkage with no-guess nulls), webhook ingestion of Meta-envelope + flat payloads post-HMAC (audit-logged, honest stored-count), GET /api/v1/messages + GET /api/v1/trips/{id}/messages (auth-gated, tenant-scoped), inbox ChannelMessagesPanel (channel/direction badges, media metadata without fabricated bodies, unlinked-vs-trip honesty, honest empty/error). Tests: BE 8/8, FE 77/77 incl. 3 new pins, tsc+ruff clean. Media (voice/image) *rendering* beyond metadata = follow-up once B6/B7 provider lane lands. |
| T9 (FND-0232) confirmation defect grading | **SHIPPED** — FND-0232 closed. `confirmation_grader.py`: deterministic grade-at-read (no migration; truthful as trip data evolves) — missing identity/segments/guests = incomplete, passenger/guest name mismatch vs travelers[] = defective (token-subset match, titles+initials stripped); served as `content_grading` on the confirmation detail endpoint; advisory only, deterministic validators authoritative, no LLM. 8/8 tests. |
| T13 SQL ledger default + E08 | **SHIPPED** — ledger SQL default verified earlier (sql when DATABASE_URL); E08 un-orphaned: `accounting_export.py` GET /api/v1/trips/{trip_id}/accounting-export?format=tally|quickbooks derives a real CommercialInvoiceSummary from persisted strategy cost + MarginPolicy margin + statutory TCS/GST (explicit PAN param; overseas-only per 206C(1G); ₹7L LRS threshold honored). INR-native: non-INR quotes refused without FX invention; no-quote-cost = explicit not-available. 7/7 tests incl. under-threshold + domestic-zero statutory paths. |
| FND-0126 | **SHIPPED+CLOSED** — concierge reply engine wired into the T6 webhook (persist → concierge → honest dispatch → both sides stored); idempotency registry prevents double-dispatch on provider retries. |
| FND-0093 | **FIXED+CLOSED** — stress_benchmark endpoint was an UNAUTHENTICATED, UNLIMITED compute-burner (my first closure claim was wrong — corrected in-store); now agency auth + trips:write + 5/min limiter, live-smoke verified. |
| T14 retention/DSR/TOS | **SHIPPED** — /privacy + /terms (code-grounded, review-pending banner); trip_dsr.py: Art. 15/20 portable export + Art. 17 structural erasure (PII scrub + message tombstones, audit chain preserved; fail-closed GDPR signing — prototype's hard-coded default key NOT carried forward; explicit confirm gate; overseas/under-threshold TCS honesty carried into E08 too). 5/5 DSR tests; full BE 5,122/0. retention_enforcer → owner DECIDE w/ archive recommendation (own docstring: RUNTIME_STATUS=shadow). |
| T4 quotes | **SHIPPED REAL (owner: "no demos, real work")** — FND-0303 closed. New canonical read model `spine_api/routers/quotes.py` GET /api/v1/trips/{trip_id}/quotes: quote derived from persisted strategy.recommended_option (persisted_modeled_cost), margin via MarginPolicy + fee_matrix.calculate_package_pricing (applied_rule_id provenance, policy_preview basis), tax=None (no producer), status from review queue/proposal link, branches surfaced unpriced. FE /quotes rewritten — fabricated tier matrix + SimulatedBadge + sample banner deleted; explicit not-ready contract with missing-inputs list. Tests: BE 6/6, FE 7/7 rewritten pins, route parity green. |
| T10/T11b/T12/T15 + E1 channel choice | **Owner DECIDE** (see session summary). |
| FND-0062 | **CLOSED** (banner already renders field names — verified live). |
| FND-0233 | Scope note recorded (router mounted; disposition ledger = owner DECIDE). |
| Parallel-agent fix | `DecisionPanel.tsx` `trip.notes` → `trip.customerMessage` (tsc break, engaged per shared-tree doctrine). |

---

## 0. Jev — what it can and cannot do for these gaps

Jev = **TypeSafe System One** (`src/llm/typesafe_client.py`, `TypesafeJevClient`, model `jev-1.13.0`): the
fast-path structured-LLM lane already wired into live intake triage (`src/decision/live_triage.py`, workbench
advisory chips), ambiguity classification (`src/intake/ambiguity_classifier.py`), failure triage
(`src/decision/failure_triage.py`), NL corporate policy (`src/corporate_policy/nl_evaluator.py`), and the eval
judge (`src/evals/judge/scorer.py`).

**Lesson from the 2026-09-18 exploration (gates G1/G2):** Jev is *literal* — rubric-explicit criteria in the
prompt took visa-eval severity from 0.207 (FAIL) to 0.632 with sev ✓ 1.00 and zero false positives. Any Jev
task here must carry rubric-explicit criteria and a deterministic validator as the authority.

| Where Jev helps | Task | Role | Boundary |
|---|---|---|---|
| Human-language question rendering (machine field → traveler-voiced ask) | T1 | Generator, rubric-constrained | Deterministic packet-field mapping remains authority |
| Traveler answer parsing → structured packet updates | T1 | Extractor proposal | Write-back requires explicit_user authority + assumption-loop integration |
| Per-traveler voiced questions (Jain meals / heights / occasion) | T1 | Generator | FND-0275 facts are the source of truth |
| Rejection-reason normalization (free text → structured revision intent) | T3 | Classifier | Reason text itself is human-provided |
| Defective-confirmation pre-screen | T9 (FND-0232) | Advisory pre-screen only | Deterministic validators (MRZ, segment/name checks) are the authority on money/documents |
| Re-engagement copy drafting (ghost follow-ups) | T11 | Generator, if wired | FND-0286-style gates before any send |
| Eval-judge for the launch falsifier (browser-journey + ask-loop E2E) | D2/E2 | Judge, rubric-explicit | Not promotion authority alone (FND-0165: add cost/latency dims) |

**Where Jev must NOT be used:** anything that is authority over money, documents, consent, or safety flags
(hard invariants stay deterministic); anything whose prompt can't carry explicit rubric criteria.

---

## A. IMPLEMENT (ordered to the council gap ranking)

| # | Task | Finding(s) / evidence | First-principles & doctrine assessment | Make-it-best additions |
|---|---|---|---|---|
| T1 | **Ask-traveler loop (gap 1)**: outbound ask delivery + traveler answer surface + packet write-back. Extend the canonical proposal-token infrastructure (TTL/revocation/consent parity) rather than building a parallel messaging system; Jev renders questions in traveler language, parses answers. | **FND-0301** (new); `DecisionTab.tsx:312-330`; `spine_api/routers/followups.py:254-313` | **Aligned**: the spine exists to resolve intent — questions answerable only by the operator violate the product's own first principle. Extends canonical token/consent infra (no duplicate route — hard rule). Must integrate with assumption loop (FND-0291) so answers carry `explicit_user` authority. | Answer pages honor proposal-token revocation/expiry; per-traveler attribution; answers update missing-fields banner; E2E falsifier test. |
| T2 | **Unify intake + decision provenance (gap 2a)**: one canonical intake route; mount decision provenance in the primary flow; apply Supersession Workflow to the orphaned `DecisionTab.tsx` (field-by-field comparison vs `trips/[tripId]/decision` before removal). Fold in FND-0236 (replayable explanation dossier) as the provenance substrate. | **FND-0304** (new); `workbench-state.ts:26-33`; `stores/themeStore.ts:32`; FND-0236 (open P3) | **Aligned**: two vocabularies for the same decision is drift-by-design; FND-0236's hashed evidence bundle is the long-term substrate, not a panel patch. | Wire dossier into the unified surface so "why" is replayable, not just displayed. |
| T3 | **Review reason capture (gap 2b)**: Reject/Request-Changes require a reason; reason flows into decision history + follow-up generation. Replace `alert()` with proper error UI; wire the dead Filters button. | **FND-0302** (new); `reviews/PageClient.tsx:176-276,325` | **Aligned**: FND-0270 closed state-vs-history; reasons are the missing half of that history. No new route — extend the existing review PATCH. | Feed reasons into override-learning pattern mining (C06) so rejection causes improve future decisions. |
| T4 | **Kill sample-data nav item (gap 2c)**: remove `/quotes` from nav or gate behind an explicit demo flag; if no real producer exists, wire-or-archive per protocol. | **FND-0303** (new); UI-cleanliness A3 | **Aligned**: honesty wave established that fabricated surfaces must be labeled *and* unreachable by default. | Audit sibling sample surfaces (`bookings`? `suppliers`?) in the same pass. |
| T5 | **UI-cleanliness cluster (gap 2d)**: breadcrumbs tell the truth, unify the three lead/status vocabularies (supersede FND-0289's `LeadStage` into the relational vocabulary), WelcomeModal no longer occludes forms. | **FND-0306** (new); FND-0289 (open P3); UI-cleanliness A1/A5-A7 | **Aligned**: vocabulary unification is the repo's own anti-duplication doctrine applied to UX. | Do the vocabulary supersession once, in the canonical location, with the Supersession Workflow documented. |
| T6 | **Message/attachment consumption (gap 3)**: inbox + intake surfaces to view/listen attachments and read channel messages; reuse multimodal router + honesty badges; Jev triage chips already exist — surface them at message level. | **FND-0305** (new); `IntakeTab.tsx:208-215`; `inbox/PageClient.tsx`; `spine_api/routers/multimodal.py` | **Aligned**: backend multi-channel ingestion (B02) is LIVE and marketed; the UI half is the missing serving-path caller — this is the FND-0261 rule applied to UI. | Attachment caps/magic-bytes already hardened (FND-0267); reuse; add per-channel source labels. |
| T7 | **Repair banner completeness (FND-0062)**: banner lists missing field names; deep-link loop reaches the traveler-visible journey too (pairs with T1). | FND-0062 (open P3); `PageClient.tsx:146-152` | **Aligned**: repair deep-link infra (41 tests) exists; this is completing a served flow, not new surface. | Render machine→human field names via the T1 Jev mapping (single mapping table, two consumers). |
| T8 | **Public proposal trust render (gap 4)**: constraints-honored line from `travelers[]` (FND-0275 facts) + D05 "why this option" on the public proposal. Verify payload first (API Contract Verification rule), then render. | Council S3; `p/[token]/page.tsx`; FND-0275 (closed) | **Aligned**: contract-first; the differentiator exists backend-side — the serving-path render is the only gap. | Add an honesty test (pattern of `public-proposal.honesty.test.tsx`) pinning the trust render. |
| T9 | **FND-0232 confirmation defect grading**: accept/defect taxonomy for supplier confirmations; deterministic validators authoritative; Jev pre-screen advisory. | FND-0232 (open P2) | **Aligned**: money/document authority stays deterministic (hard invariant); the defect is treating malformed confirmations as valid. | Grade into disposition states (accept/defect/reject) with re-shop credit path linkage to T10. |
| T10 | **FND-0233 refund/compensation disposition path** — or archive the lane honestly with a recorded ADR decision. | FND-0233 (open P2); `passenger_rights_claims.py` | **Aligned**: wire-or-archive ADR protocol; a dead-ending pipeline is worse than an absent one. | Owner decision required (DECIDE gate): wire disposition grading vs archive. |
| T11 | **Ghost concierge wire-or-archive** (gap 5 periphery): engine has zero serving-path callers; `/ghost/workflows` rows are inert. | Council S1; `spine_api/services/ghost_concierge.py`; `frontier.py:76-128` | **Aligned**: FND-0261 serving-path rule; wire-or-archive ADR pattern. | If wired: Jev-drafted re-engagement copy with FND-0286-style gates before any send. |
| T12 | **D09 pre-departure briefings wire-or-archive**: `src/briefing/pre_departure_cadence.py` implemented, zero callers. | Council S5; FND-0261-class | **Aligned**: same wire-or-archive protocol. | D-7/D-3/D-1 cadence is a natural post-proposal value surface once T1 lands. |
| T13 | **Durable money ledgers (E04/E05)**: commission + payout ledgers → durable SQL path (mirror `commission_reconciliation` SQL lessons incl. FND-0290 agency-attribution). | Council S5; FEATURE_LIST E04/E05 | **Aligned**: in-memory ledgers lose money history on restart — violates data-integrity doctrine; FND-0290 shows the SQL pattern exists. | Accounting export (E08) un-orphaned in the same pass so ledgers have a serving-path consumer. |
| T14 | **Retention + DSR**: wire-or-archive `retention_enforcer` (FND-0091/X14); traveler data export/erasure route; TOS/privacy pages. | Council S5; `src/security/retention_enforcer.py` | **Aligned**: jurisdiction_policy declares SLAs with zero enforcement — either enforce the declared policy or amend the policy (never leave the lie). | Consent artifact from proposal_token_store (FND-0219) extended to data-processing consent. |
| T15 | **Group consensus binding (FND-0184)**: two consensus engines, neither binds booking — consolidate to one engine emitting a binding artifact. | FND-0184; `GroupParetoPanel.tsx:8-16` | **Aligned**: consolidation doctrine; verify current state first (may have moved since FND-0184 registration). | Verify-then-classify before implementing (findings-store discipline). |

## B. EXPLORE (research — register in Docs/EXPLORATION_TOPICS.md)

| # | Topic | Why now | Method |
|---|---|---|---|
| E1 | Ask-traveler channel architecture: WhatsApp Business API vs shareable token link vs email — India-first, cost, consent, deliverability | Blocks T1 design | Online research + cost model; decision record |
| E2 | Jev-1.13.0 capability probe: question rendering + answer parsing on colloquial fixtures (rubric-explicit templates; G1/G2-style gate) | De-risks T1's Jev usage | Reuse `scripts/benchmark_colloquial_jev.py` harness pattern |
| E3 | Currency/locale/timezone strategy (INR-first vs multi-currency; no localization module exists) | Real-launch surface gap | Repo evidence + market research |
| E4 | Multi-user trip concurrency (roles exist in schema; no optimistic-locking evidence found) | Day-30 multi-advisor reality | Extend expected_version guard pattern (partial 2026-09-04) |
| E5 | Mobile/responsive + PWA audit (no manifest found; responsive evidence unverified) | Real-launch surface gap | Browser/device sweep (playwright-interactive) |
| E6 | B6/B7 live-provider lane sequencing (quota gate clears 2026-10-06) | Unblocks real inventory/pricing | Prep scoping now, execute after gate |

## C. DOCUMENT

| # | Task | Note |
|---|---|---|
| D1 | Reframe `Docs/LAUNCH_STATUS.md` criteria to full-launch basis per owner rule (archival addendum, preserve history) | Owner direction 2026-09-29 |
| D2 | This inventory + council record (done) | Evidence trails in both |
| D3 | Add E1–E6 to `Docs/EXPLORATION_TOPICS.md` | Exploration-map update |
| D4 | Exploration-map drift addendum (CODEBASE_FEATURES_FLOWS_LOOPS_MAP): orphaned `DecisionTab.tsx`, dual intake routes, followups-no-outbound, `/quotes` sample data | Keeps the ⭐ map runtime-true |
| D5 | Update FEATURES/flows ledger after T2/T5 supersessions | Post-implementation |

## D. Verification notes (method integrity)

- Initial naive count "147 open / 1 P0" was **wrong** (append-only rows not deduped by latest event per finding_id). Corrected: 19 open (0 P0/P1). S5's LIVE-view read was right. Lesson recorded in the council doc.
- All new findings registered through `scripts/findings.py` (FND-0301…0306); no hand-edits to the store.
- Seat reports retained verbatim in the council record; evidence tiers per doctrine (source > docs for code claims; no runtime/browser claims made).

## E. Live-code verification pass (2026-09-29, owner directive: "don't just depend on docs, check live code")

Every load-bearing inventory claim re-checked against current source. Where docs/findings and code disagree, **code wins** and the task is revised. Notes: FND-0301 carries a correction note in the store.

| Item | Doc/finding claim | Live-code verdict | Revision |
|---|---|---|---|
| T1 (FND-0301) | "No outbound channel exists" | **REVISED.** `spine_api/routers/messaging.py` POST `/messaging/send` exists and is mounted (`server.py:1570`): JWT + tenant-scoped, Meta webhook HMAC verify, audit events, honest `QUEUED` status — but **no provider HTTP call in this build** (`messaging.py:75-77`); `followups.py` has zero wiring to it. | Task = provider dispatch adapter + followups→messaging wiring + traveler answer surface + packet write-back. Smaller than originally framed. |
| T2 (FND-0304) | DecisionTab unmounted | **VERIFIED** — only importer is its own test file. | No change. |
| T3 (FND-0302) | Auto-notes / `alert()` / dead Filters | **VERIFIED** — `reviews/PageClient.tsx:263,268,326`. | No change. |
| T4 (FND-0303) | "Fabricated-quoting invitation" | **REVISED (partially).** `/quotes` renders `SimulatedBadge label='Sample data'` + `data-testid='quotes-sample-banner'` — it IS honestly labeled. Nav-reachability grep inconclusive. | Task narrows to: nav reachability check + decide whether a labeled sample surface belongs in agency nav at all. |
| T7 (FND-0062) | Banner lacks field names | **STALE — appears fixed.** `PageClient.tsx:146-152,484-490`: `formatWorkbenchMissingFields` renders `Missing: {missingFieldsLabel}`. | Re-verify via FND-0062 reverify + close with this evidence instead of implementing. |
| T8 | No travelers[]/D05 on public proposal | **VERIFIED** — `p/[token]/page.tsx` has only `traveler_name` ("Curated for…"); no constraints, no scorecard. | No change. |
| T9 (FND-0232) | Rubber-stamps defective confirmations | **STALE (likely).** `confirmation_service.py` validates evidence refs (`_validate_evidence_refs`) + ownership (`_validate_ownership`) in a transactional create; `booking_fulfillment.py` has reconciliation outcomes (matched/mismatch) and `missing_for_upgrade` sets. | Re-verify FND-0232 against current code; close or re-scope to the residual gap. |
| T10 (FND-0233) | Refund pipeline dead-ends, no disposition | **REVISED.** `spine_api/routers/passenger_rights.py` exists and is mounted (`server.py:1593`, auth-gated). | Re-verify what the router serves (grading vs listing) before implementing; likely re-scope. |
| T11 | ghost_concierge zero serving-path callers | **MOSTLY VERIFIED.** Backend engine has no backend caller; frontend has an `enable_ghost_concierge` store toggle (default **true**) + integrity test. | Add to task: the default-true toggle for an inert engine is its own honesty defect. |
| T12 (D09) | Pre-departure briefings orphaned | **REFUTED.** `spine_api/routers/pre_departure.py` mounted (`server.py:1644`): JSON + PDF bundle endpoints calling `PreDepartureCadenceEngine`; honest "Reality boundary" + missing-for-upgrade list. | Reclassify: serving path exists (on-demand preview). Residual: no scheduled D-7/D-3/D-1 trigger — decide if wanted (pairs with T1). |
| T13 (E04/E05) | In-memory commission/payout ledgers | **REVISED.** `spine_api/services/advisor_payout_store.py`: "each payout is one row" (SQL); `commission_reconciliation.py` documents legacy fake-seeded balances removed + `reconcile_trip_commission`. | Task narrows to: verify SQL path is the default (FND-0290 left a "memory dev path") + un-orphan E08 accounting export. |
| T14 | No DSR capability; no TOS/privacy pages | **REVISED (partially).** `src/memory/gdpr_engine.py` — GDPR Art. 17 Right-to-erasure engine with compliance certificates — exists. `retention_enforcer` still has no non-test importer; no TOS/privacy routes found under `frontend/src/app`. | Task narrows to: wire-or-archive retention_enforcer; extend gdpr_engine (memory-domain) to traveler-trip data; add TOS/privacy routes. |
| T15 (FND-0184) | Two consensus engines, neither binds | **PARTIALLY VERIFIED.** Both `group_consensus.py` and `group_pareto_engine.py` exist; `group_pareto` router mounted (`server.py:1625`). Binding still unverified. | Verify-then-classify stands. |
| E4 | No optimistic locking | **REVISED.** `draft_store.py` has version increment + conflict detection; trips-level locking unverified. | Scope = trips-level only. |

**Net effect:** 4 tasks materially smaller than the doc-based framing (T1, T4, T13, T14), 2 likely closable as stale findings (T7/FND-0062, T9/FND-0232), 1 refuted (T12 orphan claim), 1 refuted-then-narrowed (T10). The council's core gap ranking is unchanged; the build cost estimates drop.
