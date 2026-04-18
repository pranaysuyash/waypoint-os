# Test Suite Documentation

This directory contains the test suite for the travel agency intake/decision pipeline (NB02) and downstream systems (NB03).

## Test Categories

### Unit Tests
Test individual functions and classes in isolation.

- `test_geography.py` - Geography and location handling
- `test_follow_up_mode.py` - Follow-up question generation

### Integration Tests
Test component interactions and the full pipeline.

- `test_nb01_v02.py` - NB01 extraction pipeline tests
- `test_nb02_v02.py` - NB02 decision engine tests
- `test_nb03_v02.py` - NB03 proposal generation tests
- `test_lifecycle_retention.py` - Data lifecycle across stages
- `test_e2e_freeze_pack.py` - End-to-end packet freeze/unpack
- `test_decision_policy_conformance.py` - Decision policy validation

### Regression Tests
API contract validation to catch breaking changes early.

- `test_api_contract_v02.py` - v0.2 API contract tests
- `test_spine_api_contract.py` - Spine API contract tests (requires running server)

### Comprehensive Tests
Full coverage of decision engine behavior.

- `test_comprehensive_v02.py` - 29 tests covering blocker resolution, stage progression, contradictions, decision states, confidence scoring
- `test_realworld_scenarios_v02.py` - 13 real-world scenario tests

### Geography Tests
- `test_geography.py` - Geography utilities
- `test_geography_regression.py` - Geography regression tests

### Suitability Tests
- `test_suitability.py` - 23 tests covering Tier 1 scoring, Tier 2 context rules, catalog functions, and integration

## Running Tests

### All tests
```bash
uv run pytest
```

### All tests except integration tests (requires live spine-api)
```bash
uv run pytest -m 'not integration'
```

### Specific test file
```bash
uv run pytest tests/test_suitability.py -v
```

### Specific test class
```bash
python -m pytest tests/test_nb02_v02.py::TestBlockingAmbiguity -v
```

### Specific test function
```bash
python -m pytest tests/test_nb02_v02.py::TestBlockingAmbiguity::test_unresolved_alternatives_block -v
```

### With coverage
```bash
python -m pytest tests/ --cov=src --cov-report=html
```

### Run only fast tests
```bash
python -m pytest tests/ -m "not slow" -v
```

## v0.2 API Changes

### Field Name Canonicalization

| v0.1 Field Name | v0.2 Canonical Name |
|------------------|---------------------|
| `destination_city` | `destination_candidates` |
| `travel_dates` | `date_window` |
| `budget_range` | `budget_min` |
| `traveler_count` | `party_size` |
| `traveler_preferences` | `soft_preferences` |
| `traveler_details` | `passport_status` |
| `selected_destinations` | `resolved_destination` |

### Function Signature Changes

**`run_gap_and_decision()` (v0.2):**
- Removed: `current_stage`, `mvb_config`, `confidence_threshold` parameters
- Added: `feasibility_table`, `_cached_feasibility` parameters
- Stage is now read from `packet.stage` instead

**`field_fills_blocker()` (v0.2):**
- Added: `ambiguities`, `field_name` parameters

### Decision State Changes

- `PROCEED_TRAVELER_SAFE` vs `PROCEED_INTERNAL_DRAFT` now depends on internal confidence threshold
- `budget_raw_text` field is now required for complete packets

### Data Model Changes

- `DecisionResult` is now a dataclass (use `dataclasses.asdict()` instead of `to_dict()`)
- `CanonicalPacket.schema_version` is now `"0.2"`
- `AuthorityLevel` is a class with string constants, not an IntEnum

## Fixture Usage

The project provides test fixtures in `data/fixtures/`:

### Packet Fixtures
```python
from data.fixtures.packet_fixtures import PACKET_FIXTURES, get_fixtures_by_category

# Get a specific fixture
fixture = PACKET_FIXTURES["ask_empty"]
packet = fixture["packet"]
expected = fixture["expected"]

# Get fixtures by category
ask_fixtures = get_fixtures_by_category("ask_followup")
```

### Test Scenarios
```python
from data.fixtures.test_scenarios import TestScenarios

# Get a specific scenario
packet = TestScenarios.basic_empty()

# Get all scenarios
all_scenarios = TestScenarios.get_all()
```

### Raw Fixtures
```python
from data.fixtures.raw_fixtures import RAW_FIXTURES

fixture = RAW_FIXTURES["clean_family_booking"]
raw_input = fixture["raw_input"]
expected = fixture["expected"]
```

## Test Patterns

### Creating a Packet for Testing

```python
from intake.packet_models import CanonicalPacket, Slot, AuthorityLevel

pkt = CanonicalPacket(packet_id="test_packet", stage="discovery")

# Add facts
pkt.facts["destination_candidates"] = Slot(
    value=["Singapore"],
    confidence=0.9,
    authority_level=AuthorityLevel.EXPLICIT_USER,
)
```

### Testing Decision Results

```python
from intake.decision import run_gap_and_decision

r = run_gap_and_decision(pkt)

# Check decision state
assert r.decision_state == "ASK_FOLLOWUP"

# Check blockers
assert len(r.hard_blockers) == 0
assert "budget_min" in r.soft_blockers

# Check confidence
assert r.confidence_score > 0.7
```

## Test Status

As of 2026-04-15:

| Test File | Tests | Status |
|-----------|-------|--------|
| `test_nb01_v02.py` | - | Passing |
| `test_nb02_v02.py` | - | Passing |
| `test_nb03_v02.py` | - | Passing |
| `test_comprehensive_v02.py` | 29 | Passing |
| `test_realworld_scenarios_v02.py` | 13 | Passing |
| `test_api_contract_v02.py` | 21 | Passing |
| `test_geography.py` | - | Passing |
| `test_geography_regression.py` | - | Passing |
| `test_lifecycle_retention.py` | - | Passing |
| `test_e2e_freeze_pack.py` | - | Passing |
| `test_decision_policy_conformance.py` | - | Passing |
| `test_follow_up_mode.py` | - | Passing |

**Total:** 192+ passing tests

## Notes

- Spine API tests (`test_spine_api_contract.py`) are skipped by default as they require a running server
- Tests use pytest fixtures and markers for better organization
- Coverage reports can be generated with `--cov` flag
