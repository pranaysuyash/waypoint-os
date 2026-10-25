"""FND-0368 environment bisect: run the verified repro AS a pytest test.

If this fails under pytest but the identical code passes standalone
(tools/repro_reassessment_dates.py), the delta is pytest-session state
(conftest imports, plugin env, or collector-order pollution) — not the
pipeline. Pin the divergence before fixing anything.
"""

from src.intake.extractors import ExtractionPipeline
from src.intake.fact_overrides import record_fact_override
from src.intake.packet_models import SourceEnvelope
from spine_api.services.trip_lifecycle_service import build_reassessment_envelope_from_trip


def test_fnd0368_repro_under_pytest():
    facts = {}
    record_fact_override(facts, "budget", "USD 2500 total", source_ref="budget_correction")
    record_fact_override(facts, "dates", "10 June 2027 to 17 June 2027", source_ref="dates_correction")
    trip = {"id": "correction_deps", "extracted": {"facts": facts}}

    envelopes = [
        SourceEnvelope.from_freeform(
            "Two adults traveling from Mumbai to Italy, 1 May 2026 to 5 May 2026, budget INR 100000 total."
        ),
        build_reassessment_envelope_from_trip(trip),
    ]
    packet = ExtractionPipeline().extract(envelopes)

    date_start = packet.facts.get("date_start")
    assert date_start is not None, (
        f"date_start missing under pytest — packet.facts keys: {sorted(packet.facts.keys())}"
    )
    assert str(date_start.value).startswith("2027-06-10")
