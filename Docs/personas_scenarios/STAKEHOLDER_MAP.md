# Stakeholder & Persona Map

**Project**: Travel Agency AI Copilot  
**Date**: 2026-04-09  
**Purpose**: Identify all humans who interact with or are affected by the system

---

## Persona Categories

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PRIMARY USERS (Direct System Users)                 │
├─────────────────────────────────────────────────────────────────────────────┤
│  P1. The Solo Agent        P2. The Agency Owner      P3. The Junior Agent  │
│  (One-person show)         (Small team lead)         (New to industry)     │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                      SECONDARY USERS (Affected by System)                   │
├─────────────────────────────────────────────────────────────────────────────┤
│  S1. The Traveler          S2. The Family Decision Maker                     │
│  (End customer)            (Books for group)                                │
│                                                                              │
│  S3. The Concierge         S4. The Supplier Contact                         │
│  (High-touch service)      (Hotels, airlines)                               │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                      ANTI-PERSONAS (System Risks)                           │
├─────────────────────────────────────────────────────────────────────────────┤
│  A1. The Price Shopper     A2. The Indecisive Customer                       │
│  (Uses system to compare)  (Endless revisions)                              │
│                                                                              │
│  A3. The Over-Confident    A4. The Under-Informed                           │
│  (Ignores warnings)        (Doesn't know basics)                            │
└─────────────────────────────────────────────────────────────────────────────┘

```

---

## Primary Personas: The Agency Side

### P1: The Solo Agent ("The One-Person Show")

**Demographics**:
- 30-50 years old
- 1-person business
- Works from home or small office
- 10-30 trips booked per month
- Revenue: ₹50K-2L per month

**Current Reality**:
- Everything in their head: vendor contacts, preferences, past trips
- WhatsApp = CRM (scrolling through chats to find info)
- Google Sheets for tracking
- Personal memory for customer preferences
- No formal processes
- Works 10-12 hour days

**Pain Points**:
1. **Knowledge trapped** - If they get sick, business stops
2. **Repeat customers treated like new** - Can't remember every preference
3. **Slow response times** - Researching options from scratch each time
4. **No backup** - Single point of failure
5. **Scope creep** - Small requests become big time drains

**Goals**:
- Respond faster to leads
- Remember customer preferences automatically
- Scale without hiring
- Sleep without worrying about forgetting something

**Tech Comfort**: Medium (uses WhatsApp, basic Excel, not tech-savvy)

**Quote**: *"I know exactly which hotel in Singapore is perfect for Indian families with toddlers. But I forget which customer I told that to."*

---

### P2: The Agency Owner ("The Growing Team")

**Demographics**:
- 35-55 years old
- 3-8 employees
- Physical office location
- 50-200 trips per month
- Revenue: ₹3L-15L per month

**Current Reality**:
- Multiple agents handling different clients
- Inconsistent service quality
- Training new staff takes months
- No standardization in quotes
- Customer data scattered across agents
- Owner still involved in every decision

**Pain Points**:
1. **Quality control** - Can't review every quote
2. **Training time** - New agents take 3-6 months to become productive
3. **Customer leakage** - Agents leave, take clients with them
4. **Margin erosion** - Agents discount without approval
5. **Lack of visibility** - Don't know what's in pipeline

**Goals**:
- Standardize quality across all agents
- Reduce training time for new hires
- Capture institutional knowledge
- Monitor margins automatically
- Scale without owner bottleneck

**Tech Comfort**: Low-Medium (uses email, basic tools, resistant to complex software)

**Quote**: *"I hired 3 people and I'm still working harder than when I was solo. Knowledge walks out the door when they leave."*

---

### P3: The Junior Agent ("The New Hire")

**Demographics**:
- 22-30 years old
- 0-2 years experience
- Learning the trade
- Handles 5-15 trips per month initially

**Current Reality**:
- Shadowing senior agents
- Asking "which hotel is good?" repeatedly
- Making mistakes that cost money
- Takes 2 hours to build a quote that seniors do in 20 minutes
- Doesn't know vendor relationships
- Unsure about pricing/margins

**Pain Points**:
1. **Imposter syndrome** - Afraid to give wrong advice
2. **Slow work** - Everything requires research
3. **Dependency** - Can't work independently
4. **Mistakes** - Books wrong hotels, misses visa requirements
5. **Customer trust** - Customers ask for senior agent instead

**Goals**:
- Work independently faster
- Access institutional knowledge
- Avoid rookie mistakes
- Build confidence
- Handle complex requests

**Tech Comfort**: High (digital native, comfortable with apps and tools)

**Quote**: *"I spend 3 hours researching what my senior would know in 5 minutes. I don't want to keep asking dumb questions."*

---

## Secondary Personas: The Customer Side

### S1: The Traveler ("The End Customer")

**Demographics**:
- 28-55 years old
- Upper-middle class
- Books 1-2 international trips per year
- Budget: ₹2L-10L per trip

**Current Reality**:
- Gets quotes from 3-4 agencies
- Compares with MakeMyTrip/Booking.com
- Sends same requirements to multiple agents
- Wants personalized service but also best price
- Unrealistic expectations from Instagram

**Pain Points**:
1. **Slow responses** - Waits 24-48 hours for quotes
2. **Generic quotes** - Feels like copy-paste
3. **Hidden costs** - Surprise expenses during trip
4. **No transparency** - Can't see why one option costs more
5. **Poor fit** - Recommended hotels don't match actual needs

**Goals**:
- Fast, personalized responses
- Clear pricing breakdown
- Confidence that trip will work
- Someone to call if things go wrong
- Good value (not necessarily cheapest)

**Quote**: *"I sent my requirements to 4 agents. One replied in 2 hours with a perfect quote. The others took 2 days with generic packages. Guess who got my business?"*

---

### S2: The Family Decision Maker ("The Coordinator")

**Demographics**:
- 35-50 years old
- Planning for parents + children + spouse
- Budget conscious but wants comfort
- Needs to satisfy multiple preferences

**Current Reality**:
- Collecting preferences from 4-6 people
- Trying to keep everyone happy
- Worried about elderly parents' comfort
- Concerned about child safety/fun
- Managing expectations across generations

**Pain Points**:
1. **Different needs** - Parents want rest, kids want adventure
2. **Coordination burden** - Chasing everyone for passport details
3. **Decision fatigue** - Too many options, can't choose
4. **Risk anxiety** - What if parents get sick? What if kids are bored?
5. **Budget pressure** - Stretched across 5-6 people

**Goals**:
- One solution that works for everyone
- Clear communication to all family members
- Backup plans for emergencies
- Easy payment splitting
- Peace of mind

**Quote**: *"I'm planning a trip for my parents, my kids, and my spouse. Everyone wants something different and I'm the one who gets blamed if it's bad."*

---

## Anti-Personas: System Risks

### A1: The Price Shopper ("The Comparison Junkie")

**Behavior**:
- Gets quote, takes to competitor
- Uses system for research, books elsewhere
- Asks for detailed breakdown to compare
- No loyalty, purely transactional

**Risk to Agency**:
- Wastes time on non-converting leads
- Margin compression
- Knowledge leakage to competitors

**How System Handles**:
- Qualify early (budget + intent check)
- Don't over-invest in low-probability leads
- Track conversion probability

---

### A2: The Indecisive Customer ("The Revision Loop")

**Behavior**:
- Changes requirements daily
- "What about this? What about that?"
- 10+ revisions before booking
- Never satisfied with options

**Risk to Agency**:
- Time sink
- Agent burnout
- Opportunity cost (miss other leads)

**How System Handles**:
- Track revision count
- Charge planning fees after N revisions
- Flag for senior agent intervention
- Set clear decision deadlines

---

### A3: The Over-Confident ("The Ignorer")

**Behavior**:
- Ignores visa warnings
- Dismisses suitability concerns ("it'll be fine")
- Won't buy insurance
- Argues with expert advice

**Risk to Agency**:
- Disaster during trip = blame agency
- Liability issues
- Bad reviews despite warnings

**How System Handles**:
- Document warnings explicitly
- Require acknowledgment of risks
- Flag for legal/protection protocols
- Maybe refuse service for high-risk cases

---

## Stakeholder Matrix

| Persona | Power | Interest | Strategy |
|---------|-------|----------|----------|
| Solo Agent (P1) | High | High | **Primary user** - Design for them |
| Agency Owner (P2) | High | High | **Economic buyer** - Show ROI metrics |
| Junior Agent (P3) | Low | High | **Key beneficiary** - Make training easy |
| Traveler (S1) | Medium | High | **End customer** - Indirect, via agent |
| Family Coordinator (S2) | Medium | High | **Influencer** - Design for complex groups |
| Price Shopper (A1) | Low | Low | **Minimize** - Qualify out early |
| Indecisive (A2) | Low | Medium | **Manage** - Set boundaries |

---

## Key Insights for Scenario Design

1. **Primary focus**: Solo Agent (P1) - Most pain, highest leverage
2. **Secondary focus**: Junior Agent (P3) - Easiest adoption, tech comfort
3. **Economic buyer**: Agency Owner (P2) - Need business case
4. **Indirect beneficiary**: Travelers - Better service via agents

**Scenario creation priority**:
1. P1 scenarios (Solo agent daily work)
2. P2 scenarios (Owner oversight needs)
3. P3 scenarios (Training/onboarding)
4. S1/S2 scenarios (End customer impact)

---

*Next: Create detailed scenarios for each primary persona*
