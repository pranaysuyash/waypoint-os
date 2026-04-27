- [Project Thesis](project_thesis.md) — Core philosophy and agency-centric model.
- [Routing & Optimization Strategy](routing_and_optimization_strategy.md) — Architecture for dynamic routing and offline self-improvement.
- [Codebase Analysis 2026-04-12](codebase_analysis_2026-04-12.md) — Comprehensive analysis: what's good, bad, and needs improvement.
- [Full Documentation Wiki](../Docs/INDEX.md) — Exhaustive product and technical specs.
- **[Business Model Correction](../Docs/BUSINESS_MODEL_CORRECTION.md)** — ⚠️ CRITICAL: This is a white-label B2B SaaS platform, NOT a direct-to-consumer agency.
- [UX and User Experience](../Docs/UX_AND_USER_EXPERIENCE.md) — End-to-end flow analysis: what travelers see vs agents see.
- [UX Message Templates](../Docs/UX_MESSAGE_TEMPLATES_AND_FLOWS.md) — Actual messages travelers receive, conversation patterns.
- [UX Dashboards by Persona](../Docs/UX_DASHBOARDS_BY_PERSONA.md) — Different views for solo agents, agency owners, and juniors.
- [UX Technical Architecture](../Docs/UX_TECHNICAL_ARCHITECTURE.md) — NB01-NB03 → API → UI migration path.
- [UX Audit Mode](../Docs/UX_AUDIT_MODE_DEEP_DIVE.md) — Direct-to-consumer wedge feature.
- [UX WhatsApp Integration](../Docs/UX_WHATSAPP_INTEGRATION_STRATEGY.md) — Individual founder vs business: manual MVP first.
- [UX Multi-Channel Strategy](../Docs/UX_MULTI_CHANNEL_STRATEGY.md) — Omnichannel: portal links, email, SMS, not just WhatsApp.
- **[Platform-Led vs White-Label](../Docs/PLATFORM_LED_VS_WHITE_LABEL.md)** — ⚠️ Be like Calendly/Typeform, not white-label. Single platform, no custom domains for MVP.
- **[Single-Tenant MVP Strategy](../Docs/SINGLE_TENANT_MVP_STRATEGY.md)** — Start with one agency, add multi-tenant later.
- **[GTM & Data Network Effects](../Docs/GTM_AND_DATA_NETWORK_EFFECTS.md)** — No recommendation engines needed. Tool value > data aggregation.
- **[Pricing and Customer Acquisition](../Docs/PRICING_AND_CUSTOMER_ACQUISITION.md)** — ₹999-₹19,999 tiers, free trials, Facebook groups, host agencies.

## Strategic Docs (2026-04-14)

- **[Exploration Roadmap](../Docs/EXPLORATION_ROADMAP_WHILE_BUILDING.md)** — 12 areas to explore while building
- **[Competitive Landscape](../Docs/COMPETITIVE_LANDSCAPE.md)** — Positioning vs. ChatGPT, Duffel, status quo tools
- **[Pilot Strategy](../Docs/PILOT_AND_CUSTOMER_DISCOVERY_STRATEGY.md)** — Finding agencies, discovery calls, pilot structure
- **[Launch Strategy](../Docs/LAUNCH_STRATEGY.md)** — Staged launch: friends → design partners → beta → public
- **[Metrics and Analytics](../Docs/METRICS_AND_ANALYTICS.md)** — North Star, activation, retention, NPS
- **[Technical Infrastructure](../Docs/TECHNICAL_INFRASTRUCTURE.md)** — FastAPI + Postgres + HTMX + Clerk + Render
- **[Integrations](../Docs/INTEGRATIONS_AND_DATA_SOURCES.md)** — What to integrate (LLM, holidays) vs. skip (GDS)
- **[Feedback Loops](../Docs/FEEDBACK_LOOPS_AND_IMPROVEMENT.md)** — Weekly reviews, categorization, regression testing
- **[Support & CS](../Docs/SUPPORT_AND_CUSTOMER_SUCCESS.md)** — Channels, SLAs, onboarding, solo boundaries
- **[Risk Analysis](../Docs/RISK_ANALYSIS.md)** — API risks, business risks, legal risks, mitigations
- **[Financial Modeling](../Docs/FINANCIAL_MODELING.md)** — Unit economics, CAC/LTV, runway, freedom number
- **[Hiring & Scaling](../Docs/HIRING_AND_SCALING.md)** — When/who to hire, contractors vs full-time
- **[Personal Sustainability](../Docs/PERSONAL_SUSTAINABILITY.md)** — Avoid burnout, boundaries, community, mental health
- **[Legal Basics](../Docs/LEGAL_BASICS.md)** — TOS, privacy policy, AI disclaimers, DPDP compliance

## UX Documentation (2026-04-14)

- **[Jobs to be Done](../Docs/UX_JOBS_TO_BE_DONE.md)** — What each persona is trying to accomplish
- **[User Journeys and Aha Moments](../Docs/UX_USER_JOURNEYS_AND_AHA_MOMENTS.md)** — Journey maps with emotional shifts
- **[Detailed User Flows](../Docs/UX_DETAILED_USER_FLOWS.md)** — Screen-by-screen interaction design
- **[Synthetic Data and Fixtures](../Docs/SYNTHETIC_DATA_AND_FIXTURES.md)** — Test data, schemas, generators

## Research & Destination Intelligence (2026-04-26)

- **⚠️ [Destination Intelligence Vision](../Docs/research/DESTINATION_INTELLIGENCE_VISION_2026-04-26.md)** — READ FIRST before any research, content, SEO, or product feature work. The strategic thesis: we build the world's most comprehensive real-time destination intelligence platform. Every data point (weather, crime, AQI, costs, laws, food safety, connectivity, etc.) becomes a product feature + SEO content + free tool + programmatic page + Content Prism triple. Data compounds into an unreplicable moat.
- **[Research Opportunity Master List](../Docs/research/RESEARCH_OPPORTUNITY_MASTER_LIST_2026-04-25.md)** — 1,897 research items across 56 categories (A–BD). Covers market intelligence, customer research, product features, industry domains, technology, business models, destination intelligence, everyday practical knowledge, programmatic SEO, scoring indices, free tools, data acquisition strategy, and Content Prism (3-audience) topics. Only 211 items done; 1,686 open.

## Product Management (2026-04-14)

- **[Product Gaps and Unknowns](../Docs/PM_PRODUCT_GAPS_AND_UNKNOWN.md)** — Roadmap gaps, assumptions, validation plan, moat strategy
- **[PM Templates and Frameworks](../Docs/PM_TEMPLATES_AND_FRAMEWORKS.md)** — MVP scope, PRD, assumption log, experiment briefs, retrospectives

## Environment Setup

- **Package manager**: `uv` (https://docs.astral.sh/uv/)
- **Python version**: 3.13 (see `.python-version`)
- **Virtual env**: `.venv/` (created by `uv sync`)
- **Run notebooks/tests**: `uv run python script.py` or `uv run jupyter notebook`
- **Add dependencies**: `uv add <package>`
- **All commands must use `uv run` or `.venv/bin/python` — never system Python**
