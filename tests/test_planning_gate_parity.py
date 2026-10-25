"""Cross-stack parity pin: FE planning gate vs backend FIELD_REQUIRED_FOR.

FND-0379: the frontend's quote-stage required-fields list and the backend's
blocking-field vocabulary were derived independently, so they could drift
(SIM3-D: gate showed 2 missing while backend escalated 1 error). This test
pins the FE's quote-blocking field set onto the backend's canonical
``FIELD_REQUIRED_FOR["fare_quote"]`` — the same parity-gate discipline as the
BFF route-map gate. If either side changes without the other, this fails.
"""

import re
from pathlib import Path

from src.intake.validation import FIELD_REQUIRED_FOR

REPO = Path(__file__).resolve().parents[1]
FE_LIB = REPO / "frontend/src/lib/planning-status.ts"

# FE label -> backend canonical field name (the QUOTE-blocking projection of
# FIELD_REQUIRED_FOR: fare_quote is the stage the planning gate unlocks).
FE_LABEL_TO_FIELD = {
    "Budget range": "budget_raw_text",
    "Origin city": "origin_city",
    "Destination": "destination_candidates",
    "Travel window": "date_window",
    "Traveler count": "party_size",
}


def _fare_quote_required() -> set[str]:
    return {
        field
        for field, ops in FIELD_REQUIRED_FOR.items()
        if "fare_quote" in ops
    }


def test_fe_planning_gate_covers_every_fare_quote_blocker():
    """Every backend fare_quote-blocking field has exactly one FE gate entry."""
    fe_fields = set(FE_LABEL_TO_FIELD.values())
    backend = _fare_quote_required()
    missing_in_fe = backend - fe_fields
    extra_in_fe = fe_fields - backend
    assert not missing_in_fe, (
        f"Backend blocks fare_quote on {sorted(missing_in_fe)} but the FE "
        f"planning gate has no entry — operators see an unlocked stage while "
        f"the pipeline still escalates (FND-0379 drift class)."
    )
    assert not extra_in_fe, (
        f"FE planning gate requires {sorted(extra_in_fe)} which the backend "
        f"does not block fare_quote on — stale FE requirement."
    )


def test_fe_source_labels_match_parity_map():
    """The labels pushed by getRequiredPlanningFields in the TS source must be
    exactly the parity map's keys — editing one side without the other fails
    here instead of drifting silently in production."""
    src = FE_LIB.read_text()
    fn_start = src.index("export function getRequiredPlanningFields")
    fn_end = src.index("export function getRecommendedPlanningFields", fn_start)
    body = src[fn_start:fn_end]
    pushed = set(re.findall(r'requiredFields\.push\("([^"]+)"\)', body))
    assert pushed == set(FE_LABEL_TO_FIELD), (
        f"planning-status.ts pushes {sorted(pushed)} but the parity map covers "
        f"{sorted(FE_LABEL_TO_FIELD)} — update both together (FND-0379)."
    )
