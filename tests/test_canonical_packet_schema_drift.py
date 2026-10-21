"""Canonical packet schema drift guard (2026-09-18, gap-assessment residual).

specs/canonical_packet.schema.json declares itself the mirror of
CanonicalPacket.to_dict(). Nothing previously enforced that — the F-37 fix
added `assumptions` to to_dict() without updating the schema, and no test
would have caught the next occurrence. This guard pins the mirror contract.

Rule: every key emitted by to_dict() must be a schema property, and vice
versa. Fields deliberately excluded from serialization (raw_note, feedback,
suitability_flags) are absent from both sides and therefore need no
allowlist — the to_dict()-key set is the single source of truth.
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.intake.packet_models import CanonicalPacket

SCHEMA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "specs", "canonical_packet.schema.json"
)


def _to_dict_keys() -> set:
    pkt = CanonicalPacket(packet_id="schema_drift_probe")
    return set(pkt.to_dict().keys())


def _schema_property_keys() -> set:
    with open(SCHEMA_PATH) as f:
        return set(json.load(f)["properties"].keys())


def test_schema_mirrors_runtime_to_dict_exactly():
    runtime_keys = _to_dict_keys()
    schema_keys = _schema_property_keys()
    missing_from_schema = runtime_keys - schema_keys
    extra_in_schema = schema_keys - runtime_keys
    assert not missing_from_schema, (
        f"Runtime to_dict() emits keys missing from canonical_packet.schema.json "
        f"(update specs/canonical_packet.schema.json in the same change): "
        f"{sorted(missing_from_schema)}"
    )
    assert not extra_in_schema, (
        f"canonical_packet.schema.json declares properties the runtime never "
        f"serializes (stale schema or missing to_dict key): {sorted(extra_in_schema)}"
    )


def test_schema_version_marker_matches_runtime():
    with open(SCHEMA_PATH) as f:
        schema = json.load(f)
    runtime_version = CanonicalPacket(packet_id="v_probe").schema_version
    assert schema.get("description", "") + schema.get("title", "")  # sanity: file loaded
    # The schema header names the runtime version; keep the two honest.
    header_text = json.dumps({k: v for k, v in schema.items() if k != "properties"})
    assert runtime_version in header_text, (
        f"Schema header does not cite the runtime schema_version "
        f"{runtime_version!r} — bump the schema header in the same change."
    )


def test_trip_response_surfaces_traveler_answers_from_extra_folding():
    """FND-0307 regression pin: recorded traveler answers must reach the API
    response even when the backend folds them into analytics._extra (4th
    silent-strip instance — same class as branch_options/passenger_claim)."""
    import importlib

    contract = importlib.import_module("spine_api.contract")
    trip = {
        "id": "t_fnd0307",
        "status": "incomplete",
        "analytics": {
            "_extra": {
                "traveler_answers": [
                    {"field_name": "origin_city", "answer": "Mumbai",
                     "authority_level": "explicit_user"}
                ]
            }
        },
    }
    resp = contract.TripResponse.from_dict(trip)
    assert resp.traveler_answers and resp.traveler_answers[0]["field_name"] == "origin_city"
    # Top-level form also surfaces (column-backed stores).
    resp2 = contract.TripResponse.from_dict({**trip, "traveler_answers": [{"field_name": "x"}], "analytics": {}})
    assert resp2.traveler_answers[0]["field_name"] == "x"
