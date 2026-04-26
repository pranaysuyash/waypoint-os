# PII and LLM Model Risk Research

This document captures the research agenda for privacy, PII handling, and model risk in travel AI systems. It is deliberately broad to include travel industry-specific data risks, LLM integration risks, fine-tuning considerations, and open model governance.

## Why this matter for travel AI

Travel products are inherently sensitive: traveler identities, itineraries, companion details, health requirements, and immigration documents are all high-risk data.
When travel products use LLMs or AI agents, that risk compounds because the model can ingest, retain, or generate sensitive information unless the pipeline, training, and inference flows are designed to prevent it.

## Core research areas

### 1. Travel PII classification and handling

Key questions
- What travel fields are high-risk PII vs low-risk operational metadata?
- Which store types must be protected immediately (`TripStore`, `TeamStore`, permit pipelines, payment flows)?
- How should we classify synthetic/test data vs real user data in the travel pipeline?
- What guardrails should prevent real data from entering the current JSON/flat-file persistence?

Research directions
- PII classification matrix for travel: DNI, passport numbers, visa data, itinerary dates, party composition, health/mobility data, sponsor disclosure, payment velocities
- Data lifecycle map: capture → process → store → transmit → delete
- Minimal data retention strategy for travel AI assistants
- Encryption and access control requirements for travel-specific stores

### 2. LLM/AI pipeline privacy and leakage risk

Key questions
- Which parts of the current spine pipeline are LLM-ready and what would happen if they accidentally processed PII?
- What are the privacy risks of prompt engineering in travel: hidden fields, freeform notes, and trip summaries?
- How do we prevent LLMs from emitting crawlerable or inadvertent travel PII?

Research directions
- Prompt design guardrails for travel agent pipelines: traveler-safe system context, explicit PII exclusion, output redaction
- Safe LLM inference layers: schema-constrained responses, post-response validation, and LLM hallucination mitigation
- LLM usage classification and guardrails for PII-sensitive flows (bookings, permits, approvals, traveler support)
- Blacklisting and sanitization patterns for travel PII in prompts and outputs

### 3. Model governance, fine-tuning, and open-source LLM strategy

Key questions
- What model class should the travel product use: hosted proprietary, open-source local, or hybrid?
- When is fine-tuning appropriate for travel-specific tasks, and how can we do it without training on raw traveler PII?
- How do we assess OpenAI’s new open-source PII-safe model (and equivalent open-weight models) for travel privacy and control?

Research directions
- Vendor risk matrix: OpenAI hosted vs OpenAI open-source PII-safe model vs local open-source model vs hybrid inference
- Fine-tuning strategy using synthetic or de-identified travel data
- Private prompt engineering and retrieval-augmented generation without storing PII in the vector store
- Open-source model evaluation for travel: privacy, latency, cost, customization, and regulatory fit
- Keep both the specific OpenAI open-source PII-safe model and equivalent open-weight model offerings as parallel evaluation tracks for travel privacy and control
- Specific evaluation of OpenAI’s new open-source PII model as a potential privacy-first travel inference layer
- External operational context feeds: weather, atmosphere, crime, pollution, flight status, and advisory updates for booked destinations
- How to incorporate real-time environmental and disruption signals into travel AI decisions without expanding unnecessary data exposure

### 4. Data governance and compliance for travel AI agents

Key questions
- What compliance standards matter most for travel AI? GDPR, CCPA, DPDP, PCI, travel-specific confidentiality laws, and creator data disclosure rules.
- What governance controls are needed for AI agent decision logs, audit trails, and explainability?
- How do we classify the system when it moves from dogfood to real users?

Research directions
- Real-user escalation rules: B/C/D classification triggers based on PII volume and sensitivity
- Audit log design: retention, anonymization, access control, and review workflows
- Policy and compliance matrix for travel AI agents, including travel industry-specific disclosure and creator sponsorship rules
- Consent and traveler preference handling for AI-assisted bookings, content personalization, and creator partner outreach

### 5. Practical engineering safeguards

Key questions
- Can we add real-time PII detection at the point of ingestion before data enters the spine pipeline?
- Can we build a safe model pipeline that uses deterministic extraction first and LLM only for non-PII semantic judgment?
- How should we wire LLM provider selection, cost control, and privacy policies into the current architecture?

Research directions
- PII guard module for `ExtractionPipeline` and `PromptBundle` construction
- LLMProvider abstraction with privacy-safe defaults and provider-level privacy policies
- Usage guard and audit guard for LLM calls in travel workflows
- Data retention and deletion controls for trip proposals, messages, and logs

## Research outputs to produce

- Travel PII classification matrix and escalation rules
- LLM model risk checklist for travel AI pipelines
- Fine-tuning policy for travel models using synthetic or anonymized data
- Open-source vs hosted model comparison for travel privacy and operational fit
- Technical design for PII-safe prompt and pipeline architecture
- Compliance decision guide for moving from dogfood to real users

## Connection to existing docs

This research should connect to and extend:
- `Docs/AUDIT_CLOSURE_TRIAGE_2026-04-26.md`
- `Docs/research/ID_SPEC_IDENTITY_VAULT.md`
- `Docs/DISCOVERY_GAP_LLM_AI_INTEGRATION_2026-04-16.md`
- `Docs/MULTI_AGENT_INFRASTRUCTURE_ASSESSMENT_2026-04-22.md`
- `Docs/RISK_ANALYSIS.md`
- `Docs/industry_domain/agency_operations/CREATOR_TRAVEL_AGENCY_SETTINGS_AND_AI_SUPPORT_CONTROLS.md`
- `Docs/industry_domain/CREATOR_TRAVEL_RESEARCH_ROADMAP.md`

## Next step

- Turn this into a concrete research plan by listing the top 5 evaluation questions, data sources, and prototype checks.
- Evaluate whether the existing spine pipeline can support privacy-safe LLM integration before any real user data enters the system.
