# Exploration Topics - Master Index

**Purpose**: Living document tracking research areas for the Travel Agency AI Copilot  
**Status**: Active - Continuously updated as project evolves  
**Last Updated**: 2026-05-19

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

**Current Sequencing Note (2026-05-19)**: Provider-specific work should not start with WhatsApp/SMS/Telegram/Gmail implementation or continuity automation. First audit and design the integration enablement foundation: supported provider catalog, per-agency integration state, credential references, capability model, health/status, audit trail, and runtime adapter boundaries.

**Key Questions**:
- Is there an integration enablement layer today, or only provider-specific aspirations?
- Which agency has enabled which integration, who configured it, and what state is it in?
- Where do credentials/tokens live, and are they encrypted/referenced rather than exposed?
- How are integration health, auth expiry, degraded status, and disabled behavior surfaced?
- How does the system send/receive WhatsApp messages?
- Which hotel/flight booking APIs are accessible?
- What CRMs do travel agencies actually use?
- How are payments processed?
- Where are documents stored?

**Research Areas**:
- Integration registry and per-agency integration instances
- Credential references and secret rotation policy
- Capability model: inbound messages, outbound messages, calendar read/write, file backup, alerts
- Health checks, safe error codes, and integration status UI/API
- Audit trail for enable/disable/test/rotate operations
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

**Current live evidence (2026-06-21)**: The authenticated workbench and overview are now live-tested with `newuser@test.com` / `testpass123`. The owner/operator path reaches the overview, captures new inquiries, and surfaces both blocked and planning-ready processing states with clearer trip-detail guidance than before. Two concrete live runs now anchor the readout: a thin Mumbai-to-Bali request blocked on missing origin, budget, and trip purpose; after a backend restart, an explicit `Origin city: Nairobi` / `Budget: USD 4,500` request promoted to `Ready to build options` instead of stalling. The ready path now shows optional refinements as `Recommended details` with `Add recommended details or continue to options.` rather than blocker copy. A follow-up live rerun of the Zanzibar scenario confirmed the backend trip record now stores `destination: Zanzibar` instead of leaking the origin city into destination candidates, and the authenticated trip page now opens as `Zanzibar family trip`. The lead inbox default operations profile now avoids repeating the same age signal twice on each card, rows with missing destinations now headline as `Trip details incomplete`, the inbox header count label no longer has duplicated wrapper markup, the team-lead inbox profile now shows ownership, SLA, and priority without repeating the same recency signal in the metrics row, finance/fulfillment now humanize stage as `Options` instead of leaking raw lowercase enum text, grouped quote examples now avoid repeating the same title twice, the quote review queue now falls back to `Trip details incomplete` for unknown destinations instead of showing `Unknown leisure`, and the trips planning stage trail now renders as a clean plain-language progress line instead of a punctuation mashup. That makes dense queues easier to scan at a glance. The overview planning cards now also collapse exact duplicates into a single grouped card with a visible matching-trip badge and grouped-count summary line, grouped quote clusters show explicit counts, the `/trips` card view now uses the same grouped-card logic with a grouped-count summary, incomplete trips now headline as `Trip details incomplete` instead of a raw trip type while still showing the actual missing-field set, the status badge copy across overview/trips/intake/shell now consistently reads `Missing customer details`, the amber planning label now reads `Ready to build options`, and the trips/pipeline routes now share a single workspace-status constant in `lib/trip-domain.ts`. A valid deep link to `/trips/tc_roundtrip_b3bbea85678b/intake` also loaded the real Bali workspace, while a stale deep link correctly fell back to a recovery screen. The latest Bali simulation also proved two contract fixes in the intake pipeline: month-day date ranges like `July 10 to July 16` now parse correctly, and the derived `visa_concerns_present` signal now carries heuristic maturity instead of hard-failing discovery validation. The fresh authenticated Lagos/Zanzibar check proved the completed trip handoff works cleanly at `/trips/trip_577f7bc1714b/intake`, and the remaining validation work is no longer about whether the shell loads; it’s about whether each blocked state explains itself fast enough for a small agency owner and a high-volume team.

**Current live evidence (2026-06-22 addendum)**: A fresh authenticated Chrome session confirmed the Lagos/Zanzibar scenario end to end. The workbench recorded `Family of 6 from Lagos for 8N Zanzibar in August, beachfront resort, NGN 2.5m budget, halal meals, kids activities, anniversary + family celebration.`, extracted `destination: Zanzibar`, `origin: Lagos`, `budget_currency: NGN`, and `budget_min/max: 2500000`, then opened the trip workspace cleanly at `/trips/trip_577f7bc1714b/intake`. That trip workspace shows `Ready to build options`, `Zanzibar leisure trip`, `6 pax`, `in Aug`, and a compact `₦2,500,000` budget, which proves the market-currency fix survived all the way into the operator surface.
The same fresh session also confirmed the high-volume inbox now renders SLA overages as human `X SLA` labels instead of raw four-digit percentages, so crowded queues stay scannable without losing urgency.

The same fresh session also confirmed the trip workspace follow-through works cleanly: `Open options` on a completed trip routes to `/trips/trip_577f7bc1714b/strategy`, and the strategy page renders a real options brief with session goal, suggested opening, priority sequence, and assumptions instead of a placeholder.

**Current live evidence (2026-06-22 later pass)**: A fresh owner-led workbench simulation for `Couple from Mumbai for 6N Bali in July, beach villa preference, INR 3-4L budget, vegetarian meals, anniversary trip` persisted the draft cleanly, but the primary `Process Inquiry` action did not surface a visible in-flight state or a matching `draft_process_started` event during the browser test window. The same long session eventually fell back to the sign-in modal, which means auth/session stability should be part of the validation checklist whenever we test longer end-to-end agency flows.

**Current live evidence (2026-06-22 clean browser recheck)**: A fresh `:3102` frontend session authenticated with `newuser@test.com` / `testpass123`, then processed `Family of 6 from Lagos for 8N Zanzibar in August, beachfront resort, NGN 2.5m budget, halal meals, kids activities, anniversary + family celebration.` into `draft_6bb50ae710ab` and landed on `Frontier OS` with `Processed successfully`. This confirms the intake-to-frontier handoff in a clean browser/server combination and shows the app can carry the global-market request through to the post-run operator surface.

**Current live evidence (2026-06-22 quote review follow-up)**: A fresh `:3102` browser session also found that the `Quote Review` page could show `Pending Quotes 22` while rendering no detailed review cards. That mismatch is now explained in the UI so larger-team operators can tell summary backlog from detailed approvals without reading a contradiction.

**Current live evidence (2026-06-22 seasonal-campaign pass)**: A fresh authenticated `:3102` browser session created a `Monsoon Push` campaign, then successfully ran `Simulate`, `Preflight`, and `Dry run` dispatch. This confirms the seasonal planning module is live and not a stub: it produces projected leads/bookings/margin, a named preflight check set, and a dispatch summary for owner-led planning.

**Current live evidence (2026-06-23 seasonal-scenario pass)**: A fresh browser replay on `/seasons` created `Monsoon Kerala Small Agency` and `Global Holiday Portfolio`, then reran simulation in baseline/aggressive/conservative modes. After the backend fix, the planner now produces materially different outputs per scenario: the small-agency plan moved from `Leads: 100 / Margin: 15.5% / Confidence: 0.72` in baseline to `Leads: 118 / Margin: 13.7% / Confidence: 0.66` in aggressive and `Leads: 84 / Margin: 16.7% / Confidence: 0.79` in conservative. That closes the gap where the scenario selector only changed a label instead of a planning outcome.

**Current live evidence (2026-06-23 seasonal dispatch follow-through)**: A fresh browser replay on the same `Monsoon Kerala Small Agency` card selected `conservative`, ran `Dry run`, and the result card now preserved `Scenario: conservative` alongside `Status: Ready`, `Dry run: Yes`, and the dispatch timestamp. That confirms the planner keeps its assumption visible all the way from what-if simulation into the action step instead of dropping context at the last moment.

**Current live evidence (2026-06-23 quote-ready escalation mismatch)**: A fresh browser replay on `/trips/trip_631a3149d1a8/strategy` initially rendered `Escalate to senior review due to critical contradictions.` for a trip whose intake surface already said `Ready to build options` and whose trip payload showed `highest_ready_tier: quote_ready`. The strategy preview now falls back to a derived options brief in that case, so the operator sees `Prepare a clear options plan for Zanzibar while keeping kid-friendly, beach access, relaxed pace and $5,000 - $6,000 aligned.` instead of an over-conservative escalation script. That closes a trust gap between intake readiness and the options page opening line.

**Current live evidence (2026-06-23 safety bundle fallback)**: The workbench safety tab now keeps a useful customer-message QA preview visible even when the persisted safety bundle is absent. Before the fallback, the tab only said the safety bundle was unavailable; after the change, the operator still sees the decision state plus the traveler message preview, which makes the review step feel like a continuation of the workflow instead of a dead end.

**Current live evidence (2026-06-23 browser-backed handoff)**: A live Chrome replay on `:3101` processed `Family of 3 from Nairobi planning 4N Zanzibar in January. 2 adults and 1 child, beachfront hotel, airport transfers, budget USD 4500-5500.` and opened the resulting trip workspace at `/trips/trip_107b6580a60a/intake`. The trip view showed `Zanzibar family leisure trip`, `Ready to build options`, `Origin Nairobi`, `Destination Zanzibar`, `Type leisure`, `Purpose family leisure`, `Party Size 3 pax`, `Dates in Jan`, `Budget $4,500 - $5,500`, and `Must-haves beach access, kid-friendly`. That confirms the purpose cue now survives into the trip workspace and the remaining opportunity is richer narrative context, not a missing core field.

**Current live evidence (2026-06-23 inbox contract recheck)**: A fresh browser replay on `:3103` logged in successfully, opened overview/workbench/inbox, and searched the inbox for `9E7D`. The live queue returned `trip_9e7d8d596519` with `tripPurpose: family leisure`, `destination: Zanzibar`, and the visible card title `Zanzibar family leisure trip`. That proves the purpose field now survives into the inbox contract and that the main app keeps the same trip cue visible across intake, queue, and planning surfaces.

**Current live evidence (2026-06-23 process-path recheck)**: The workbench primary action still submits a real run when the form is submitted directly. A live Nairobi/Zanzibar replay advanced the app to `Risk Review`, showed `Processed successfully`, and surfaced the follow-up `Please provide trip purpose to generate a quote.` This is the correct operator-facing response for a sparse request: the system does not overstate readiness and instead asks for the missing planning intent.

**Current live evidence (2026-06-23 procurement-heavy corporate quote)**: A fresh authenticated workbench replay on `:3101` processed `Large Nairobi agency managing a corporate group of 18 travelers from Nairobi to Singapore in October 2026. Budget is USD 42,000. Need 6 nights, mid-to-upscale hotel blocks, airport transfers, two separate rooming lists, and a fast quote that can be shared with procurement.` The run produced `POST /api/drafts` and `POST /api/spine/run`, advanced into `Processing`, and surfaced `PROCEED_INTERNAL_DRAFT` with a `soft_preferences` blocker plus a concrete follow-up question. That proves the main app handles procurement-heavy group quotes as a real operator flow rather than a stub.

**Current live evidence (2026-06-23 itinerary mismatch replay)**: A fresh authenticated workbench replay on `:3101` processed `Family of 3 from Bangalore to Bali. Travel dates: July 10-16, 2026. Flight lands at 22:30 on 10 July, but the hotel check-in is afternoon on 10 July.` The run advanced to `Risk Review` with `WAITING ON CUSTOMER` and a concrete follow-up: `Your flight arrives after hotel check-in. Should we move hotel check-in or choose an earlier flight?` The saved trip packet kept the structured `flight_hotel_mismatch` contradiction, which confirms the operator-facing safety question now survives the real browser path for the phrasing people actually use.
The trip intake page for the saved trip now also shows a red `Critical Issue` card with `Flight / Hotel Mismatch` and the same move-hotel-or-choose-earlier-flight guidance, so the signal is visible both in the safety run and in the trip workspace.

**Current live evidence (2026-06-23 corporate procurement replay)**: A fresh authenticated workbench replay on `:3101` processed `Large Nairobi agency managing a corporate group of 18 travelers from Nairobi to Singapore in October 2026. Budget is USD 42,000. Need 6 nights, mid-to-upscale hotel blocks, airport transfers, and two separate rooming lists for procurement.` The resulting trip workspace now preserves the group shape with `Group logistics`, `2 rooming lists`, and `shareable with procurement`. That confirms the app no longer flattens procurement-heavy quotes into a generic business trip, and the rooming-list detail survives from the live intake all the way into the saved trip page.

**Current live evidence (2026-06-23 quote-review backlog visibility)**: A fresh browser replay on `:3103/reviews` showed `Pending Quotes 47` while only 25 quote cards were loaded in the view. The page now states that explicitly with `Showing 25 loaded quotes while the summary reports 47 pending quotes. Refresh if you expect the queue to have grown since the last load.` That closes a trust gap where the queue could look complete even though only a loaded subset was visible.

**Current live evidence (2026-06-23 Africa/Europe country replay)**: A fresh `:3101` browser replay processed `Small Accra agency handling a family holiday for 2 adults and 1 child from Accra to Ghana in April 2027. Budget USD 6,500. 5 nights. Beach resort, airport transfers, vegetarian meals.` The saved trip page now opens as `Ghana family leisure trip` with `Origin: Accra` and `Destination: Ghana`. A companion geography regression also keeps `Zagreb -> Croatia` working. This matters because the app now handles a small African agency request the same way it handles the better-covered Bali/Zanzibar-style requests: the trip becomes planning-ready instead of stopping on a missing-country fallback.

**Current live evidence (2026-06-23 corporate procurement replay)**: A fresh `:3101` browser replay processed `Large Mumbai agency managing a corporate group of 18 travelers from Mumbai to Singapore in October 2026. Budget USD 42,000. Need 6 nights, mid-to-upscale hotel blocks, airport transfers, two separate rooming lists, and a fast quote that can be shared with procurement.` The saved trip page opened as `Singapore business trip` with `Origin: Mumbai`, `Destination: Singapore`, `Trip Purpose: business`, and `Group logistics: 2 rooming lists · Shareable with procurement`. This is the useful opposite of the Accra family case: a larger agency sees its procurement shape survive into the operator surface instead of getting flattened into a generic leisure trip.

**Current live evidence (2026-06-23 hyphenated traveler-count replay)**: A fresh `:3100` browser replay exposed a parser miss on `18-traveler corporate offsite` phrasing. Before the fix, the Risk Review tab asked for party size even though the number was present. After updating the party extractor to accept hyphenated traveler counts, the same request now resolves `party_size = 18`, the trip page shows `18 pax`, and the corporate trip carries `NGN 15,000,000` plus `shareable with procurement` into the durable trip view.

**Current live evidence (2026-06-23 documents picker pass)**: A fresh browser replay on `/documents` confirmed the page is a real canonical document shell, not a parallel workflow. The trip picker now stays readable for incomplete trips by falling back to a trip reference instead of `Unknown (...)`, which matters when an operator has to scan a large queue quickly.

**Current live evidence (2026-06-23 suppliers route pass)**: A fresh browser replay on `/suppliers` found that the nav item had been a 404. The route now opens as a real shell with a trip selector, supplier-risk context, and a link back to the trip workspace, so the app no longer advertises a dead destination to an operator exploring the main app.

**Current live evidence (2026-06-23 corporate type-label fix)**: The same Mumbai/Singapore replay initially surfaced a stale `Type: leisure` label on the trip intake shell even though the request was clearly corporate. The canonical trip-field resolver was updated so `tripType` now follows the stored business purpose, and a fresh browser reload now shows `Type: business` alongside `Purpose: business`. This matters because the operator-facing label should not contradict the real request shape when a larger agency is trying to move fast.

**Current live evidence (2026-06-23 strategy-handoff fix)**: The same Mumbai/Singapore replay also showed that the strategy/options page had been serving the old generic internal-draft boilerplate. The backend strategy builder and the strategy tab now prefer business-aware phrasing when the trip context is clearly corporate, and the live page now opens with `Prepare a clear options plan for Singapore for the business trip while keeping budget usd 42,000 aligned.` plus `Here’s the options plan for Singapore with the business requirements in view.` The follow-up wording now says `priorities or must-haves` instead of leaking the raw field label, which keeps the first read on the options page more truthful and more useful for the operator.

**Current live evidence (2026-06-23 budget-format cleanup)**: The same strategy replay now also formats the budget cleanly as `$42,000` rather than a raw lowercase string, which makes the options page read like a real planning artifact rather than a stitched-together debug view.

**Current live evidence (2026-06-23 ops fallback improvement)**: A browser replay on `/trips/tc_roundtrip_a069120cb3c6/ops` still shows the ops gate for a discovery-stage trip, but the fallback link now says `Return to Options` rather than `Return to Intake` when the trip already has enough planning context. This keeps the operator in the planning flow instead of sending them backwards to start over.

**Current live evidence (2026-06-23 processed-draft rehydration)**: A fresh browser replay on the same Lagos/Zanzibar draft showed that the workbench now restores the completed trip handoff after reload by reading the persisted `run_snapshots[].snapshot.trip_id` from the draft payload. Reopening `draft_4f291c1da41b` now shows `Promote Draft`, and promoting it lands on `/trips/trip_c5cc2e04e021/intake` with `Zanzibar family leisure trip`, `Ready to build options`, `5 pax`, `in Dec`, and `₦2,500,000`. That closes a trust gap where a successful run could previously vanish on refresh even though the draft had already recorded the created trip id.

**Current live evidence (2026-06-23 output-preview fallback)**: A fresh authenticated browser replay on `/trips/trip_c5cc2e04e021/output` now shows a derived preview instead of a blank dead end when the persisted traveler bundle is missing. The page keeps the operator on the same trip, shows `Showing a derived preview from the current strategy and decision because the persisted output bundle has not been saved yet.`, and the customer-facing draft now reads `Here’s the options plan for Zanzibar.` instead of leaking the generic internal-draft boilerplate. That makes the output stage truthful, useful, and safe for a small-agency handoff.

**Current live evidence (2026-06-23 quote-assessment clarity pass)**: A fresh authenticated browser replay on `/trips/trip_c5cc2e04e021/decision` now shows `Waiting on Customer`, `Quote Ready`, and `2 fields needed for shortlist`, but the stage-advance button is hidden until the missing shortlist fields are complete. The page now explains that the missing fields must be completed first instead of suggesting an advance that would have been confusing or premature. That keeps the quote-review flow honest for a real operator.

**Current live evidence (2026-06-23 planning-helper wording pass)**: The planning helper that drives the intake/trip shell next-step copy now says `Prepare the traveler-ready draft before sending.` for internal-draft states, so the operator sees traveler-facing language instead of internal boilerplate when a trip is past intake but not yet ready to send.

**Current live evidence (2026-06-23 insights recovery pass)**: The `/insights` route briefly regressed to 500 because Turbopack cache state had gone bad after a stale parse error, and the browser replay confirmed the route recovered after the dev server was restarted with a clean cache. The live page now responds 200 again, the browser title is `Waypoint OS — Insights`, and the funnel copy no longer shows impossible conversion rates when adjacent stage counts are not comparable. The remaining UI note is a Recharts width warning during initial load, which is visible in the dev console but does not stop the route from rendering.

**Current live evidence (2026-06-23 shell honesty pass)**: The agency shell navigation now keeps genuinely planned sections inert instead of rendering them as fake clickable actions that only trigger a toast. That matters because the shell should not overpromise navigation affordances for routes that do not exist yet, even if the label is still useful as a roadmap signal.

**Current live evidence (2026-06-23 auth-boundary pass)**: A clean browser session on `/workbench` and `/settings` still shows the loading shell until sign-in happens, and the browser console records a 401 from `/api/auth/me`. The same backend login credentials (`newuser@test.com` / `testpass123`) do work, and once authenticated the protected settings endpoint returns the full agency payload. That means the route contracts are healthy, but live browser validation needs an authenticated session before protected surfaces can be judged fairly.
**Current live evidence (2026-06-23 auth-boundary follow-up)**: The protected workbench and settings pages now surface an explicit sign-in notice instead of leaving the browser on a frozen-looking loader when the session is missing. The authenticated path is unchanged; this only makes the unauthenticated state more truthful and easier to recover from.
**Current live evidence (2026-06-23 intake edit-controls replay)**: A fresh browser replay on the live trip intake page found that the inline budget/origin edit controls were sitting inside the parent form without explicit `type="button"` behavior, so clicks could act like accidental submits instead of opening the editor. The buttons now open the inline editor correctly, and the backend budget patch path now reuses the shared parser so compact values like `₹3.5L` stay truthful instead of collapsing into a raw decimal fragment. That makes the main agent workflow feel like a real edit-and-save loop rather than a flaky form shim.
**Current live evidence (2026-06-23 queue-density pass)**: A fresh signed-in browser session reached `/trips` and loaded the real workspace queue with `100 in planning` and `96 needs details`. The card view collapsed the queue into `12 grouped cards`, which keeps the large-list triage surface readable, but also raises a product question about how much of the queue should be summarized versus fully enumerated for larger agencies.

**Current live evidence (2026-06-23 payments-queue scale pass)**: The authenticated live backend now serves `/payments` for a large agency with `11,373` queue items in under a second, instead of stalling on a per-trip booking lookup loop. The queue also derives a readable fallback title when a trip is missing its stored name, so sparse rows no longer render as blank operator cells.

**Current implementation note (2026-06-23 clipboard hardening)**: Shared clipboard actions now only use the async clipboard API when permission is explicitly granted and otherwise fall back to the safer copy path. That should reduce browser permission noise on overview/workbench copy actions in restricted sessions without changing the operator-facing action.

**Current live evidence (2026-06-23 audit contract fix)**: The audit log page now reads the backend's `entries` payload instead of `items`, which means the owner/admin audit surface can actually display returned rows rather than a false empty state. This came directly from comparing the live frontend fetch with the `/api/audit` route contract.

**Current live evidence (2026-06-23 global quote-review currency fix)**: The quote review cards now format each row using the quote's own currency code instead of hardcoding a dollar sign. This closes a real multi-market truth gap for Indian, African, and global agencies because review values now match the currency already carried in the review payload.
**Current live evidence (2026-06-23 route-shell density pass)**: The Documents and Suppliers route shells are truthful and not dead links, but a fresh authenticated browser replay showed that their trip pickers become noisy on a large queue because many rows repeat the same short surface label. This is not a correctness break, but it is a real operator-readability issue for larger agencies and should be treated as a follow-on UX improvement rather than a placeholder success.
**Current live evidence (2026-06-23 route-shell density follow-up)**: The Documents and Suppliers pickers now use a tail-segment reference in each option label, so the large queue rows are distinguishable as `1294`, `C2DD`, `A22A`, and so on instead of collapsing into the same `TC_R`-style label. The route shells remain truthful, but now the picker is actually scannable in a large workspace.

**Current build wording**: Decision-state labels now say `Waiting on Customer` instead of `Need More Info`.

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

**Detailed Research**: [research/REAL_WORLD_VALIDATION.md](research/REAL_WORLD_VALIDATION.md) *(create when started)*; [main simulation doc](travel_agency_main_app_simulation_2026-06-21.md); [issue review](travel_agency_process_issue_review_2026-06-19.md)

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
- Live inbox verification now also covers operator-facing label cleanup, including stage humanization in finance and fulfillment views, so queue scans read like the app promise rather than backend payloads.
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

## Live Validation Note

- The June 21 live Chrome pass covered a small-agency intake scenario in addition to the Bali scenario.
- That pass exposed two real product gaps:
  - party composition was being downgraded from `3 pax` to `1 pax`
  - INR budgets like `2.5L` were being displayed as `₹3`
- Both issues are now fixed in the intake parser / shared budget formatter and are worth keeping in the exploration map because they came from a real operator workflow, not a synthetic unit test.

## Live Validation Note: Options Surface Contract

- The June 21 live Chrome pass now covers the trip strategy route as well as intake and workbench handoff.
- The options page no longer shows the dead `Options builder not connected yet` state when trip context is available.
- The trip response now exposes `strategy`, which reduces frontend guesswork and keeps the route aligned with the persisted trip state.
- This is a real operator pain point because the user sees a planning-ready trip, but the previous placeholder implied the app was still disconnected.

## Live Validation Note: Destination Disambiguation

- A Nairobi-based agency scenario showed the parser initially mistaking an agency-origin prefix for the trip destination.
- After the filter fix, the same request resolved correctly to Zanzibar instead of Nairobi.
- This keeps agency metadata separate from traveler intent and prevents wrong trip titles from leaking into the operator surface.
- The same live rerun also revealed duplicate internal-data warnings in the strategy brief, which are now deduped.

## Live Validation Note: Ready CTA Advance

- The Zanzibar trip intake page had a `Continue to options` CTA that was enabled but previously did nothing.
- The live fix now routes that control to the strategy page when the trip is ready and has no recommended details left.
- That makes the final intake action honest and prevents a silent workflow dead-end at the exact handoff point.

## Live Validation Note: Ready CTA Copy Alignment

- A ready Bali trip with INR budget, destination, and dates exposed a second mismatch: the footer CTA looked like navigation even when it was a processing action.
- The footer label now reads `Build trip options`, which makes the action honest and distinct from the top `Open options` route link.
- This is worth keeping in the exploration map because it came straight from a live operator clickthrough and clarified the difference between route navigation and background processing.

## Live Validation Note: Strategy Placeholder Cleanup

- The Bali trip strategy preview originally showed `Check TBD and Bali together` when origin was missing.
- The preview builder now uses a human fallback sentence instead of echoing placeholder text, so the generated options brief stays polished even when context is incomplete.
- This is worth keeping in the exploration map because it surfaced from a live operator page, not a synthetic fixture.

## Live Validation Note: Output Empty-State Handoff

- The Bali trip output page initially pushed the operator back to Options even though quote-assessment context was already present.
- The empty-state routing now prefers Quote Assessment when that context exists, which better matches the actual trip lifecycle.
- This is worth keeping in the exploration map because it removes a stale fallback that would have sent operators one stage too far backward.

## Live Validation Note: Timeline Stage Label Cleanup

- The trip timeline originally showed raw `Unknown` for an unset stage badge during the live Chrome simulation.
- The shared timeline helper now renders `Stage not set`, which keeps the history view human-readable and aligned with the rest of the app’s labels.
- This is worth keeping in the exploration map because it was a real operator-facing mismatch, not just a synthetic test fixture issue.

## Live Validation Note: Overview Queue Language Cleanup

- The overview command center originally showed `Travel TBD` in enquiry and quote cards when the date window was missing.
- The shared date-window formatter now normalizes that sentinel into `Travel Dates to confirm`, which makes the queue feel like an operational surface instead of a temporary scaffold.
- Quote cards with synthetic `TRIP-UNKNOWN` references now hide that fake id, so the queue no longer treats placeholder metadata like a real trip reference.
- This is worth keeping in the exploration map because it came from the busiest live surface in the app, where placeholder language has the highest trust cost.

## Live Validation Note: Auth Transport + Origin Recovery

- The fresh `:3103` browser replay confirmed two main-app issues from the same operator flow:
  - login transport was double-encoding JSON and failing the auth contract
  - natural-language origin phrasing like `from Nairobi planning...` was not being recovered into the canonical packet
- The login path now works again because the shared API client serializes JSON only once before it reaches the BFF route.
- The origin parser now recognizes the conversational phrasing from the browser replay, so the flow no longer gets stuck on `incomplete_intake` for that sentence shape.
- The remaining blocker in the tested live scenario is budget feasibility, which is the more honest next question for an owner/operator to answer.
- This belongs in the exploration map because it came from a real browser replay of the main app, not from a synthetic fixture.

## Live Validation Note: Party Size and Budget Range Preservation

- The larger-agency replay of `Family of 4 from Nairobi planning 7 nights in Bali in August. Budget USD 7000-9000...` initially exposed two trust losses:
  - party size collapsed to `1 pax`
  - budget range collapsed to a single visible number
- The extractor now respects the explicit family count over generic child keywords, so the trip shell shows `4 pax`.
- The budget contract now preserves both bounds and the shared budget display renders `$7,000 - $9,000`.
- This belongs in the exploration map because it was caught by a live operator replay on the main app, and it materially improves the honesty of the summary screen for larger-agency workflows.

## Live Validation Note: Global-Market Purpose Capture

- A Lagos/Zanzibar replay showed that the intake flow still needs a clearer purpose cue for global-market operators.
- Without an explicit trip purpose, the run correctly fell back to `WAITING ON CUSTOMER` and `incomplete_intake`.
- With `Trip purpose: family vacation` added to the agent note, the same request advanced to `PROCEED_INTERNAL_DRAFT` with `soft_preferences`.
- This belongs in the exploration map because it is a real operator friction point: the app knows how to proceed once the purpose exists, but the surface does not yet make that requirement obvious enough.

## Live Validation Note: Canonical Purpose Prompt Surfaced in Intake

- The workbench intake screen now renders the canonical `trip_purpose` prompt from `frontend/src/lib/traveler-prompts.ts`.
- That keeps the visible helper copy aligned with the extraction vocabulary and makes the missing-detail cue clear before the operator presses `Process Inquiry`.
- This belongs in the exploration map because it closes the loop between the live simulation finding and the operator-facing remedy.

## Live Validation Note: Purpose Visible in Packet Summary

- The trip-details packet summary now includes `Purpose` alongside destination, origin, dates, budget, and party size.
- That keeps the extracted trip intent visible after processing instead of burying it only in the inferred-details section.
- This belongs in the exploration map because it strengthens the operator’s post-process summary with the same global-market signal that the intake surface now asks for up front.

## Live Validation Note: Trip Details Stays Reachable After Completion

- After the terminal run settles, selecting `Trip Details` now keeps the workbench on the packet view instead of snapping the operator back to the terminal review tab.
- The live packet view shows the purpose card together with destination, dates, budget, and party size, which makes the post-run handoff much more useful for global-market operators.
- This belongs in the exploration map because it removes an interaction trap discovered by browser replay, not by static code inspection.

## Live Validation Note: Global-Market Pattern Generalizes

- A second browser replay with a Nairobi/Zanzibar family request showed the same purpose-card and trip-summary behavior.
- The packet view preserved the budget range, party count, and purpose details, which suggests the fix is not just a Lagos-specific happy path.
- This belongs in the exploration map because it gives us a second market/persona confirmation for the same user-facing pattern.

## Live Validation Note: Compact India-First Honeymoon Replay

- A shorter Mumbai/Goa honeymoon replay also preserved purpose, budget, origin, destination, and party size in the packet view.
- INR formatting stayed human-readable and the summary remained concise, which is important for owner-led agencies that do not want a verbose template.
- This belongs in the exploration map because it confirms the same behavior on a compact India-first request, not only on the longer family-market scenarios.

## Live Validation Note: Source-City Descriptors Must Not Become Destination Candidates

- A live browser replay of `Small Mumbai agency handling a family holiday for 4 adults and 2 kids from Mumbai to Bali in August 2026...` initially produced `destination_candidates = ["Mumbai", "Bali"]`.
- That caused the workbench to ask the operator to choose between Mumbai and Bali, even though Mumbai was the origin and Bali was the destination.
- The destination extractor now drops source-city descriptors like `Mumbai agency` and origin phrasing like `from Mumbai to Bali`, so the same sentence now resolves to `destination_candidates = ["Bali"]`.
- This belongs in the exploration map because it came from a real browser replay of the main app and it directly changed the quality of the intake handoff.

## Live Validation Note: Date Flexibility Should Stay Separate From Budget Flexibility

- A later Cape Town/Dubai replay still surfaced a bogus `budget_flexibility` ambiguity because the request said `They are flexible on exact dates within the month.`
- That wording is about timing, not budget stretch, so it created unnecessary commercial noise in an otherwise clean family quote.
- The budget-flex trigger is now limited to actual budget-flex phrases, and the same replay comes back with an empty ambiguity report.
- This belongs in the exploration map because it shows the parser needs typed flexibility signals, not a generic `flexible` keyword bucket.

## Live Validation Note: Fully Explicit Intake Advances to Frontier OS

- After the origin/destination fix, the same browser replay with an explicit `from Mumbai to Bali` request advanced beyond `WAITING ON CUSTOMER`.
- The workbench switched to `tab=frontier` and showed the Frontier OS panel instead of staying blocked on a false destination ambiguity.
- This matters because it proves the main app can move a complete intake forward once the parser is not tripping over source-city noise.
- The live run now shows one `View Trip` action and one `View Frontier` action in the processed state, which is a cleaner operator handoff.

## Live Validation Note: USD Budgets Are No Longer Treated As INR

- A large-agency Singapore replay with `Budget is USD 42,000` initially hit a false `budget_feasibility` block because the numeric amount was compared against an INR heuristic table.
- The extractor already had the currency fact, so the issue was not missing data but a currency-blind decision rule.
- The feasibility check now skips the INR table for non-INR budgets, and the same replay advances to `tab=frontier` instead of inventing a budget problem.
- This belongs in the exploration map because it is a high-trust global-market failure mode: currency-aware decisions matter as much as destination logic.

## Live Validation Note: Group Logistics Stay Visible for Large Agencies

- The large-agency Singapore replay now surfaces `Group Logistics` in the Trip Details tab.
- The summary reads `2 rooming lists · Shareable with procurement`, which keeps the operational logistics visible at a glance.
- The extracted information table also preserves the rooming and procurement facts for deeper review.
- This belongs in the exploration map because large agencies need rooming/procurement context as much as destination and budget.

## Live Validation Note: Generated Draft IDs Should Not Trip Phone Detection

- A dogfood-mode replay initially failed because the privacy guard mistook the generated draft id for a phone number.
- The guard now exempts obvious generated ids such as `draft_...`, so the same replay completes normally.
- This belongs in the exploration map because a false privacy block is a real operator failure, even if the underlying data was safe.

## Live Validation Note: Corporate Group Purpose Is Business, Not Cultural

- A large Nairobi-to-Singapore corporate replay originally surfaced `PURPOSE cultural` even though the lead was procurement-heavy and described a corporate group.
- The intent classifier now recognizes corporate/procurement language as business purpose.
- The live packet now shows `PURPOSE business`, which matches the operator framing better for a procurement-managed quote.
- This belongs in the exploration map because purpose labels drive tone and planning lens, especially on large agency requests.

## Live Validation Note: Generic Amenity Words Must Not Become Destinations

- A fresh Nairobi-to-Zanzibar family replay initially produced `destination_candidates = ["Zanzibar", "Beach"]`.
- That caused the workbench to ask an unnecessary `Between Zanzibar and Beach` follow-up, even though `beach resort` was only a preference.
- The destination extractor now excludes generic amenity nouns like `Beach`, `Hotel`, `Resort`, and `Villa` from destination candidates.
- The same replay now advances to `PROCEED_INTERNAL_DRAFT` and the saved trip remains a Zanzibar family leisure trip.
- This belongs in the exploration map because amenity nouns are a common global-market preference signal and should not be mistaken for trip targets.

## Live Validation Note: KES Budgets Must Not Fall Back to INR

- A fresh Nairobi family replay with `KES 480,000` initially rendered as `₹4.8L` in the saved trip summary.
- The frontend budget helper now recognizes KES source text and renders the budget as `KSh480,000`.
- The live trip page keeps the African-market currency intact, which matches the operator’s commercial context.
- This belongs in the exploration map because currency is part of the trip truth and should survive from intake through display.

## Live Validation Note: Mauritius Must Resolve as a Destination

- A fresh Cape Town replay with `from Cape Town to Mauritius` initially fell back to `destination = Unknown`.
- Mauritius is now included in the canonical destination synonym set, so the same replay resolves to a real Mauritius trip.
- The live trip page now shows `Mauritius family leisure trip` with origin `Cape Town`.
- This belongs in the exploration map because clearly stated country destinations should not require extra clarification.

## Live Validation Note: Seychelles Must Resolve as a Destination

- A fresh Nairobi replay with `from Nairobi to Seychelles` initially produced no destination candidates.
- Seychelles is now included in the canonical destination synonym set, so the same replay resolves to a real Seychelles trip.
- The live trip page now shows `Seychelles family leisure trip` with origin `Nairobi`.
- This belongs in the exploration map because Seychelles is a common market destination and should behave like one in the canonical flow.

## Live Validation Note: Namibia Must Resolve as a Destination

- A fresh Johannesburg replay with `from Johannesburg to Namibia` initially produced no destination candidates.
- Namibia is now included in the canonical destination synonym set, so the same replay resolves to a real Namibia trip.
- The live trip page now shows `Namibia family leisure trip` with origin `Johannesburg`.
- This belongs in the exploration map because Namibia is a common regional travel target and should behave like one in the canonical flow.

## Live Validation Note: Iceland Must Resolve as a Destination

- A fresh Reykjavik replay with `from Reykjavik to Iceland` initially produced no destination candidates.
- Iceland is now included in the canonical destination synonym set, so the same replay resolves to a real Iceland trip.
- The live trip page now shows `Iceland family leisure trip` with origin `Reykjavik`.
- This belongs in the exploration map because Iceland is a common travel destination and should behave like one in the canonical flow.

## Live Validation Note: Georgia Must Resolve as a Destination

- A fresh Tbilisi replay with `from Tbilisi to Georgia` initially produced no destination candidates.
- Georgia is now included in the canonical destination synonym set, so the same replay resolves to a real Georgia trip.
- The live trip page now shows `Georgia family leisure trip` with origin `Tbilisi`.
- This belongs in the exploration map because Georgia is a common travel destination and should behave like one in the canonical flow.

## Live Validation Note: Manual Planning Edits Must Survive Auto-Reassess

- A live trip intake simulation on `/trips/trip_2333bff6434d/intake` showed that budget and origin edits can be made inline from the agent page.
- The reassessment request now carries the current trip fields forward as a structured overlay, so manual edits do not get wiped by the next auto-reprocess run.
- This belongs in the exploration map because preserving agent-entered truth across auto-reassess is a core trust boundary for the planning workflow.
