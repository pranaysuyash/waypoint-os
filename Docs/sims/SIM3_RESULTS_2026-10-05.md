# Sim #3 Results — "Four Doors" (four personas, four product doors, live run)

**Date:** 2026-10-05 · **Executor:** ZCode (API-driven via
`tools/sim3_runner.py` + Playwright screenshots against the real product,
backend `:8000`, frontend `:3005`, `TRIPSTORE_BACKEND=sql`, Postgres
`waypoint_os`, test agency `d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b`) ·
**Design:** `Docs/sims/SIM3_DESIGN_2026-10-05.md` · **Personas:**
`Docs/sims/personas/SIM3_PERSONAS_2026-10-05.md` (verbatim scripts, quoted
in full there) · **Evidence:** `Docs/sims/assets/sim3/` (per-sim JSON +
6 screenshots) · **Runner:** `tools/sim3_runner.py` (documented in
`tools/README.md`).

**Environment note (honest telemetry):** `/health` reported
`llm.available: false` for this session — every result below is the
DETERMINISTIC stack (regex/heuristic extractors, gates, services), which is
also the stack the Option 3 origin semantics live in. LLM-assisted stages
were not under test.

**Standing verdict: 4 doors opened, 4 different outcomes.** The ops chain
(door C) and the memory store (door B) are genuinely strong; the Hinglish
intake door (A) and the constraint/attribution door (D) fail in a NEW
fabrication class the Sim #2 council did not predict (Hindi words and human
names becoming "definite" destinations), and two launch-wave endpoints share
one crash. **12 findings registered: FND-0308..0319 (7×P1, 4×P2, 1×P3).**

---

## 1. What ran (verbatim scripts executed in full)

| Sim | Persona | Door | Steps executed |
|-----|---------|------|----------------|
| 3-A | Rahul Mehta (31, Hinglish VFR) | Intake `/run` via draft + reprocess | note 1 → run → blocked packet graded → note 2 appended via `PATCH /api/drafts/{id}` `customer_message` → re-run on same draft (T2 path) → packet re-graded |
| 3-B | Ananya Rao (29, return guest) | Memory `/api/v1/customers` | seed profile → durable lookup → leakage negative control → intake run with her email in-line → `hydrate-trip` display-only hydration → post-run re-lookup |
| 3-C | Vikram Shetty (45, disruption) | Inbound T6 + claims T10 + ghost concierge T11b | realistic inbound email probe (`inbound/parse`) → seed via `/run` → `flight_status_updates` PATCH (T11b trigger) → `/evaluate` → `/generate-claim` → disposition GET + 3 illegal probes + legal chain to CLOSED → messages read |
| 3-D | Col. Arvind Sen (72) & Kamala Sen (68), narrated by Priyanka | Constraints + ask loop T1 + confirmations T9 | intake run → packet graded → `/followups/{trip}/send` (ask mint) → public `/a/{token}` attempt → confirmations `/extract` + list |

Every run completed all pipeline stages (`packet, validation, decision,
strategy, blocked_result`); leads PERSISTED to the lead inbox (the trips
appear in the 100-lead planning table — IMP-01 holding, consistent with the
FND-0272 retraction).

## 2. Predictions vs outcomes (design doc P1–P17)

| # | Prediction | Outcome |
|---|-----------|---------|
| P1 | `bangalore se` → origin FACT 0.85 | **PASS** — `origin_city=Bangalore` 0.85 EXPLICIT_USER, evidence span "bangalore se" (both passes) |
| P2 | `jaipur side` no origin fabrication | **PASS** — Jaipur never became origin; bare-side stayed out (hypothesis path not even needed) |
| P3 | Hinglish VFR phrasing misses `family_visit` | **CONFIRMED FAIL (predicted)** — "mummy-papa ke saath" and even "family visit hi main purpose hai" (noun order) → `trip_purpose` unknown |
| P4 | `diwali`/`chhath` no occasion anchor | **CONFIRMED (predicted)** — no festival anchor exists (`_OCCASION_DATE` covers anniversary/birthday/honeymoon only) |
| P5 | Reprocess records festival shift w/ trail | **PARTIAL** — draft patch + re-run on same trip works (draft_id `draft_fe2bdd48bd6c`, trip `trip_be34bf6222ba`); decision history surface not yet graded (see FND-0309 for what the reprocess did to destinations) |
| P6 | Memory durable, scoped, null on stranger | **PASS** — profile survives processes; `wrong.customer@…` → `null`; agency-scoped store (commit `0c6efae4` path) |
| P7 | History-informed intake signal | **FAIL** — run path never touches memory: no returning-guest signal in packet; profile unchanged after the run; only the display-only `hydrate-trip` (E-D slot 2) surfaces memory (`memory_found: true`, 3 fields) |
| P8 | evaluate returns named framework + math | **PASS with defect** — eligible, US_DOT, $300/pax → $654 total, named reason … but see FND-0312 (generate-claim disagrees) |
| P9 | letter: airline pays traveler directly | **PASS** — "Please remit compensation directly to the affected passengers within 14 days" |
| P10 | disposition machine enforces transitions | **PASS 6/6** — illegal `SUBMITTED→TRAVELER_PAID` 409, backwards `→DRAFTED` 409, terminal `CLOSED→SUBMITTED` 409; legal `SUBMITTED→AIRLINE_PARTIAL→TRAVELER_PAID→CLOSED` clean history |
| P11 | ghost concierge via flight facts → drafts only | **PASS** — `overall_health: DISRUPTED`, `SEARCH_FALLBACK_FLIGHTS` CRITICAL + `DRAFT_EU261_CLAIM`, all `DRAFT_AWAITING_OPERATOR` |
| P12 | no payment initiation | **PASS** — disposition `outcome` is recorded-only by contract; no money path invoked anywhere |
| P13 | wheelchair/slow-pace captured | **PASS (greedy)** — `mobility_constraints` captured, but the span over-runs into the mother's clause (attribution blended, see FND-0308 context) |
| P14 | per-traveler attribution | **FAIL (predicted, Sim #2 F1 class)** — one blended string; no traveler entity |
| P15 | `45th anniversary on november 18th` anchor | **PASS** — `occasion: {type: anniversary, date: "november 18th"}` |
| P16 | ask loop end-to-end | **FAIL — wiring** — `/followups/{trip}/send` → 409 "Trip has no open follow-up questions"; source `decision.follow_up_questions` is empty despite blocking unknowns (FND-0313). UI per-field "Ask traveler" buttons and the Suggested Follow-up compose exist and ask the right things (screenshot `UI_packet_D_accessibility.png`) |
| P17 | dispatch honest when unconfigured | **UNREACHABLE** — blocked by P16's 409 before dispatch status could be observed |

## 3. Findings (registered, FND-0308..0319)

**FND-0308 (P1) — Hinglish words and human names become "definite"
destinations.** Pass 1 (Rahul): `destination_candidates = [Gaya, Din, Aur,
Haan, Varanasi, Add, Aas]` — Hindi function words ("din" = day, "aur" =
and, "haan" = yes) plus one real city swept in. Pass 2: `['Baad']` ("baad" =
after) with **`destination_status = definite` (0.8)**. Ananya: `[Rao, Sim,
Japan, Vietnam]` (surname + email fragment). Sens: `[Manage, Sen, Uses,
Kamala, Plan, Pace, Varanasi, Pure]` (the mother's name extracted as a
city). This is the Sim #3 headline defect: the destination tokenizer treats
any capitalized token as a place, and the status resolver then asserts
definiteness on garbage that would go straight into quote math.

**FND-0309 (P1) — reprocess clobbers candidates.** The note-2 reprocess
replaced the entire candidate list; Varanasi (stated, real: "varanasi add
karna chahta hoon") was LOST, surviving in neither pass-2 candidates nor
destination. Supersession has no salvage step for previously-real values.

**FND-0310 (P1) — `POST /api/v1/customers/remember` → 500 after successful
commit.** `InvalidRequestError: Could not refresh instance` at
`customer_memory.py:328` (`await db.refresh(profile_row)`), deterministic on
insert AND update; the row IS persisted (lookup 200 immediately after). The
canonical memory-write endpoint reports failure for every successful write.

**FND-0311 (P1) — same crash on `/api/trips/{id}/confirmations/extract`.**
`confirmation_service.py:363` (`await db.refresh(c)`) — identical signature.
Two launch-wave endpoints (T9/T10 wave; FND-0060 wave) share one
refresh-after-commit defect class → systemic async-session pattern, one fix
should cover both (and should sweep every `db.refresh` after commit in
services).

**FND-0312 (P1) — claims framework self-contradiction.** Identical inputs
(TG318, CANCELLED, 19 h, 2,400 km, 2 pax): `/evaluate` → `US_DOT`
($300/pax); `/generate-claim` → `EU261/2004`. BKK→BOM on a Thai carrier is
plausibly neither — but whichever is right, the two engines must agree; the
claim letter cites a regulation the eligibility engine didn't select.

**FND-0313 (P1) — T1 ask door unreachable.** `_open_questions` reads
`trip.decision.follow_up_questions` (`public_asks.py`); the pipeline leaves
it `[]` even with blocking unknowns (date_window, trip_purpose, party), so
`/followups/{trip}/send` 409s and the public `/a/{token}` loop can never be
entered from a live run. The UI already composes the right questions
(screenshot) — the decision→ask wiring is the missing inch.

**FND-0314 (P1) — party_size fabrication.** Sen note (2 travelers) →
`party_size 4`, rendered "4 pax" in the operator UI (screenshot); plausibly
the "45th" ordinal leaking. Vikram's booking note ("2 passengers") → "1
pax" default. Party drives per-person quote math — corruption here is
money-adjacent.

**FND-0315 (P2) — privacy-guard door inconsistency.** `inbound/parse` with
a plaintext `customer_contact` email fail-closes (R-15 dogfood matrix,
`privacy_guard.py:565`) → 500; the `/run` door persisted the same address
inside `raw_note`. Net: the T6 inbound door is dead in the default dev env
while the run door accepts equivalent data. Likely intended per the mode
matrix but behaviorally inconsistent across doors; needs a documented
decision or an encrypted-contact path for inbound.

**FND-0316 (P2) — JEV vs validation contradiction.** Packet metadata:
`semantic_ambiguity: PROCEED (0.87), destination/dates/party/budget all
clear` — same packet: 3 blocking unknowns, `STOP_NEEDS_REVIEW`,
`intake_completion` ESCALATED. Operators see two opposite epistemic verdicts
on one surface.

**FND-0317 (P2) — claim card unreachable in UI for blocked trips.** The
planning gate locks the decision tab ("Complete budget range, origin city,
and travel window…") — the ClaimDispositionCard (T10) renders there, so the
exact disruption trips that hold live claims can't show the claim surface
without first satisfying intake fields (screenshot
`UI_decision_C_claim_card.png`).

**FND-0318 (P2) — budget extraction gaps.** "$2400" (USD, Ananya) → budget
fields absent entirely; "₹45,000 se zyada nahi" (hard cap) →
`budget_flexibility soft` — mitigated by an honest ASSUMPTION entry
("Value defaulted by system business rules… Operator confirmation
recommended"), but the cap language is unrecognized. ₹ parsing itself is
solid (45,000 INR, scope=total 0.95, both sims).

**FND-0319 (P3) — ghost concierge cosmetic + message store empty.** Summary
"Flight TG318 (->)" drops the route; `/api/v1/trips/{id}/messages` returns
count 0 — no traveler-message ingest path exists in the default env (T6's
write side), so the disruption note never attached to the trip.

## 4. Positives (for honesty)

- **Origin Option 3 holds end-to-end** in the live pipeline: `se`=fact,
  `side` never fabricated an origin, deictic/compound guards unnecessary
  here but harmless (P1/P2 PASS).
- **Occasion anchor** fired exactly per regex contract on the Sens' note.
- **Memory durability + leakage control** (door B): durable across
  processes, agency-scoped, stranger lookup `null`, display-only hydration
  with 3 labeled fields — the FND-0060 store works.
- **Disposition state machine: 6/6 probes correct** including three 409
  rejections and a clean terminal state.
- **Claim letter wording** is the corrected T10 form (airline → traveler
  directly).
- **Ghost concierge** produced drafts only, honest statuses, no sends.
- **Leads persist** (Sim #2's P0 class stays dead).
- **Assumption honesty:** the soft-budget default was flagged as an
  assumption with operator-confirm guidance rather than asserted.
- **Money boundary:** no payment initiation surface was reachable from any
  chain exercised.

## 5. Visual evidence (all inspected, none blank)

| File | Shows |
|------|-------|
| `UI_packet_A_hinglish.png` | Rahul's lead: honest missing-fields worklist (travel window), per-field Ask-traveler buttons, suggested follow-up compose |
| `UI_packet_D_accessibility.png` | Sens lead: **"4 pax"** corruption live in the header (FND-0314), origin+dates correctly demanded |
| `UI_decision_C_claim_card.png` | Vikram's decision tab gated by the planning gate — claim surface hidden (FND-0317) |
| `UI_leads_table.png` | Lead inbox table: sim trips among 100 persisted leads |
| `UI_inbox_feed.png`, `UI_agency_overview.png` | T6 inbox feed + agency overview context |

## 6. Verdicts per door

| Door | Verdict |
|------|---------|
| A — Hinglish intake | **FAIL** — origin semantics strong, destination extraction fabricates (FND-0308/0309), VFR/festival blind (predicted) |
| B — memory | **PARTIAL** — store excellent; `remember` 500 (FND-0310); intake not history-informed (P7) |
| C — disruption ops | **PASS with defects** — chain works end-to-end honestly; framework disagreement (FND-0312), message ingest missing (FND-0315/0319), UI gate hides claims (FND-0317) |
| D — constraints + asks | **FAIL** — occasion/mobility captured; party corrupted (FND-0314), attribution blended (predicted), T1 unreachable (FND-0313), confirm-extract 500 (FND-0311) |

## 7. Handoff

- **Fix-first queue (suggested order):** FND-0311 (one root cause covers
  0310), FND-0313 (wire decision.follow_up_questions → unblocks T1
  end-to-end), FND-0308 (destination tokenizer stoplist + status gate),
  FND-0314 (party extraction), FND-0312 (single framework authority).
- **Re-run anything:** `tools/sim3_runner.py --sim {A|B|C|D|all}` then
  `--shots` (see `tools/README.md`). Verbatim persona scripts live in
  `tools/sim3_sims.py` (`VOICES`) and the personas doc.
- **Not yet graded:** T2 decision-history UI (trail exists via draft, panel
  not asserted), confirmation grader output quality (extract 500 blocked
  it), ask-loop traveler answer round-trip (blocked by FND-0308…0313 chain
  upstream).
- **Data safety:** all seeds additive (new drafts/trips/profiles only);
  no truncation/deletes; test agency untouched otherwise.
