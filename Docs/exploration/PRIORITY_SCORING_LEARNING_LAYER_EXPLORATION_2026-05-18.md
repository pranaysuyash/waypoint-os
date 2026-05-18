# Priority Scoring — Learning Layer (Extension of #20)

**Date**: 2026-05-18
**Status**: Exploration draft. Strictly an **extension** of an existing complete design — does not duplicate or override it.
**Parent index**: [../EXPLORATION_TOPICS.md](../EXPLORATION_TOPICS.md) #20
**Builds on**: [DESIGN_2D_PRIORITY_MODEL_2026-05-08.md](../DESIGN_2D_PRIORITY_MODEL_2026-05-08.md) *(design complete, implementation pending)*
**Related**: KDD override mining (override→signal), Process mining (stuck-trip→signal), Advanced Learning & Optimization (#15)

---

## 1. Scope Statement (Read First)

The 2D priority model (urgency × importance) is already designed in [DESIGN_2D_PRIORITY_MODEL_2026-05-08.md](../DESIGN_2D_PRIORITY_MODEL_2026-05-08.md). That work is **the source of truth** for the rule-based scoring formula. This document does **not** propose a different model, alternative formula, or replacement.

What this doc proposes is a **second-stage learning layer** that sits *on top of* the rule-based score, observes operator behavior, and adjusts only at the margins where evidence is strong. The rule-based score remains the authoritative default.

## 2. Why a Learning Layer Is Worth Considering Separately

Rule-based scoring is correct, debuggable, and shippable. Its limitation: it can't tell you that **this specific agency** treats "SLA-yellow + high-value + repeat-client" trips with higher actual urgency than the formula assigns. Only behavior reveals that.

A learning layer answers:
- Which operators actually pick up first, and how does it differ from the score's ranking?
- Which signals predict "operator opens this trip within N minutes" better than the rule formula?
- Where does the rule-based formula systematically over- or under-prioritize per agency?

This is the same KDD pattern as override mining (parent KDD doc): observed behavior is a labeled signal that the deterministic system can't see.

## 3. What This Adds That #20 Doesn't

| Concern | Rule-based #20 | Learning layer (this doc) |
|---|---|---|
| Initial score for new trip | ✅ owns this | reads, never overrides |
| Behavior when formula is wrong | manual tuning | observes, surfaces, optionally adjusts |
| Agency-specific differences | constants in the formula | learned weight residuals per agency |
| Explainability | full (rule trace) | full (rule trace + residual + N) |
| Safety / kill switch | ✅ #20 already includes | inherits + adds its own off-switch |
| Cold start | works day one | needs N before contributing |

## 4. Architectural Constraint

The learning layer must satisfy three rules to be acceptable:

1. **Additive only**: the final shown priority is `rule_score + learned_residual`, where `learned_residual` is 0 until evidence exceeds threshold.
2. **Bounded influence**: residual capped at ±X% of the rule score (e.g., 20%). The rule formula always dominates.
3. **Always explainable**: every shown priority decomposes into its rule components + the residual + the residual's evidence count.

If any of these three is violated, the layer becomes a shadow model that nobody can debug. That's how learning-based prioritization fails in production.

## 5. KDD Framing

| Step | Activity |
|---|---|
| Selection | Per-trip events: `(rule_score_at_t, time_to_first_operator_open, operator_actions, outcome)`. |
| Preprocessing | Join trip features with rule-score components; bucket time-to-open into ordinal bands. |
| Transformation | Feature vector = rule components + trip metadata. Target = operator behavior signal (e.g., open-within-15-min). |
| Mining | Per-agency lightweight model — start with logistic regression over rule components. Resist neural nets; keep the model interpretable. |
| Interpretation | The model's residual vs the rule score becomes the learned adjustment. Surface alongside the rule trace. |

## 6. Why Logistic Regression (Not Something Fancier)

- Linear, interpretable, per-feature coefficient = explainable to operators.
- Trains on tiny N without overfitting if regularized.
- Easy to bound, easy to audit, easy to kill.
- Fancier models (gradient boosting, neural) buy little here because the rule formula already captures most signal; the residual is a small slice.

If logistic regression hits a ceiling, the next step is *more features*, not a more complex model.

## 7. Risks

| Risk | Mitigation |
|---|---|
| Learning amplifies operator bias | Per-agency only; review of learned coefficients before they affect display; explicit "this is what the system learned" surface. |
| Drift over time | Rolling window training; coefficient deltas tracked; kill switch if drift exceeds threshold. |
| Cold-start agency penalized | Residual = 0 until N threshold; document N. |
| Operators game the system | Reuse #20's kill switch; add coefficient-stability monitoring. |
| Layer becomes the new source of truth | §4 rules 1-3 are non-negotiable. If they erode, scrap the layer. |
| Conflict with existing rule-tuning workflow | Coordinate ownership: rule constants are deterministic config, residuals are observed. Document the boundary. |

## 8. Relationship to Other Mining Topics

- **KDD override mining**: every override produces a "this was wrong" signal usable here too. A trip operators repeatedly override is one the priority formula likely misranked.
- **Process mining**: trips stuck in their stage are priority candidates. The mining output can become a new rule input (preferred) or a residual feature (secondary).
- **Suitability mining**: orthogonal — suitability is about *which trips will book*, priority is about *which trip to work on next*.

## 9. Decision Recommendation

**Defer until the rule-based #20 is implemented and in production for ≥4 weeks.** Reasoning:
- The rule formula must exist and be observed before its residuals can be learned.
- Operator-behavior signal needs accumulation.
- Building both in parallel risks the learning layer biasing the rule design.

When #20 is in production with ≥4 weeks of observed behavior, revisit this with real data. Estimated effort then: 2-3 days for v0 with logistic regression + the explainability surface.

## 10. Kill Criteria

If after 4 weeks of operation:
- coefficients are unstable (sign flips week-to-week), or
- residuals don't correlate with measured operator outcomes, or
- no operator notices the difference when the residual is toggled off,

scrap the layer. Keep the rule-based model. No partial keeps.

## 11. Open Questions

1. What is the canonical operator-behavior signal — first-open time, time-to-action, completed action, all of the above?
2. Does the surface in #20 already have a hook for "adjustment shown alongside rule trace"?
3. Per-agency vs per-agency-per-role: do owners and junior agents need separate residuals?
4. Where does the residual training run — same job runner as KDD v0?
5. Privacy: per-operator residuals are explicitly out of scope (avoidance of individualized scoring). Confirm.

---

*Extension exploration. The rule-based design (#20) remains authoritative.*
