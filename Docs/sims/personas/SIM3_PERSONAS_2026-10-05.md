# Sim #3 Personas — "Four Doors" suite (bounded simulation constructs)

**Project:** Waypoint OS (travel_agency_agent) — project-specific personas for
Sim #3. **These are NOT canonical personas** and must not be added to the
canonical persona repository (`Understanding_Personas_sept6`). Construct
precedent: the Sim #2 delegation (Priya/Arjun/Meera/Dev,
`Docs/sims/personas/SIM2_DELEGATION_PERSONAS_2026-09-12.md`, committed
constructs) and the Sim #1 Tool-Taster hobbyist.

**Purpose:** four single-party sims, each through a different product door
the Sim #2 family summit never opened:

| Sim | Door (use case class) | Persona(s) | New surfaces exercised |
|-----|----------------------|------------|------------------------|
| 3-A | Hinglish VFR intake — origin semantics, purpose, occasion | Rahul Mehta (31) | Origin Option 3 (`se`=fact / `side`=hypothesis), family_visit purpose, occasion anchors, T2 supersession via reprocess |
| 3-B | Repeat-guest memory — durable profiles, history-informed intake, leakage control | Ananya Rao (29) | FND-0060 durable agency-scoped customer memory (`/api/v1/customers`), region_affinity, cross-customer negative control |
| 3-C | Mid-trip disruption — claims + honest ops | Vikram Shetty (45) + operator | T6 inbound message ingestion, T10 claim engine + 8-state disposition, T11b ghost concierge (DRAFT_AWAITING_OPERATOR), money boundary |
| 3-D | Accessibility duo — constraints + the ask loop | Col. Arvind Sen (72), Kamala Sen (68), narrator-daughter Priyanka Sen | Mobility/medical constraint capture, per-traveler attribution (Sim #2 F4/F1 regression), T1 ask-traveler loop (`/a/{token}`), T9 confirmation grader |

All personas are fictional. Verbatim scripts are quoted in full below and are
the ONLY text submitted — no paraphrase, no cleanup — per the Sim #2
honest-input convention.

---

## SIM3-A — Rahul Mehta, 31, software engineer, Bengaluru

- **Definition:** burned-out techie planning a Diwali visit home. Writes in
  natural code-switched Hinglish — the way real Indian customers actually
  type. Single voice (no delegation noise this time; the variable under test
  is *language*, not multi-actor merge).
- **Mandate in the sim:** exercise the owner-ratified origin Option 3 and the
  VFR/occasion extractors against genuinely colloquial input.
- **Engineered cues (each maps to a repo fact):**
  1. `bangalore se hoon` — explicit "se" → origin FACT 0.85
     (`src/intake/extractors.py` postposition branch, Option 3 comment).
  2. `jaipur side jaana hai` — bare "side" → directional, must NOT fabricate
     a Jaipur origin; Jaipur should surface as destination intent or a
     hypothesis, never a 0.85 origin fact.
  3. `ghar jaana hai` + `mummy-papa ke saath` — VFR intent in Hinglish; the
     `family_visit` regex (extractors.py:2556) only fires on
     `visit|see|meet + family|parents…` — PREDICTED MISS on pure-Hinglish
     phrasing (the finding, not the bug).
  4. `diwali` — festival timing; occasion anchors only cover
     `anniversary|birthday|honeymoon` + month-date (extractors.py:2663) —
     PREDICTED MISS on festival anchors.
  5. `₹45,000 se zyada nahi` — Hinglish budget with a Devanagari-free rupee
     figure; budget_scope should be total, flexibility firm.
  6. Follow-up message shifts the festival (`diwali nahi, chhath ke baad`) —
     reprocess path: does the supersession trail (T2) record the reason?
- **Never says:** an English "visit family" phrase in message 1 (that phrasing
  is deliberately held back for message 2, to isolate the Hinglish-only
  behavior in pass 1).
- **Success signals:** origin=Bangalore fact, no Jaipur-origin fabrication,
  budget total/firm intact, per-traveler narrator ("main") not expanded to a
  group, follow-up recorded with provenance.

**Verbatim note 1 (lead-opening, New Inquiry):**
> bhai bohot ho gaya cube ki life. main bangalore se hoon, diwali pe ghar
> jaana hai — jaipur side, mummy-papa ke saath 4 din. aur haan unke liye ek
> chhota sa varanasi add karna chahta hoon, 2 din. budget: ₹45,000 se zyada
> nahi total, flights included. dates flexible hain diwali ke aas paas.

**Verbatim note 2 (follow-up, festival shift):**
> arre ek correction — diwali nahi, chhath ke baad karte hain trip, around
> nov last week. family visit hi main purpose hai, mummy-papa ko hi milna
> hai. baat same hai warna.

## SIM3-B — Ananya Rao, 29, product designer

- **Definition:** the repeat guest the memory loop (E-10, FND-0060 closure)
  was built for. Her durable profile is seeded FIRST via the canonical
  `/api/v1/customers` router, then a fresh intake note references history
  obliquely — testing whether the pipeline is history-informed, not
  history-ignorant.
- **Email:** `ananya.rao.sim3@waypointtest.dev` (dedicated sim address; the
  negative control is any OTHER name/email returning `null` from the same
  lookup within the same agency).
- **Seeded profile facts:** loves traditional stays (ryokan-equivalent),
  strict vegetarian, window-seat flights, past trip Japan/Kyoto spring 2026,
  region_affinity: east_asia, pace: unhurried.
- **Mandate in the sim:** prove memory is (a) durable across processes,
  (b) agency-scoped, (c) reflected in intake, (d) not leaked to other
  customers.
- **Success signals:** profile round-trips through the SQL store; the new run
  surfaces her preference inheritance (or at minimum the pipeline flags her
  as a returning guest); a lookup for `wrong.customer@waypointtest.dev`
  returns null; her new-trip facts are upserted without clobbering seeded
  history.

**Verbatim note (intake with her email in-line):**
> hi — ananya here (ananya.rao.sim3@waypointtest.dev). you planned japan for
> me last year and it was genuinely perfect. i want something with the same
> feeling but vietnam this time — 10 days in march, 2 people, around $2400
> excluding international flights. same kind of quiet heritage stays please.

## SIM3-C — Vikram Shetty, 45, sales director (traveler) + the operator seat

- **Definition:** mid-trip disruption. His voice arrives through the
  *inbound message* door (T6), not the intake form — the realistic
  "customer emails from the airport" path. The operator (advisor seat) then
  works the claim desk.
- **Scenario state (seeded additively):** one confirmed trip for Vikram,
  Bangkok → Mumbai return, 2 passengers, booking ref `SIM3-WP7K2M`.
- **Mandate in the sim:** drive the full honest-ops chain — inbound message →
  trip attachment → statutory evaluation → claim letter → disposition state
  machine → ghost concierge draft — and hold the money boundary (the system
  never moves money; the airline pays the traveler directly).
- **Success signals:** message ingested and attached to the right trip;
  evaluation returns a named framework (EU261/UK261/US_DOT) with per-pax
  math; disposition transitions follow the ALLOWED_TRANSITIONS table
  (`spine_api/services/claim_disposition.py:31`) and REJECT illegal jumps
  (e.g. DRAFTED→AIRLINE_ACCEPTED); ghost concierge produces a
  DRAFT_AWAITING_OPERATOR draft (never sends); no payment initiation of any
  kind.

**Verbatim inbound message (from the airport):**
> hi, vikram shetty here — you booked our bangkok trip (booking SIM3-WP7K2M).
> our flight TG318 bkk to bom yesterday got cancelled at the gate, 2 of us
> travelling. airline put us on a flight 19 hours later, no hotel, no meal
> voucher. this can't be right? what are our options, what is the airline
> supposed to give us?

## SIM3-D — The Sens: Col. Arvind Sen (72), Kamala Sen (68), narrated by daughter Priyanka

- **Definition:** an accessibility-heavy couple's pilgrimage, booked by their
  daughter. Third-person narrative (party is the parents, booker is the
  daughter) plus hard per-traveler constraints that must be ATTRIBUTED, not
  blended — the Sim #2 finding class (group-wide misattribution), now on
  medical/safety data.
- **Mandate in the sim:** constraint capture with attribution + the full
  ask-traveler loop end-to-end in the browser (first live sim of the T1
  surface) + the confirmation grader.
- **Engineered cues:**
  1. `wheelchair` (father) — mobility regex (extractors.py, mobility branch).
  2. `knee trouble, slow pace` (mother) — mobility/pace, DIFFERENT traveler.
  3. `step-free access` — accommodation constraint.
  4. `45th anniversary on november 18th` — occasion anchor with the
     month-date shape the regex expects.
  5. `pure veg` — meal constraint.
- **Success signals:** both mobility constraints survive (Sim #2 F4 analog —
  a dropped safety constraint is an automatic fail); anniversary anchor
  present with the date; asks mint a signed token, the public `/a/{token}`
  page renders and accepts answers, answers flow back onto the trip;
  confirmation grading runs honestly on a confirmation message.

**Verbatim note 1 (New Inquiry, from Priyanka):**
> hello, i'm booking for my parents — they don't use apps much so i manage
> everything. col. arvind sen, 72, uses a wheelchair and needs step-free
> access everywhere; my mother kamala sen, 68, has knee trouble so please
> plan a slow pace for her. they want varanasi for their 45th anniversary on
> november 18th, 3 nights, pure veg meals only. budget around ₹90,000 total.
> i can share exact travel dates once you confirm ghats access is doable for
> a wheelchair.

**Verbatim answers to the ask page (submitted as the traveler):**
> dates: arriving nov 16 evening, leaving nov 19 morning. room: one accessible
> double room, ground floor preferred. extra: please book a boat that has
> handrails, my mother is nervous on water.
