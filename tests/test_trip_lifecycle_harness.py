"""Trip-lifecycle distribution harness tests (Addendum 8 graduation gate)."""

from spine_api.core import trip_lifecycle_harness as harness
from spine_api.core import trip_lifecycle as tl


def setup_function():
    harness._LEDGER.raised.clear()
    harness._LEDGER.reviewed_keep_logged.clear()


def test_distribution_report_ranks_and_shares():
    report = harness.distribution_report(
        {"planning->completed": 8, "intake->booked": 2},
        status_counts={"new": 40, "in_progress": 10},
    )
    assert report["violation_total"] == 10
    assert report["violation_classes"][0]["class"] == "planning->completed"
    assert report["violation_classes"][0]["share"] == 0.8
    assert report["status_distribution"] == {"new": 40, "in_progress": 10}


def test_graduation_flips_enforcement_only_via_review():
    counts = {"planning->completed": 9}
    assert harness.graduation_ready(counts) == ["planning->completed"]
    # before review: still logged
    assert not harness.should_raise("planning->completed")
    harness.graduate_class("planning->completed", "review: fabricated jump seen in prod data")
    assert harness.should_raise("planning->completed")
    report = harness.distribution_report(counts)
    entry = report["violation_classes"][0]
    assert entry["enforcement"] == "raise"
    assert "review" in entry["review_note"]


def test_keep_logged_records_the_why():
    harness.keep_logged("new->booked", "operator hand-fix pattern; data is clean")
    assert not harness.should_raise("new->booked")
    assert harness._LEDGER.reviewed_keep_logged["new->booked"].startswith("operator")


def test_graduation_ready_threshold():
    assert harness.graduation_ready({"a->b": 4}, min_samples=5) == []
    assert harness.graduation_ready({"a->b": 5}, min_samples=5) == ["a->b"]


def test_machine_gate_still_classifies_for_the_harness():
    assessment = tl.assess_transition("new", "completed")
    assert assessment.verdict == "log"
    assert assessment.old_state == "intake" and assessment.new_state == "completed"
