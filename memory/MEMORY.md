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

## Environment Setup

- **Package manager**: `uv` (https://docs.astral.sh/uv/)
- **Python version**: 3.13 (see `.python-version`)
- **Virtual env**: `.venv/` (created by `uv sync`)
- **Run notebooks/tests**: `uv run python script.py` or `uv run jupyter notebook`
- **Add dependencies**: `uv add <package>`
- **All commands must use `uv run` or `.venv/bin/python` — never system Python**
