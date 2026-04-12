# Research: Prompt Versioning & Regression Protection

**Status**: 🔵 Specification — Infrastructure for Offline Loop  
**Topic ID**: 20  
**Parent**: [EXPLORATION_TOPICS.md](../EXPLORATION_TOPICS.md)  
**Last Updated**: 2026-04-09

---

## The Problem

The system relies on prompts for:
- NB01: Extraction prompts
- NB03: Session strategy prompts, tone guardrails
- Future NB04: Proposal generation prompts

**Without versioning**:
- "Improving" a prompt silently breaks 5 fixtures
- No way to A/B test prompt changes
- Can't rollback when a change hurts quality
- Autoresearch becomes chaos (mutate → score → ???)

**The principle**: *No live improvised prompting. Use a registry. Only keep changes that pass eval.*

---

## Requirements

### Functional Requirements

1. **Version Control**: Every prompt has a version hash
2. **Regression Testing**: Changing a prompt re-runs the fixture suite
3. **A/B Testing**: Can run two prompt versions side-by-side
4. **Rollback**: Can revert to previous prompt version instantly
5. **Audit Trail**: Know which prompt version generated which output

### Non-Functional Requirements

- **Determinism**: Same input + same prompt version = same output (within LLM variance)
- **Performance**: Prompt lookup < 10ms
- **Storage**: Git-friendly (text files, not database blobs)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        PROMPT REGISTRY ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  prompts/                                                                   │
│  ├── registry.yaml                    # Index of all prompts                │
│  ├── nb01/                            # Extraction prompts                  │
│  │   ├── extract_traveler_info/                                             │
│  │   │   ├── v1.0.0.yaml              # Stable version                      │
│  │   │   ├── v1.1.0.yaml              # Candidate version                   │
│  │   │   └── README.md                # Changelog, test results              │
│  │   └── extract_dates/                                                     │
│  ├── nb03/                            # Session strategy prompts            │
│  │   ├── ask_followup_template/                                             │
│  │   ├── branch_presentation/                                               │
│  │   └── tone_guardrails/                                                   │
│  └── shared/                          # Reusable components                 │
│      ├── travel_context/                                                    │
│      └── safety_reminders/                                                  │
│                                                                             │
│  tests/prompts/                       # Prompt-specific tests               │
│  ├── test_prompt_quality.py                                                 │
│  └── test_regression.py                                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Registry Schema

### registry.yaml

```yaml
# Prompt Registry
# This file is the source of truth for prompt versions

schema_version: "1.0"
last_updated: "2026-04-09"

prompts:
  # NB01: Extraction Prompts
  nb01.extract_traveler_info:
    current_version: "v1.0.0"
    description: "Extract traveler count, composition, and preferences from raw text"
    owner: "system"
    active_versions:
      - version: "v1.0.0"
        path: "nb01/extract_traveler_info/v1.0.0.yaml"
        status: "stable"
        fixture_pass_rate: 1.0
        deployed_at: "2026-04-01"
      - version: "v1.1.0"
        path: "nb01/extract_traveler_info/v1.1.0.yaml"
        status: "candidate"
        fixture_pass_rate: 0.97  # Lower than v1.0.0
        deployed_at: null

  nb01.extract_dates:
    current_version: "v1.0.0"
    description: "Extract travel dates and duration"
    active_versions:
      - version: "v1.0.0"
        path: "nb01/extract_dates/v1.0.0.yaml"
        status: "stable"
        fixture_pass_rate: 1.0

  # NB03: Session Strategy Prompts
  nb03.ask_followup_template:
    current_version: "v1.0.0"
    description: "Template for ASK_FOLLOWUP state messages"
    active_versions:
      - version: "v1.0.0"
        path: "nb03/ask_followup_template/v1.0.0.yaml"
        status: "stable"

  nb03.branch_presentation:
    current_version: "v1.0.0"
    description: "How to present BRANCH_OPTIONS to traveler"
    active_versions:
      - version: "v1.0.0"
        path: "nb03/branch_presentation/v1.0.0.yaml"
        status: "stable"

  nb03.tone_guardrails.cautious:
    current_version: "v1.0.0"
    description: "Tone instructions for confidence < 0.3"
    active_versions:
      - version: "v1.0.0"
        path: "nb03/tone_guardrails/cautious_v1.0.0.yaml"
        status: "stable"

# A/B Tests
experiments:
  - id: "exp_001"
    name: "More conversational ask_followup"
    prompt: "nb03.ask_followup_template"
    variants:
      - version: "v1.0.0"
        weight: 0.9
      - version: "v1.1.0"
        weight: 0.1
    start_date: "2026-04-10"
    end_date: "2026-04-17"
    success_metric: "response_rate"
```

---

## Prompt File Format

### v1.0.0.yaml

```yaml
# Prompt: nb01.extract_traveler_info v1.0.0
# Purpose: Extract traveler information from agency notes

metadata:
  version: "v1.0.0"
  created_at: "2026-04-01"
  created_by: "system"
  prompt_hash: "sha256:a1b2c3..."
  
  # Test results
  test_results:
    fixture_pass_rate: 1.0
    fixtures_tested: 31
    last_tested: "2026-04-09"
  
  # Changelog
  changelog: |
    v1.0.0 (2026-04-01)
    - Initial version
    - Passes all 31 fixtures

# The actual prompt
prompt:
  system: |
    You are a travel data extraction assistant.
    Extract traveler information from agency notes.
    
    Rules:
    - Only extract what is explicitly stated
    - Use null for unknown values
    - Note confidence level (0.0-1.0)
    - Preserve original phrasing in evidence
  
  user_template: |
    Extract from this agency note:
    
    ```
    {raw_input}
    ```
    
    Return JSON:
    {{
      "traveler_count": <number or null>,
      "traveler_composition": <string or null>,
      "confidence": <0.0-1.0>
    }}

# Few-shot examples (optional)
examples:
  - input: "Family of 4 from Bangalore"
    output:
      traveler_count: 4
      traveler_composition: "family"
      confidence: 0.95
  
  - input: "Big group, maybe 6-8 people"
    output:
      traveler_count: null
      traveler_composition: "big group"
      confidence: 0.4
      note: "ambiguous count"

# Constraints on output
output_schema:
  type: "object"
  required: ["traveler_count", "confidence"]
  properties:
    traveler_count:
      type: ["number", "null"]
    confidence:
      type: "number"
      minimum: 0.0
      maximum: 1.0
```

---

## Runtime API

```python
# prompts/registry.py

from typing import Optional, Dict, Any
import yaml
import hashlib
from dataclasses import dataclass

@dataclass
class PromptVersion:
    prompt_id: str
    version: str
    prompt_text: str
    metadata: Dict[str, Any]
    
    @property
    def hash(self) -> str:
        """Content hash for provenance tracking."""
        return hashlib.sha256(self.prompt_text.encode()).hexdigest()[:16]


class PromptRegistry:
    """
    Central registry for all prompts.
    """
    
    def __init__(self, registry_path: str = "prompts/registry.yaml"):
        self.registry_path = registry_path
        self._registry = self._load_registry()
        self._cache = {}  # version -> PromptVersion
    
    def get_prompt(
        self, 
        prompt_id: str, 
        version: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> PromptVersion:
        """
        Get a prompt by ID and version.
        
        If version is None, returns current_version.
        If A/B test is active for this prompt, selects variant based on context.
        """
        # Check for active experiment
        if version is None:
            version = self._select_version(prompt_id, context)
        
        cache_key = f"{prompt_id}:{version}"
        if cache_key not in self._cache:
            self._cache[cache_key] = self._load_prompt(prompt_id, version)
        
        return self._cache[cache_key]
    
    def _select_version(self, prompt_id: str, context: Optional[Dict]) -> str:
        """Select version based on registry and any active experiments."""
        # Check for active experiment
        for exp in self._registry.get("experiments", []):
            if exp["prompt"] == prompt_id:
                if self._is_experiment_active(exp):
                    return self._select_variant(exp, context)
        
        # Return current version
        return self._registry["prompts"][prompt_id]["current_version"]
    
    def list_versions(self, prompt_id: str) -> list:
        """List all versions of a prompt."""
        return self._registry["prompts"][prompt_id]["active_versions"]
    
    def deploy_version(self, prompt_id: str, version: str):
        """
        Set a version as current (after it passes all tests).
        """
        # Verify version exists
        versions = self.list_versions(prompt_id)
        if not any(v["version"] == version for v in versions):
            raise ValueError(f"Version {version} not found for {prompt_id}")
        
        # Update current version
        self._registry["prompts"][prompt_id]["current_version"] = version
        self._save_registry()
        
        # Invalidate cache
        self._cache = {}


# Usage in NB03
def build_ask_followup_prompts(decision, packet):
    """Build prompts using registry."""
    registry = PromptRegistry()
    
    # Get current version of ask_followup template
    prompt_version = registry.get_prompt("nb03.ask_followup_template")
    
    # Render with context
    prompt_text = prompt_version.prompt_text.format(
        questions=format_questions(decision.follow_up_questions),
        known_facts=format_facts(packet.facts),
    )
    
    # Log prompt version for provenance
    return PromptBundle(
        system_context=prompt_text,
        _prompt_version=prompt_version.version,
        _prompt_hash=prompt_version.hash,
        # ...
    )
```

---

## Regression Testing

### test_prompt_regression.py

```python
#!/usr/bin/env python3
"""
Regression tests for prompt changes.

Any change to a prompt must pass all fixtures.
"""

import pytest
from prompts.registry import PromptRegistry
from notebooks.nb04_eval_runner import run_fixture

def test_all_prompts_pass_fixtures():
    """
    For each prompt version marked 'stable', run all fixtures.
    """
    registry = PromptRegistry()
    
    for prompt_id, config in registry.list_prompts().items():
        for version_info in config["active_versions"]:
            if version_info["status"] != "stable":
                continue
            
            version = version_info["version"]
            pass_rate = version_info.get("fixture_pass_rate", 0)
            
            # Re-run fixtures
            actual_pass_rate = run_fixtures_with_prompt(prompt_id, version)
            
            assert actual_pass_rate >= 0.95, (
                f"Prompt {prompt_id}@{version} regressed: "
                f"{actual_pass_rate:.0%} pass rate (expected >95%)"
            )


def test_new_prompt_better_than_current():
    """
    A candidate version must beat current version to be promoted.
    """
    registry = PromptRegistry()
    
    for prompt_id, config in registry.list_prompts().items():
        current = config["current_version"]
        
        for version_info in config["active_versions"]:
            if version_info["status"] != "candidate":
                continue
            
            candidate = version_info["version"]
            
            # Must have been tested
            assert "fixture_pass_rate" in version_info, (
                f"Candidate {prompt_id}@{candidate} not tested"
            )
            
            # Must beat current (or match with other benefits)
            current_rate = get_version_rate(prompt_id, current)
            candidate_rate = version_info["fixture_pass_rate"]
            
            assert candidate_rate >= current_rate, (
                f"Candidate {candidate} ({candidate_rate:.0%}) not better "
                f"than current {current} ({current_rate:.0%})"
            )
```

---

## A/B Testing Protocol

### 1. Create Candidate Version

```bash
# Copy current version
cp prompts/nb03/ask_followup_template/v1.0.0.yaml \
   prompts/nb03/ask_followup_template/v1.1.0.yaml

# Edit v1.1.0.yaml with changes
# Update metadata.version
# Update metadata.changelog
```

### 2. Test Candidate

```python
# Run fixtures with candidate
python -m pytest tests/prompts/test_prompt_regression.py \
    -k "nb03.ask_followup_template" \
    --prompt-version=v1.1.0

# Check results
# If pass rate >= current version, proceed
```

### 3. Deploy as Experiment

```yaml
# Update registry.yaml
experiments:
  - id: "exp_001"
    name: "More conversational ask_followup"
    prompt: "nb03.ask_followup_template"
    variants:
      - version: "v1.0.0"
        weight: 0.9
      - version: "v1.1.0"
        weight: 0.1
    start_date: "2026-04-10"
    success_metric: "response_rate"
```

### 4. Measure and Decide

```python
# After experiment period
results = analyze_experiment("exp_001")

if results.variant_b_beats_a(significance=0.95):
    registry.deploy_version("nb03.ask_followup_template", "v1.1.0")
else:
    # Keep current, archive candidate
    registry.archive_version("nb03.ask_followup_template", "v1.1.0")
```

---

## Integration with NB03

```python
# notebooks/03_session_strategy.ipynb

class PromptBundle:
    """Now includes prompt version for audit."""
    system_context: str
    user_message: str
    # ...
    _prompt_version: str      # e.g., "nb03.ask_followup_template:v1.0.0"
    _prompt_hash: str         # Content hash


def build_ask_followup_prompts(decision, packet):
    registry = PromptRegistry()
    
    # Get prompt with A/B selection
    prompt = registry.get_prompt(
        "nb03.ask_followup_template",
        context={"packet_id": packet.packet_id}  # For consistent A/B assignment
    )
    
    # Render
    system_context = prompt.prompt_text.format(
        decision_state="ASK_FOLLOWUP",
        questions=decision.follow_up_questions,
        tone="cautious" if decision.confidence < 0.3 else "measured",
    )
    
    return PromptBundle(
        system_context=system_context,
        user_message=render_questions(decision.follow_up_questions),
        _prompt_version=f"nb03.ask_followup_template:{prompt.version}",
        _prompt_hash=prompt.hash,
        constraints=["Max 3 questions", "Constraint-first order"],
    )
```

---

## Success Criteria

| Criterion | Target | Measurement |
|-----------|--------|-------------|
| Prompt lookup latency | <10ms | Runtime benchmark |
| Regression test time | <2 min | CI pipeline |
| A/B experiment setup | <1 hour | Time to deploy experiment |
| Rollback time | <30 sec | Time to revert prompt |
| Version audit trail | 100% | All outputs tagged with prompt version |

---

## Implementation Checklist

- [ ] Create `prompts/` directory structure
- [ ] Implement `PromptRegistry` class
- [ ] Migrate existing NB03 prompts to registry
- [ ] Add regression test to CI
- [ ] Document A/B testing protocol
- [ ] Integrate version logging into SessionOutput

---

## Related Topics

- [EVALUATION_FRAMEWORK.md](EVALUATION_FRAMEWORK.md) — How to measure prompt quality
- [INTERNAL_DATA_INTEGRATION.md](INTERNAL_DATA_INTEGRATION.md) — Prompts vs internal data
- Notebook 03 contract — Where prompts are used

---

*This is infrastructure for the offline improvement loop.*
