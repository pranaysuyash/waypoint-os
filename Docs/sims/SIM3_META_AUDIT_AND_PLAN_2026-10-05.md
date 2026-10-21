# Sim #3 Meta-Audit & Implementation Plan — full candidate inventory, doctrine alignment, and the work queue

**Date:** 2026-10-05 · **Author:** ZCode (audit pass over Sim #3 "Four Doors")
· **Subject of audit:** everything the Sim #3 session produced, surfaced, or
implied — explicit findings, code-level inferences, doc gaps, process items —
classified per OPERATING_DOCTRINE §9 (candidate → disposition) and graded for
first-principles, long-term, and doctrine alignment.
**Inputs:** `Docs/sims/SIM3_RESULTS_2026-10-05.md` (execution record),
`Docs/sims/assets/sim3/` (evidence + screenshots),
`Docs/sims/SIM3_DESIGN_2026-10-05.md`, `Docs/sims/personas/SIM3_PERSONAS_2026-10-05.md`,
findings store (FND-0308..0321), OPERATING_DOCTRINE.md v8.2,
`Docs/architecture/adr/ADR-008-AGENCY_BOUNDARY_AND_AUTONOMY_RUNGS_2026-09-06.md`.

**Truth labels used below** (doctrine §2): **Observed** (seen live in this
session), **Verified** (independently checked — test, article text, or
code-read this session), **Inferred** (best explanation; assumption named),
**Proposed** (not yet implemented), **Unknown** (check stated).

---

## 0. Session record (the "chat stuff", durably)

1. Ground-truth refresh: agent-start context pack regenerated; prior-sim
   corpus read (Sim #2 personas/results/design); launch-wave surfaces mapped
   in code (`/run`, `/api/public/asks`, `/api/v1/passenger-rights`,
   `/api/v1/customers`, `/api/v1/inbound`, `ghost_concierge_monitor`,
   disposition states at `spine_api/services/claim_disposition.py:22`,
   occasion/VFR/mobility extractors in `src/intake/extractors.py`).
2. Design + personas committed to docs BEFORE execution (predictions P1–P17,
   repo-fact anchored, verbatim scripts).
3. Environment: backend `:8000` (uvicorn, `TRIPSTORE_BACKEND=sql`,
   `llm.available: false` — Observed via `/health`; **this is the ratified
   production posture**, ADR-008 §8 "prod posture 0 pending X-09", so the
   deterministic-stack results are the production-representative lane, not a
   degraded one), frontend `:3005`.
4. Runner built as a reusable tool (`tools/sim3_runner.py` +
   `tools/sim3_sims.py`, documented in `tools/README.md`); three runner-side
   contract errors were hit and corrected during execution (cookie-vs-bearer
   auth, trip-PATCH-vs-draft-PATCH append door, disposition field name
   `new_state`) — each left as evidence in the per-sim JSON (Observed).
5. Four sims executed live; 12 defects registered (FND-0308..0319); 6
   screenshots captured and individually inspected; results doc written.
6. This audit: +2 findings (FND-0320/0321), full inventory below,
   implementation plan, task list. Web-search prime was rate-limited
   (resets 2026-10-06 17:07); the EU261/US_DOT check used the built-in
   WebSearch answer + established regulation text (Verified against
   EC 261/2004 Art. 3 and US DOT rules; falsifier: quote the article text in
   the fix's test fixtures).

---

## 1. Master inventory — every candidate, classified

Dispositions: **IMPL** (implementation), **EXPR** (exploration/research),
**DOC** (documentation), **MAP** (exploration-map/registry update),
**PROC** (process/owner decision). Every item names its evidence tier.

### 1.1 The registered defects — fix paths + alignment verdicts

| FND | Item (truth label) | Disposition | First-principles assessment | Doctrine alignment | Best-shape fix (Proposed) |
|-----|--------------------|-------------|------------------------------|--------------------|----------------------------|
| 0308 | Destination tokenizer fabricates words/names as candidates, some `definite` (Observed, Tier 4) | IMPL | A destination anchors fare math and visa corridor; a hypothesis wearing a fact's clothes corrupts every downstream quote. Root cause is not "missing stopwords" — it is missing **membership proof**. | §2 truth taxonomy (fact vs hypothesis); §11 canonical validation; **owner already ratified the posture** (commit `eeb2edbc`: gazetteer-collision candidates downgrade to semi_open, operator-confirm over silent definite) — the sim words didn't trip the existing sweep, so this is **extend-the-canonical-sweep**, not new machinery | Gazetteer-membership gate: `destination_status=definite` requires `is_known_city/destination` hit; non-members become `semi_open` hypotheses with operator-confirm; keep raw tokens in evidence refs only. S2 via sim3 probe |
| 0309 | Reprocess clobbers candidate list — real Varanasi lost to `['Baad']` (Observed, Tier 4) | IMPL | Supersession should be value-additive (doctrine kernel #4: preserve compatible work). Last-writer-wins on a LIST field is a category error — lists merge. | §6 semantic salvage; §11 data integrity (preserve data on malformed input) | List-merge with provenance: union of gazetteer-confirmed across passes; garbage never evicts confirmed values; record `superseded_by` trail. S2: pass2 keeps Varanasi |
| 0310 | `/customers/remember` 500 after successful commit (Observed, Tier 4 + traceback) | IMPL | A write that persists but reports failure forces operator retries and erodes trust in the memory layer — worse than a clean failure. | §11; §13 (operator can recover the workflow) | Drop `db.refresh` after commit (return the session object with a targeted re-select, or `expire_on_commit=False` on the RLS session maker); **sweep every `db.refresh` after commit in services** (0311 is the same class). S2: sim B re-run 200 |
| 0311 | `/confirmations/extract` 500, identical signature at `confirmation_service.py:363` (Observed) | IMPL | Same root cause as 0310; two launch-wave endpoints prove the pattern is systemic, not local. | §10 (no "pre-existing" dodge inside blast radius); kernel #4 | One fix, both endpoints, plus a repo-wide grep gate (`rg "await db.refresh" spine_api/services` audit) added to the probe |
| 0312 | Framework disagreement: evaluate=US_DOT vs generate-claim=EU261, both wrong for BKK→BOM (Observed; law Verified against EC 261/2004 Art. 3 + DOT rules) | IMPL + EXPR | This is a **legal-claim surface**: the letter cites a regulation that does not apply, to an airline that will rightly reject it. Wrong-but-confident is worse than absent. | **§13 claim reality** (customer-facing legal/protection claims must match actual applicability); ADR-008 R2 (claims are operator-sent) | Single framework resolver consulted by ALL THREE consumers (evaluate, generate-claim, ghost concierge's DRAFT_EU261_CLAIM): jurisdiction matrix (departure/arrival/carrier-license) → EU261 | UK261 | US_DOT | **NONE→Montreal Convention Art. 19 + carrier policy**; matrix as test fixtures with article citations. EXPR: confirm Thai/India-side regimes when search quota resets (owner-notified) |
| 0313 | T1 ask door unreachable — `decision.follow_up_questions` always empty (Observed, Tier 4) | IMPL | The loop's entire value is asking the RIGHT next question; the pipeline already computes unknowns + `required_for` (TS-07 machinery exists) — the decision stage just never writes questions out. Wiring, not invention. | ADR-008: ask-send stays operator action (R1-flavored) ✓; §13 | Decision stage populates `follow_up_questions` from the blocking-unknowns graph (priority by `required_for`); UI per-field Ask buttons already compose correctly (screenshot) — unify on ONE question source (decision), UI template becomes fallback. S2: D re-run → send 200 → token → public page |
| 0314 | party_size fabrication: 45th→4 ("4 pax" in UI); "2 passengers"→1 pax (Observed + screenshot) | IMPL | Party multiplies every per-person number — this is money-adjacent corruption. Named-party Hinglish ("mummy-papa ke saath"=3) and ordinals are the two failure classes. Verified non-case: "2 people" parsed correctly (B). | §2, §11 | Ordinal guard (`\d+(st|nd|rd|th)` never feeds party), named-relation counter, explicit "N passengers/people" parser; default stays absent-not-1 when unstated (honest unknown). Visual BEFORE/AFTER pair per §3 |
| 0315 | Privacy-guard door inconsistency: inbound/parse fail-closed vs /run persists same email (Observed both sides) | EXPR + PROC (owner) | The guard honored its R-15 matrix on BOTH paths (raw_note is scanned too — the run path encrypts raw_input before save, Inferred from FND-0285 lineage; **verify encryption at rest** is the stated check). The inconsistency is the T6 door being unusable-by-default. | §4 authorization; SECURITY_PRIVACY_SAFETY doctrine; R-15 matrix is owner-ratified — do NOT weaken it | Owner decision between: (a) encrypt `customer_contact` at the inbound edge before persistence (canonical, recommended), (b) document dogfood limitation + operator guidance. Either way FND-0320's error contract ships |
| 0316 | JEV says PROCEED/all-clear 0.87 in a packet with 3 blocking unknowns + ESCALATED gate (Observed) | IMPL | Two opposite verdicts on one surface means the operator doesn't know which brain to trust — epistemic incoherence is worse than either verdict alone. | §2 (contested verdicts must be surfaced as contested, not blended) | Coherence rule: JEV `intake_action=PROCEED` requires zero blocking unknowns; else PROCEED_WITH_ASKS/BLOCK with the unknown list embedded. Small, canonical, in `jev`/decision seam |
| 0317 | ClaimDispositionCard unreachable: planning gate locks the decision tab for blocked trips (Observed + screenshot) | IMPL | A disruption trip is an OPERATIONS object, not a planning object; the gate conflates two jobs. The operator mid-disruption cannot see the claim they must advance — the workflow is unrecoverable in UI. | §13 (operator recovery = feature completeness); §9 | Read-only exception: trips holding `claims` (or ghost_concierge drafts) unlock the decision tab read-only, or surface the claim card on the ungated Timeline tab. Visual pair |
| 0318 | Budget gaps: `$2400` missed; `se zyada nahi` cap→soft default (Observed; soft was honestly flagged ASSUMED) | IMPL | Currency myopia: the extractor handles ₹ and misses $ — international customers are the growth surface. Cap-language ("not more than", "se zyada nahi", "max") → firm is the same class Sim #2 already fixed for "MAX". | §11; kernel #4 | Add USD/EUR symbols to budget regex; extend cap-cue list; keep the honest-assumption path for genuine defaults. S2: B re-run budget_max=2400 |
| 0319 | Ghost summary drops route ("TG318 (->)"); messages store count 0 (Observed) | IMPL (cosmetic) + EXPR (write path folds into 0315 decision) | Cosmetic but trust-visible: an ops tool that can't name the route reads as broken. | §13 | Route from flight-fact fields or trip origin/destination at draft time. Messages write path = the 0315 owner decision |
| 0320 | PrivacyGuardError → naked 500 (Observed) | IMPL | Fail-closed is correct; a silent 500 is not — the operator can't distinguish "bug" from "policy block" or learn the remediation. | §11 canonical error contract; §13 | Map `PrivacyGuardError` → 422 with `{reason, remediation}` body at the router seam. S2: probe asserts 422+detail |
| 0321 | Async bridge loop-mismatch teardown noise (Observed in logs; correlation with 0310/0311 Inferred) | EXPR → IMPL if confirmed | Same subsystem (`persistence.py _run_async_blocking`) that produced the refresh 500s; chronic loop churn is latency + flakiness debt. | §11 | Audit the bridge: one long-lived loop (or full-async endpoints) for SQL-store paths; measure first (EXPLORE), then fix once |

### 1.2 Inferred-but-unregistered observations → follow-through

| # | Candidate (label) | Disposition | Notes |
|---|-------------------|-------------|-------|
| U1 | Memory has THREE stores: `CustomerMemoryProfile` SQL, 5-tier `MemoryStore` (ingest), process-local registry fallback (Verified: router docstrings + hydrate fallback text) | MAP + EXPR | Document ownership in the codebase map; propose consolidation boundary (profiles = identity/preferences truth; 5-tier = episodic facts). Drift risk is real (E-10 wrote to MemoryStore; FND-0060 to SQL) |
| U2 | Two reprocess doors: draft+run (append) and `/trips/{id}/reassess` (operator, autonomy-gated `allow_explicit_reassess`) — both live, both legitimate (Verified: route map + Settings AutonomyTab) | DOC | Document when to use which in the codebase map (append = new traveler input; reassess = operator recompute) |
| U3 | Ask tokens reuse `generate_signed_proposal_token` (proposals signing) (Observed in `followups.py:340`) | MAP | One signing seam for public traveler links — record in map; TTL/revocation story shared with proposals |
| U4 | Occasion date could seed `date_window` as a hypothesis ("anniversary ON november 18th" → trip must COVER nov 18) | EXPR → proposal | Sim #2 Dev-note asked for exactly this ("trip must COVER that date"); today even a parsed occasion doesn't feed the window. Small, high-value; owner-ratify the inference rule first |
| U5 | LLM-on shadow-lane sim (hybrid engine posture is ratified-0; a sim of the X-09 flip posture) | EXPR + PROC | Owner-gated; the KDD ladder harness already exists to cheapen this |
| U6 | Sim voices → adversarial eval fixtures (6 verbatim notes into the 50-fixture corpus / adversarial lane) | IMPL | Converts sim findings into permanent gates; doctrine: failure-becomes-fixture rule already repo-standard |
| U7 | `tools/sim3_acceptance_probe.py` (S2 gate: fail-before/pass-after for 0308/0309/0313/0314/0316/0318/0320 + refresh-500 sweep check) | IMPL | Doctrine §3 mandates S2 for defect fixes; probe is the S2 vehicle; mirror of sim2_acceptance_probe precedent |
| U8 | T2 decision-history surface in UI never graded (trail exists via draft; panel assertion missing) | EXPR (verify task) | Cheap: one browser pass on the A trip |
| U9 | Confirmation-grader output quality — blocked by 0311 | EXPR (verify-after-fix) | D evidence has the request; re-run post-fix |
| U10 | Ask-loop answer round-trip (public POST → trip fields) — blocked by 0313 | EXPR (verify-after-fix) | Endpoint logic code-read OK; needs live pass |
| U11 | Planning-gate required-fields source = `PlanningStageGate.tsx` (frontend-derived list) vs packet unknowns (backend) — two field-blocked definitions (Verified: both exist; whether they can diverge: Unknown — check: force a packet unknown outside gate list) | EXPR | If they diverge, operator sees "complete" while pipeline says blocked — potential future finding |
| U12 | Doors never sim'd: quotes (T4), seasons/suppliers/knowledge, payments absence, corporate policy, insights | EXPR (Sim #4 backlog) | Natural next suite; quotes especially since T4 deleted tiers |
| U13 | Runner hygiene: `submit_run` legacy method unused after draft-flow refactor | IMPL (5-min) | Remove per supersession rule (documented in commit message when committing) |
| U14 | Evidence JSONs contain full run payloads incl. raw notes with sim PII — fine (synthetic), but the runner should never be pointed at real agencies without a redaction flag | PROC | Add `--redact` flag note to tools/README when touching next |

### 1.3 Documentation & map updates

| # | Item | Disposition | State |
|---|------|-------------|-------|
| D1 | INDEX.md entry for Sim #3 docs | DOC | **Done this pass** |
| D2 | CODEBASE_FEATURES_FLOWS_LOOPS_MAP addendum: four doors + claims/asks/memory/ghost surfaces + the two-doors notes (U2, U3) | MAP | Task (T-map-1) |
| D3 | tools/README.md runner section | DOC | Done (prior pass) |
| D4 | Results/design/personas docs | DOC | Done |
| D5 | Findings store rows w/ evidence pointers | DOC | Done (14 rows total) |
| D6 | ZCode memory MEMORY.md oversize (35.4KB > 24.4KB limit; index lines too long) | PROC (memory hygiene) | Trim index lines, move detail to topic files — outside repo, flagged |
| D7 | Search-quota-gated research: Thai/India-side disruption regimes for the framework matrix (EXPR companion to 0312) | EXPR | Recheck 2026-10-06 17:07+ |

### 1.4 Process / owner decisions outstanding

| # | Decision | Why owner |
|---|----------|-----------|
| P-1 | FND-0315 posture: encrypt contact at inbound edge vs document dogfood limit | Privacy posture is owner-ratified territory (R-15) |
| P-2 | Commit authorization for the whole sim-3 artifact set (~15 files: tools, docs, evidence, screenshots) | Git safety rule |
| P-3 | U4 occasion→window inference rule ratification | Changes packet semantics |
| P-4 | U5 LLM-lane sim authorization | Posture/rung territory (ADR-008 §8) |

---

## 2. First-principles / long-term / doctrine verdict on the Sim #3 work itself (self-audit)

**Aligned (keep):**
- Findings through the canonical CLI only; verbatim scripts; predictions
  registered BEFORE execution (falsifiable design); evidence JSONs + inspected
  screenshots (Tier 4); runner as a durable reusable tool; docs-first.
- The defect classes themselves are first-principles-framed: membership
  proof over stoplists (0308), merge-over-replace for lists (0309), one
  root cause over two patches (0310/0311), single legal authority (0312),
  wiring over invention (0313), honest-unknown over default-1 (0314).

**Deviations & improvements (adopt):**
1. Sim #2 was browser-first; Sim #3 was API-first with screenshot sampling.
   Defensible (Tier 4 covers live runtime; reproducibility is better
   long-term) — but the UI visual pair rule (doctrine §3, 2026-09-22) means
   **UI-affecting fixes must ship BEFORE/AFTER captures**; the plan bakes
   that in (T-impl items carry visual-pair requirements).
2. The runner accumulated three mid-execution contract fixes — a
   `--dry-run contract probe` mode (assert the 5 door contracts before the
   scenario) would make future runs single-pass. (T-impl-9)
3. Evidence JSONs are verbose; a `--summary` mode emitting just the graded
   fields would make review cheaper. (Nice-to-have, folded into T-impl-9)
4. The sim stopped at first-order effects (packet fields). A follow-up sim
   should chase SECOND-order: does a garbage destination actually produce a
   wrong quote end-to-end? That's the money-path proof that makes P1s
   undeniable. (Fold into U12 Sim #4 design.)
5. Nothing is committed (git safety) — the artifact set needs an owner
   commit decision (P-2) before it becomes the durable record doctrine §14
   expects.

**Explicitly rejected directions (recorded per doctrine §9):**
- A stoplist-only fix for 0308 (whack-a-mole; every new Hinglish word
  re-breaks it; membership proof is the invariant).
- Auto-sending asks when questions exist (would violate the ADR-008 rung —
  ask-send is an operator action).
- Weakening the privacy guard to unblock T6 (the guard is owner-ratified
  fail-closed; the door needs an encrypted-contact path, not a bypass).
- A separate "sim findings" markdown register (forbidden — findings store
  v2 is canonical; AGENTS.md findings lifecycle rule 6).

---

## 3. Implementation plan (sequenced, S2-gated)

**Phase 1 — stop the bleeding (canonical, small, high-leverage):**
1. T-impl-1: refresh-500 root fix (0310+0311): sweep `db.refresh` after
   commit in services; one pattern; probe asserts both endpoints 200. S2.
2. T-impl-2: 0320 error contract: `PrivacyGuardError` → 422 + remediation
   body at router seam. S2.
3. T-impl-3: 0313 wiring: decision stage populates `follow_up_questions`
   from blocking unknowns (leverage existing TS-07 `required_for` graph);
   unify UI Ask buttons on decision as source. S2 + visual pair (Ask flow
   reachable in UI).
4. T-impl-4: 0316 JEV coherence gate (PROCEED requires zero blocking
   unknowns). S2.

**Phase 2 — extraction truthfulness (money-adjacent):**
5. T-impl-5: 0308 gazetteer-membership gate + definite-status posture
   enforcement (extend the `eeb2edbc` collision sweep; verify its current
   coverage first — Unknown→check). S2 + fixtures from sim voices (U6).
6. T-impl-6: 0309 candidate list-merge with provenance. S2 (pass2 keeps
   Varanasi).
7. T-impl-7: 0314 party ordinal guard + named-party parser + honest
   unknown. S2 + visual pair ("4 pax" → "2 pax" on the Sen trip).
8. T-impl-8: 0318 USD/EUR budget + cap-cue list. S2 (B budget_max=2400).

**Phase 3 — claims correctness (legal surface):**
9. T-impl-9: 0312 framework resolver + matrix fixtures (EU261/UK261/US_DOT/
   NONE+Montreal), consumed by evaluate + generate-claim + ghost concierge;
   0319 route-in-summary cosmetic rides along. EXPR companion: D7 research
   when quota resets. S2 (matrix unit tests) + one live C re-run.
10. T-impl-10: 0317 claim-card reachability (read-only decision-tab unlock
    for claim-bearing trips). Visual pair mandatory.

**Phase 4 — gates & knowledge:**
11. T-impl-11: U7 `sim3_acceptance_probe.py` (or fold checks into the
    existing sim2 probe file? — separate file, mirrored structure) wired
    into the probe suite; includes the `db.refresh` sweep grep gate.
12. T-map-1: D2 codebase-map addendum (four doors, U1 memory stores, U2
    reprocess doors, U3 token seam).
13. T-impl-12: U6 fixtures from the six sim voices into the adversarial
    corpus.
14. T-impl-13: U13 runner cleanup + U14 redaction note.

**Owner-gated (evidence prepared, work paused):** P-1 (0315 posture),
P-3 (occasion→window), P-4 (LLM-lane sim), P-2 (commits).

**Verification-after-fix (unblocks the ungraded list):** U8 (T2 trail),
U9 (confirm grader), U10 (ask round-trip) — each is one re-run of the
corresponding sim via `tools/sim3_runner.py`.

---

## 4. Open questions / falsifiers

- Does raw_input actually encrypt at rest on the /run path? (0315 check:
  read the persisted trip row for Ananya — ciphertext or plaintext email.)
- Does the `eeb2edbc` collision sweep cover single unrecognized tokens or
  only multi-token collisions? (0308 scoping check.)
- Can PlanningStageGate's required list diverge from packet unknowns? (U11
  check: craft a trip with an unknown outside the gate list.)
- Is the JEV `intake_action` consumed anywhere downstream (quotes?) such
  that the 0316 coherence gate changes more than display? (grep consumers.)

---

## 5. Implementation wave receipt (2026-10-05, same day — Phase 1–3 executed)

**11 of 14 findings CLOSED/FIXED** (FND-0308/0309/0310/0311/0312/0313/0314/
0316/0318/0319/0320), each with S2 fail-before/pass-after evidence and a
live Tier-4 re-run. Open: 0315 (owner posture decision), 0317 (frontend
claim-card task, T-impl-10), 0321 (bridge hardening).

**Landed:**
- `refresh_or_reselect` helper (spine_api/core/rls.py:295) — root cause
  PROVEN: session-level RLS GUC is lost when commit releases the pooled
  connection, so post-commit refresh re-checks out a GUC-less connection and
  FORCE RLS hides the row. 20 sites converted (customer_memory,
  confirmation_service ×6, booking_task ×5, routing ×7, membership,
  extraction_service ×5, workspace ×2); flush→refresh→commit sites in
  collection/document_service deliberately untouched (rationale comments).
- `PrivacyGuardError → 422 {reason, remediation}` handler (server.py) +
  inbound.py re-raise path.
- Decision ask-floor (decision.py Phase 9b) + the REAL 0313 root: the NB01
  ESCALATE short-circuit (orchestration.py) returned before the decision
  stage ever ran — blocked leads now carry their blocking-unknown questions.
  `blocking_unknowns()` canonical detector (validation.py:149) shared by
  both the floor and the JEV coherence guard (orchestration.py:
  PROCEED+blocking → PROCEED_WITH_ASKS).
- Destination sweep stoplist + definite-status invariant + merge-with-
  provenance (extractors.py) — extended the ratified eeb2edbc doctrine after
  discovering every garbage token IS a gazetteer member (Din=Iran,
  Aur=Colorado, Baad=Iran); membership proof alone cannot exclude them.
- Party counting precedence: named-age persons > relation words > speaker;
  the three views coalesce instead of summing (was 4→now 2 on the Sen note;
  first live fix was still wrong — 6 — caught by the Tier-4 re-run and
  corrected; the unit test alone was insufficient).
- Claims framework resolver (services/claim_framework.py): EU261/UK261/
  US_DOT/NONE+Montreal Art. 19; evaluate + generate-claim + ghost concierge
  rewired to one authority; BKK→BOM now honestly NONE (was US_DOT vs EU261).
- USD/EUR budgets + Hinglish cap cues ("se zyada nahi" → firm).
- Ghost route cosmetic (never "(->)").

**Live verification (post-fix re-runs):** A: dests=['Varanasi'], survives
reprocess. B: remember 200 (was 500), $2400 captured, dests=[Japan,
Vietnam]. C: inbound probe 422+remediation, evaluate=NONE+Montreal, letter =
"…UNDER THE MONTREAL CONVENTION 1999, ARTICLE 19…", ghost DRAFT_CLAIM,
disposition chain intact. D: party 2 pax (visual pair), send-ask 200/3
questions → public view 200 → traveler answers recorded:3 — the T1 ask loop
works END-TO-END for the first time. Confirm-extract 200.

**Tests:** 60 new (5 files) + 408 regression green + agent-suite runs (314/
549/79) — zero fixture edits forced except one test that had pinned
DRAFT_EU261_CLAIM for a non-EU route (the exact lie being fixed; flagged in
the agent report).

**Deferred in this wave (with reasons):** T-impl-10 (0317 frontend gate —
separate FE task), server-side wholesale trip overwrite in save_processed_trip
(extractor-side merge shipped; the operator "clear destination" path needs
design before touching the server merge — flagged by the extraction agent),
D7 research (search quota resets 2026-10-06 17:07), T-map-1, T-impl-13.
