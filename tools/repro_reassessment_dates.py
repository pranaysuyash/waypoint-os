"""Isolated repro for FND-0368: reassessment date-dependent recompute.

Run from the repo root: `uv run python tools/repro_reassessment_dates.py`
Verdict (2026-10-25): PASSES in isolation — date_start/date_end recomputed
correctly from the date_window correction. The pytest-session failure is
environment- or test-order-dependent (conftest env, noop-extractor gating,
or pollution from earlier tests in the same file). Next: bisect the pytest
env delta (DATA_PRIVACY_MODE / RUNNING_TESTS / extractor monkeypatches).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.intake.extractors import ExtractionPipeline
from src.intake.fact_overrides import record_fact_override
from src.intake.packet_models import SourceEnvelope
from spine_api.services.trip_lifecycle_service import build_reassessment_envelope_from_trip

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
print("date_start:", getattr(date_start, "value", "MISSING"))
assert date_start is not None and str(date_start.value).startswith("2027-06-10"), (
    f"FND-0368 repro FAILED: date_start={date_start}"
)
print("repro OK — pipeline behaves correctly in isolation")
