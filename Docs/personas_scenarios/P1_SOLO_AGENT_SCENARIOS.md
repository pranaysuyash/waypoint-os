# P1: The Solo Agent - Real Work Scenarios

**Persona**: One-person travel agency, everything in their head, 10-30 trips/month  
**Goal**: Capture 80% of real situations they face in a typical month

---

## Scenario P1-S1: The 11 PM WhatsApp Panic

### Situation
**Time**: 11:23 PM  
**Channel**: WhatsApp  
**Customer**: Mrs. Sharma (past customer, booked Singapore 2024)  
**Message**:
> "Hi! Remember us? We want to go to Europe this time. Family of 5 - parents + 2 kids (now 8 and 12). Thinking June or July, maybe 10-12 days. Budget around 4-5L. Kids want to see snow. Parents can't walk too much. Can you send options by tomorrow morning? We want to book fast."

### Agent's Internal State
- Lying in bed, about to sleep
- Remembers Sharma family liked Gardens by the Bay in Singapore
- Can't remember if they have passports
- June/July is peak Europe season - hotels expensive
- "Snow in summer" = Switzerland, but that's expensive for 5 people
- Not sure if 4-5L is realistic for 5 people in Europe peak season

### Current Reality (Without System)
1. Sets alarm for 6 AM
2. Wakes up, scrolls WhatsApp to find their Singapore trip details
3. Opens 3-4 tabs: MakeMyTrip, hotel sites, flight search
4. Spends 2 hours researching
5. Builds quote in Word/Excel
6. Sends at 10 AM
7. Mrs. Sharma replies: "Oh we were hoping for 3L, can you reduce?" (wasted effort)

### What System Should Do
1. **Recognize customer**: Pull up Sharma family profile
   - Past trip: Singapore, Mar 2024, family of 4 (kids were younger)
   - Budget: 2.5L for Singapore
   - Preferences: Gardens, kid-friendly, vegetarian food
   - Passports: Valid until 2027

2. **Detect changes**:
   - Family size: 4 → 5 (added grandparent?)
   - Kids ages: Now 8 and 12 (different needs than last year)
   - Budget: 2.5L → 4-5L (good increase)

3. **Flag issues**:
   - ⚠️ "Snow in summer" + "Europe" = Switzerland/Alps, 4-5L for 5 people is tight in June/July
   - ⚠️ "Parents can't walk too much" - need accessible hotels, not just "snow"
   - ⚠️ "Tomorrow morning" + "Peak season" = rush job, limited options

4. **Suggested response** (agent can edit):
   > "Hi Mrs. Sharma! Great to hear from you. I remember you loved Gardens by the Bay. 
   > 
   > Quick questions for the best options:
   > 1. Is the 5th person a grandparent? (affects hotel rooms and pace)
   > 2. When you say 'snow' - do you mean see mountains or actually play in snow? 
   >    (Switzerland has both but very different budgets)
   > 3. Is 4-5L per person or total for family?
   > 
   > June/July peak season books fast - I'll hold some options while you confirm."

5. **Next morning prep**:
   - System has already pulled 3 suitable Switzerland itineraries
   - Flagged accessible hotels with lifts
   - Calculated realistic budget: 5-6L for 5 people
   - Ready for agent to review and send

### Key System Behaviors Tested
- Customer recognition and history lookup
- Change detection (family size, ages)
- Suitability warnings (budget vs reality)
- Question generation for missing info
- Pre-computation of options

---

## Scenario P1-S2: The Repeat Customer Who Forgot They Booked

### Situation
**Channel**: WhatsApp  
**Customer**: Mr. Gupta (booked Dubai Jan 2025)  
**Message** (3 months after Dubai trip):
> "Hello, planning a trip for family. Dubai was great! Want to try something new. Me, wife, 2 kids. Thinking international. Budget flexible. Suggestions?"

### Agent's Internal State
- Remembers Dubai trip went well
- Thinks: "Did I save their details? Where?"
- Opens WhatsApp, scrolls up 100 messages
- Finds: 2 kids ages 6 and 9, wife is vegetarian, stayed at Atlantis
- But doesn't remember: passport numbers, exact dates, what they liked/disliked

### Current Reality (Without System)
- Treated like new customer
- Asks same questions again
- Customer annoyed: "I told you this last time"
- Agent looks unprofessional

### What System Should Do
1. **Auto-recognize**: "Gupta family - Dubai trip Jan 2025"

2. **Pull complete profile**:
   ```
   Family: 2 adults, 2 kids (6F, 9M)
   Past trip: Dubai, 5 nights, Atlantis
   Budget: ~3.5L (was flexible, spent 3.2L)
   Preferences from post-trip notes:
   - Loved: Atlantis water park, Desert safari
   - Complained: Food was expensive, heat in afternoon
   - Wife: Strict vegetarian, needs Jain options
   - Kids: Need activities, get bored easily
   Passports: Valid until 2029
   ```

3. **Suggest based on pattern**:
   - "Since you liked Atlantis water park → consider Sentosa in Singapore"
   - "Since you complained about heat → avoid SE Asia in summer"
   - "Since kids need activities → Thailand has more than Bali"

4. **Agent sends**:
   > "Hi Mr. Gupta! So glad you enjoyed Dubai. I remember the kids loved Atlantis water park and your wife found great Jain options at that Indian restaurant.
   > 
   > Based on what you liked, here are 3 options:
   > 1. **Singapore**: Similar to Dubai (clean, organized), Sentosa has water parks, great Indian food
   > 2. **Thailand**: More activities for kids, but busier/crazier
   > 3. **Malaysia**: Genting Highlands for theme parks, cooler weather
   > 
   > Your passports are valid, so we're good to go once you decide!"

### Key System Behaviors Tested
- Customer history retention
- Preference learning from past trips
- Pattern matching (liked X → suggest similar Y)
- Avoiding repetitive questions

---

## Scenario P1-S3: The Customer Who Changes Everything

### Situation
**Initial Request** (Monday):
> "Family of 4, Maldives, March 15-20, budget 3L, honeymoon vibe"

**Revision 1** (Tuesday):
> "Actually can we do Bali instead? Same dates."

**Revision 2** (Wednesday):
> "Parents want to join, so 6 people now. And dates shifted to April."

**Revision 3** (Thursday):
> "Back to Maldives but for 6. But budget still 3L. Can we do it?"

### Agent's Internal State
- Frustrated: 3 hours of work, still no booking
- Started with Maldives overwater villa quote (romantic)
- Then Bali villa quote (different style)
- Now Maldives family resort (completely different)
- Math: 3L / 6 people = 50K per person = impossible for Maldives
- Doesn't want to say "no" and lose customer

### Current Reality (Without System)
- Builds 4 different quotes
- Each takes 1-2 hours
- Customer keeps changing
- Agent burns out
- Eventually books with competitor

### What System Should Do
1. **Track revision history**:
   ```
   Rev 1: Maldives, 4 pax, March, 3L (reasonable)
   Rev 2: Bali, 4 pax, March, 3L (reasonable)
   Rev 3: Bali, 6 pax, April, ??? (budget unknown)
   Rev 4: Maldives, 6 pax, April, 3L (IMPOSSIBLE)
   ```

2. **Flag reality check**:
   - ⚠️ "Maldives for 6 people on 3L budget = ₹50K/person"
   - ⚠️ "Maldives family resort cheapest = ₹80K/person including flights"
   - ⚠️ "Budget gap: ₹1.8L short"

3. **Suggest alternatives**:
   - "Maldives not possible at 3L for 6. Options:
     1. Increase budget to 5L
     2. Consider Andaman Islands (similar vibe, cheaper)
     3. Do Bali instead (luxury villa for 6 fits in 3L)"

4. **Agent protection**:
   - Show revision count: "4 versions in 4 days"
   - Suggest: "Let's confirm requirements before next quote"
   - Maybe: "Planning fee of ₹5000 after 3 revisions"

### Key System Behaviors Tested
- Change tracking across versions
- Reality checking (budget vs feasibility)
- Agent protection (time sink detection)
- Alternative generation when original won't work

---

## Scenario P1-S4: The Visa Problem at Last Minute

### Situation
**Current Date**: March 1  
**Travel Date**: March 20 (19 days away)  
**Customer**: First-time international travelers, family of 4  
**Destination**: Dubai  
**Booking Status**: Hotels booked, flights on hold  
**Agent's Discovery**: Customer passports expired 2 months ago

### Agent's Internal State
- PANIC
- Dubai visa typically takes 5-7 working days
- Passport renewal takes 15-20 days minimum
- March 20 is impossible
- Customer will blame agent for not asking earlier

### Current Reality (Without System)
- Agent forgot to check passport validity
- Customer assumed "international trip" = agent handles everything
- Emergency passport renewal (₹5000 extra, may not finish in time)
- If they miss the trip: ₹2L in cancellation fees
- Agent pays or loses customer

### What System Should Do
1. **At intake** (when Dubai was first discussed):
   - Check: "Passport validity" as HARD BLOCKER
   - Don't allow "PROCEED" until passports verified
   - Show: "⚠️ Passport required. Minimum 6 months validity needed."

2. **At booking stage**:
   - System enforces: Cannot mark "booking ready" without passport scan
   - Like a checklist that must be checked

3. **Now (crisis mode)**:
   - Show options:
     - Emergency tatkal passport (15 days, ₹5000 extra, RISKY)
     - Change dates to April (rebook everything, fees apply)
     - Change destination to domestic (no passport needed)
   - Calculate cost of each option

4. **Learning**:
   - Flag this agent to ALWAYS check passports first
   - Update intake flow to require passport before quoting

### Key System Behaviors Tested
- Hard blockers (visa/documentation)
- Stage gating (can't proceed without docs)
- Crisis management suggestions
- Learning from failures

---

## Scenario P1-S5: The Group Trip with Different Paying Parties

### Situation
**Group**: 3 families (6 adults, 5 kids)  
**Destination**: Singapore  
**Coordinator**: Mrs. Reddy (organizing for all 3 families)  
**Complexity**:
- Family A: Can pay full upfront
- Family B: Needs EMI/Installments
- Family C: Will pay 50% now, 50% later
- Total budget: 8L (3L + 2.5L + 2.5L)
- Different rooming: Some want connecting rooms, some separate

### Agent's Internal State
- One quote or three quotes?
- How to track who paid what?
- What if Family C doesn't pay second installment?
- Who is responsible if someone cancels?
- Messy logistics

### Current Reality (Without System)
- Agent builds one master quote
- Tracks payments in Excel
- Constantly updating: "Family B paid installment 2"
- At airport: realizes Family C didn't submit passport copies
- Chaos

### What System Should Do
1. **Split view**:
   - Master itinerary (same for all)
   - Individual family views (different payment terms)

2. **Payment tracking**:
   ```
   Family A (Reddy): ₹3L — Paid in full ✅
   Family B (Kumar): ₹2.5L — Installment 2/3 paid (₹1.67L remaining)
   Family C (Shah): ₹2.5L — 50% paid (₹1.25L remaining, due March 1)
   ```

3. **Dependency management**:
   - Can't confirm booking until ALL families pay minimum 50%
   - Automated reminders to Family B and C
   - Clear: "Payment from Family C overdue - booking at risk"

4. **Document collection**:
   - Track: Family A submitted all passports
   - Track: Family B missing 1 child's passport
   - Track: Family C not submitted any
   - Blocker: "Cannot proceed to booking - missing documents from Family B, C"

### Key System Behaviors Tested
- Multi-party booking management
- Payment tracking with different terms
- Dependency gating (all or nothing)
- Document collection tracking

---

## Summary: What Solo Agent Needs

| Need | Scenario | System Feature |
|------|----------|----------------|
| **Memory** | P1-S2 (repeat customer) | Customer profiles, preference history |
| **Speed** | P1-S1 (11 PM request) | Pre-computed options, quick questions |
| **Protection** | P1-S3 (revision loop) | Change tracking, time-sink alerts |
| **Compliance** | P1-S4 (visa/passport) | Hard blockers, document checklists |
| **Complexity** | P1-S5 (group payment) | Multi-party tracking, payment management |

**Common thread**: Solo agent needs a **memory and safety system** - so they don't drop balls, forget details, or waste time.

---

*Next: P2 Agency Owner scenarios (oversight, team management, standardization)*
