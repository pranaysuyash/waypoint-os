# Travel Agency Industry Roles & AI Agent Mapping

**Date**: 2026-04-23
**Purpose**: Comprehensive analysis of every role in the travel agency industry — what real people do, what the system currently implements, what it should implement, and how each maps to AI agents.
**Scope**: Full industry (boutique agencies, mid-size, DMCs, OTAs) with focus on the boutique/solo planner segment (the product's wedge).

---

## How to Read This Document

Each role is analyzed across five dimensions:

1. **The Real Job** — What this person actually does day-to-day in a travel agency. Tasks, decisions, tools, pressures.
2. **Industry Context** — How this role varies across agency sizes, geographies, and specializations. What certifications or qualifications exist.
3. **Current System Coverage** — What the codebase already implements that serves this role's functions. Specific files, functions, and capabilities.
4. **Gaps (What Should Exist)** — What this role needs that the system does NOT yet provide. Concrete, actionable gaps.
5. **AI Agent Specification** — What the AI agent for this role should look like: inputs, outputs, decision authority, escalation triggers, and boundaries.

---

## Role Taxonomy

The travel agency industry has a layered structure. Roles are organized from strategic/commercial (top) to operational execution (bottom):

```
TIER 1: LEADERSHIP & STRATEGY
├── Agency Owner / Principal
├── Operations Manager
└── Sales / Business Development Manager

TIER 2: TRIP PLANNING & CLIENT MANAGEMENT (Core)
├── Travel Consultant / Planner (Primary)
├── Senior / Specialist Planner
├── Destination Specialist
├── Corporate Travel Manager
└── Group / MICE Coordinator

TIER 3: SUPPLY CHAIN & COMMERCIAL
├── Procurement / Supplier Manager
├── Revenue / Pricing Analyst
├── DMC (Destination Management Company) Liaison
└── Wholesaler / Consolidator Account Manager

TIER 4: OPERATIONS & EXECUTION
├── Tour Guide / Local Expert
├── Visa / Documentation Specialist
├── Booking Coordinator / Ticketing Agent
├── Ground Operations / Transport Coordinator
└── In-Trip Concierge / Support

TIER 5: FINANCE & ADMINISTRATION
├── Finance / Accounts Manager
├── Insurance Coordinator
└── Compliance / Regulatory Officer

TIER 6: MARKETING & GROWTH
├── Marketing Manager
├── Customer Success / Relationship Manager
├── Social Media / Channel Manager
└── Referral / Partnership Coordinator
```

---

## TIER 1: LEADERSHIP & STRATEGY

---

### R01: Agency Owner / Principal

#### The Real Job

The agency owner is the business. In boutique agencies (1-5 people), the owner is simultaneously the CEO, senior planner, salesperson, finance head, and janitor. In mid-size agencies (5-20 people), the owner shifts toward strategic oversight but still handles high-value clients personally.

**Daily responsibilities:**
- **P&L ownership**: Track revenue, margins, costs. Know which trip types are profitable and which drain resources. Decide whether to accept a low-margin trip or decline it.
- **Client relationship management**: Personally handle VIP/repeat clients. These relationships are the agency's moat — the owner knows the family's preferences, dietary restrictions, past complaints, and budget sensitivities.
- **Supplier negotiation**: Negotiate commission rates with hotels, volume discounts with airlines, preferred rates with DMCs. These relationships are proprietary and directly affect margins.
- **Team oversight**: Assign leads to planners based on specialization and workload. Review proposals before they go to clients. Approve discounts or custom pricing.
- **Quality control**: The final check before a proposal reaches a client. Catches errors that could damage reputation — wrong dates, unsuitable hotels, missed visa requirements.
- **Strategic decisions**: Which destinations to specialize in. Whether to add corporate travel. Whether to hire another planner. When to raise prices.
- **Risk management**: When a trip goes wrong (missed flights, overbooking, natural disasters), the owner decides how to respond — absorb the cost, negotiate with suppliers, or pass costs to the client.
- **Business development**: Networking with hotel chains, attending travel expos, maintaining consortia memberships (TAAI, ASTA, IATA).

**Tools they use today:**
- WhatsApp (client communication, 60-70% of workflow)
- Phone calls (high-value clients, supplier negotiations)
- Excel/Google Sheets (revenue tracking, margin calculations)
- Email (formal proposals, supplier confirmations)
- Memory (client preferences, supplier reliability, seasonal patterns)
- Sometimes a CRM (Zoho, HubSpot) — but rarely used consistently

**Key pressures:**
- Revenue concentration: Top 20% of clients generate 80% of revenue. Losing one is catastrophic.
- Knowledge trapped in their head: If the owner is unavailable, the agency cannot function.
- Margin squeeze: OTAs and direct booking make it harder to justify commission-based pricing.
- Seasonality: Revenue is lumpy. Good months must cover bad months.
- Trust dependency: The entire business model is built on the owner's personal credibility.

**Certifications/qualifications:**
- IATA accreditation (required for airline ticketing in many markets)
- TAAI/ASTA membership (industry body credibility)
- Destination certifications (Australia Specialist, Switzerland Expert, etc.)
- No formal degree required — the industry runs on relationships and experience

#### Industry Context

In India specifically (the product's primary market):
- Most boutique agencies are family-run businesses with 1-3 employees
- The owner typically has 10-20 years of industry experience, often starting as a counter agent
- Cash flow management is a constant concern — clients want credit, suppliers want advance payment
- Seasonal peaks (summer holidays, Diwali, Christmas) drive 60-70% of annual revenue
- WhatsApp is the primary business tool, not email
- Many owners resist technology adoption — they've run the business on relationships and paper for decades

In the broader global market:
- Agency consolidation is accelerating — small agencies are being acquired by larger groups
- Commission rates from airlines have dropped to near-zero; hotels and packages are the margin drivers
- Boutique agencies survive by offering what OTAs cannot: personalization, trust, and handling complexity
- The "solo planner" segment is growing — former travel agents starting their own micro-agencies

#### Current System Coverage

| Capability | Implementation | Location |
|---|---|---|
| Override/approval authority | Owner can override any decision, with audit trail | `src/analytics/review.py`, OverrideModal frontend |
| Autonomy policy configuration | Per-agency rules for what requires owner approval | `src/intake/config/agency_settings.py` |
| Review workflow | Pending reviews queue with approve/reject/escalate actions | `spine_api/server.py` review endpoints, `/owner/reviews` page |
| Margin calculation | Risk-adjusted fee calculation with multipliers | `src/fees/calculation.py` |
| Dashboard overview | Pipeline funnel, SLA tracking, trip counts by stage | `src/services/dashboard_aggregator.py`, Dashboard page |
| Timeline with provenance | Full audit trail of every decision and who made it | `src/analytics/logger.py`, TimelinePanel |
| Agency settings | Brand tone, target margin, approval gates | Settings page, agency_settings.db |
| Multi-tenant awareness | Architecture supports multiple agencies | `spine_api/` tenant model, auth system |

#### Gaps (What Should Exist)

| Gap | Severity | Description |
|---|---|---|
| **No P&L view** | P0 | Owner cannot see revenue, margins, or profitability across trips. No financial dashboard. |
| **No client memory** | P0 | System treats every trip as isolated. No cross-trip traveler profile, preference history, or lifetime value tracking. |
| **No team performance** | P1 | Cannot see which planner converts leads, how fast they respond, or their client satisfaction scores. |
| **No lead pipeline** | P1 | No visibility into leads that are cooling, ghosting, or about to close. No conversion funnel. |
| **No supplier management** | P1 | Cannot manage preferred supplier list, track commission rates, or score vendor reliability. |
| **No business intelligence** | P2 | No seasonal trends, destination popularity, or pricing optimization recommendations. |
| **No strategic alerting** | P2 | No alerts for "margin dropping below threshold," "lead volume down this month," or "top client hasn't booked in 6 months." |
| **No delegation controls** | P1 | Cannot configure which decisions auto-proceed and which always require owner review. Current autonomy policy exists but is coarse. |
| **No scenario planning** | P2 | Cannot model "what if I raise prices 10%" or "what if I drop budget trips." |

#### AI Agent Specification: `OwnerAgent`

**Role**: Strategic oversight and approval authority. Does NOT plan trips. Reviews, approves, intervenes.

**Inputs:**
- Aggregated pipeline metrics (trips by stage, conversion rates, SLA breaches)
- Financial summary (revenue, margins, outstanding payments)
- Risk escalations from all other agents
- Override requests from planners
- Lifecycle signals (churn risk, ghost risk, repeat likelihood)

**Outputs:**
- Approval/rejection/escalation decisions on proposals
- Margin override authorizations
- Strategic recommendations ("Top 3 destinations to push this quarter")
- Alert summaries ("3 VIP clients haven't booked in 4 months")
- Team performance reports

**Decision Authority:**
- **Full authority**: Approve/reject any proposal, set pricing policy, configure autonomy rules
- **Escalation receiver**: All agents escalate unresolvable situations to OwnerAgent
- **Override power**: Can override any other agent's decision, with mandatory rationale logged

**Escalation Triggers (receives from others):**
- Margin below configured threshold
- Risk score CRITICAL on any trip
- Client complaint or dispute
- New lead from VIP/repeat client
- Planner requesting exception to policy

**Boundaries:**
- Does not plan trips or interact directly with travelers
- Does not modify canonical packet facts
- Does not make commercial commitments without human confirmation
- All override decisions are logged with rationale

---

### R02: Operations Manager

#### The Real Job

In agencies with 3+ planners, the operations manager is the air traffic controller. They ensure trips move through the pipeline efficiently, nothing falls through the cracks, and resources are allocated optimally.

**Daily responsibilities:**
- **Lead assignment**: Receive new leads and assign them to the right planner based on specialization, workload, and client profile. A family-with-toddler lead goes to the planner who handles family trips, not the adventure specialist.
- **Pipeline monitoring**: Track where every trip is in the lifecycle. Flag trips that are stuck (lead assigned but no response in 4 hours, proposal sent but no follow-up in 48 hours).
- **SLA enforcement**: Ensure first response within a defined window, proposal delivery within agreed timeline, booking confirmations sent on time.
- **Quality spot-checks**: Review a sample of outgoing proposals to ensure quality standards. Catch errors before clients see them.
- **Escalation handling**: When a planner is stuck (complex itinerary, difficult client, supplier issue), the ops manager steps in or reassigns.
- **Workload balancing**: Prevent any single planner from being overloaded while others are idle. Redistribute during peak season.
- **Process compliance**: Ensure all planners follow the agency's standard operating procedures (SOPs) — intake forms, proposal templates, confirmation checklists.
- **Reporting**: Generate weekly/monthly reports on pipeline velocity, conversion rates, team productivity.

**Tools they use today:**
- Whiteboard/Excel (lead tracking)
- WhatsApp group with planners (coordination)
- Mental tracking ("I know Rahul has 5 active trips and Priya has 3")
- Occasional Trello/Asana board (rarely maintained consistently)

**Key pressures:**
- Visibility gap: Cannot see real-time status of all trips without asking each planner
- Bottleneck detection: By the time they realize a trip is stuck, the client is already annoyed
- No data: Most decisions are gut-feel because there's no tracking system
- Peak season chaos: During summer holidays, the volume doubles but the team doesn't

#### Current System Coverage

| Capability | Implementation | Location |
|---|---|---|
| Trip assignment | Trips can be assigned to users | `spine_api/persistence.py` AssignmentStore |
| Assignment API | GET /api/assignments endpoint | `spine_api/server.py` |
| SLA breach detection | New >4h and Assigned >24h thresholds | `src/services/dashboard_aggregator.py` |
| Pipeline state | Trip counts by stage | `src/services/dashboard_aggregator.py` |
| Inbox with filters | Filter by stage, priority, SLA, role | `/inbox` page, InboxFilterBar |
| Orphan detection | Trips with no assignment | `src/services/dashboard_aggregator.py` |

#### Gaps (What Should Exist)

| Gap | Severity | Description |
|---|---|---|
| **No auto-assignment** | P1 | Leads are not automatically routed to appropriate planners based on specialization or workload. |
| **No workload dashboard** | P1 | Cannot see how many active trips each planner has, their capacity, or utilization rate. |
| **No pipeline velocity metrics** | P1 | Cannot measure time-in-stage or identify where trips get stuck. Metrics exist but use simulated data. |
| **No escalation triggers** | P1 | No automatic escalation when a trip exceeds SLA threshold or a planner goes unresponsive. |
| **No process compliance checks** | P2 | No verification that planners followed intake procedure, sent proposals on time, or captured all required fields. |
| **No capacity planning** | P2 | Cannot predict staffing needs based on seasonal patterns or current pipeline volume. |

#### AI Agent Specification: `OrchestratorAgent`

**Role**: Pipeline coordination, assignment, monitoring, and escalation.

**Inputs:**
- New lead events (from intake)
- Trip stage transitions
- Planner workload data (active trips, capacity)
- SLA thresholds (configurable per agency)
- Planner specialization profiles

**Outputs:**
- Lead-to-planner assignment recommendations (with rationale)
- Pipeline health alerts (stuck trips, SLA breaches, orphan trips)
- Workload rebalancing suggestions
- Escalation packets to OwnerAgent when thresholds exceeded
- Weekly pipeline velocity reports

**Decision Authority:**
- **Auto-assign leads** based on planner specialization and workload (if autonomy policy allows)
- **Flag** trips that exceed SLA thresholds
- **Escalate** to OwnerAgent when auto-assignment fails or thresholds are critically exceeded
- **Monitor** all pipeline transitions for anomalies

**Escalation Triggers:**
- No planner available for assignment
- Trip stuck in same stage > configured threshold
- Planner unresponsive > 24h
- Multiple trips hitting SLA breach simultaneously (capacity crisis)

---

### R03: Sales / Business Development Manager

#### The Real Job

In boutique agencies, the owner IS the sales manager. In mid-size agencies, this is a dedicated role focused on growing the client base and revenue.

**Daily responsibilities:**
- **Lead generation**: Drive new inquiries through marketing channels (social media, referrals, partnerships, expos).
- **Lead qualification**: Assess whether an inquiry is a real prospect (dates, budget, group size) or a tire-kicker. Prioritize high-value leads.
- **Conversion optimization**: Analyze why leads don't convert. Is it pricing? Response time? Proposal quality?
- **Partnership development**: Build relationships with corporate HR departments, wedding planners, event companies, or other referral sources.
- **CRM management**: Maintain lead database, track touchpoints, schedule follow-ups.
- **Revenue forecasting**: Predict monthly/quarterly revenue based on pipeline state and historical patterns.
- **Competitive monitoring**: Track what competitors are offering, pricing changes, new destinations.

**Key pressures:**
- Lead quality varies wildly — 80% of inquiries never book
- No systematic way to score leads or prioritize effort
- Follow-ups are inconsistent — busy weeks mean warm leads go cold
- Attribution is impossible — did that lead come from Instagram, a referral, or the Google ad?

#### Current System Coverage

| Capability | Implementation | Location |
|---|---|---|
| Lead lifecycle state machine | NEW_LEAD through LOST/REPEAT_BOOKED | `Docs/LEAD_LIFECYCLE_AND_RETENTION.md`, `src/intake/packet_models.py` LifecycleInfo |
| Intent scoring | Ghost risk, window-shopper risk, repeat likelihood, churn risk | `src/intake/decision.py` (NB02 deterministic scoring) |
| Commercial decision routing | SEND_FOLLOWUP, SET_BOUNDARY, REQUEST_TOKEN, MOVE_TO_NURTURE, etc. | `Docs/LEAD_LIFECYCLE_AND_RETENTION.md` |
| Revenue metrics (partial) | Revenue data structures exist | `src/analytics/models.py` |
| Follow-up generation | Strategy produces follow-up prompts | `src/intake/strategy.py` |

#### Gaps (What Should Exist)

| Gap | Severity | Description |
|---|---|---|
| **No lead scoring UI** | P1 | Intent scores exist in backend but are not surfaced in a usable lead scoring dashboard. |
| **No follow-up automation** | P1 | Commercial decisions (SEND_FOLLOWUP, MOVE_TO_NURTURE) are computed but not automatically scheduled or executed. |
| **No lead source tracking** | P2 | Cannot track where leads come from or which channels convert best. |
| **No pipeline forecasting** | P2 | Cannot predict revenue based on current pipeline state. |
| **No conversion funnel** | P2 | Cannot see drop-off rates at each pipeline stage. |

#### AI Agent Specification: `SalesAgent`

**Role**: Lead intelligence, conversion optimization, and commercial lifecycle management.

**Inputs:**
- New lead events with extracted traveler profile
- Lifecycle intent scores (ghost, window-shopper, churn)
- Commercial decision outputs from NB02
- Historical conversion data (once available)
- Channel/source attribution data

**Outputs:**
- Lead priority scores and ranking
- Recommended next action per lead (with timing)
- Follow-up message drafts (personalized)
- Conversion funnel analytics
- Revenue forecasts (simple models)

**Decision Authority:**
- **Score and rank** all active leads
- **Recommend** follow-up timing and content
- **Auto-draft** follow-up messages for planner review
- **Flag** high-value leads for immediate attention
- **Move** leads to nurture/lost states based on scoring thresholds

---

## TIER 2: TRIP PLANNING & CLIENT MANAGEMENT

---

### R04: Travel Consultant / Planner (Primary Role)

#### The Real Job

This is the heart of the agency. The travel consultant (also called "travel agent," "planner," or "consultant") is the person who turns a messy client conversation into a bookable trip. In boutique agencies, this IS the owner.

**Daily responsibilities:**

**1. Client Intake (30-40% of time)**
- Receive inquiries via WhatsApp, phone, email, walk-in, or social media
- Extract key facts: destination (or "somewhere nice"), dates (or "flexible"), budget (or "reasonable"), group composition, special needs
- Identify hidden constraints that clients don't mention: elderly parents with knee issues, a toddler who needs nap time, vegetarian food requirements, fear of water
- Assess client sophistication: first-time traveler vs. seasoned explorer — determines how much guidance they need
- Build rapport: This is a trust business. The client is sharing personal information (budget, family situation, preferences)

**2. Research & Planning (30-40% of time)**
- Check internal packages first: "Do we have a Singapore package that fits this profile?"
- Search preferred suppliers: "Which of our partner hotels in Bali are family-friendly?"
- Check feasibility: "Can you actually do 5 cities in 7 days with a 2-year-old?" (Answer: No)
- Budget decomposition: "2.5 lakh for a family of 4 to Europe for 10 days — is this realistic?" (Break down: flights 1L, hotels 80K, activities 30K, food 25K, buffer 15K)
- Handle ambiguity: "We want something adventurous but not too adventurous" — translate vague intent into concrete options
- Compare options: Build 2-3 variants (budget-friendly, balanced, premium) with trade-offs clearly explained

**3. Proposal Creation (15-20% of time)**
- Create itinerary documents (often in Word/PDF or PowerPoint)
- Include day-by-day breakdown, hotel options, activity recommendations, pricing breakdown
- Write "why this fits your family" personalization narrative
- Prepare internal notes: actual costs, margins, risks, assumptions

**4. Revision Handling (10-15% of time)**
- Client wants to change dates, swap a hotel, add a city, adjust budget
- Track what changed and why — critical for avoiding scope creep
- Re-evaluate feasibility after changes
- Manage expectations: "If we add Phuket, we lose a day in Bangkok and the budget goes up by 40K"

**5. Client Communication (ongoing)**
- WhatsApp messages throughout the day
- Regular updates during planning
- Setting expectations on timeline, pricing, documentation

**Key skills:**
- Empathy and active listening (extracting unstated needs)
- Geographic knowledge (destinations, logistics, seasonal patterns)
- Commercial awareness (margins, supplier relationships, upselling)
- Crisis management (when things go wrong during a trip)
- Documentation management (visas, insurance, confirmations)

**Key pressures:**
- Repetitive work: 70% of trip planning is the same research and documentation work
- Knowledge asymmetry: Senior planners are 3-5x faster than juniors because they "just know" things
- Error risk: A single missed visa requirement or wrong date can cost thousands and destroy trust
- Scope creep: Clients keep changing their minds; each change requires rework
- Time pressure: Clients expect rapid responses; slow response = lost lead

#### Current System Coverage

This is the most heavily served role in the system. The entire NB01→NB02→NB03 pipeline is built for this role.

| Capability | Implementation | Location |
|---|---|---|
| **Intake extraction** | Pattern-based extraction from freeform text: destinations, dates, budgets, party composition, constraints, intent | `src/intake/extractors.py` (1300+ lines) |
| **Geography validation** | 590K+ city database, country detection, origin/destination classification | `src/intake/geography.py` |
| **Normalization** | Currency (L/K/Lakh→INR), dates, city names, urgency detection | `src/intake/normalizer.py` |
| **Contradiction detection** | Identifies conflicting client requirements | `src/intake/decision.py` |
| **Budget feasibility** | Per-destination cost tables (25+ destinations), budget decomposition into cost buckets | `src/intake/decision.py` |
| **Activity suitability** | Tier 1 (deterministic rules) + Tier 2 (coherence checks) for per-person activity fit | `src/suitability/` (6 files) |
| **Risk flagging** | Elderly mobility, toddler pacing, visa timeline, margin risk, coordination risk | `src/intake/decision.py` |
| **Strategy generation** | Conversation strategy, tone scaling, follow-up question priority, prompt bundles | `src/intake/strategy.py` |
| **Traveler-safe output** | Sanitization layer stripping internal-only data, leakage detection | `src/intake/safety.py` |
| **Decision engine** | Hybrid rule + LLM + cache for cost optimization | `src/decision/` (13 files) |
| **Canonical packet** | Single source of truth with provenance, authority levels, mutation audit trail | `src/intake/packet_models.py` |
| **Session strategy** | Operating-mode-specific goals, openings, exit criteria | `src/intake/strategy.py` |
| **Workbench UI** | 5-tab view: Intake, Decision, Strategy, Safety, Flow | `app.py` (Streamlit) |
| **Workspace UI** | Per-trip deep views: intake, packet, decision, strategy, safety, output, timeline, suitability | 10+ Next.js pages |
| **Lifecycle scoring** | Ghost risk, window-shopper risk, repeat likelihood | `src/intake/decision.py` |
| **Fee calculation** | Risk-adjusted pricing by service type | `src/fees/calculation.py` |

#### Gaps (What Should Exist)

| Gap | Severity | Description |
|---|---|---|
| **No itinerary generation** | P0 | System extracts constraints and flags risks but does NOT generate actual day-by-day itineraries. The planner still builds these manually. |
| **No option generation** | P0 | System identifies problems but does not propose solutions. "Budget too low for Europe" — but no alternative destinations suggested. |
| **No hotel/activity recommendation** | P0 | No integration with hotel databases or activity catalogs beyond the 18 static activities in suitability. Planner cannot search for "family-friendly hotel in Bali under $100." |
| **No proposal builder** | P0 | No document generation for client-facing proposals. Planners still create these in Word/Canva manually. |
| **No multi-turn conversation** | P1 | Pipeline is single-turn: input → processing → output. Cannot maintain context across a multi-day WhatsApp conversation. |
| **No internal package matching** | P1 | Cannot match client requirements against the agency's own pre-built packages. No package database. |
| **No preferred supplier search** | P1 | Cannot search the agency's preferred supplier network. No vendor database with suitability tags, commission rates, or reliability scores. |
| **No revision tracking** | P1 | Cannot track what changed between proposal v1 and v2, or why. Change history exists for packet fields but not for proposal iterations. |
| **No client communication channel** | P2 | No integrated messaging. Planner copies from dashboard to WhatsApp manually. |
| **No trip template library** | P2 | Cannot save successful itineraries as reusable templates. Each trip starts from scratch. |

#### AI Agent Specification: `PlanningAgent`

**Role**: The core trip planning intelligence. Takes extracted constraints and generates actionable options.

This is the most critical agent — it represents the majority of the planner's cognitive work.

**Inputs:**
- CanonicalPacket (from IntakeAgent)
- DecisionResult (from QualityGateAgent)
- Agency's package library (future)
- Preferred supplier database (future)
- Historical trip data (future)

**Outputs:**
- 2-3 ranked itinerary options with day-by-day breakdown
- Per-option trade-off analysis (cost vs. comfort vs. pace)
- Hotel recommendations per destination with suitability tags
- Activity recommendations per day with per-person utility scores
- Internal notes: cost breakdown, margin calculation, risk assessment, assumptions
- Client-facing proposal draft (traveler-safe)

**Decision Authority:**
- **Generate** itinerary options within confirmed constraints
- **Rank** options using multi-factor scoring (traveler fit, operational fit, commercial fit)
- **Recommend** preferred option with rationale
- **Flag** when constraints are too tight for viable options
- **Suggest** constraint relaxation ("If budget increases by 20%, you unlock significantly better options")

**Escalation Triggers:**
- No viable options within stated constraints
- Contradictory hard constraints (cannot be resolved)
- Client profile unusual/rare (no historical reference)
- Margin below configured threshold

**Boundaries:**
- Cannot override hard constraints stated by traveler
- Cannot commit to pricing without supplier confirmation
- Cannot book anything — only recommend
- All outputs marked with confidence levels and assumptions

---

### R05: Senior / Specialist Planner

#### The Real Job

The senior planner handles what junior planners cannot: complex multi-city itineraries, special needs travelers, high-value clients, and crisis situations. They also review junior planners' work.

**Daily responsibilities:**
- **Complex case handling**: Multi-country itineraries, special dietary/medical needs, large groups with conflicting preferences, ultra-luxury requirements
- **Quality review**: Review proposals created by junior planners before they reach clients. Check for feasibility errors, missed constraints, pricing accuracy, and presentation quality
- **Mentorship**: Train junior planners on destination knowledge, supplier relationships, and client management
- **Escalation resolution**: When a junior planner encounters a situation they can't handle, the senior planner steps in
- **Knowledge documentation**: Maintain the agency's "playbook" — destination notes, supplier reviews, client handling tips
- **Crisis management**: Handle in-trip emergencies — missed connections, overbooked hotels, natural disasters, medical emergencies

**Key difference from primary planner:**
- Judgment over process: Junior planners follow templates; senior planners know when to break the rules
- Supplier relationships: They know which hotel manager to call for an upgrade, which DMC responds fastest
- Pattern recognition: "This client profile looks exactly like the Sharma family trip that went wrong last year — let me check what happened"

#### Current System Coverage

| Capability | Implementation | Location |
|---|---|---|
| Quality gates | NB01 and NB02 gates enforce data quality and decision quality | `src/intake/gates.py` |
| Contradiction detection | Identifies conflicting requirements | `src/intake/decision.py` |
| Confidence scoring | Data quality, judgment confidence, commercial confidence scores | `src/intake/decision.py` |
| Review workflow | Owner/senior can review and approve/reject proposals | `src/analytics/review.py` |
| Suitability flags | Per-person activity suitability assessment | `src/suitability/` |

#### Gaps (What Should Exist)

| Gap | Severity | Description |
|---|---|---|
| **No pattern matching** | P1 | Cannot detect "this looks like a past failed trip pattern" or "this client profile matches 3 successful past trips." |
| **No knowledge base** | P1 | No system to store and retrieve tribal knowledge ("Hotel X has tiny rooms but amazing breakfast"). |
| **No peer review workflow** | P2 | No structured review flow where junior proposals go to seniors. Current review is owner-only. |
| **No past trip reference** | P2 | Cannot search past trips by similarity to current case. |

#### AI Agent Specification: `QualityGateAgent`

**Role**: Quality enforcement, pattern detection, and senior review function.

**Inputs:**
- Proposed itinerary/planning output
- Historical trip outcomes (success/failure patterns)
- Quality rubrics (configurable per agency)
- Contradiction and feasibility reports from NB02

**Outputs:**
- Quality score with dimension breakdown (feasibility, suitability, commercial, presentation)
- Pattern matches ("Similar to 3 past trips — 2 succeeded, 1 failed due to budget overrun")
- Specific improvement suggestions
- Approval/rejection/revision-needed verdict

**Decision Authority:**
- **Block** proposals that fail quality thresholds
- **Suggest** improvements for proposals that are close but not ready
- **Approve** proposals that meet all quality criteria
- **Escalate** to OwnerAgent for borderline cases

---

### R06: Destination Specialist

#### The Real Job

A destination specialist has deep, often firsthand knowledge of a specific region. They know which beach in Bali is clean, which street in Bangkok has the best street food, which month to avoid Dubai, and how to get from Kyoto to Osaka efficiently.

**Daily responsibilities:**
- **Geographic expertise**: Know logistics, seasons, cultural nuances, hidden gems, and tourist traps for their region
- **Itinerary refinement**: Take a generic itinerary and make it destination-specific — add local restaurants, optimize transport, suggest off-peak timing
- **Supplier relationships**: Know the reliable local operators, guides, and transport providers
- **Risk assessment**: "Monsoon season in Kerala starts in June — this outdoor-heavy itinerary will be miserable"
- **Client education**: Explain cultural norms, visa requirements, health precautions, packing suggestions
- **Pricing calibration**: Know actual costs on the ground, not just published rates

**In boutique agencies:**
- This role is usually combined with the primary planner — one person specializes in 3-5 destinations
- Knowledge is almost entirely in the planner's head
- There is no documentation — just years of experience and personal notes

**In larger agencies:**
- Dedicated destination teams (e.g., "Europe Desk," "Southeast Asia Desk")
- Shared knowledge bases (rarely maintained)
- Regular training from tourism boards

#### Current System Coverage

| Capability | Implementation | Location |
|---|---|---|
| Destination detection | Geography database with 590K+ cities, country detection | `src/intake/geography.py` |
| Budget feasibility tables | Per-destination cost benchmarks (25+ destinations) | `src/intake/decision.py` |
| Season/risk awareness | Basic risk flags for visa timeline, weather-sensitive activities | `src/intake/decision.py` |

#### Gaps (What Should Exist)

| Gap | Severity | Description |
|---|---|---|
| **No destination knowledge base** | P0 | No structured database of destination-specific logistics, seasons, cultural notes, or local tips. |
| **No seasonal calendars** | P1 | No automated seasonality checks (monsoon, peak tourist, festival seasons). Planner must remember these. |
| **No local logistics engine** | P1 | Cannot compute transfer times, suggest optimal routing between activities, or flag transport gaps. |
| **No destination risk database** | P1 | No database of destination-specific risks (political instability, health advisories, safety ratings). |
| **No cultural guidance** | P2 | No automated cultural tips (tipping norms, dress codes, religious holidays affecting services). |

#### AI Agent Specification: `DestinationExpertAgent`

**Role**: Deep geographic intelligence for specific destinations.

**Inputs:**
- Destination(s) from CanonicalPacket
- Travel dates
- Group profile (ages, mobility, dietary restrictions)
- Budget range
- Activity preferences

**Outputs:**
- Season-specific recommendations and warnings
- Day-by-day logistics optimization (activity ordering, transfer times)
- Local tips and cultural guidance
- Risk assessment specific to destination + dates + group profile
- Cost calibration (actual vs. published rates)

**Decision Authority:**
- **Flag** destinations as inadvisable for given dates/group
- **Optimize** itinerary logistics within a destination
- **Recommend** specific areas/neighborhoods for accommodation
- **Override** generic recommendations with destination-specific knowledge

---

### R07: Corporate Travel Manager

#### The Real Job

Corporate travel is a different business from leisure travel. The corporate travel manager manages business trips for companies — flights, hotels, visas, expense reporting, and policy compliance.

**Daily responsibilities:**
- Policy enforcement: Ensure employees book within company travel policy (hotel grade, flight class, advance booking requirements)
- Cost optimization: Negotiate corporate rates, manage unused tickets, optimize routing
- Duty of care: Know where all traveling employees are at any time; handle emergencies
- Expense management: Ensure proper documentation for reimbursement and tax compliance
- Reporting: Monthly travel spend analysis, vendor performance, policy compliance rates

**Relevance to this product:** LOW for current scope. Corporate travel is fundamentally different from leisure/custom travel. This role is mentioned for completeness and future roadmap consideration.

#### Current System Coverage

None. The system is designed for leisure/custom travel planning, not corporate travel management.

#### AI Agent Specification

**Status**: NOT RECOMMENDED for current build. Corporate travel requires:
- GDS integration (mandatory)
- Policy engine (mandatory)
- Expense management integration
- Duty-of-care tracking
- Fundamentally different workflow

**Future consideration**: If the platform expands to agencies that serve both leisure and corporate clients, a `CorporateTravelAgent` would handle policy compliance, corporate rate management, and business trip optimization.

---

### R08: Group / MICE Coordinator

#### The Real Job

MICE = Meetings, Incentives, Conferences, Exhibitions. This specialist handles group travel for corporate events, weddings, school trips, and other large-group scenarios.

**Daily responsibilities:**
- Group logistics: Coordinate travel for 20-500 people with varying requirements
- Venue sourcing: Find hotels/convention centers with appropriate capacity and facilities
- Budget management per person vs. total
- Dietary/accommodation matrix: Track individual requirements within the group
- Supplier negotiation: Volume-based pricing for flights, hotels, transfers
- Timeline management: Complex dependency chains (venue must be confirmed before catering, etc.)
- On-site coordination: Ensure everything runs during the event

**Relevance to this product:** MEDIUM. Some boutique agencies handle small group travel (10-30 people for family reunions, destination weddings). The current system does not support this, but the constraint satisfaction engine could be extended.

#### Current System Coverage

| Capability | Implementation | Location |
|---|---|---|
| Multi-party support | Sub-groups within CanonicalPacket | `src/intake/packet_models.py` SubGroup |
| Per-person suitability | Individual activity scoring | `src/suitability/` |

#### Gaps

- No group size tracking or management
- No per-person budget decomposition
- No venue/hotel capacity matching
- No group-specific logistics (bulk transport, shared transfers)
- No volume pricing models

#### AI Agent Specification

**Status**: DEFERRED. Add when agencies request group travel support. Would extend the PlanningAgent with group-specific logic.

---

## TIER 3: SUPPLY CHAIN & COMMERCIAL

---

### R09: Procurement / Supplier Manager

#### The Real Job

This role builds and maintains the agency's supply network — the preferred hotels, transport providers, tour operators, and guides that the agency uses repeatedly. In boutique agencies, this is the owner.

**Daily responsibilities:**
- **Supplier onboarding**: Evaluate new hotels, transport companies, and activity providers. Negotiate rates, commission structures, and service level agreements.
- **Rate management**: Track contracted rates vs. published rates. Know the margin on every supplier. Update rates seasonally.
- **Relationship maintenance**: Regular contact with supplier partners. Resolve disputes. Ensure preferred treatment for the agency's clients.
- **Quality monitoring**: Track supplier performance — response time, booking accuracy, client complaints, overbooking incidents. Drop underperformers.
- **Contract management**: Maintain contracts, commission agreements, and cancellation policies for each supplier.
- **Rate comparison**: Compare preferred supplier rates against open market rates to ensure competitiveness.
- **New product development**: Identify new destinations, hotels, or experiences to add to the portfolio.

**Data they manage (in their head or Excel):**
- Preferred hotel list with: commission rate, net cost, suitability tags, contact person, response reliability score
- Transport provider list with: vehicle types, rates, reliability, geographic coverage
- DMC partnerships with: contracted rates, response SLA, quality rating
- Competitor pricing intelligence

**Key pressures:**
- Rate volatility: Hotel rates change seasonally; keeping up is manual and error-prone
- Relationship dependency: A key supplier relationship going sour can disrupt the entire business
- No systematic tracking: Most boutique agencies manage this entirely in their heads or spreadsheets
- Commission leakage: Hotels sometimes bypass the agency and deal directly with clients

#### Current System Coverage

| Capability | Implementation | Location |
|---|---|---|
| Sourcing hierarchy model | 4-tier sourcing defined in product vision | `Docs/PRODUCT_VISION_AND_MODEL.md` |
| Margin calculation | Risk-adjusted fees | `src/fees/calculation.py` |
| Activity catalog | 18 static activities with suitability tags | `src/suitability/catalog.py` |

#### Gaps (What Should Exist)

| Gap | Severity | Description |
|---|---|---|
| **No supplier database** | P0 | No structured database of preferred suppliers, their rates, suitability tags, or reliability scores. |
| **No rate management** | P0 | No system to store, compare, or update supplier rates. No margin tracking per supplier. |
| **No reliability tracking** | P1 | No automated tracking of supplier response times, booking accuracy, or complaint rates. |
| **No commission management** | P1 | No system to track expected vs. received commissions from suppliers. |
| **No contract storage** | P2 | No document storage for supplier contracts and agreements. |

#### AI Agent Specification: `SupplierAgent`

**Role**: Supplier intelligence, rate optimization, and sourcing recommendations.

**Inputs:**
- Client requirements from CanonicalPacket
- Sourcing hierarchy rules (internal packages → preferred suppliers → network → open market)
- Supplier database (rates, suitability, reliability)
- Margin targets from OwnerAgent

**Outputs:**
- Ranked supplier recommendations per requirement (hotel, transport, activities)
- Margin-aware pricing ("Hotel A costs 20% less than Hotel B but margin is 5% higher")
- Rate comparison alerts ("Published rate dropped below your contracted rate for Hotel X")
- Supplier performance reports
- Sourcing order recommendations (which tier to source from)

**Decision Authority:**
- **Recommend** suppliers from preferred network first
- **Flag** when preferred network cannot fulfill requirements
- **Alert** on margin-eroding situations
- **Score** suppliers on multi-dimensional fit (traveler, operational, commercial)

---

### R10: Revenue / Pricing Analyst

#### The Real Job

Ensures the agency's pricing is competitive, profitable, and defensible. This role is often informal in boutique agencies — the owner sets prices by gut feel.

**Daily responsibilities:**
- **Trip pricing**: Calculate total trip cost including all components, apply agency markup, produce client-facing pricing
- **Margin analysis**: Track margins per trip type, per destination, per supplier. Identify where margin is leaking.
- **Competitive pricing**: Monitor competitor pricing for similar trips. Ensure the agency's proposals are in the right range.
- **Budget decomposition**: Break a total budget into component costs (flights, hotels, activities, food, transport, buffer) — ensure the allocation is realistic
- **Dynamic pricing**: Adjust pricing based on seasonality, demand, supplier availability
- **Discount management**: Decide when to offer discounts, how much, and whether it still preserves minimum margin

**Key pressures:**
- Pricing opacity: Clients don't see the breakdown — they just see a total number. If it feels high, they walk.
- Margin pressure: Clients comparison-shop with OTAs. The agency must justify its premium.
- Scope creep pricing: Each revision to the itinerary may change costs, but the client expects the original price
- Seasonal volatility: Same trip can cost 40% more in peak season

#### Current System Coverage

| Capability | Implementation | Location |
|---|---|---|
| Budget decomposition | 8-bucket model (flights, stay, food, activities, transport, visa, shopping, buffer) | `src/intake/decision.py` |
| Budget feasibility | Per-destination cost tables with realistic benchmarks | `src/intake/decision.py` |
| Fee calculation | Risk-adjusted pricing by service type with risk multipliers | `src/fees/calculation.py` |
| Margin estimation | 15-25% range with risk adjustments | `src/analytics/engine.py` |

#### Gaps (What Should Exist)

| Gap | Severity | Description |
|---|---|---|
| **No actual cost tracking** | P0 | System estimates costs but cannot track actual supplier costs vs. budgeted costs. |
| **No markup engine** | P0 | No configurable markup rules (flat %, tiered, per-component). Planners calculate markup manually. |
| **No competitive pricing** | P1 | No market rate comparison or pricing intelligence. |
| **No dynamic pricing** | P1 | No seasonality-based pricing adjustments. |
| **No margin dashboard** | P1 | Cannot view margins across trips, destinations, or time periods. |

#### AI Agent Specification: `PricingAgent`

**Role**: Pricing intelligence, margin optimization, and commercial feasibility.

**Inputs:**
- CanonicalPacket with budget and requirements
- Supplier cost data (from SupplierAgent)
- Margin targets (from OwnerAgent)
- Seasonal pricing factors
- Competitive intelligence (future)

**Outputs:**
- Per-component cost estimates with confidence intervals
- Recommended pricing with markup options
- Margin analysis per trip
- Budget-to-actual variance tracking
- Pricing optimization suggestions

**Decision Authority:**
- **Calculate** pricing within configured markup rules
- **Warn** when margin falls below threshold
- **Recommend** pricing adjustments for scope changes
- **Compare** costs across sourcing tiers

---

### R11: DMC (Destination Management Company) Liaison

#### The Real Job

A DMC is a local company in the destination country that provides ground services — airport transfers, local guides, hotel bookings, restaurant reservations, and activity coordination. Agencies partner with DMCs to handle on-the-ground logistics.

**Daily responsibilities:**
- **DMC selection**: Choose the right DMC for each destination based on service quality, pricing, and reliability
- **Brief creation**: Send structured trip requirements to the DMC — dates, group profile, hotel preferences, activity requests
- **Quote comparison**: Compare quotes from multiple DMCs for the same trip
- **Quality oversight**: Ensure DMC delivers as promised. Track response times, booking accuracy, and client satisfaction
- **Payment coordination**: Manage advance payments, credit terms, and reconciliation with DMCs
- **Emergency coordination**: When a client has an in-trip issue, the DMC liaison coordinates the local response

**Relevance to this product:** HIGH for mid-size agencies. Boutique agencies often deal directly with local operators rather than through DMCs.

#### Current System Coverage

None explicitly. The sourcing hierarchy mentions network/consortium inventory as tier 3, but no implementation exists.

#### Gaps

- No DMC database or management
- No structured brief generation for DMCs
- No quote comparison workflow
- No DMC performance tracking

#### AI Agent Specification: `DMCConnectorAgent`

**Status**: FUTURE. When agencies have multiple DMC partnerships, this agent would:
- Generate structured briefs from CanonicalPacket
- Route to appropriate DMCs based on destination and service type
- Compare and rank DMC quotes
- Track DMC performance metrics
- Handle payment milestone tracking

---

### R12: Wholesaler / Consolidator Account Manager

#### The Real Job

Wholesalers and consolidators provide bulk rates for flights, hotels, and packages. Agencies that are part of a consortium (e.g., TAAI, Travel Leaders) get access to these rates.

**Daily responsibilities:**
- Manage consortium membership and compliance
- Access and compare wholesale rates vs. direct rates
- Navigate booking portals for consolidator inventory
- Track savings achieved through wholesale channels

**Relevance to this product:** LOW for current scope (boutique agencies). Mentioned for completeness.

#### AI Agent Specification

**Status**: DEFERRED. Would be relevant when the platform serves agencies that are part of consortia.

---

## TIER 4: OPERATIONS & EXECUTION

---

### R13: Tour Guide / Local Expert

#### The Real Job

The tour guide is the on-the-ground person who brings the trip to life. They meet clients at the airport, take them on city tours, manage logistics during the day, and handle real-time problems.

**Daily responsibilities:**
- **Airport transfers**: Meet clients, assist with luggage, transport to hotel
- **City tours**: Conduct guided tours with historical, cultural, and local knowledge
- **Logistics management**: Navigate the group through the day's itinerary — timing, transport, reservations
- **Real-time problem solving**: Restaurant is closed? Activity is overbooked? Weather turned bad? The guide pivots.
- **Language/cultural bridge**: Translate, explain local customs, negotiate with local vendors
- **Client relationship**: Build rapport, read the group's mood, adjust pace and content
- **Safety**: Ensure group safety, manage medical emergencies, handle lost documents
- **Feedback collection**: Informal — "How was today? Anything you'd change for tomorrow?"

**Key pressures:**
- Information asymmetry: The guide knows the ground reality; the remote planner does not
- Real-time pressure: Decisions must be made instantly; no time to consult the planner
- Client expectations: Clients expect the guide to know everything and handle everything
- Weather and traffic: Uncontrollable factors that disrupt the best-planned itinerary

#### Current System Coverage

| Capability | Implementation | Location |
|---|---|---|
| Day-wise pacing | Suitability engine checks daily intensity | `src/suitability/context_rules.py` |
| Activity timing | Activity catalog with duration estimates | `src/suitability/catalog.py` |

#### Gaps (What Should Exist)

| Gap | Severity | Description |
|---|---|---|
| **No day-wise ops dashboard** | P1 | No view showing today's itinerary, pickups, timing, and contact information for ground staff. |
| **No disruption playbook** | P1 | No pre-planned alternatives for common disruptions (rain, closure, delay). |
| **No real-time communication** | P2 | No channel between guide and planner during the trip. |
| **No in-trip feedback** | P2 | No mechanism for guide to feed back real-time issues to the planning system. |

#### AI Agent Specification: `GroundOpsAgent`

**Role**: On-the-ground operations support, disruption handling, and real-time logistics.

**Inputs:**
- Confirmed itinerary with day-by-day breakdown
- Pickup/transfer schedule with contact information
- Disruption signals (weather API, traffic, flight delays — future)
- Guide/traveler messages (from WhatsApp integration — future)

**Outputs:**
- Day-wise ops brief for guide (morning digest)
- Real-time disruption alerts with recommended alternatives
- Transfer schedule with GPS tracking links (future)
- Daily summary report

**Decision Authority:**
- **Suggest** alternatives when disruptions occur
- **Alert** planner/owner when disruption exceeds threshold
- **Track** daily progress against planned itinerary
- **Cannot** make booking changes or financial commitments

---

### R14: Visa / Documentation Specialist

#### The Real Job

The visa and documentation specialist ensures every traveler has the right documents for their trip — passports, visas, travel insurance, health certificates, and other requirements.

**Daily responsibilities:**
- **Visa requirement check**: Determine visa requirements based on nationality, destination, duration, and purpose of travel. Requirements vary by passport, change frequently, and have exceptions.
- **Document checklist generation**: Create per-traveler document checklists — passport validity (6 months), photos, bank statements, employment letters, itinerary copies
- **Application preparation**: Fill visa application forms (or guide clients through them), ensure photos meet specifications, organize supporting documents
- **Submission tracking**: Track when applications were submitted, expected processing times, and pickup dates
- **Status monitoring**: Check visa application status, follow up with embassies/consulates
- **Emergency handling**: Expedited visa processing when timelines are tight. Last-minute document procurement.
- **Compliance verification**: Ensure all documents are valid, not expired, and meet destination requirements before travel
- **Record keeping**: Maintain copies of all submitted documents for future reference and audit

**Key pressures:**
- Requirements change frequently — what was valid last month may not be valid this month
- Consequences of error are severe — a denied boarding costs thousands and destroys client trust
- Timeline sensitivity — visa processing takes 5-15 business days; late submission = missed trip
- Per-country complexity — some countries require biometrics, interviews, or sponsors
- Group complexity — family members may have different nationalities/passports, requiring different visas

#### Current System Coverage

| Capability | Implementation | Location |
|---|---|---|
| Visa timeline risk flag | Flags when visa processing may not complete in time | `src/decision/rules/visa_timeline.py` |
| Document risk flag | Risk flags for document-related issues | `src/intake/decision.py` |
| Passport extraction | Can extract passport/visa status from intake text | `src/intake/extractors.py` |

#### Gaps (What Should Exist)

| Gap | Severity | Description |
|---|---|---|
| **No visa requirement database** | P0 | No database of visa requirements by nationality + destination. System flags timing risk but cannot tell you whether a visa is needed or what type. |
| **No document checklist generator** | P0 | Cannot generate per-traveler document checklists based on destination, nationality, and trip type. |
| **No document collection tracker** | P1 | No tracking of which documents have been received, which are pending, and which are overdue. |
| **No application timeline management** | P1 | No timeline with milestones (documents due, application submit date, expected approval date). |
| **No document storage** | P2 | No secure storage for passport copies, visa applications, and supporting documents. |

#### AI Agent Specification: `DocumentAgent`

**Role**: Visa and documentation intelligence, tracking, and compliance.

**Inputs:**
- Traveler nationalities and passport details
- Destination countries
- Travel dates
- Trip purpose (tourism, business, transit)

**Outputs:**
- Per-traveler visa requirement summary
- Document checklist per traveler
- Application timeline with milestones
- Document collection status tracker
- Compliance verification results
- Expiry alerts (passport expiring within 6 months)

**Decision Authority:**
- **Determine** visa requirements (based on maintained database)
- **Flag** timeline risks when processing time exceeds available window
- **Track** document collection status
- **Alert** when documents are overdue or non-compliant
- **Cannot** submit applications or make legal determinations

---

### R15: Booking Coordinator / Ticketing Agent

#### The Real Job

The booking coordinator handles the actual reservations — flights, hotels, transfers, activities, insurance. This is the execution arm that turns a planned itinerary into confirmed bookings.

**Daily responsibilities:**
- **Flight booking**: Search and book flights via GDS (Amadeus, Sabre, Galileo), airline direct, or consolidators. Handle seat selection, meal preferences, frequent flyer numbers.
- **Hotel booking**: Book hotels via contracted rates, wholesaler platforms, or direct. Ensure room type matches requirements (connecting rooms for families, ground floor for elderly).
- **Transfer booking**: Arrange airport transfers, inter-city transport. Coordinate pickup times with flight schedules.
- **Activity booking**: Reserve tour slots, activity tickets, restaurant reservations. Manage booking confirmations and vouchers.
- **Confirmation management**: Collect and organize all booking confirmations into a trip master record. Cross-check names, dates, and details.
- **Name/date verification**: Ensure every booking has correct passenger names (matching passport), correct dates, and correct details. A single transposition error can strand a traveler.
- **Payment processing**: Collect payments from clients, make payments to suppliers. Track advance vs. balance.
- **Modification handling**: Handle date changes, name corrections, cancellations. Navigate supplier modification policies and fees.

**Key pressures:**
- Accuracy is everything — a wrong name on a flight ticket can cost the full fare
- Confirmation chaos — dozens of emails/PDFs that must be organized and cross-checked
- Payment timing — suppliers want advance, clients want to pay later; the coordinator manages the gap
- Cancellation policies — every supplier has different rules; missing a deadline costs money
- Multi-system navigation — GDS for flights, hotel portals for hotels, WhatsApp for local operators

#### Current System Coverage

None. The system explicitly does NOT handle booking (per design decision in `Docs/INTEGRATIONS_AND_DATA_SOURCES.md`). The system stops at the planning/proposal stage.

#### Gaps

This is an intentional design decision, not a gap. The system is "pre-booking intelligence" — it helps planners create better proposals. Booking is handled by the planner using their existing tools (GDS, hotel portals, etc.).

**Future consideration**: A `BookingAgent` could be added when the platform integrates with booking APIs, but this is explicitly deferred per the product vision.

#### AI Agent Specification: `BookingAgent` (FUTURE)

**Status**: DEFERRED per product strategy. Would require:
- GDS integration (Amadeus/Sabre)
- Hotel booking API integration
- Payment gateway integration
- This is a different product scope

---

### R16: Ground Operations / Transport Coordinator

#### The Real Job

Manages all transportation logistics — airport transfers, inter-city travel, daily transport during the trip.

**Daily responsibilities:**
- **Transfer scheduling**: Coordinate pickup/dropoff times across all travelers and destinations
- **Vehicle selection**: Choose appropriate vehicles (sedan for 2, van for 6, coach for 30)
- **Driver management**: Assign drivers, communicate schedules, handle driver issues
- **Real-time coordination**: Adjust for flight delays, traffic, or weather
- **Cost tracking**: Track transport costs per trip against budget

**Relevance:** MEDIUM. Important for agencies doing custom tours with ground transport.

#### Current System Coverage

None specific to transport coordination. Budget decomposition includes a transport bucket.

#### AI Agent Specification

**Status**: FUTURE. Would be part of the GroundOpsAgent (R13) when in-trip operations are addressed.

---

### R17: In-Trip Concierge / Support

#### The Real Job

The person travelers call when something goes wrong during their trip. Available 24/7 during trip dates.

**Daily responsibilities:**
- **Emergency response**: Handle missed flights, lost luggage, medical emergencies, natural disasters
- **Real-time problem solving**: Hotel overbooked? Find an alternative. Activity cancelled? Suggest a replacement. Restaurant closed? Recommend another.
- **Client reassurance**: Keep anxious travelers calm. Provide confidence that someone is handling their issue.
- **Supplier coordination**: Contact hotels, airlines, and local operators to resolve issues
- **Documentation**: Log all incidents for future reference and potential insurance claims
- **Cost management**: Decide whether the agency absorbs costs, passes them to the client, or recovers from suppliers

**Key pressures:**
- 24/7 availability — trips don't respect business hours
- Limited information — often resolving problems without full context
- Emotional clients — travelers in crisis are stressed, angry, or frightened
- Time pressure — a missed connection needs resolution in minutes, not hours
- Cost pressure — every emergency has a financial impact on margins

#### Current System Coverage

None. The system operates pre-trip. No in-trip monitoring or support capabilities.

#### Gaps

| Gap | Severity | Description |
|---|---|---|
| **No trip master record** | P1 | No single document with all confirmations, contacts, and backup plans that can be referenced during the trip. |
| **No disruption playbooks** | P1 | No pre-planned responses for common disruptions specific to this trip. |
| **No real-time alerting** | P2 | No monitoring of flight delays, weather alerts, or supplier issues during trip dates. |

#### AI Agent Specification: `ConciergeAgent`

**Status**: FUTURE. Would require:
- Real-time data feeds (flight status, weather)
- Communication channel integration (WhatsApp)
- Trip master record (all confirmations in one place)
- Disruption response templates

---

## TIER 5: FINANCE & ADMINISTRATION

---

### R18: Finance / Accounts Manager

#### The Real Job

Manages all money flowing through the agency — client payments, supplier payments, commissions, taxes, and profit tracking.

**Daily responsibilities:**
- **Invoicing**: Generate invoices for clients with detailed breakdowns
- **Payment tracking**: Track who has paid, who hasn't, and what's overdue
- **Supplier payments**: Pay suppliers on time to maintain relationships and avoid cancellation
- **Commission tracking**: Track commissions owed by suppliers and follow up on overdue payments
- **Tax compliance**: Calculate and remit TCS (Tax Collected at Source), GST, and other applicable taxes
- **Profit tracking**: Calculate actual profit per trip (revenue minus all costs)
- **Cash flow management**: Manage the gap between when clients pay and when suppliers are paid
- **Reconciliation**: Match payments received against invoices, identify discrepancies
- **Financial reporting**: Monthly P&L, cash flow statements, tax filings

**Key pressures:**
- TCS/GST compliance is complex and penalties are severe
- Cash flow gaps: Suppliers want advance, clients want credit
- Commission recovery: Suppliers sometimes delay or "forget" commissions
- Multi-currency: International trips involve currency conversion and exchange rate risk
- Audit requirements: Tax authorities require detailed records

#### Current System Coverage

| Capability | Implementation | Location |
|---|---|---|
| Fee calculation | Risk-adjusted fee calculation | `src/fees/calculation.py` |
| Revenue metrics | Revenue data models | `src/analytics/models.py` |
| Margin estimation | 15-25% range calculation | `src/analytics/engine.py` |

#### Gaps (What Should Exist)

| Gap | Severity | Description |
|---|---|---|
| **No invoicing** | P0 | Cannot generate invoices for clients. Planners create these manually. |
| **No payment tracking** | P0 | No tracking of payments received, pending, or overdue. |
| **No TCS/GST calculation** | P0 | No automated tax computation. Critical for Indian market compliance. |
| **No commission tracking** | P1 | No tracking of expected vs. received commissions from suppliers. |
| **No profit tracking** | P1 | Cannot calculate actual profit per trip (estimated costs vs. actual costs). |
| **No cash flow view** | P1 | No visibility into cash flow position (money in vs. money out). |
| **No financial reporting** | P2 | No P&L statements, tax summaries, or financial dashboards. |

#### AI Agent Specification: `FinanceAgent`

**Role**: Financial operations, invoicing, payment tracking, and tax compliance.

**Inputs:**
- Trip cost breakdown (from PricingAgent)
- Payment terms (per agency configuration)
- Tax rules (TCS, GST rates by service type)
- Supplier payment schedules

**Outputs:**
- Client invoices with tax computation
- Payment status tracker (per trip, per client)
- Supplier payment schedule
- Commission tracking ledger
- Profit/loss per trip
- Monthly financial summary

**Decision Authority:**
- **Generate** invoices and payment reminders
- **Calculate** tax liabilities
- **Flag** overdue payments
- **Track** commission receivables
- **Cannot** make financial commitments or process payments

---

### R19: Insurance Coordinator

#### The Real Job

Recommends appropriate travel insurance, handles policy issuance, and manages claims.

**Daily responsibilities:**
- **Risk assessment**: Evaluate trip-specific risks (destination safety, activity risk, health concerns)
- **Product recommendation**: Match insurance products to trip profile (adventure sports coverage, medical coverage, cancellation protection)
- **Policy issuance**: Coordinate with insurance providers to issue policies
- **Claims processing**: Help clients file claims when things go wrong — documentation, follow-up, escalation
- **Compliance**: Ensure all required insurances are in place (some destinations require mandatory travel insurance)

**Relevance:** MEDIUM. Insurance is important but often handled informally in boutique agencies.

#### Current System Coverage

| Capability | Implementation | Location |
|---|---|---|
| Insurance in fee calculation | Insurance as a service type in fee calculation | `src/fees/calculation.py` |
| Risk assessment | General risk flagging (activity risk, destination risk) | `src/intake/decision.py`, `src/suitability/` |

#### Gaps

- No insurance product database
- No risk-to-product matching
- No claims tracking
- No policy management

#### AI Agent Specification

**Status**: DEFERRED. When implemented, would be a lightweight module that:
- Recommends insurance products based on trip risk profile
- Generates insurance requirement summaries
- Tracks policy status per trip

---

### R20: Compliance / Regulatory Officer

#### The Real Job

Ensures the agency operates within legal and regulatory requirements. In India, this includes IATA compliance, TAAI membership requirements, TCS/GST regulations, and consumer protection laws.

**Daily responsibilities:**
- **Regulatory compliance**: Ensure agency maintains required licenses, certifications, and registrations
- **Consumer protection**: Ensure terms and conditions are fair, cancellation policies are clear, and refunds are processed correctly
- **Data protection**: Handle client personal data (passport numbers, payment details) in compliance with privacy regulations
- **Record keeping**: Maintain records required by law (financial records, client agreements, supplier contracts)
- **Audit preparation**: Keep documentation organized for potential audits by tax authorities or industry bodies

**Relevance:** LOW for current scope. Most boutique agencies handle compliance informally. The platform should ensure basic compliance (data protection, tax calculation) but doesn't need a dedicated compliance agent.

#### Current System Coverage

| Capability | Implementation | Location |
|---|---|---|
| Data provenance | Full provenance tracking on every packet field | `src/intake/packet_models.py` |
| Audit trail | Every decision logged with who, what, why | `src/analytics/logger.py` |
| Authority levels | Fact-level, derived, hypothesis — different trust levels | `src/intake/packet_models.py` |

#### AI Agent Specification

**Status**: NOT RECOMMENDED as a separate agent. Compliance should be baked into every agent's behavior:
- Data protection: Automatic in every agent (never expose PII in traveler-safe output)
- Tax compliance: Part of FinanceAgent
- Record keeping: Part of the audit trail system (already implemented)

---

## TIER 6: MARKETING & GROWTH

---

### R21: Customer Success / Relationship Manager

#### The Real Job

Manages the post-booking and post-trip relationship. Ensures client satisfaction, collects feedback, and drives repeat bookings and referrals.

**Daily responsibilities:**
- **Pre-trip communication**: Ensure clients have all documents, understand the itinerary, and know emergency contacts
- **In-trip check-ins**: Proactive messages during the trip ("How was today's tour? Everything on schedule?")
- **Post-trip follow-up**: Collect feedback, address complaints, request reviews
- **Repeat booking nurturing**: Maintain contact after the trip. Reach out at appropriate intervals with relevant suggestions ("Planning a summer trip? We have a great Kerala package")
- **Referral generation**: Ask satisfied clients for referrals. Sometimes offer referral incentives
- **Client memory**: Remember preferences, past trips, feedback, and special dates (birthdays, anniversaries)
- **Win-back**: Reactivate clients who haven't booked in a while with personalized outreach
- **VIP management**: Special attention to high-value repeat clients

**Key pressures:**
- Most agencies do zero post-trip follow-up — the trip ends and the relationship dies
- Client memory is entirely in the planner's head — if they leave, the memory leaves with them
- No systematic reactivation — repeat bookings happen by chance, not by design
- Feedback is rarely collected formally — agencies don't know what clients actually think

#### Current System Coverage

| Capability | Implementation | Location |
|---|---|---|
| Lifecycle state machine | Includes RETENTION_WINDOW, REPEAT_BOOKED, DORMANT states | `Docs/LEAD_LIFECYCLE_AND_RETENTION.md` |
| Repeat likelihood scoring | Deterministic scoring based on past trip signals | `src/intake/decision.py` |
| Churn risk scoring | Deterministic scoring for won customers | `src/intake/decision.py` |
| Reactivation playbooks | Defined in lifecycle document | `Docs/LEAD_LIFECYCLE_AND_RETENTION.md` |
| Feedback panel | UI for post-trip feedback collection | `frontend/` FeedbackPanel |

#### Gaps (What Should Exist)

| Gap | Severity | Description |
|---|---|---|
| **No client memory** | P0 | No cross-trip traveler profile. Cannot remember "Sharma family prefers vegetarian hotels and avoids crowded attractions." |
| **No automated follow-up** | P1 | Lifecycle playbooks defined but not automated. No scheduled post-trip messages or reactivation campaigns. |
| **No feedback collection workflow** | P1 | Feedback panel exists in UI but no automated post-trip feedback request. |
| **No referral tracking** | P2 | No tracking of referral sources or referral incentives. |
| **No reactivation campaigns** | P2 | No automated reactivation messaging based on lifecycle state. |

#### AI Agent Specification: `RetentionAgent`

**Role**: Client relationship continuity, feedback collection, and repeat booking nurturing.

**Inputs:**
- Lifecycle state transitions
- Trip completion events
- Feedback data
- Client profile history (future)
- Seasonal patterns

**Outputs:**
- Post-trip feedback requests (auto-generated)
- Reactivation messages (personalized, timed)
- Client satisfaction scores
- Repeat booking suggestions
- Referral request drafts
- VIP alerts ("Top client hasn't booked in 4 months")

**Decision Authority:**
- **Schedule** follow-up messages based on lifecycle state
- **Score** client satisfaction from feedback
- **Recommend** reactivation timing and content
- **Flag** churn-risk clients for owner attention
- **Cannot** make financial commitments or book trips

---

### R22: Social Media / Channel Manager

#### The Real Job

Manages the agency's presence on social media and other marketing channels. Drives inbound leads through content, engagement, and advertising.

**Daily responsibilities:**
- **Content creation**: Post travel inspiration, destination guides, client testimonials, and promotional offers
- **Lead capture**: Convert social media interest into actual inquiries (DM to WhatsApp, comment to call)
- **Channel management**: Maintain presence across Instagram, Facebook, WhatsApp Status, and potentially YouTube/TikTok
- **Inquiry routing**: Route incoming inquiries from different channels to the appropriate planner
- **Response management**: Ensure quick response to inquiries on all channels
- **Analytics**: Track which content generates leads, which channels convert best

**Relevance:** MEDIUM for boutique agencies (most rely on word-of-mouth). HIGH for agencies trying to grow.

#### Current System Coverage

None specific to marketing/channel management.

#### Gaps

- No multi-channel message intake
- No content management or scheduling
- No channel analytics
- No lead source attribution

#### AI Agent Specification

**Status**: FUTURE. Would require:
- Social media API integrations
- Content generation capabilities
- Multi-channel message normalization
- Attribution tracking

---

### R23: Referral / Partnership Coordinator

#### The Real Job

Builds and manages referral networks — other businesses or individuals who send clients to the agency.

**Daily responsibilities:**
- **Partnership development**: Build relationships with wedding planners, corporate HR departments, event managers, and other travel agencies (for overflow)
- **Referral tracking**: Track who sent which lead, conversion rates, and referral payments
- **Referral incentive management**: Manage referral fees, commissions, or reciprocal arrangements
- **Partner satisfaction**: Ensure partners are happy with the arrangement and continue sending leads

**Relevance:** LOW for current scope. Important for growth but not core to trip planning.

#### AI Agent Specification

**Status**: DEFERRED. Would be a lightweight module tracking referral sources and conversion when agencies request it.

---

## CROSS-CUTTING ROLES

---

### R24: Front Desk / First Response

#### The Real Job

The first point of contact for any inquiry. In boutique agencies, this is the planner or owner. In larger agencies, a dedicated receptionist or first-response agent.

**Daily responsibilities:**
- **Initial triage**: Receive inquiry, determine if it's a genuine lead or a general question
- **Basic information capture**: Get essential details (name, phone, destination interest, approximate dates)
- **Routing**: Assign to the appropriate planner or handle directly if simple
- **Immediate acknowledgment**: Send a quick "We received your inquiry" response within minutes
- **Queue management**: Ensure no inquiry goes unanswered for more than a defined period

**Key pressures:**
- Speed matters: Response within 5 minutes = 90% conversion; response after 1 hour = 30% conversion
- Volume management: Peak season can bring 20-50 inquiries per day
- First impression: The initial response sets the tone for the entire relationship

#### Current System Coverage

| Capability | Implementation | Location |
|---|---|---|
| Intake extraction | Extracts structured data from freeform text | `src/intake/extractors.py` |
| Operating mode detection | Classifies inquiry type (package_suitable, custom_supplier, etc.) | `src/intake/extractors.py` |
| Urgency detection | Computes urgency based on dates and context | `src/intake/normalizer.py` |
| Inbox with SLA tracking | Shows inquiries with time-since-arrival | `/inbox` page |

#### Gaps

| Gap | Severity | Description |
|---|---|---|
| **No auto-acknowledgment** | P1 | No automatic "We received your inquiry" response generation. |
| **No inquiry routing** | P1 | No automatic triage and assignment based on inquiry type and planner specialization. |
| **No response time tracking** | P2 | No tracking of first-response time per inquiry. |

#### AI Agent Specification: `InboxAgent` / `FrontDoorAgent`

**Role**: Initial triage, acknowledgment, and routing.

**Inputs:**
- Raw inquiry (text, WhatsApp message, form submission)
- Planner availability and specialization
- Agency configuration (routing rules, SLA targets)

**Outputs:**
- Structured initial assessment (is this a real lead? what type?)
- Auto-generated acknowledgment message (draft for planner review)
- Routing recommendation (which planner should handle this)
- Priority classification (urgent, normal, low)

**Decision Authority:**
- **Classify** inquiry type and priority
- **Draft** acknowledgment response (planner approves)
- **Recommend** planner assignment
- **Flag** SLA breaches for unassigned inquiries

---

## SYNTHESIS: AGENT PRIORITY MATRIX

Based on the gap analysis above, here is the recommended implementation priority for AI agents:

### Priority 0 — Core Trip Planning (Build Now)

| Agent | Role Served | Why | Current Gap |
|---|---|---|---|
| **PlanningAgent** | Travel Consultant (R04) | The system extracts constraints but doesn't generate options or itineraries. This is the largest gap. | No itinerary generation, no option construction, no proposal builder |
| **SupplierAgent** | Procurement (R09) | No supplier database. The sourcing hierarchy is defined in docs but has no implementation. | No supplier data, no rate management, no sourcing search |
| **DocumentAgent** | Visa Specialist (R14) | High-stakes, rules-heavy, automatable. Currently only a timing risk flag exists. | No visa requirements DB, no checklists, no tracking |

### Priority 1 — Operational Excellence (Build Next)

| Agent | Role Served | Why | Current Gap |
|---|---|---|---|
| **PricingAgent** | Revenue Analyst (R10) | Extend existing fee calculation into full pricing engine. | No markup engine, no cost tracking, no margin dashboard |
| **OrchestratorAgent** | Ops Manager (R02) | Extend existing assignment/SLA code into full orchestration. | No auto-assignment, no workload tracking, no escalation |
| **QualityGateAgent** | Senior Planner (R05) | Extend existing review/gates into pattern-matching review system. | No pattern matching, no knowledge base, no peer review |
| **DestinationExpertAgent** | Destination Specialist (R06) | Extend geography and budget tables into destination intelligence. | No knowledge base, no seasonality, no logistics engine |
| **FinanceAgent** | Finance (R18) | Critical for Indian market (TCS/GST). Invoicing gap blocks operations. | No invoicing, no payment tracking, no tax calculation |
| **RetentionAgent** | Customer Success (R21) | Lifecycle scoring exists; activation is the gap. | No client memory, no automated follow-up |
| **SalesAgent** | Sales (R03) | Lead scoring exists; conversion workflow is missing. | No lead scoring UI, no follow-up automation |
| **InboxAgent** | Front Desk (R24) | Intake exists; triage and routing is missing. | No auto-routing, no acknowledgment |

### Priority 2 — Growth & Scale (Build When Demand Exists)

| Agent | Role Served | Why |
|---|---|---|
| **GroundOpsAgent** | Tour Guide (R13) | Requires real-time data feeds and communication integration |
| **ConciergeAgent** | In-Trip Support (R17) | Requires 24/7 availability and real-time monitoring |
| **DMCConnectorAgent** | DMC Liaison (R11) | Relevant when agencies have multiple DMC partnerships |

### Deferred

| Agent | Role Served | Why Deferred |
|---|---|---|
| **BookingAgent** | Booking Coordinator (R15) | Per product strategy — system is pre-booking intelligence |
| **CorporateTravelAgent** | Corporate Manager (R07) | Fundamentally different business model |
| **ComplianceAgent** | Compliance (R20) | Compliance should be baked into every agent, not separate |
| **ChannelAgent** | Social Media (R22) | Requires social media integrations |
| **ReferralAgent** | Partnerships (R23) | Low priority for current segment |

---

## HOW THE ROLES INTERACT

### The Trip Lifecycle with Role Touchpoints

```
LEAD ARRIVES
    ↓
[R24 Front Desk] ← First response, triage
    ↓
[R03 Sales Manager] ← Lead qualification, scoring
    ↓
[R02 Ops Manager] ← Assignment to planner
    ↓
[R04 Travel Consultant] ← Main planning loop ──────────────────────┐
    ↓                    Uses:                                       │
[R06 Destination Specialist] ← Geographic expertise                  │
[R09 Procurement] ← Supplier selection                               │
[R10 Pricing] ← Cost calculation                                     │
[R14 Visa Specialist] ← Document requirements                        │
[R05 Senior Planner] ← Quality review                                │
[R01 Agency Owner] ← Approval (if needed)                            │
    ↓                                                                │
PROPOSAL SENT                                                        │
    ↓                                                                │
REVISION LOOP (returns to R04) ─────────────────────────────────────┘
    ↓
BOOKING CONFIRMED
    ↓
[R15 Booking Coordinator] ← Actual reservations
[R18 Finance] ← Invoicing, payment
[R19 Insurance] ← Policy issuance
    ↓
PRE-TRIP
    ↓
[R21 Customer Success] ← Pre-trip communication, document delivery
    ↓
IN-TRIP
    ↓
[R13 Tour Guide] ← On-ground execution
[R16 Transport] ← Ground logistics
[R17 Concierge] ← Emergency support
    ↓
POST-TRIP
    ↓
[R21 Customer Success] ← Feedback, retention
[R18 Finance] ← Commission reconciliation, final P&L
[R01 Agency Owner] ← Business review
```

---

## IMPLEMENTATION NOTES

### Why the `src/agents/` Directory is Empty

The current architecture uses a **pipeline-based approach** (spine: NB01→NB02→NB03→safety→fees) rather than discrete agents. This was the correct early decision — the system needed deterministic backbone logic before adding agent-level complexity.

The role-to-agent mapping above describes the **target state**. The transition from pipeline to agents should be additive:
1. Keep the spine as the deterministic backbone
2. Add agents as orchestration layers ABOVE the spine
3. Each agent calls spine stages as needed and adds role-specific intelligence on top

### The Solo Planner Reality

The most important insight from this analysis: In the target market (boutique agencies, 1-3 people), **ONE PERSON plays ALL these roles**. The owner is simultaneously the front desk, sales manager, travel consultant, destination specialist, visa handler, finance person, and concierge.

This means the AI agents are not replacing a team — they are **giving a solo operator a virtual team**. The priority should be:
1. Automate the roles the solo operator hates doing (documentation, visa tracking, invoicing)
2. Amplify the roles the solo operator does well but slowly (planning, research, pricing)
3. Handle the roles the solo operator simply cannot do (24/7 concierge, systematic retention)

### The Multi-Agent Interaction Pattern

When multiple agents are implemented, they should follow this pattern:
1. **Each agent owns its domain** — no overlapping responsibilities
2. **Agents communicate through the CanonicalPacket** — the shared state model
3. **Escalation flows upward** — PlanningAgent → QualityGateAgent → OwnerAgent
4. **Commercial decisions flow sideways** — PlanningAgent ↔ PricingAgent ↔ SupplierAgent
5. **All mutations are logged** — the provenance system already supports this

---

## DOCUMENT MAINTENANCE

This document should be updated when:
- A new agent is implemented (update "Current System Coverage" for the relevant role)
- A gap is resolved (move from "Gaps" to "Current System Coverage")
- New roles are discovered through user research
- Industry context changes (regulations, market shifts)

**Last reviewed**: 2026-04-23
**Next review**: When first agent (PlanningAgent or SupplierAgent) implementation begins
