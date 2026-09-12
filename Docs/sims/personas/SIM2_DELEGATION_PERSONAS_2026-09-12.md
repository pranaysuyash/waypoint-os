# Sim #2 Personas — "The Family Summit" delegation (bounded simulation constructs)

**Project:** Waypoint OS (travel_agency_agent) — project-specific personas for
Sim #2. **These are NOT canonical personas** and must not be added to the
canonical repository (`Understanding_Personas_sept6`), which intentionally
contains no consumer travelers. Provenance: Sim #2 council decision
(`Docs/sims/SIM2_CUSTOMER_DELEGATION_COUNCIL_DESIGN_2026-09-12.md`, committed
`1f71657`); construct precedent: the Tool-Taster hobbyist persona (Sim #1).
Canonical lens personas used by the council are documented separately in that
decision (PER-0442/0465/0477/0478/1141/0924).

**Purpose:** drive the real Waypoint OS intake flow via computer-use with a
multi-voice customer delegation, and grade the product's behavior against
business-surface criteria (identity resolution, per-traveler constraint
attribution, conflict surfacing, budget integrity, follow-up quality, no
fabrications).

**The delegation:** four adults, two couples, one Japan trip, negotiated
asynchronously. Priya is the channel-of-record (everything routes through
her); the other three speak in contradictory side-notes. The group-chat dump
interleaves all four voices into one messy paste.

---

## P1 — Priya Raghavan (organizer / booker)

- **Definition:** the group's channel-of-record and the only person who will
  ever touch the booking. Practical, list-making, budget-keeping.
- **Mandate in the sim:** open the lead, hold the ₹3.5L TOTAL hard cap,
  convert the group's chaos into "so what do we each owe."
- **Hard constraints:** total budget ₹3,50,000 (all-in, flights included —
  she says so explicitly once).
- **Soft preferences:** spring/cherry-blossom timing; one cultural cooking
  class for the group.
- **Voice:** structured, slightly weary, uses lists and total amounts,
  references what others said second-hand.
- **Never says:** any dietary/height/anniversary constraint (those belong to
  Meera's notes — testing whether the pipeline merges cross-voice facts).
- **Success signal the sim looks for:** pipeline treats her as the single
  booker/contact; her ₹3.5L TOTAL is not doubled-counted with anyone's
  per-person number.

**Verbatim note 1 (lead-opening, typed into New Inquiry):**
> hi! i'm organising a japan trip for me and 3 friends — 2 couples. we're
> thinking spring next year for cherry blossoms but dates are flexible.
> budget is 3.5 lakhs total for everyone INCLUDING flights, that's my hard
> cap. we want to do tokyo + kyoto, maybe osaka. one cooking class somewhere
> would be amazing. everyone's sending me their own requests so i'll forward
> them as they come 😅

## P2 — Arjun Mehta (adventure friend)

- **Definition:** high-energy pusher of activities; treats the trip as a
  story to tell. Price-insensitive with other people's money.
- **Mandate in the sim:** inject contradictions — season conflict (December
  vs spring), pace conflict (packed itinerary), cost pressure (scuba,
  nightlife).
- **Hard constraints:** none (that's the conflict).
- **Soft preferences:** scuba day, nightlife/Osaka, "pack the schedule".
- **Voice:** hype, superlatives, dismissive of "boring" options, uses slang.
- **Contradictions injected:** wants December (cheaper + skiing) vs Priya's
  spring; wants to ADD cost vs Priya's hard cap.
- **Success signal:** his December-vs-spring contradiction surfaces as a
  follow-up question or advisor-visible flag, not silently resolved by
  last-writer-wins.

**Verbatim note 2 (contradicting voice-note):**
> yo it's arjun — priya's forwarding this. honestly spring is overrated and
> everyone goes. december = cheaper flights AND we can ski in hakuba. also we
> NEED a scuba day (okinawa side trip?) and osaka nightlife is non-negotiable,
> dotonbori till 3am. let's pack the schedule, we can sleep when we're dead.
> budget whatever, we'll manage.

## P3 — Meera Iyer (anniversary, dietary, fear of heights)

- **Definition:** traveling with her husband Dev for their 10th anniversary.
  The constraint-heavy voice.
- **Mandate in the sim:** inject per-traveler constraints that must NOT be
  applied group-wide (Jain food is HERS; the fear of heights is HERS) — the
  core per-traveler-attribution test.
- **Hard constraints:** Jain food (strict — no onion/garlic), absolutely no
  heights (no cable cars, no observation decks, no heli tours), quiet
  lodging (ryokan, not party hostel).
- **Soft preferences:** anniversary dinner on the actual date (April 14th),
  kimono photo session.
- **Voice:** polite, specific, occasionally anxious; states constraints as
  personal ("I can't"), which the pipeline must not generalize to the group.
- **Success signal:** her constraints survive to the packet with HER
  attribution (expected FAIL — per-traveler attribution is not modeled; the
  finding is the objective), and the no-heights constraint kills Arjun's
  observation-deck/ski-lift ideas in any advisor-facing output.

**Verbatim note 3 (constraints voice-note):**
> hello, meera here (arjun's forwarding for me too). a few important things —
> i'm jain, so strictly no onion and no garlic, i'll need jain or at least
> pure veg meals everywhere. i'm also terrified of heights so please no
> cable cars, no observation decks, nothing like that. we'd love a quiet
> ryokan for a couple of nights — it's our 10th anniversary on the trip
> (april 14th), so a nice anniversary dinner that day would mean a lot. and
> definitely NOT a party hostel 😄 please keep a kimono photo session if
> possible.

## P4 — Dev Iyer (peacemaker, date-flexible)

- **Definition:** Meera's husband; the compromiser. His function is to
  introduce a trade (dates for price) and contradict Arjun on pace.
- **Mandate in the sim:** inject the dates-for-savings trade and the
  two-rooms-vs-one-group-booking wrinkle; soften Arjun's pace.
- **Hard constraints:** none beyond Meera's (he inherits hers).
- **Soft preferences:** will shift dates ±1 week to save ~₹40k; wants 2
  twin/double rooms (not a shared hostel room); a slower middle week.
- **Voice:** measured, compromising, quantifies trades.
- **Contradictions injected:** contradicts Arjun's "pack the schedule";
  his ±1 week flexibility collides with Priya's cherry-blossom window AND
  Meera's April-14 anniversary date — a three-way date constraint that only
  survives with proper attribution.
- **Success signal:** the ±1-week flexibility attaches to the group dates
  WITHOUT wiping the April-14 anniversary constraint.

**Verbatim note 4 (compromise voice-note):**
> hi, dev here. quick one — we can shift the dates by a week either side if
> it saves meaningful money, say 40k or more; meera's anniversary is april 14
> so the trip needs to COVER that date no matter what. also please book 2
> separate double rooms, we're not doing one big shared room (sorry arjun 😄).
> and maybe don't pack every single day — one slow mid-week would be nice.

## The group-chat dump (note 5 — interleaved chaos)

**Verbatim (pasted as ONE message):**
> [priya]: ok updates — total is still 3.5L MAX, don't make me the bad cop
> [arjun]: DECEMBER. skiing. just saying
> [meera]: i really can't do cold-weather stuff, and remember NO HEIGHTS. also jain food, it's in my earlier msg
> [dev]: april works for us, we just want the 14th covered
> [arjun]: fine but someone tell me why we're not doing scuba
> [priya]: because 3.5L, arjun
> [meera]: a quiet dinner on the 14th please, that's all i'm asking
> [dev]: 2 rooms, twin or double, sorted?
> [arjun]: osaka nightlife tho
> [priya]: can someone just tell me what the plan is and what each of us owes??

## Priya's follow-up (note 6 — post-acknowledgement pressure)

**Verbatim:**
> ok so what's the plan?? what's bookable within 3.5L, what dates are we
> looking at, and what does each person owe? also did everyone's requests
> actually get noted?? meera's food thing keeps getting lost in the group 😤

---

## Expected pipeline behaviors (repo-fact predictions, for grading contrast)

- Party resolution to **4 adults / 2 couples** with cross-voice merge:
  partially covered (party_composition is first-class), merge-across-notes
  untested.
- Meera's Jain/no-heights: extraction tokens exist (vegetarian/allergy/
  mobility hits verified in `src/intake/`), but **group-wide misattribution
  is the predicted failure** ("we are vegetarian").
- April-14 anniversary: `anniversary` exists in decision.py; the
  three-way date constraint (spring window ∩ ±1 week ∪ covers Apr 14) is
  predicted to collapse.
- ₹3.5L total + "we'll manage" (Arjun) + ₹40k trade (Dev): budget_scope
  per-person vs total is fixture-covered; three-voice budget noise is not.
- Delegation/approval flow (what each person owes): not modeled — the
  finding, not a bug.

## Grading rubric anchor

Criteria and verdicts live in the results doc
(`SIM2_FAMILY_SUMMIT_RESULTS_2026-09-12.md`): each pass/fail tied to business
surfaces (packet fields, follow-up questions, quote/lead state), zero credit
for cosmetic extraction, all findings registered.
