# Product Manager Perspective: Gaps and Unknowns

**Date**: 2026-04-14
**Purpose: What we haven't thought through yet

---

## Executive Summary

We've documented:
- ✅ Product vision and model
- ✅ UX and user flows
- ✅ Business model and pricing
- ✅ GTM and customer acquisition
- ✅ Technical architecture
- ✅ Jobs to be done and user journeys

**But we're missing critical PM thinking on:**
- ❌ Product roadmap and sequencing
- ❌ Definition of MVP vs v1 vs v2
- ❌ Assumption validation plan
- ❌ Success metrics and targets
- ❌ Stakeholder management
- ❌ Integration strategy
- ❌ Data moat and long-term defensibility
- ❌ Feature prioritization framework
- ❌ Experiment design and learning plan
- ❌ Competitive moat beyond "workflow"

---

## Part 1: Product Roadmap Gaps

### We Don't Have Clear Answers To:

| Question | Why It Matters | Current State |
|----------|----------------|---------------|
| **What exactly is MVP?** | Can't build without scope | "First principles" exists, but not concrete feature list |
| **What's v1 (post-MVP)?** | Can't plan iterations | No defined roadmap |
| **What's in v2, v3?** | Can't communicate vision | No long-term thinking |
| **What will we NOT build?** | Focus is critical | No "never build" list |
| **What's the release cadence?** | Sets expectations | Undefined |

### Critical PM Task: Create Feature Roadmap

**Need to define**:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  PRODUCT ROADMAP TEMPLATE                                                        │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  MVP (Month 1-3):                                                                │
│  ├─ Intent extraction from freeform text                                        │
│  ├─ Contradiction/blocker detection                                             │
│  ├─ Basic option generation (2-3 archetypes)                                    │
│  ├─ Agent review workflow                                                       │
│  └─ Client-facing link sharing                                                  │
│                                                                                  │
│  v1.0 (Month 4-6):                                                               │
│  ├─ Learning from agency patterns                                                │
│  ├─ Improved suggestions based on history                                        │
│  ├─ Analytics dashboard for agency owner                                        │
│  └─ Multi-tenant support (if needed)                                            │
│                                                                                  │
│  v1.5 (Month 7-9):                                                               │
│  ├─ Trip comparison view                                                        │
│  ├─ Template library for common trips                                            │
│  ├─ Calendar integration                                                         │
│  └─ Mobile app (maybe)                                                           │
│                                                                                  │
│  v2.0 (Month 10-12):                                                             │
│  ├─ Booking integrations (if demanded)                                          │
│  ├─ CRM integrations                                                             │
│  ├─ Advanced analytics                                                           │
│  └─ White-label option (if demanded)                                            │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Part 2: Assumptions We Haven't Validated

### Critical Assumptions (Unproven)

| Assumption | Risk If Wrong | How to Validate |
|------------|---------------|-----------------|
| **Agencies will paste real client data into AI tool** | Security concern kills adoption | 5 design partners commit to trying |
| **Agents trust AI-generated options** | They ignore output, churn | A/B test: AI-assisted vs manual |
| **Agencies will pay for this** | No revenue, business fails | Pre-sell 5-10 customers |
| **Quality is "good enough" initially** | Bad word-of-mouth | NPS target > 40 |
| **Agencies will share client WhatsApp messages** | Privacy concerns | Data policy review with 10 agencies |
| **Junior agents can use this effectively** | Complexity, mistakes | Usability test with 5 juniors |
| **Option generation is faster than manual** | Perceived value drops | Time trials: measure actual speedup |
| **Travelers accept agent-AI-collaboration** | Agencies hide use | Survey: "Would you care if agent used AI?" |

### Validation Plan Needed

```markdown
## Assumption Validation Timeline

### Week 1-2: Problem Validation
- Interview 15 agencies
- Ask: "Walk me through your current planning process"
- Identify pain points we think we solve
- Confirm: Is this a real problem? Worth solving?

### Week 3-4: Solution Validation
- Show mockups to 10 agencies
- Ask: "Would this help? What's missing?"
- Test: Would they paste real client data?

### Week 5-8: Prototype Validation
- 5 design partners use real work
- Measure: Time saved, quality perceived, rework needed
- Test: Will they pay after free trial?

### Month 3-4: Market Validation
- 20 beta users
- Measure: Activation, retention, NPS, conversion
- Test: Is CAC < LTV/3?

### Go/No-Go Decision Point
- If activation > 40% and NPS > 30: Continue
- If not: Pivot or persevere with different approach
```

---

## Part 3: Feature Prioritization Gaps

### We Don't Have a Framework

**RICE Score** (or similar) needed:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  FEATURE PRIORITIZATION TEMPLATE                                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  Feature: [Description]                                                          │
│                                                                                  │
│  Reach:    _____ users affected                                                  │
│  Impact:  _____ (1 = minimal, 3 = massive)                                      │
│  Confidence: _____ % (how sure are we?)                                          │
│  Effort:   _____ months                                                         │
│                                                                                  │
│  RICE Score = (Reach × Impact × Confidence) / Effort                             │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────┐  │
│  │ BACKLOG (sorted by RICE)                                                 │  │
│  ├────────────────────────────────────────────────────────────────────────────┤  │
│  │ 1. Intent extraction improvements — RICE: 120                            │  │
│  │ 2. Mobile-responsive design — RICE: 95                                  │  │
│  │ 3. Analytics dashboard — RICE: 80                                       │  │
│  │ 4. Template library — RICE: 75                                          │  │
│  │ 5. Calendar integration — RICE: 45                                       │  │
│  └────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Features We Haven't Scored

- Multi-language support
- Currency conversion
- Visa requirement checking
- Real-time flight pricing
- Hotel availability checking
- Itinerary sharing with travelers
- Quote generation
- Invoice generation
- Commission tracking
- Agency branding options
- Webhook integrations
- API access
- Bulk operations
- Trip archiving/search

**Question**: Which of these are must-have vs nice-to-have?

---

## Part 4: Success Metrics Gaps

### We Have Metrics, But Not Targets

**Need to define**:

| Metric | Current (documented) | Missing: Target |
|--------|---------------------|-----------------|
| Trips/week | Track this | What's success? 50? 100? |
| Activation rate | % who use in first week | What threshold? |
| Retention | Week 4 retention | What's acceptable? |
| NPS | Net Promoter Score | What target? |
| Time savings | "Faster than manual" | How much faster? |
| Quality | "Good options" | How measured? |

### Success Definition Needed

```markdown
## Success Criteria (by stage)

### MVP Success (Month 3)
- 5 design partners actively using
- 80%+ say "saved time"
- 60%+ say "quality acceptable or better"
- 40%+ week 4 retention
- NPS > 30

### v1.0 Success (Month 6)
- 20 paying customers
- ₹20K+ MRR
- 40%+ activation
- 30%+ week 4 retention
- NPS > 40
- CAC < LTV/3

### v1.5 Success (Month 9)
- 50 paying customers
- ₹50K+ MRR
- 20%+ month-over-month growth
- Churn < 10%/month

### v2.0 Success (Month 12)
- 100 paying customers
- ₹1L+ MRR
- Profitable (or clear path to profitability)
```

---

## Part 5: Stakeholder Management Gaps

### Who Are Our Stakeholders?

| Stakeholder | Interest | Influence | Current Engagement Strategy |
|-------------|----------|-----------|----------------------------|
| **Agencies (customers)** | Product success | High | Discovery calls, pilots |
| **Agency owners** | Business value | High | Direct outreach |
| **Senior agents** | Usability | Medium | Design partners |
| **Junior agents** | Learning curve | Medium | Usability testing |
| **Travelers (end users)** | Experience | Low | Indirect (through agencies) |
| **Host agencies** | Partnership | High | Not yet engaged |
| **Travel tech community** | Word of mouth | Medium | Content marketing |
| **Investors (future)** | Returns | TBD | Not applicable yet |

### Missing Stakeholder Maps

- **Host agencies** — What's their incentive? How do we approach?
- **Industry associations** — TAAI, TAFI? Should we engage?
- **Travel influencers** — Can they help distribution?
- **Competitors** — What if they build this? Partnership or competition?
- **Regulators** — Any travel industry regulations we should know about?

---

## Part 6: Competitive Moat Gaps

### What's Our Long-Term Defensibility?

**Current thinking**: "We're faster and more focused"

**Problem**: That's not a moat. Speed is temporary. Focus can be copied.

### Real Moat Options (Not Explored)

| Moat Type | Description | Do we have it? | How to build it? |
|-----------|-------------|----------------|-----------------|
| **Network effects** | Product improves with more users | ❌ | Not applicable (each agency is siloed) |
| **Data moat** | Proprietary data improves product | Maybe | We need data strategy |
| **Switching costs** | Painful to leave | Maybe | Make product sticky |
| **Brand** | Trusted, recognized | ❌ | Time and consistency |
| **Ecosystem** | Integrations, partnerships | ❌ | Build partnerships |
| **IP/Technology** | Hard to replicate | Maybe | Need technical differentiation |
| **Process** | Embedded in workflow | Maybe | Make it essential |

### Critical Question: What Data Do We Collect?

**Data we SHOULD collect** (for moat):

```markdown
## Data Moat Strategy

### What to Track (Privacy-Respecting)

1. **Constraint patterns**
   - What constraints go together (e.g., "Europe + June + family = budget concern")
   - Seasonal preferences
   - Budget ranges by destination/season

2. **Feasibility patterns**
   - What trips get flagged as problematic
   - What resolves blockers
   - Success rates by trip type

3. **Option preferences**
   - Which options get chosen
   - What gets edited
   - What gets rejected

4. **Agent behavior**
   - Common workflows
   - Typical modifications
   - Time spent per task

5. **Client feedback**
   - What clients love/hate
   - Revision patterns
   - Booking conversion

### How This Becomes a Moat

After 1000 trips:
- We know: "Families with kids under 10 in Europe prefer 60% culture max"
- We suggest: Automatically adjust options based on this
- Competitors: Don't have this data

After 10,000 trips:
- We know: "₹3L budget for 4-person Europe in June needs specific trade-offs"
- We suggest: Proactive budget coaching
- Competitors: Can't match our predictive quality

### Privacy Consideration

All of this is:
- Aggregated (not attributable to specific clients)
- Optional (agencies can opt-out of data sharing)
- Secure (encrypted, access-controlled)
- Agency-owned (they can export/delete)
```

---

## Part 7: Integration Strategy Gaps

### What Systems Do Agencies Already Use?

**We don't know because we haven't asked enough agencies.**

Potential integrations to research:

| Category | Example Products | Priority | Why |
|----------|------------------|----------|-----|
| **CRM** | HubSpot, Zoho, Salesforce | Low | Few small agencies use CRM |
| **Email** | Gmail, Outlook | Medium | Calendar integration, email parsing |
| **WhatsApp Business** | WATI, Twilio | Medium | Automation (later) |
| **Booking engines** | TBO, Yatra B2B | High | Could be huge value |
| **Accounting** | Tally, Zoho Books | Low | Back office |
| **Payment gateways** | Razorpay, Stripe | Medium | Taking payments |
| **Travel-specific** | Amadeus, Sabre, Expedia TAAP | TBD | Don't know yet |

### Integration Philosophy Needed

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  INTEGRATION DECISION FRAMEWORK                                                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  Build integration when:                                                         │
│  1. 10+ customers request it                                                     │
│  2. It's core to workflow (not nice-to-have)                                    │
│  3. We can execute it with current team                                          │
│  4. It doesn't distract from core value                                          │
│                                                                                  │
│  Don't build when:                                                               │
│  1. It's a "nice to have" that few use                                          │
│  2. It requires learning a complex API                                          │
│  3. The platform might change/disappear                                          │
│  4. It can be done manually for now                                              │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Part 8: Experiment Design Gaps

### What Experiments Should We Run?

**Current state**: We're planning to BUILD. We should be planning to LEARN.

### Experiments to Design

```markdown
## Experiment 1: The "Fake Door" Test

**Question**: Will agencies pay for this before it's built?

**Method**:
- Create landing page with full product description
- Add pricing and "Buy Now" button
- When clicked: "Coming soon, join waitlist"
- Track: Click-through rate, email signups

**Success metric**: 20%+ click pricing, 10%+ join waitlist

**Learn**: Is there real interest? At what price point?

---

## Experiment 2: The Concierge MVP

**Question**: Can we deliver value manually before building AI?

**Method**:
- Offer service: "Send us your messy client messages, we'll send back organized options"
- Do it manually at first (you + AI behind scenes)
- 10 design partners, 3 months

**Success metric**: 80%+ say "this is valuable"

**Learn**: What parts of the workflow are most valuable? Where's the friction?

---

## Experiment 3: The A/B Pricing Test

**Question**: What's the right price?

**Method**:
- Show landing page with 3 price points to different groups
- ₹999, ₹1,999, ₹2,999
- Track: Which gets most signups?

**Success metric**: Find optimal price point

**Learn**: Price sensitivity, value perception

---

## Experiment 4: The Wizard of Oz

**Question**: Does the AI-generated quality meet standards?

**Method**:
- Generate options using AI
- Have agents review without knowing source
- Compare to their own manual options
- Survey: Which is better?

**Success metric**: 60%+ say AI-assisted is equal or better

**Learn**: Quality baseline, what to improve
```

---

## Part 9: Unknown Unknowns

### Things We Haven't Even Considered

| Category | Unknown Unknowns | Fears |
|----------|------------------|-------|
| **Regulatory** | Are there travel industry regulations we're subject to? | Compliance issues |
| **Liability** | If AI suggests something that causes a problem, are we liable? | Legal action |
| **Data privacy** | What if agencies share PII we're not supposed to have? | GDPR/DPDP issues |
| **Seasonality** | What if usage drops dramatically in off-season? | Revenue cliff |
| **Agency failure** | What if our customer agency goes out of business? | Churn, payment issues |
| **Platform risk** | What if OpenAI changes API/pricing? | Cost structure breaks |
| **Competitor response** | What if a big player launches this as a free feature? | Market disappears |
| **Cultural fit** | What if travel agents just don't trust AI? | Adoption ceiling |
| **User behavior** | What if agents use it for edge cases, not normal work? | Value misaligned |
| **Scaling problems** | What breaks at 10, 100, 1000 users? | Unknown complexity |

### Mitigation: Premortem

**Exercise**: Imagine it's 6 months from now and the product FAILED. Why?

```markdown
## Premortem: Why Agency OS Failed (Hypothetical)

### Reason 1: Agencies wouldn't share real client data
- **Why**: Privacy concerns, competitive advantage
- **Sign we should have seen**: Pilots asked to use fake data
- **Prevention**: Strong data governance, clear ownership, maybe local-first

### Reason 2: AI quality wasn't good enough
- **Why**: Hallucinations, generic options, missed constraints
- **Sign we should have seen**: Low NPS, high edit rates
- **Prevention**: Quality thresholds, human review always, gradual rollout

### Reason 3: Workflow didn't match reality
- **Why**: Agents work differently than we assumed
- **Sign we should have seen**: Low activation, feedback on usability
- **Prevention**: More shadowing, usability testing, iteration

### Reason 4: Agencies wouldn't pay
- **Why**: Budget constraints, "good enough with WhatsApp"
- **Sign we should have seen**: Low conversion from free trial
- **Prevention**: Stronger value prop, prove ROI before charging

### Reason 5: We couldn't acquire customers cost-effectively
- **Why**: CAC > LTV, channels didn't work
- **Sign we should have seen**: High churn, low word-of-mouth
- **Prevention**: Start with organic, measure unit economics, scale carefully
```

---

## Part 10: Decision Framework Gaps

### How Do We Make Product Decisions?

**We need a framework**:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  PRODUCT DECISION FRAMEWORK                                                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  Before building ANY feature, ask:                                              │
│                                                                                  │
│  1. PROBLEM: What user problem does this solve?                                 │
│     └─ If no clear problem: DON'T BUILD                                         │
│                                                                                  │
│  2. VALUE: How much better is life after this feature?                          │
│     └─ If marginal improvement: DEFER                                           │
│                                                                                  │
│  3. ALTERNATIVES: Is there a simpler way to solve this?                         │
│     └─ If yes: DO THE SIMPLER THING                                            │
│                                                                                  │
│  4. MEASURABILITY: How will we know if this worked?                             │
│     └─ If not measurable: REFRAME OR DON'T BUILD                                │
│                                                                                  │
│  5. COST: What are we NOT building if we build this?                            │
│     └─ If opportunity cost is high: DEFER                                       │
│                                                                                  │
│  6. VALIDATION: Have we talked to users about this?                             │
│     └─ If no: TALK TO USERS FIRST                                              │
│                                                                                  │
│  ───────────────────────────────────────────────────────────────────────────────│
│                                                                                  │
│  GO/NO-GO Checklist:                                                             │
│  ☐ Solves a real problem                                                       │
│  ☐ Users have requested it (or we've validated)                                │
│  ☐ We can measure success                                                       │
│  ☐ Fits our positioning                                                         │
│  ☐ We can execute it                                                            │
│  ☐ Opp cost is acceptable                                                       │
│                                                                                  │
│  If 4+ checks: Green light                                                      │
│  If 3 checks: Discuss                                                           │
│  If <3 checks: Red light                                                         │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Summary: Critical Gaps to Address

### Immediate (This Week)

1. **Define MVP scope** — What's the absolute minimum to ship?
2. **Create assumption list** — What are we betting on?
3. **Design validation plan** — How do we prove/disprove assumptions?
4. **Set success metrics** — What does "worked" look like?

### Short-term (This Month)

5. **Build feature roadmap** — MVP, v1, v1.5, v2
6. **Create prioritization framework** — How do we decide what to build?
7. **Design experiments** — What do we learn before building?
8. **Map stakeholders** — Who else matters?

### Medium-term (Next Quarter)

9. **Define data moat** — What makes us defensible in 12 months?
10. **Plan integrations** — What will agencies want us to connect to?
11. **Run premortem** — What could kill us, and how do we prevent?
12. **Establish decision process** — How do we make choices?

---

## The One Thing

**As a solo builder, you can't do everything.**

But you CAN:
1. Write down your assumptions
2. Talk to 5-10 agencies
3. Ship a tiny MVP
4. Measure what happens
5. Iterate based on data

**The gap between "good idea" and "good business" is: validation.**

Everything else is optimization.
