- [Product Vision and Model](PRODUCT_VISION_AND_MODEL.md) — The B2B Agency OS thesis and sourcing hierarchy.
- [Detailed Agent Map](DETAILED_AGENT_MAP.md) — Catalog of all 20+ agents, roles, and v1 stack.
- [Voice Intake and Orchestration](VOICE_ORCHESTRATION_AND_SESSIONS.md) — 2-screen model, routing loop, and "brackets" logic.
- [Audit and Intelligence Engine](AUDIT_AND_INTELLIGENCE_ENGINE.md) — Wasted-spend detection, URL ingestion, and market learning.
- [Technical Scaffold and Autoresearch](TECHNICAL_SCAFFOLD_AND_AUTORESEARCH.md) — Two-loop architecture and prompt registry.
- [Data Model and Taxonomy](DATA_MODEL_AND_TAXONOMY.md) — Brackets, budget splits, and the shared state schema.
- [Sourcing and Decision Policy](Sourcing_And_Decision_Policy.md) — Sourcing hierarchy and "Proceed/Ask" gating logic.
- [Discussion Log](DISCUSSION_LOG.md) — Audit trail of pivots and agent feedback.
- [Gemini Issue Review](gemini%20issue%20review.md) — Active issue register for identified/validated gaps.
- [First Principles Foundation (2026-04-14)](FIRST_PRINCIPLES_FOUNDATION_2026-04-14.md) — Core truths, objective function, and strict dependency-ordered build sequence.
- [Rolling Context Synthesis](ROLLING_CONTEXT_SYNTHESIS.md) — Active cross-part synthesis and implementation contracts.
- [First Mile Implementation](FIRST_MILE_IMPLEMENTATION.md) — Roadmap for the Agency Context deconstruction.

---

## Business Model (2026-04-13)

**IMPORTANT**: This is a **platform-led SaaS** (like Calendly/Typeform), NOT a white-label product.

- **[GTM & Data Network Effects](GTM_AND_DATA_NETWORK_EFFECTS.md)** — ⭐ GTM strategy, recommendation engines, data sharing: first principles analysis.
- **[Platform-Led vs White-Label](PLATFORM_LED_VS_WHITE_LABEL.md)** — Re-thought: Why white-label? Be like Calendly/Notion/Typeform instead.
- **[Business Model Correction](BUSINESS_MODEL_CORRECTION.md)** — You're building the platform FOR agencies, not running an agency.
- **[Single-Tenant MVP Strategy](SINGLE_TENANT_MVP_STRATEGY.md)** — Start simple: one agency first, add complexity later.
- **[Pricing and Customer Acquisition](PRICING_AND_CUSTOMER_ACQUISITION.md)** — Pricing tiers, free trials, and GTM channels: Facebook groups, host agencies, SEO.
- **[Pilot and Customer Discovery Strategy](PILOT_AND_CUSTOMER_DISCOVERY_STRATEGY.md)** — How to find willing agencies, run discovery calls, and structure pilots.

---

## Strategy and Operations (2026-04-14)

- **[Exploration Roadmap](EXPLORATION_ROADMAP_WHILE_BUILDING.md)** — 12 strategic areas to explore in parallel: legal, competitive, metrics, infrastructure, risks.

### Product Management

- **[Product Gaps and Unknowns](PM_PRODUCT_GAPS_AND_UNKNOWN.md)** — What we haven't thought through: roadmap, assumptions, metrics, moat, experiments, unknown unknowns.
- **[PM Templates and Frameworks](PM_TEMPLATES_AND_FRAMEWORKS.md)** — Ready-to-use templates: MVP scope, PRD, assumption log, weekly review, interview script, experiment brief, retrospectives.
- **[PM Execution Blueprint (2026-04-14)](PM_EXECUTION_BLUEPRINT_2026-04-14.md)** — Product-manager view of what makes the system tick: role-based outcomes, detailed execution flows, JTBD/aha synthesis, and prioritized P0-P2 plan.

### Competitive and Market

- **[Competitive Landscape](COMPETITIVE_LANDSCAPE.md)** — Who else is doing this? Why you? Positioning vs. ChatGPT, Duffel, existing tools.
- **[Pricing and Customer Acquisition](PRICING_AND_CUSTOMER_ACQUISITION.md)** — Pricing tiers, free trials, and GTM channels: Facebook groups, host agencies, SEO.
- **[Pilot and Customer Discovery Strategy](PILOT_AND_CUSTOMER_DISCOVERY_STRATEGY.md)** — How to find willing agencies, run discovery calls, and structure pilots.
- **[Launch Strategy](LAUNCH_STRATEGY.md)** — Soft launch → design partners → beta → public: staged launch plan.

### Product and Operations

- **[Metrics and Analytics](METRICS_AND_ANALYTICS.md)** — What to measure: North Star, activation, retention, NPS. Solo-friendly tracking.
- **[Technical Infrastructure](TECHNICAL_INFRASTRUCTURE.md)** — Stack: FastAPI + Postgres + HTMX + Clerk + Render. Hosting, costs, scaling.
- **[Integrations and Data Sources](INTEGRATIONS_AND_DATA_SOURCES.md)** — What APIs you actually need (LLM, holidays) vs. don't (GDS, CRM).
- **[Feedback Loops and Improvement](FEEDBACK_LOOPS_AND_IMPROVEMENT.md)** — Weekly reviews, categorization framework, regression testing.
- **[Support and Customer Success](SUPPORT_AND_CUSTOMER_SUCCESS.md)** — Channels, SLAs, onboarding, boundaries for solo builder.
- **[Risk Analysis](RISK_ANALYSIS.md)** — What could go wrong: API downtime, hallucinations, legal, burnout. Mitigations.

### Business and Personal

- **[Financial Modeling](FINANCIAL_MODELING.md)** — Unit economics, CAC/LTV, runway, break-even, freedom number calculator.
- **[Hiring and Scaling](HIRING_AND_SCALING.md)** — When to hire, first hire framework, contractor vs full-time, managing people.
- **[Personal Sustainability](PERSONAL_SUSTAINABILITY.md)** — Avoid burnout: boundaries, energy management, community, mental health.
- **[Legal Basics](LEGAL_BASICS.md)** — Minimal legal: TOS, privacy policy, AI disclaimers, data protection (India DPDP).

---

## UX and User Experience (2026-04-14)

### Core UX Framework

- **[Jobs to be Done](UX_JOBS_TO_BE_DONE.md)** — What each persona (agency owner, agent, junior, traveler) is trying to accomplish. Functional, emotional, and social jobs.
- **[User Journeys and Aha Moments](UX_USER_JOURNEYS_AND_AHA_MOMENTS.md)** — Detailed journey maps from pain to delight. Before/After states, emotional shifts, value realization.
- **[Detailed User Flows](UX_DETAILED_USER_FLOWS.md)** — Screen-by-screen flows: onboarding, intake, processing, options generation, client presentation.
- **[Synthetic Data and Fixtures](SYNTHETIC_DATA_AND_FIXTURES.md)** — Schemas, test messages, fixtures for development. Clean/moderate/messy/edge cases.

### Previous UX Docs (2026-04-13)

> **Note**: Earlier docs assumed direct-to-consumer incorrectly. Refer to 2026-04-14 docs for platform-led B2B model.

- **[UX Overview](UX_AND_USER_EXPERIENCE.md)** — End-to-end UX analysis: B2B2C architecture, what travelers see vs agents see.
- **[Message Templates](UX_MESSAGE_TEMPLATES_AND_FLOWS.md)** — Actual WhatsApp/email templates, conversation flows, tone guidelines.
- **[Dashboards by Persona](UX_DASHBOARDS_BY_PERSONA.md)** — Wireframes for Solo Agent, Agency Owner, Junior Agent views.
- **[Technical Architecture](UX_TECHNICAL_ARCHITECTURE.md)** — How NB01-NB03 connect to web/mobile UI, API design, state management.
- **[Audit Mode Deep Dive](UX_AUDIT_MODE_DEEP_DIVE.md)** — Direct-to-consumer wedge feature: landing page, upload flow, lead capture.
- **[WhatsApp Integration](UX_WHATSAPP_INTEGRATION_STRATEGY.md)** — Individual founder vs business: manual MVP, WATI, official API options.
- **[Multi-Channel Strategy](UX_MULTI_CHANNEL_STRATEGY.md)** — Beyond WhatsApp: portal links, email, SMS, omnichannel routing.
