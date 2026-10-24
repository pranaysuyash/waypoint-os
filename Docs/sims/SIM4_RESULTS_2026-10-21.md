# Sim #4 Results — "Eleven Doors" (eleven personas, eleven product doors, live run, two privacy postures)

**Date:** 2026-10-21 · **Executor:** ZCode (API-driven via `tools/sim4_runner.py`
+ `tools/sim4_sims.py` + `tools/sim4_wave3_probes.py`, Playwright screenshots
against the real product; backend **`:8010`** (port 8000 held by an unrelated
process, untouched), frontend `:3005` with `SPINE_API_URL` override,
`TRIPSTORE_BACKEND=sql`, Postgres `waypoint_os`, test agency
`d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b`) · **Design:**
`Docs/sims/SIM4_DESIGN_2026-10-21.md` (P1–P47) · **Personas:**
`Docs/sims/personas/SIM4_PERSONAS_2026-10-21.md` · **Evidence:**
`Docs/sims/assets/sim4/evidence/` (dogfood posture, corrected contracts),
`evidence_dogfood/` (snapshot), `evidence_beta/` (beta posture + wave-3), 7
inspected screenshots `Docs/sims/assets/sim4/UI_*.png` · **Council:**
`Docs/sims/SIM4_COUNCIL_JUDGEMENT_2026-10-21.md` · **Meta-audit + plan:**
`Docs/sims/SIM4_META_AUDIT_AND_PLAN_2026-10-21.md`.

**Environment note (honest telemetry):** `/health` → `llm.available: false`
(OpenAI path) — the deterministic extraction/decision lane is the ratified
production posture (ADR-008 §8). The TypeSafe/Jev triage lane IS live
(`source: "jev"` on `/api/triage/message`). Sims ran in **two privacy postures**
because the first lane revealed that posture decides whether whole doors exist:
(1) `DATA_PRIVACY_MODE` unset = `dogfood` (repo default, no `ENCRYPTION_KEY`);
(2) `DATA_PRIVACY_MODE=beta` + a fresh process-only `ENCRYPTION_KEY` (never
written to `.env`). A mid-session key change between lanes also surfaced a
real defect (FND-0327) — recorded, not hidden.

**Standing verdict: eleven doors opened; two are structurally broken at the
last step (group share, ask-loop consumption), two are honest-but-empty
(Art.15 export, quotes for blocked leads), two fabricate on compliance/money
surfaces (noop passport extractor, proposal compiler economics), and the
privacy posture itself is the biggest single determinant of product behaviour
— and its boundary is partial.** **25 findings registered (FND-0326..0350;
1 P0, 12 P1, 7 P2, 4 P3 after retracting FND-0331 as a runner artifact; FND-0346 superseded into the reopened FND-0321).**

---

## 1. What ran (verbatim scripts executed in full)

| Sim | Persona | Door | Steps executed (lanes) |
|-----|---------|------|------------------------|
| 4-A | Kavya Nair (12-person offsite) | group/MICE + multi-city | run → packet → group invites → public share → soft-hold (dogfood + beta + W3) |
| 4-B | Ritu Malhotra (corporate) | corporate policy | policy-rules → run → audit-policy → approve-override (dogfood, corrected) |
| 4-C | Rehan Qureshi (adversarial) | privacy Layer-2 + injection | C-full (PAN) run+poll → PAN negative controls → C-inject run → packet (both lanes) |
| 4-D | Arjun & Isha (honeymoon) | quotes T4 + proposal compile | run → packet → quotes → compile (full body) → public proposal (dogfood, corrected) |
| 4-E | Nikita Iyer (solo, IN passport) | visa radar | run → packet → /check IN→JP + IN→TH contrast → trip requirements (dogfood) |
| 4-F | Meera Krishnan (GDPR) | DSR Art.15/17 + memory | run → remember → export → erasure → re-fetch all stores (both lanes) + W3 forget |
| 4-G | Priyanka Sen (returning) | ask-loop round trip 2 | run → dashboard → send via **BFF** + direct → public page → answers → reassess (beta + W3) |
| 4-H | Dinesh Kulkarni (+child) | triage + inbound + pre-departure | run → triage → inbound parse (`whatsapp_web`) → messages → pre-departure bundle (both lanes) |
| 4-I | Elena (owner seat) | money ops tracking-only | run → mandate register/get/revoke/revoke-again → commission split → accounting export → analytics (dogfood, corrected) |
| 4-J | Devi Sharma (4 notes) | reprocess stress | 4× draft PATCH + run on one draft, packet after each, asks survival (dogfood) |
| 4-K | Farhan Ali (documents) | stage-gated documents | run → uploads (403 at discovery) → W3: stage→proposal → valid/zip/dup uploads → extract → accept → download-url |
| P | — | BFF parity | 21 doors × 2 path shapes through the product BFF |

Runner contract errors found mid-execution and corrected (left as evidence,
Sim #3 precedent): override path missing `/{trip_id}`, compile body needs the
full `CompileProposalRequest`, inbound `channel` enum (`whatsapp_web`), mandate
`purpose` enum (`INITIAL_DEPOSIT`), documents router has no `/api/v1` prefix,
`find_trip` newest-trip fallback (removed — it silently graded the previous
sim's trip when a run FAILED), a bind failure on the first "beta" restart (the
old process kept serving dogfood; detected via `ps eww`, fixed, both lanes
re-run and labelled).

## 2. Predictions vs outcomes (design doc P1–P47)

| # | Prediction | Outcome |
|---|-----------|---------|
| P1 | "12 people" → party 12 | **PASS** (facts + UI "12 pax") |
| P2 | ₹18,000 per_person INR | **PASS** in packet (`budget_scope=per_person` 0.95) — **FAIL in UI**: shows "₹18,000" with no scope/total (FND-0344) |
| P3 | "from bangalore" → origin | **PASS** (0.9, span "from bangalore,") |
| P4 | Jaipur+Udaipur definite + night-split branch | **PARTIAL** — both candidates (conf 0.5, FACT) but `branch_options=[]`; UI destination shows Jaipur only (FND-0344) |
| P5 | group invites → public share | **FAIL (posture + auth)** — dogfood: invites 422 (guard on invitee email); beta: invites 200, tokens minted, but public `GET /api/v1/group/token/{t}` → **401** (FND-0330) |
| P6 | soft-hold honest without contract | **PASS** — 404 "Contract … not found for agency" |
| P7 | audit cost_source=estimated_default + warning | **PASS on provenance** — but the estimate is then used to assert a hard VIOLATION (FND-0338) |
| P8 | business-class rule named | **FAIL** — only the hotel-rate violation; 9h>6h business rule in policy-rules never evaluated (FND-0338) |
| P9 | override needs reason + audit | **PASS** — 200, `pending_second_approval: true` (dual-approval control) |
| P10 | PAN note fails closed 422 | **FAIL as predicted-shape, PASS on outcome** — `/run` is async: 200 accept, then the lead reached `blocked`; the PAN text is NOT in any persisted trip column (DB row scan) in either posture; Layer-2 did not block (spaced PAN) — note text survives only in the draft store (FND-0326 scope) |
| P11 | injection never moves budget | **PASS** — 60000 firm; "₹1" never won |
| P12 | "6 guys" → party absent | **CONFIRMED (predicted)** honest unknown (FND-0350 cheap win) |
| P13 | Goa definite; "next weekend" | **PASS/honest** — Goa definite; dates unknown (no relative-weekend parser) |
| P14 | ₹3,50,000 Indian grouping defect | **FALSIFIED (good)** — parses 350000 INR total |
| P15 | honeymoon purpose; occasion miss | **PASS on purpose/duration, RETRACTION NOTE** — the live packet carries `trip_purpose=honeymoon` and `trip_duration_days={7,7}`; the runner's digest allow-list used the wrong key names and initially hid them (FND-0331 was opened on that artifact and RETRACTED the same session with the live evidence). Occasion miss confirmed (FND-0349) |
| P16 | "flying out of delhi" → origin | **PASS** (0.92) |
| P17 | "2 of us" → party 2 | **PASS** |
| P18 | quotes basis labels; USD default | **PARTIAL** — `quote_ready:false` with honest `missing` (no recommended option for a blocked lead); money path never starts for blocked leads (FND-0342); currency fallback "USD" confirmed in code |
| P19 | compile → token → public page | **FAIL (honesty)** — compile 200 but `share_token:null`, `share_blocked_reason: simulated_inventory` (honest), and economics `optimized_take_rate_pct: 1240.0`, net $8,701 vs ₹3.5L budget, `is_feasibility_passed: true` (FND-0337) |
| P20 | ₹2.2 lakh → 220000 | **PASS** |
| P21 | solo → party 1 | **MISS** → absent (honest; FND-0350) |
| P22 | IN→JP registry miss disclosed | **FAIL** — identical "requires E_VISA" assertion for the registry MISS (JP) and the registry HIT (TH); no disclosure (FND-0339). Validity math PASS (4.7 months, urgent). |
| P23 | requirements abstain (VA-01) | **PASS** — "Visa radar abstains from a legal determination…" |
| P24 | [Tokyo, Kyoto] + Japan | **FAIL (headline)** — `destination_candidates=['Solo']` DEFINITE; japan/tokyo/kyoto dropped (FND-0329) |
| P25 | /run with email in note persists | **PASS** (both postures) |
| P26 | export carries personal fields | **FAIL** — `personal_data: {}`, `facts_summary: []` (FND-0336) |
| P27 | erasure scrubs nested + memory | **PARTIAL/FAIL** — dogfood: 503 (needs signing key — honest refusal); beta: 200 + certificate, email gone, but **name survives** and **memory profile survives**; standalone `/memory/forget` works (FND-0335) |
| P28 | BFF send 200 + token | **PASS** (beta) — `POST /api/followups/{id}/send` via the product → 200 + `/a/{token}` |
| P29 | public page 200; answers POST; asks updated | **PASS** — unauthenticated page 200; answers recorded (`origin_city=kolkata`, `authority=explicit_user`, `channel=ask_link`) |
| P30 | reassess does NOT consume answers | **CONFIRMED FAIL (as predicted)** — follow_ups unchanged, `origin_city` still None after reassess (FND-0328). The answer text does appear in the trip header display — one display-level reader, no pipeline reader |
| P31 | triage discloses lane; urgent | **PASS** — `is_urgent:true` 0.87, `source:"jev"`, routing SENIOR_AGENT_DISPATCH; confidence 0.28 low (honest); intent `general_inquiry` is weak for a passport-expiry panic (persona judgment, not registered) |
| P32 | inbound attaches; messages>0 | **FAIL** — inbound creates a NEW trip; messages 0 on both (FND-0334) |
| P33 | pre-departure honest | **PASS** — `reality_tier: deterministic_preview`, `provider_connected:false`, `missing_for_upgrade` named |
| P34 | party 3 + composition | **PASS** — `{adults:2, children:1}` |
| P35 | mandate REAL tier; CAS 409 | **PASS** — register 200 (REAL, "execution sim-tier" note), revoke 200, second revoke **409** |
| P36 | commission split preview only | **PASS** — `COMPUTED_PREVIEW`, `deterministic_preview`, `provider_connected:false` |
| P37 | accounting export basis-labelled | **UNREACHABLE/honest** — 409 "No persisted quote cost" (FND-0342) |
| P38 | money boundary | **PASS** — no charge/capture path reachable in any chain; mandates are consent records |
| P39 | family of 5 → 5 + kids | **PASS** — party 5, `{adults:2, children:3}`, ages [4,9,12] |
| P40 | after N2 [Kerala, Coorg] | **FAIL** — Kerala/Coorg never extracted in ANY pass (regions absent from gazetteer, FND-0329); after N4 `['Young']` DEFINITE |
| P41 | budget → 190000 with trail | **FAIL** — stays 150000 across N3/N4; no supersession trail surfaced |
| P42 | Coorg persists (no removal) | **MOOT** (never extracted); mobility "ground floor rooms only" captured, attribution blended (predicted) |
| P43 | asks survive reprocess | **NOT GRADED** — `/followups/generate` is the re-engagement copy generator, not an ask minter (no asks existed to survive); its copy had a template glitch ("your custom your destin…") |
| P44 | magic bytes / size cap | **PASS** — PNG 200 (`pending_review`), zip-as-png **415**, oversize **413** (cap enforced even before the stage gate); uploads at discovery stage **403** "Upload only allowed at proposal/booking stage" (stage rule works; `PATCH /trips/{id}/stage` → proposal unlocked it) |
| P45 | extraction honest | **FAIL** — `extracted_by: noop_extractor` with `overall_confidence 0.85`, `nationality: "US"` from a 1×1 PNG (FND-0333) |
| P46 | accept + signed URL | **PASS** — accepted; `/api/internal/documents/{id}/download?token=…&expires=` 900 s. **Duplicate upload → new document, no dedup flag** (folded into FND-0333 scope) |
| P47 | BFF parity | **CONFIRMED** — true BFF-deny (`{"error":"Not found"}`): dsr, visa-radar, corporate, customers/memory, accounting-export, analytics, financial-ops, supplier soft-hold, pre-departure, passenger-rights claims, group token; forwarded (`{"detail":"Trip not found"}`): quotes, reassess; mapped+200: followups, triage, trips (FND-0340) |

**Unpredicted, observed (registered):** the privacy guard refuses the Sens
accessibility lead AFTER the pipeline ran all stages — run `failed`, lead
lost, yet the packet with "wheelchair"/the traveler's name is retained in the
run ledger and the note in the draft store (FND-0326); group invites blocked
by the same guard in dogfood; an `ENCRYPTION_KEY` change bricks reads of
earlier trips with a 500 (FND-0327, UI "Workspace unavailable"); the UI shows
"1 pax" for a 2-traveler packet (FND-0343); the PlanningStageGate demands
budget+destination the packet already holds (FND-0332); unmarked "60k" →
USD (FND-0341); analytics totals are exactly 10,000/1,000 on a 45,944-trip
DB (FND-0345); loop-teardown errors recur (FND-0321 reopened); the guard's
remediation text names the wrong knob (FND-0347); a second send-ask mints a
question-less token (FND-0348).

## 3. Findings (registered FND-0326..0350; see `scripts/findings.py show`)

| FND | P | One line |
|-----|---|----------|
| 0326 | P0 | Privacy-guard boundary covers TripStore only — run ledger + drafts keep refused PII (both postures) |
| 0327 | P1 | `_decrypt_blob` on foreign-key token → ciphertext → `json.loads` 500; key rotation bricks reads |
| 0328 | P1 | AUD-06 part two: traveler answers recorded, never consumed by reassess |
| 0329 | P1 | 'Solo'/'Young' definite destinations; japan/tokyo/kyoto + kerala/coorg dropped (no region layer) |
| 0330 | P1 | Group share URL 401 for the invitee |
| 0331 | — | **RETRACTED** (runner key-name artifact; live facts carry purpose + duration) |
| 0332 | P1 | PlanningStageGate contradicts present facts (U11 confirmed) |
| 0333 | P1 | noop passport extractor fabricates nationality "US" @0.85; duplicates not flagged |
| 0334 | P1 | Inbound creates duplicate leads, writes no messages |
| 0335 | P1 | Art.17: name + CustomerMemoryProfile survive erasure (forget door works standalone) |
| 0336 | P1 | Art.15 export structurally empty |
| 0337 | P1 | Proposal compiler: 1240% take rate, $8.7k net vs ₹3.5L budget, feasibility "passed" |
| 0338 | P1 | Corporate audit: violation from an estimated baseline; class/duration rule unwired |
| 0339 | P1 | Visa radar invents E_VISA for unknown corridors, undisclosed |
| 0340 | P2 | BFF parity: 11 door families product-unreachable (T14 GDPR among them) |
| 0341 | P2 | Unmarked amounts default USD |
| 0342 | P2 | Quotes/accounting unreachable for blocked leads; USD fallback |
| 0343 | P2 | UI "1 pax" vs packet 2 |
| 0344 | P2 | Per-person scope lost in UI; multi-city collapsed in display |
| 0345 | P2 | Analytics totals are pagination caps |
| 0321 | P2 | (reopened) loop-teardown errors recur |
| 0347 | P3 | Guard message names the wrong knob |
| 0348 | P3 | Send-ask not idempotent |
| 0349 | P3 | Occasion before-date order; U4 inference absent |
| 0350 | P3 | Colloquial count nouns / solo |

## 4. Positives (for honesty)

- **Extraction core is strong on the mainstream shapes:** 12 people, per-person
  scope, "from X"/"flying out of X" origins, Indian digit grouping and lakh
  units, "2 of us", "2 adults and 1 child" with composition, "family of 5"
  with child ages — all PASS first time.
- **Injection demotion holds** (budget never moved to ₹1).
- **Honest tiers everywhere they were designed:** pre-departure bundle, commission
  split, mandates ("execution sim-tier"), proposal `share_blocked_reason:
  simulated_inventory`, visa trip-requirements abstain, soft-hold 404, accounting
  409, quotes `missing` list.
- **Controls that work:** mandate CAS revoke (409), dual-approval policy
  override, stage-gated uploads with magic-byte (415) and size (413)
  enforcement, signed expiring download URLs, `/memory/forget` certificate,
  Art.17 fail-closed without a signing key (503 with reason).
- **Ask loop is wired end-to-end through the product BFF** for the first time
  (send 200 → public page → answers recorded with provenance) — only the
  consumption inch is missing.
- **Money boundary held** in every chain exercised.

## 5. Visual evidence (all inspected)

| File | Shows |
|------|-------|
| `UI_trip_G_ask_loop.png` | **"1 pax"** on a 2-traveler packet; gate demands budget+destination the packet holds; answer text in header; garbled compose sentence |
| `UI_trip_A_group.png` | "12 pax · mid-Feb", **₹18,000** shown without per-person scope, destination **Jaipur** only, type/purpose "business", must-have "meeting room" |
| `UI_trip_K_documents.png` | Honest "Dates to confirm", travel-window ask, Ops tab present |
| `UI_trip_J_supersession.png`, `UI_trip_D_honeymoon_money.png` | **"Workspace unavailable — Internal Server Error"** (FND-0327 key-mismatch 500) |
| `UI_leads_table_sim4.png`, `UI_quotes_page.png` | Lead inbox with sim leads; quotes page (real read model, empty for blocked leads) |

## 6. Verdicts per door

| Door | Verdict |
|------|---------|
| A group/MICE | **FAIL→FIXED (2026-10-23 door wave)** — share link 401 was three stacked causes (middleware allowlist, FORCE-RLS GUC-less scan, twin proposal lookup); all fixed, live-verified OPEN ✓ (unauth share 200 + pay-share NOTIFIED_PAID); dogfood-blocks-invites is posture (DP-03a); UI scope/multi-city still queued (0344) |
| B corporate policy | **FAIL** — fabricated-baseline violation; class rule unwired; override control good |
| C adversarial | **PASS with scope note** — injection held; PAN not persisted on trip; draft/ledger scope → FND-0326 |
| D honeymoon → money | **FAIL** — compiler economics incoherent; quotes empty for blocked leads (purpose/duration are captured — FND-0331 retracted) |
| E visa | **FAIL** — 'Solo' destination; invented visa type; abstain + validity math good |
| F GDPR | **FAIL** — export empty; erasure leaves name + memory |
| G ask loop | **FAIL→OPEN ✓ (2026-10-23 door wave)** — full loop verified: send → unauth answers → auto-reassess consumed them (follow_ups=[], answered slots persisted explicit_user); UI gate/party defects remain (0332/0343) |
| H inbound | **FAIL** — duplicate lead, no message rows; triage + pre-departure honest |
| I money ops | **PASS** — mandates/CAS/commission/boundary all honest; analytics caps (P2) |
| J reprocess | **FAIL** — regions never extracted; 'Young' definite; budget supersession lost; page 500 (key) |
| K documents | **PARTIAL** — gates/caps/URLs good; extractor fabricates; no dedup |

## 7. Handoff

- **Fix-first queue:** FND-0326 (persistence boundary: ledger+drafts — owner
  posture + encryption scope), FND-0327 (decrypt discrimination + typed error),
  FND-0328 (consume answers in reassess/run), FND-0329 (leading-epithet guard + region layer + definite corroboration),
  FND-0330 (public group share), FND-0333 (noop extractor honesty), FND-0332
  (gate reads canonical unknowns), FND-0335/0336 (DSR completeness),
  FND-0338/0339 (honest policy/visa), FND-0334 (inbound link + message write).
- **Re-run anything:** `SIM_BACKEND_URL=http://127.0.0.1:8010 .venv/bin/python
  tools/sim4_runner.py --sim {A..K|P|all}`; beta lane with
  `SIM4_EVIDENCE_DIR=Docs/sims/assets/sim4/evidence_beta` and a backend started
  with `DATA_PRIVACY_MODE=beta ENCRYPTION_KEY=<fernet>`; wave-3 via
  `tools/sim4_wave3_probes.py`.
- **Data safety:** all seeds additive (new drafts/trips/profiles/mandates/docs);
  the only deletion was the GDPR sim's own synthetic profile via the canonical
  forget/erasure endpoints; no TRUNCATE/DELETE; `.env` untouched; the
  process-only `ENCRYPTION_KEY` used for the beta lane was never persisted —
  trips created in that lane are readable only by a process holding that key
  (this is FND-0327's point; they are synthetic sim rows).
