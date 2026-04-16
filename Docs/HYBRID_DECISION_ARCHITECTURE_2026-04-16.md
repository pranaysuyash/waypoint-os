# Hybrid Decision Architecture: Rules + LLM + Cache

**Date**: 2026-04-16
**Goal**: Cost-optimized decision system that compiles intelligence over time

---

## Core Philosophy

```
┌─────────────────────────────────────────────────────────────┐
│  Decision Request                                            │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │  Rule Cache Lookup    │
              │  (JSON decision DB)   │
              └───────────────────────┘
                          │
              ┌───────────┴───────────┐
              │                       │
         ▼ YES                  ▼ NO (Cache Miss)
    ┌─────────┐          ┌──────────────────┐
    │ Return  │          │ Rule Engine      │
    │ Cached  │          │ (Deterministic)  │    │
    │ Decision│          └──────────────────┘
    └─────────┘                    │
                            ┌───────┴───────┐
                            │               │
                       ▼ SOLVED          ▼ NOVEL
                  ┌──────────┐      ┌─────────────┐
                  │ Return   │      │ LLM Agent   │
                  │ Rule     │      │ (Gemini/    │
                  │ Decision │      │  OpenAI/    │
                  └──────────┘      │  Local)     │
                                    └─────────────┘
                                          │
                                    ┌─────┴─────┐
                                    │           │
                                ▼ SUCCESS   ▼ FAIL
                            ┌──────────┐  ┌────────┐
                            │ Cache    │  │ Fallback│
                            │ Decision │  │ to      │
                            │ for      │  │ Safe    │
                            │ Reuse    │  │ Default │
                            └──────────┘  └────────┘
```

---

## Part 1: Decision Classification

### What CAN Be Rules (No LLM Needed)

| Category | Examples | Decision Logic |
|----------|----------|----------------|
| **Data Validation** | Passport expiry, visa requirements | Date arithmetic, lookup tables |
| **Basic Feasibility** | "Europe in 5 days" | Duration thresholds per destination |
| **Budget Sanity** | ₹50k for Europe for 4 people | Cost per person per day tables |
| **Document Checks** | Missing passport info | Required field lists |
| **Age Thresholds** | Toddler activities | Age < activity_min_age |
| **Season Rules** | Monsoon season = avoid Goa | Calendar + destination season map |

### What NEEDS LLM (Novel/Complex)

| Category | Examples | Why LLM Needed |
|----------|----------|----------------|
| **Ambiguity Resolution** | "We want somewhere with beaches but not too touristy" | Requires understanding nuance |
| **Contradiction Detection** | "Luxury on a backpacker budget" | Requires inference of intent |
| **Contextual Trade-offs** | "We want to see everything but move slowly" | Requires understanding impossibility |
| **Preference Inference** | Reading between the lines of vague requests | Requires natural language understanding |
| **Complex Composition** | Multi-gen family with conflicting needs | Requires balancing priorities |

---

## Part 2: The Decision Cache (Core Innovation)

### Cache Schema

```python
# src/decision/cache_schema.py
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional
import hashlib

@dataclass
class CachedDecision:
    """A compiled decision that can be reused without LLM."""
    
    # Cache key (hash of inputs)
    cache_key: str
    
    # What was asked
    decision_type: str  # "feasibility", "risk_analysis", "clarification"
    input_hash: str
    
    # The decision (what rule engine would return)
    decision: Dict[str, Any]
    confidence: float
    
    # Provenance
    source: str  # "rule_engine", "llm_compiled", "human_verified"
    llm_model_used: Optional[str]  # If from LLM, which model?
    created_at: datetime
    last_used_at: datetime
    use_count: int
    
    # Learning metadata
    success_rate: float = 1.0  # Updated based on user feedback
    feedback_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "cache_key": self.cache_key,
            "decision_type": self.decision_type,
            "decision": self.decision,
            "confidence": self.confidence,
            "source": self.source,
            "use_count": self.use_count,
            "success_rate": self.success_rate,
            "last_used_at": self.last_used_at.isoformat(),
        }
```

### Cache Key Generation

```python
# src/decision/cache_key.py
def generate_cache_key(
    decision_type: str,
    packet: CanonicalPacket,
    context: Dict[str, Any] = None,
) -> str:
    """
    Generate a deterministic cache key from inputs.
    
    Only include fields that actually affect the decision.
    """
    # Normalize packet to decision-relevant fields
    relevant_fields = _get_relevant_fields(decision_type, packet)
    
    # Sort and serialize for stable hashing
    normalized = json.dumps(relevant_fields, sort_keys=True, default=str)
    
    # Add context if provided
    if context:
        normalized += json.dumps(context, sort_keys=True, default=str)
    
    # Hash for compact key
    return hashlib.sha256(normalized.encode()).hexdigest()[:32]


def _get_relevant_fields(decision_type: str, packet: CanonicalPacket) -> Dict:
    """Extract only fields that matter for this decision type."""
    
    if decision_type == "elderly_mobility_risk":
        return {
            "destination": packet.facts.get("destination_candidates"),
            "has_elderly": _has_composition_member(packet, "elderly"),
            "elderly_count": _get_composition_count(packet, "elderly"),
        }
    
    elif decision_type == "toddler_pacing_risk":
        return {
            "destination": packet.facts.get("destination_candidates"),
            "has_toddler": _has_composition_member(packet, "toddler"),
            "toddler_ages": packet.facts.get("child_ages"),
            "duration_days": _get_trip_duration(packet),
        }
    
    elif decision_type == "budget_feasibility":
        return {
            "destination": packet.facts.get("destination_candidates"),
            "budget_min": packet.facts.get("budget_min"),
            "party_size": packet.facts.get("party_size"),
            "duration_days": _get_trip_duration(packet),
            "domestic_or_intl": packet.derived_signals.get("domestic_or_international"),
        }
    
    # ... more mappings
```

---

## Part 3: Hybrid Decision Engine

```python
# src/decision/hybrid_engine.py
from typing import Dict, Any, Optional
import json

class HybridDecisionEngine:
    """
    Cost-optimized decision engine:
    1. Check cache (compiled decisions)
    2. Try rule engine (deterministic)
    3. Fall back to LLM (novel cases)
    4. Compile LLM decisions for reuse
    """
    
    def __init__(
        self,
        cache_path: str = "data/decision_cache.json",
        llm_client: Any = None,  # Gemini, OpenAI, or local
        use_local_llm: bool = True,
    ):
        self.cache = self._load_cache(cache_path)
        self.llm_client = llm_client
        self.use_local_llm = use_local_llm
        self.stats = {
            "cache_hits": 0,
            "rule_hits": 0,
            "llm_calls": 0,
            "total_decisions": 0,
        }
    
    def decide(
        self,
        decision_type: str,
        packet: CanonicalPacket,
        context: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Make a decision using the hybrid approach.
        """
        self.stats["total_decisions"] += 1
        
        # STEP 1: Check cache
        cache_key = generate_cache_key(decision_type, packet, context)
        cached = self.cache.get(cache_key)
        
        if cached and self._is_cache_valid(cached):
            cached["last_used_at"] = datetime.now().isoformat()
            cached["use_count"] += 1
            self.stats["cache_hits"] += 1
            self._save_cache()  # Persist use count
            return {
                "decision": cached["decision"],
                "source": "cache",
                "confidence": cached["confidence"],
                "cache_hit": True,
            }
        
        # STEP 2: Try rule engine
        rule_result = self._try_rule_engine(decision_type, packet, context)
        
        if rule_result is not None:
            self.stats["rule_hits"] += 1
            # Cache the rule result for faster lookup next time
            self._cache_decision(
                cache_key=cache_key,
                decision_type=decision_type,
                decision=rule_result,
                source="rule_engine",
                confidence=1.0,
            )
            return {
                "decision": rule_result,
                "source": "rule_engine",
                "confidence": 1.0,
                "cache_hit": False,
            }
        
        # STEP 3: Fall back to LLM
        self.stats["llm_calls"] += 1
        llm_result = self._call_llm(decision_type, packet, context)
        
        # STEP 4: Compile the LLM decision for future reuse
        self._cache_decision(
            cache_key=cache_key,
            decision_type=decision_type,
            decision=llm_result["decision"],
            source="llm_compiled",
            confidence=llm_result.get("confidence", 0.7),
        )
        
        return {
            "decision": llm_result["decision"],
            "source": "llm",
            "confidence": llm_result.get("confidence", 0.7),
            "cache_hit": False,
        }
    
    def _try_rule_engine(
        self,
        decision_type: str,
        packet: CanonicalPacket,
        context: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Try to solve with rules. Return None if not possible."""
        
        if decision_type == "elderly_mobility_risk":
            return self._rule_elderly_mobility(packet)
        
        elif decision_type == "toddler_pacing_risk":
            return self._rule_toddler_pacing(packet)
        
        elif decision_type == "budget_feasibility":
            return self._rule_budget_feasibility(packet)
        
        elif decision_type == "visa_timeline_risk":
            return self._rule_visa_timeline(packet)
        
        # ... more rule functions
        
        return None  # No rule available, needs LLM
    
    def _rule_elderly_mobility(self, packet: CanonicalPacket) -> Optional[Dict]:
        """
        Rule-based elderly mobility risk assessment.
        Returns None if inputs are too complex for rules.
        """
        # Check if we have the required data
        dest_slot = packet.facts.get("destination_candidates")
        comp_slot = packet.facts.get("party_composition")
        
        if not dest_slot or not comp_slot:
            return None
        
        # Get elderly count
        composition = comp_slot.value
        if not isinstance(composition, dict):
            return None
        
        elderly_count = composition.get("elderly", 0)
        if elderly_count == 0:
            return {"risk": "none", "severity": "none"}
        
        # Rule-based destination risk assessment
        # (This is the part that becomes a lookup table, not hardcoded)
        destinations = dest_slot.value if isinstance(dest_slot.value, list) else [dest_slot.value]
        
        # Check against destination risk database
        risk_db = self._load_destination_risk_db()
        max_risk = "none"
        
        for dest in destinations:
            dest_risk = risk_db.get(dest, {}).get("elderly_mobility", "low")
            if self._risk_compare(dest_risk, max_risk) > 0:
                max_risk = dest_risk
        
        if max_risk == "none":
            return {"risk": "none", "severity": "none"}
        
        return {
            "risk": "elderly_mobility",
            "severity": max_risk,
            "destinations": destinations,
            "elderly_count": elderly_count,
        }
    
    def _load_destination_risk_db(self) -> Dict:
        """
        Load destination risk database.
        This is the COMPILED INTELLIGENCE from past LLM decisions.
        """
        # data/destination_risk_db.json
        # Gets populated over time from LLM decisions
        try:
            with open("data/destination_risk_db.json") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}  # Will be populated as LLM makes decisions
```

---

## Part 4: Local LLM Options

### Option A: Transformers.js (Browser-Based)

```javascript
// browser-based decision engine for frontend
import { pipeline, env } from '@transformers.js';

// Skip local models check, use CDN
env.allowLocalModels = false;
env.useBrowserCache = true;

// Load a small but capable model
const classifier = await pipeline(
    'text-classification',
    'Xenova/distilbert-base-uncased-finetuned-sst-2-english'
);

// Use for simple classification tasks
async function classifyTravelerInput(text) {
    const result = await classifier(text);
    return {
        sentiment: result[0].label,
        confidence: result[0].score,
    };
}

// For more complex decisions, use a local Q&A model
const qaModel = await pipeline(
    'question-answering',
    'Xenova/distilbert-base-cased-distilled-squad'
);

async function extractTripDetails(text) {
    const questions = [
        'What is the destination?',
        'What is the budget?',
        'How many people are traveling?',
        'What are the travel dates?'
    ];
    
    const results = {};
    for (const question of questions) {
        const answer = await qaModel(question, text);
        results[question] = answer.answer;
    }
    
    return results;
}
```

### Option B: Python + HuggingFace (Backend)

```python
# src/llm/local_llm.py
from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer
import torch

class LocalLLMClient:
    """
    Local LLM using HuggingFace models.
    Runs on CPU, no API costs.
    """
    
    def __init__(self, model_name: str = "microsoft/phi-3-mini-4k-instruct"):
        """
        Use a small but capable model:
        - phi-3-mini: 3.8B params, runs well on CPU
        - tinyllama: 1.1B params, very fast
        - gemma-2b: Fast for simple tasks
        """
        self.model_name = model_name
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        print(f"Loading model {model_name} on {self.device}...")
        
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float32 if self.device == "cpu" else torch.float16,
            device_map="auto"
        )
        
        # Create pipeline for text generation
        self.generator = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
            max_new_tokens=512,
            temperature=0.3,
            do_sample=False,
        )
    
    def decide(self, prompt: str, schema: Dict) -> Dict:
        """
        Generate a decision following the given schema.
        """
        # Add format instruction
        formatted_prompt = f"""
{prompt}

Respond in JSON format with this schema:
{json.dumps(schema, indent=2)}

JSON Response:
"""
        
        # Generate
        outputs = self.generator(
            formatted_prompt,
            max_new_tokens=512,
            return_full_text=False,
        )
        
        # Parse JSON from output
        response_text = outputs[0]["generated_text"]
        try:
            # Extract JSON from response
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            json_str = response_text[json_start:json_end]
            return json.loads(json_str)
        except:
            # Fallback: return raw response
            return {"raw_response": response_text}
```

### Option C: Gemini API (Cost-Effective)

```python
# src/llm/gemini_client.py
import google.generativeai as genai
from typing import Dict, Any
import os

class GeminiClient:
    """
    Google Gemini API client.
    Very cost-effective for production use.
    Free tier: 15 requests/minute
    Paid: ~$0.075/1M tokens (much cheaper than GPT-4)
    """
    
    def __init__(self, model: str = "gemini-1.5-flash"):
        """
        Use flash for speed/cost, pro for quality.
        - flash: Fast, cheap, good enough for most decisions
        - pro: Better reasoning for complex cases
        """
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)
    
    def decide(
        self,
        prompt: str,
        schema: Dict[str, Any],
        temperature: float = 0.3,
    ) -> Dict[str, Any]:
        """
        Generate a structured decision.
        """
        # Add schema instruction
        formatted_prompt = f"""
{prompt}

IMPORTANT: Respond ONLY with valid JSON matching this schema:
{json.dumps(schema, indent=2)}

Do not include any text outside the JSON.
"""
        
        # Generate
        response = self.model.generate_content(
            formatted_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=1024,
            )
        )
        
        # Parse response
        try:
            return json.loads(response.text)
        except json.JSONDecodeError:
            # Try to extract JSON
            import re
            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            
            # Fallback
            return {"error": "Could not parse LLM response", "raw": response.text}
```

### Option D: OpenAI (When Needed)

```python
# src/llm/openai_client.py
from openai import OpenAI
import os

class OpenAIClient:
    """
    OpenAI API client.
    Use gpt-4o-mini for cost-effective decisions.
    ~$0.15/1M input tokens, $0.60/1M output tokens
    """
    
    def __init__(self, model: str = "gpt-4o-mini"):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set")
        
        self.client = OpenAI(api_key=api_key)
        self.model = model
    
    def decide(
        self,
        prompt: str,
        schema: Dict[str, Any],
        temperature: float = 0.3,
    ) -> Dict[str, Any]:
        """
        Generate a structured decision using JSON mode.
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a travel planning decision engine. Always respond with valid JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            response_format={"type": "json_object"},
        )
        
        content = response.choices[0].message.content
        return json.loads(content)
```

---

## Part 5: Model Selection Strategy

### Decision Type → Model Mapping

| Decision Complexity | Use Model | Rationale |
|---------------------|-----------|-----------|
| **Simple classification** | Rule Engine | Deterministic, zero cost |
| **Ambiguity detection** | Local LLM (phi-3-mini) | Fast, runs locally |
| **Preference extraction** | Gemini Flash | Fast, cheap API |
| **Complex trade-offs** | Gemini Pro | Better reasoning |
| **Edge cases** | GPT-4o-mini | Highest quality |

### Cost Comparison (per 1M decisions)

| Approach | Cost (approx) | When to Use |
|----------|---------------|-------------|
| **Rule Engine** | $0 | Always first |
| **Cache Hit** | $0 | After first LLM |
| **Local LLM** | $0 (compute only) | Simple tasks |
| **Gemini Flash** | ~$0.10 | Standard API |
| **Gemini Pro** | ~$1.00 | Complex tasks |
| **GPT-4o-mini** | ~$0.50 | Backup API |

---

## Part 6: Implementation Steps

### Step 1: Create Decision Cache (Day 1)

```bash
mkdir -p data/decision_cache
touch data/decision_cache/elderly_mobility.json
touch data/decision_cache/toddler_pacing.json
touch data/decision_cache/budget_feasibility.json
```

### Step 2: Port Existing Rules (Day 1-2)

Extract current logic from `src/intake/decision.py` into rule functions:

```python
# src/decision/rules/elderly_mobility.py
def rule_elderly_mobility(packet: CanonicalPacket) -> Optional[Dict]:
    """
    Extracted from decision.py:1052-1058
    Now callable from hybrid engine.
    """
    risky_dests = {"Maldives", "Andaman", "Andamans", "Bhutan", "Nepal"}
    # ... existing logic
```

### Step 3: Add Local LLM Option (Day 2-3)

```bash
# Add to requirements.txt
transformers>=4.30.0
torch>=2.0.0
sentencepiece>=0.1.99
```

### Step 4: Add Gemini API (Day 3)

```bash
# .env
GEMINI_API_KEY=your_key_here

# Install
pip install google-generativeai
```

### Step 5: Build Hybrid Engine (Day 3-4)

Wire it all together in `src/decision/hybrid_engine.py`

### Step 6: Run in Shadow Mode (Day 4-5)

```python
# Run both rule and LLM, compare results
result_rule = engine._try_rule_engine(...)
result_llm = engine._call_llm(...)
log_comparison(result_rule, result_llm)
```

---

## Part 7: The Learning Loop

### From LLM Decision → Compiled Rule

```python
# src/decision/learning.py
class DecisionCompiler:
    """
    Compile successful LLM decisions into reusable rules.
    """
    
    def analyze_patterns(self, decisions: List[CachedDecision]) -> List[Dict]:
        """
        Find patterns in LLM decisions that can become rules.
        """
        patterns = []
        
        # Group by decision type
        by_type = groupby(decisions, key=lambda d: d.decision_type)
        
        for decision_type, type_decisions in by_type:
            # Find common input → output mappings
            common_mappings = self._find_common_patterns(type_decisions)
            
            for mapping in common_mappings:
                # If same inputs → same output 95%+ of the time, make it a rule
                if mapping["consistency"] > 0.95:
                    patterns.append({
                        "decision_type": decision_type,
                        "input_pattern": mapping["inputs"],
                        "output_decision": mapping["output"],
                        "confidence": mapping["consistency"],
                        "sample_size": mapping["count"],
                    })
        
        return patterns
    
    def suggest_rules(self, patterns: List[Dict]) -> str:
        """
        Generate rule code from patterns.
        """
        rule_code = []
        
        for pattern in patterns:
            rule_code.append(f"""
# Auto-generated rule from {pattern['sample_size']} LLM decisions
# Confidence: {pattern['confidence']}
def rule_{pattern['decision_type']}_pattern_{len(rule_code)}(packet):
    if packet.matches({pattern['input_pattern']}):
        return {pattern['output_decision']}
""")
        
        return "\n".join(rule_code)
```

---

## Part 8: Configuration

```yaml
# config/decision_engine.yaml
decision_engine:
  # Model selection
  primary_llm: "gemini-flash"
  fallback_llm: "gpt-4o-mini"
  enable_local_llm: true
  local_model: "microsoft/phi-3-mini-4k-instruct"
  
  # Cache settings
  cache_enabled: true
  cache_ttl_days: 30
  max_cache_size_mb: 100
  
  # Rule engine priority
  rules_first: true
  rule_confidence_threshold: 0.95
  
  # Learning
  auto_compile_patterns: true
  pattern_min_occurrences: 10
  pattern_consistency_threshold: 0.95
  
  # Cost controls
  max_llm_calls_per_minute: 10
  max_llm_cost_per_day_rs: 100
```

---

## Part 9: Monitoring & Metrics

```python
# src/decision/monitoring.py
@dataclass
class DecisionMetrics:
    """Track decision engine performance."""
    
    # Call breakdown
    total_decisions: int
    cache_hits: int
    rule_hits: int
    llm_calls: int
    
    # Quality metrics
    llm_success_rate: float  # User feedback
    rule_accuracy: float      # Verified against LLM
    
    # Cost tracking
    estimated_cost_rs: float
    
    # Learning progress
    rules_compiled_this_week: int
    cache_hit_rate_improvement: float
    
    @property
    def cost_per_decision(self) -> float:
        if self.total_decisions == 0:
            return 0
        return self.estimated_cost_rs / self.total_decisions
    
    @property
    def automation_rate(self) -> float:
        """What % of decisions are cache+rule (no LLM)."""
        if self.total_decisions == 0:
            return 0
        return (self.cache_hits + self.rule_hits) / self.total_decisions
```

---

## Part 10: Quick Start Checklist

- [ ] Create `data/decision_cache/` directory structure
- [ ] Add `GEMINI_API_KEY` to `.env`
- [ ] Install: `transformers`, `torch`, `google-generativeai`
- [ ] Create `src/decision/hybrid_engine.py`
- [ ] Port existing rules from `decision.py`
- [ ] Add cache key generation
- [ ] Implement `LocalLLMClient` (optional, can start with API)
- [ ] Implement `GeminiClient` (primary)
- [ ] Wire into `run_gap_and_decision()`
- [ ] Add shadow mode logging
- [ ] Run comparison tests
- [ ] Enable cache + rules, measure LLM reduction

---

## Summary

**Architecture**: Rules → Cache → LLM (in that order)

**Cost Optimization**:
1. Rules cost nothing → Use where possible
2. Cache hits cost nothing → Compile LLM decisions
3. Local LLM costs compute → Use for simple tasks
4. API calls cost money → Use only when necessary

**The Learning Loop**:
```
Day 1: 90% LLM calls (learning)
Day 30: 60% LLM calls (building cache)
Day 90: 30% LLM calls (rules compiled)
Day 180: 10% LLM calls (mostly edge cases)
```

You're not replacing LLMs — you're **compiling their intelligence** into rules.
