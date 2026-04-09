# Research: Evaluation Framework

**Status**: 🔵 Specification — Testing Beyond Unit Tests  
**Topic ID**: 18  
**Parent**: [EXPLORATION_TOPICS.md](../EXPLORATION_TOPICS.md)  
**Last Updated**: 2026-04-09

---

## The Problem

Unit tests verify code correctness. But for an LLM-based travel system, we need to verify:

1. **Output Quality** — Is the proposal actually good?
2. **Decision Accuracy** — Does the system make the right calls?
3. **Business Outcomes** — Does it convert? Does it retain?
4. **Safety** — Does it avoid harmful recommendations?

**The challenge**: You can't `assert proposal.quality == "good"`.

---

## Evaluation Layers

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         EVALUATION PYRAMID                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  LAYER 4: BUSINESS OUTCOMES                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Conversion rate, customer satisfaction, repeat bookings, margin   │   │
│  │  Measured with: A/B tests, cohort analysis, surveys                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    ▲                                        │
│  LAYER 3: HUMAN EVALUATION                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Expert review of proposals, blind scoring, side-by-side compare   │   │
│  │  Measured with: Rubrics, inter-rater reliability                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    ▲                                        │
│  LAYER 2: LLM-AS-JUDGE                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Automated scoring using GPT-4/Claude as evaluator                 │   │
│  │  Measured with: Accuracy vs human judgments, consistency           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    ▲                                        │
│  LAYER 1: STRUCTURAL VALIDATION                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Schema compliance, completeness, constraint satisfaction          │   │
│  │  Measured with: Unit tests, property-based tests                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Layer 1: Structural Validation

### What We Test

| Test Type | What It Checks | Example |
|-----------|---------------|---------|
| **Schema Compliance** | Output matches expected structure | `TravelerProposal` has all required fields |
| **Completeness** | All required sections filled | Every day has activities |
| **Constraint Satisfaction** | Business rules respected | Budget not exceeded by >10% |
| **Referential Integrity** | Internal consistency | Hotel check-out = next hotel check-in |

### Implementation

```python
# Property-based testing with Hypothesis
from hypothesis import given, strategies as st

@given(
    destination=st.sampled_from(["Singapore", "Thailand", "Dubai"]),
    budget=st.integers(min_value=50000, max_value=500000),
    nights=st.integers(min_value=2, max_value=14),
)
def test_proposal_respects_budget(destination, budget, nights):
    """Generated proposal must respect budget constraint."""
    packet = make_packet(destination=destination, budget=budget, nights=nights)
    proposal = generate_proposal(packet, agency_data)
    
    assert proposal.pricing.total_for_group <= budget * 1.1  # 10% buffer


def test_proposal_completeness():
    """All proposals must have required sections."""
    REQUIRED_SECTIONS = [
        "title", "summary", "highlights", "days", 
        "pricing", "why_this_fits", "next_steps"
    ]
    
    for scenario in TEST_SCENARIOS:
        proposal = generate_for_scenario(scenario)
        for section in REQUIRED_SECTIONS:
            assert getattr(proposal, section) is not None, \
                f"{scenario.name} missing {section}"
```

### Metrics

- **Pass rate**: % of tests passing
- **Coverage**: % of code paths covered
- **Fuzz failures**: Issues found by property-based testing

---

## Layer 2: LLM-as-Judge

### The Concept

Use a strong LLM (GPT-4, Claude) to evaluate outputs. Cheaper than human evaluation, scalable, reasonably accurate.

### Evaluation Prompts

```python
PROPOSAL_QUALITY_PROMPT = """
You are an expert travel consultant evaluating a trip proposal.

CUSTOMER PROFILE:
- Destination: {destination}
- Group: {composition}
- Budget: ₹{budget}
- Purpose: {purpose}
- Dates: {dates}

PROPOSAL:
{proposal_text}

Evaluate on these dimensions (1-5 scale):

1. PERSONALIZATION (1-5)
   - Does it address the specific customer needs?
   - Is the rationale clear and compelling?
   
2. FEASIBILITY (1-5)
   - Are the logistics realistic?
   - Are travel times between activities reasonable?
   
3. VALUE CLARITY (1-5)
   - Is pricing transparent?
   - Are inclusions/exclusions clear?
   
4. APPROPRIATENESS (1-5)
   - Is it suitable for the group composition?
   - Any activities that don't fit (e.g., strenuous for elderly)?
   
5. COMPLETENESS (1-5)
   - Are all necessary details included?
   - Would the customer have to ask follow-up questions?

Provide scores and brief justification for each.

OUTPUT FORMAT:
{{
    "personalization": {{"score": X, "reason": "..."}},
    "feasibility": {{"score": X, "reason": "..."}},
    "value_clarity": {{"score": X, "reason": "..."}},
    "appropriateness": {{"score": X, "reason": "..."}},
    "completeness": {{"score": X, "reason": "..."}},
    "overall": X,
    "critical_issues": ["..."]
}}
"""


def evaluate_proposal_with_llm(proposal: TravelerProposal, packet: CanonicalPacket) -> dict:
    """
    Use LLM to evaluate proposal quality.
    """
    prompt = PROPOSAL_QUALITY_PROMPT.format(
        destination=packet.facts.get("destination_city", {}).value,
        composition=packet.facts.get("traveler_composition", {}).value,
        budget=packet.facts.get("budget_range", {}).value,
        purpose=packet.facts.get("trip_purpose", {}).value,
        dates=packet.facts.get("travel_dates", {}).value,
        proposal_text=format_proposal_for_eval(proposal),
    )
    
    response = llm_client.complete(prompt, model="claude-3-5-sonnet")
    return json.loads(response)
```

### Calibration

Before trusting LLM judgments, calibrate against human evaluators:

```python
def calibrate_llm_judge():
    """
    Compare LLM scores to human scores to establish accuracy.
    """
    # Get 100 proposals
    proposals = load_test_proposals(n=100)
    
    # Human evaluation
    human_scores = human_evaluate(proposals)
    
    # LLM evaluation  
    llm_scores = [evaluate_proposal_with_llm(p) for p in proposals]
    
    # Calculate correlation
    correlation = pearson_correlation(human_scores, llm_scores)
    
    print(f"Human-LLM correlation: {correlation:.2f}")
    # Target: >0.8 for reliable automated evaluation
```

### Metrics

- **Accuracy vs humans**: Correlation coefficient
- **Consistency**: Same input → same score (within variance)
- **Bias check**: No systematic over/under-scoring for certain destinations/types

---

## Layer 3: Human Evaluation

### Expert Review Panel

**Who**: 3-5 experienced travel agents (not involved in development)

**What they evaluate**:
- Would you send this to a customer?
- What's missing?
- What would you change?
- Would this convert?

### Evaluation Rubric

```yaml
rubric:
  send_immediately:
    description: "Ready to send without changes"
    criteria:
      - All customer constraints addressed
      - Pricing clear and accurate
      - No obvious errors
    scale: yes/no

  minor_changes:
    description: "Minor edits needed"
    criteria:
      - 1-2 small tweaks (wording, formatting)
      - No structural issues
    scale: count_of_changes

  major_revision:
    description: "Significant rework needed"
    criteria:
      - Missing key components
      - Poor fit for customer
      - Pricing issues
    scale: severity (1-3)

  reject:
    description: "Not usable"
    criteria:
      - Safety issues
      - Major errors
      - Completely wrong destination/activities
    requires: detailed_feedback
```

### Blind Comparison

```python
def run_blind_comparison():
    """
    Human agents evaluate proposals without knowing source.
    """
    scenarios = load_test_scenarios(n=50)
    
    proposals = {
        "system_v1": [generate_v1(s) for s in scenarios],
        "system_v2": [generate_v2(s) for s in scenarios],
        "human_baseline": [load_human_proposal(s) for s in scenarios],
    }
    
    # Shuffle and present blind
    for scenario in scenarios:
        present_proposals_blind(scenario, proposals)
    
    # Calculate win rates
    results = calculate_win_rates()
    # Target: system_v2 beats human_baseline on >40% of scenarios
```

### Metrics

- **Send rate**: % marked "send immediately"
- **Avg changes needed**: Lower is better
- **Win rate vs human**: % preferred over human-written
- **Inter-rater reliability**: Agreement between evaluators

---

## Layer 4: Business Outcomes

### The Ultimate Metric

Does it drive business results?

### Metrics to Track

| Metric | Definition | Target |
|--------|-----------|--------|
| **Quote-to-Booking Rate** | % of proposals that convert | >30% |
| **Time to Quote** | Hours from request to proposal | <2 hours |
| **Revision Rate** | % of proposals requiring changes | <20% |
| **Customer Satisfaction** | Post-trip NPS | >50 |
| **Margin Preservation** | Average margin % | >12% |
| **Agent Efficiency** | Proposals per agent per day | >5 |

### A/B Testing Framework

```python
# Production A/B test
def route_request(request):
    """
    Route to system or human based on experiment bucket.
    """
    if request.agent_id in EXPERIMENT_AGENTS:
        if random.random() < 0.5:
            return generate_with_system(request)  # Test group
        else:
            return route_to_human(request)  # Control group
    else:
        return route_to_human(request)  # Not in experiment


# Metrics collection
@track_metrics
async def generate_proposal(request):
    proposal = await system.generate(request)
    
    # Log for analysis
    analytics.log({
        "request_id": request.id,
        "method": "system",
        "generation_time_ms": proposal.generation_time,
        "timestamp": now(),
    })
    
    return proposal


# Outcome tracking
def track_outcome(proposal_id, event):
    """
    Track what happened to the proposal.
    Events: sent, opened, revised, accepted, rejected, booked
    """
    analytics.outcome(proposal_id, event)
```

### Cohort Analysis

```sql
-- Compare system-generated vs human-generated proposals
SELECT 
    generation_method,
    COUNT(*) as total_proposals,
    AVG(CASE WHEN status = 'booked' THEN 1 ELSE 0 END) as conversion_rate,
    AVG(generation_time_hours) as avg_time_to_quote,
    AVG(margin_percent) as avg_margin,
    AVG(revision_count) as avg_revisions
FROM proposals
WHERE created_at > '2026-01-01'
GROUP BY generation_method;
```

---

## Safety Evaluation

### Harmful Recommendation Detection

```python
SAFETY_CHECKS = {
    "medical": {
        "check": "Does proposal include strenuous activities for travelers with medical constraints?",
        "severity": "high"
    },
    "visa": {
        "check": "Does proposal assume visa availability without verification?",
        "severity": "critical"
    },
    "budget": {
        "check": "Does total exceed stated budget by >20% without flagging?",
        "severity": "medium"
    },
    "unrealistic": {
        "check": "Are travel times between activities physically possible?",
        "severity": "medium"
    },
    "inappropriate": {
        "check": "Are activities suitable for group composition?",
        "severity": "high"
    }
}


def run_safety_check(proposal: TravelerProposal, packet: CanonicalPacket) -> List[SafetyIssue]:
    """
    Run all safety checks on a proposal.
    """
    issues = []
    
    # Medical check
    if "elderly" in packet.composition and has_strenuous_activities(proposal):
        issues.append(SafetyIssue(
            category="medical",
            severity="high",
            description="Strenuous activities included for elderly travelers",
            mitigation="Add mobility warnings or suggest alternatives"
        ))
    
    # Visa check
    if requires_visa(packet.destination) and not packet.visa_verified:
        issues.append(SafetyIssue(
            category="visa",
            severity="critical",
            description="Visa requirements not verified",
            mitigation="Add visa check requirement before booking"
        ))
    
    return issues
```

### Red Team Testing

```python
def red_team_test_cases():
    """
    Adversarial test cases designed to break the system.
    """
    return [
        # Medical edge case
        {
            "description": "90-year-old with heart condition, Everest base camp trek",
            "expected": "STOP_NEEDS_REVIEW or strong warning",
        },
        # Budget manipulation
        {
            "description": "Budget ₹50K, 2 weeks Europe",
            "expected": "Flag unrealistic, suggest alternatives",
        },
        # Contradictory constraints
        {
            "description": "Luxury honeymoon, budget ₹30K, Maldives",
            "expected": "BRANCH_OPTIONS or STOP_NEEDS_REVIEW",
        },
        # Safety issue
        {
            "description": "Family with toddler, skydiving activity",
            "expected": "Reject activity, suggest alternatives",
        },
    ]
```

---

## Continuous Evaluation Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CONTINUOUS EVALUATION PIPELINE                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐                │
│  │   PROPOSAL   │────▶│  STRUCTURAL  │────▶│   LLM-JUDGE  │                │
│  │   GENERATED  │     │  VALIDATION  │     │   EVALUATION │                │
│  └──────────────┘     └──────────────┘     └──────┬───────┘                │
│         │                                         │                         │
│         │                                         ▼                         │
│         │                              ┌──────────────┐                    │
│         │                              │   QUALITY    │                    │
│         │                              │   SCORE > 4  │                    │
│         │                              └──────┬───────┘                    │
│         │                                     │                            │
│         │                        NO ┌────────┴────────┐ YES                │
│         │                           ▼                 ▼                     │
│         │                  ┌──────────────┐   ┌──────────────┐             │
│         │                  │  HUMAN       │   │  AUTO-       │             │
│         │                  │  REVIEW      │   │  APPROVED    │             │
│         │                  └──────┬───────┘   └──────────────┘             │
│         │                         │                                       │
│         │                         ▼                                       │
│         │                ┌──────────────┐                                │
│         └───────────────▶│  FEEDBACK    │                                │
│                          │  LOOP        │                                │
│                          └──────────────┘                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Feedback Integration

```python
def integrate_feedback(proposal_id: str, feedback: dict):
    """
    Incorporate outcome feedback into evaluation dataset.
    """
    # Load original proposal
    proposal = db.get_proposal(proposal_id)
    
    # Create training example
    example = {
        "input": proposal.request,
        "output": proposal,
        "feedback": feedback,
        "label": "good" if feedback["booked"] else "needs_improvement"
    }
    
    # Add to evaluation dataset
    evaluation_dataset.add(example)
    
    # Trigger re-evaluation if dataset size crosses threshold
    if len(evaluation_dataset) % 100 == 0:
        trigger_model_evaluation()
```

---

## Evaluation Dashboard

### Key Metrics to Display

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                        EVALUATION DASHBOARD                                  │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  WEEKLY SUMMARY                    │  QUALITY METRICS                        │
│  ─────────────                     │  ───────────────                        │
│  Proposals generated: 127          │  Avg LLM Quality Score: 4.2/5           │
│  Human review needed: 23 (18%)     │  Send immediately: 68%                  │
│  Auto-approved: 104 (82%)          │  Minor changes: 22%                     │
│                                    │  Major revision: 8%                     │
│                                    │  Rejected: 2%                           │
│  BUSINESS OUTCOMES                 │                                         │
│  ─────────────────                 │  SAFETY METRICS                         │
│  Conversion rate: 34% (↑3%)        │  ─────────────                          │
│  Avg time to quote: 1.4 hrs (↓2hr) │  Safety issues caught: 12               │
│  Revision rate: 15% (↓5%)          │  Critical: 0                            │
│  Customer NPS: 52 (↑4)             │  Escalated to human: 3                  │
│                                    │                                         │
│  COMPARISON (System vs Human)      │  TRENDING                               │
│  ───────────────────────────       │  ─────────                              │
│  Conversion: 34% vs 31% (win)      │  ⚠️  Vietnam proposals scoring low       │
│  Margin: 13.2% vs 12.1% (win)      │  ✅ Family packages improving            │
│  Time: 1.4h vs 4.2h (win)          │  📈 Repeat customer conversion up        │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Implementation Priority

### Phase 1: Structural Validation (Week 1)
- Unit tests for all output types
- Property-based testing for constraints
- Schema validation

### Phase 2: LLM-as-Judge (Week 2-3)
- Build evaluation prompts
- Calibrate against human judgments
- Integrate into CI/CD

### Phase 3: Human Evaluation (Week 4)
- Recruit expert panel
- Define rubric
- Run baseline evaluation

### Phase 4: Production Monitoring (Ongoing)
- A/B testing framework
- Outcome tracking
- Continuous feedback loop

---

## Success Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| Structural pass rate | >99% | Automated tests |
| LLM-human correlation | >0.8 | Calibration study |
| Human "send immediately" | >60% | Expert review |
| Conversion rate | >30% | Production tracking |
| Safety incidents | 0 | Manual review |
| Time to quote | <2 hours | Production tracking |

---

*This is a specification for building the evaluation framework.*
