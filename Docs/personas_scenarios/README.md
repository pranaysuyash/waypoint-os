# Persona-Based Scenario Documentation

**Approach**: User-centered design starting from real stakeholders  
**Core Mapped Scenarios**: 20 (P1, P2, P3, S1/S2) — mapped to the N01/N02 pipeline  
**Total Scenario Exploration Files**: 340+ (including additional, frontier, and deep-dive scenarios)  
**Coverage**: 5 personas, 5 anti-personas

> **Agent Note**: The additional scenario files (ADDITIONAL_SCENARIOS_*.md, numbered 21–329+) are  
> product explorations, customer research inputs, and future-domain ideas. They are **not** all  
> mapped to the pipeline or implemented in code. Treat them as research artifacts unless they  
> have an explicit entry in `SCENARIOS_TO_PIPELINE_MAPPING.md`. Do **not** assume a scenario  
> described in any additional scenario file is already implemented. Always verify against the  
> current codebase before building.

---

## Quick Navigation

| Document | Persona | Scenarios | Focus |
|----------|---------|-----------|-------|
| [STAKEHOLDER_MAP.md](STAKEHOLDER_MAP.md) | All | N/A | Persona definitions and power analysis |
| [P1_SOLO_AGENT_SCENARIOS.md](P1_SOLO_AGENT_SCENARIOS.md) | Solo Agent | 5 | Memory, speed, protection, compliance |
| [P2_AGENCY_OWNER_SCENARIOS.md](P2_AGENCY_OWNER_SCENARIOS.md) | Agency Owner | 5 | Visibility, control, standardization |
| [P3_JUNIOR_AGENT_SCENARIOS.md](P3_JUNIOR_AGENT_SCENARIOS.md) | Junior Agent | 5 | Guidance, safety, learning |
| [S1S2_CUSTOMER_SCENARIOS.md](S1S2_CUSTOMER_SCENARIOS.md) | Customers | 5 | Experience, transparency, confidence |

---

## Scenario Matrix

### By Persona

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ P1: SOLO AGENT (The One-Person Show)                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│ P1-S1: 11 PM WhatsApp Panic       → Speed + memory                          │
│ P1-S2: Repeat customer forgot     → Customer history                        │
│ P1-S3: Customer changes everything → Revision tracking                       │
│ P1-S4: Visa problem at last minute → Compliance/blockers                     │
│ P1-S5: Group with different payments → Multi-party management                │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ P2: AGENCY OWNER (The Growing Team)                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│ P2-S1: Quote disaster review      → Quality control                         │
│ P2-S2: Agent who left             → Knowledge retention                     │
│ P2-S3: Margin erosion problem     → Financial controls                       │
│ P2-S4: Training time problem      → Onboarding acceleration                  │
│ P2-S5: Weekend panic (no visibility) → Operational dashboard                │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ P3: JUNIOR AGENT (The New Hire)                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│ P3-S1: First solo quote           → Guided workflows                        │
│ P3-S2: Visa mistake prevention    → Hard blockers                           │
│ P3-S3: "Is this right?" check     → Validation + peer comparison             │
│ P3-S4: Don't know answer          → Knowledge base                           │
│ P3-S5: Comparison trap            → Margin protection + negotiation          │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ S1/S2: CUSTOMERS (The End Experience)                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│ S1-S1: Comparison shopper         → Speed + options                         │
│ S1-S2: Post-booking anxiety       → Proactive communication                  │
│ S1-S3: Trip emergency             → 24/7 crisis support                      │
│ S2-S1: Preference collection      → Group consensus tools                    │
│ S2-S2: Document chaos             → Distributed collection                   │
│ S2-S3: Budget conversation        → Expectation management                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Key System Requirements (Derived from Scenarios)

### Must-Have Features (Critical for Success)

| Feature | Scenarios | Why Critical |
|---------|-----------|--------------|
| **Customer Profiles** | P1-S2, P2-S2 | Knowledge walks out with agents |
| **Hard Blockers** | P1-S4, P3-S2 | Prevent disasters (visa, passport) |
| **Quote Validation** | P2-S1, P3-S3 | Quality control, completeness |
| **Margin Tracking** | P2-S3 | Financial viability |
| **Guided Workflows** | P3-S1 | Reduce training time |
| **Proactive Comms** | S1-S2, S1-S3 | Customer confidence |

### Should-Have Features (Important)

| Feature | Scenarios | Value |
|---------|-----------|-------|
| Revision tracking | P1-S3 | Agent protection |
| Multi-party payments | P1-S5 | Complex bookings |
| Knowledge base | P3-S4 | Consistency |
| Preference collection | S2-S1 | Group trip handling |
| Competitive analysis | P3-S5 | Negotiation support |

### Nice-to-Have (Differentiators)

| Feature | Scenarios | Value |
|---------|-----------|-------|
| AI suggestions | P1-S1 | Speed |
| Crisis protocols | S1-S3 | Premium service |
| Document collection | S2-S2 | Coordinator relief |
| Budget reality check | S2-S3 | Expectation setting |

---

## Failure Modes Addressed

Each scenario prevents a specific failure:

| Failure | Scenario | Cost of Failure |
|---------|----------|-----------------|
| **Bad quote** | P2-S1 | Lost customer, bad review |
| **Knowledge loss** | P2-S2 | Reputation damage |
| **Margin erosion** | P2-S3 | Business unsustainable |
| **Compliance miss** | P1-S4, P3-S2 | ₹L+ in cancellations, legal |
| **Agent burnout** | P1-S3 | Turnover, training cost |
| **Customer anxiety** | S1-S2 | Support burden, complaints |
| **Crisis mishandling** | S1-S3 | Reviews, refunds |
| **Group chaos** | S2-S2 | Lost complex bookings |

---

## Design Principles (Derived)

### For Agents
1. **Don't make me remember** - System is my memory
2. **Don't let me break things** - Hard blockers for disasters
3. **Teach me as I work** - Just-in-time guidance
4. **Protect my time** - Flag time-wasters

### For Owners
1. **See without micromanaging** - Dashboards, not meetings
2. **Knowledge stays when people leave** - Persistent profiles
3. **Standardize without killing flexibility** - Templates + judgment
4. **Know before it breaks** - Alerts, not surprises

### For Customers
1. **Fast beats perfect** - Respond quickly, refine later
2. **Show your work** - Transparent pricing
3. **Be there when I panic** - 24/7 crisis support
4. **Make me look good** - Help coordinators succeed

---

## Usage Guide

### For Product Decisions
1. Pick a persona (e.g., P1 Solo Agent)
2. Read their 5 scenarios
3. Identify their top 3 pain points
4. Map to system features
5. Prioritize by frequency × severity

### For Design Reviews
1. Take a feature (e.g., "Quote Builder")
2. Check against all scenarios
3. Ask: "Does this help P1-S3? P2-S1? P3-S1?"
4. If no, feature may be wrong

### For Testing
1. Take a scenario (e.g., "P1-S1: 11 PM WhatsApp")
2. Build that exact situation
3. Does system produce desired output?
4. Measure: Speed, accuracy, agent confidence

---

## Comparison: Code Tests vs Persona Scenarios

| Aspect | Code Tests (Before) | Persona Scenarios (Now) |
|--------|---------------------|-------------------------|
| **Format** | `CanonicalPacket(facts={...})` | "Mrs. Sharma WhatsApp'd at 11 PM..." |
| **Focus** | System logic | Human situation |
| **Starting point** | Data structure | User need |
| **Validation** | Functions pass | Real problem solved |
| **Audience** | Developers | Product team |

**Both needed**: Persona scenarios define WHAT to build. Code tests validate it works.

---

## Next Steps

1. **Prioritize scenarios** by frequency × pain
2. **Map to system capabilities** (Notebook 01, 02, 03)
3. **Create acceptance criteria** from scenarios
4. **Build incrementally** - start with P1 (Solo Agent, highest pain)
5. **Validate with real users** - Do real agents recognize these situations?

---

## Files in This Directory

```
personas_scenarios/
├── README.md                          # This file
├── STAKEHOLDER_MAP.md                 # Persona definitions
├── P1_SOLO_AGENT_SCENARIOS.md         # 5 scenarios
├── P2_AGENCY_OWNER_SCENARIOS.md       # 5 scenarios  
├── P3_JUNIOR_AGENT_SCENARIOS.md       # 5 scenarios
└── S1S2_CUSTOMER_SCENARIOS.md         # 5 scenarios

Total: 6 documents, 20 scenarios
```

---

*Method: User-centered design starting from stakeholder reality, not system capability.*
