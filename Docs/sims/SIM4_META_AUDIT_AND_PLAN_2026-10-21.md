# Sim #4 Meta-Audit & Implementation Plan — full candidate inventory, first-principles review, and the work queue

**Date:** 2026-10-21 · **Author:** ZCode (audit pass over Sim #4 "Eleven Doors")
· **Subject:** everything the Sim #4 session produced, surfaced, or implied —
registered findings, code-level inferences, doc/map gaps, process items —
classified per OPERATING_DOCTRINE §9 (candidate → disposition) and graded for
first-principles, long-term, and doctrine alignment. **Inputs:**
`SIM4_RESULTS_2026-10-21.md`, `SIM4_COUNCIL_JUDGEMENT_2026-10-21.md`,
`SIM4_DESIGN_2026-10-21.md`, personas doc, evidence dirs, findings store
(FND-0326..0350, FND-0321 reopened), the 2026-10-12 council register
(AUD-01..20), Sim #3 meta-audit (U-items carried).

**Truth labels** (doctrine §2): Observed / Verified / Inferred / Proposed / Unknown.

---

## 0. Session record (the "chat stuff", durably)

1. Ground truth: agent-start pack regenerated; Sim #2/#3 corpus read; 10-12
   council read; findings store = 0 P0/P1/P2 open at start (16 P3).
2. Environment facts discovered and handled: `:8000` held by an unrelated
   "Living Museum API" process (left untouched; backend run on `:8010`);
   Postgres not running (started `postgresql@17`); frontend started with
   `SPINE_API_URL` override; Playwright chromium installed for shots.
3. Parallel-agent drift noted: `Docs/audit/*` and `Docs/exploration/*` files
   dated today by other agents; Sim #3 findings 0315/0317/0321 closed
   2026-10-20 by a parallel wave; tree heavily uncommitted (git untouched).
4. Subagent explorers failed on a provider usage limit; all mapping, council
   seats, and grading were executed in-thread (disclosed in the council doc).
5. Docs-first: personas + design (P1–P47) written before execution.
6. Execution: dogfood lane (A–K + P), a first "beta" restart that FAILED TO
   BIND (old process kept serving — detected via `ps eww`, both lanes then
   re-run and labelled), beta lane (A,C,F,G,H,I,K), wave-3 probes; 7
   screenshots inspected; unit-level extractor probes for root causes.
7. A process-only `ENCRYPTION_KEY` was used for the beta lane (never written
   to `.env`); the resulting key mismatch for earlier rows surfaced FND-0327
   and left a handful of synthetic beta-lane rows readable only under that
   key — the Phase-1 re-encryption tool below resolves this (owned, not hidden).
8. 25 findings registered via `scripts/findings.py` (FND-0326..0350),
   FND-0321 reopened, FND-0346 superseded into it; store `validate` OK.
9. Council via `$council-orchestrator`: manifest, 6 seats, cross-exam, Lead
   synthesis; `validate_seat_labels.py` PASS.

---

## 1. Master inventory — every candidate, classified

Dispositions: **IMPL** · **EXPR** (exploration/research) · **DOC** · **MAP**
(exploration-map/registry) · **PROC** (process/owner decision). Evidence tier
stated per item.

### 1.1 Registered findings — fix paths + alignment verdicts

| FND | Item (label) | Disp. | First-principles assessment | Doctrine alignment | Best-shape fix (Proposed) |
|-----|--------------|-------|-----------------------------|--------------------|----------------------------|
| 0326 | Guard covers TripStore only; ledger/drafts/messages keep refused PII (Observed T4, both postures) | IMPL + PROC | A boundary that guards one of three doors is not a boundary. The fix is to make *persistence* the boundary, not one table. Posture (dogfood/beta) is orthogonal to coverage. | SECURITY_PRIVACY (R-15 owner-ratified — do not weaken); §11 data integrity; kernel: one canonical boundary | (a) Owner picks dev posture; (b) regardless: apply `_PII_FIELDS` encryption to run-ledger packets + drafts + message store, or route all three through `check_trip_data` — one seam (`persist_guard`) called by every store; (c) failed-run UX: structured `privacy_refused` run state + remediation, draft retained and linked (U19) |
| 0327 | `_decrypt_blob` foreign-token → 500 (Observed T4 + traceback) | IMPL | Legacy-plaintext tolerance and foreign-ciphertext are different cases; conflating them turns a key event into an outage. Versioned ciphertext is the invariant. | §11; §13 operator recovery | `{"__encrypted_blob":true,"v":2,"kid":<fingerprint>,"ciphertext":…}`; decrypt: parse-as-JSON-first for legacy, typed `EncryptedFieldUnreadable` → 409/422 with remediation (never 500); reusable `tools/reencrypt_trip_rows.py --from-key --to-key` (also cleans the sim rows) |
| 0328 | Answers recorded, never consumed (Observed T4) | IMPL | The loop's value is the second half. A write with no reader is a decoration. Consumption must flow through the canonical merge (authority/provenance), not a side-channel. | ADR-008 (answers are traveler facts, `explicit_user`); §6 field-merge precedence | `reassess`/`run` call `field_merge` with each `traveler_answers` entry (`authority=explicit_user`, `channel=ask_link`, span=answer text) BEFORE validation; answered unknowns cleared; display header already consumes — unify on packet |
| 0329 | Homonym epithets definite; regions dropped (Verified T2 + T4) | IMPL | Membership ≠ intent. `definite` must mean *corroborated*: a destination cue, or ≥2 signals, or resolver agreement. Regions are first-class destinations in Indian domestic travel. | §2 fact vs hypothesis; Sim #3 self-audit rejected stoplist-only | (1) leading-token epithet guard (sentence-initial adjective/noun words that are also gazetteer names → hypothesis unless cued); (2) `definite` requires cue corroboration; (3) IN states/UTs + canonical regions layer with `destination_kind`; (4) parenthesised multi-city "(A + B)" pattern; (5) sim voices → fixtures |
| 0330 | Group share 401 (Observed T4) | IMPL | A public share is a capability token, not an auth session. Same pattern as `/a/{token}` and `/p/{token}` — reuse, don't invent. | ADR-008 (shares are operator-sent); PT-01 token discipline | Make `GET /api/v1/group/token/{token}` + `pay-share` token-gated (signed, TTL, revocable) without session auth; exposes only the invitee's own share |
| 0331 | ~~purpose/duration dropped from facts~~ **RETRACTED** (Observed T4 live: `trip_purpose=honeymoon`, `trip_duration_days={7,7}` present) | — | The runner's digest allow-list used the wrong key names; a false finding caught by re-checking the raw trip before coding. | §2 (verify before asserting) | Runner keep-list fixed (`tools/sim4_runner.py pack`); store closed `no_go` with evidence |
| 0332 | Gate contradicts facts (Observed T4 screenshot) | IMPL | Two definitions of "complete" guarantee divergence; the gate must read the one canonical unknowns graph. | §11 canonical validation; U11 (Sim #3) | `PlanningStageGate` consumes `validation`/`blocking_unknowns` from the backend (expose in `TripResponse` if absent); FE required-list becomes labels only; visual pair |
| 0333 | noop extractor fabricates (Observed T4) | IMPL | A noop must say "no". Placeholders at 0.85 are fabricated confidence on passport data. Duplicate content must be flagged. | §13 claim reality; honesty taxonomy | noop → `status: NOT_EXTRACTED`, `confidence: null`, `fields: []`; content-hash dedup flag on upload |
| 0334 | Inbound duplicates + no message rows (Observed T4) | IMPL (+EXPR design) | Inbound is a *message* door that happens to create leads; linkage first, creation second. | FND-0284 class; T6 contract | Match existing lead (agency + booking ref / contact / name+recent) → attach message row; else create + `duplicate_candidate` flag; always write message store |
| 0335 | Erasure leaves name + memory (Observed T4) | IMPL | Art.17 is per-subject, not per-table; the orchestration must enumerate stores. The forget door already works — call it. | SECURITY_PRIVACY; T14 | Erasure orchestrator: trip (incl. `customer_name`, display fields), drafts, messages, `CustomerMemoryProfile` (via `/memory/forget` service), run-ledger packet; certificate lists stores |
| 0336 | Export empty (Observed T4) | IMPL | A DSAR response with `{}` is a non-answer. | T14 | Export reads `extracted.facts`, booking data, messages, memory profile, answers; provenance per field |
| 0337 | Compiler economics (Observed T4) | IMPL | Numbers without basis coherence are fabrication even when labelled preview. Feasibility against the customer's budget is the first gate. | §13; FND-0268 basis doctrine | Budget-feasibility gate (`exceeds_budget` flag + reason), INR-native or explicit FX line with rate basis, return `provenance_assertions`, bound take-rate to policy |
| 0338 | Audit violation from estimate; class rule unwired (Observed T4) | IMPL | Estimated inputs can warn, never convict. The policy already states the class/duration rule — evaluate it. | §13 claim reality (corporate surface) | Violations only from sourced inputs; estimated → warnings; evaluate `allowed_flight_class` + `max_flight_duration_for_business_hours` from packet/strategy class + route duration |
| 0339 | Visa invented type undisclosed (Observed T4) | IMPL | Same class as FND-0312: a wrong-but-confident determination on a legal surface. Conservative default is fine for *validity*; type must disclose the miss. | §13; FND-0312 precedent | `registry_match: false` + `visa_type_required: UNKNOWN_VERIFY` + Timatic language for misses; keep validity math |
| 0340 | BFF parity: 11 door families product-unreachable (Observed T4 probe) | IMPL + PROC | "Shipped" means reachable from the product. Deny-by-default is right; the gap is a missing inventory gate. | §13 feature-vs-code readiness; AGENTS route-map allowlist | CI gate: product-facing backend routes must have a route-map key; owner decides which doors need UI before launch (T14 DSR is non-optional) |
| 0341 | USD default on unmarked amounts (Verified T2) | IMPL + PROC | Locale is agency state, not a global constant. | D1 RQ-01 (documented decision — revisit) | `AgencySettings.default_currency` → extractor default; owner ratifies the RQ-01 change |
| 0342 | Quotes/accounting unreachable for blocked leads (Observed T4) | IMPL (UI label) + EXPR | Empty with no state is indistinguishable from broken. | §13 | UI state "Quotes unlock when the lead is planning-ready" + what's missing; EXPR: labelled partial preview |
| 0343 | UI "1 pax" vs packet 2 (Observed T4) | IMPL | FE fallback-to-1 reintroduces the absent-not-1 antipattern. | §2 | Read packet party; absent → "party not set"; visual pair |
| 0344 | Per-person scope lost; multi-city collapsed (Observed T4) | IMPL | Scope is part of the number. | §2 | Derived total with scope label (packet `derived_total` with provenance); destination display lists all candidates |
| 0345 | Analytics caps as totals (Observed T4) | IMPL | A capped scan is not a count. | §13 | COUNT queries or "first N" labels |
| 0321 | Loop-teardown residual (Observed T4 logs) | EXPR→IMPL | AUD-08 named 7 stores; 5 fixed. | §11 | Per-store loop-id probe; fix remaining stores |
| 0347 | Guard message wrong knob (Verified T2) | IMPL + DOC | The remediation must name the real control. | §13 | Message names `DATA_PRIVACY_MODE`; docs row |
| 0348 | Send not idempotent (Observed T4) | IMPL | Two live asks for one question set = confusion. | ADR-008 | 409 or reuse the open ask |
| 0349 | Occasion order; U4 inference (Verified T2) | IMPL (regex) + PROC (U4) | Small regex win; the window inference changes packet semantics → owner. | §2 | Date-before-occasion branch; U4 stays owner-gated |
| 0350 | Colloquial count nouns / solo (Verified T2) | IMPL | Honest-unknown is correct; cheap nouns raise recall. | §2 | Add guys/folks/ladies/mates/colleagues; `solo` → 1 |

### 1.2 Inferred-but-unregistered observations → follow-through

| # | Candidate (label) | Disp. | Notes |
|---|-------------------|-------|-------|
| U1 | Dev privacy posture: dogfood (strict) vs beta+key (encrypted) as the default local posture (Observed both) | PROC (owner; Sim #3 P-1 redux) | Either is coherent only with full coverage (0326) |
| U2 | PAN redact-at-ingest in ALL modes (Luhn) — card numbers are never product-needed (Inferred) | PROC (new R-15 row) + IMPL after ratification | Does not weaken any matrix row; probe ready |
| U3 | Ciphertext key id + re-encryption tool (part of 0327) | IMPL | Also resolves the sim's beta-lane rows |
| U4 | CI BFF parity gate (route-map keys vs product-facing routes) | IMPL (test) | Makes 0340 permanent |
| U5 | Sim #4 voices → adversarial fixtures (E1, J1/J4, D1, C2, A1) | IMPL | failure-becomes-fixture rule |
| U6 | `tools/sim4_acceptance_probe.py` S2 vehicle (0327/0328/0331/0333/0329/0347) | IMPL | mirrors sim3 probe |
| U7 | Runner hygiene: `--shots` trip resolution by step name; `tools/README.md` section; `sim3_sims._find_trip` newest-trip fallback has the same contamination flaw | IMPL (small) | Fix both runners |
| U8 | `/followups/generate` copy template glitch ("your custom your destin…") (Observed) | IMPL (small) | verify template |
| U9 | Triage intent `general_inquiry` for a passport-expiry panic; routing on 0.28 confidence (Observed) | EXPR | Jev lane calibration (FND-0322 lineage) |
| U10 | LLM-lane destination resolver vs 'Solo'/'Young' | EXPR (owner-gated X-09) | |
| U11 | Budget supersession lost on cumulative notes (P41) (Observed) | EXPR→IMPL | latest-scalar-wins with trail (T2) |
| U12 | Relative dates: "next weekend", "next month", "2 weeks from now" (Observed misses) | IMPL | date extractor gap, cheap |
| U13 | Memory→run wiring (Sim #3 P7 residual) still absent (Verified at design) | EXPR→IMPL | returning-guest signal |
| U14 | Night-split "(2 nights jaipur, 1 night udaipur)" never becomes a branch option (Observed) | IMPL (small) | TS-06 pattern |
| U15 | Mobility attribution blended (Sim #2 F1 class) | carry-over | travelers entity |
| U16 | Docs/map: INDEX.md, codebase map addendum (eleven doors, posture matrix, persistence doors, BFF parity), EXPLORATION_TOPICS, LAUNCH_STATUS refresh (TRV-N01) | DOC/MAP | this pass + task |
| U17 | `.env.example`/docs: local realistic dogfooding needs `DATA_PRIVACY_MODE` + key guidance | DOC | with 0347 |
| U18 | ZCode MEMORY.md oversize (flagged by harness) | PROC (memory hygiene) | outside repo |

### 1.3 Process / owner decisions outstanding

| # | Decision | Why owner |
|---|----------|-----------|
| P-1 | Dev posture default (U1) + guard-all-doors vs encrypt-all-doors (0326) | R-15 is owner-ratified |
| P-2 | PAN redact-at-ingest as a new R-15 row (U2) | Changes customer text at rest |
| P-3 | Which BFF-unmapped doors need UI before launch (0340) | Scope/launch |
| P-4 | Agency default currency replacing RQ-01 USD default (0341) | Documented decision |
| P-5 | U4 occasion→window inference | Packet semantics |
| P-6 | LLM-lane sim (U10) | Posture/rung |
| P-7 | Commit authorization for the Sim #4 artifact set (docs, tools, evidence, fixes) | Git safety |

---

## 2. First-principles / long-term / doctrine verdict on the Sim #4 work itself (self-audit)

**Aligned (keep):** docs-first falsifiable predictions; verbatim scripts;
canonical findings CLI only; two-posture lanes labelled honestly; unit
probes to convert black-box failures into root causes; runner as a reusable
tool with env-selectable backend/evidence dir; council via the skill with
validated seat labels; the parity probe distinguishing BFF-deny from
forwarded 404s.

**Deviations & improvements (adopt):**
1. The first "beta" restart failed to bind and I initially graded the
   second lane as beta — caught by checking the process environment. Rule
   added to the runner docs: verify posture in-process (`ps eww`) before
   labelling a lane.
2. Changing `ENCRYPTION_KEY` mid-session created mixed-key rows in the shared
   test DB. Correct long-term answer is the re-encryption tool (Phase 1),
   not a key file in `.env`.
3. The newest-trip fallback contaminated one sim; strict run-ledger
   resolution is now the rule (both runners).
4. Subagent unavailability meant one executor voiced all seats; the council
   doc discloses it and keeps evidence/inference/judgement separated.

**Explicitly rejected directions (doctrine §9):**
- Weakening the privacy guard to open doors (R-15 ratified).
- Stoplist-only fix for 'Solo'/'Young' (Sim #3 rejected; invariant is
  corroboration).
- Removing auth from the group share without a capability token.
- Writing the beta key into `.env` to "make it work".
- A markdown findings register for Sim #4 (store v2 is canonical).

---

## 3. Implementation plan (sequenced, dependency-aware, S2-gated)

**Phase 1 — persistence safety + facts never lost (canonical, no owner gate):**
1. T-impl-1 (0327): versioned ciphertext + legacy/foreign discrimination +
   typed error; `tools/reencrypt_trip_rows.py`; S2: foreign-token read → explicit
   unreadable marker + `encryption_warnings`, legacy plaintext still reads; re-encrypt the sim rows.
2. T-impl-2 (0331): RETRACTED — no work.
3. T-impl-3 (0328): answers → `field_merge` in reassess/run; S2: recorded
   `origin_city` clears the unknown after reassess. Depends on nothing;
   benefits from T-impl-2's slot plumbing.
4. T-impl-4 (0333): noop extractor honesty + content-hash dedup flag; S2.
5. T-impl-5 (0347 + U17): guard message + docs.

**Phase 2 — extraction truthfulness:**
6. T-impl-6 (0329): epithet guard + cue-corroborated `definite` + region
   layer + "(A + B)" pattern; U5 fixtures; S2: E1 → Japan/Tokyo/Kyoto,
   'Solo' absent; J4 → 'Young' absent; J1 → Kerala.
7. T-impl-7 (0350/U12/0349-regex): count nouns, `solo`, relative dates,
   date-before-occasion. S2 unit.
8. T-impl-8 (0341): agency default currency — after P-4.

**Phase 3 — honesty on legal/money surfaces:**
9. T-impl-9 (0338): estimate → warning only; class/duration rule. S2 on B.
10. T-impl-10 (0339): registry-miss disclosure. S2 on E.
11. T-impl-11 (0337): feasibility gate + FX line + provenance. S2 on D.
12. T-impl-12 (0342): quotes state label (FE) — visual pair.

**Phase 4 — DSR completeness (compliance):**
13. T-impl-13 (0335): erasure orchestrator across stores (calls memory
    forget). S2 on F (beta lane).
14. T-impl-14 (0336): export completeness. S2 on F.

**Phase 5 — product reachability + UI truth:**
15. T-impl-15 (0332): gate reads canonical unknowns; visual pair.
16. T-impl-16 (0343/0344/U14): FE party/scope/derived total; branch option
    for night-splits; visual pairs.
17. T-impl-17 (0330): group share capability token (reuse proposal signing
    seam); S2: unauthenticated GET 200 for the invitee's own share.
18. T-impl-18 (0340/U4): CI parity gate + per-door decisions after P-3.
19. T-impl-19 (0348): send idempotency.

**Phase 6 — infra + boundary:**
20. T-impl-20 (0321): per-store loop audit + fix.
21. T-impl-21 (0326/U19): persistence boundary across ledger/drafts/messages
    + structured `privacy_refused` run state — after P-1 for posture; the
    encryption of ledger/drafts can proceed as additive hardening now.
22. T-impl-22 (0334): inbound linkage + message write.
23. T-impl-23 (0345): analytics counts.

**Phase 7 — gates & knowledge:** U6 acceptance probe; U7 runner hygiene +
README; U16 docs/map; U8 template glitch.

**Owner-gated (evidence prepared, work paused):** P-1..P-7 above.

**Verification-after-fix:** re-run `tools/sim4_runner.py --sim D,E,G,J,K`
(+ beta lane F) as the Tier-4 proof; `tools/sim4_acceptance_probe.py` as the
S2 gate; targeted pytest + ruff + tsc; `scripts/findings.py close` with the
probe output as evidence.

---

## 4. Task list (live — updated as work proceeds in this session)

| # | Task | Status |
|---|------|--------|
| T-impl-1 | 0327 versioned ciphertext + discrimination + typed error + re-encrypt tool | **done** (6 tests; 9 rows rotated; live 200s) |
| T-impl-2 | 0331 — RETRACTED, no code change needed | **done** (retraction) |
| T-impl-3 | 0328 answers → canonical slots + identity-safe write | **done-part** (4 tests; live: slot written + overlay consumed by the run; remaining = FND-0351 save-path + lossy draft-flow input) |
| T-impl-4 | 0333 noop extractor honesty + dedup flag + explicit MockExtractor | **done** (2+67 tests) |
| T-impl-5 | 0347 guard message names the real knobs | **done** (71 tests) |
| T-impl-6 | 0329 epithet guards + region layer + paren-tolerant city-set | **done** (9 tests + 262 regression) |
| T-impl-7 | 0350/U12/0349 cheap extraction wins | **done 2026-10-23** (guys/folks/ladies + solo→1; occasion reverse order w/ named groups; 4 tests + 9 regression — initially mis-marked done before implementation; corrected) |
| T-impl-9 | 0338 corporate audit honesty (estimate warns; class/duration rule wired) | **done** (7 corporate tests) |
| T-impl-10 | 0339 visa registry-miss disclosure (UNKNOWN_VERIFY + Timatic) | **done** (51 visa tests) |
| T-impl-13 | 0335 erasure orchestrator (identity cascade incl. drafts/raw note) | **done** (live: memory ERASED ✓) |
| T-impl-14 | 0336 export completeness (raw_note + draft_messages) | **done** (live: draft note exported) |
| T-impl-15 | 0332 gate reads canonical unknowns (FE) | queued |
| T-impl-16 | 0343/0344 FE party/scope | queued |
| T-impl-17 | 0330 group share capability token | queued |
| U5/U6 | fixtures (tests/test_sim4_destination_context.py voices) + acceptance probes (4 new sim4 test files) | **done** (probe-as-tests form) |
| U7/U16 | runner hygiene + README + INDEX + map addendum | queued |
| T-impl-8/11/12/18..23 | remaining phases | queued (see §3) |

(Status cells are updated in place as each unit lands with S2 evidence; the
authoritative receipt is §5.)

---

## 5. Implementation wave receipt

See the section appended at the end of this file after the wave (same-day).


---

## 5. Implementation wave receipt (2026-10-21, same session)

**7 findings closed/fixed with live Tier-4 + test evidence** (FND-0327, 0329,
0333, 0335, 0336, 0339, 0347) + **1 retracted** (0331, runner artifact) +
**1 partially fixed with live proof and a precise residual** (0328 → FND-0351
carries the remaining save-path/input-loss work) + **FND-0321 reopened** with
fresh telemetry. **2 pre-existing reds exposed and registered** (FND-0358
booking_data contract break — fails at HEAD; FND-0359 suite-composition
pollution).

**Landed (code):**
- `src/security/encryption.py`: `key_fingerprint`, `decrypt_strict`,
  `looks_like_fernet_token` (FND-0327).
- `spine_api/persistence.py`: v2 blobs with `kid`; unreadable-marker +
  `encryption_warnings` (never a 500); foreign-key PII sentinel.
- `tools/reencrypt_trip_rows.py`: RLS-scoped key-rotation tool (dry-run
  default); rotated the 9 mixed-key sim rows (28 fields, 0 unreadable).
- `spine_api/routers/public_asks.py`: `_apply_answers_to_facts` — canonical
  slot writes + corrupted-list self-heal + overlay aliases (FND-0328 part 1).
- `src/intake/extractors.py`: epithet guards (sweep + verbless),
  `_COMMON_WORD_TOPONYMS` += solo/young, `_REGION_DESTINATIONS` layer,
  paren-tolerant city-set (FND-0329).
- `spine_api/services/extraction_service.py`: honest `NoopExtractor`;
  explicit opt-in `MockExtractor` (FND-0333).
- `spine_api/routers/trip_documents.py`: `duplicate_of_document_id`,
  `provider_note` (FND-0333).
- `src/security/privacy_guard.py`: `_block_message` names the real knobs
  (FND-0347).
- `spine_api/routers/corporate_policy.py`: estimated costs warn, never
  convict; business-class/duration rule evaluated (FND-0338).
- `spine_api/services/visa_radar.py`: registry-miss → `UNKNOWN_VERIFY` +
  Timatic disclosure (FND-0339).
- `spine_api/services/trip_dsr.py` + `spine_api/routers/dsr.py` +
  `spine_api/routers/customer_memory.py`: speakers scrub; `raw_note` +
  `draft_messages` in the Art.15 export; identity-based memory cascade
  (`forget_profiles_matching_identity`) in Art.17 (FND-0335/0336).

**Tests:** 6 sim4 test files new (encryption rotation 6, answer slots 4,
destination context 9, noop honesty 2, plus updated contract pins in
document/attempts/vision 67, visa 51, corporate 7, privacy 71, smoke 14 —
all green file-wise); ruff clean on every touched path; frontend tsc clean.

**Full-suite census (honest):** WITHOUT privacy env: 138F/5204P — dominated
by the dogfood guard 422-ing PII-shaped endpoint tests (posture, not code).
WITH `DATA_PRIVACY_MODE=beta`: **71F/5401P**. The census is
composition-sensitive (constraint-engine file: 37F in census, 37P alone in
the same tree; doc-extraction 0F file-alone) and master advanced mid-session
(3a41d134). Classification of the 71 vs HEAD is the top follow-up (FND-0359
note has the repro commands); every file containing a Sim #4 diff passes
file-wise, but a per-file bisect of the 71 is owed before a "zero
regressions" claim.

**Deferred with reasons:** T-impl-8 (currency default — owner P-4),
T-impl-11/12 (compiler economics + quotes label), T-impl-15/16/17 (FE gate/
pax/scope + group share token), T-impl-18..23 — queued with dependencies in
§3; FND-0326 posture decision (P-1) blocks its implementation by design.


---

## 6. Door-fix wave receipt (2026-10-23) — the two last-inch doors are OPEN

**Door 1 — group share (FND-0330, was 401/404 at the last step):**
THREE stacked causes, all fixed:
1. `AuthMiddleware` allowlist lacked the capability-token prefix → added
   `/api/v1/group/token/` (identical posture to the ratified
   `/api/v1/proposals/token/`; `/group/{trip_id}/invites` and
   `/manual-override` stay session-authed). Pinned by
   `tests/test_sim4_public_capability_paths.py`.
2. `get_trip_by_group_token` scanned **GUC-less under FORCE RLS** — zero rows
   visible, 404 even when authed. Rewritten as
   `TripStore._scan_all_agencies_for_trip`: enumerate agencies (non-RLS
   table), scan each under its own GUC, canonical analytics decrypt (the
   invitee sees their NAME, not a Fernet token), `agency_id` carried for the
   FND-0290 attribution guard.
3. `get_trip_by_proposal_token` had the **identical FORCE-RLS hole** (twin
   door, latent on the SQL backend since the RLS wave) — same per-agency scan.

**Live S2:** unauthenticated `GET /api/v1/group/token/{tok}` → 200 with the
invitee's own share (name "Kavya Nair", ₹5,000 share); unauthenticated
`pay-share` → 200 `NOTIFIED_PAID` (tracking only — money boundary held).
Suites: group_booking_router 25 + group/fulfillment/group_and_vault 28 green.

**Door 2 — ask-loop consumption (FND-0351 + 0328 residual):**
1. Lossy input fixed: `build_reassessment_request_from_trip` falls back to the
   linked draft's `customer_message` when `raw_input.submission` is absent
   (draft-flow trips carry the traveler's words ONLY in the draft).
2. Destructive refresh fixed: `_preserve_authoritative_facts` in the preserve
   path carries forward `explicit_user`/`operator` fact slots a re-extraction
   lacks or downgrades — an answered question can never regress to unknown.
**Live S2 (fresh Sens trip):** send 3 questions → unauthenticated answers 200
→ auto-reassess consumed them → `follow_up_questions: []`,
`origin_city=kolkata` (`explicit_user/traveler_ask_link`), date_window filled.
Tests: `tests/test_sim4_reassess_losslessness.py` 5/5.

**Also this wave:** FND-0348 closed no-go (the send endpoint already 409s on
zero open questions — the "empty token page" was the page fetched after
answers landed; `status` correctly flips open→answered). FND-0366 registered
P0: the canonical test-agency trip corpus (45,944 rows) was WIPED mid-session
by a parallel wave while commits landed on master — triage/recovery owned
separately (evidence + candidate deleter in the finding).


---

## 7. Continuation-wave receipt (2026-10-23, "fix the doors")

**Both last-inch doors are OPEN, live-verified:**

- **Door 1 — group share (FND-0330)**: three stacked causes fixed —
  (1) `AuthMiddleware` allowlist gained `/api/v1/group/token/` (capability-
  token posture, advisor routes stay authed; pinned in
  `tests/test_sim4_public_capability_paths.py`); (2) `get_trip_by_group_token`
  scanned GUC-less under FORCE RLS → rewritten as per-agency GUC scan
  (`_scan_all_agencies_for_trip`) with canonical analytics decrypt (invitee
  sees their name, not ciphertext) and `agency_id` for the FND-0290 guard;
  (3) `get_trip_by_proposal_token` had the identical hole (twin) — same fix.
  Live: unauth share 200 (name + share_cents), unauth pay-share 200
  NOTIFIED_PAID.
- **Door 2 — ask-loop consumption (FND-0351 + 0328)**: (1) draft-note fallback
  in `build_reassessment_request_from_trip` (draft-flow trips carry the
  traveler's words only in the draft); (2) `_preserve_authoritative_facts` in
  the preserve path — answered/operator slots can never be erased or
  downgraded by a re-extraction. Live: fresh Sens trip → send 3 → unauth
  answers → auto-reassess consumed them → `follow_up_questions: []`,
  origin_city persisted `explicit_user`.
- **FND-0348 closed no-go** (send already 409s on zero open questions; page
  flips open→answered by design). **FND-0349/0350 fixed** (occasion reverse
  order; guys/folks/ladies + solo→1) — with an honesty correction: the
  receipt had claimed T-impl-7 done before implementation; corrected, then
  actually landed with tests (`test_sim4_extraction_wins.py` 4/4).
- **FND-0366 corrected + deferred**: the "corpus wipe" P0 was an RLS artifact
  — FORCE RLS (enabled on trips by a parallel wave mid-arc) makes GUC-less
  sessions (psql included) see zero rows; verified 47,925 rows intact via a
  canonical-GUC session. Deferred with a precise reopen condition
  (CanonicalDataDeletionError from the landed `tests/_data_safety_guard.py`
  CI tripwire, or a GUC-set count below baseline).
- **New pre-existing class noted** (under FND-0359): `component_key` column
  missing locally — parallel commit 7f30f252's migration not applied to the
  dev DB; two confirmation tests fail on it.

**Store state:** 11 Sim4-area findings closed fixed + 1 retracted + 2 no-go/
deferred; open P1s remaining: 0332 (FE gate source), 0334 (inbound dedupe),
0337 (compiler economics); open P2s: 0340 (BFF parity gate), 0341-0345, 0358/
0359 (pre-existing). Owner decisions DP-03a-e pending.


---

## 8. Continuation-wave receipt 2 (2026-10-23, "do them all") — the full remaining queue

**Applied the pending DB migration:** `booking_confirmations.component_key`
(ADD COLUMN IF NOT EXISTS, mirrors model server_default 'primary') — 5/5
confirmation tests green.

**FND-0337 (P1, money honesty):** `compile_from_intake` gains
budget_amount/budget_currency; the budget feeds the CANONICAL
ConstraintEngine FINANCIAL_BOUND family (no parallel gate invented); the
package carries `budget_check` with the honest tri-state — same-currency
comparison authoritative (BUDGET_CEILING/TARGET_EXCEEDED → within_budget
false), INR-vs-USD REPORTED (BUDGET_CURRENCY_UNVERIFIED + component totals,
within_budget null), no budget = no claim. Router /compile reads the trip's
persisted budget facts AND gained the missing `Depends(get_current_agency)`
tenant gate. Tests: test_sim4_compiler_budget_gate.py 5/5.

**FND-0334 (P1, inbound door):** `_resolve_existing_lead` matches an existing
non-terminal lead before minting (explicit contact → identity scraped from
the message text → exact name), bounded 5×500 multi-page scan (a single
100-row page missed recent leads in the accumulated corpus); parse persists
top-level contact_email/phone on create so future matches work; the message
row is ALWAYS written (message_store.append_message — T6's store half).
LIVE S2: second inbound from the same traveler ATTACHED (t1==t2) with 2
message rows. Inbound suite 44/44.

**FND-0332 (P1, FE dead-end):** `getRequiredPlanningFields` consults the
canonical packet facts (`readPacketFacts` normalizes both slot shapes) before
declaring Budget/Origin/Destination/Window/Party missing — a display column
lagging the packet can no longer lock workspace tabs (the Sens lead held
budget_max+Varanasi while the gate demanded both). `Trip.extracted` typed in
api-client. vitest planning-status 15/15 (2 new tests incl. the live Sens
shape). The two tsc errors in EmptyStateOnboarding.outcomes.test.tsx are
pre-existing and unmodified by this session.

**FND-0343/0344 (FE truth):** the fabricated party fallback-1 removed
(absent party renders "Party to confirm", never "1 pax"); per-person budget
scope surfaced ("₹18,000 per person (~216,000 total for 12)").

**FND-0345:** analytics pipeline (10k cap) and bottlenecks (1k cap) replaced
with the canonical `_all_agency_records` pager; verified live: the canonical
pager yields 48,172 trips and totalInquiries reads 48,172.

**FND-0340:** CI parity gate landed (`tests/test_bff_parity_gate.py` +
`tests/fixtures/bff_parity_known_gaps.json` — 46-route snapshot captured
2026-10-23): the product-facing GET gap set can never silently GROW, and the
snapshot must stay fresh (stale pinned routes fail). Shrinks as DP-03c
decisions map doors.

**FND-0342 closed no-go:** quotes/PageClient already renders the explicit
`quotes-not-ready` panel with the missing-inputs list — wave-1 graded the API
contract, not the UI.

**FND-0366 deferred with corrected facts:** the "corpus wipe" was an RLS
artifact (FORCE RLS + GUC-less sessions see zero rows); 47,925 rows verified
intact via canonical-GUC session. Deferred with a precise reopen condition
tied to the landed _data_safety_guard tripwire.

**Also:** `component_key` migration applied (5/5 confirmation tests);
FND-0348 closed no-go; FND-0321 reopened→0346 superseded into it;
T-impl-7 receipt corrected then actually landed (0349/0350 fixed).

**Remaining open:** FND-0341 (P2 — blocked on DP-03d owner currency call),
0358/0359 (pre-existing reds, evidence recorded), DP-03a–e owner decisions.
