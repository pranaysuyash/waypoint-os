# P2: The Agency Owner - Real Work Scenarios

**Persona**: Small agency owner, 3-8 employees, scaling challenges, quality control concerns  
**Goal**: Capture oversight, management, and standardization needs

---

## Scenario P2-S1: The Quote Disaster Review

### Situation
**Monday Morning**: Owner reviewing weekend quotes sent by team  
**Agent**: Ramesh (junior, 3 months experience)  
**Quote**: For customer Mr. Mehta - Singapore family trip

### What Owner Finds
**Quote sent by Ramesh**:
- 5-star hotel: Marina Bay Sands
- 5 nights: ₹4.5L for family of 4
- Flights: Singapore Airlines business class
- Total: ₹6.5L

**Customer Response**: "Too expensive, going with another agent"

### Owner's Analysis (Without System)
- Checks Ramesh's work manually
- Finds: Customer budget was "2-3L flexible" - Ramesh quoted 6.5L
- Finds: Customer asked for "kid-friendly" - Ramesh suggested Marina Bay (not kid-friendly)
- Finds: No alternative options given
- Ramesh says: "But sir, Marina Bay is best hotel"
- Owner thinks: "He doesn't understand customer fit vs luxury"

### What Actually Happened
Customer wanted:
- Budget: 2-3L (not 6.5L)
- Kid-friendly: Pool, activities, near Universal Studios
- Ramesh suggested: Marina Bay (casino focus, not for kids, expensive)

**Mistake**: Ramesh quoted what HE thought was best, not what customer needed.

### What System Should Show Owner
1. **Quote Review Dashboard**:
   ```
   Quote #1234 - Ramesh - Mr. Mehta
   Status: Customer declined ❌
   Issues Detected:
   ⚠️ Budget mismatch: Customer said 2-3L, quoted 6.5L (217% over)
   ⚠️ Suitability risk: Marina Bay has casino, not ideal for kids (ages 6,9)
   ⚠️ No alternatives: Only 1 option given (should be 2-3)
   ⚠️ Margin: Only 8% (should be 12-15%)
   
   Suggested Alternative:
   - Hotel: Hard Rock Sentosa (kid-friendly, pool, near USS)
   - Total: ₹2.8L (within budget)
   - Margin: 14%
   ```

2. **Training Opportunity**:
   - Flag for Ramesh: "Review: Budget alignment lesson"
   - Show: Comparison of "what was quoted" vs "what customer asked"

3. **Customer Recovery**:
   - Owner can send: "Apologies, my agent misunderstood. Here's better option..."

### Key System Behaviors Tested
- Quote quality monitoring
- Budget/suitability checking
- Automated issue detection
- Training opportunity identification

---

## Scenario P2-S2: The Agent Who Left (Knowledge Walkout)

### Situation
**Agent**: Priya (2 years experience, handled 40+ customers)  
**Action**: Quit last Friday, joined competitor  
**Problem**: All her customer knowledge walked out with her

### What Owner Loses (Without System)
- Priya had 15 active bookings in progress
- She knew: "Mr. Sharma is picky about vegetarian food"
- She knew: "Mrs. Kumar always pays late, need reminders"
- She knew: "The Gupta kids get car sick, avoid long drives"
- All in Priya's head and WhatsApp
- New agent doesn't know any of this

### Immediate Crisis
**Monday**: 3 customers call, new agent answers:
- Mr. Sharma: "Tell Priya I confirmed the Jain restaurant"
  - New agent: "Uh... Priya left, what Jain restaurant?"
  - Customer: "You don't know? I told her last week!"
  
- Mrs. Kumar: "I'm paying tomorrow, tell Priya not to worry"
  - New agent: "Which booking? When is deadline?"
  - Customer: "She knows, it's our 3rd trip with you"

### What System Should Have
1. **Customer Knowledge Base**:
   ```
   Mr. Sharma (Customer #234)
   ├── Preferences (captured by Priya)
   │   ├── Strict Jain vegetarian
   │   ├── Avoids AC buses (gets cold)
   │   ├── Prefers early morning flights
   │   └── Birthday: March 15 (send greeting)
   ├── Payment History
   │   ├── Always pays 50% upfront, 50% 1 week before
   │   └── Never late, but needs reminders
   └── Active Booking: Singapore, Mar 15-20
       └── Special notes: Confirmed Jain restaurant at Hard Rock
   ```

2. **Agent Transition Protocol**:
   - When agent leaves: Auto-transfer all customers
   - New agent sees: "Inherited from Priya - read notes before calling"
   - Customer doesn't know agent changed (seamless)

3. **Active Bookings Dashboard**:
   ```
   Priya's Bookings (15) - REASSIGNED TO Suresh
   
   URGENT (This Week):
   - Sharma: Flight tomorrow, vegetarian meal confirmed? ⚠️
   - Kumar: Payment due Mar 10, send reminder 📅
   
   IN PROGRESS:
   - Gupta: Finalizing itinerary, kids get car sick 🚗
   - Reddy: Passport copies pending 🛂
   ```

### Key System Behaviors Tested
- Knowledge persistence (survives agent departure)
- Customer context preservation
- Agent transition management
- Institutional memory

---

## Scenario P2-S3: The Margin Erosion Problem

### Situation
**Month-End Review**: Owner checking P&L  
**Problem**: Revenue up 20% but profit flat  
**Mystery**: Where is the money going?

### Owner's Investigation (Without System)
- Reviews 30 quotes manually
- Finds patterns:
  - Agent 1 (Ramesh): Averaging 8% margin
  - Agent 2 (Suresh): Averaging 12% margin
  - Agent 3 (Priya): Averaging 15% margin
- Ramesh is undercutting to close deals
- No standard pricing rules
- Every agent decides margin independently

### Root Causes
1. **No minimum margin enforcement**: Ramesh quoting 5-8% to "win"
2. **No visibility**: Owner sees final quote, not decision process
3. **No training**: Ramesh doesn't understand margin impact
4. **Discount authority**: Junior agents can discount freely

### What System Should Show
1. **Margin Dashboard**:
   ```
   Monthly Margin Analysis
   ┌─────────────────────────────────────────┐
   │ Overall: 11.2% (Target: 13%)            │
   │                                         │
   │ By Agent:                               │
   │ • Priya:  15.3% ✅ Exceeds target       │
   │ • Suresh: 12.1% ✅ On target            │
   │ • Ramesh:  8.4% ❌ Below minimum        │
   │                                         │
   │ Ramesh's Low-Margin Quotes:             │
   │ • Quote #123: 5% margin (Mehta)         │
   │ • Quote #145: 7% margin (Kumar)         │
   │ • Quote #167: 6% margin (Sharma)        │
   └─────────────────────────────────────────┘
   ```

2. **Quote Approval Workflow**:
   - Auto-approve: Margin > 12%
   - Needs approval: Margin 8-12%
   - Blocked: Margin < 8% (must get owner approval)

3. **Agent Coaching**:
   - Ramesh sees: "Your average margin is 8.4%. Each 1% = ₹X less revenue."
   - Suggested: "Try bundling airport transfers to increase margin without raising price"

### Key System Behaviors Tested
- Margin tracking and alerting
- Automated approval workflows
- Performance comparison across agents
- Coaching based on data

---

## Scenario P2-S4: The Training Time Problem

### Situation
**New Hire**: Anita (fresh graduate, zero travel industry experience)  
**Current Reality**:
- Day 1-7: Shadowing senior agent
- Day 8-14: Trying to build quotes, seniors checking everything
- Day 15-30: Still needs help with every quote
- Day 30: Can't work independently

**Problem**: 1 month of salary (₹25K) before productive  
**Question**: Can system reduce this to 1 week?

### What Training Looks Like Now (Without System)
- Anita asks: "Which hotel in Singapore is good for families?"
- Senior says: "Hard Rock Sentosa, but not if budget is tight"
- Anita asks: "What is tight budget?"
- Senior says: "Under 2.5L for 4 people"
- Anita forgets, asks again next week
- Knowledge not captured, repeated 100 times

### What System Should Enable
1. **Guided Quote Building**:
   ```
   Anita is building quote for: Family of 4, Singapore, 3L budget
   
   System suggests:
   ┌────────────────────────────────────────────────┐
   │ Step 1: Destination                            │
   │ ✅ Singapore selected                          │
   │                                                │
   │ Step 2: Hotel (Budget: 3L for 4 people)        │
   │ System recommends:                             │
   │ • Hard Rock Sentosa (₹12K/night) - Kid-friendly│
   │ • York Hotel (₹8K/night) - Budget option       │
   │ • Marina Bay (₹25K/night) - Too expensive ❌   │
   │                                                │
   │ Why: 5 nights × ₹25K = ₹1.25L just hotel       │
   │      Remaining for flights = ₹1.75L            │
   │      Flights cost ₹2L, so over budget ⚠️       │
   └────────────────────────────────────────────────┘
   ```

2. **Just-in-Time Learning**:
   - When Anita selects "Marina Bay": System shows popup
   - "This hotel is expensive. Good for honeymoon, not families on budget"
   - "Learn more: Click here to see family-friendly alternatives"

3. **Confidence Scoring**:
   ```
   Anita's Quote #1: Confidence 45%
   Issues:
   - Budget feasibility not checked
   - No alternative options
   - Suitability not verified
   
   Suggest: Review with senior before sending
   ```

4. **Auto-Check Before Send**:
   - System validates: Margin, budget, suitability
   - If issues found: "Quote has warnings. Send anyway?"
   - Tracks: "Anita sent quote with warnings 3 times this week"

### Key System Behaviors Tested
- Guided workflows for beginners
- Real-time coaching
- Confidence scoring
- Validation before action

---

## Scenario P2-S5: The Weekend Panic (No Visibility)

### Situation
**Friday 6 PM**: Owner leaving office  
**Sunday 8 PM**: Emergency call from customer  
**Customer**: "My flight is tomorrow and I don't have the ticket!"

### Owner's Panic (Without System)
- Which agent handled this?
- Was ticket actually booked?
- Did customer pay?
- Where are the documents?
- Calls agent (not picking up)
- Calls customer: "Let me check, call you back"
- Spends 2 hours chasing info

### What Actually Happened
- Agent Suresh booked flight Thursday
- Sent ticket to customer's old email (typo)
- Customer didn't receive
- No follow-up from Suresh
- No system tracking if customer received documents

### What System Should Show Owner (Sunday 8 PM)
1. **Emergency Dashboard**:
   ```
   🚨 URGENT: Tomorrow's Departures (March 15)
   ┌──────────────────────────────────────────────┐
   │ Mr. Sharma - Singapore                       │
   │ Status: Booked ✅                             │
   │ Flight: SQ423, Mar 15, 10:30 AM              │
   │ Ticket: Sent to sharma@gmsil.com (typo?) ⚠️  │
   │ Payment: Received ✅                          │
   │ Documents: Passport copy missing 🛂          │
   │                                              │
   │ Action: Customer called - resend ticket      │
   │         to correct email                     │
   └──────────────────────────────────────────────┘
   ```

2. **Daily Digest**:
   - Every morning: "Today's departures: 3 trips"
   - Show: What's confirmed, what's missing
   - Auto-sms customer: "Your trip is tomorrow! Here's your ticket..."

3. **Document Verification**:
   - Ticket sent: ✓
   - Customer opened email: ✓
   - Customer downloaded ticket: ✗ (not confirmed)
   - System flagged: "Customer may not have ticket"
   - Auto-reminder sent Saturday: "Download your ticket"

### Key System Behaviors Tested
- Operational visibility (what's happening tomorrow)
- Document delivery tracking
- Proactive alerting
- Emergency dashboard

---

## Summary: What Agency Owner Needs

| Need | Scenario | System Feature |
|------|----------|----------------|
| **Quality Control** | P2-S1 (quote disaster) | Automated quote review, issue detection |
| **Knowledge Retention** | P2-S2 (agent left) | Persistent customer profiles |
| **Margin Control** | P2-S3 (erosion) | Margin tracking, approval workflows |
| **Training Efficiency** | P2-S4 (new hire) | Guided workflows, coaching |
| **Operational Visibility** | P2-S5 (weekend panic) | Dashboards, proactive alerts |

**Common thread**: Owner needs **visibility and control** without micromanaging every detail.

---

*Next: P3 Junior Agent scenarios (onboarding, confidence building, mistake prevention)*
