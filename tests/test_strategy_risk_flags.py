from src.intake.strategy import _extract_risk_flags


def test_extract_risk_flags_dedupes_repeated_messages():
    risk_flags = [
        "Internal data present (internal-only owner constraints) — ensure traveler-safe boundary",
        "Internal data present (internal-only owner constraints) — ensure traveler-safe boundary",
        {"flag": "Critical activity suitability flags require operator review before traveler-facing output."},
    ]

    assert _extract_risk_flags(risk_flags) == [
        "Internal data present (internal-only owner constraints) — ensure traveler-safe boundary",
        "Critical activity suitability flags require operator review before traveler-facing output.",
    ]
