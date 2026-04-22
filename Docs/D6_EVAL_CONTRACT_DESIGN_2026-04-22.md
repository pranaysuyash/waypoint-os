# D6 Evaluation Contract Design — Phase B

**Date**: 2026-04-22
**Basis**: Hybrid Engine Audit Phase A (`Docs/HYBRID_ENGINE_AUDIT_2026-04-22.md`)
**Purpose**: Define the minimal eval contract that validates judgment accuracy before it reaches consumer surfaces (D2 gate)

---

## 1. The Problem D6 Solves

From the governing principle (V02 §1):
> "Every repeated LLM judgment should be considered a candidate for graduation into a deterministic rule"

From the audit:
> "Without D6, graduation is dangerous."

D6 is the validation layer. It answers:
1. Is the NB02 state machine making correct decisions on known inputs?
2. Is the hybrid engine's rule coverage sufficient?
3. When the system says "PROCEED_TRAVELER_SAFE", is it actually safe?
4. What confidence threshold justifies shipping a consumer-facing surface (D2)?

---

## 2. Three-Phase Eval Progression (per ADR)

| Phase | Name | Purpose | Entry Gate | Exit Gate |
|-------|------|---------|------------|-----------|
| Phase 1 | **Golden Path** | Validate NB02 state machine on canonical fixtures | Fixture corpus ready | 95% state accuracy ongolden paths |
| Phase 2 | **Shadow Mode** | Run eval in parallel with production, compare divergence | Golden path passing | <5% divergence on production traffic |
| Phase 3 | **Gating** | Block consumer surface deployment if eval fails | Shadow mode stable | CI/CD gate: eval must pass before D2 code ships |

---

## 3. Golden Path Fixture Contract

### Fixture Schema
```json
{
  "fixture_id": "gp_001_family_jaipur",
  "category": "family_travel",
  "complexity": "low",
  "description": "Standard family trip to Jaipur, budget ₹2L, 2 adults + 2 kids",
  
  "input": {
    "canonical_packet": { /* full packet v0.2 */ }
  },
  
  "expected": {
    "decision_state": "PROCEED_TRAVELER_SAFE",
    "confidence": { "data": 0.9, "judgment": 0.85, "commercial": 0.7 },
    "risk_flags": [],
    "blockers": [],
    "ambiguities": []
  },
  
  "eval_rules": {
    "strict_state_match": true,
    "allowable_divergence": { /* optional tolerance */ }
  },
  
  "rationale": "Standard case: all required fields present, budget realistic, no composition risks for typical family"
}
```

### Fixture Tiers

| Tier | Count | Description |
|------|-------|-------------|
| Tier 1 — Canonical | 20 | Clean inputs, obvious decisions. Baseline for "does the system even work?" |
| Tier 2 — Edge Cases | 15 | Missing fields, budget stress, composition risks, visa urgency |
| Tier 3 — Adversarial | 10 | Contradictory inputs, ambiguous destinations, conflicting dates |
| Tier 4 — Real-World Derived | 25 | Derived from actual test cases or simulated scenarios |

**Total**: 70 fixtures for initial corpus. This is manageable by hand and covers the decision surface.

### Fixture Sources
1. `data/fixtures/test_messages.json` (30 categorized cases)
2. `data/fixtures/trip_examples.json` (complete trip examples)
3. `Docs/Trip_Feasibility_Scenario_*.md` synthetic scenarios
4. Manual construction for missing categories

---

## 4. Shadow Mode Comparison Protocol

### What Is Shadow Mode
Run the eval harness on production traffic **without affecting** the real decision. Compare:

```
Production NB02 decision:  PROCEED_TRAVELER_SAFE
Shadow eval decision:      PROCEED_TRAVELER_SAFE
Divergence:                NONE (match)

Production NB02 decision:  PROCEED_TRAVELER_SAFE  
Shadow eval decision:      ASK_FOLLOWUP
Divergence:                HIGH (flag for review)
```

### Protocol Design

```python
class ShadowComparison:
    """Structured divergence report."""
    
    packet_id: str
    production_state: DecisionState
    shadow_state: DecisionState
    match: bool
    divergence_type: Optional[Literal["state", "confidence", "flags", "rationale"]]
    severity: Literal["low", "medium", "high", "critical"]
    
    # Context for debugging
    production_risk_flags: List[Dict]
    shadow_risk_flags: List[Dict]
    packet_summary: Dict  # redacted, no PII
```

### Divergence Categories

| Category | Definition | Action |
|----------|-----------|--------|
| **State divergence** | `decision_state` differs | Always flagged |
| **Confidence divergence** | Same state but confidence differs by >0.2 | Monitor |
| **Flag divergence** | Same state but different risk flags | Monitor |
| **Rationale divergence** | Same state but different follow-up questions | Low priority |

### Alert Thresholds
- >0% state divergence on Tier 1 fixtures → **Block CI**
- >5% state divergence on shadow traffic → **Alert owner, don't block**
- >10% state divergence → **Escalate to STOP_NEEDS_REVIEW for affected packets**
- Single critical divergence (`PROCEED_TRAVELER_SAFE` vs `STOP_NEEDS_REVIEW`) → **Immediate alert**

---

## 5. Consumer Surface Gate (D2 Dependency)

The D2 consumer surface (Itinerary Checker free tool) is gated on eval precision.

### Precision Requirements by Surface

| Surface | Required Eval Precision | Rationale |
|---------|------------------------|-----------|
| Internal workbench (current) | No eval gate | Operator reviews everything anyway |
| Agency owner dashboard | 90% state accuracy | Owner trusts system recommendation |
| Consumer free engine (D2) | **95% state accuracy** + <2% false positive on `PROCEED_TRAVELER_SAFE` | Consumer has no recourse if we mis-judge feasibility |
| Public pricing estimate | 99% state accuracy | Financial estimates must be reliable |

### Why 95% for Consumer Surface
A consumer-facing itinerary checker that says "this trip is feasible" when it's actually a `STOP_NEEDS_REVIEW` case destroys trust. The 95% threshold means:
- 19/20 itineraries are correct
- 1/20 is conservatively gated to review
- False negatives (telling someone their trip needs review when it's actually fine) are acceptable
- False positives (telling someone their trip is fine when it's not) are **not acceptable**

### D1 Autonomy Policy Integration
From the D1 policy contract we just implemented, add an eval-derived gate:

```python
# In AgencyAutonomyPolicy.effective_gate()
if eval_precision < 0.95:
    # Override to review for consumer-facing decisions
    return "review", "eval_precision_below_threshold"
```

This means: even if the policy says "auto" for `PROCEED_TRAVELER_SAFE`, the eval system can downgrade to "review" if precision is insufficient.

---

## 6. Eval Infrastructure Contract

### Directory Structure
```
src/evals/
├── __init__.py
├── golden_path/
│   ├── fixtures/           # 70 JSON fixtures
│   ├── runner.py           # execute fixtures, compare expected vs actual
│   └── report.py           # generate markdown/HTML reports
├── shadow/
│   ├── divergence_tracker.py
│   └── alert_manager.py
├── gating/
│   ├── ci_gate.py          # pytest plugin or pre-commit hook
│   └── deployment_gate.py  # blocks Deploy if eval < threshold
└── contracts/
    ├── fixture_schema.py   # Pydantic models for fixtures
    └── comparison_models.py
```

### Runner Interface
```python
class GoldenPathRunner:
    """Execute golden path fixtures and produce eval reports."""
    
    def __init__(self, fixture_dir: Path, engine: NB02Engine):
        self.fixtures = load_fixtures(fixture_dir)
        self.engine = engine
    
    def run(self) -> EvalReport:
        results = []
        for fixture in self.fixtures:
            actual = self.engine.evaluate(fixture.input.packet)
            expected = fixture.expected
            results.append(compare(fixture.id, expected, actual))
        
        return EvalReport(results)
    
    def assert_passing(self, threshold: float = 0.95) -> None:
        report = self.run()
        if report.accuracy < threshold:
            raise EvalFailure(f"Eval failed: {report.accuracy} < {threshold}")
```

### CI/CD Integration
```yaml
# .github/workflows/eval.yml (conceptual)
name: Eval Gate
on: [pull_request]
jobs:
  eval:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Golden Path Eval
        run: uv run pytest tests/evals/test_golden_path.py --threshold=0.95
      - name: Run Shadow Comparison
        run: uv run pytest tests/evals/test_shadow_divergence.py --threshold=0.05
```

---

## 7. Statistical Methodology

### Accuracy Metrics

| Metric | Formula | Target |
|--------|---------|--------|
| **State Accuracy** | correct_states / total_fixtures | ≥95% |
| **Per-State Precision** | TP(state) / (TP + FP) | ≥90% for PROCEED_TRAVELER_SAFE |
| **Per-State Recall** | TP(state) / (TP + FN) | ≥90% for STOP_NEEDS_REVIEW |
| **False Positive Rate** | FP(PT-safe) / total_actual_not_safe | <2% |
| **Confidence Calibration** | avg(confidence when correct) - avg(confidence when wrong) | >0.3 |

### Why Per-State Metrics Matter
Global accuracy can hide bias. If the system is 99% accurate but all errors are on `STOP_NEEDS_REVIEW` (safety-critical), that's worse than 90% accuracy with evenly distributed errors.

### Confidence Calibration
A well-calibrated system should have higher confidence when correct and lower confidence when wrong. The `ConfidenceScorecard` in `intake/decision.py` provides three confidence dimensions (data/judgment/commercial). The eval should verify they're actually predictive.

---

## 8. Relationship to D1 Autonomy

The eval system feeds directly into D1:

```
NB02 evaluates packet
    ↓
Eval system checks accuracy (D6)
    ↓
D1 autonomy policy considers eval precision + NB02 state
    ↓
Effective gate action (auto / review / block)
    ↓
Downstream consumer (agency owner) or public surface (D2 consumer)
```

If eval precision is below threshold, `effective_gate()` should:
1. Downgrade `auto` → `review` for consumer-facing outputs
2. Emit telemetry: `rule_source = "eval_precision_gate"`
3. Alert the owner that eval confidence is insufficient for auto-mode

---

## 9. Implementation Order

The eval contract is designed to be implemented in phases:

1. **Phase 0 (now)**: Define fixture schema and write 10 Tier-1 fixtures. No runner yet.
2. **Phase 1**: Implement `GoldenPathRunner`, run against existing NB02. Document baseline accuracy.
3. **Phase 2**: Build shadow comparison infrastructure. Start producing divergence reports.
4. **Phase 3**: Wire D1 `effective_gate()` to eval precision. Add CI gate.

---

## 10. Verification

Success criteria for this design:

1. ✅ Fixture schema is versioned and backward-compatible
2. ✅ CI gate can be implemented as a pytest plugin
3. ✅ Shadow mode produces structured divergence reports
4. ✅ D1 autonomy policy has a slot for eval-derived precision
5. ✅ Consumer surface gate has explicit accuracy requirements

```bash
# Phase 0 verification (schema only)
uv run pytest tests/evals/test_fixture_schema.py -q

# Phase 1 verification (once runner exists)
uv run pytest tests/evals/test_golden_path.py --threshold=0.95 -q
```

---

## References

- `Docs/ARCHITECTURE_DECISION_D4_D6_SUITABILITY_AUDIT_2026-04-16.md` — Original D6 ADR
- `Docs/ARCHITECTURE_DECISION_LLM_CACHE_NB05_NB06_2026-04-16.md` — NB05/NB06 rationale
- `Docs/HYBRID_ENGINE_AUDIT_2026-04-22.md` — Phase A findings this design responds to
- `Docs/ARCHITECTURE_DECISION_D1_AUTONOMY_GRADIENT_2026-04-18.md` — D1 eval precision integration
- `Docs/V02_GOVERNING_PRINCIPLES.md` — Deterministic-first principle

---

Checklist applied: IMPLEMENTATION_AGENT_REVIEW_HANDOFF_CHECKLIST.md
