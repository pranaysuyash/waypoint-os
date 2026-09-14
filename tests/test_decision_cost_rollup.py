"""
E-C steps 2-3: cost-per-decision attribution tests.

Covers (COST_PER_OUTCOME_MODEL_2026-09-07 §1, §3.2, §3.3):
- DecisionTelemetry.get_cost_rollup math (empty window, mixed sources, sums)
- decision_id minting in run_gap_and_decision (distinct per invocation)
- record_decision backward compatibility (pre-correlation positional calls)
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.decision.telemetry import get_telemetry, reset_telemetry
from src.intake.decision import run_gap_and_decision
from src.intake.packet_models import CanonicalPacket, Slot


def _fresh_telemetry():
    reset_telemetry()
    return get_telemetry()


def _sample_packet(packet_id: str = "ec_rollup_packet") -> CanonicalPacket:
    return CanonicalPacket(
        packet_id=packet_id,
        stage="discovery",
        operating_mode="normal_intake",
        facts={
            "destination_city": Slot(
                value="Singapore", confidence=0.9, authority_level="explicit_user"
            ),
            "origin_city": Slot(
                value="Bangalore", confidence=0.9, authority_level="explicit_user"
            ),
            "travel_dates": Slot(
                value="2026-10-10 to 2026-10-15",
                confidence=0.9,
                authority_level="explicit_user",
            ),
            "traveler_count": Slot(
                value=2, confidence=0.9, authority_level="explicit_user"
            ),
        },
    )


# ---------------------------------------------------------------------------
# Rollup math
# ---------------------------------------------------------------------------


def test_cost_rollup_empty_window():
    telemetry = _fresh_telemetry()

    rollup = telemetry.get_cost_rollup(window_seconds=3600)

    assert rollup["total_cost_inr"] == 0.0
    assert rollup["decisions"] == 0
    assert rollup["cost_per_decision_inr"] == 0.0  # no ZeroDivisionError
    assert rollup["by_source"] == {}


def test_cost_rollup_sums_cost_across_mixed_sources():
    telemetry = _fresh_telemetry()

    # Pre-correlation positional call + correlated keyword calls, mixed sources.
    # Positional order mirrors the original signature:
    # (decision_type, source, latency_ms, cache_hit, llm_used, error, cost_inr)
    telemetry.record_decision("risk_a", "llm", 10.0, False, True, None, 2.0)
    telemetry.record_decision(
        "risk_b", "llm", 20.0, decision_id="d-2", trip_id="t-1", cost_inr=3.0
    )
    telemetry.record_decision(
        "risk_c", "rule", 5.0, decision_id="d-3", trip_id="t-1", cost_inr=0.0
    )
    telemetry.record_decision(
        "risk_d", "cache", 1.0, decision_id="d-4", trip_id="t-1", cost_inr=0.5
    )

    rollup = telemetry.get_cost_rollup(window_seconds=3600)

    assert rollup["decisions"] == 4
    assert rollup["total_cost_inr"] == 5.5  # 2.0 + 3.0 + 0.0 + 0.5
    assert rollup["cost_per_decision_inr"] == 5.5 / 4

    by_source = rollup["by_source"]
    assert set(by_source) == {"llm", "rule", "cache"}

    llm = by_source["llm"]
    assert llm["decisions"] == 2
    assert llm["cost_inr"] == 5.0
    assert llm["cost_per_decision_inr"] == 2.5

    assert by_source["rule"]["decisions"] == 1
    assert by_source["rule"]["cost_inr"] == 0.0
    assert by_source["rule"]["cost_per_decision_inr"] == 0.0

    assert by_source["cache"]["decisions"] == 1
    assert by_source["cache"]["cost_inr"] == 0.5
    assert by_source["cache"]["cost_per_decision_inr"] == 0.5


def test_cost_rollup_respects_window():
    telemetry = _fresh_telemetry()
    # Rollup with an empty window must not see recent records.
    telemetry.record_decision("risk_a", "llm", 10.0, cost_inr=2.0)

    empty_rollup = telemetry.get_cost_rollup(window_seconds=0)
    assert empty_rollup["decisions"] == 0
    assert empty_rollup["total_cost_inr"] == 0.0

    full_rollup = telemetry.get_cost_rollup(window_seconds=3600)
    assert full_rollup["decisions"] == 1
    assert full_rollup["total_cost_inr"] == 2.0


def test_export_prometheus_includes_cost_per_decision_gauge():
    telemetry = _fresh_telemetry()
    telemetry.record_decision("risk_a", "llm", 10.0, cost_inr=2.0)

    snapshot = telemetry.get_snapshot(window_seconds=300)
    exposition = telemetry.export_prometheus(snapshot)

    assert "hybrid_decision_cost_per_decision_inr" in exposition
    assert "2.0000" in exposition


# ---------------------------------------------------------------------------
# decision_id minting (run_gap_and_decision)
# ---------------------------------------------------------------------------


def test_run_gap_and_decision_mints_distinct_decision_ids():
    result_a = run_gap_and_decision(_sample_packet("ec_id_packet_a"))
    result_b = run_gap_and_decision(_sample_packet("ec_id_packet_b"))

    assert result_a.decision_id is not None
    assert result_b.decision_id is not None
    assert result_a.decision_id != result_b.decision_id
    # UUID-shaped join key (E-C §3.2)
    assert len(result_a.decision_id) == 36
    assert result_a.decision_id.count("-") == 4


def test_decision_id_is_optional_and_defaults_to_none():
    # Additive field with default None — constructing the dataclass directly
    # (the path existing consumers use) must keep working.
    from src.intake.decision import DecisionResult

    result = DecisionResult(
        packet_id="ec_default_packet",
        current_stage="discovery",
        operating_mode="normal_intake",
        decision_state="ASK_FOLLOWUP",
    )
    assert result.decision_id is None


# ---------------------------------------------------------------------------
# record_decision backward compatibility
# ---------------------------------------------------------------------------


def test_record_decision_positional_calls_still_work():
    telemetry = _fresh_telemetry()

    # Exact pre-correlation positional signature:
    # (decision_type, source, latency_ms, cache_hit, llm_used, error, cost_inr)
    telemetry.record_decision("risk_a", "cache", 1.0, True, False, None, 0.0)
    telemetry.record_decision("risk_b", "llm", 5.0, False, True, "boom", 1.5)

    snapshot = telemetry.get_snapshot(window_seconds=300)
    assert snapshot.total_decisions == 2
    assert snapshot.total_cost_inr == 1.5
    assert snapshot.decisions_by_source == {"cache": 1, "llm": 1}
    assert snapshot.error_count == 1

    rollup = telemetry.get_cost_rollup(window_seconds=300)
    assert rollup["decisions"] == 2
    assert rollup["total_cost_inr"] == 1.5


def test_record_decision_correlated_fields_are_stored():
    telemetry = _fresh_telemetry()

    telemetry.record_decision(
        decision_type="risk_a",
        source="llm",
        latency_ms=7.0,
        cost_inr=0.25,
        decision_id="d-ec-1",
        trip_id="trip-ec-1",
    )

    metrics = telemetry._metrics
    assert len(metrics) == 1
    assert metrics[0].decision_id == "d-ec-1"
    assert metrics[0].trip_id == "trip-ec-1"
