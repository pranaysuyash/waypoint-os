# Scenario Analysis: What is NB02 Actually For?

## First Principles: What Problem Are We Solving?

A boutique travel agency gets a lead. The agency owner jots down messy, partial notes. The question is:

**"What does the agent need to ask the traveler next, and in what order, to make this trip bookable?"**

That is the ONLY job of Notebook 02. Everything else — blockers, contradictions, confidence scores — is just machinery to answer that question.

The real test is not "does the code run." It's: **given a real messy agency note, does the system produce the right next action?**

---

## The Core Insight

The system is a **triage engine**. Like a nurse in an ER:
1. What do we know? (facts from notes)
2. What's critical and missing? (hard blockers)
3. What's contradictory? (contradictions)
4. Can we proceed safely, or do we need more info? (decision state)

The output is NOT an itinerary. It's: **stop, ask, draft, or present.**

---

## Real-World Scenarios

### Scenario 1: "The Vague Lead" — Almost Nothing Known
```
Agency note: "Someone called, wants to go international, big family, 
maybe around March, said budget is fine, will call back."
```

**What's actually known:**
- Trip scope: international (vague)
- Travelers: "big family" — count unknown, composition unknown
- Dates: "maybe March" — no window
- Budget: "is fine" — meaningless
- Destination: completely unknown
- Origin: completely unknown

**What the system should decide:** `ASK_FOLLOWUP` with questions ordered:
1. How many people, and who? (children? elderly? — this changes EVERYTHING)
2. Where are you departing from?
3. Which countries are you considering?
4. What dates exactly?
5. What does "budget is fine" actually mean in numbers?

**What would go wrong if the system fails:** The agent calls the traveler and asks about hotels before knowing if it's 3 people or 15. Wastes the call.

**What the system must NOT do:** Proceed to internal draft with a guess. A guess on family composition leads to completely wrong sourcing.

---

### Scenario 2: "The Confused Family" — Contradictory Inputs
```
Note from husband (envelope 1): "Singapore, 5 nights, March 15-20, 2 adults, 120k"
Note from wife (envelope 2): "Thailand would be better, April 1-6, 2 adults + baby, 200k"
```

**What the system should detect:**
- Destination contradiction: Singapore vs Thailand → ASK_FOLLOWUP
- Date contradiction: March vs April → **STOP_NEEDS_REVIEW** (critical per policy)
- Budget contradiction: 120k vs 200k → would be BRANCH_OPTIONS
- Traveler count conflict: 2 vs 3 (baby unknown to husband)

**What the system should decide:** `STOP_NEEDS_REVIEW` because date contradiction is critical. The agent should NOT call until the couple agrees on dates.

**What would go wrong if the system fails:** The agent calls and presents a Singapore March 15 itinerary to a wife who wants Thailand in April. The agency looks incompetent.

**The deeper insight:** This is not a data problem. It's a human problem. The system's job is to say "don't call yet — they haven't agreed with each other." That is the actual value.

---

### Scenario 3: "The Dreamer" — Luxury Wants, Budget Reality
```
Note: "Family of 4 from Bangalore, wants 5-star resort in Maldives, 
7 nights, they said 1.5 lakh total."
```

**What's known:**
- Origin: Bangalore ✓
- Travelers: 4 (composition unknown but count known) ✓
- Destination: Maldives ✓
- Duration: 7 nights ✓
- Hotel: 5-star resort
- Budget: 1.5L total = 37.5k/person

**What the system should detect:**
- Budget vs hotel contradiction: "5-star Maldives" vs "37.5k/person" → ADVISORY
- 1.5L for 4 people in Maldives is backpacker tier, but they want 5-star

**What the system should decide:** `PROCEED_INTERNAL_DRAFT` (hard blockers filled, but budget/hotel contradiction needs resolving). The agent should call with questions like: "We found beautiful options, but your budget would get 3-star. Would you prefer to adjust the hotel or the budget?"

**What would go wrong:** The system either (a) drafts a 3-star hotel and the traveler feels insulted, or (b) drafts a 5-star at 6L and the traveler feels ripped off. The right move is to ask about the tension explicitly.

---

### Scenario 4: "The Ready-to-Buy" — Everything Known
```
Note: "Confirmed — Sharma family, 2 adults + 1 toddler (2 years), 
Bangalore → Singapore, March 15-22, 5-star Orchard Hotel, 
budget 4L confirmed, payment ready, passport details in CRM."
```

**What the system should decide:** `PROCEED_TRAVELER_SAFE`. Hard blockers filled. No contradictions. High confidence.

**But also:** The system should recognize the traveler type = mixed_age_family (toddler present) and the agent should be thinking about:
- Flight timing (avoid red-eye with toddler)
- Hotel crib availability
- Pacing (toddlers nap)

These are NOT blockers. They are risk flags for the NEXT notebook (session strategy). NB02's job is just: "yes, proceed."

---

### Scenario 5: "The WhatsApp Dump" — Unstructured Chaos
```
WhatsApp from agency owner: "ok so this family from Chennai, 3 of them I think, 
want to go somewhere with beaches, kids are young so nothing too adventurous, 
husband said they have around 2 lakhs, wife mentioned they can stretch if it's 
good, dates flexible around April-May, they've been to Goa already so don't suggest 
that, maybe Andaman or Sri Lanka?"
```

**What the system should extract as facts:**
- Origin: Chennai ✓
- Destination: "Andaman or Sri Lanka" — two options, not decided
- Travelers: 3, "kids are young" → parents + young kids
- Budget: "around 2 lakhs" with stretch possibility
- Dates: "April-May" — window known but not exact
- Constraints: "don't suggest Goa", "nothing too adventurous"

**What the system should detect:**
- Destination ambiguity (not a contradiction — they're open to both)
- Budget range exists but soft ("can stretch")
- Soft blockers: specific destination, exact dates

**What the system should decide:** `ASK_FOLLOWUP` or `PROCEED_INTERNAL_DRAFT` depending on whether the system considers "Andaman or Sri Lanka" as a destination being filled or still ambiguous.

**The key insight:** The system must distinguish between "they haven't decided yet" (branch) and "they don't know at all" (ask).

---

### Scenario 6: "The CRM Return" — Old Data, New Context
```
CRM has: "Kumar family, Bangalore, 2 adults, budget 2L, international"
New note: "They called again, now it's 4 people, want Japan specifically, 
dates are locked — first week of May, they saved up so budget is now 5L"
```

**What the system should do:**
- Facts from new note override old CRM data (higher authority from explicit_user vs imported_structured)
- Detect: traveler count changed (2 → 4), budget changed (2L → 5L), destination narrowed (international → Japan)
- All discovery hard blockers filled
- Decision: `PROCEED_TRAVELER_SAFE`

**What would go wrong:** If the system uses old CRM data (imported_structured) instead of the new explicit_user note. The authority hierarchy exists for exactly this reason.

---

### Scenario 7: "The Partial Booking" — Stage 2/3/4 Progression
```
Shortlist stage packet: 
- Origin: Bangalore ✓, Destination: Singapore ✓, Dates: March 15-22 ✓
- Travelers: 3 ✓, Selected destinations: ["Singapore", "Malaysia"]
- But: selected_itinerary NOT chosen yet
```

**What the system should decide at proposal stage:** `ASK_FOLLOWUP` — missing selected_itinerary.

**The question generated:** "Which itinerary option do you prefer?"

**What the system should NOT do:** Proceed to booking when the traveler hasn't even chosen between Singapore and Malaysia.

---

### Scenario 8: "The Elderly Pilgrimage" — High-Risk Traveler Profile
```
Note: "4 elderly people from Varanasi, want to do Char Dham Yatra, 
budget 1 lakh, September dates, all have medical conditions"
```

**What the system should detect:**
- All 4 hard blockers filled ✓
- Traveler type: elderly group → HIGH RISK
- Medical conditions flagged
- Budget: 25k/person for Char Dham is tight
- Destination: Char Dham (Uttrakhand) — domestic

**What the system should decide:** `PROCEED_TRAVELER_SAFE` on the blocker logic, but the session strategy (NB03) must flag:
- Medical facility proximity is critical
- Physical fitness for temple visits
- Emergency contact requirements

**The insight:** NB02 says "proceed" because the MVB is satisfied. But "proceed safely" means different things for different traveler types. The MVB should potentially have medical constraints as a hard blocker for elderly pilgrimages. This is a GAP in the current MVB design.

---

### Scenario 9: "The Corporate Group" — Non-Standard Trip
```
Note: "IT company from Bangalore, 25 people, team offsite, 
3 nights, Goa, budget 5L per person, December dates"
```

**What the system should detect:**
- All blockers filled ✓
- Traveler type: corporate (not in current traveler types!)
- Budget: 5L/person × 25 = 1.25Cr → ultra_luxury
- 25 people is a massive group — logistics complexity

**Gap discovered:** The current MVB has no "corporate" handling. The traveler_type enum in NB01 includes CORPORATE but the MVB doesn't have corporate-specific blockers like:
- Venue booking confirmation
- Group flight block booking
- Corporate billing terms

**Insight:** The MVB is designed for family leisure trips. Corporate/group trips need different blockers.

---

### Scenario 10: "The Last-Minute Booker" — Urgency Over Perfection
```
Note: "Need to book for this weekend! 2 adults, Bangalore → Dubai, 
4 nights, any hotel, budget 3L, flying Friday"
```

**What the system should detect:**
- All hard blockers filled ✓
- Dates: "this weekend, Friday" — very specific, very soon
- Soft blockers: none filled, but who cares — it's last minute

**What the system should decide:** `PROCEED_TRAVELER_SAFE` and the session strategy should prioritize SPEED over completeness. Skip the soft blocker questions. Book first, refine later.

**Insight:** The MVB doesn't account for urgency. A "rush" flag could suppress soft blocker questions.

---

## What This Reveals About NB02

### What NB02 Does Well
1. **The triage logic works** — empty → ask, complete → proceed, contradictory → stop
2. **The authority hierarchy is essential** — new notes override old CRM data
3. **Contradiction detection catches real problems** — couples who haven't agreed
4. **Stage progression is correct** — you can't book what you haven't chosen

### What NB02 Is Missing (From Real Scenarios)
1. **Urgency/rush handling** — last-minute trips should skip soft blockers
2. **Traveler-type-specific MVB** — elderly pilgrimages need medical blockers, corporate needs venue blockers
3. **Destination ambiguity vs ignorance** — "Andaman OR Sri Lanka" is different from "somewhere nice"
4. **Budget stretch signals** — "around 2L, can stretch" is not a single budget value
5. **Multi-source authority** — when husband and wife say different things, the system detects the contradiction but doesn't track WHO said what (the envelope tracking exists but the contradiction output doesn't surface it)

### The One Metric That Matters

**Does the agent waste the traveler's call?**

A wasted call is when the agent asks questions they should already know, or doesn't ask questions they critically need. NB02's job is to prevent wasted calls. Every test should be: "given this messy real note, does the system produce the right action?"

---

## Recommended Scenario Tests

If I were to write tests for NB02 from first principles, they'd look like:

```
Test: "Vague Lead" → ASK_FOLLOWUP with composition question FIRST
Test: "Confused Couple" → STOP_NEEDS_REVIEW (date conflict)
Test: "Dreamer" → INTERNAL_DRAFT with budget-vs-hotel question
Test: "Ready Buyer" → PROCEED_TRAVELER_SAFE
Test: "WhatsApp Dump" → ASK_FOLLOWUP with destination clarification
Test: "CRM Update" → PROCEED_TRAVELER_SAFE (new data overrides old)
Test: "Elderly Pilgrimage" → PROCEED_TRAVELER_SAFE but flag medical risk
Test: "Corporate Group" → Gap: no corporate-specific MVB
Test: "Last Minute" → PROCEED_TRAVELER_SAFE (urgency suppresses soft blockers)
```

These are the tests that matter. Not "empty packet returns 4 blockers" — nobody deploys an empty packet. Real data is always partial, always messy, always contradictory.
