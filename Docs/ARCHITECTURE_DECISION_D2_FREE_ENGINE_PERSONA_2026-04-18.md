# Architecture Decision: D2 — Free Engine Target Persona

**Date**: 2026-04-18
**Status**: Decision document — core architecture locked, execution sequenced by dependency
**Source**: `Docs/DISCUSSION_THESIS_DEEP_DIVE_2026-04-16.md` Thread 2 ("Intelligence Layer as Lead-Gen")
**Cross-references**:
- `Docs/context/ITINERARY_CHECKER_GTM_WEDGE_2026-04-14.md` (execution plan for consumer-facing checker)
- `Docs/context/DECISION_MEMO_ITINERARY_CHECKER_2026-04-14.md` (v1 scope lock, 30-day go/no-go gates)
- `Docs/PRODUCT_VISION_AND_MODEL.md` L85-91 (free engine validation wedge)
- `Docs/PILOT_AND_CUSTOMER_DISCOVERY_STRATEGY.md` L124-137 (Approach A: "Free Beta Tester")
- `Docs/V02_GOVERNING_PRINCIPLES.md` L55 (`operating_mode: "audit"`)
- `Docs/ARCHITECTURE_DECISION_D4_D6_SUITABILITY_AUDIT_2026-04-16.md` (audit eval suite, manifest-driven categories)
- `Docs/FIRST_PRINCIPLES_FOUNDATION_2026-04-14.md` Stage 7 (GTM surfaces after quality floor)

---

## Document Consolidation Note

The thesis deep dive (Thread 2) identified "Funnel B: Consumer audit → agency referral" as a concept. The **Itinerary Checker GTM Wedge** (`Docs/context/ITINERARY_CHECKER_GTM_WEDGE_2026-04-14.md`) and its **Decision Memo** (`Docs/context/DECISION_MEMO_ITINERARY_CHECKER_2026-04-14.md`) are the execution plan for that same concept. These are the same thing described at two altitudes — the thesis deep dive named the funnel, the GTM wedge scoped the product.

Going forward, references to "Funnel B" and "itinerary checker GTM wedge" should be understood as the same initiative.

---

## The Two Funnels (Both Production Targets, Sequenced by Dependency)

| | Funnel A: Agency Self-Audit | Funnel B: Consumer Free Engine (= Itinerary Checker GTM Wedge) |
|---|---|---|
| **Who** | Agency owner/planner validating their own itinerary | End traveler with an existing plan from any source |
| **Motivation** | Quality check before sending to client | "What should I be asking about before I finalize?" |
| **Conversion** | Adopts full platform (PLG hook) | Becomes informed consumer; organic lead if agency can't answer well |
| **Friction** | Low — already knows the tool | Medium — trust earned by helpfulness, not by redirect |
| **Ships when** | Stage 2 (current) — `operating_mode: "audit"` | After D6 eval suite gating categories pass precision thresholds |

---

## Positioning Decision (Critical — Owner-Directed)

### What the free engine IS

> "Here are things worth discussing with your planner before you finalize."

The free engine **empowers the consumer to ask better questions** of their existing agency. It does NOT claim to do better than the agency. It surfaces risks, gaps, and questions the consumer might not have thought to ask.

### What the free engine is NOT

- NOT "your plan is bad, we'll fix it" (adversarial to agencies)
- NOT "we found problems, want a better agency?" (trust transfer fails)
- NOT a replacement for agency planning (reinforces the "copilot, not replacement" thesis from Thread 1)

### Why This Positioning Works

1. **Consumer trust**: The tool earns credibility by helping, not by attacking. The consumer's relationship with their agency is respected.
2. **Agency non-hostility**: Agencies don't see this as a threat. If anything, their clients come back with better questions — which makes the agency's job easier if they're good, and exposes gaps if they're not.
3. **Natural lead-gen**: The conversion isn't forced. If the consumer asks their agency "what about visa requirements for our transit stop?" and the agency can't answer well, the consumer discovers organically that they need better planning support. The itinerary checker CTA ("want to explore this with a partner agency?") is an option, not a push.
4. **Precision imperative**: Under this framing, a false positive doesn't just damage brand — it undermines the consumer's relationship with their own agency on false pretenses. Precision must be high.

### How This Maps to the GTM Wedge Output

The itinerary checker's free tier output (`ITINERARY_CHECKER_GTM_WEDGE_2026-04-14.md` L40-44):
- Overall score (0-10) — reframe as "completeness score" not "quality score"
- Top critical + warning issues — reframe as "things to discuss with your planner"
- Basic extraction summary — what the system understood from the uploaded plan
- CTA — "want to explore these questions further?" not "want a better agency?"

---

## Architecture Decision: Shared Pipeline, Different Presentation

### One Pipeline, Two NB03 Builders

Both funnels use the same NB01 → NB02 → NB03 pipeline. The difference is in presentation and filtering.

```
Consumer uploads itinerary → NB01 (normalize) → CanonicalPacket (operating_mode: "audit")
                                                        ↓
Agency submits for self-audit → NB01 (normalize) → CanonicalPacket (operating_mode: "audit")
                                                        ↓
                                                   NB02 (judgment)
                                                   Same analyzers, same rules
                                                        ↓
                                                   DecisionResult
                                                        ↓
                                              ┌─────────┴─────────┐
                                              │                   │
                                    presentation_profile      presentation_profile
                                       = "agency"               = "consumer"
                                              │                   │
                                    NB03 Agent Audit         NB03 Consumer Report
                                    Builder                  Builder
                                              │                   │
                                    Full findings,           Filtered findings,
                                    internal language,       consumer-safe language,
                                    workspace integration    score + discussion points
```

### What Differs Between Surfaces

| Dimension | Agency Self-Audit | Consumer Free Engine |
|-----------|-------------------|---------------------|
| `operating_mode` | `"audit"` | `"audit"` (same) |
| `presentation_profile` | `"agency"` | `"consumer"` (new field — controls NB03 builder selection) |
| Input source | Structured/freeform via workspace | Upload (PDF/image/text) via public page |
| Rule coverage | Full rule set — all categories | Curated subset — only `gating` category rules (per D6 manifest) |
| Output format | Full `DecisionResult` in workspace | Scored report: completeness score + discussion points + CTA |
| Language | Internal language OK (risk flags, technical terms) | Consumer-safe language only (per NB03 visibility semantics) |
| Findings framing | "Issues found" | "Things to discuss with your planner" |
| Data capture | Trip enters agency pipeline | Structured brief captured; lead routing optional |
| False positive tolerance | Low (agent can override, but erodes trust) | Very low (no agent to catch; undermines consumer-agency relationship) |

### Quality Bar: Stricter for Consumer Surface

The consumer has no agent to catch errors. Under the empowerment framing, a false positive tells the consumer to question their agency about a non-issue — damaging a real relationship on false pretenses.

**Rule**: Consumer surface only shows findings from `gating` category rules (per D6 eval suite manifest):
- `gating` status requires: precision ≥ 0.95, recall ≥ 0.95, severity accuracy ≥ 0.90
- `shadow` category rules (precision/recall still being measured) do NOT appear on consumer surface
- `planned` category rules (not yet implemented) obviously excluded

This means the consumer surface starts narrow (budget findings only, since that's the first `gating` category) and expands as more categories graduate from `shadow` → `gating`. The D6 eval suite is the quality gate for consumer-surface expansion.

### Why Not a Separate "Lite" Pipeline

The itinerary checker GTM wedge doc proposed "NB02-lite with 15 initial checks" — a constrained ruleset. Under the shared pipeline architecture:
- These aren't separate rules — they're the same `AuditRule` instances from the D6 registry
- "15 initial checks" = the rules in `gating` status at launch time
- As more rules graduate to `gating`, the consumer surface automatically gets richer
- Accuracy improvements (from D6 eval fixtures, feedback, cache → rule graduation) compound across both surfaces

A separate lite pipeline would fork accuracy trajectories — the agency surface would improve while the consumer surface stagnates on its own rule set. Shared pipeline prevents this.

---

## Sequencing (Dependency-Ordered)

| Phase | What | Depends On |
|-------|------|------------|
| **Now** (Stage 2) | Agency self-audit via `operating_mode: "audit"` in workspace | Budget feasibility (✅ exists), audit-mode NB03 builder |
| **After D6 eval suite** | Consumer report NB03 builder (presentation_profile: "consumer") | D6 gating categories passing precision thresholds |
| **After precision gates** | Public-facing upload page + consumer report rendering | Frontend public surface, PDF/image extraction (NB01 enhancement) |
| **After conversion validation** | Paid fix tier (₹999 per decision memo) + lead routing | 30-day go/no-go gates from decision memo passing |

The 30-day go/no-go gates from the decision memo (`DECISION_MEMO_ITINERARY_CHECKER_2026-04-14.md` L33-40) apply to the consumer surface specifically:
- Upload completion rate ≥ 20%
- Valid extraction success ≥ 85%
- Critical-rule precision ≥ 80% (note: this is the go/no-go gate, not the per-rule gating threshold)
- Email capture ≥ 25%
- Paid fix conversion ≥ 5%

---

## Contract Addition

```python
# Addition to audit request / NB03 builder selection
presentation_profile: Literal["agency", "consumer"] = "agency"
```

This field controls:
1. Which NB03 builder runs (agent audit builder vs. consumer report builder)
2. Which findings are surfaced (all vs. gating-only)
3. Language register (internal vs. consumer-safe)
4. Output format (workspace integration vs. scored report)

It does NOT affect NB01 or NB02 — the pipeline is identical up to the presentation layer.

---

*Both funnels are production targets. Agency self-audit ships first because the pipeline already supports it. Consumer free engine ships after the D6 eval suite proves accuracy. The free engine empowers consumers to ask better questions — it doesn't claim to replace their agency. Shared pipeline ensures improvements compound across both surfaces.*
