"""T9 (FND-0232): deterministic confirmation content grading.

The registration defect: confirmations with missing segments or mismatched
passenger names passed ungraded and fed retry loops. The grader grades at
read: incomplete = expected structural content absent; defective = present
content contradicts the trip. Deterministic only — no LLM in this path.
"""

from spine_api.services.confirmation_grader import grade_confirmation_content

TRIP = {
    "id": "trip_grade_1",
    "packet": {
        "customer_name": "Meera Sharma",
        "facts": {
            "travelers": {
                "value": [
                    {"name": "Meera Sharma", "constraints": []},
                    {"name": "Dev Patel", "constraints": []},
                ],
            },
        },
    },
}


def test_clean_flight_confirmation():
    grade = grade_confirmation_content(
        confirmation_type="flight",
        content={
            "supplier_name": "IndiGo",
            "confirmation_number": "PNR-AB12CD",
            "segments": [{"flight_number": "6E 123", "date": "2026-12-15"}],
            "passengers": ["Meera Sharma", "Dev Patel"],
        },
        trip=TRIP,
    )
    assert grade.grade == "clean"
    assert grade.issues == []


def test_missing_flight_segments_is_incomplete():
    grade = grade_confirmation_content(
        confirmation_type="flight",
        content={"supplier_name": "IndiGo", "confirmation_number": "PNR-XY99"},
        trip=TRIP,
    )
    assert grade.grade == "incomplete"
    assert any(i.code == "missing_segments" for i in grade.issues)


def test_passenger_name_mismatch_is_defective():
    grade = grade_confirmation_content(
        confirmation_type="flight",
        content={
            "supplier_name": "IndiGo",
            "confirmation_number": "PNR-AB12CD",
            "segments": [{"flight_number": "6E 123", "date": "2026-12-15"}],
            "passengers": ["Meera Sharma", "Riya Kapoor"],
        },
        trip=TRIP,
    )
    assert grade.grade == "defective"
    assert any(i.code == "passenger_name_mismatch" and "Riya Kapoor" in i.detail for i in grade.issues)


def test_name_order_and_titles_tolerated():
    grade = grade_confirmation_content(
        confirmation_type="flight",
        content={
            "supplier_name": "IndiGo",
            "confirmation_number": "PNR-AB12CD",
            "segments": [{"flight_number": "6E 123", "date": "2026-12-15"}],
            "passengers": ["Sharma Meera M", "Mr Dev Patel"],
        },
        trip=TRIP,
    )
    assert grade.grade == "clean"


def test_missing_hotel_guests_is_incomplete():
    grade = grade_confirmation_content(
        confirmation_type="hotel",
        content={"supplier_name": "Taj", "confirmation_number": "BK-77"},
        trip=TRIP,
    )
    assert grade.grade == "incomplete"
    assert any(i.code == "missing_guests" for i in grade.issues)


def test_no_identity_at_all_is_incomplete():
    grade = grade_confirmation_content(
        confirmation_type="insurance",
        content={"notes": "some note"},
        trip=TRIP,
    )
    assert grade.grade == "incomplete"
    assert any(i.code == "missing_identity" for i in grade.issues)


def test_types_without_structural_crosscheck_can_be_clean():
    grade = grade_confirmation_content(
        confirmation_type="insurance",
        content={"supplier_name": "Allianz", "confirmation_number": "POL-1"},
        trip=TRIP,
    )
    assert grade.grade == "clean"


def test_grade_is_serializable():
    grade = grade_confirmation_content(
        confirmation_type="flight",
        content={"supplier_name": "IndiGo"},
        trip=TRIP,
    )
    payload = grade.to_dict()
    assert payload["grade"] in ("clean", "incomplete", "defective")
    assert isinstance(payload["issues"], list)
    assert all(set(i.keys()) == {"code", "detail"} for i in payload["issues"])
    assert isinstance(payload["checked"], list)
