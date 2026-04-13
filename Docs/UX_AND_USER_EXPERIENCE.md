# UX and User Experience: End-to-End Flow Analysis

**Date**: 2026-04-13
**Purpose**: Document what end users, visitors, and agents actually see and interact with
**Status**: Exploration - First pass at understanding the UX layer

---

## Executive Summary

This project is **B2B2C software**, not B2C. Travelers never touch the system directly. The system outputs shape what agents say to travelers via WhatsApp, email, and phone.

The UX challenge is designing for two distinct user groups:
1. **Agents** (P1, P2, P3) - Primary system users who see dashboards and make decisions
2. **Travelers** (S1, S2) - Secondary beneficiaries who receive crafted messages

**Exception**: Audit Mode is the only direct-to-consumer interaction, where travelers upload self-booked itineraries and receive waste analysis.

---

## The B2B2C Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TRAVELER LAYER (S1, S2)                            │
│  What they see: WhatsApp messages, email PDFs, document collection links   │
│  What they touch: Nothing in the system directly                           │
│  Their experience: Entirely mediated through human agent                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓ WhatsApp/Email/Phone
┌─────────────────────────────────────────────────────────────────────────────┐
│                           AGENT LAYER (P1, P2, P3)                          │
│  What they see: Dashboard, blockers, questions, recommendations             │
│  What they touch: Full system - intake, decision, strategy                │
│  Their experience: AI copilot suggesting next actions                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓ System prompts
┌─────────────────────────────────────────────────────────────────────────────┐
│                      SYSTEM ENGINE (NB01→NB02→NB03)                        │
│  Processes: Raw input → CanonicalPacket → Decision → Strategy             │
│  Outputs: Structured guidance for the agent                                │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Implications

1. **No traveler login**: Travelers don't have accounts. Their "identity" exists in the agent's customer database
2. **No traveler UI**: There's no app for travelers to download
3. **Agent is the interface**: The agent's judgment, tone, and relationship remain central
4. **System is copilot, not pilot**: Agent can override, edit, or ignore system suggestions

---

## Persona Experience Matrix

### P1: The Solo Agent

| Interaction | Current Reality | With System |
|-------------|----------------|-------------|
| **11 PM WhatsApp request** | Sets alarm for 6 AM, 2 hours research | System recognizes repeat customer, flags issues, pre-computes options overnight |
| **Repeat customer** | Scrolls WhatsApp chat to remember preferences | Auto-pulls profile with past trips, preferences, document status |
| **Customer changes everything** | Builds 4 different quotes, burns out | System tracks revisions, flags impossible budgets, suggests alternatives |
| **Visa problem discovered** | PANIC, may miss it until too late | Hard blocker enforcement, cannot proceed without passport verification |
| **Multi-party payment** | Excel tracking, constant updates | Per-family payment tracking, dependency gating, automated reminders |

**What P1 sees**:
- A single dashboard showing current customer state
- Blockers (hard/soft) with clear visual distinction
- Suggested questions ready to send
- Risk flags (budget feasibility, urgency, document gaps)
- Customer history sidebar (repeat customers only)

**What P1 doesn't see**:
- Raw JSON or CanonicalPacket structure
- Internal decision engine reasoning
- LLM prompts or system internals

---

### P2: The Agency Owner

| Interaction | Current Reality | With System |
|-------------|----------------|-------------|
| **Quality control** | Reviews every quote manually | Dashboard showing all active quotes with margin/quality flags |
| **Training new staff** | 3-6 months shadowing | System guides juniors with institutional knowledge |
| **Customer data scattered** | Knowledge leaves with agents | Centralized customer database with trip history |
| **Pipeline visibility** | "What's in the works?" | Real-time view of all deals, stages, probabilities |

**What P2 sees**:
- Agency-level dashboard with all agents' pipelines
- Margin risk flags across all quotes
- Training mode showing junior agent interactions
- Customer retention/churn metrics

**What P2 cares about**:
- Standardization across agents
- Margin protection
- Knowledge capture (so business doesn't leave with agents)
- Scaling without quality drop

---

### P3: The Junior Agent

| Interaction | Current Reality | With System |
|-------------|----------------|-------------|
| **First solo quote** | 2 hours research, anxiety | System suggests 3 options with rationale |
| **"Is this hotel good?"** | Asks senior repeatedly | System shows hotel history, suitability scores, past feedback |
| **Visa mistake** | Books without checking, disaster | Hard blockers prevent proceeding without documents |
| **Pricing doubt** | Undercuts margin | System flags margin risk, shows acceptable range |

**What P3 sees**:
- Same dashboard as P1 but with MORE guidance
- Confidence scoring (low = ask senior)
- "Why this recommendation" explanations
- Common mistakes flagged before sending

**What P3 needs**:
- Guardrails to prevent rookie mistakes
- Explanations, not just answers
- Progressive disclosure (more detail as they learn)
- Clear escalation paths

---

### S1: The Individual Traveler

**What they think is happening**: "I'm messaging my travel agent"
**What's actually happening**: Agent is using system to craft personalized responses

| Interaction | Current Reality | With System |
|-------------|----------------|-------------|
| **Initial inquiry** | 24-48 hour response, generic | 2-hour response, specific questions show expertise |
| **Receiving options** | 1 generic package | 3 clear options (budget/mid/luxury) with value breakdown |
| **Pre-trip anxiety** | Chases agent for confirmations | Automated 3-day-before with all documents in one message |
| **Trip emergency** | Agency closed, leaves voicemail | 24/7 automated triage + agent callback in 10 minutes |

**What S1 sees** (example WhatsApp flow):

```
[Day 0 - Initial message from Rahul]
Rahul: "Hi, planning anniversary trip with wife to Maldives, March 15-20, 2 people"

[2 hours later - via Agent, system-crafted]
Agent: "Hi Rahul! Congratulations on your anniversary! 🎉

I found 3 Maldives options for March 15-20:

🥉 BUDGET (₹2.2L)
• Hotel: Local island guesthouse
• Pros: Authentic experience, great reef
• Cons: No alcohol, basic amenities

🥈 RECOMMENDED (₹3.5L) ⭐
• Hotel: Adaaran Club (water villa)
• Pros: All-inclusive, house reef, spa
• Why this price: Water villa + transfers + meals

🥇 LUXURY (₹6L)
• Hotel: Soneva Fushi
• Pros: Private island, celebrity spot
• Best for: Once-in-a-lifetime

Quick questions:
1. Do you need alcohol? (Some islands are dry)
2. Is water villa important or beach villa OK?
3. Flights from Mumbai or Delhi?

I can hold Option 2 for 24 hours while you decide."

[Day 1 - Rahul responds]
Rahul: "Option 2 looks good. We don't drink. Water villa yes. Mumbai."

[Day 1 - Agent sends, system-generated]
Agent: "Perfect! I'm confirming your water villa at Adaaran Club.

This resort is great for couples - quiet, romantic, and the house reef
has some of the best snorkeling in Maldives.

Total: ₹3.5L including:
→ Flights: Mumbai-Male-Mumbai (SpiceJet morning departure)
→ Resort: 5 nights water villa, all-inclusive
→ Transfers: Speedboat (30 min each way)
→ Insurance: Travel insurance covered

Next steps:
1. I'll send payment link (50% to confirm booking)
2. Need passport copies for both travelers
3. I'll share detailed itinerary once confirmed

Does this work?"

[Day 3 - Pre-trip automated, 3 days before]
"Hi Rahul! 🇲🇻 Your Maldives trip is in 3 days!

✅ CONFIRMED:
   • Flight SG123: Mar 15, 6:30 AM (Gate 12)
   • Resort: Adaaran Club (Water Villa #42)
   • Return: SG124: Mar 20, 2:00 PM

📱 YOUR DOCUMENTS:
   [Flight Tickets] [Resort Voucher] [Insurance Policy]

⏰ REMINDERS:
   • Reach airport 3 hours early
   • Resort check-in: 2 PM (early check-in requested)
   • Speedboat transfer: Last boat 10 PM

❓ QUESTIONS? Reply here, we respond in 10 mins

Have an amazing anniversary! 🌴"
```

**Key UX pattern**: System generates, Agent edits, Traveler receives

---

### S2: The Family Coordinator

**What they think is happening**: "I'm coordinating my family's trip preferences"
**What's actually happening**: System provides tools to collect, analyze, and reconcile conflicting preferences

| Interaction | Current Reality | With System |
|-------------|----------------|-------------|
| **Collecting preferences** | Individual WhatsApps, confusion | Shared link with structured questions |
| **Conflicting needs** | Mom wants X, Dad wants Y, kids want Z | System detects conflicts, suggests compromise destinations |
| **Document collection** | Coordinator chases everyone personally | Automated reminders to each person, coordinator sees dashboard |
| **Budget reality** | "Around 5L for 6 people" (unrealistic) | System shows feasibility check upfront with alternatives |

**What S2 sees** (example preference collection):

```
[Coordinator shares link]
Mrs. Reddy in family WhatsApp: "Help me plan! Answer 5 quick questions: [link]"

[Each family member sees]
┌─────────────────────────────────────────────────────────────────────────────┐
│  REDDY FAMILY TRIP PLANNER                                                  │
│  Mrs. Reddy is planning a trip for everyone. Help by sharing your prefs!    │
└─────────────────────────────────────────────────────────────────────────────┘

1. PACE PREFERENCE:
   ○ Relaxed (lots of downtime, flexible schedule)
   ● Balanced (mix of activities and rest) [Selected]
   ○ Active (packed schedule, see everything)

2. MUST-HAVES (pick up to 3):
   ☑ History/Culture [Selected]
   ☐ Shopping
   ☐ Adventure activities
   ☑ Relaxation/Spa [Selected]
   ☑ Food experiences [Selected]
   ☐ Nightlife

3. TRAVEL STYLE:
   ○ Luxury (5-star, premium everything)
   ● Comfort (good hotels, not extravagant) [Selected]
   ○ Budget (clean, basic, stretch the budget)

4. DIETARY NEEDS:
   ● No restrictions [Selected]
   ○ Vegetarian
   ○ Vegan
   ○ Jain
   ○ Other: _______

5. MOBILITY CONSIDERATIONS:
   ○ Full mobility (can walk long distances)
   ● Some limitations (avoid excessive walking) [Selected]
   ○ Mobility assistance required

[SUBMIT]

[System aggregates and shows coordinator]
┌─────────────────────────────────────────────────────────────────────────────┐
│  FAMILY PREFERENCE ANALYSIS                                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  COMMON GROUND (everyone wants):                                           │
│  • Good food experiences                                                   │
│  • Some relaxation time                                                   │
│  • Comfort (not budget, not luxury)                                        │
│                                                                             │
│  CONFLICTS DETECTED:                                                       │
│  • Father: History + Slow pace                                             │
│  • Husband: Adventure + Nightlife                                          │
│  • Kids: Activities + Fun                                                  │
│  • Mother: Relaxation + Shopping + Food                                    │
│                                                                             │
│  SYSTEM RECOMMENDATION: Singapore                                          │
│  Why Singapore works for everyone:                                         │
│  • Father: Museums, heritage areas, Chinatown                              │
│  • Husband: Night Safari, adventure parks, Clarke Quay nightlife           │
│  • Kids: Universal Studios, water parks, Gardens by the Bay                │
│  • Mother: Orchard Road shopping, spa days, hawker food + fine dining      │
│  • Pace: Can be as active or relaxed as desired                            │
│                                                                             │
│  Alternative: Thailand (more adventure, less history)                      │
│  Alternative: Japan (great food, but more walking required)                │
│                                                                             │
│  [Show Singapore options] [Adjust preferences] [Share with family]         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Document collection dashboard** (S2 sees):

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  DOCUMENT COLLECTION STATUS                                                 │
│  Trip: Reddy Family to Singapore | Deadline: March 1 (15 days left)        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  FAMILY A - REDDY (4 people)                                               │
│  ✅ Mrs. Reddy: Passport uploaded Feb 15                                   │
│  ✅ Mr. Reddy: Passport uploaded Feb 15                                    │
│  ✅ Child 1: Passport uploaded Feb 16                                      │
│  ✅ Child 2: Passport uploaded Feb 16                                      │
│  COMPLETE ✅                                                                │
│                                                                             │
│  FAMILY B - KUMAR (3 people)                                               │
│  ✅ Mr. Kumar: Passport uploaded Feb 17                                    │
│  ✅ Mrs. Kumar: Passport uploaded Feb 17                                   │
│  ⚠️ Child: Photo blurry - resend requested Feb 18 (pending)                │
│  ACTION NEEDED: 1 document                                                 │
│                                                                             │
│  FAMILY C - SHAH (4 people)                                                │
│  ✅ Mr. Shah: Passport uploaded Feb 19                                     │
│  ⏳ Mrs. Shah: Reminder sent Feb 18 (2 days ago)                           │
│  ⏳ Child 1: Reminder sent Feb 18 (2 days ago)                             │
│  ⏳ Child 2: Reminder sent Feb 18 (2 days ago)                             │
│  ACTION NEEDED: 3 documents                                                │
│                                                                             │
│  ─────────────────────────────────────────────────────────────────────────  │
│  PROGRESS: 7/11 complete (64%)                                             │
│  BLOCKER: Cannot proceed to booking until 100% complete                    │
│                                                                             │
│  [Send bulk reminder] [Extend deadline] [View individual status]           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## The Traveler-Safe vs Internal Boundary

This is the **most critical UX concept** in the system. There's data the traveler should NEVER see:

### Internal-Only Data (Agent Dashboard)

| Data Type | Example | Why Hidden |
|-----------|---------|------------|
| Ambiguity flags | `destination: "Andaman or Sri Lanka"` | Shows system uncertainty |
| Blocker status | `hard_blocker: party_size missing` | Implementation detail |
| Contradictions | `budget_stated: 5L, budget_reality: 8L` | Could offend |
| Margin risk | `margin: -12% (this quote loses money)` | Commercial secret |
| Hypotheses | `hypothesis: customer is price-shopping` | Could be wrong, offensive |
| Authority levels | `source: derived_signal vs explicit_user` | Meaningless to traveler |
| Confidence scores | `confidence: 0.62 (low)` | Undermines trust |

### Traveler-Safe Transforms

| Internal State | Traveler Sees | Transformation |
|----------------|---------------|----------------|
| `destination_candidates: ["Andaman", "Sri Lanka"]` | "I'm researching both Andaman and Sri Lanka for you..." | Present as exploration, not confusion |
| `hard_blocker: party_size` | "Quick question: How many people are traveling?" | Natural conversation |
| `budget_feasibility: infeasible` | "Let's discuss options to make this work within budget" | Solution-focused |
| `margin_risk: HIGH` | "This option is premium. Would you like to see alternatives?" | Gentle framing |
| `urgency: HIGH` | "Since you're traveling soon, let's focus on getting this confirmed" | Helpful urgency |

### Structural Enforcement (P0 Priority)

From `SCENARIO_COVERAGE_GAPS.md` P0-5:

> **Current state**: The boundary is procedural (different functions), not enforced at type level
> **Risk**: A subtle leakage bug could ship to production — traveler sees "unknown", "hypothesis", "contradiction" — trust destroyed
> **Fix needed**: `is_internal` flag on every prompt block, enforced by builder

**Example leakage prevention**:

```python
@dataclass
class PromptBlock:
    content: str
    is_internal: bool  # MANDATORY flag
    keywords_blocked: List[str] = field(default_factory=lambda: [
        "unknown", "hypothesis", "contradiction", "blocker", "margin", "confidence"
    ])

    def validate_for_traveler(self) -> bool:
        if self.is_internal:
            raise ValueError("Internal block cannot be shown to traveler")
        for keyword in self.keywords_blocked:
            if keyword.lower() in self.content.lower():
                raise ValueError(f"Blocked keyword '{keyword}' in traveler-safe content")
        return True
```

---

## Audit Mode: The Direct-to-Consumer Exception

**This is the ONLY mode where travelers interact directly with the system.**

### User Flow

```
1. Traveler arrives via: Ad link, QR code, or referral
2. Sees landing page: "Upload your itinerary - find wasted spend"
3. Uploads: Screenshot, forwarded booking email, or text paste
4. System analyzes: Extracts components, runs suitability checks
5. Displays: Wasted spend breakdown, better alternatives, fit score
6. Call-to-action: "Get agency quote" or "Chat with expert" (lead capture)
```

### What Traveler Sees (Audit Mode UI)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  AUDIT YOUR TRIP                                                             │
│  Find wasted spend and poor-fit choices in your booking                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  [DROP ZONE]                                                                │
│  Upload your itinerary screenshot or booking confirmation                   │
│  Supported: Screenshot image, booking email, or paste text                  │
│                                                                             │
│  ──────────────── OR ────────────────                                       │
│  [PASTE YOUR BOOKING DETAILS]                                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

[After upload and analysis]

┌─────────────────────────────────────────────────────────────────────────────┐
│  AUDIT RESULTS                                                               │
│  Your trip: Universal Studios Singapore + Marina Bay Sands, 5 people        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  💰 WASTED SPEND DETECTED: ₹45,000 (28% of your trip)                       │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ Universal Studios Singapore                                           │ │
│  │ Your cost: ₹24,000 for 5 people                                       │ │
│  │ Problem: 3/5 people get low value                                     │ │
│  │   • Adults (2): 100% fit ✓                                            │ │
│  │   • Elderly (1): 30% fit - limited mobility, can't do rides           │ │
│  │   • Toddler (1): 20% fit - too young for most attractions             │ │
│  │                                                                        │ │
│  │ 💡 BETTER: Singapore Zoo + River Wonders (₹12,000)                    │ │
│  │    Everyone enjoys, 50% savings, same duration                       │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ Hotel: Marina Bay Sands (₹45,000 for 3 nights)                        │ │
│  │ Suitability: 60%                                                       │ │
│  │ Issues:                                                                │ │
│  │   • You wanted "relaxing family trip" - MBS is busy/clubby            │ │
│  │   • Pool requires booking, long queues                                │ │
│  │   • ₹15K/night premium for view you'll rarely enjoy                   │ │
│  │                                                                        │ │
│  │ 💡 BETTER: Shangri-La (₹28,000)                                      │ │
│  │    Family-friendly pools, garden access, calmer vibe                 │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  📊 OVERALL FIT SCORE: 62/100                                              │
│                                                                             │
│  Your trip has some great choices but significant optimization potential.  │
│                                                                             │
│  [Get agency quote to optimize] [Chat with expert] [Share results]         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Lead Capture Strategy

The audit mode serves as a **lead generation tool**:
- Traveler sees value immediately (wasted spend)
- Agency demonstrates expertise
- Clear path to "fix" the problems (book through agency)
- Contact captured before showing full results

---

## Decision State UX Mapping

Each NB02 decision state maps to a specific UX pattern:

| Decision State | Agent Action | Traveler Experience |
|----------------|--------------|---------------------|
| `ASK_FOLLOWUP` | System generates questions, agent edits/sends | Receives clarifying questions |
| `PROCEED_INTERNAL_DRAFT` | System generates options, agent reviews | Nothing yet (agent working) |
| `PROCEED_TRAVELER_SAFE` | System generates proposal, agent edits/sends | Receives structured options |
| `BRANCH_OPTIONS` | System shows paths, agent chooses | Receives "here are your options" |
| `STOP_NEEDS_REVIEW` | System flags crisis, agent calls personally | Agent calls (escalated treatment) |

### Flow Visualization

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CUSTOMER INQUIRY                                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                         NB01: INTAKE                                        │
│  Extract facts, detect ambiguities, build CanonicalPacket                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                         NB02: DECISION                                      │
│  Check blockers, feasibility, contradictions → Determine action            │
└─────────────────────────────────────────────────────────────────────────────┘
                    │                   │                   │
                    ↓                   ↓                   ↓
        ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐
        │   ASK_FOLLOWUP    │  │ PROCEED_..._SAFE  │  │  STOP_NEEDS_...   │
        │                   │  │                   │  │                   │
        │ Agent gets        │  │ System generates  │  │ Agent calls       │
        │ questions to ask  │  │ proposal options  │  │ customer directly │
        └───────────────────┘  └───────────────────┘  └───────────────────┘
                    │                   │                   │
                    └───────────────────┴───────────────────┘
                                        ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                         NB03: STRATEGY                                      │
│  Generate prompts, tone, traveler-safe transformations                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                         WHAT TRAVELER RECEIVES                              │
│  WhatsApp message, email PDF, document link, or phone call                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Operating Mode UX Variations

From `NB02_V02_SPEC.md`, operating modes change what the agent sees and does:

### Normal Intake Mode
- **Agent sees**: Standard blocker/question dashboard
- **Traveler receives**: Normal inquiry flow

### Audit Mode
- **Agent sees**: Value gap analysis, wasted spend flags
- **Traveler receives**: Comparison with their self-booked itinerary

### Emergency Mode
- **Agent sees**: Red UI, suppressed soft blockers, crisis protocols
- **Traveler receives**: "I'm calling you right now" + 24/7 support info
- **UX implication**: Speed over completeness, safety first

### Follow-Up Mode
- **Agent sees**: Engagement timeline, last contact date, nurture prompts
- **Traveler receives**: Gentle check-in, not sales-heavy

### Cancellation Mode
- **Agent sees**: Policy engine, refund calculator, insurance status
- **Traveler receives**: Clear options with financial implications

### Post-Trip Mode
- **Agent sees**: Review request timing, sentiment analysis, loyalty signals
- **Traveler receives**: "How was your trip?" at optimal time (day 3-5)

### Coordinator Group Mode
- **Agent sees**: Per-sub-group status, payment tracking, document collection
- **Traveler receives**: Coordinator-specific updates, individual reminders

### Owner Review Mode
- **Agent (owner) sees**: Commercial audit, margin flags, quality scores
- **UX implication**: Internal quality control, no traveler-facing output

---

## Wireframe Sketches: Agent Dashboard

### Main Dashboard Layout

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  AGENCY OS                                                                 [?] │
├─────────────────────────────────────────────────────────────────────────────────┤
│  Customers  Pipelines  Knowledge Base  Settings                               │
│  ─────────────────────────────────────────────────────────────────────────────  │
│                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────┐  │
│  │ CUSTOMER: Mrs. Sharma (Repeat)                   Last contact: 2 hrs ago  │  │
│  │ ────────────────────────────────────────────────────────────────────────  │  │
│  │                                                                          │  │
│  │ ┌────────────────────────────────────────────────────────────────────┐   │  │
│  │ │ PAST TRIPS                                                          │   │  │
│  │ │ • Singapore, Mar 2024 (4 people, 2.5L, "Loved Gardens by the Bay")  │   │  │
│  │ │ • Goa, Dec 2022 (4 people, 1.8L, "Beach resort, good food")        │   │  │
│  │ └────────────────────────────────────────────────────────────────────┘   │  │
│  │                                                                          │  │
│  │ ┌────────────────────────────────────────────────────────────────────┐   │  │
│  │ │ CURRENT INQUIRY                                                     │   │  │
│  │ │ • Destination: Europe (wants snow)                                  │   │  │
│  │ │ • Dates: June/July, 10-12 days                                      │   │  │
│  │ │ • People: 5 (2 adults, 2 kids ages 8+12, +1 elderly?)               │   │  │
│  │ │ • Budget: 4-5L                                                      │   │  │
│  │ │ • Special: Kids want snow, parents can't walk much                  │   │  │
│  │ └────────────────────────────────────────────────────────────────────┘   │  │
│  │                                                                          │  │
│  │ ┌────────────────────────────────────────────────────────────────────┐   │  │
│  │ │ SYSTEM ANALYSIS                                                      │   │  │
│  │ │ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐         │   │  │
│  │ │ │ STAGE      │ │ MODE       │ │ CONFIDENCE │ │ URGENCY    │         │   │  │
│  │ │ │ Discovery  │ │ Normal     │ │ 72%        │ │ 🔴 High    │         │   │  │
│  │ │ └────────────┘ └────────────┘ └────────────┘ └────────────┘         │   │  │
│  │ │                                                                      │   │  │
│  │ │ 🚫 HARD BLOCKERS (2) - Must resolve before proceeding:               │   │  │
│  │ │   ❌ destination_candidates: "Europe" too broad (need country)        │   │  │
│  │ │   ❌ party_size: "5 people" - need age details for 5th person        │   │  │
│  │ │                                                                      │   │  │
│  │ │ ⚠️  SOFT BLOCKERS (2) - Nice to have:                                 │   │  │
│  │ │   ⚠ budget_scope: Per person or total?                               │   │  │
│  │ │   ⚠ trip_purpose: Anniversary? Family vacation?                      │   │  │
│  │ │                                                                      │   │  │
│  │ │ 🔴 RISK FLAGS:                                                        │   │  │
│  │ │   • Budget feasibility: TIGHT (4-5L for 5 in Swiss peak is low)      │   │  │
│  │ │   • Urgency: High (June/Jul books fast, <3 months to plan)           │   │  │
│  │ │   • Passport: Unknown (check if valid from 2024 trip)                │   │  │
│  │ │                                                                      │   │  │
│  │ │ ▶ RECOMMENDED: ASK_FOLLOWUP                                          │   │  │
│  │ │    Rationale: Clear blockers before investing time in options        │   │  │
│  │ └────────────────────────────────────────────────────────────────────┘   │  │
│  │                                                                          │  │
│  │ ┌────────────────────────────────────────────────────────────────────┐   │  │
│  │ │ SUGGESTED QUESTIONS (ready to send via WhatsApp)                    │   │  │
│  │ │                                                                      │   │  │
│  │ │ "Hi Mrs. Sharma! Great to hear from you. I remember your family     │   │  │
│  │ │  loved Gardens by the Bay. Quick questions for the best options:"   │   │  │
│  │ │                                                                      │   │  │
│  │ │ 1. Is the 5th person a grandparent? (affects room accessibility)    │   │  │
│  │ │ 2. When you say 'snow' - do you mean see mountains or actually      │   │  │
│  │ │    play in snow? (Switzerland has both, different budgets)          │   │  │
│  │ │ 3. Is 4-5L per person or total for the family?"                     │   │  │
│  │ │                                                                      │   │  │
│  │ │ [Edit message] [Send via WhatsApp] [Copy to clipboard]              │   │  │
│  │ └────────────────────────────────────────────────────────────────────┘   │  │
│  │                                                                          │  │
│  │ ┌────────────────────────────────────────────────────────────────────┐   │  │
│  │ │ INTERNAL NOTES (agent only, never shared)                           │   │  │
│  │ │ • Switzerland recommended for snow, but 5-6L more realistic         │   │  │
│  │ │ • If budget is firm, consider Andaman (beach, domestic)             │   │  │
│  │ │ • Elderly mobility: prioritize hotels with lifts, less walking      │   │  │
│  │ │ • Past pattern: Willing to stretch for right option (did 2.5L→2.8L) │   │  │
│  │ └────────────────────────────────────────────────────────────────────┘   │  │
│  └──────────────────────────────────────────────────────────────────────────┘  │
│                                                                                  │
│  [New Customer] [Search] [Filter] [Sort by: Urgency ▼]                            │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Mobile Considerations

### Agent: Mobile-First Design

Agents work from phone (WhatsApp primary channel). Dashboard must work on mobile:

**Critical mobile features**:
- One-tap WhatsApp message send
- Swipe to mark follow-up done
- Push notifications for urgent blockers
- Offline mode for customer lookup
- Voice-to-text for quick notes

### Traveler: No App Needed

Travelers don't need an app. They interact through:
1. **WhatsApp**: Primary channel (questions, updates, documents)
2. **SMS**: For urgent alerts (flight delays, emergencies)
3. **Email**: For PDF documents (tickets, vouchers, policies)
4. **Web**: One-time document upload forms (no login)

**Key insight**: Meet travelers where they already are, don't ask them to download yet another app.

---

## Open Questions & Design Decisions Needed

### 1. Agent Review vs. Auto-Send
- **Question**: Should the system auto-send questions, or must agent always review?
- **Trade-off**: Speed vs. Control
- **Recommendation**: Agent review for first interaction, can enable auto-mode for trusted scenarios

### 2. Question Format
- **Question**: Structured form vs. natural language questions?
- **Trade-off**: Easy to aggregate vs. natural conversation
- **Recommendation**: Hybrid - natural language for traveler, system extracts structure

### 3. Document Collection UX
- **Question**: Agent sends link or automated system?
- **Trade-off**: Personal touch vs. automation
- **Recommendation**: Agent initiates, system handles reminders

### 4. Audit Mode Access
- **Question**: Public landing page or agent-shared links?
- **Trade-off**: Lead volume vs. lead quality
- **Recommendation**: Start with agent-shared links for qualified leads

### 5. Real-Time Updates
- **Question**: Live dashboard vs. batch updates?
- **Trade-off**: Fresh data vs. system load
- **Recommendation**: Real-time for blockers, batch for analytics

---

## Next Steps for UX Development

1. **Wireframe the agent dashboard** - Figma or equivalent
2. **Map all decision states to traveler outputs** - Template library
3. **Design the traveler-safe boundary enforcement** - Technical spec
4. **Prototype audit mode landing page** - User testing
5. **Document mobile interaction patterns** - WhatsApp-first design
6. **Create message template library** - For all common scenarios
7. **Design multi-party coordinator view** - Complex group management
8. **Plan onboarding flow** - How agents learn the system

---

## Related Documentation

- `Docs/personas_scenarios/STAKEHOLDER_MAP.md` - All personas defined
- `Docs/personas_scenarios/P1_SOLO_AGENT_SCENARIOS.md` - Solo agent workflows
- `Docs/personas_scenarios/S1S2_CUSTOMER_SCENARIOS.md` - Customer experience
- `Docs/personas_scenarios/SCENARIO_COVERAGE_GAPS.md` - Feature gaps by scenario
- `notebooks/NB02_V02_SPEC.md` - Decision logic that drives UX
- `specs/canonical_packet.schema.json` - Data structure backing all UX

---

*This document will evolve as we explore deeper. All design decisions should be traced back to persona needs documented in the personas_scenarios folder.*
