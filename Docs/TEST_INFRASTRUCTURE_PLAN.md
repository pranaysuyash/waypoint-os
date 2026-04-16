# Test Infrastructure Improvement Plan: v0.2 API Migration and Enhancement

## Executive Summary

This plan addresses the test infrastructure gaps identified after migrating notebook tests (test_02_comprehensive.py, test_scenarios_realworld.py) to v0.2 API. The core issues are:

1. **Fixture files still use v0.1 field names** - packet_fixtures.py, raw_fixtures.py, test_scenarios.py use legacy names (destination_city, travel_dates, traveler_count, budget_range) instead of v0.2 canonical names (destination_candidates, date_window, party_size, budget_min)

2. **Notebook tests not formalized as pytest** - test_02_comprehensive.py and test_scenarios_realworld.py are standalone scripts, not integrated into the pytest test suite

3. **No API contract regression tests** - Changes to the v0.2 API (LEGACY_ALIASES, MVB_BY_STAGE, AuthorityLevel, DecisionResult, function signatures) are not validated by automated tests

4. **Missing test documentation** - tests/README.md doesn't exist to explain test organization, v0.2 changes, and how to run tests

---

## Detailed Implementation Plan

### Phase 1: Migrate Fixture Files to v0.2

#### 1.1 Migrate `data/fixtures/packet_fixtures.py`

**Current State Analysis:**
- Uses v0.1 field names: destination_city, travel_dates, traveler_count, budget_range, traveler_preferences
- Defines ~25 CanonicalPacket fixtures for policy-only testing
- Imported by `notebooks/04_eval_runner.ipynb`
- Uses local Slot/Packet definitions (not from src/)

**Required Changes:**

| v0.1 Field Name | v0.2 Canonical Name | Notes |
|----------------|---------------------|-------|
| destination_city | destination_candidates | Now always a list (even single destination) |
| travel_dates | date_window | Structured window, not freeform |
| traveler_count | party_size | Standardized naming |
| budget_range | budget_min | Use budget_min for numeric value |
| traveler_preferences | soft_preferences | Clearer semantic meaning |

**Migration Strategy:**
1. Update all packet fact field names to v0.2 canonical names
2. Update expected result assertions to use canonical names
3. Keep local Slot/Packet definitions (they're standalone fixtures)
4. Add LEGACY_ALIASES import for backward compatibility tests

**Key Fixtures to Update:**
- `ask_empty`: hard_blockers expect `destination_candidates, origin_city, date_window, party_size`
- `ask_missing_destination`: facts use `destination_candidates`
- `proceed_complete_discovery`: all facts use canonical names
- All contradiction fixtures: field names in contradictions dict

**Verification:**
```bash
# After migration, eval runner should pass
python notebooks/04_eval_runner.ipynb
```

#### 1.2 Migrate `data/fixtures/raw_fixtures.py`

**Current State Analysis:**
- Raw input fixtures for end-to-end testing
- Uses v0.1 field names in `expected.extracted_fields`
- 12 fixtures across categories: clean_happy_path, messy_under_specified, hybrid_conflict, contradiction_heavy, branch_worthy_ambiguity
- Imported by `notebooks/04_eval_runner.ipynb`

**Required Changes:**
Same field name mappings as packet_fixtures.py, but applied to:
- `extracted_fields` dict in each fixture
- `nb02_hard_blockers` expected values
- Field names in contradictions (where applicable)

**Verification:**
```bash
# Run eval runner mode 1 (e2e)
python notebooks/04_eval_runner.ipynb
```

#### 1.3 Migrate `data/fixtures/test_scenarios.py`

**Current State Analysis:**
- 30 test scenario factories for comprehensive testing
- Uses v0.1 field names throughout
- Defines local CanonicalPacket/Slot/EvidenceRef classes
- Imported by `data/fixtures/run_all_tests.py`

**Required Changes:**
1. Update all scenario methods to use v0.2 field names
2. Update `get_expected_results()` to reference canonical field names
3. Update hard_blockers expected lists

**Specific Scenarios:**
- Category A (Basic): `basic_complete_discovery`, `basic_soft_only`
- Category B (Contradictions): All 5 scenarios
- Category D (Stage Progression): All 4 scenarios
- Category E (Edge Cases): All 5 scenarios
- Category F (Complex Hybrid): All 5 scenarios

**Verification:**
```bash
python data/fixtures/run_all_tests.py
```

---

### Phase 2: Formalize Notebook Tests as Pytest

#### 2.1 Convert `notebooks/test_02_comprehensive.py` to `tests/test_comprehensive_v02.py`

**Current State:**
- Standalone script with custom test framework
- Loads notebook code via `load_notebook_namespace()`
- 15 test dimensions covering blocker resolution, contradictions, authority, decision states

**Conversion Strategy:**
1. Create new pytest module at `tests/test_comprehensive_v02.py`
2. Keep the `load_notebook_namespace()` approach to test actual notebook code
3. Convert custom `test()` function to pytest test functions
4. Use pytest fixtures for shared setup
5. Maintain section headers with `# ===========================================================================`

**Test Structure:**
```python
"""
Comprehensive v0.2 Decision Engine Tests

Run: pytest tests/test_comprehensive_v02.py -v
"""

import pytest
from intake.packet_models import CanonicalPacket, Slot, AuthorityLevel
from intake.decision import run_gap_and_decision, MVB_BY_STAGE

# ===========================================================================
# SECTION 1: BLOCKER RESOLUTION
# ===========================================================================

class TestBlockerResolution:
    def test_empty_packet_all_hard_blockers(self):
        # Test implementation
        ...

# ===========================================================================
# SECTION 2: CONTRADICTION HANDLING
# ===========================================================================

class TestContradictionHandling:
    # Tests for contradiction types
    ...

# Continue with remaining sections
```

**Key Imports:**
- From `intake.packet_models`: CanonicalPacket, Slot, EvidenceRef, AuthorityLevel, Ambiguity
- From `intake.decision`: run_gap_and_decision, field_fills_blocker, MVB_BY_STAGE, LEGACY_ALIASES

**Verification:**
```bash
pytest tests/test_comprehensive_v02.py -v
```

#### 2.2 Convert `notebooks/test_scenarios_realworld.py` to `tests/test_realworld_scenarios_v02.py`

**Current State:**
- Real-world scenario tests (not unit tests)
- Tests messy agency notes -> next action
- Uses custom test framework

**Conversion Strategy:**
Same as test_02_comprehensive.py but focused on:
- Scenario-based testing
- Real input patterns
- End-to-end decision validation

**Test Categories:**
1. Vague Lead -> ASK_FOLLOWUP
2. Confused Couple -> STOP_NEEDS_REVIEW
3. Budget Stretch -> advisory handling
4. Emergency Mode -> soft blocker suppression
5. Coordinator Group -> subgroup handling

**Verification:**
```bash
pytest tests/test_realworld_scenarios_v02.py -v
```

---

### Phase 3: Add v0.2 API Contract Regression Test

#### 3.1 Create `tests/test_api_contract_v02.py`

**Purpose:** Detect breaking changes to v0.2 API contract

**Test Categories:**

1. **Constant Validation**
   - `LEGACY_ALIASES` - ensure all v0.1 -> v0.2 mappings exist
   - `MVB_BY_STAGE` - validate structure for each stage
   - `AuthorityLevel` enum - verify all 7 levels exist
   - `CONTRADICTION_ACTIONS` - validate decision states

2. **Function Signature Validation**
   - `run_gap_and_decision(packet) -> DecisionResult`
   - `field_fills_blocker(slot, ambiguities, field_name) -> bool`
   - `classify_ambiguity_severity(field_name, ambiguity_type) -> str`
   - Use `inspect` module to verify signatures

3. **Dataclass Structure Validation**
   - `DecisionResult` fields match expected
   - `CanonicalPacket` has schema_version, stage, operating_mode
   - `Ambiguity` has all required fields
   - `Slot` has maturity field for derived signals

4. **Backward Compatibility Tests**
   - LEGACY_ALIASES mapping works both ways
   - Resolve field checks legacy names
   - field_fills_blocker handles legacy field names

**Implementation Pattern:**
```python
"""
v0.2 API Contract Regression Tests

Run: pytest tests/test_api_contract_v02.py -v
"""

import inspect
import pytest
from intake.packet_models import AuthorityLevel, CanonicalPacket, DecisionResult, Slot
from intake.decision import (
    LEGACY_ALIASES,
    MVB_BY_STAGE,
    run_gap_and_decision,
    field_fills_blocker,
    classify_ambiguity_severity,
)

class TestLegacyAliases:
    def test_all_v01_names_mapped(self):
        """Ensure all v0.1 field names have v0.2 mappings."""
        v01_names = {
            "destination_city", "travel_dates", "budget_range",
            "traveler_count", "traveler_details", "traveler_preferences",
        }
        assert v01_names.issubset(LEGACY_ALIASES.keys())

    def test_aliases_point_to_valid_v02_fields(self):
        """Ensure all alias targets are valid v0.2 fields."""
        for alias, canonical in LEGACY_ALIASES.items():
            assert canonical in MVB_BY_STAGE["discovery"]["hard_blockers"] or \
                   canonical in MVB_BY_STAGE["discovery"]["soft_blockers"]

class TestMVBByStage:
    def test_all_stages_defined(self):
        """All expected stages exist in MVB_BY_STAGE."""
        expected_stages = {"discovery", "shortlist", "proposal", "booking"}
        assert expected_stages.issubset(MVB_BY_STAGE.keys())

    def test_discovery_mvb_structure(self):
        """Discovery stage has correct hard and soft blockers."""
        discovery = MVB_BY_STAGE["discovery"]
        assert "destination_candidates" in discovery["hard_blockers"]
        assert "party_size" in discovery["hard_blockers"]

class TestAuthorityLevels:
    def test_all_levels_defined(self):
        """All 7 authority levels exist."""
        levels = {
            AuthorityLevel.MANUAL_OVERRIDE,
            AuthorityLevel.EXPLICIT_USER,
            AuthorityLevel.IMPORTED_STRUCTURED,
            AuthorityLevel.EXPLICIT_OWNER,
            AuthorityLevel.DERIVED_SIGNAL,
            AuthorityLevel.SOFT_HYPOTHESIS,
            AuthorityLevel.UNKNOWN,
        }
        assert len(levels) == 7

class TestFunctionSignatures:
    def test_run_gap_and_decision_signature(self):
        """run_gap_and_decision accepts CanonicalPacket, returns DecisionResult."""
        sig = inspect.signature(run_gap_and_decision)
        params = list(sig.parameters.keys())
        assert "packet" in params
        # Return type annotation check
        assert sig.return_annotation == DecisionResult or sig.return_annotation != inspect.Parameter.empty

class TestDecisionResultStructure:
    def test_all_required_fields_exist(self):
        """DecisionResult has all required v0.2 fields."""
        result = DecisionResult(packet_id="test", current_stage="discovery",
                               operating_mode="normal", decision_state="ASK_FOLLOWUP")
        required_fields = {
            "packet_id", "current_stage", "operating_mode", "decision_state",
            "hard_blockers", "soft_blockers", "ambiguities", "contradictions",
            "follow_up_questions", "branch_options", "rationale", "confidence_score",
        }
        assert hasattr(result, "packet_id")
        # Check all fields exist
```

**Verification:**
```bash
pytest tests/test_api_contract_v02.py -v
```

---

### Phase 4: Add Test Documentation

#### 4.1 Create `tests/README.md`

**Structure:**

```markdown
# Test Suite Documentation

## Test Categories

### Unit Tests (`tests/test_*.py`)
Test individual components in isolation.

- `test_nb01_v02.py` - ExtractionPipeline producing CanonicalPacket v0.2
- `test_nb02_v02.py` - Decision engine gap and decision logic
- `test_nb03_v02.py` - Session strategy generation
- `test_comprehensive_v02.py` - Comprehensive decision engine tests (migrated from notebooks)
- `test_realworld_scenarios_v02.py` - Real-world scenario tests (migrated from notebooks)
- `test_api_contract_v02.py` - API contract regression tests

### Integration Tests
Test multiple components working together.

- `test_e2e_freeze_pack.py` - Full spine freeze pack flow
- `test_lifecycle_retention.py` - Packet lifecycle and event retention
- `test_decision_policy_conformance.py` - Decision policy adherence

### Regression Tests
Ensure existing behavior is maintained.

- `test_geography_regression.py` - Geography data validation
- `test_spine_api_contract.py` - Spine API contract validation

## Running Tests

### Run All Tests
```bash
pytest tests/ -v
```

### Run Specific Test File
```bash
pytest tests/test_nb02_v02.py -v
```

### Run Specific Test Class
```bash
pytest tests/test_nb02_v02.py::TestBlockingDestinationAmbiguity -v
```

### Run Specific Test
```bash
pytest tests/test_nb02_v02.py::TestBlockingDestinationAmbiguity::test_unresolved_alternatives_block -v
```

### Run with Coverage
```bash
pytest tests/ --cov=src --cov-report=html
```

## v0.2 API Changes

### Canonical Field Names (v0.1 -> v0.2)

| v0.1 Field Name | v0.2 Canonical Name |
|----------------|---------------------|
| destination_city | destination_candidates |
| travel_dates | date_window |
| budget_range | budget_min |
| traveler_count | party_size |
| traveler_preferences | soft_preferences |
| traveler_details | passport_status |

### LEGACY_ALIASES
The v0.2 API maintains backward compatibility via `LEGACY_ALIASES` in `src/intake/decision.py`. Old field names are automatically mapped to new names.

### CanonicalPacket Structure (v0.2)
```python
@dataclass
class CanonicalPacket:
    packet_id: str
    schema_version: Literal["0.2"]
    stage: Literal["discovery", "shortlist", "proposal", "booking"]
    operating_mode: str
    decision_state: str
    facts: Dict[str, Slot]
    derived_signals: Dict[str, Slot]
    hypotheses: Dict[str, Slot]
    ambiguities: List[Ambiguity]
    unknowns: List[UnknownField]
    contradictions: List[Dict[str, Any]]
    # ... additional fields
```

## Fixture Usage

### Packet Fixtures
Located at `data/fixtures/packet_fixtures.py`

```python
from data.fixtures.packet_fixtures import PACKET_FIXTURES

fixture = PACKET_FIXTURES["ask_missing_destination"]
packet = fixture["packet"]
expected = fixture["expected"]
```

### Raw Fixtures
Located at `data/fixtures/raw_fixtures.py`

```python
from data.fixtures.raw_fixtures import RAW_FIXTURES

fixture = RAW_FIXTURES["clean_family_booking"]
raw_input = fixture["raw_input"]
expected = fixture["expected"]
```

### Test Scenarios
Located at `data/fixtures/test_scenarios.py`

```python
from data.fixtures.test_scenarios import TestScenarios

packet = TestScenarios.basic_complete_discovery()
```

## Writing New Tests

1. Follow existing test patterns: class-based organization with descriptive test names
2. Use `extract_and_decide()` helper for text -> packet -> decision flow
3. Include section headers with `# ===========================================================================`
4. Use v0.2 canonical field names directly
5. Add docstrings explaining what is being tested

## Test Helper Functions

### extract_and_decide(text, source)
Raw text -> CanonicalPacket -> DecisionResult

### make_packet(...)
Convenience for creating CanonicalPacket with common defaults

### S(value, conf, auth, evidence)
Shorthand for Slot creation
```

---

## Implementation Order

### Step 1: Migrate Fixture Files (Prerequisite)
1. Migrate `data/fixtures/packet_fixtures.py`
2. Migrate `data/fixtures/raw_fixtures.py`
3. Migrate `data/fixtures/test_scenarios.py`
4. Verify with `python data/fixtures/run_all_tests.py`
5. Verify with `python notebooks/04_eval_runner.ipynb`

### Step 2: Formalize Notebook Tests
1. Create `tests/test_comprehensive_v02.py`
2. Create `tests/test_realworld_scenarios_v02.py`
3. Verify both pass with pytest

### Step 3: Add API Contract Tests
1. Create `tests/test_api_contract_v02.py`
2. Add tests for all contract elements
3. Verify with pytest

### Step 4: Add Documentation
1. Create `tests/README.md`
2. Document test categories
3. Document v0.2 changes
4. Document fixture usage

### Step 5: Cleanup (Optional)
1. Archive original notebook test files
2. Update CI to run new pytest tests
3. Remove deprecated test runner scripts if no longer needed

---

## Critical Files for Implementation

- `/Users/pranay/Projects/travel_agency_agent/data/fixtures/packet_fixtures.py`
- `/Users/pranay/Projects/travel_agency_agent/data/fixtures/raw_fixtures.py`
- `/Users/pranay/Projects/travel_agency_agent/data/fixtures/test_scenarios.py`
- `/Users/pranay/Projects/travel_agency_agent/src/intake/decision.py` (for LEGACY_ALIASES reference)
- `/Users/pranay/Projects/travel_agency_agent/src/intake/packet_models.py` (for dataclass definitions)
- `/Users/pranay/Projects/travel_agency_agent/tests/test_nb02_v02.py` (reference for pytest patterns)
