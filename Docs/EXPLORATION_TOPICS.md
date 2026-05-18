# Exploration Topics - Master Index

**Purpose**: Living document tracking research areas for the Travel Agency AI Copilot  
**Status**: Active - Continuously updated as project evolves  
**Last Updated**: 2026-05-11

---

## How to Use This Document

**This is the master index**. It provides:
- Overview of each exploration area
- Why it matters
- Current status
- Links to detailed research (when available)

**For deep research**, each topic has its own document:
- `research/INTEGRATION_ARCHITECTURE.md`
- `research/DATA_STRATEGY.md`
- etc.

**To add new topics**:
1. Add entry to this index
2. Create detailed doc in `research/` folder
3. Link both directions

---

## Topic Categories

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    EXPLORATION TOPICS MASTER MAP                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  INFRASTRUCTURE & CONNECTIVITY          AI/ML STRATEGY                      │
│  ├── Integration Architecture  [🔴]     ├── LLM Strategy & Costs         [ ] │
│  ├── Data Strategy & Persistence [🔴]   ├── Prompt Engineering          [ ] │
│  └── Security & Compliance       [ ]    └── Evaluation Framework        [ ] │
│                                                                             │
│  PRODUCT & USER EXPERIENCE              BUSINESS & GROWTH                   │
│  ├── Real-World Validation       [ ]    ├── Pricing & Monetization      [ ] │
│  ├── Competitive Landscape       [ ]    ├── Go-to-Market Strategy       [ ] │
│  └── Future Roadmap              [ ]    └── Partnership Opportunities   [ ] │
│                                                                             │
│  PIPELINE EVOLUTION                                                         │
│  ├── Notebook 04: Response Generation                                       │
│  ├── Notebook 05: Multi-Turn Conversations                                  │
│  └── Advanced: Learning & Optimization                                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

Legend:
[🔴] = High Priority (Blocking next phase)
[🟡] = Medium Priority (Enables scale)
[🟢] = Low Priority (Nice to have)
[ ] = Not Started
[✓] = Completed
```

---

## INFRASTRUCTURE & CONNECTIVITY

### 0. Architecture Topology 🟡 [EXPLORED]
**Status**: Current architecture classified; migration direction proposed

**Overview**: Clarifies whether Waypoint OS is a monolith, microservices, or another topology. Current verdict: **BFF + backend modular monolith in a monorepo**, with future worker/process boundaries for long-running jobs and integrations.

**Key Questions**:
- Which boundaries are real runtime boundaries today?
- Which boundaries should stay module-level while the product evolves?
- Which workloads justify a future worker or independent service?
- What should be cleaned before any extraction?

**Deliverable**: Architecture topology review with current-state evidence, topology options, target architecture, migration phases, and guardrails.

**Detailed Research**: [exploration/ARCHITECTURE_TOPOLOGY_REVIEW_2026-05-11.md](exploration/ARCHITECTURE_TOPOLOGY_REVIEW_2026-05-11.md)

**Related Topics**: Integration Architecture, Data Strategy & Persistence, Security & Compliance

### 1. Integration Architecture 🔴 [IN PROGRESS]
**Status**: High Priority - Research started

**Overview**: How the AI pipeline connects to real-world systems. The core AI is getting solid, but it needs to actually *do* things.

**Key Questions**:
- How does the system send/receive WhatsApp messages?
- Which hotel/flight booking APIs are accessible?
- What CRMs do travel agencies actually use?
- How are payments processed?
- Where are documents stored?

**Research Areas**:
- WhatsApp Business API vs WhatsApp Cloud API
- Hotel booking APIs (Booking.com, Expedia, direct hoteliers)
- Flight APIs (Amadeus, Sabre, Skyscanner)
- CRM connectors (Salesforce, Zoho, HubSpot, Excel/Google Sheets)
- Payment gateways (Razorpay, Stripe, direct bank)
- Document storage (AWS S3, Google Cloud, local)
- Email/SMS gateways (SendGrid, Twilio)

**Deliverable**: Integration architecture doc with API research, cost estimates, complexity ratings

**Detailed Research**: [research/INTEGRATION_ARCHITECTURE.md](research/INTEGRATION_ARCHITECTURE.md) *[ACTIVE]*

**Related Topics**: Data Strategy (storage), Security (compliance)

---

### 2. Data Strategy & Persistence 🔴 [IN PROGRESS]
**Status**: High Priority - Research started

**Overview**: Notebooks 01-02 use in-memory objects. Real system needs persistence. What gets stored, where, for how long?

**Key Questions**:
- How do we store CanonicalPackets? (JSONB vs normalized tables)
- What about vector similarity search? (customer matching, recommendations)
- How long do we keep travel documents?
- How do we handle PII (passport numbers, etc.)?
- What's the migration path from Excel/WhatsApp chaos?

**Research Areas**:
- Database selection (PostgreSQL, MongoDB, hybrid)
- Schema design for CanonicalPacket persistence
- Vector database for embeddings (Pinecone, Weaviate, pgvector)
- Data retention & GDPR compliance
- Backup & disaster recovery
- Migration tools from existing agency systems
- Audit trails for compliance

**Deliverable**: Data model diagrams, schema proposals, storage cost estimates

**Detailed Research**: [research/DATA_STRATEGY.md](research/DATA_STRATEGY.md) *[ACTIVE]*

**Related Topics**: Integration Architecture (data flow), Security (compliance)

---

### 3. Security & Compliance 🟡
**Status**: Medium Priority - Critical before real customers

**Overview**: Travel data is sensitive. Passport info, dates when homes are empty, payment details. Security can't be an afterthought.

**Key Questions**:
- How do we encrypt passport numbers?
- What compliance standards apply? (GDPR, local data laws)
- How do we handle authentication?
- What's the incident response plan?
- How do we secure API keys?

**Research Areas**:
- Data encryption at rest and in transit
- PII handling best practices
- Compliance frameworks (GDPR, ISO 27001)
- Authentication & authorization (OAuth, JWT)
- API key management (HashiCorp Vault, AWS Secrets Manager)
- Security audit checklist
- Incident response playbook

**Deliverable**: Security architecture, compliance checklist, threat model

**Detailed Research**: [research/SECURITY_AND_COMPLIANCE.md](research/SECURITY_AND_COMPLIANCE.md) *(create when started)*

**Related Topics**: Data Strategy (encryption), Integration Architecture (API security)

---

## AI/ML STRATEGY

### 4. LLM Strategy & Cost Optimization 🟡
**Status**: Medium Priority - Important for scalability

**Overview**: The system uses LLMs for extraction, classification, generation. Costs can explode at scale. Need a smart strategy.

**Key Questions**:
- Which model for which task? (GPT-4 vs Claude vs local)
- What's the cost per booking at different scales?
- How do we cache similar requests?
- What if OpenAI is down?
- How do we optimize prompts for tokens?

**Research Areas**:
- Model selection matrix (cost vs quality vs latency)
- Cost modeling (10/100/1000 bookings/month scenarios)
- Caching strategies (semantic cache for similar queries)
- Token optimization (prompt compression techniques)
- Fallback strategies (multi-provider setup)
- Local model options (Llama, Mistral for simple tasks)
- A/B testing framework for model selection

**Deliverable**: LLM strategy doc with cost models, provider comparison, optimization techniques

**Detailed Research**: [research/LLM_STRATEGY.md](research/LLM_STRATEGY.md) *(create when started)*

**Related Topics**: Prompt Engineering (optimization), Evaluation Framework (quality measurement)

---

### 5. Prompt Engineering 🟢
**Status**: Low Priority - Can evolve with system

**Overview**: Prompts are currently inline. Need a registry, versioning, and optimization system.

**Key Questions**:
- How do we version prompts?
- How do we A/B test prompt changes?
- What's the prompt registry structure?
- How do we track prompt performance?

**Research Areas**:
- Prompt registry architecture
- Versioning strategies (git-based, database)
- A/B testing framework
- Prompt performance tracking
- Few-shot example management
- Dynamic prompt composition

**Deliverable**: Prompt management system design

**Detailed Research**: [research/PROMPT_ENGINEERING.md](research/PROMPT_ENGINEERING.md) *(create when started)*

**Related Topics**: LLM Strategy (optimization), Notebook 04 (response generation)

---

### 6. Evaluation Framework 🟡
**Status**: Medium Priority - Needed for quality assurance

**Overview**: How do we know the system is getting better? Need metrics beyond "tests pass."

**Key Questions**:
- What metrics matter? (accuracy, latency, cost, user satisfaction)
- How do we evaluate extraction quality?
- How do we test decision quality?
- What's the human-in-the-loop feedback mechanism?

**Research Areas**:
- Evaluation metrics definition
- Gold dataset creation and maintenance
- Human evaluation workflows
- Automated evaluation pipelines
- Regression detection
- Continuous improvement processes

**Deliverable**: Evaluation framework with metrics, datasets, and workflows

**Detailed Research**: [research/EVALUATION_FRAMEWORK.md](research/EVALUATION_FRAMEWORK.md) *(create when started)*

**Related Topics**: LLM Strategy (performance), Real-World Validation (feedback)

---

### 6b. Knowledge Discovery from Data (KDD) 🟡 [EXPLORATION OPEN]
**Status**: Exploration drafted 2026-05-18. Not yet implemented. Worth pursuing because the data streams already exist (override audit, gate outcomes, trip events, validation reasons) and the highest-leverage application (override mining) directly feeds the known AI-override launch blocker.

**Overview**: Apply the Fayyad KDD pipeline (Selection → Preprocessing → Transformation → Data Mining → Interpretation) to the corpus of operator overrides, gate decisions, validation outcomes, and lifecycle events the app already persists. Goal is a continuous learning loop, not a vanity dashboard.

**Key Questions**:
- Can clustering the override corpus identify systematic failure modes the AI should learn from?
- Can association-rule mining on gate failures (e.g., NB01/NB02) discover intake → escalation patterns that drive extractor/validator improvements?
- Can mining successful trips surface the suitability signals the renderer is currently blocked on?
- What KDD applications are premature given current N per agency, and which work even at low N?
- How does the override corpus get versioned, labeled, and fed back into prompts/models without duplicating evaluation infrastructure?

**Highest-leverage applications** (ranked):
1. Override-mining → continuous-improvement loop (closes operator override blocker).
2. Escalation cause discovery via association rules on `Validation.gate/reasons`.
3. Suitability signal mining from successful trip outcomes.
4. Process mining on workflow timelines (time-to-stage, bottlenecks).
5. Cross-agency anomaly detection (defer until N is large enough).

**Non-goals**: a generic KDD dashboard; mining anything where N per agency is too small to be honest; duplicating the Evaluation Framework (this complements it by producing the patterns the evaluator measures against).

**Deliverable**: KDD pipeline design + override-corpus schema + first-pattern prototype (override clusters or gate-failure association rules) wired into a weekly digest.

**Detailed Research**: [exploration/KDD_KNOWLEDGE_DISCOVERY_EXPLORATION_2026-05-18.md](exploration/KDD_KNOWLEDGE_DISCOVERY_EXPLORATION_2026-05-18.md)

**v0 Implementation Scope** (handoff-ready): [exploration/KDD_V0_OVERRIDE_MINING_SCOPE_2026-05-18.md](exploration/KDD_V0_OVERRIDE_MINING_SCOPE_2026-05-18.md)

**Related Topics**: Evaluation Framework (#6, complementary), LLM Strategy (#4, override mining feeds prompt versioning), Advanced: Learning & Optimization (#15), Multi-Dimensional Priority Scoring (#20), Suitability renderer (cross-link to AI override controls launch blocker in `AGENTS.md`).

---

### 6c. Suitability Signal Mining 🟡 [EXPLORATION OPEN]
**Status**: Exploration drafted 2026-05-18. Recommended to defer one cycle behind KDD v0 (reuses same pipeline). Directly addresses the suitability-renderer launch blocker.

**Overview**: Mine successful trips (booked-and-stuck) for repeatable (destination × season × traveler-shape × budget-band) tuples. Each surviving pattern is a candidate suitability signal carrying sample size and lift.

**Key Questions**: see exploration doc.

**Deliverable**: per-agency suitability signal store + counter-signal surfacing at intake + renderer feed.

**Detailed Research**: [exploration/SUITABILITY_SIGNAL_MINING_EXPLORATION_2026-05-18.md](exploration/SUITABILITY_SIGNAL_MINING_EXPLORATION_2026-05-18.md)

**Related Topics**: KDD (#6b, sibling), AI override controls launch blocker, Real-World Validation (#7).

---

### 6d. Process Mining on Workflow Timelines 🟡 [EXPLORATION OPEN]
**Status**: Exploration drafted 2026-05-18. Recommended to ship **in parallel** with KDD v0 (lowest N requirement, smallest blast radius, fastest operational ROI).

**Overview**: Apply process-mining techniques (timing, bottleneck, stuck-trip detection) to trip event timelines. Use DuckDB + SQL for v0 (no new dependency); promote to pm4py only if model-inference questions become real consumers.

**Key Questions**: see exploration doc.

**Deliverable**: read-only ops surface with per-stage timing, gate-firing rate, and stuck-trip alerts per agency.

**Detailed Research**: [exploration/PROCESS_MINING_WORKFLOW_TIMELINES_EXPLORATION_2026-05-18.md](exploration/PROCESS_MINING_WORKFLOW_TIMELINES_EXPLORATION_2026-05-18.md)

**Related Topics**: Priority Scoring (#20, complementary signal source), Evaluation Framework (#6), KDD (#6b).

---

### 6f. Open Exploration Ideation (rolling) [ITERATION 1: 2026-05-18]
**Status**: Rolling ideation rounds spanning categories the map under-covers — trust/governance, customer-facing surfaces, domain depth (supplier intelligence, operational risk), owner-persona surfaces, agency people/process, compliance, multi-modality, business-model shape. Iteration 1 surfaces 19 candidates ranked HIGH/MED/LOW with paired-workstream recommendations.

**Iteration 1 HIGH picks**: AI Agent Autonomy Levels Framework (A1), Customer-Facing Surfaces (B1), Supplier-Side Intelligence (C1), Voice/WhatsApp Multi-Modal Intake (B2).

**Recommended paired workstreams**: A1+A2 (governance), C2+C3+E4 (owner persona), C1+E2+C4 (institutional memory).

**Detailed Ideation**: [exploration/OPEN_EXPLORATION_IDEATION_2026-05-18.md](exploration/OPEN_EXPLORATION_IDEATION_2026-05-18.md)

**Iteration 2 (2026-05-18) — Messaging by ICP/Persona**: opinionated 8-ICP × 12-angle matrix mapping which messaging frame (derisking / automation / CRM / AI-leverage / margin / quality / speed-to-quote / knowledge-retention / compliance / white-glove / anti-OTA / visibility) leads, supports, or backfires for each ICP. Per-ICP one-line headlines and value props. Owner-vs-user persona split rules. Hardened stance (rev 2026-05-18): AI is the engine, not the marquee — never in headlines for ICPs 4/5/7; only limited "AI-augmented" use for ICPs 3/6. → [exploration/MESSAGING_BY_ICP_PERSONA_2026-05-18.md](exploration/MESSAGING_BY_ICP_PERSONA_2026-05-18.md)

**Iteration 3 (2026-05-18) — ML Strategy (distinct from LLM Strategy #4 and KDD #6b)**: layered approach (rules → classical ML → embeddings → LLMs → fine-tuning). Identifies underused classical-ML opportunities (message/document classification, will-book prediction, supplier reliability scoring, routing, churn, anomaly). Cost/latency analysis showing 6-orders-of-magnitude gap between rules and frontier LLMs. ML infrastructure staging (don't build platform before 5+ models). Anti-patterns and explicit "do not" list. → [exploration/ML_STRATEGY_2026-05-18.md](exploration/ML_STRATEGY_2026-05-18.md)

---

### 6e. Off-Map Exploration Candidates [PROPOSAL]
**Status**: Proposal doc drafted 2026-05-18. Ranks ten topics not currently on the map with honest rationale and promotion recommendations. Awaiting your call on which to promote.

**Recommended promotions** (HIGH): Explainability Layer for AI Decisions, Embeddings "Similar Past Trip" Retrieval, Concept Drift Detection.

**Recommended gated additions** (MEDIUM): Active Learning sampling, Adversarial Intake Red-Teaming.

**Recommended documented defers** (LOW): Knowledge Graph, Bandit Variant Selection, Causal Inference, Federated Learning, Time-Series Forecasting.

**Detailed Proposal**: [exploration/OFF_MAP_CANDIDATES_2026-05-18.md](exploration/OFF_MAP_CANDIDATES_2026-05-18.md)

---

## PRODUCT & USER EXPERIENCE

### 7. Real-World Validation 🟡
**Status**: Medium Priority - Critical before launch

**Overview**: We have 30 scenarios, but are they the *right* scenarios? Do real agents recognize these?

**Key Questions**:
- How do we find beta travel agencies?
- What should we validate? (scenarios, pricing, features)
- How do we measure success in pilot?
- What feedback signals matter?

**Research Areas**:
- Beta user recruitment strategy
- Interview protocols for travel agents
- Pilot program design (which features first)
- Success metrics definition
- Feedback collection mechanisms
- Iteration cadence

**Deliverable**: Validation playbook, interview templates, pilot design

**Detailed Research**: [research/REAL_WORLD_VALIDATION.md](research/REAL_WORLD_VALIDATION.md) *(create when started)*

**Related Topics**: All persona scenarios (validation), Pricing (willingness to pay)

---

### 8. Competitive Landscape 🟢
**Status**: Low Priority - Context setting

**Overview**: What tools do travel agencies use now? Who are we competing with?

**Key Questions**:
- What do agencies use today? (Excel, WhatsApp, TourRadar, Rezdy)
- What are the strengths/weaknesses of competitors?
- What's our differentiation?
- What's our moat?

**Research Areas**:
- Competitor analysis (TourRadar, Rezdy, TravelPerk, etc.)
- Feature comparison matrix
- Pricing comparison
- Market gap analysis
- Differentiation strategy

**Deliverable**: Competitive landscape analysis

**Detailed Research**: [research/COMPETITIVE_LANDSCAPE.md](research/COMPETITIVE_LANDSCAPE.md) *(create when started)*

**Related Topics**: Pricing (positioning), Go-to-Market (positioning)

---

### 9. Future Roadmap 🟢
**Status**: Low Priority - Strategic planning

**Overview**: Where does this go after MVP? What's the 2-year vision?

**Key Questions**:
- What features after core pipeline?
- What about voice integration?
- Multi-language support?
- Supplier integrations?
- Marketplace model?

**Research Areas**:
- Feature prioritization framework
- Voice integration (Vapi, Bland)
- Multi-language support (i18n)
- Supplier marketplace
- Mobile app strategy
- API for third-party developers

**Deliverable**: Product roadmap (1-year, 2-year)

**Detailed Research**: [research/FUTURE_ROADMAP.md](research/FUTURE_ROADMAP.md) *(create when started)*

**Related Topics**: All (priority setting)

---

## BUSINESS & GROWTH

### 10. Pricing & Monetization 🟡
**Status**: Medium Priority - Revenue model

**Overview**: What do agencies pay? How do we price this?

**Key Questions**:
- Per-trip? Per-agent? SaaS subscription?
- What's the willingness to pay?
- Free tier or trial?
- Enterprise pricing?

**Research Areas**:
- Pricing model comparison (SaaS vs usage-based)
- Willingness-to-pay research
- Value-based pricing
- Competitive pricing
- Enterprise vs SMB pricing
- Trial/freemium strategy

**Deliverable**: Pricing strategy with models, price points, rationale

**Detailed Research**: [research/PRICING_AND_MONETIZATION.md](research/PRICING_AND_MONETIZATION.md) *(create when started)*

**Related Topics**: Real-World Validation (price testing), LLM Strategy (cost basis)

---

### 11. Go-to-Market Strategy 🟢
**Status**: Low Priority - Launch planning

**Overview**: How do we get first 100 customers? First 1000?

**Key Questions**:
- Who do we target first? (solo agents vs agencies)
- Direct sales or partnerships?
- Marketing channels?
- Sales motion?

**Research Areas**:
- Ideal customer profile refinement
- Channel strategy (direct, partner, marketplace)
- Marketing tactics (content, ads, events)
- Sales process design
- Partnership opportunities
- Launch sequencing

**Deliverable**: GTM plan with targets, channels, timeline

**Detailed Research**: [research/GO_TO_MARKET_STRATEGY.md](research/GO_TO_MARKET_STRATEGY.md) *(create when started)*

**Related Topics**: Real-World Validation (beta), Pricing (positioning)

---

### 12. Partnership Opportunities 🟢
**Status**: Low Priority - Growth lever

**Overview**: Who can accelerate this? Travel consortiums? OTA partnerships?

**Key Questions**:
- Which travel consortiums exist?
- Can we partner with MakeMyTrip/OTAs?
- Hotel chain partnerships?
- Technology partnerships?

**Research Areas**:
- Travel consortium landscape (TAAI, etc.)
- OTA partnership programs
- Hotel chain API programs
- Technology partnership opportunities
- Integration marketplace potential

**Deliverable**: Partnership map with priorities and approach

**Detailed Research**: [research/PARTNERSHIP_OPPORTUNITIES.md](research/PARTNERSHIP_OPPORTUNITIES.md) *(create when started)*

**Related Topics**: Integration Architecture (APIs), Go-to-Market (channels)

---

## PIPELINE EVOLUTION

### 13. Notebook 04: Response Generation
**Status**: Not Started - Next in sequence

**Overview**: After DecisionState (N02), we need to actually generate responses. What does the agent say? How?

**Key Questions**:
- How do we generate natural WhatsApp responses?
- How do we maintain tone/personality?
- How do we handle multi-turn conversations?
- What about follow-up scheduling?

**Research Areas**:
- Response generation patterns
- Tone/personality consistency
- Multi-turn state management
- Follow-up automation
- Template vs dynamic generation
- Human-in-the-loop approval

**Deliverable**: Notebook 04 contract (inputs, outputs, test scenarios)

**Detailed Research**: [research/NOTEBOOK_04_RESPONSE_GENERATION.md](research/NOTEBOOK_04_RESPONSE_GENERATION.md) *(create when started)*

**Related Topics**: Prompt Engineering (generation), Evaluation Framework (quality)

---

### 14. Notebook 05: Multi-Turn Conversations
**Status**: Not Started - Future evolution

**Overview**: Current pipeline is turn-by-turn. How do we handle ongoing conversations?

**Key Questions**:
- How do we maintain context across days?
- How do we handle interruptions?
- How do we resume conversations?
- What about scheduled follow-ups?

**Research Areas**:
- Conversation state management
- Context window optimization
- Interruption handling
- Scheduled reminder system
- Conversation threading
- Cross-channel continuity (WhatsApp ↔ Email)

**Deliverable**: Multi-turn architecture design

**Detailed Research**: [research/NOTEBOOK_05_MULTI_TURN.md](research/NOTEBOOK_05_MULTI_TURN.md) *(create when started)*

**Related Topics**: Data Strategy (persistence), Notebook 04 (generation)

---

### 15. Advanced: Learning & Optimization
**Status**: Not Started - Future evolution

---

## PROBLEM DOMAIN DEEP DIVES

### 16. Agency Internal Data Assets ✅
**Status**: Completed - Research docs written

**Research Docs**:
- [research/AGENCY_INTERNAL_DATA.md](research/AGENCY_INTERNAL_DATA.md) — Catalog of internal data types
- [research/INTERNAL_DATA_INTEGRATION.md](research/INTERNAL_DATA_INTEGRATION.md) — Integration architecture with NB02/NB03

**Key Deliverables**:
- 7 categories of internal data (preferred suppliers, tribal knowledge, historical patterns, margins, customer memory, packages, reliability)
- 6 integration points identified
- 2 new decision states: BRANCH_DESTINATION, ADVISORY_BRANCH
- Full architecture diagram

---

### 17. Notebook 04: Response Generation 🔵
**Status**: Specification complete - Ready for implementation

**Overview**: Complete contract for the "Last Mile" compiler stage that transforms SessionOutput into traveler-ready proposals and internal quote sheets.

**Key Components**:
- `TravelerProposal` — Customer-facing document with itinerary, pricing, rationale
- `InternalQuoteSheet` — Agent-facing operational document with vendors, margins, risks
- 3 generation modes: Template-based, Constraint-assembly, Research-intensive
- Component selection logic (hotels, activities) with multi-factor scoring
- Personalization engine ("why this fits" rationale)
- Quality gates and error handling

**Deliverable**: [research/NOTEBOOK_04_CONTRACT.md](research/NOTEBOOK_04_CONTRACT.md)

---

### 18. Evaluation Framework 🔵
**Status**: Specification complete - Ready for implementation

**Overview**: 4-layer evaluation pyramid for testing beyond unit tests:
1. Structural Validation (schema, completeness, constraints)
2. LLM-as-Judge (automated quality scoring)
3. Human Evaluation (expert review, blind comparison)
4. Business Outcomes (conversion, satisfaction, margin)

**Key Components**:
- LLM evaluation prompts with calibration
- Human evaluation rubric
- Safety evaluation (red team testing)
- A/B testing framework
- Continuous evaluation pipeline
- Success criteria and dashboard

**Deliverable**: [research/EVALUATION_FRAMEWORK.md](research/EVALUATION_FRAMEWORK.md)

---

### 19. Real-World Validation Strategy 🔵
**Status**: Specification complete - Roadmap defined

**Overview**: 4-phase roadmap from lab to production:
1. **Lab Validated** (current) — Unit tests, fixtures, golden path
2. **Shadow Mode** (2 weeks) — Parallel running, no customer exposure
3. **Pilot Agency** (1 month) — Real quotes, 1-2 agencies, agent review required
4. **Scale** (3+ months) — Multi-agency rollout, production workload

**Key Components**:
- Shadow mode collector for parallel comparison
- Pilot partner selection criteria
- Scope limits and safety gates
- Feature flags for gradual rollout
- Pricing model options (per quote vs subscription)
- Success metrics (business, product, technical)
- Risk mitigation strategies

**Deliverable**: [research/REAL_WORLD_VALIDATION.md](research/REAL_WORLD_VALIDATION.md)

---

**Overview**: Agencies have rich internal data (preferred suppliers, tribal knowledge, historical patterns) that can dramatically improve recommendations and preserve margins. How do we capture and use this?

**Key Questions**:
- What internal data do agencies already have?
- How can preferred supplier lists reduce search space?
- What "tribal knowledge" exists only in agents' heads?
- How do we balance customer fit with agency margin?

**Research Areas**:
- Preferred supplier networks (hotels, airlines, guides)
- Tribal knowledge capture (reality checks, hidden issues)
- Historical booking patterns
- Margin and commercial data
- Customer preference memory
- Package templates
- Vendor reliability scores

**Deliverable**: Internal data integration strategy

**Detailed Research**: [research/AGENCY_INTERNAL_DATA.md](research/AGENCY_INTERNAL_DATA.md) *[ACTIVE]*

**Related Topics**: All persona scenarios (data utilization), DATA_STRATEGY (storage)

**Overview**: The "Autoresearch" loop from specs. How does the system improve itself?

**Key Questions**:
- How do we collect implicit feedback?
- How do we A/B test prompts?
- How do we detect regressions?
- How do we learn from corrections?

**Research Areas**:
- Feedback collection mechanisms
- Automated A/B testing
- Regression detection
- Online learning
- Human feedback integration
- Continuous deployment for prompts

**Deliverable**: Learning architecture design

**Detailed Research**: [research/LEARNING_AND_OPTIMIZATION.md](research/LEARNING_AND_OPTIMIZATION.md) *(create when started)*

**Related Topics**: Evaluation Framework (metrics), Prompt Engineering (versioning)

### 20. Multi-Dimensional Priority Scoring for Travel Operations 🔴

**Status:** Active Research — Design doc complete, implementation pending

**Overview:** Travel agency CRM tools universally lack computed priority scores. Operators visually scan lists of 20-50 trips and manually decide what to work on next. This is research into a 2D priority model (urgency × importance) that computes actionable priority from SLA states, departure dates, trip values, client tiers, and lead sources.

**Key Questions:**
- What signals constitute urgency vs importance in travel operations?
- How do enterprise design systems (IBM Carbon) visualize multi-dimensional priority?
- What patterns exist in ITIL/ITSM, Salesforce, HubSpot, Zendesk for ticket/lead scoring?
- How do the major travel agency CRMs (TravelJoy, Travefy, Tern) handle priority?
- What dashboard UX patterns (Smashing Magazine, NN/G) apply to priority visualization?

**Research Areas:**
- ITIL/ITSM urgency × impact priority matrices (5×5 grid → P1-P4)
- Salesforce lead scoring: fit signals + interest signals + recency decay
- HubSpot predictive lead scoring with negative signals
- IBM Carbon shape indicator patterns (WCAG compliant: color + shape + text)
- NN/G conditional indicator taxonomy (contextual, passive, space-aware)
- Smashing Magazine real-time dashboard UX (delta indicators, sparklines, micro-animations)
- Dashboard Design Patterns (curated vs data collection dashboards)
- Travel agency CRM gap analysis (none have computed priority — white space opportunity)

**Deliverable:** Comprehensive design document with scoring formulas, visual indicator patterns, implementation plan, and operational safety (kill switch, rollback, monitoring)

**Detailed Research:** [Docs/DESIGN_2D_PRIORITY_MODEL_2026-05-08.md](Docs/DESIGN_2D_PRIORITY_MODEL_2026-05-08.md) *[DESIGN COMPLETE]*

**Learning-Layer Extension** (additive, deferred until #20 ships + 4 weeks of behavior data): [exploration/PRIORITY_SCORING_LEARNING_LAYER_EXPLORATION_2026-05-18.md](exploration/PRIORITY_SCORING_LEARNING_LAYER_EXPLORATION_2026-05-18.md)

**Related Topics:** Real-World Validation (operator testing), Evaluation Framework (scoring accuracy), Future Roadmap (learning from operator behavior), KDD (#6b — override signals could become priority residuals), Process Mining (#6d — stuck-trip signal could be a priority input)

---

### Start Now (High Priority 🔴)

1. **Integration Architecture** - WhatsApp Business API research
2. **Data Strategy** - Database schema design

These are **blocking** for moving from notebooks to real implementation.

### Start Next (Medium Priority 🟡)

3. **LLM Strategy & Costs** - Before scaling
4. **Real-World Validation** - Beta user recruitment
5. **Pricing & Monetization** - Business model validation

### Start Later (Low Priority 🟢)

6-15. Everything else - Can be figured out as we go

---

## How to Add New Topics

```markdown
### N. Topic Name [🔴/🟡/🟢]
**Status**: Current status

**Overview**: 2-3 sentence summary

**Key Questions**:
- Question 1?
- Question 2?

**Research Areas**:
- Area 1
- Area 2

**Deliverable**: What you'll produce

**Detailed Research**: [research/TOPIC_NAME.md](research/TOPIC_NAME.md)

**Related Topics**: Links to other topics
```

---

### 21. UI/UX Affordances 🟢
**Status**: Proposed — Research not started

**Overview**: Systematic treatment of affordances as an HCI concept — how UI elements signal their possible actions (perceived, hidden, false, metaphorical affordances) and how the Travel Agency Agent UI can be audited and improved against these principles.

**Key Questions**:
- What types of affordances apply to travel agency operational software? (perceived, hidden, false, pattern, metaphorical)
- Where does the current UI have false affordances (elements that look actionable but aren't) or hidden affordances (actions that exist but can't be discovered)?
- How do we audit affordances systematically? (cognitive walkthrough, heuristic evaluation, Norman's principles)
- What are the signifier patterns for AI-generated content vs human-verified content?
- How do affordances differ for the 4 personas? (Owner, Agent, Junior, Traveler)
- What cross-platform affordance issues exist? (hover-only on desktop vs touch on mobile)
- How do we design affordances for AI-stateful UI? (processing, draft, needs-review, approved — each with different action possibilities)

**Research Areas**:
- Don Norman's affordance framework (The Design of Everyday Things)
- Hartson's taxonomy: cognitive, physical, sensory, functional affordances
- Nielsen's 10 usability heuristics (especially visibility of system status, match with real world)
- Signifier patterns for AI state visibility
- False affordance detection methodology
- Hidden affordance discovery (hover-only controls, right-click menus)
- Cross-device affordance mapping (desktop hover → touch tap)
- Platform convention affordances (system UI patterns users already know)
- Affordance audit methodology for CRMs/operational tools
- Travel agency CRM affordance patterns (competitor analysis)

**Deliverable**: Affordance audit framework + annotated UI findings + design guidelines per persona

**Related Topics**: UX Anti-Patterns, DATA_CAPTURE_UI_UX_AUDIT, Real-World Validation, DESIGN_2D_PRIORITY_MODEL

---

- [x] Notebook 01 implementation review
- [x] Notebook 02 implementation review
- [x] 30 persona-based scenarios documented
- [x] Pipeline mapping for all scenarios
- [x] Test identification strategy

---

## Next Actions

1. **Create research/ folder** for detailed docs
2. **Start Integration Architecture** (WhatsApp API research)
3. **Start Data Strategy** (database schema)
4. **Update this doc** as research progresses

---

*This is a living document. Update it as the project evolves.*
