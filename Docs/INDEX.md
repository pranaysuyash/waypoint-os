- [Product Vision and Model](PRODUCT_VISION_AND_MODEL.md) — The B2B Agency OS thesis and sourcing hierarchy.
- [Detailed Agent Map](DETAILED_AGENT_MAP.md) — Catalog of all 20+ agents, roles, and v1 stack.
- [Voice Intake and Orchestration](VOICE_ORCHESTRATION_AND_SESSIONS.md) — 2-screen model, routing loop, and "brackets" logic.
- [Audit and Intelligence Engine](AUDIT_AND_INTELLIGENCE_ENGINE.md) — Wasted-spend detection, URL ingestion, and market learning.
- [Technical Scaffold and Autoresearch](TECHNICAL_SCAFFOLD_AND_AUTORESEARCH.md) — Two-loop architecture and prompt registry.
- [Data Model and Taxonomy](DATA_MODEL_AND_TAXONOMY.md) — Brackets, budget splits, and the shared state schema.
- [Sourcing and Decision Policy](Sourcing_And_Decision_Policy.md) — Sourcing hierarchy and "Proceed/Ask" gating logic.
- [Lead Lifecycle and Retention](LEAD_LIFECYCLE_AND_RETENTION.md) — Unified state machine, schema, scoring, and interventions for repeat, ghosting, window-shopping, and churn.
- [Discussion Log](DISCUSSION_LOG.md) — Audit trail of pivots and agent feedback.
- [Thesis Deep Dive Discussion (2026-04-16)](DISCUSSION_THESIS_DEEP_DIVE_2026-04-16.md) — Four-thread analysis of PROJECT_THESIS.md: copilot autonomy line, intelligence layer lead-gen model, sourcing hierarchy configurability, per-person suitability depth.
- [Architecture Decision: D4+D6 Suitability & Audit (2026-04-16)](ARCHITECTURE_DECISION_D4_D6_SUITABILITY_AUDIT_2026-04-16.md) — Full production architecture for suitability engine (activity_matcher) and audit eval suite. Protocol-based plugin pattern, manifest-driven eval, phased by dependency.
- [Architecture Decision: LLM Cache + NB05/NB06 (2026-04-16)](ARCHITECTURE_DECISION_LLM_CACHE_NB05_NB06_2026-04-16.md) — LLM output extraction/caching strategy, NB05 golden-path demo system, NB06 shadow-mode replay. Extends existing `src/decision/hybrid_engine.py` pattern to all LLM touchpoints.
- [Architecture Decision Addendum: D4/D6 Sub-Decisions (2026-04-18)](ARCHITECTURE_DECISION_D4_SUBDECISIONS_ADDENDUM_2026-04-18.md) — Resolves D4.1–D4.3, D6.1–D6.2. Evolves scoring from per-activity to three-tier (deterministic tag rules → tour-context sequence rules → LLM contextual). Extends `SuitabilityContext` with day/trip activity lists. Fixture tiers: isolated → day-sequence → trip-sequence.
- [Architecture Decision: D1 Autonomy Gradient (2026-04-18)](ARCHITECTURE_DECISION_D1_AUTONOMY_GRADIENT_2026-04-18.md) — Agency-level autonomy policy with per-decision_state approval gates. Safety invariant: STOP_NEEDS_REVIEW always blocks. Adaptive autonomy via customer+trip classification identified as evolution path, pending deep dive.
- [Plugin System Exploration (Draft, 2026-04-17)](PLUGIN_SYSTEM_EXPLORATION_DRAFT_2026-04-17.md) — Draft exploration of protocol/registry plugin architecture, execution guardrails, fallback model, and phased rollout.
- [Coverage Assessment (2026-04-15)](COVERAGE_ASSESSMENT_2026-04-15.md) — Summary of what is now covered across risks, stakeholders, scenarios, use cases, and markets, plus remaining documentation/runtime gaps.
- [Coverage Matrix (2026-04-15)](COVERAGE_MATRIX_2026-04-15.md) — Control document separating what is documented, scenario-covered, tested, and implemented across risks, stakeholders, lifecycle, markets, and commercial logic.
- [Issue Review](issue_review.md) — Active issue register for identified/validated gaps.
- [Process Issue Review (2026-04-15)](process_issue_review_2026-04-15.md) — Runtime/code issues identified during implementation passes with project-neutral naming.
- [Status Matrix (2026-04-15)](status/STATUS_MATRIX.md) — Control layer that preserves full scope while mapping what is active now vs phased orchestration expansion.
- [Coverage Closure Build Queue (2026-04-15)](status/COVERAGE_CLOSURE_BUILD_QUEUE_2026-04-15.md) — Dependency-ordered queue derived from the coverage matrix, aligned to runtime modules, tests, and acceptance signals.
- [Phase 1 Build Queue (2026-04-15)](status/PHASE_1_BUILD_QUEUE.md) — Ordered execution checklist for deterministic foundations before broader specialist activation.
- [Frontend Product Spec (Full, 2026-04-15)](FRONTEND_PRODUCT_SPEC_FULL_2026-04-15.md) — Full product frontend architecture and screen contracts (internal/operator/owner/traveler/public), no Streamlit path.
- [Frontend Workflow Coverage Baseline (2026-04-16)](FRONTEND_WORKFLOW_COVERAGE_2026-04-16.md) — Verified current-state route/workflow coverage map with surface-by-surface gap analysis.
- [Frontend Workflow Implementation Checklist (2026-04-16)](FRONTEND_WORKFLOW_IMPLEMENTATION_CHECKLIST_2026-04-16.md) — Phased execution checklist with route-level acceptance criteria and delivery gates.
- [Next.js Implementation Track (2026-04-15)](status/NEXTJS_IMPLEMENTATION_TRACK_2026-04-15.md) — Corrected execution plan with spine-aligned BFF enums and phased build order (foundation -> workspace core -> expansion).
- [Activity Suitability Implementation Handoff (2026-04-16)](status/ACTIVITY_SUITABILITY_IMPLEMENTATION_HANDOFF_2026-04-16.md) — Execution-ready handoff: provider field mapping, scoring pseudocode, ingestion order, confidence model, and acceptance gates for Product B/GTM suitability matrix.
- [Operator Workbench Component Spec (2026-04-15)](status/OPERATOR_WORKBENCH_COMPONENT_SPEC_2026-04-15.md) — Screen-level behavior reference for Workbench/Flow Simulation (not runtime stack authority).
- [Workbench Acceptance Checklist (2026-04-15)](status/WORKBENCH_ACCEPTANCE_CHECKLIST_2026-04-15.md) — Acceptance gates used as behavior validation reference for the Next.js workbench surface.
- [Vendor/Cost Tracking Gap Analysis (2026-04-16)](VENDOR_COST_TRACKING_GAP_ANALYSIS_2026-04-16.md) — Critical gap: no vendor management, margin calculation, or sourcing hierarchy logic. Documented as intentional deferral.
- [Vendor/Cost/Sourcing Discovery Gap Analysis (2026-04-16)](VENDOR_COST_TRACKING_DISCOVERY_GAP_ANALYSIS_2026-04-16.md) — Full deep-dive: evidence inventory, gap taxonomy, dependency graph, data models, phase-in plan for vendor/supplier/cost/margin/sourcing.
- [Master Gap Register (2026-04-16)](MASTER_GAP_REGISTER_2026-04-16.md) — ⭐ Single source of truth: ALL 17 gap areas with priority, dependencies, deep-dive status, and naming convention.
- [Session Writeup: Trip Workspace Fix (2026-04-17)](SESSION_WRITEUP_TRIP_WORKSPACE_FIX_2026-04-17.md) — Fixed broken trip loading (blank workspace on click), enriched all 7 trips with full pipeline mock data, wired Process Trip button, cleaned up wording.
- [Hybrid Decision Engine Validation (2026-04-17)](validation/hybrid_engine_validation_report.md) — ✅ Validation of hybrid decision engine with 100% accuracy, 34% rule hit rate, cache key bug fix, and production readiness.
- [Validation Session Summary (2026-04-17)](validation/session_summary_20260417.md) — Implementation summary of hybrid engine validation, bug fixes, and test coverage expansion.

### Validation and Testing (2026-04-17)

- [Hybrid Decision Engine Architecture](HYBRID_DECISION_ARCHITECTURE_2026-04-16.md) — Core philosophy: Rules + LLM + Cache. Decision classification, cache schema, rule patterns, LLM integration, and cost optimization.
- [LLM Decision Layer Migration Guide (2026-04-16)](LLM_DECISION_LAYER_MIGRATION_GUIDE_2026-04-16.md) — How to migrate from hardcoded decisions to hybrid engine, step-by-step migration patterns.
- [How to Add a Decision Rule](development/how_to_add_a_decision_rule.md) — Step-by-step guide for adding new decision rules to increase free decision rate.
- [Rule Expansion TODO](development/rule_expansion_todo.md) — 📋 Future exploration opportunities: push to 70%+ rule hit rate, learn from real traffic, dynamic rule compilation.

### Exploration Backlog (2026-04-18)

- [Exploration Backlog](exploration/backlog.md) — 📋 Living list of areas to explore: intake, safety, decisions, API, frontend, testing, observability, operations, integrations, security, and more. Add items freely.

### Discovery Gap Deep-Dives (2026-04-16)

- [Gap #01: Vendor/Cost/Sourcing/Margin](VENDOR_COST_TRACKING_DISCOVERY_GAP_ANALYSIS_2026-04-16.md) — ✅ Complete
- [Gap #02: Data Persistence](DISCOVERY_GAP_DATA_PERSISTENCE_2026-04-16.md) — ✅ Complete
- [Gap #03: Communication/Channels](DISCOVERY_GAP_COMMUNICATION_CHANNELS_2026-04-16.md) — ✅ Complete
- [Gap #04: Financial State Tracking](DISCOVERY_GAP_FINANCIAL_STATE_2026-04-16.md) — ✅ Complete
- [Gap #05: Cancellation/Refund Policy Engine](DISCOVERY_GAP_CANCELLATION_REFUND_2026-04-16.md) — ✅ Complete
- [Gap #06: Customer Lifecycle & Cross-Trip Memory](DISCOVERY_GAP_CUSTOMER_LIFECYCLE_2026-04-16.md) — ✅ Complete
- [Gap #07: LLM/AI Integration Architecture](DISCOVERY_GAP_LLM_AI_INTEGRATION_2026-04-16.md) — ✅ Complete
- [Gap #08: Auth/Identity & Multi-Agent](DISCOVERY_GAP_AUTH_IDENTITY_MULTI_AGENT_2026-04-16.md) — ✅ Complete
- Gaps #09-#17: ⬜ Pending → ✅ All complete:
  - [Gap #09: In-Trip Ops & Emergency Protocol](DISCOVERY_GAP_IN_TRIP_OPS_EMERGENCY_2026-04-16.md)
  - [Gap #10: Document/Visa Management](DISCOVERY_GAP_DOCUMENT_VISA_MANAGEMENT_2026-04-16.md)
  - [Gap #11: Post-Trip/Feedback/Learning Loops](DISCOVERY_GAP_POST_TRIP_FEEDBACK_LOOPS_2026-04-16.md)
  - [Gap #12: Analytics/Reporting Pipeline](DISCOVERY_GAP_ANALYTICS_REPORTING_2026-04-16.md)
  - [Gap #13: Audit Trail/Action Logging](DISCOVERY_GAP_AUDIT_TRAIL_ACTION_LOGGING_2026-04-16.md)
  - [Gap #14: Seasonality/Dynamic Pricing](DISCOVERY_GAP_SEASONALITY_DYNAMIC_PRICING_2026-04-16.md)
  - [Gap #15: Insurance/TCS/GST Compliance](DISCOVERY_GAP_INSURANCE_TCS_GST_2026-04-16.md)
  - [Gap #16: Configuration Management](DISCOVERY_GAP_CONFIGURATION_MANAGEMENT_2026-04-16.md)
  - [Gap #17: Industry Blind Spots](DISCOVERY_GAP_INDUSTRY_BLIND_SPOTS_2026-04-16.md)
- [First Principles Foundation (2026-04-14)](FIRST_PRINCIPLES_FOUNDATION_2026-04-14.md) — Core truths, objective function, and strict dependency-ordered build sequence.
- [Rolling Context Synthesis](ROLLING_CONTEXT_SYNTHESIS.md) — Active cross-part synthesis and implementation contracts.
- [First Mile Implementation](FIRST_MILE_IMPLEMENTATION.md) — Roadmap for the Agency Context deconstruction.
- [Meta Design Reference Synthesis (2026-04-14)](context/META_DESIGN_REFERENCE_SYNTHESIS_2026-04-14.md) — Extracted actions from 5:45 PM external design artifacts (`Do now / Do later / Discuss`).
- [Institutional Memory Layer Synthesis (2026-04-14)](context/INSTITUTIONAL_MEMORY_LAYER_SYNTHESIS_2026-04-14.md) — Missing angles and operating model for Template Genome, Supplier Graph, Pricing Memory, Customer Genome, and Playbook Engine.
- [Geography Extraction Design Decision (2026-04-15)](context/GEOGRAPHY_EXTRACTION_DESIGN_DECISION_2026-04-15.md) — Hybrid city database: GeoNames (CC-BY 4.0) + world-cities.json (ODbL-1.0) + organic accumulation. Attribution required.
- [Trip Feasibility Scenario (2026-04-15)](context/TRIP_FEASIBILITY_SCENARIO_2026-04-15.md) — Synthetic route, investigation tasks, input/output schema, and evaluated feasibility result for multi-country travel planning.
- [Trip Budget Reality Scenario (2026-04-15)](context/TRIP_BUDGET_REALITY_SCENARIO_2026-04-15.md) — Synthetic budget investigation with missing cost bucket coverage, sub-bucket estimates, and quote shock prevention.
- [Trip Visa & Document Risk Scenario (2026-04-15)](context/TRIP_VISA_DOCUMENT_RISK_SCENARIO_2026-04-15.md) — Synthetic document risk investigation for multi-border travel with visa, transit, and insurance uncertainty.
- [Trip Transfer Complexity Scenario (2026-04-15)](context/TRIP_TRANSFER_COMPLEXITY_SCENARIO_2026-04-15.md) — Synthetic transfer and route friction investigation for a multi-city itinerary with high mobility demand.
- [Trip Activity & Pacing Scenario (2026-04-15)](context/TRIP_ACTIVITY_PACING_SCENARIO_2026-04-15.md) — Synthetic pacing risk investigation for a multi-region active itinerary with a senior and child.
- [Risk Area Catalog (2026-04-15)](context/RISK_AREA_CATALOG_2026-04-15.md) — Customer, vendor, operational, and external risk taxonomy for travel feasibility and agency operations.
- [Itinerary Checker GTM Wedge (2026-04-14)](context/ITINERARY_CHECKER_GTM_WEDGE_2026-04-14.md) — Free checker strategy, 15-rule NB02-lite scope, API contract, rollout plan, and data-flywheel linkage.
- [Decision Memo: Itinerary Checker (2026-04-14)](context/DECISION_MEMO_ITINERARY_CHECKER_2026-04-14.md) — Go/no-go decision, 30-day gates, locked v1 scope, and execution cadence.
- [SEO + Next.js GTM Playbook Synthesis (2026-04-14)](context/SEO_NEXTJS_GTM_PLAYBOOK_SYNTHESIS_2026-04-14.md) — Integrated external implementation draft with keep/change/defer decisions for practical MVP rollout.
- [Travel Agency Context 2 Synthesis (2026-04-14)](context/TRAVEL_AGENCY_CONTEXT_2_SYNTHESIS_2026-04-14.md) — One-time-link workspace framing, 5-core architecture compression, canonical packet reinforcement, and commercial-layer priorities.
- [Workflow Compliance Entry (2026-04-15)](context/WORKFLOW_COMPLIANCE_ENTRY_2026-04-15.md) — Explicit Analysis→Document→Plan→Research→Decision→Implement→Test→Results execution record for lifecycle/churn additions.

---

## Business Model (2026-04-13)

**IMPORTANT**: This is a **platform-led SaaS** (like Calendly/Typeform), NOT a white-label product.

- **[GTM & Data Network Effects](GTM_AND_DATA_NETWORK_EFFECTS.md)** — ⭐ GTM strategy, recommendation engines, data sharing: first principles analysis.
- **[Platform-Led vs White-Label](PLATFORM_LED_VS_WHITE_LABEL.md)** — Re-thought: Why white-label? Be like Calendly/Notion/Typeform instead.
- **[Business Model Correction](BUSINESS_MODEL_CORRECTION.md)** — You're building the platform FOR agencies, not running an agency.
- **[Single-Tenant MVP Strategy](SINGLE_TENANT_MVP_STRATEGY.md)** — Start simple: one agency first, add complexity later.
- **[Pricing and Customer Acquisition](PRICING_AND_CUSTOMER_ACQUISITION.md)** — Pricing tiers, free trials, and GTM channels: Facebook groups, host agencies, SEO.
- **[Pricing Packaging Discussion (Draft, 2026-04-17)](PRICING_PACKAGING_DISCUSSION_DRAFT_2026-04-17.md)** — Working packaging direction: ₹6k default plan (1 owner/admin + 4 team), team packs, and modular add-ons. Explicitly non-final.
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

### Fixture Files (data/fixtures/)

- **[product_persona_flows_synthetic_v1.json](../data/fixtures/product_persona_flows_synthetic_v1.json)** — PM/UX synthetic scenarios with personas, JTBD, aha moments, flows, and flywheel instrumentation.
- **[test_messages.json](../data/fixtures/test_messages.json)** — 30 categorized test messages (clean/moderate/messy/contradictory/edge cases) for intake and feasibility testing.
- **[trip_examples.json](../data/fixtures/trip_examples.json)** — Complete trip examples with full journey data for development and demos.
- **[README.md](../data/fixtures/README.md)** — Fixture files documentation, usage examples, data structures.

## Architecture Decision Records

- **[ADR-001: Scenario Handling Architecture](architecture/adr/ADR-001-SCENARIO-HANDLING-ARCHITECTURE.md)** — Enhanced scenario handling system with structured risk format.
- **[ADR-002: Spine API Architecture](architecture/adr/ADR-002-SPINE-API-ARCHITECTURE.md)** — HTTP service architecture replacing subprocess approach for better performance and scalability.

### Previous UX Docs (2026-04-13)

> **Note**: Earlier docs assumed direct-to-consumer incorrectly. Refer to 2026-04-14 docs for platform-led B2B model.

- **[UX Overview](UX_AND_USER_EXPERIENCE.md)** — End-to-end UX analysis: B2B2C architecture, what travelers see vs agents see.
- **[Message Templates](UX_MESSAGE_TEMPLATES_AND_FLOWS.md)** — Actual WhatsApp/email templates, conversation flows, tone guidelines.
- **[Dashboards by Persona](UX_DASHBOARDS_BY_PERSONA.md)** — Wireframes for Solo Agent, Agency Owner, Junior Agent views.
- **[Technical Architecture](UX_TECHNICAL_ARCHITECTURE.md)** — How NB01-NB03 connect to web/mobile UI, API design, state management.
- **[Audit Mode Deep Dive](UX_AUDIT_MODE_DEEP_DIVE.md)** — Direct-to-consumer wedge feature: landing page, upload flow, lead capture.
- **[WhatsApp Integration](UX_WHATSAPP_INTEGRATION_STRATEGY.md)** — Individual founder vs business: manual MVP, WATI, official API options.
- **[Multi-Channel Strategy](UX_MULTI_CHANNEL_STRATEGY.md)** — Beyond WhatsApp: portal links, email, SMS, omnichannel routing.
