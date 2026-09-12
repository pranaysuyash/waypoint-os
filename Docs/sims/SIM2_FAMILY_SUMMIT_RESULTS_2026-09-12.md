# Sim #2 Results — "The Family Summit" (customer delegation, live run)

**Date:** 2026-09-12 · **Executor:** ZCode (computer-use via Playwright against
the real product at `localhost:3005`, backend `:8000`, `TRIPSTORE_BACKEND=sql`)
· **Design:** `Docs/sims/SIM2_CUSTOMER_DELEGATION_COUNCIL_DESIGN_2026-09-12.md`
· **Personas:** `Docs/sims/personas/SIM2_DELEGATION_PERSONAS_2026-09-12.md`
(bounded sim constructs — Priya/Arjun/Meera/Dev, verbatim scripts quoted
in-full below). Draft: `draft_b4117a661e95`.

**Verdict on the delegation capability: FAIL — Postpone.** 1 P0 regression +
7 P1 findings, every one of them in the multi-actor class the council
predicted, plus one P0-adjacent data-corruption class the council did NOT
predict (cross-voice field overwrites).

---

## 1. Flow executed (verbatim, all six notes)

All notes were appended into a single Customer Message thread (the realistic
"organizer forwards everything" pattern) and the run was re-processed after
each addition — testing IMP-01's reprocess path five times:

1. Priya's opening (japan, 2 couples, spring flexible, ₹3.5L total incl.
   flights, tokyo+kyoto+maybe osaka, cooking class).
2. + Arjun's contradiction (december/ski, scuba/okinawa, osaka nightlife,
   "budget whatever, we'll manage").
3. + Meera's constraints (jain no-onion-garlic, NO heights, quiet ryokan,
   10th anniversary april 14th, not a party hostel, kimono photos).
4. + Dev's compromise (±1 week for ₹40k+, trip must COVER april 14, 2
   separate double rooms, slow mid-week).
5. + the 10-line group-chat dump (all four voices interleaved).
6. + Priya's direct follow-up ("what's bookable within 3.5L, what does each
   person owe, meera's food thing keeps getting lost").

Run completed all stages (packet, validation, decision, strategy,
blocked_result) on every pass; final state **Blocked** on
`Travel Dates, Trip Purpose`.

## 2. Pass/fail against the design criteria

| # | Criterion | Verdict | Evidence |
|---|---|---|---|
| 1 | Party resolution (4 adults / 2 couples) | **PARTIAL** | `Party Size 4`, `Party Composition: Adults: 4` ✓; but "2 couples" never structured (no room-orientation), and party never changes across voices ✓ (stable) |
| 2 | Per-traveler constraint attribution | **FAIL (predicted)** | `Meal Preferences: jain` is group-unattributed — the packet cannot say it is Meera's, so "vegetarian food" joins group-wide Trip Priorities alongside Arjun's "adventure activities". No traveler entity exists at all. |
| 3 | Conflict surfacing (december-vs-spring, ryokan-vs-party) | **FAIL** | No ambiguity, no follow-up question, no advisor flag for either conflict. Arjun's "DECEMBER. skiing." vs Priya/Dev's april window never surfaces anywhere. |
| 4 | Budget integrity (₹3.5L total, no double-count) | **FAIL — worst finding** | After Note 2 (Arjun's number-free "budget whatever, we'll manage"), **Budget Scope flipped `total → per_night` at 95% confidence** while Min/Max stayed 350000 — i.e. ₹3.5L *per night*. Note 5 then flipped Budget Flexibility `soft → firm` (that one was correct — "3.5L MAX"). Cross-voice field overwrite with no provenance. |
| 5 | Follow-up quality (asks what a real agent would) | **FAIL** | Missing-fields list never mentions the room-count, anniversary-date, or season-conflict questions; the "Missing fields" line also silently mutated between runs (see F6). |
| 6 | No crashes / no fabrications | **FAIL (fabrications)** | See F2/F3 below — fabricated `Origin City: okinawa`, corrupted Constraints/Soft Preferences fields. No crash ✓ (that part holds). |

**Plus the P0:** the blocked lead **never persisted to the Lead Inbox.** After
all six processing passes: inbox search for `japan` / `organising` / the draft
id → **0 leads**. The lead exists only as `data/drafts/draft_b4117a661e95.json`.
This is the exact IMP-01 contract ("blocked runs persist incomplete leads via
save_processed_trip") failing in the browser-driven path — the 3,194 inbox
leads are all stale test rows. Registered as **FND-0272 (P0)**.

## 3. Findings (live-evidenced, in-run order)

**F1 (P1) — Cross-voice budget-scope overwrite.** Note 2 contains no number
and no per-night language; after it, `Budget Scope: per_night` (95%,
explicit_user) replaces Note 1's correct `total`. Quote math on this packet
would be ₹3.5L *per night*. Precedence across appended voices is
last-writer-wins with no authority comparison.

**F2 (P1) — Proposed destination extracted as Origin.** Arjun's "okinawa side
trip?" (a *destination proposal*) became `Origin City: okinawa` (80%) —
replacing the correct missing-state. Fabrication: no origin was ever stated
by anyone.

**F3 (P1) — Channel transcript leaks into packet fields.** After the chat
dump: `Constraints` = "onion and no garlic, cable cars, observation decks,
photo session if possible, **matter what**, heights" (fragment "matter what"
from "no matter what"), and `Soft Preferences` contains raw chat lines
including speaker labels: "[arjun]: fine but someone tell me why we're not
doing scuba [priya]: because 3". Packet fields must never contain channel
transcript fragments.

**F4 (P1) — Safety-critical constraint dropped.** Meera's "terrified of
heights, no cable cars, no observation decks" — stated in Note 3 AND repeated
in the dump ("remember NO HEIGHTS") — never appears in any field. Arjun's
skiing (chair lifts) and any observation-deck activity would have been
proposed to a traveler with acrophobia. (`Constraints` field only captures
fragments, post-corruption.)

**F5 (P1) — Anniversary date dropped twice.** "10th anniversary… april 14th"
(Meera) and "needs to COVER that date no matter what" (Dev) — repeated twice,
never captured; no date-anchored constraint exists. Trip Priorities even
absorbed "the 14th covered" as *preference prose* inside a corrupted field.

**F6 (P2) — Missing-fields list is unstable across runs.** Note 1 pass:
`Origin City, Travel Dates, Trip Purpose`; Note 2 pass: `Travel Dates, Trip
Purpose` (Origin "resolved" by the okinawa fabrication — the missing-list
improved because a wrong value appeared); later passes still show both
wrong-or-missing values without noting the conflict.

**F7 (P2) — Ambiguity "Raw:" quotes don't match the input.** The
Flights-Inclusiveness ambiguity shows `Raw: 5 lakhs total for everyone
including flights, that's my hard cap` — the note said **3.5** lakhs. The
raw-evidence snippet is corrupted (digit dropped), undermining the packet's
provenance story. Also: the ambiguity fired even though "INCLUDING flights"
is explicit — the D-02 detector should not fire on explicit inclusiveness.

**F8 (P2) — Additive destination from second voice not merged.** "maybe
osaka" (Priya) + "osaka nightlife is non-negotiable" (Arjun) — Osaka appears
in neither Destinations nor Ambiguities. Meanwhile "adventure activities"
(from Arjun) DID merge into Trip Priorities — merging works for priorities
but not destinations.

**Positives (for honesty):** Party Size/Composition stable at 4-adults across
all six passes (no drift); Jain meal captured; "adventure activities" +
"vegetarian food" merged into Trip Priorities; Budget Flexibility soft→firm
on "MAX" was correct; no crashes; IMP-01's reprocess path never produced
duplicate leads (idempotent, just… unpersisted, see F0/P0).

## 4. The P0 in context (IMP-01 regression)

IMP-01's shipped contract: a blocked run persists an incomplete lead
(`save_processed_trip`, status=incomplete) so leads never vanish. Today the
blocked run completed every stage **but no trip record exists** in the SQL
store under the test agency — the only artifact is the UI draft. Suspect
surface: the browser intake path may be skipping the ESCALATE persistence
branch that the API/tests exercise (tests pass; the UI path diverges). This
is precisely the verify-intent lesson: "tests green" ≠ "serving path
behaves".

## 5. Verdict

**Delegation capability: FAIL — Postpone.** The single-voice extraction wave
works; every failure is specifically multi-actor: attribution, precedence,
conflict, transcript contamination, and now lead persistence on the UI path.
The council's prediction held almost exactly — with the cross-voice overwrite
class (F1) as the unplanned discovery, and it is the most dangerous one.

## 6. Next actions

1. FND-0272 (P0): UI-path blocked-run persistence — reproduce via API vs UI,
   find the divergence, restore IMP-01 contract + regression test.
2. FND-0273 (P1): per-field source precedence for appended messages (scope/
   origin/ambiguity overwrites) — authority-aware merge, never
   last-writer-wins.
3. FND-0274 (P1): transcript-contamination guard — chat fragments must never
   enter packet fields (F3 evidence).
4. Per-traveler attribution primitive (IDEA-134) — design gate before Sim #2
   re-run.
5. F6/F7 (P2): unstable missing-fields list + corrupted ambiguity raw quotes
   + D-02 misfire on explicit inclusiveness.
