#!/usr/bin/env python3
"""
CanonicalPacket Fixtures for NB02 → NB03 Policy-Only Testing

These are hand-crafted packets that bypass NB01 extraction.
They test decision logic, contradiction routing, branch generation,
and internal/external boundary integrity.

Usage:
    from data.fixtures.packet_fixtures import PACKET_FIXTURES
    fixture = PACKET_FIXTURES["ask_missing_destination"]
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'notebooks'))

# Load NB02 models
from importlib import util as import_util

def _load_nb02_models():
    spec = import_util.spec_from_file_location(
        "nb02_models",
        os.path.join(os.path.dirname(__file__), '..', '..', 'notebooks', 'test_02_comprehensive.py')
    )
    # Instead of importing the test runner, define the models directly here
    # to avoid circular dependencies
    from dataclasses import dataclass, asdict, field
    from datetime import datetime
    from typing import List, Dict, Any, Optional
    from enum import IntEnum

    class AuthorityLevel(IntEnum):
        MANUAL_OVERRIDE = 1
        EXPLICIT_USER = 2
        IMPORTED_STRUCTURED = 3
        EXPLICIT_OWNER = 4
        DERIVED_SIGNAL = 5
        SOFT_HYPOTHESIS = 6
        UNKNOWN = 7

    @dataclass
    class EvidenceRef:
        ref_id: str
        envelope_id: str
        evidence_type: str
        excerpt: str
        field_path: Optional[str] = None
        offset: Optional[Dict[str, int]] = None
        confidence: float = 1.0
        metadata: Dict[str, Any] = field(default_factory=dict)

    @dataclass
    class Slot:
        value: Any = None
        confidence: float = 0.0
        authority_level: str = "unknown"
        extraction_mode: str = "unknown"
        evidence_refs: List[EvidenceRef] = field(default_factory=list)
        updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
        notes: Optional[str] = None

    @dataclass
    class UnknownField:
        field_name: str
        reason: str
        attempted_at: Optional[str] = None
        notes: Optional[str] = None

    @dataclass
    class CanonicalPacket:
        packet_id: str
        created_at: str
        last_updated: str
        facts: Dict[str, Slot] = field(default_factory=dict)
        derived_signals: Dict[str, Slot] = field(default_factory=dict)
        hypotheses: Dict[str, Slot] = field(default_factory=dict)
        unknowns: List[UnknownField] = field(default_factory=list)
        contradictions: List[Dict[str, Any]] = field(default_factory=list)
        source_envelope_ids: List[str] = field(default_factory=list)
        stage: str = "discovery"

    return Slot, EvidenceRef, UnknownField, CanonicalPacket


# Build models once
_Slot, _EvidenceRef, _UnknownField, _CanonicalPacket = _load_nb02_models()

def S(value, conf=0.9, auth="explicit_user", evidence=None):
    """Shorthand for Slot creation."""
    refs = []
    if evidence:
        refs.append(_EvidenceRef(
            ref_id=evidence.get("ref", "ref_001"),
            envelope_id=evidence.get("env", "env_001"),
            evidence_type=evidence.get("type", "text_span"),
            excerpt=evidence.get("excerpt", str(value)),
        ))
    return _Slot(value=value, confidence=conf, authority_level=auth, evidence_refs=refs)

def P(**kwargs):
    """Shorthand for CanonicalPacket creation."""
    kwargs.setdefault("packet_id", "fixture")
    kwargs.setdefault("created_at", "now")
    kwargs.setdefault("last_updated", "now")
    kwargs.setdefault("stage", "discovery")
    return _CanonicalPacket(**kwargs)


PACKET_FIXTURES = {

    # ============================================================
    # ASK_FOLLOWUP (8-10 fixtures)
    # ============================================================

    "ask_empty": {
        "fixture_id": "ask_empty",
        "category": "ask_followup",
        "packet": P(
            packet_id="ask_empty",
            facts={},
            hypotheses={},
        ),
        "expected": {
            "decision_state": "ASK_FOLLOWUP",
            "hard_blockers": ["destination_city", "origin_city", "travel_dates", "traveler_count"],
            "soft_blockers": ["budget_range", "trip_purpose", "traveler_preferences"],
            "question_count_min": 4,
        },
    },

    "ask_missing_destination": {
        "fixture_id": "ask_missing_destination",
        "category": "ask_followup",
        "packet": P(
            packet_id="ask_no_dest",
            facts={
                "origin_city": S("Bangalore"),
                "travel_dates": S("March 2026"),
                "traveler_count": S(3),
            },
        ),
        "expected": {
            "decision_state": "ASK_FOLLOWUP",
            "hard_blockers": ["destination_city"],
            "question_count_min": 1,
        },
    },

    "ask_missing_dates": {
        "fixture_id": "ask_missing_dates",
        "category": "ask_followup",
        "packet": P(
            packet_id="ask_no_dates",
            facts={
                "origin_city": S("Bangalore"),
                "destination_city": S("Singapore"),
                "traveler_count": S(4),
            },
        ),
        "expected": {
            "decision_state": "ASK_FOLLOWUP",
            "hard_blockers": ["travel_dates"],
            "question_count_min": 1,
        },
    },

    "ask_only_origin": {
        "fixture_id": "ask_only_origin",
        "category": "ask_followup",
        "packet": P(
            packet_id="ask_only_origin",
            facts={
                "origin_city": S("Bangalore", auth="explicit_owner"),
            },
        ),
        "expected": {
            "decision_state": "ASK_FOLLOWUP",
            "hard_blockers": ["destination_city", "travel_dates", "traveler_count"],
            "question_count_min": 3,
        },
    },

    "ask_budget_only": {
        "fixture_id": "ask_budget_only",
        "category": "ask_followup",
        "packet": P(
            packet_id="ask_budget",
            facts={
                "origin_city": S("Bangalore"),
                "destination_city": S("Goa"),
                "traveler_count": S(2),
                "budget_range": S("50000", auth="explicit_owner"),
            },
        ),
        "expected": {
            "decision_state": "ASK_FOLLOWUP",
            "hard_blockers": ["travel_dates"],
            "question_count_min": 1,
        },
    },

    "ask_post_contradiction": {
        "fixture_id": "ask_post_contradiction",
        "category": "ask_followup",
        "packet": P(
            packet_id="ask_contra",
            facts={
                "origin_city": S("Bangalore"),
                "traveler_count": S(3),
            },
            contradictions=[
                {"field_name": "destination_city", "values": ["Singapore", "Thailand"], "sources": ["env1", "env2"]},
            ],
        ),
        "expected": {
            "decision_state": "ASK_FOLLOWUP",
            "hard_blockers": ["destination_city", "travel_dates"],
        },
    },

    "ask_hypothesis_only_destination": {
        "fixture_id": "ask_hypothesis_only_destination",
        "category": "ask_followup",
        "packet": P(
            packet_id="ask_hyp_dest",
            facts={
                "origin_city": S("Bangalore"),
                "travel_dates": S("March 2026"),
                "traveler_count": S(4),
            },
            hypotheses={
                "destination_city": S("Singapore", conf=0.5, auth="soft_hypothesis"),
            },
        ),
        "expected": {
            "decision_state": "ASK_FOLLOWUP",
            "hard_blockers": ["destination_city"],  # Hypothesis doesn't fill
            "question_count_min": 1,
        },
    },

    "ask_composition_unknown": {
        "fixture_id": "ask_composition_unknown",
        "category": "proceed_internal_draft",
        "packet": P(
            packet_id="ask_composition",
            facts={
                "origin_city": S("Delhi"),
                "destination_city": S("Europe"),
                "travel_dates": S("June-July"),
                "traveler_count": S("big family", conf=0.4, auth="explicit_owner"),
            },
        ),
        "expected": {
            "decision_state": "PROCEED_INTERNAL_DRAFT",
            "hard_blockers": [],
            "soft_blockers": ["budget_range", "trip_purpose", "traveler_preferences"],
        },
    },

    # ============================================================
    # PROCEED_TRAVELER_SAFE (4-5 fixtures)
    # ============================================================

    "proceed_complete_discovery": {
        "fixture_id": "proceed_complete_discovery",
        "category": "proceed_traveler_safe",
        "packet": P(
            packet_id="proceed_complete",
            facts={
                "origin_city": S("Bangalore", conf=0.95, auth="explicit_user"),
                "destination_city": S("Singapore", conf=0.95, auth="explicit_user"),
                "travel_dates": S("2026-03-15 to 2026-03-22", conf=0.9, auth="explicit_user"),
                "traveler_count": S(3, conf=0.95, auth="explicit_user"),
                "budget_range": S("250000", conf=0.85, auth="explicit_user"),
                "trip_purpose": S("family leisure", conf=0.85, auth="explicit_user"),
                "traveler_preferences": S("kid-friendly", conf=0.8, auth="explicit_user"),
            },
        ),
        "expected": {
            "decision_state": "PROCEED_TRAVELER_SAFE",
            "hard_blockers": [],
            "soft_blockers": [],
            "nb03_behavior": "Generate traveler-ready proposal. Direct tone. No hedging.",
        },
    },

    "proceed_manual_override": {
        "fixture_id": "proceed_manual_override",
        "category": "proceed_traveler_safe",
        "packet": P(
            packet_id="proceed_manual",
            facts={
                "origin_city": S("Bangalore", conf=1.0, auth="manual_override"),
                "destination_city": S("Maldives", conf=1.0, auth="manual_override"),
                "travel_dates": S("2026-05-01 to 2026-05-07", conf=1.0, auth="manual_override"),
                "traveler_count": S(2, conf=1.0, auth="manual_override"),
                "budget_range": S("400000", conf=1.0, auth="manual_override"),
                "trip_purpose": S("honeymoon", conf=1.0, auth="manual_override"),
                "traveler_preferences": S("5-star resort", conf=1.0, auth="manual_override"),
            },
        ),
        "expected": {
            "decision_state": "PROCEED_TRAVELER_SAFE",
            "hard_blockers": [],
            "soft_blockers": [],
        },
    },

    "proceed_derived_destination": {
        "fixture_id": "proceed_derived_destination",
        "category": "proceed_traveler_safe",
        "packet": P(
            packet_id="proceed_derived",
            facts={
                "origin_city": S("Bangalore", conf=0.9, auth="explicit_user"),
                "travel_dates": S("2026-04-01 to 2026-04-07", conf=0.85, auth="explicit_user"),
                "traveler_count": S(3, conf=0.9, auth="explicit_user"),
                "budget_range": S("300000", conf=0.8, auth="explicit_user"),
                "trip_purpose": S("beach vacation", conf=0.8, auth="explicit_user"),
                "traveler_preferences": S("beaches, water sports", conf=0.75, auth="explicit_user"),
            },
            derived_signals={
                "destination_city": S("Andaman", conf=0.7, auth="derived_signal",
                    evidence={"ref": "ref_derived", "env": "env_prefs", "type": "derived",
                              "excerpt": "beach vacation + water sports + budget fits Andaman"}),
            },
        ),
        "expected": {
            "decision_state": "PROCEED_TRAVELER_SAFE",
            "hard_blockers": [],
            "soft_blockers": [],
        },
    },

    # ============================================================
    # PROCEED_INTERNAL_DRAFT (3-4 fixtures)
    # ============================================================

    "draft_soft_blockers_only": {
        "fixture_id": "draft_soft_blockers_only",
        "category": "proceed_internal_draft",
        "packet": P(
            packet_id="draft_soft",
            facts={
                "origin_city": S("Bangalore"),
                "destination_city": S("Singapore"),
                "travel_dates": S("March 2026"),
                "traveler_count": S(3),
            },
        ),
        "expected": {
            "decision_state": "PROCEED_INTERNAL_DRAFT",
            "hard_blockers": [],
            "soft_blockers": ["budget_range", "trip_purpose", "traveler_preferences"],
            "nb03_behavior": "Generate internal draft with assumptions listed. NOT for traveler.",
        },
    },

    "draft_low_confidence": {
        "fixture_id": "draft_low_confidence",
        "category": "proceed_internal_draft",
        "packet": P(
            packet_id="draft_low",
            facts={
                "origin_city": S("Mumbai", conf=0.5, auth="explicit_owner"),
                "destination_city": S("Dubai", conf=0.5, auth="explicit_owner"),
                "travel_dates": S("sometime in May", conf=0.4, auth="explicit_owner"),
                "traveler_count": S("maybe 4 or 5", conf=0.4, auth="explicit_owner"),
                "budget_range": S("around 3L", conf=0.5, auth="explicit_owner"),
                "trip_purpose": S("family trip", conf=0.5, auth="explicit_owner"),
                "traveler_preferences": S("something nice", conf=0.3, auth="explicit_owner"),
            },
        ),
        "expected": {
            "decision_state": "PROCEED_INTERNAL_DRAFT",
            "hard_blockers": [],
            "soft_blockers": [],
            "nb03_behavior": "Internal draft with cautious tone. All values are vague.",
        },
    },

    "draft_budget_stretch": {
        "fixture_id": "draft_budget_stretch",
        "category": "proceed_traveler_safe",
        "packet": P(
            packet_id="draft_stretch",
            facts={
                "origin_city": S("Bangalore"),
                "destination_city": S("Singapore"),
                "travel_dates": S("April 2026"),
                "traveler_count": S(4),
                "budget_range": S("200000 (can stretch)", conf=0.7, auth="explicit_owner"),
                "trip_purpose": S("family leisure"),
                "traveler_preferences": S("good hotels"),
            },
        ),
        "expected": {
            "decision_state": "PROCEED_TRAVELER_SAFE",
            "hard_blockers": [],
            "soft_blockers": [],
        },
    },

    # ============================================================
    # BRANCH_OPTIONS (2-3 fixtures)
    # ============================================================

    "branch_budget_contradiction": {
        "fixture_id": "branch_budget_contradiction",
        "category": "branch_options",
        "packet": P(
            packet_id="branch_budget",
            facts={
                "origin_city": S("Bangalore"),
                "destination_city": S("Maldives"),
                "travel_dates": S("2026-06-01 to 2026-06-07"),
                "traveler_count": S(2),
                "budget_range": S(
                    value=["budget", "premium"],
                    conf=0.6,
                    auth="explicit_owner",
                    evidence={"ref": "ref1", "env": "env_husband", "type": "text_span", "excerpt": "budget trip"},
                ),
            },
            contradictions=[
                {"field_name": "budget_range", "values": ["budget", "premium"], "sources": ["env_husband", "env_wife"]},
            ],
        ),
        "expected": {
            "decision_state": "BRANCH_OPTIONS",
            "hard_blockers": [],
            "nb03_behavior": "Present budget options neutrally. Option A: budget Maldives. Option B: premium Maldives.",
        },
    },

    "branch_destination_ambiguity": {
        "fixture_id": "branch_destination_ambiguity",
        "category": "branch_options",
        "packet": P(
            packet_id="branch_dest",
            facts={
                "origin_city": S("Mumbai"),
                "destination_city": S("Andaman or Sri Lanka", conf=0.6, auth="explicit_owner"),
                "travel_dates": S("May 2026"),
                "traveler_count": S(2),
                "budget_range": S("200000"),
            },
            contradictions=[
                {"field_name": "destination_city", "values": ["Andaman", "Sri Lanka"], "sources": ["env_notes"]},
            ],
        ),
        "expected": {
            "decision_state": "ASK_FOLLOWUP",  # Destination contradiction is critical → ASK
            "hard_blockers": [],
            "nb03_behavior": "ASK_FOLLOWUP due to destination contradiction. Ask: 'Andaman or Sri Lanka?'",
        },
    },

    # ============================================================
    # STOP_NEEDS_REVIEW (2-3 fixtures)
    # ============================================================

    "stop_date_contradiction": {
        "fixture_id": "stop_date_contradiction",
        "category": "stop_needs_review",
        "packet": P(
            packet_id="stop_date",
            facts={
                "origin_city": S("Bangalore"),
                "destination_city": S("Singapore"),
                "traveler_count": S(3),
                "travel_dates": S(
                    value=["2026-03-15", "2026-04-01"],
                    conf=0.6,
                    auth="explicit_owner",
                ),
            },
            contradictions=[
                {"field_name": "travel_dates", "values": ["2026-03-15", "2026-04-01"], "sources": ["env1", "env2"]},
            ],
        ),
        "expected": {
            "decision_state": "STOP_NEEDS_REVIEW",
            "nb03_behavior": "STOP. Date contradiction. Generate human review briefing. Agent must NOT call.",
        },
    },

    "stop_multiple_critical": {
        "fixture_id": "stop_multiple_critical",
        "category": "stop_needs_review",
        "packet": P(
            packet_id="stop_multi",
            facts={
                "origin_city": S("Bangalore"),
                "destination_city": S("Singapore"),
                "traveler_count": S(3),
                "travel_dates": S(
                    value=["2026-03-15", "2026-04-01"],
                    conf=0.5,
                    auth="explicit_owner",
                ),
            },
            contradictions=[
                {"field_name": "travel_dates", "values": ["2026-03-15", "2026-04-01"], "sources": ["env1", "env2"]},
                {"field_name": "destination_city", "values": ["Singapore", "Thailand"], "sources": ["env1", "env3"]},
            ],
        ),
        "expected": {
            "decision_state": "STOP_NEEDS_REVIEW",
            "nb03_behavior": "STOP. Multiple critical contradictions. Date + destination conflict.",
        },
    },

    "stop_empty_no_facts": {
        "fixture_id": "stop_empty_no_facts",
        "category": "stop_needs_review",
        "packet": P(
            packet_id="stop_empty",
            facts={},
            contradictions=[
                {"field_name": "travel_dates", "values": ["March", "April"], "sources": ["env1", "env2"]},
                {"field_name": "destination_city", "values": ["Singapore", "Thailand"], "sources": ["env1", "env2"]},
            ],
        ),
        "expected": {
            "decision_state": "STOP_NEEDS_REVIEW",
            "nb03_behavior": "STOP. No facts + 2 core contradictions. Data too inconsistent.",
        },
    },
}

# Utility: Get fixtures by category
def get_fixtures_by_category(category: str) -> dict:
    return {k: v for k, v in PACKET_FIXTURES.items() if v["category"] == category}

# Utility: Get all fixture IDs
def get_all_fixture_ids() -> list:
    return list(PACKET_FIXTURES.keys())

# Utility: Print fixture summary
def print_summary():
    categories = {}
    for fid, f in PACKET_FIXTURES.items():
        cat = f["category"]
        categories.setdefault(cat, []).append(fid)
    print(f"Total packet fixtures: {len(PACKET_FIXTURES)}")
    for cat, ids in categories.items():
        print(f"  {cat}: {len(ids)}")
        for i in ids:
            print(f"    - {i}")
