# LLM Decision Layer Migration Guide

**Date**: 2026-04-16
**Purpose**: Bridge the gap between existing spine skeleton and multi-agent vision

---

## Part 1: Current State vs Vision

### What You Built (Skeleton ✅)

```
Input Envelopes
      ↓
[ExtractionPipeline] → CanonicalPacket (provenance, authority, evidence)
      ↓
[validate_packet] → ValidationReport (errors, warnings)
      ↓
[run_gap_and_decision] → DecisionResult (RULE-BASED STUBS)
      ↓
[build_session_strategy] → SessionStrategy (RULE-BASED TEMPLATES)
      ↓
[build_traveler_safe_bundle] → PromptBundle (STRING TEMPLATES)
```

**Status**: Production-grade data structures, zero LLM intelligence.

### What You Designed (Agent Map 📋)

20+ specialized agents across 7 layers:
- **Lead & Discovery**: Client Intake, Traveler Profiling, Clarification
- **Feasibility**: Feasibility, Budget Allocation, Policy/Logistics
- **Research**: Flight Strategy, Stay Selection, Activities, Food, Mobility
- **Synthesis**: Trade-off/Ranking, Personalization/Tone, Document Pack
- **Booking**: Booking Readiness, Vendor Coordination, Price Watch
- **In-Trip**: Concierge, Disruption Recovery
- **Post-Trip**: Feedback/Memory, CRM/Upsell

**Status**: Well-designed architecture, zero implementation.

### The Gap

| Component | Current | Should Be |
|-----------|---------|-----------|
| `run_gap_and_decision` | Rule-based if/else | LLM-powered reasoning |
| Risk flags | Hardcoded patterns | Agent: `FeasibilityAgent` |
| Strategy generation | String templates | Agent: `StrategyComposerAgent` |
| Follow-up questions | Template-based | Agent: `ClarificationAgent` |
| Budget breakdown | Table lookup | Agent: `BudgetAllocationAgent` |

---

## Part 2: Where LLMs Should Replace Rules

### Current Decision Logic (Rule-Based)

**File**: `src/intake/decision.py:1623-1680`

```python
def run_gap_and_decision(packet, feasibility_table=None):
    # 1. Check MVB blockers (rule-based)
    hard_blockers = _evaluate_mvb_blockers(packet, stage)

    # 2. Risk flags (hardcoded patterns)
    risk_flags = generate_risk_flags(packet, stage)

    # 3. Commercial scoring (magic number thresholds)
    commercial_decision = _make_commercial_decision(lifecycle)

    # 4. Return result
    return DecisionResult(...)
```

### Target Decision Logic (LLM-Powered)

```python
def run_gap_and_decision(packet, feasibility_table=None):
    # 1. Router: Decide which agents to invoke
    agent_plan = DecisionRouter.route(packet)

    # 2. Specialists: Each agent handles its domain
    results = {}
    if agent_plan["needs_feasibility"]:
        results["feasibility"] = FeasibilityAgent.evaluate(packet)
    if agent_plan["needs_risk_analysis"]:
        results["risks"] = RiskAnalysisAgent.identify(packet)
    if agent_plan["needs_commercial_scoring"]:
        results["commercial"] = CommercialScoringAgent.score(packet)

    # 3. Synthesizer: Combine agent outputs
    decision = DecisionSynthesizer.combine(results, packet)

    return decision
```

---

## Part 3: Agent Implementation Priority

### Phase 1: Decision Core (P0 - Unblock Everything)

**1. DecisionRouterAgent**
- **Purpose**: Analyze packet state, determine which specialists to call
- **Input**: CanonicalPacket (facts, ambiguities, contradictions)
- **Output**: List of agents to invoke, priority order
- **LLM Task**: Classification + reasoning about what's missing
```python
class DecisionRouterAgent:
    prompt = """
    You are a decision router for a travel agency intake system.
    Analyze this traveler packet and determine:

    1. What critical information is missing?
    2. What contradictions need resolution?
    3. What specialist agents should be invoked?

    Respond in JSON:
    {
        "decision_state": "ASK_FOLLOWUP" | "PROCEED_INTERNAL_DRAFT" | ...,
        "required_agents": ["feasibility", "risk_analysis", ...],
        "blocking_gaps": ["destination_candidates", "budget_min", ...],
        "priority_order": [...]
    }
    """
```

**2. FeasibilityAgent**
- **Purpose**: Evaluate if trip requirements are realistic
- **Current**: Hardcoded destination cost table
- **LLM Task**: Reason about timing, pacing, destination fit
```python
class FeasibilityAgent:
    prompt = """
    You are a travel feasibility expert.
    Given:
    - Destination: {destination}
    - Duration: {duration} days
    - Party: {party_composition}
    - Travel dates: {dates}

    Evaluate:
    1. Is the duration sufficient for this destination?
    2. Any pacing issues with this composition?
    3. Seasonal concerns?
    4. Realistic budget range needed?

    Return structured assessment.
    """
```

**3. ClarificationAgent**
- **Purpose**: Generate contextual follow-up questions
- **Current**: Template-based questions
- **LLM Task**: Understand context, ask natural questions
```python
class ClarificationAgent:
    prompt = """
    You need to clarify missing information from a traveler.

    Context so far: {known_facts}
    Missing: {gaps}
    Traveler bracket: {traveler_type}

    Generate 2-3 follow-up questions that:
    1. Feel natural and conversational
    2. Collect exactly the missing information
    3. Match the tone to the traveler type

    Return questions with priority and field mapping.
    """
```

### Phase 2: Domain Intelligence (P1 - Product Value)

**4. RiskAnalysisAgent**
- **Purpose**: Identify trip-specific risks (beyond hardcoded patterns)
- **Current**: 5 hardcoded "risky destinations" for elderly
- **LLM Task**: Reason about destination + composition fit
```python
class RiskAnalysisAgent:
    prompt = """
    Analyze this trip for potential issues:

    Destination: {destination}
    Party: {composition} (ages, mobility considerations)
    Dates: {dates}
    Budget: {budget}

    Identify risks:
    1. Mobility/accessibility concerns
    2. Document/visa issues
    3. Budget realism
    4. Pacing problems
    5. Age-inappropriate activities

    For each risk: severity, mitigation, whether it's a blocker.
    """
```

**5. BudgetAllocationAgent**
- **Purpose**: Smart budget breakdown
- **Current**: Fixed bucket ranges per destination
- **LLM Task**: Allocate based on traveler preferences + destination economics
```python
class BudgetAllocationAgent:
    prompt = """
    Allocate this budget across cost buckets:

    Total: {budget}
    Destination: {destination} (cost structure: {economics})
    Traveler priorities: {preferences}
    Party: {composition}

    Provide ranges for:
    - Flights
    - Stay (hotel category based on preferences)
    - Food (dining style)
    - Activities
    - Local transport
    - Buffer

    Explain your reasoning.
    """
```

**6. TravelerTypingAgent**
- **Purpose**: Classify traveler into useful segments
- **LLM Task**: Analyze preferences to infer type
```python
class TravelerTypingAgent:
    prompt = """
    Based on these trip parameters, classify the traveler:

    {all_facts_and_preferences}

    Determine:
    1. Primary motivation (relaxation, adventure, shopping, culture)
    2. Pace preference (packed, balanced, relaxed)
    3. Budget sensitivity (budget-conscious, flexible, luxury)
    4. Travel style (structured, spontaneous, mixed)

    This affects ALL downstream recommendations.
    """
```

### Phase 3: Content Generation (P2 - Polish)

**7. StrategyComposerAgent**
- **Purpose**: Build session strategy (goal, tone, sequence)
- **Current**: String templates based on decision state
- **LLM Task**: Synthesize strategy from all available context

**8. ToneAdapterAgent**
- **Purpose**: Adapt message tone to traveler type
- **LLM Task**: Rewrite facts in appropriate voice

---

## Part 4: Orchestration Patterns

### Pattern A: Router → Specialist → Synthesizer

**Best for**: Decision layer, feasibility analysis

```python
class AgentOrchestrator:
    def execute(self, packet: CanonicalPacket) -> DecisionResult:
        # 1. Router decides what to do
        router_output = DecisionRouterAgent.run(packet)

        # 2. Invoke specialists in parallel where possible
        specialist_results = {}
        for agent_name in router_output["required_agents"]:
            agent = self.get_agent(agent_name)
            specialist_results[agent_name] = agent.run(packet)

        # 3. Synthesize final decision
        decision = DecisionSynthesizer.synthesize(
            router_output=router_output,
            specialist_results=specialist_results,
            packet=packet
        )

        return decision
```

### Pattern B: Debate / Consensus

**Best for**: Complex trade-offs, budget allocation

```python
class DebateOrchestrator:
    def execute(self, packet: CanonicalPacket) -> DecisionResult:
        # Each agent proposes independently
        proposals = {
            "budget": BudgetAgent.propose(packet),
            "experience": ExperienceAgent.propose(packet),
            "logistics": LogisticsAgent.propose(packet)
        }

        # Agents critique each other's proposals
        critiques = {}
        for role, proposal in proposals.items():
            other_roles = [r for r in proposals if r != role]
            critiques[role] = self.get_critiques(proposal, other_roles)

        # Final synthesizer makes call
        return self.synthesize_from_debate(proposals, critiques)
```

### Pattern C: Verifier Loop

**Best for**: Safety-critical decisions, compliance

```python
class VerifierOrchestrator:
    def execute(self, packet: CanonicalPacket) -> DecisionResult:
        max_iterations = 3

        for i in range(max_iterations):
            # Generate decision
            decision = PrimaryAgent.run(packet)

            # Verify
            verification = VerifierAgent.verify(decision, packet)

            if verification["passed"]:
                return decision

            # Refine with verification feedback
            packet = packet.with_feedback(verification["issues"])

        # Failed verification - escalate
        return self.escalate(packet)
```

---

## Part 5: LLM Integration Architecture

### Option A: Direct API Calls (Simple, Start Here)

```python
# src/agents/base.py
import anthropic

class BaseAgent:
    def __init__(self, model="claude-3-5-sonnet-20241022"):
        self.client = anthropic.Anthropic()
        self.model = model

    def run(self, packet: CanonicalPacket) -> Dict[str, Any]:
        prompt = self.build_prompt(packet)
        response = self.client.messages.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,  # Lower for consistent decisions
            max_tokens=2000
        )
        return self.parse_response(response.content)
```

### Option B: LangGraph (Recommended for Multi-Agent)

```python
# src/agents/graph.py
from langgraph.graph import StateGraph
from typing import TypedDict

class AgentState(TypedDict):
    packet: CanonicalPacket
    router_output: Dict
    specialist_results: Dict
    final_decision: DecisionResult

def build_decision_graph():
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("router", decision_router_node)
    graph.add_node("feasibility", feasibility_agent_node)
    graph.add_node("risk_analysis", risk_analysis_agent_node)
    graph.add_node("synthesizer", decision_synthesizer_node)

    # Add edges
    graph.set_entry_point("router")
    graph.add_conditional_edges(
        "router",
        should_route_to_feasibility,
        {"feasibility": "feasibility", "skip": "risk_analysis"}
    )
    graph.add_edge("feasibility", "risk_analysis")
    graph.add_edge("risk_analysis", "synthesizer")
    graph.set_finish_point("synthesizer")

    return graph.compile()
```

### Option C: Framework-Agnostic (If you want control)

```python
# src/agents/registry.py
class AgentRegistry:
    _agents = {}

    @classmethod
    def register(cls, name: str, agent_class):
        cls._agents[name] = agent_class

    @classmethod
    def get(cls, name: str) -> BaseAgent:
        return cls._agents[name]()

# Usage
AgentRegistry.register("feasibility", FeasibilityAgent)
AgentRegistry.register("risk_analysis", RiskAnalysisAgent)
```

---

## Part 6: Migration Path

### Step 1: Add LLM Infrastructure (1-2 days)

1. Create `src/agents/` directory
2. Build `BaseAgent` with Anthropic/OpenAI integration
3. Add prompt templates
4. Create agent registry

### Step 2: Replace One Decision Function (3-5 days)

**Target**: `run_gap_and_decision()` in `src/intake/decision.py`

**Approach**:
1. Keep existing function as fallback
2. Add `run_gap_and_decision_llm()` with new flow
3. Feature flag to switch between them
4. A/B test results

```python
# Feature flag
USE_LLM_DECISION = os.getenv("USE_LLM_DECISION", "false") == "true"

def run_gap_and_decision(packet, ...):
    if USE_LLM_DECISION:
        return run_gap_and_decision_llm(packet, ...)
    return run_gap_and_decision_legacy(packet, ...)
```

### Step 3: Build Core Agents (1-2 weeks)

**Priority order**:
1. `DecisionRouterAgent` - unlocks everything else
2. `FeasibilityAgent` - replaces hardcoded tables
3. `ClarificationAgent` - better user experience
4. `RiskAnalysisAgent` - catches issues rules miss

### Step 4: Gradual Rollout

1. Run agents in shadow mode (log but don't use results)
2. Compare agent vs rule outputs on same packets
3. Measure: correctness, consistency, edge cases
4. Gradually shift traffic to LLM path

---

## Part 7: Prompt Engineering Guidelines

### Structure Prompts for Decisions

```markdown
# Role
You are a {role} for a boutique travel agency.

# Context
{structured_context}

# Task
{specific_task}

# Input Data
{packet_data}

# Constraints
- Only use provided facts
- Flag when information is insufficient
- Consider agency constraints (margin, preferred suppliers)

# Output Format
{json_schema}

# Examples
{few_shot_examples}
```

### Use Chain-of-Thought for Complex Reasoning

```markdown
Think step by step:
1. What information do I have?
2. What am I being asked to decide?
3. What rules/principles apply?
4. What's my reasoning?
5. What's my final answer?
```

### Validate Structured Outputs

```python
from pydantic import BaseModel, Field

class DecisionOutput(BaseModel):
    decision_state: Literal["ASK_FOLLOWUP", "PROCEED_INTERNAL_DRAFT", ...]
    confidence: float = Field(ge=0, le=1)
    blockers: list[str]
    follow_up_questions: list[dict]

# Use for validation
response = agent.run(packet)
parsed = DecisionOutput.model_validate_json(response)
```

---

## Part 8: Evaluation & Testing

### Test Framework for Agents

```python
# tests/agents/test_decision_agents.py
class TestDecisionAgents:
    def test_feasibility_agent(self):
        packet = load_test_fixture("family_with_toddler_maldives.json")
        result = FeasibilityAgent.run(packet)

        assert result["is_feasible"] == False
        assert "duration_too_short" in result["flags"]

    def test_router_agent(self):
        # Test various packet states
        for fixture in ["complete", "missing_budget", "contradiction"]:
            packet = load_test_fixture(f"{fixture}.json")
            result = DecisionRouterAgent.run(packet)
            # Assert routing decisions
```

### Metrics to Track

| Metric | Why | Target |
|--------|-----|--------|
| Decision accuracy | Is the LLM making right calls? | >90% |
| Consistency | Same input → same output? | >95% |
| Edge case handling | Weird inputs don't break it | Graceful degradation |
| Latency | Can we use this in real-time? | <5s p95 |
| Cost | Per-decision cost | <₹5 |

---

## Part 9: Quick Start Decision

### Question: Which LLM Provider?

| Option | Pros | Cons | Recommendation |
|--------|------|------|----------------|
| **Claude (Anthropic)** | Strong reasoning, long context | Higher cost | **Start here** |
| **GPT-4o (OpenAI)** | Faster, cheaper | Less structured output | If cost is concern |
| **Haiku** | Very fast, cheap | Weaker reasoning | For simple classification |

### Question: Build or Use Framework?

| Option | Pros | Cons | Recommendation |
|--------|------|------|----------------|
| **LangGraph** | Battle-tested, great tooling | Learning curve | **If you want full multi-agent** |
| **Direct API** | Full control, simple | Manual orchestration | **Start here, migrate later** |
| **Custom framework** | Tailored to needs | Maintenance burden | Only if you have unique needs |

---

## Summary: Your Path Forward

```
Current: Rule-based stubs in run_gap_and_decision()
         ↓
Step 1: Add BaseAgent + Anthropic integration
         ↓
Step 2: Build DecisionRouterAgent (replace rule-based routing)
         ↓
Step 3: Build 3 core agents (Feasibility, Risk, Clarification)
         ↓
Step 4: Shadow mode testing vs rule-based
         ↓
Step 5: Gradual migration, measure improvements
         ↓
Future: Full multi-agent graph with 20+ specialized agents
```

**The key insight**: You don't need to rebuild your spine. You need to **inject LLM intelligence at decision points** while keeping the excellent data structures you built.

Start with ONE agent replacement, prove it works, then expand.
