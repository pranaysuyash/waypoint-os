"""Head-hash anchoring tests — EXPLORE #5 / topic 51a hardening item (gap 1).

Pins: record_head_anchor writes the verify_chain head to the witness file;
detect_anchor_divergence catches (a) chain shrink after anchoring and
(b) in-place head rewrite at unchanged count; growth and no-anchor cases are
not divergent.
"""

import json

from spine_api.persistence import AuditStore
from spine_api.services import audit_head_anchor as aha


def test_record_head_anchor_writes_the_witness(tmp_path, monkeypatch):
    anchor_file = tmp_path / "anchors.jsonl"
    monkeypatch.setattr(aha, "ANCHOR_FILE", anchor_file)
    monkeypatch.setattr(
        AuditStore, "verify_chain",
        staticmethod(lambda: {"valid": True, "event_count": 10, "head_hash": "HEAD-1", "errors": []}),
    )

    entry = aha.record_head_anchor()

    assert entry["head_hash"] == "HEAD-1"
    assert entry["event_count"] == 10
    assert anchor_file.exists()
    saved = json.loads(anchor_file.read_text().splitlines()[-1])
    assert saved["head_hash"] == "HEAD-1"
    assert "anchored_at" in saved


def test_chain_shrink_after_anchoring_is_detected(tmp_path, monkeypatch):
    monkeypatch.setattr(aha, "ANCHOR_FILE", tmp_path / "anchors.jsonl")
    monkeypatch.setattr(
        AuditStore, "verify_chain",
        staticmethod(lambda: {"valid": True, "event_count": 100, "head_hash": "HEAD-100", "errors": []}),
    )
    aha.record_head_anchor()
    # Attacker rewrote history: chain now shorter, different head.
    monkeypatch.setattr(
        AuditStore, "verify_chain",
        staticmethod(lambda: {"valid": True, "event_count": 40, "head_hash": "HEAD-FAKE", "errors": []}),
    )

    verdict = aha.detect_anchor_divergence()

    assert verdict["diverged"] is True
    assert "shrank" in verdict["reason"]


def test_in_place_rewrite_at_unchanged_count_is_detected(tmp_path, monkeypatch):
    monkeypatch.setattr(aha, "ANCHOR_FILE", tmp_path / "anchors.jsonl")
    monkeypatch.setattr(
        AuditStore, "verify_chain",
        staticmethod(lambda: {"valid": True, "event_count": 100, "head_hash": "HEAD-100", "errors": []}),
    )
    aha.record_head_anchor()
    # Same count, different head = events substituted in place.
    monkeypatch.setattr(
        AuditStore, "verify_chain",
        staticmethod(lambda: {"valid": True, "event_count": 100, "head_hash": "HEAD-SWAPPED", "errors": []}),
    )

    verdict = aha.detect_anchor_divergence()

    assert verdict["diverged"] is True
    assert "in-place rewrite" in verdict["reason"]


def test_growth_and_no_anchor_are_not_divergent(tmp_path, monkeypatch):
    monkeypatch.setattr(aha, "ANCHOR_FILE", tmp_path / "anchors.jsonl")

    # No anchor file at all.
    assert aha.detect_anchor_divergence({"head_hash": "H", "event_count": 5})["diverged"] is False

    # Legitimate growth after anchoring.
    monkeypatch.setattr(
        AuditStore, "verify_chain",
        staticmethod(lambda: {"valid": True, "event_count": 100, "head_hash": "HEAD-100", "errors": []}),
    )
    aha.record_head_anchor()
    monkeypatch.setattr(
        AuditStore, "verify_chain",
        staticmethod(lambda: {"valid": True, "event_count": 150, "head_hash": "HEAD-150", "errors": []}),
    )
    verdict = aha.detect_anchor_divergence()
    assert verdict["diverged"] is False
