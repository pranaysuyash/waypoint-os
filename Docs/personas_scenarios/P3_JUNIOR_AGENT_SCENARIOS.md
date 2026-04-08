# P3: The Junior Agent - Real Work Scenarios

**Persona**: New to industry, 0-2 years experience, learning, afraid of mistakes  
**Goal**: Build confidence, learn fast, avoid expensive errors

---

## Scenario P3-S1: The First Solo Quote

### Situation
**Agent**: Anita (Week 3, first quote without supervision)  
**Customer**: WhatsApp inquiry  
**Message**: "Hi, family trip. 2 adults, 1 kid age 7. Want to see snow. Budget 2-3L. When can you send options?"

### Anita's Internal State
- PANIC: "What do I do first?"
- Questions in head:
  - Which destination has snow in March?
  - Is 2-3L enough for 3 people?
  - What hotels are kid-friendly?
  - How do I build a quote?
- Wants to ask senior but feels embarrassed
- Spends 30 minutes just staring at the message

### Current Reality (Without System)
1. Anita asks senior: "What should I suggest?"
2. Senior says: "Check their dates first"
3. Anita asks customer: "When do you want to travel?"
4. Customer: "March 15-20"
5. Anita realizes: "Wait, snow in March means... where?"
6. Spends 2 hours researching "snow destinations in March"
7. Builds quote manually
8. Senior reviews, finds 3 mistakes
9. Anita feels incompetent

### What System Should Do
1. **Guided Intake**:
   ```
   New Lead Detected
   ┌──────────────────────────────────────────────┐
   │ Step 1: Capture Basic Info                   │
   │ ✅ Group size: 3 (2 adults, 1 child age 7)   │
   │ ✅ Interest: Snow                            │
   │ ✅ Budget: 2-3L                              │
   │ ❓ Dates: Not specified - MUST ASK           │
   │ ❓ Origin: Not specified - MUST ASK          │
   │                                               │
   │ [Ask Customer] → Generates WhatsApp message: │
   │ "Thanks! To suggest the best options,        │
   │  which dates work for you? And where        │
   │  will you be traveling from?"                │
   └──────────────────────────────────────────────┘
   ```

2. **Smart Suggestions** (when dates come: March 15-20):
   ```
   Customer wants: Snow in mid-March
   
   System suggests:
   • Manali, India (snow likely, fits budget) 🇮🇳
   • Gulmarg, Kashmir (snow certain, check security) 🇮🇳  
   • Switzerland (guaranteed snow, budget may be tight) 🇨🇭
   
   ⚠️ Budget Check: 2-3L for 3 people
   • Manali: Fits comfortably (₹1.5-2L)
   • Switzerland: Tight (₹2.5-3L minimum)
   
   Anita clicks: "Manali - Family Package"
   → Auto-builds quote with:
      • Kid-friendly hotel (play area, warm rooms)
      • Day trip to Solang Valley (snow activities)
      • Flight from Delhi (common origin assumption)
   ```

3. **Confidence Score Before Sending**:
   ```
   Your Quote Confidence: 78%
   
   ✅ Budget checked: Within range
   ✅ Suitability: Hotel has play area for 7-year-old
   ⚠️ Flights: Assumed Delhi origin - CONFIRM
   ❓ Visa: Not needed for India domestic
   
   Suggest: Add line "Assuming Delhi departure - 
            please confirm your city"
   ```

4. **Safety Net**:
   - Quote doesn't send directly to customer
   - Goes to senior for review first (Week 1-4 setting)
   - Senior approves or adds comments

### Key System Behaviors Tested
- Step-by-step guidance
- Smart suggestions based on constraints
- Budget feasibility checking
- Confidence scoring
- Mentorship workflow

---

## Scenario P3-S2: The Visa Mistake Prevention

### Situation
**Agent**: Anita  
**Booking**: Thailand for family of 4  
**Customer**: First-time international travelers  
**Anita's Knowledge**: "Thailand is visa-free for Indians" (learned in training)

### What Anita Doesn't Know
- Thailand visa-free: Only for stays under 15 days
- This customer: 18-day trip
- Requires visa-on-arrival or pre-approved visa
- Passport must have 6 months validity
- 2 kids need birth certificates

### Current Reality (Without System)
- Anita books flights and hotels
- Tells customer: "No visa needed"
- Customer reaches airport
- Airline: "You need visa for 18 days"
- Customer misses flight
- ₹80K loss + agency reputation damaged
- Anita feels terrible, considers quitting

### What System Should Do
1. **At Intake** (capturing travel dates):
   ```
   Destination: Thailand
   Duration: 18 days
   
   ⚠️ VISA ALERT
   Thailand visa-free only for <15 days
   This trip: 18 days → VISA REQUIRED
   
   Options:
   1. Visa on Arrival (₹4000/person, queue at airport)
   2. Pre-approved visa (₹2500/person, apply now)
   
   Required Documents:
   ✅ Passport (6 months validity)
   ✅ Return flight tickets
   ✅ Hotel bookings
   ❓ Birth certificates for kids (not captured)
   ```

2. **Hard Blocker**:
   - System won't allow "PROCEED_TO_BOOKING" until:
     - Visa requirement acknowledged
     - Passport validity confirmed
     - Document checklist complete

3. **Anita's View**:
   ```
   ⚠️ CANNOT PROCEED - VISA ISSUE
   
   You said: "No visa needed"
   Reality: Visa required for 18 days
   
   System guidance:
   Step 1: Inform customer visa is needed
   Step 2: Collect passport copies
   Step 3: Check validity (6 months)
   Step 4: Apply for visa OR reduce trip to 14 days
   
   [Learn More: Thailand visa rules]
   ```

4. **Learning Moment**:
   - After resolution, system shows:
     "Lesson learned: Always check duration for visa-free destinations"
   - Adds to Anita's knowledge base

### Key System Behaviors Tested
- Visa requirement checking
- Hard blockers on critical info
- Mistake prevention
- Just-in-time education

---

## Scenario P3-S3: The "Is This Right?" Check

### Situation
**Agent**: Anita  
**Quote**: Built for Europe trip, 2 weeks, family of 4  
**Budget quoted**: ₹12L  
**Anita's doubt**: "Seems expensive but I calculated twice..."

### What Anita Did
- Added flights: ₹4L
- Added hotels: ₹5L (4-star, 14 nights)
- Added activities: ₹1.5L
- Added transfers: ₹1L
- Added margin: ₹0.5L (10%)
- Total: ₹12L

### What She's Missing
- European hotels charge city tax (€3-5/night) - not included
- Schengen visa: ₹8000/person = ₹32K (forgot)
- Travel insurance: ₹15K (forgot)
- Meals not included: €50/day × 14 = ₹70K (didn't mention to customer)
- Actual cost to customer will be ₹13.5L+, not ₹12L

### Current Reality (Without System)
- Anita sends quote
- Customer books
- During trip: Surprise expenses
- Customer angry: "You said ₹12L, spent ₹14L!"
- Anita learns: "Always include all costs"
- But damage done

### What System Should Do
1. **Quote Completeness Check**:
   ```
   Quote Review - Europe, 14 days, Family of 4
   
   ✅ Included:
      • Flights: ₹4L
      • Hotels: ₹5L
      • Activities: ₹1.5L
      • Transfers: ₹1L
   
   ❌ MISSING (Common for Europe):
      • Schengen visa: ₹32K (4 people)
      • Travel insurance: ₹15K (recommended)
      • City tax: ₹25K (€4/night × 14 nights)
      • Meals: ~₹70K (if not included)
      
   True Total: ₹12L + ₹1.42L = ₹13.42L
   
   Suggest: Add line "Excludes visa, insurance, 
            city tax, meals (~₹1.4L additional)"
   ```

2. **Peer Comparison**:
   ```
   Similar Europe quotes by other agents:
   • Priya's quote (Mar 2024): ₹13.8L (similar itinerary)
   • Suresh's quote (Feb 2024): ₹12.5L (shorter trip)
   
   Your quote: ₹12L (seems low - missing items?)
   ```

3. **Confidence Boost**:
   - System: "Quote looks good but add visa/insurance disclosure"
   - Anita feels supported, not stupid
   - Adds disclaimer, sends quote
   - Customer: "Thanks for transparency about extra costs"

### Key System Behaviors Tested
- Quote completeness validation
- Missing item detection
- Peer comparison for calibration
- Transparency enforcement

---

## Scenario P3-S4: The Customer Asks Something I Don't Know

### Situation
**Agent**: Anita  
**Customer**: "Is Hotel X wheelchair accessible? My mother uses a wheelchair."

### Anita's Internal State
- Doesn't know Hotel X accessibility
- Afraid to say "I don't know" (looks unprofessional)
- Afraid to guess (might be wrong)
- Searches hotel website for 10 minutes
- Still not sure

### Current Reality (Without System)
- Anita says: "I think so, most hotels have ramps"
- Customer books based on this
- Arrives: Hotel has stairs at entrance
- Mother can't access lobby
- Disaster trip
- Bad review: "Agent lied about accessibility"

### What System Should Do
1. **Knowledge Base Query**:
   ```
   Customer asks: "Is Marina Bay Sands wheelchair accessible?"
   
   System shows:
   ┌──────────────────────────────────────────────┐
   │ Marina Bay Sands - Accessibility             │
   │ ✅ Wheelchair accessible entrance            │
   │ ✅ Elevator to all floors                    │
   │ ✅ Accessible rooms available (request)      │
   │ ❌ Pool area has steps (not accessible)      │
   │                                               │
   │ Source: Hotel website + 3 agent notes        │
   │ Last verified: Jan 2025                      │
   └──────────────────────────────────────────────┘
   
   Suggested response:
   "Yes, Marina Bay Sands is wheelchair accessible 
    with ramps and elevators. They have accessible 
    rooms, but please request in advance. Note: 
    The infinity pool area has steps."
   ```

2. **If Unknown**:
   ```
   No accessibility info for "Hotel ABC"
   
   Options:
   1. Check hotel website (link provided)
   2. Call hotel directly (phone provided)
   3. Ask in agent group chat
   4. Tell customer: "Let me verify and get back"
   
    Never guess on accessibility
   ```

3. **Capture Learning**:
   - After Anita finds out, system asks:
     "Add accessibility info for Hotel ABC to knowledge base?"
   - Next agent benefits

### Key System Behaviors Tested
- Knowledge base access
- "Don't guess" protection
- Learning capture
- Transparency encouragement

---

## Scenario P3-S5: The Comparison Trap

### Situation
**Agent**: Anita  
**Customer**: "Another agent quoted ₹2.5L for same Singapore trip. You're asking ₹3L. Why?"

### Anita's Internal State
- Panic: "Am I overcharging?"
- Self-doubt: "Maybe I should reduce margin"
- Doesn't know what other agent included
- Pressure to match price
- Might reduce to ₹2.5L and lose money

### Current Reality (Without System)
- Anita reduces quote to ₹2.5L
- Margin drops from 12% to 5%
- Later finds: Other agent's quote didn't include:
  - Airport transfers (₹15K)
  - Some meals (₹20K)
  - Universal Studios tickets (₹30K)
- Customer: "Your quote is missing things!"
- Anita loses credibility and margin

### What System Should Do
1. **Apples-to-Apples Comparison**:
   ```
   Customer comparing: ₹2.5L (Agent X) vs ₹3L (You)
   
   System analysis:
   ┌──────────────────────────────────────────────┐
   │ Your Quote (₹3L)          │ Agent X (₹2.5L)  │
   ├───────────────────────────┼──────────────────┤
   │ Hotel: Hard Rock          │ Hotel: York      │
   │ (₹12K/night)              │ (₹8K/night)      │
   │                           │                  │
   │ Transfers: Included       │ Transfers: ❌    │
   │ (₹15K)                    │ (Not included)   │
   │                           │                  │
   │ USS Tickets: Included     │ USS Tickets: ❌  │
   │ (₹30K)                    │ (Not included)   │
   │                           │                  │
   │ Total inclusions: ₹3L     │ If you add       │
   │                           │ missing items:   │
   │                           │ ₹2.5L + ₹65K     │
   │                           │ = ₹3.15L         │
   └──────────────────────────────────────────────┘
   
   Your quote is actually BETTER value
   ```

2. **Suggested Response**:
   ```
   "Happy to explain! My ₹3L includes:
   • Hard Rock (vs York Hotel - better for kids)
   • Airport transfers (₹15K value)
   • Universal Studios tickets (₹30K value)
   
   If you add these to the ₹2.5L quote, 
   it becomes ₹2.95L with a lower-grade hotel.
   
   Would you like me to adjust to match 
   the lower hotel and remove inclusions?"
   ```

3. **Margin Protection**:
   - System: "Don't drop below 10% margin"
   - Shows: "At ₹2.5L, your margin is 3% - not viable"
   - Suggest: Offer value comparison instead of price match

### Key System Behaviors Tested
- Competitive quote analysis
- Value comparison (not just price)
- Margin protection
- Negotiation support

---

## Summary: What Junior Agent Needs

| Need | Scenario | System Feature |
|------|----------|----------------|
| **Guidance** | P3-S1 (first quote) | Step-by-step workflows |
| **Mistake Prevention** | P3-S2 (visa) | Hard blockers, alerts |
| **Completeness** | P3-S3 (missing costs) | Validation, peer comparison |
| **Knowledge Access** | P3-S4 (accessibility) | Instant knowledge base |
| **Confidence** | P3-S5 (comparison) | Negotiation support, margin protection |

**Common thread**: Junior agent needs a **safety net and coach** - so they learn fast without breaking things.

---

*Next: S1/S2 Customer scenarios (end customer experience)*
