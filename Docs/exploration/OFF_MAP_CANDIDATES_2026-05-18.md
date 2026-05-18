# Off-Map Exploration Candidates — 2026-05-18

**Date**: 2026-05-18
**Status**: Proposal. Picks for promotion into `EXPLORATION_TOPICS.md` await your call.
**Parent**: [../EXPLORATION_TOPICS.md](../EXPLORATION_TOPICS.md)
**Purpose**: My honest peer-level ranking of exploration topics that are *not* on the current map but probably should be.

---

## How To Read This

For each candidate I give:
- **What it is** (one paragraph)
- **Why it matters here** (concrete tie to this product, not generic)
- **What it does NOT solve** (so the topic doesn't oversell)
- **My honest rank**: HIGH / MEDIUM / LOW
- **Cheapest first move** (so the topic is actionable, not abstract)

I'm ranking based on: leverage on existing launch blockers, leverage on existing data, N-tolerance (works at small data?), implementation cost, and overlap with already-planned work. I push back on speculative additions even if they're trendy.

---

## RANKED CANDIDATES

### 1. Explainability Layer for AI Decisions — HIGH

**What**: A traceability/explainability surface that shows, for any AI decision (extract, gate, suitability, recommendation), the inputs that drove it and the rule/prompt/model path that produced it. Not a UI; a contract on every decision payload, plus a renderer.

**Why it matters here**: The AI override controls launch blocker (AGENTS.md) isn't only about *enabling* overrides — it's about *operators being willing to trust* the system enough to override it intelligently. "I don't know why the AI decided this" is the actual root blocker. Pairs directly with KDD override mining: clusters become 10x more useful when each clustered override carries the AI's stated reasoning.

**What it doesn't solve**: model quality (separate problem); doesn't replace evaluation; doesn't fix hallucination, only exposes it.

**Cheapest first move**: define a `DecisionTrace` contract — `{ decision, inputs_used, rule_path | prompt_id | model_version, confidence, rationale_text }` — and require any new agent surface to populate it. Backfill the existing surfaces opportunistically. No UI yet; just the contract and a debug endpoint.

**Rank rationale**: directly addresses a launch blocker, low blast radius, compounds with KDD and suitability mining. Nearest-term ROI of any off-map candidate.

---

### 2. Embeddings-Based "Similar Past Trip" Retrieval — HIGH

**What**: For each trip, compute an embedding from intake + extracted slots. At any point in the trip lifecycle, an operator can see the N most similar past trips (own agency, optionally cross-agency with opt-in). This is the foundational retrieval substrate that several other systems would otherwise reinvent.

**Why it matters here**: Concrete operator workflow win: "what did we do last time for a similar customer?" is a question operators ask informally today. It's also the substrate for: template seeding (suitability mining §7.4), gate-failure precedent lookup, draft itinerary recall, junior-agent coaching. Building it once unlocks many downstream features.

**What it doesn't solve**: doesn't decide *for* the operator, doesn't generate content, doesn't replace mining. It's retrieval, not generation.

**Cheapest first move**: pick an embedding model (probably `text-embedding-3-small` for cost/quality balance, or a local sentence-transformers for cost/privacy); persist embeddings in pgvector (Postgres extension we likely already have access to); ship a single endpoint `GET /api/trips/{id}/similar?k=5`. UI in the workspace comes second.

**Rank rationale**: foundational substrate, near-term operator value, well-understood technology, cheap to ship, hard to misuse.

---

### 3. Concept Drift Detection — HIGH (gated)

**What**: Monitor whether the AI's accuracy degrades over time because *the world changed*, not because *the model changed*. Track input feature distributions (covariate shift) and prediction quality (concept drift) on rolling windows; alert on threshold breaches.

**Why it matters here**: Every ML system needs this and most ship without it. For travel specifically, the world really does change — destinations open and close, suppliers fail, regulations shift, seasonal patterns evolve. Without drift detection, the eval framework only catches degradation when someone notices.

**What it doesn't solve**: doesn't fix the drift, only detects it. Doesn't help if there's no eval ground truth to compare against (so it's gated on the eval framework reaching a workable state).

**Cheapest first move**: instrument feature-distribution snapshots into the same patterns store the KDD pipeline uses; compute weekly PSI (Population Stability Index) or KL-divergence per feature; alert on threshold breach. No new model needed.

**Rank rationale**: HIGH on principle (essential safety net), but **gated on Evaluation Framework (#6)** progressing. Without ground-truth signal, drift detection has nothing to compare against.

---

### 4. Active Learning / Sampling for Operator Review — MEDIUM

**What**: Optimize the scarcest resource (operator attention) by surfacing for review the cases where review *yields the most learning*. Pairs with KDD: which override clusters should an operator label first to compound model quality fastest?

**Why it matters here**: KDD v0 produces clusters; the digest review UI asks operators to label them. The naive order (newest first, or biggest first) wastes attention on easy cases. Active learning sampling — uncertainty + diversity — concentrates operator time on the cases that move the needle.

**What it doesn't solve**: doesn't replace human judgment, doesn't help if there are no clusters to review (so it's gated on KDD v0).

**Cheapest first move**: when KDD v0 is in production, add a "review priority" score to each cluster based on (a) cluster size, (b) within-cluster heterogeneity (uncertainty proxy), (c) novelty vs already-reviewed clusters. Order the digest by this score. Pure ordering change, no new mining.

**Rank rationale**: compounds KDD value but requires KDD v0 to exist first. Defer until v0 ships.

---

### 5. Adversarial Intake Red-Teaming — MEDIUM

**What**: Systematically generate intake variations designed to break the extractor and validators. Synthetic stress-testing of the AI surface. Output: failure cases that become test fixtures + extractor improvements.

**Why it matters here**: Today, extractor quality is measured on real intake, which is biased toward common patterns. Edge cases (ambiguous destinations, mixed currencies, conflicting dates, hostile inputs) are underrepresented until a customer hits one in production. Red-teaming surfaces them proactively.

**What it doesn't solve**: doesn't help with normal-case quality (use eval framework + KDD for that); doesn't replace real-world validation.

**Cheapest first move**: an LLM-driven generator that takes a successful intake → produces N variations along axes (ambiguity, conflict, missing info, edge format) → runs them through the extractor → flags divergence from expected slots. Ship as a developer-mode CLI before any user-facing surface.

**Rank rationale**: real value, but compete with eval framework progress. Could fold into #6 rather than standing alone.

---

### 6. Knowledge Graph (Destinations × Suppliers × Traveler-Types) — MEDIUM, defer

**What**: A graph representation of the travel-domain entities and their relationships, built from internal data + external sources (Amadeus, GeoNames). Substrate for recommendations, suitability, supplier reliability, destination disambiguation.

**Why it matters here**: Multiple proposed features (suitability mining, recommendations, association rules) would each separately reinvent partial domain knowledge. A shared graph would unify them.

**What it doesn't solve**: doesn't replace any of those features, just makes them cheaper. High upfront cost; payoff requires multiple consumers.

**Cheapest first move**: do **nothing yet**. Wait until at least two of (suitability mining, recommendations, association rules) are real and would clearly benefit. Premature graph-building is a classic over-engineering trap.

**Rank rationale**: real long-term substrate, but explicit *defer*. Document it so we don't accidentally reinvent it piecemeal.

---

### 7. Multi-Armed Bandit for Prompt / Variant Selection — LOW (gated)

**What**: When the system has multiple prompt variants for the same task, use a bandit (Thompson sampling, UCB) to route requests to the variant that's empirically winning, while maintaining exploration. Standard, well-studied.

**Why it matters here**: Eventually we will have prompt variants (post-fine-tuning, A/B prompts, agent-mode variants). Without bandit routing, prompt selection is either static (waste) or eyeballed (noise).

**What it doesn't solve**: doesn't generate variants, doesn't evaluate them in absolute terms, doesn't replace eval framework.

**Cheapest first move**: nothing until prompt versioning + multi-variant capability is real. This is downstream of prompt engineering and eval framework maturity.

**Rank rationale**: standard tool, valuable when its prerequisites exist, premature now. Add to the map so it's remembered.

---

### 8. Causal Inference / Counterfactual Analysis — LOW

**What**: Move beyond correlation: "did the operator action *cause* the booking, or did the booking happen anyway?" Methods: propensity scoring, instrumental variables, uplift modeling.

**Why it matters here**: Eventually high value (what interventions actually drive conversion?), but requires reliable outcome data, careful experimental design, and enough N to overcome confounding. None of those exist at scale yet.

**Cheapest first move**: nothing now. Note that *any* future intervention experimentation (A/B, multivariate) should be designed with causal analysis in mind, so logging supports it later.

**Rank rationale**: real discipline, real eventual value, premature now. Worth mapping so the eventual A/B framework doesn't preclude it.

---

### 9. Federated / Privacy-Preserving Cross-Agency Learning — LOW

**What**: Train models that benefit from cross-agency data without raw data ever crossing agency boundaries. Differential privacy, federated learning, secure aggregation.

**Why it matters here**: Cross-agency mining is the obvious next step after per-agency mining matures, but multi-tenant SaaS makes raw-data sharing a non-starter. If we ever want cross-agency signal, the privacy architecture must be designed up front.

**Cheapest first move**: nothing now. When KDD reaches v1 (multi-agency), revisit. Add to map as a documented "if we get there, this is how."

**Rank rationale**: speculatively important, currently premature.

---

### 10. Time-Series Forecasting (Booking Volume, Seasonality) — LOW (gated on data)

**What**: Per-agency forecasting of booking volume, destination demand, seasonality breaks. Operational planning value.

**Why it matters here**: Useful to agencies for staffing, supplier negotiation, marketing timing. Requires real volume per agency to be honest.

**Cheapest first move**: nothing now. Add when at least one agency has ≥18 months of trip history.

**Rank rationale**: real ops value at scale; defer until the data exists.

---

## SUMMARY RANKING

| Rank | Topic | Status | Gated on |
|---|---|---|---|
| HIGH | Explainability Layer | promote now | nothing |
| HIGH | Embeddings "similar trip" | promote now | nothing |
| HIGH | Concept Drift Detection | promote, gate | Eval Framework #6 |
| MEDIUM | Active Learning | promote, gate | KDD v0 shipped |
| MEDIUM | Adversarial Red-Teaming | promote or fold into #6 | nothing |
| MEDIUM | Knowledge Graph | document, explicit defer | 2+ consumers exist |
| LOW | Bandit Selection | map only | prompt versioning |
| LOW | Causal Inference | map only | experimentation infra |
| LOW | Federated Learning | map only | cross-agency mining |
| LOW | Time-Series Forecasting | map only | data volume |

## RECOMMENDED MAP ACTIONS

1. **Promote to full topics**: Explainability Layer, Embeddings Similar-Trip, Concept Drift Detection.
2. **Add as gated topics**: Active Learning, Adversarial Red-Teaming.
3. **Add as "deferred / documented" topics**: Knowledge Graph, Bandit Selection, Causal Inference, Federated Learning, Time-Series Forecasting.
4. **Decide on Association Rule Mining**: currently lives in KDD parent §4.2. My recommendation — leave it nested under KDD until KDD v0 ships, then promote if it stands on its own. No urgent reason to split.

## REJECTED (Considered, Not Recommended)

- **Reinforcement learning for agent policy** — premature by years; requires a stable simulator and reward signal we don't have.
- **Generic "AI agent observability platform"** — buzzword, would duplicate eval framework + KDD + drift detection without adding clarity. Reject.
- **Vector database as a separate service** — pgvector inside Postgres covers v0 needs cheaper.
- **LLM cost mining as a separate topic** — fold into existing LLM Strategy (#4); doesn't deserve a new line.

---

*Proposal document. Your call on promotions.*
