# UX Documentation Index

**Last Updated**: 2026-04-13
**Purpose**: Complete index of all UX and user experience documentation

---

## Quick Start

| If you want to... | Read this |
|-------------------|-----------|
| Understand the overall UX philosophy | [UX_AND_USER_EXPERIENCE.md](UX_AND_USER_EXPERIENCE.md) |
| See actual message templates | [UX_MESSAGE_TEMPLATES_AND_FLOWS.md](UX_MESSAGE_TEMPLATES_AND_FLOWS.md) |
| Design dashboards | [UX_DASHBOARDS_BY_PERSONA.md](UX_DASHBOARDS_BY_PERSONA.md) |
| Build the frontend | [UX_TECHNICAL_ARCHITECTURE.md](UX_TECHNICAL_ARCHITECTURE.md) |
| Implement Audit Mode | [UX_AUDIT_MODE_DEEP_DIVE.md](UX_AUDIT_MODE_DEEP_DIVE.md) |

---

## Document Overview

### 1. UX_AND_USER_EXPERIENCE.md
**Purpose**: Big picture UX architecture and philosophy

**Contents**:
- B2B2C architecture (travelers never touch the system)
- Persona experience matrix (P1, P2, P3, S1, S2)
- Traveler-safe vs internal-only boundary
- Decision state UX mapping
- Wireframe sketches for main dashboard

**Key Takeaways**:
- This is not a traveler app - it's an agent copilot
- WhatsApp is primary channel
- Audit Mode is the only direct-to-consumer feature

**Audience**: Designers, PMs, anyone understanding the system

---

### 2. UX_MESSAGE_TEMPLATES_AND_FLOWS.md
**Purpose**: Actual messages travelers receive

**Contents**:
- Message template library (acknowledgment, clarification, proposal, etc.)
- Conversation flow maps (golden path, complex flow, emergency flow)
- Tone guidelines by scenario
- Common edge cases and responses
- Anti-patterns to avoid

**Key Takeaways**:
- Every message must be human-sounding, not robotic
- Templates support personalization variables
- Never mention "the system" to travelers

**Audience**: Copywriters, frontend devs implementing messaging

---

### 3. UX_DASHBOARDS_BY_PERSONA.md
**Purpose**: Different views for different user types

**Contents**:
- P1 Solo Agent dashboard (customer focus)
- P2 Agency Owner dashboard (pipeline/margin focus)
- P3 Junior Agent dashboard (guidance/coaching focus)
- Coordinator dashboard (multi-party trips)
- Mobile vs desktop considerations

**Key Takeaways**:
- Same data, different presentations
- Junior agents see MORE guidance, not less
- Agency owners need aggregate views, not customer details

**Audience**: UI/UX designers, frontend developers

---

### 4. UX_TECHNICAL_ARCHITECTURE.md
**Purpose**: How notebooks connect to a web UI

**Contents**:
- Current state (notebooks only) vs target state (full stack)
- Migration path: notebook → service → API → UI
- API contract definitions (NB01, NB02, NB03 endpoints)
- State management strategy
- WhatsApp integration approaches
- Real-time updates with WebSockets
- Deployment considerations

**Key Takeaways**:
- Extract notebook logic to service functions first
- FastAPI for backend, React for frontend
- PostgreSQL for persistence, Redis for cache

**Audience**: Full-stack developers, architects

---

### 5. UX_AUDIT_MODE_DEEP_DIVE.md
**Purpose**: The direct-to-consumer wedge feature

**Contents**:
- What is Audit Mode and why it matters
- Conversion funnel design
- Landing page UX
- Upload experience (screenshot, email, paste)
- Results display
- Lead capture flow
- Technical implementation
- Conversion optimization

**Key Takeaways**:
- Audit Mode is a lead generation tool
- Should be built before full agent dashboard
- Fastest path to proving value

**Audience**: PMs, marketers, frontend devs

---

### 6. UX_WHATSAPP_INTEGRATION_STRATEGY.md
**Purpose**: WhatsApp integration for individual founders vs businesses

**Contents**:
- Manual copy-paste MVP (no business required)
- WhatsApp Business App (free, no API)
- Third-party providers (WATI, 360dialog)
- Official WhatsApp Business API (requires business)
- Recommended implementation path
- Code examples for copy-paste UI
- Message tracking database schema

**Key Takeaways**:
- You DON'T need a business to start
- Manual copy-paste is best for MVP
- Automate only after product-market fit

**Audience**: Individual founders, full-stack devs

---

### 7. UX_MULTI_CHANNEL_STRATEGY.md
**Purpose**: Multi-channel communication beyond just WhatsApp

**Contents**:
- Channel use cases by stage (discovery, proposal, booking, pre-trip)
- Secure link/portal strategy (why it's better than WhatsApp for many things)
- Customer portal features and wireframes
- Channel preference matrix (by customer type and communication type)
- Technical implementation: link generation, portal API
- Message routing logic
- SMS and email integration

**Key Takeaways**:
- Portal is primary (proposals, docs, payments)
- WhatsApp is for conversation (questions, updates)
- Don't force customers to use one channel
- Think "omnichannel" not "WhatsApp-only"

**Audience**: PMs, full-stack devs, UX designers

---

## Reading Order by Role

### Product Manager
1. UX_AND_USER_EXPERIENCE.md (overview)
2. UX_AUDIT_MODE_DEEP_DIVE.md (wedge feature)
3. UX_MESSAGE_TEMPLATES_AND_FLOWS.md (customer experience)

### UI/UX Designer
1. UX_AND_USER_EXPERIENCE.md (philosophy)
2. UX_DASHBOARDS_BY_PERSONA.md (wireframes)
3. UX_MESSAGE_TEMPLATES_AND_FLOWS.md (messaging patterns)
4. UX_AUDIT_MODE_DEEP_DIVE.md (Audit Mode specific)

### Frontend Developer
1. UX_TECHNICAL_ARCHITECTURE.md (how to build)
2. UX_DASHBOARDS_BY_PERSONA.md (what to build)
3. UX_MESSAGE_TEMPLATES_AND_FLOWS.md (content to render)
4. UX_AND_USER_EXPERIENCE.md (context)

### Full-Stack Developer
1. UX_TECHNICAL_ARCHITECTURE.md (full picture)
2. UX_DASHBOARDS_BY_PERSONA.md (UI requirements)
3. specs/canonical_packet.schema.json (data contracts)
4. notebooks/ (source of truth for logic)

### Copywriter/Content Designer
1. UX_MESSAGE_TEMPLATES_AND_FLOWS.md (templates)
2. UX_AND_USER_EXPERIENCE.md (tone guidelines)
3. Docs/personas_scenarios/ (context for scenarios)

---

## Related Documentation

### Core Specs
- `specs/canonical_packet.schema.json` - Data structure behind all UX
- `notebooks/NB02_V02_SPEC.md` - Decision logic that drives UX
- `Docs/V02_GOVERNING_PRINCIPLES.md` - Implementation principles

### Persona & Scenario Docs
- `Docs/personas_scenarios/STAKEHOLDER_MAP.md` - All personas defined
- `Docs/personas_scenarios/P1_SOLO_AGENT_SCENARIOS.md` - Solo agent workflows
- `Docs/personas_scenarios/S1S2_CUSTOMER_SCENARIOS.md` - Customer experience

### Analysis Docs
- `memory/HOLISTIC_PROJECT_ASSESSMENT.md` - Project-level perspective
- `memory/codebase_analysis_2026-04-12.md` - Technical state analysis

---

## Design Principles (All Docs)

1. **Traveler-Safe Boundary**: Never show internal concepts to travelers
2. **WhatsApp-First**: Design for mobile messaging first
3. **Progressive Disclosure**: Summary first, details on click
4. **Action-Oriented**: Every view has clear next action
5. **Multi-Persona**: Same data, different presentations

---

## Open Design Questions

| Question | Status | Owner |
|----------|--------|-------|
| Agent review vs auto-send | Open | UX |
| Structured forms vs natural questions | Open | UX |
| Audit mode public vs agent-shared links | Open | PM |
| Real-time updates: Live vs batch | Open | Engineering |
| Mobile: Native vs responsive web | Open | Engineering |

---

## Version History

| Date | Change | Author |
|------|--------|--------|
| 2026-04-13 | Initial UX documentation created | Claude (exploration session) |

---

*This index will be updated as UX documentation evolves.*
