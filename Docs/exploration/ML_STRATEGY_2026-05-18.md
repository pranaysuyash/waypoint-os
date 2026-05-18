# Machine Learning Strategy — Honest Take

**Date**: 2026-05-18
**Status**: Open exploration. Iteration 3 of the open-exploration series.
**Parent**: [../EXPLORATION_TOPICS.md](../EXPLORATION_TOPICS.md)
**Siblings**: [KDD parent](KDD_KNOWLEDGE_DISCOVERY_EXPLORATION_2026-05-18.md) (data mining), [OFF_MAP_CANDIDATES](OFF_MAP_CANDIDATES_2026-05-18.md) (ML-adjacent topics), [LLM Strategy & Cost (#4)](../EXPLORATION_TOPICS.md)
**Distinct from**: KDD (which is pattern discovery from data); this doc is about *building and operating models* that predict, classify, score, or rank in production.

---

## TL;DR (Read This First)

This is an **LLM-heavy product**. The temptation is to do everything with LLMs because they're available. The strategic mistake is doing *only* LLMs because they're available.

**The right answer is layered**:

```diagram
╭───────────────────────────────────────────────────╮
│ Rules                                             │ ← try first, always
│ - deterministic, explainable, free, fast          │
╰────────────────────┬──────────────────────────────╯
                     ▼
╭───────────────────────────────────────────────────╮
│ Classical ML (sklearn / xgboost / lightgbm)       │ ← when N supports it
│ - cheap, fast, mostly interpretable               │
│ - classification, ranking, scoring                │
╰────────────────────┬──────────────────────────────╯
                     ▼
╭───────────────────────────────────────────────────╮
│ Embeddings (pgvector + general embedding model)   │ ← for retrieval & clustering
│ - similar-trip, semantic search, KDD inputs       │
╰────────────────────┬──────────────────────────────╯
                     ▼
╭───────────────────────────────────────────────────╮
│ LLMs (Anthropic / OpenAI / local)                 │ ← when only language can do it
│ - intake parsing, draft generation, summarization │
│ - rationale, multi-step reasoning                 │
╰────────────────────┬──────────────────────────────╯
                     ▼
╭───────────────────────────────────────────────────╮
│ Fine-tuned / own models                           │ ← last, gated on volume + cost
│ - only when a prompt-engineered LLM hits ceiling  │
│   or cost dominates a high-volume task            │
╰───────────────────────────────────────────────────╯
```

**The honest rule**: a task should sit at the lowest layer that can do it correctly. Don't use an LLM where a regex works. Don't use classical ML where a rule works. Don't fine-tune where a prompt works.

---

## Where LLMs Already Earn Their Keep (Keep Doing This)

These tasks should stay on LLMs. Classical ML or rules would be worse:

| Task | Why LLM is right |
|---|---|
| Intake parsing (raw note → structured slots) | Natural language understanding; pre-LLM NLP was significantly worse |
| Draft proposal generation | Open-ended generation, style-aware |
| Free-text summarization (timeline, audit) | Same reason |
| Decision rationale text | Same reason |
| Multi-turn clarification dialog | Reasoning + context tracking |
| Edge-case interpretation | Where the long tail eats classical models alive |

**Caveat**: high-volume LLM tasks become candidates for fine-tuned smaller models once volume justifies the fine-tuning cost. That's a *future* optimization, not a *now* one.

---

## Where Classical ML Genuinely Fits (Underused Today)

These are tasks the product probably does either with LLMs (wasteful) or with rules (less accurate at scale). Each is a real opportunity:

### 1. Email / Message Classification (Intent + Urgency + Type)
**Use case**: every inbound message gets classified (booking inquiry, document submission, cancellation, complaint, FYI, automation reply) with urgency band.
**Why classical ML**: tiny supervised classifier (logistic regression or small gradient-boosted model), <10ms inference, fraction of a cent per call. An LLM call is 500-2000ms and 100-1000x the cost.
**Practical model**: bag-of-words + sklearn → upgrade to small embedding + classifier if needed.
**N requirement**: ~200-500 labeled messages per class to start. Bootstrap from operator triage history.

### 2. Document Type Classification
**Use case**: incoming files/scans get auto-classified (passport scan, invoice, itinerary, insurance cert, payment confirmation, complaint screenshot).
**Why classical ML**: standard problem with strong off-the-shelf solutions (file-type heuristic → image classifier or OCR + text classifier).
**N requirement**: ~50-200 per class. Public pre-trained models cover most of it.

### 3. Will-This-Trip-Book Prediction
**Use case**: surface at proposal stage a probability that the trip converts. Operators triage their attention accordingly.
**Why classical ML**: tabular prediction with mixed features. Gradient boosting (xgboost/lightgbm) is the right tool. LLMs are overkill and worse at calibration.
**N requirement**: ~500 trips with known outcomes per agency before per-agency models; cross-agency baseline can ship earlier.
**Risk**: must be calibrated and presented as probability, not as recommendation.

### 4. Operator-to-Trip Routing (Learning to Rank)
**Use case**: when a new trip arrives, which available agent should pick it up? Today this is rule-based or first-available.
**Why classical ML**: learning-to-rank over (agent, trip) features (specialty match, current load, past success on similar trips, customer preference).
**N requirement**: large enough trip-assignment-outcome history. Probably v1 territory, not v0.
**Risk**: never auto-assign; surface as ranked suggestion. Operator preserves control.

### 5. Cancellation / Churn Risk
**Use case**: customer behavior + trip-stage signals predict cancellation risk; surfaces early-intervention opportunities.
**Why classical ML**: classic churn-prediction problem; well-studied; tabular features.
**N requirement**: needs sufficient cancellation events per agency, which is the whole point and also the bottleneck.

### 6. Anomaly Detection (Fraud, Operational Outliers, Drift)
**Use case**: trips that look unusual; agencies that look unusual; intake patterns that look unusual.
**Why classical ML**: isolation forest, autoencoders, statistical drift tests (PSI, KL-divergence). LLMs are wrong tool.
**N requirement**: workable at moderate N; scales well.
**Ties to**: Concept Drift Detection (off-map #3).

### 7. Priority Scoring Residual Layer
**Use case**: already documented separately — [PRIORITY_SCORING_LEARNING_LAYER](PRIORITY_SCORING_LEARNING_LAYER_EXPLORATION_2026-05-18.md). Logistic regression on top of the rule-based score.

### 8. Supplier Reliability Scoring
**Use case**: per-supplier reliability score from booking history, dispute history, cancellation rate, on-time performance.
**Why classical ML**: Bayesian / beta distributions for sparse-data confidence intervals; not a "model" so much as a statistical layer.
**N requirement**: works at any N if you present uncertainty honestly (wide confidence intervals when N is small).
**Ties to**: Supplier-Side Intelligence (C1 in [OPEN_EXPLORATION_IDEATION](OPEN_EXPLORATION_IDEATION_2026-05-18.md)).

---

## Where Embeddings Sit (Important Middle Layer)

Embeddings are not "ML" in the model-training sense, but they're not LLMs either — they're a retrieval/similarity primitive. Underused in the current product.

| Use case | Notes |
|---|---|
| Similar-trip retrieval | Off-map #2; foundational substrate |
| Semantic search over knowledge base | Operator-facing "what did we do for clients like this?" |
| Clustering inputs for KDD | KDD over embedding vectors instead of hand-crafted features for some tasks |
| Duplicate / near-duplicate detection | "Have we seen this customer or trip before?" |
| Cross-language similarity | Once multi-language intake matters |

**Practical recipe**: pgvector inside Postgres (no new service); `text-embedding-3-small` for cost-quality balance, or a local sentence-transformer for cost-privacy. Build the embedding pipeline once; reuse across many features.

---

## Where ML Is Overkill or the Wrong Tool

Be honest about where ML doesn't belong:

| Anti-pattern | Better approach |
|---|---|
| Predicting things a rule decides exactly | Use the rule |
| Tasks with N too small to train honestly | Rule + escalation; revisit at threshold |
| Replacing operator judgment in customer-facing decisions | Never (this is the line) |
| Building "ML platform" before having 3+ models in production | Use scikit-learn locally; defer platform |
| LLM-everywhere because the LLM API is easy | Profile cost + latency; downgrade where classical works |
| Fine-tuning early to "improve quality" | Prompt-engineer first; fine-tune only when prompt hits ceiling AND volume justifies it |
| Custom-trained embeddings before off-the-shelf hits the wall | Use off-the-shelf; custom is a v3 conversation |

---

## The Cost / Latency Argument (Often Decisive)

A typical comparison for a routine classification task:

| Approach | Latency | Per-call cost | Per-1M-call cost |
|---|---|---|---|
| Rule | <1ms | $0 | $0 |
| Classical ML | 1-10ms | ~$0.000001 | ~$1 |
| Embeddings + classifier | 50-100ms | ~$0.0001 | ~$100 |
| Small LLM (cheap tier) | 300-800ms | ~$0.0001-$0.001 | ~$100-$1,000 |
| Frontier LLM | 1-5s | ~$0.005-$0.05 | ~$5,000-$50,000 |

For high-volume tasks, the difference is six orders of magnitude. **"Use LLM for everything" becomes a real P&L problem at scale.** This is the single strongest argument for the layered approach.

---

## Fine-Tuning: When It's Actually Right

Don't fine-tune to "improve quality." Fine-tune when:

1. **Volume**: a task runs ≥100K times/month and LLM cost is a material line item.
2. **Plateau**: prompt-engineering has hit a real ceiling, not "we tried a few prompts."
3. **Proprietary signal**: the task depends on data only you have (your trip outcomes, your operator overrides), and that data improves the model meaningfully.
4. **Stable task definition**: fine-tuning a moving target is waste.

Realistic candidates eventually: intake extraction (high volume, proprietary signal, stable task), draft generation in a specific agency's voice (proprietary signal, but only for premium tier). Not now; possibly in 12-18 months.

**Until then**: prompt engineering + cheaper-model routing + few-shot is almost always more cost-effective than fine-tuning.

---

## ML Infrastructure: How Much, How Soon

**Most failed ML strategies fail at infrastructure**, not algorithms. The trap: building a "platform" before you have models that need it.

Honest progression:

| Stage | Models in production | Infrastructure needed |
|---|---|---|
| 0 | 0 | None. Notebook + scripts. |
| 1 | 1-2 | Existing job runner + a `models/` table for versions. |
| 2 | 3-5 | Lightweight model registry (filesystem + DB rows); feature view in DB. |
| 3 | 5-10 | Real feature store (Feast or homegrown); proper model registry; CI for model rollout. |
| 4 | 10+ or regulated workloads | Full MLOps (training pipelines, monitoring, A/B routing, drift alerts). |

**Recommendation**: stay at stage 0-1 as long as possible. The KDD pipeline + this document's recommended classifiers fit comfortably at stage 1.

---

## Specific Recommendations for This Project

### Now (gated on no new prerequisites)
1. **Email/message classification** (small classifier, ~1 day of work + labeling). Replaces LLM calls in the triage path → measurable cost win.
2. **Document type classification** when document collection ships. Small image classifier or OCR + text classifier.
3. **Supplier reliability statistical layer** (not really ML — beta distribution + confidence intervals) once supplier intelligence (C1) ships.

### After KDD v0 (reusing its infrastructure)
4. **Will-book prediction** (gradient boosting on tabular features). Pairs with KDD override mining and suitability mining.
5. **Operator-behavior modeling** for priority residual (already scoped in priority learning layer).

### Gated on data volume
6. **Cancellation / churn prediction** — needs cancellation events.
7. **Routing / learning-to-rank** — needs assignment-outcome history.
8. **Anomaly detection in production** — pair with concept-drift detection.

### Eventually, only if conditions met
9. **Fine-tune intake extraction** — only when volume + plateau + cost justify.
10. **Custom embeddings** — only when off-the-shelf hits a wall.

### Never (in scope I can see)
- Reinforcement learning for agent policy.
- Generative video / image / audio models (not the wedge).
- Generic "AutoML" platform.

---

## Risks

| Risk | Mitigation |
|---|---|
| LLM-everywhere becomes a cost problem at scale | Profile cost per feature; identify candidates for downgrade. |
| Building too much ML infra too early | Stage 0-1 discipline; resist platform-building until 5+ models live. |
| Models that nobody owns operationally | Each model gets an owner + a kill switch. No exceptions. |
| Stealth ML decisions affecting customers | Explainability + autonomy framework (off-map / Open A1+A2) must precede customer-affecting model decisions. |
| Drift unnoticed | Concept drift detection (off-map #3) is the safety net every ML system needs. |
| ML overshadows the LLM-native strengths | LLMs are still the product's core; ML augments specific layers. Don't let "we're using ML now" reframe the product. |
| Classical ML treated as second-class because LLMs feel modern | Reverse the bias intentionally. Cheap, fast, deterministic models are professional; LLM-everywhere is amateur-hour at scale. |

---

## What This Doc Does NOT Cover

- **LLM cost optimization** (model routing, caching, prompt compression) — that's [LLM Strategy & Cost (#4)](../EXPLORATION_TOPICS.md) territory. ML strategy and LLM strategy are siblings; this doc avoids stepping on the other.
- **Evaluation framework for ML models** — same as for LLMs, see [#6 Evaluation Framework](../EXPLORATION_TOPICS.md). Both LLM evals and classical ML metrics live there.
- **Specific algorithm tutorials** — this is strategy, not handbook.
- **MLOps platform comparison** — premature for this project's stage.

---

## Open Questions

1. Is there appetite for *one specific* classical-ML feature shipping in the next 30 days (message classification feels like the strongest candidate)?
2. Who owns the boundary between "use an LLM" and "use a classifier" — engineering taste, cost monitoring, or product?
3. What is the current monthly LLM spend, and which features dominate it? (Drives where ML downgrade has the most ROI.)
4. Is there a stated principle on AI/ML autonomy (touches A1 in [OPEN_EXPLORATION_IDEATION](OPEN_EXPLORATION_IDEATION_2026-05-18.md))? Some ML features (routing, prediction) push autonomy questions earlier than expected.
5. Cross-agency ML — when does it start being acceptable and under what privacy contract?

---

## Bottom Line

This product's identity is "LLM-native travel agency OS" — and it should stay that way. But identity ≠ implementation. Internally the right tool wins per task:

- **LLMs** for the language-shaped problems (most of the user-visible AI).
- **Classical ML** for the score/classify/rank-shaped problems (mostly invisible to users; visible in cost and quality).
- **Embeddings** for the similarity/retrieval-shaped problems (foundational substrate).
- **Rules** for everything else (most things, actually).

The risk to manage: every team building LLM-heavy products eventually realizes the layered approach is necessary. The teams that realize it early ship cheaper, faster, more reliable products. The teams that realize it late have to retrofit while bleeding margin.

This doc is a recommendation to realize it early.

---

*Open exploration document. Recommendations are hypotheses to validate against actual cost/latency profiles, not commitments.*
