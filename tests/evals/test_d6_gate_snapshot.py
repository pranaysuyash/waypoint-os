import json
from pathlib import Path

from src.evals.audit.snapshot import (
    build_gate_snapshot,
    stable_snapshot_view,
    verify_gate_snapshot_file,
    write_gate_snapshot,
)


def test_build_gate_snapshot_includes_activity_gate_and_metrics():
    snapshot = build_gate_snapshot()
    assert snapshot["manifest_version"] == 1
    assert snapshot["total_fixtures"] >= 1
    assert "activity" in snapshot["categories"]
    activity = snapshot["categories"]["activity"]
    assert activity["status"] == "shadow"
    assert activity["authoritative_for_public_surface"] is False
    assert isinstance(activity["metrics"], dict)


def test_build_gate_snapshot_includes_routing_health_gate():
    snapshot = build_gate_snapshot()
    rh = snapshot["routing_health"]
    assert rh["status"] == "healthy"
    assert rh["blocks_ci"] is False
    assert isinstance(rh["thresholds"], dict)
    assert rh["alerts"] == []
    assert rh["thresholds"]["fallback_trigger_rate_warning"] == 0.3
    assert rh["thresholds"]["latency_p95_ms_critical"] == 30_000
    assert rh["metrics_snapshot"]["fallback_trigger_rate"] == 0.0
    assert rh["metrics_snapshot"]["review_trigger_rate"] == 0.0
    assert "checked_at" in rh


def test_stable_snapshot_view_strips_volatile_timestamp_from_routing_health():
    snapshot = build_gate_snapshot()
    stable = stable_snapshot_view(snapshot)
    rh = stable["routing_health"]
    assert isinstance(rh, dict)
    assert "status" in rh
    assert "blocks_ci" in rh
    assert "thresholds" in rh
    assert "alerts" in rh
    assert "metrics_snapshot" in rh
    # Volatile timestamp must not be present
    assert "checked_at" not in rh


def test_build_gate_snapshot_routing_health_baseline_healthy():
    """With no live data, routing health should always be healthy."""
    snapshot = build_gate_snapshot()
    rh = snapshot["routing_health"]
    assert rh["status"] == "healthy"
    assert rh["blocks_ci"] is False


def test_write_gate_snapshot_creates_json_file(tmp_path: Path):
    output = tmp_path / "d6_gate_snapshot.json"
    written = write_gate_snapshot(output_path=output)
    assert written == output
    payload = json.loads(output.read_text())
    assert payload["categories"]["budget"]["status"] == "gating"
    assert "generated_at" in payload
    assert "routing_health" in payload


def test_write_gate_snapshot_routing_health_in_json(tmp_path: Path):
    output = tmp_path / "d6_gate_snapshot.json"
    write_gate_snapshot(output_path=output)
    payload = json.loads(output.read_text())
    rh = payload["routing_health"]
    assert rh["status"] == "healthy"
    assert isinstance(rh["thresholds"], dict)
    assert len(rh["thresholds"]) >= 6


def test_verify_gate_snapshot_file_detects_drift(tmp_path: Path):
    output = tmp_path / "d6_gate_snapshot.json"
    write_gate_snapshot(output_path=output)
    ok, _, _ = verify_gate_snapshot_file(snapshot_path=output)
    assert ok is True

    payload = json.loads(output.read_text())
    payload["categories"]["activity"]["status"] = "gating"
    output.write_text(json.dumps(payload, indent=2))

    ok, expected, actual = verify_gate_snapshot_file(snapshot_path=output)
    assert ok is False
    assert expected["categories"]["activity"]["status"] == "shadow"
    assert actual["categories"]["activity"]["status"] == "gating"


def test_verify_gate_snapshot_detects_routing_health_drift(tmp_path: Path):
    output = tmp_path / "d6_gate_snapshot.json"
    write_gate_snapshot(output_path=output)
    ok, _, _ = verify_gate_snapshot_file(snapshot_path=output)
    assert ok is True

    # Tamper with routing_health thresholds
    payload = json.loads(output.read_text())
    payload["routing_health"]["thresholds"]["fallback_trigger_rate_warning"] = 0.99
    output.write_text(json.dumps(payload, indent=2))

    ok, expected, actual = verify_gate_snapshot_file(snapshot_path=output)
    assert ok is False
    assert expected["routing_health"]["thresholds"]["fallback_trigger_rate_warning"] == 0.3
    assert actual["routing_health"]["thresholds"]["fallback_trigger_rate_warning"] == 0.99


def test_verify_gate_snapshot_detects_routing_health_status_drift(tmp_path: Path):
    output = tmp_path / "d6_gate_snapshot.json"
    write_gate_snapshot(output_path=output)

    payload = json.loads(output.read_text())
    payload["routing_health"]["status"] = "critical"
    output.write_text(json.dumps(payload, indent=2))

    ok, _, _ = verify_gate_snapshot_file(snapshot_path=output)
    assert ok is False


# --- extraction_health gate tests ---


def test_build_gate_snapshot_includes_extraction_health():
    snapshot = build_gate_snapshot()
    eh = snapshot["extraction_health"]
    assert isinstance(eh, dict)
    assert "status" in eh
    assert "overall_f1" in eh
    assert "overall_precision" in eh
    assert "overall_recall" in eh
    assert "total_fixtures" in eh
    assert eh["total_fixtures"] == 50
    assert "by_document_type" in eh
    assert "by_difficulty" in eh
    # Self-consistent baseline: expected outputs used as actuals → 100% F1
    assert eh["status"] == "passing"
    assert eh["overall_f1"] == 1.0
    assert eh["blocks_ci"] is False


def test_stable_snapshot_view_strips_extraction_health_volatile_fields():
    snapshot = build_gate_snapshot()
    stable = stable_snapshot_view(snapshot)
    eh = stable["extraction_health"]
    assert isinstance(eh, dict)
    assert "status" in eh
    assert "overall_f1" in eh
    assert "blocks_ci" in eh
    # Volatile note field must not be present
    assert "note" not in eh


def test_write_gate_snapshot_includes_extraction_health(tmp_path: Path):
    output = tmp_path / "d6_gate_snapshot.json"
    write_gate_snapshot(output_path=output)
    payload = json.loads(output.read_text())
    assert "extraction_health" in payload
    eh = payload["extraction_health"]
    assert eh["total_fixtures"] == 50


def test_verify_gate_snapshot_detects_extraction_health_drift(tmp_path: Path):
    output = tmp_path / "d6_gate_snapshot.json"
    write_gate_snapshot(output_path=output)

    payload = json.loads(output.read_text())
    payload["extraction_health"]["overall_f1"] = 0.99
    output.write_text(json.dumps(payload, indent=2))

    ok, _, _ = verify_gate_snapshot_file(snapshot_path=output)
    assert ok is False


def test_extraction_health_baseline_has_all_document_types():
    snapshot = build_gate_snapshot()
    eh = snapshot["extraction_health"]
    by_type = eh["by_document_type"]
    assert "passport" in by_type
    assert "visa" in by_type
    assert "insurance" in by_type


def test_extraction_health_manifest_category_present():
    snapshot = build_gate_snapshot()
    assert "extraction" in snapshot["categories"]
    extraction_cat = snapshot["categories"]["extraction"]
    assert extraction_cat["status"] == "shadow"
    assert extraction_cat["blocks_ci"] is False
    assert extraction_cat["authoritative_for_public_surface"] is False


def test_extraction_manifest_category_evaluated_with_accuracy():
    """Extraction category should receive overall_f1 from extraction_health."""
    snapshot = build_gate_snapshot()
    extraction_cat = snapshot["categories"]["extraction"]
    # Self-consistent baseline: f1=1.0, meets min_accuracy=0.85
    assert extraction_cat["status"] == "shadow"
    assert extraction_cat["meets_thresholds"] is True
    assert extraction_cat["blocks_ci"] is False
    assert "actual_source_not_independent" in extraction_cat["reasons"]


def test_extraction_manifest_category_min_accuracy_threshold():
    """Verify the extraction category uses min_accuracy from manifest.yaml."""
    from src.evals.audit.manifest import load_manifest
    manifest = load_manifest()
    extraction_config = manifest.categories["extraction"]
    assert extraction_config.min_accuracy == 0.85
    assert extraction_config.status == "shadow"


def test_extraction_baseline_drift_fields_present():
    """Extraction health should include expected_baseline_f1 and baseline_drifted."""
    snapshot = build_gate_snapshot()
    eh = snapshot["extraction_health"]
    assert "expected_baseline_f1" in eh
    assert "baseline_drifted" in eh
    assert eh["expected_baseline_f1"] == 1.0


def test_extraction_baseline_no_drift_by_default():
    """Self-consistent baseline should produce no drift."""
    snapshot = build_gate_snapshot()
    eh = snapshot["extraction_health"]
    assert eh["baseline_drifted"] is False
    assert eh["overall_f1"] == eh["expected_baseline_f1"]


def test_extraction_mirror_is_explicitly_calibration_only():
    """Expected-vs-expected scores carry zero evidence for product quality."""
    snapshot = build_gate_snapshot()
    eh = snapshot["extraction_health"]
    assert eh["actual_source"] == "expected_fixture_mirror"
    assert eh["live_grading"] is False
    assert eh["evidence_tier"] == 0


def test_extraction_baseline_drift_detected_with_live_results():
    """Empty live results that diverge from expected should trigger drift."""
    snapshot = build_gate_snapshot(extraction_live_results={})
    eh = snapshot["extraction_health"]
    assert eh["baseline_drifted"] is True
    assert eh["overall_f1"] < eh["expected_baseline_f1"]


def test_extraction_baseline_drift_in_stable_view():
    """Drift fields should appear in stable snapshot view."""
    snapshot = build_gate_snapshot()
    stable = stable_snapshot_view(snapshot)
    eh = stable["extraction_health"]
    assert "expected_baseline_f1" in eh
    assert "baseline_drifted" in eh
    # Volatile note field must not be present
    assert "note" not in eh


def test_extraction_live_results_blocks_ci_when_below_threshold():
    """Low F1 with gating status should block CI via manifest category."""
    snapshot = build_gate_snapshot(extraction_live_results={})
    extraction_cat = snapshot["categories"]["extraction"]
    assert extraction_cat["status"] == "shadow"
    assert extraction_cat["meets_thresholds"] is False
    assert extraction_cat["blocks_ci"] is False


def test_extraction_baseline_f1_constant_matches():
    """EXPECTED_EXTRACTION_BASELINE_F1 should equal 1.0."""
    from src.evals.audit.snapshot import EXPECTED_EXTRACTION_BASELINE_F1
    assert EXPECTED_EXTRACTION_BASELINE_F1 == 1.0


# --- pipeline_health gate tests ---


def test_build_gate_snapshot_includes_pipeline_health():
    snapshot = build_gate_snapshot()
    ph = snapshot["pipeline_health"]
    assert isinstance(ph, dict)
    assert "status" in ph
    assert "overall_accuracy" in ph
    assert "total_fixtures" in ph
    assert "fixtures_passing" in ph
    assert "fixtures_failing" in ph
    assert "stage_accuracies" in ph
    assert ph["total_fixtures"] == 7
    # Self-consistent baseline: expected outputs used as actuals → 100% accuracy
    assert ph["status"] == "passing"
    assert ph["overall_accuracy"] == 1.0
    assert ph["blocks_ci"] is False


def test_stable_snapshot_view_strips_pipeline_health_volatile_fields():
    snapshot = build_gate_snapshot()
    stable = stable_snapshot_view(snapshot)
    ph = stable["pipeline_health"]
    assert isinstance(ph, dict)
    assert "status" in ph
    assert "overall_accuracy" in ph
    assert "total_fixtures" in ph
    assert "blocks_ci" in ph
    # Volatile note and stage_accuracies must not be present
    assert "note" not in ph
    assert "stage_accuracies" not in ph


def test_write_gate_snapshot_includes_pipeline_health(tmp_path: Path):
    output = tmp_path / "d6_gate_snapshot.json"
    write_gate_snapshot(output_path=output)
    payload = json.loads(output.read_text())
    assert "pipeline_health" in payload
    ph = payload["pipeline_health"]
    assert ph["total_fixtures"] == 7
    assert isinstance(ph["stage_accuracies"], dict)


def test_verify_gate_snapshot_detects_pipeline_health_drift(tmp_path: Path):
    output = tmp_path / "d6_gate_snapshot.json"
    write_gate_snapshot(output_path=output)

    payload = json.loads(output.read_text())
    payload["pipeline_health"]["overall_accuracy"] = 0.99
    output.write_text(json.dumps(payload, indent=2))

    ok, _, _ = verify_gate_snapshot_file(snapshot_path=output)
    assert ok is False


# --- pipeline manifest category tests ---


def test_pipeline_manifest_category_present():
    snapshot = build_gate_snapshot()
    assert "pipeline" in snapshot["categories"]
    pipeline_cat = snapshot["categories"]["pipeline"]
    assert pipeline_cat["status"] == "shadow"
    assert pipeline_cat["blocks_ci"] is False
    assert pipeline_cat["authoritative_for_public_surface"] is False


def test_pipeline_manifest_category_evaluated_with_accuracy():
    """Pipeline category should receive overall_accuracy from pipeline_health."""
    snapshot = build_gate_snapshot()
    pipeline_cat = snapshot["categories"]["pipeline"]
    snapshot["pipeline_health"]
    # Self-consistent baseline: expected outputs as actuals → 100% accuracy
    # Pipeline category is gating, and accuracy meets the 0.80 threshold
    assert pipeline_cat["status"] == "shadow"
    assert pipeline_cat["meets_thresholds"] is True
    assert pipeline_cat["blocks_ci"] is False
    assert "actual_source_not_independent" in pipeline_cat["reasons"]


def test_pipeline_manifest_category_min_accuracy_threshold():
    """Verify the pipeline category uses min_accuracy from manifest.yaml."""
    from src.evals.audit.manifest import load_manifest
    manifest = load_manifest()
    pipeline_config = manifest.categories["pipeline"]
    assert pipeline_config.min_accuracy == 0.80
    assert pipeline_config.status == "shadow"


def test_pipeline_category_blocks_ci_when_accuracy_below_threshold():
    """Gating status means blocks_ci is True when accuracy is below threshold."""
    from src.evals.audit.gates import _meets_thresholds
    # Simulate low accuracy (below 0.80 threshold)
    meets, reasons = _meets_thresholds(
        None, min_precision=0.0, min_recall=0.0, min_severity_accuracy=0.0,
        min_accuracy=0.80, accuracy=0.50,
    )
    assert meets is False
    assert "accuracy_below_threshold" in reasons


def test_pipeline_category_passes_when_accuracy_above_threshold():
    """Gating status with accuracy above threshold should not block CI."""
    from src.evals.audit.gates import _meets_thresholds
    meets, reasons = _meets_thresholds(
        None, min_precision=0.0, min_recall=0.0, min_severity_accuracy=0.0,
        min_accuracy=0.80, accuracy=0.90,
    )
    assert meets is True
    assert "accuracy_below_threshold" not in reasons


# --- live pipeline results tests ---


def test_build_gate_snapshot_with_live_pipeline_results():
    """Live pipeline results should override the self-consistent baseline."""
    snapshot = build_gate_snapshot()
    baseline_acc = snapshot["pipeline_health"]["overall_accuracy"]
    # Baseline is 1.0 (self-consistent)
    assert baseline_acc == 1.0

    # Now provide partial live results (only one fixture matches perfectly)
    from src.evals.audit.rules.pipeline import load_pipeline_fixtures
    fixtures = load_pipeline_fixtures(Path("data/fixtures/pipeline/pipeline_golden.json"))
    live_results = {
        fixtures[0].fixture_id: {
            "extraction": fixtures[0].expected_extraction,
            "agents": fixtures[0].expected_agents,
            "decision": fixtures[0].expected_decision,
        },
    }
    degraded = build_gate_snapshot(pipeline_live_results=live_results)
    degraded_acc = degraded["pipeline_health"]["overall_accuracy"]
    # Accuracy should drop because only 1 of 7 fixtures has actual results
    assert degraded_acc < baseline_acc
    assert degraded_acc > 0.0


def test_pipeline_live_results_accuracy_degrades_to_warning():
    """Partial live results should produce warning status (0.50-0.80)."""
    from src.evals.audit.rules.pipeline import load_pipeline_fixtures
    fixtures = load_pipeline_fixtures(Path("data/fixtures/pipeline/pipeline_golden.json"))
    # Provide results for 2 of 7 fixtures
    live_results = {
        fixtures[0].fixture_id: {
            "extraction": fixtures[0].expected_extraction,
            "agents": fixtures[0].expected_agents,
            "decision": fixtures[0].expected_decision,
        },
        fixtures[1].fixture_id: {
            "extraction": fixtures[1].expected_extraction,
            "agents": fixtures[1].expected_agents,
            "decision": fixtures[1].expected_decision,
        },
    }
    snapshot = build_gate_snapshot(pipeline_live_results=live_results)
    ph = snapshot["pipeline_health"]
    # 2/7 fixtures with perfect results → accuracy ~0.28
    assert ph["overall_accuracy"] < 0.80
    assert ph["status"] in ("failing", "warning")


def test_pipeline_live_results_empty_degrades_to_failing():
    """Empty live results should produce failing status."""
    snapshot = build_gate_snapshot(pipeline_live_results={})
    ph = snapshot["pipeline_health"]
    assert ph["overall_accuracy"] < 0.50
    assert ph["status"] == "failing"
    assert ph["blocks_ci"] is True


def test_pipeline_live_results_blocks_ci_when_below_threshold():
    """Low accuracy with gating status should block CI via manifest category."""
    snapshot = build_gate_snapshot(pipeline_live_results={})
    pipeline_cat = snapshot["categories"]["pipeline"]
    assert pipeline_cat["status"] == "shadow"
    assert pipeline_cat["meets_thresholds"] is False
    assert pipeline_cat["blocks_ci"] is False


def test_write_gate_snapshot_with_live_results(tmp_path: Path):
    """write_gate_snapshot should accept pipeline_live_results."""
    from src.evals.audit.rules.pipeline import load_pipeline_fixtures
    fixtures = load_pipeline_fixtures(Path("data/fixtures/pipeline/pipeline_golden.json"))
    live_results = {
        fixtures[0].fixture_id: {
            "extraction": fixtures[0].expected_extraction,
            "agents": fixtures[0].expected_agents,
            "decision": fixtures[0].expected_decision,
        },
    }
    output = tmp_path / "d6_gate_snapshot.json"
    write_gate_snapshot(output_path=output, pipeline_live_results=live_results)
    payload = json.loads(output.read_text())
    ph = payload["pipeline_health"]
    assert ph["overall_accuracy"] < 1.0
    assert ph["overall_accuracy"] > 0.0


# --- pipeline baseline drift detection tests ---


def test_pipeline_baseline_drift_fields_present():
    """Pipeline health should include expected_baseline_accuracy and baseline_drifted."""
    snapshot = build_gate_snapshot()
    ph = snapshot["pipeline_health"]
    assert "expected_baseline_accuracy" in ph
    assert "baseline_drifted" in ph
    assert ph["expected_baseline_accuracy"] == 1.0


def test_pipeline_baseline_no_drift_by_default():
    """Self-consistent baseline should produce no drift."""
    snapshot = build_gate_snapshot()
    ph = snapshot["pipeline_health"]
    assert ph["baseline_drifted"] is False
    assert ph["overall_accuracy"] == ph["expected_baseline_accuracy"]


def test_pipeline_mirror_is_explicitly_calibration_only():
    """Pipeline fixture mirrors cannot be mistaken for runtime actuals."""
    snapshot = build_gate_snapshot()
    ph = snapshot["pipeline_health"]
    assert ph["actual_source"] == "expected_fixture_mirror"
    assert ph["live_grading"] is False
    assert ph["evidence_tier"] == 0


def test_pipeline_baseline_drift_detected_with_live_results():
    """Live results that diverge from expected should trigger drift."""
    snapshot = build_gate_snapshot(pipeline_live_results={})
    ph = snapshot["pipeline_health"]
    assert ph["baseline_drifted"] is True
    assert ph["overall_accuracy"] < ph["expected_baseline_accuracy"]


def test_pipeline_baseline_drift_in_stable_view():
    """Drift fields should appear in stable snapshot view for drift detection."""
    snapshot = build_gate_snapshot()
    stable = stable_snapshot_view(snapshot)
    ph = stable["pipeline_health"]
    assert "expected_baseline_accuracy" in ph
    assert "baseline_drifted" in ph
    # Volatile note and stage_accuracies must not be present
    assert "note" not in ph
    assert "stage_accuracies" not in ph


def test_pipeline_baseline_drift_detected_by_verify(tmp_path: Path):
    """Tampering with pipeline accuracy should be detected as drift."""
    output = tmp_path / "d6_gate_snapshot.json"
    write_gate_snapshot(output_path=output)

    payload = json.loads(output.read_text())
    payload["pipeline_health"]["overall_accuracy"] = 0.50
    output.write_text(json.dumps(payload, indent=2))

    ok, _, _ = verify_gate_snapshot_file(snapshot_path=output)
    assert ok is False


def test_pipeline_baseline_accuracy_constant_matches():
    """EXPECTED_PIPELINE_BASELINE_ACCURACY should equal 1.0."""
    from src.evals.audit.snapshot import EXPECTED_PIPELINE_BASELINE_ACCURACY
    assert EXPECTED_PIPELINE_BASELINE_ACCURACY == 1.0


# --- colloquial_health gate tests (DEMO-02 / IMP-07) ---


def test_build_gate_snapshot_includes_colloquial_health():
    """Colloquial gate runs the live intake pipeline on colloquial_golden.json."""
    snapshot = build_gate_snapshot()
    ch = snapshot["colloquial_health"]
    assert isinstance(ch, dict)
    assert ch["total_fixtures"] == 16
    # Live pipeline path: expected fixtures fully matched by the real extractor
    assert ch["note"].startswith("Live pipeline extraction results")
    assert ch["status"] == "passing"
    assert ch["overall_f1"] == 1.0
    assert ch["baseline_drifted"] is False
    assert ch["blocks_ci"] is False


def test_stable_snapshot_view_strips_colloquial_health_volatile_fields():
    snapshot = build_gate_snapshot()
    stable = stable_snapshot_view(snapshot)
    ch = stable["colloquial_health"]
    assert isinstance(ch, dict)
    assert "status" in ch
    assert "overall_f1" in ch
    assert "baseline_drifted" in ch
    assert "blocks_ci" in ch
    # Volatile note field must not be present
    assert "note" not in ch
    # fixture_accuracy lives in the grouping metrics — pure value mismatches
    # move fixture accuracy without moving precision/recall, so the
    # comparable view must include them for drift detection.
    assert "by_document_type" in ch
    assert "by_difficulty" in ch


def test_write_gate_snapshot_includes_colloquial_health(tmp_path: Path):
    output = tmp_path / "d6_gate_snapshot.json"
    write_gate_snapshot(output_path=output)
    payload = json.loads(output.read_text())
    assert "colloquial_health" in payload
    assert payload["colloquial_health"]["total_fixtures"] == 16


def test_verify_gate_snapshot_detects_colloquial_health_drift(tmp_path: Path):
    output = tmp_path / "d6_gate_snapshot.json"
    write_gate_snapshot(output_path=output)

    payload = json.loads(output.read_text())
    payload["colloquial_health"]["overall_f1"] = 0.99
    output.write_text(json.dumps(payload, indent=2))

    ok, _, _ = verify_gate_snapshot_file(snapshot_path=output)
    assert ok is False


def test_colloquial_manifest_category_present():
    snapshot = build_gate_snapshot()
    assert "colloquial" in snapshot["categories"]
    cat = snapshot["categories"]["colloquial"]
    assert cat["status"] == "gating"
    assert cat["meets_thresholds"] is True
    assert cat["blocks_ci"] is False


def test_colloquial_manifest_category_min_accuracy_threshold():
    from src.evals.audit.manifest import load_manifest
    manifest = load_manifest()
    config = manifest.categories["colloquial"]
    assert config.min_accuracy == 0.85
    assert config.status == "gating"


def test_colloquial_baseline_drift_detected_with_empty_live_results():
    """Empty live results that diverge from expected should trigger drift + block CI."""
    snapshot = build_gate_snapshot(colloquial_live_results={})
    ch = snapshot["colloquial_health"]
    assert ch["baseline_drifted"] is True
    assert ch["overall_f1"] < ch["expected_baseline_f1"]
    assert ch["status"] == "failing"
    assert ch["blocks_ci"] is True
    cat = snapshot["categories"]["colloquial"]
    assert cat["meets_thresholds"] is False
    assert cat["blocks_ci"] is True


def test_colloquial_single_field_regression_trips_drift():
    """Dropping one extracted field on one fixture must be detectable."""
    from src.evals.audit.rules.extraction import load_golden_dataset
    fixtures = load_golden_dataset(
        Path("data/fixtures/extraction/colloquial_golden.json")
    )
    target = next(f for f in fixtures if f.fixture_id == "colloq_dest_verb_object_001")
    degraded = {target.fixture_id: {"destination_status": target.expected_extracted_fields["destination_status"]}}
    # All other fixtures keep their expected values; only D1 loses fields.
    live_results = {
        f.fixture_id: (degraded.get(f.fixture_id) or f.expected_extracted_fields)
        for f in fixtures
    }
    snapshot = build_gate_snapshot(colloquial_live_results=live_results)
    ch = snapshot["colloquial_health"]
    assert ch["overall_f1"] < 1.0
    assert ch["baseline_drifted"] is True


def test_colloquial_live_collector_covers_every_fixture():
    """The live collector must produce results for all colloquial fixture ids."""
    from src.evals.audit.rules.extraction import load_golden_dataset
    from src.evals.audit.snapshot import _collect_live_colloquial_results
    fixtures = load_golden_dataset(
        Path("data/fixtures/extraction/colloquial_golden.json")
    )
    live = _collect_live_colloquial_results()
    assert {f.fixture_id for f in fixtures} <= set(live)
    # Whitelist fields are always present in each mapped result.
    first = next(iter(live.values()))
    assert "destination_candidates" in first
    assert "party_size" in first


def test_build_gate_snapshot_hybrid_degraded_parity_and_promotion_gate():
    """ADR-008 §7 item 2: the D6 snapshot grades the degraded-mode authority
    invariant and embeds the machine-readable gap_decision promotion gate."""
    import os

    from src.evals.audit.hybrid_parity import collect_hybrid_parity
    from src.evals.audit.snapshot import DEFAULT_SCENARIO_FIXTURES_PATH

    snapshot = build_gate_snapshot()
    # hybrid_config travels on scenario_health (X-09's vehicle); the
    # categories["gap_decision"] view is a field allowlist without it.
    hybrid_config = snapshot["scenario_health"].get("hybrid_config") or {}

    parity = hybrid_config.get("degraded_parity")
    assert isinstance(parity, dict), "hybrid_config.degraded_parity missing"
    assert parity.get("credential_safe") is True
    assert parity.get("parity") == "pass", (
        f"degraded parity failed: divergent={parity.get('divergent_scenarios')}"
    )
    assert parity.get("scenarios_compared", 0) > 0

    gate = hybrid_config.get("promotion_gate")
    assert isinstance(gate, dict), "hybrid_config.promotion_gate missing"
    assert gate.get("category") == "gap_decision"
    assert gate.get("current") == "shadow"
    condition_ids = {c["id"] for c in gate.get("conditions", [])}
    assert {
        "degraded_parity_pass",
        "provider_lane_kdd_grade",
        "pii_egress_authorized",
    } <= condition_ids
    parity_condition = next(
        c for c in gate["conditions"] if c["id"] == "degraded_parity_pass"
    )
    assert parity_condition["met"] is (parity.get("parity") == "pass")

    # The collector itself must be credential-safe and restore the env.
    fake_key = "test-key-not-real"
    os.environ["OPENAI_API_KEY"] = fake_key
    try:
        record = collect_hybrid_parity(DEFAULT_SCENARIO_FIXTURES_PATH)
        assert os.environ.get("OPENAI_API_KEY") == fake_key, "env not restored"
    finally:
        os.environ.pop("OPENAI_API_KEY", None)
    assert record["parity"] == "pass"
    assert record["scenarios_compared"] > 0
