#!/usr/bin/env python3
"""
Raw-Input Fixtures for NB01 → NB02 → NB03 End-to-End Testing

Each fixture is a real messy agency note with expected outcomes.
These test the FULL spine: extraction → decision → session planning.

Usage:
    from data.fixtures.raw_fixtures import RAW_FIXTURES
    fixture = RAW_FIXTURES["clean_family_booking"]
"""

RAW_FIXTURES = {

    # ============================================================
    # CLEAN / HAPPY PATH (3 fixtures)
    # ============================================================

    "clean_family_booking": {
        "fixture_id": "clean_family_booking",
        "source_type": "freeform_text",
        "category": "clean_happy_path",
        "raw_input": (
            "Family of 4 from Bangalore — 2 adults, 2 kids (ages 8 and 12). "
            "Want to go to Singapore, 5 nights, March 15-20. "
            "Budget around 3 lakhs total. They've been to Thailand before and loved it. "
            "Want kid-friendly activities, vegetarian food important. "
            "Both kids have valid passports. Ready to book."
        ),
        "structured_input": None,
        "expected": {
            "extracted_fields": {
                "origin_city": {"value": "Bangalore", "authority": "explicit_owner"},
                "destination_city": {"value": "Singapore", "authority": "explicit_owner"},
                "travel_dates": {"value": "March 15-20", "authority": "explicit_owner"},
                "traveler_count": {"value": 4, "authority": "explicit_owner"},
                "budget_range": {"value": "300000", "authority": "explicit_owner"},
                "traveler_composition": {"value": "2 adults, 2 kids (8, 12)", "authority": "explicit_owner"},
                "traveler_preferences": {"value": "kid-friendly, vegetarian food", "authority": "explicit_owner"},
                "trip_purpose": {"value": "family leisure", "authority": "explicit_owner"},
            },
            "expected_unknowns": [],
            "expected_contradictions": [],
            "nb02_decision_state": "PROCEED_TRAVELER_SAFE",
            "nb02_hard_blockers": [],
            "nb03_behavior": "Generate traveler-ready proposal. Direct tone. No hedging. All fields known.",
        },
    },

    "complete_pilgrimage": {
        "fixture_id": "complete_pilgrimage",
        "source_type": "freeform_text",
        "category": "clean_happy_path",
        "raw_input": (
            "Group of 6 elderly people from Varanasi. "
            "Want to do Char Dham Yatra in Uttarakhand. "
            "September 10-18, 2026. Budget 2 lakhs total. "
            "All have medical conditions — need accessible transport. "
            "Passports not needed (domestic). "
            "Coordinator: Mrs. Sharma, phone verified."
        ),
        "structured_input": None,
        "expected": {
            "extracted_fields": {
                "origin_city": {"value": "Varanasi", "authority": "explicit_owner"},
                "destination_city": {"value": "Char Dham, Uttarakhand", "authority": "explicit_owner"},
                "travel_dates": {"value": "September 10-18, 2026", "authority": "explicit_owner"},
                "traveler_count": {"value": 6, "authority": "explicit_owner"},
                "budget_range": {"value": "200000", "authority": "explicit_owner"},
                "traveler_composition": {"value": "6 elderly", "authority": "explicit_owner"},
                "traveler_preferences": {"value": "accessible transport, medical needs", "authority": "explicit_owner"},
                "trip_purpose": {"value": "pilgrimage", "authority": "explicit_owner"},
            },
            "expected_unknowns": [],
            "expected_contradictions": [],
            "nb02_decision_state": "PROCEED_TRAVELER_SAFE",
            "nb02_hard_blockers": [],
            "nb03_behavior": "Generate proposal. Flag medical/accessibility as risk. Direct tone.",
        },
    },

    "business_shortlist": {
        "fixture_id": "business_shortlist",
        "source_type": "hybrid",
        "category": "clean_happy_path",
        "raw_input": (
            "Tech company offsite. Bangalore team, 15 people. "
            "Goa, 3 nights, first week of May. Budget 5 lakhs. "
            "Need conference room + team activities. "
            "Already shortlisted: Grand Hyatt Goa and Taj Fort Aguada."
        ),
        "structured_input": {
            "traveler_count": 15,
            "destination_city": "Goa",
            "selected_destinations": ["Grand Hyatt Goa", "Taj Fort Aguada"],
        },
        "expected": {
            "extracted_fields": {
                "origin_city": {"value": "Bangalore", "authority": "explicit_owner"},
                "destination_city": {"value": "Goa", "authority": "explicit_owner"},
                "travel_dates": {"value": "First week of May", "authority": "explicit_owner"},
                "traveler_count": {"value": 15, "authority": "imported_structured"},
                "budget_range": {"value": "500000", "authority": "explicit_owner"},
                "selected_destinations": {"value": ["Grand Hyatt Goa", "Taj Fort Aguada"], "authority": "imported_structured"},
                "budget_range": {"value": "500000", "authority": "explicit_owner"},
                "trip_purpose": {"value": "corporate offsite", "authority": "explicit_owner"},
                "traveler_preferences": {"value": "conference room + team activities", "authority": "explicit_owner"},
            },
            "expected_unknowns": [],
            "expected_contradictions": [],
            "nb02_decision_state": "PROCEED_TRAVELER_SAFE",
            "nb02_hard_blockers": [],
            "nb03_behavior": "Generate proposal for shortlisted options. Direct tone.",
        },
    },

    # ============================================================
    # MESSY / UNDER-SPECIFIED (3 fixtures)
    # ============================================================

    "vague_lead": {
        "fixture_id": "vague_lead",
        "source_type": "freeform_text",
        "category": "messy_under_specified",
        "raw_input": (
            "Someone called, wants to go international. "
            "Big family, maybe around March. "
            "Said budget is fine, will call back."
        ),
        "structured_input": None,
        "expected": {
            "extracted_fields": {
                "traveler_composition": {"value": "big family (unknown count)", "authority": "explicit_owner"},
                "travel_dates": {"value": "maybe March", "authority": "explicit_owner"},
            },
            "expected_unknowns": [
                "origin_city",
                "destination_city",
                "traveler_count",
            ],
            "expected_contradictions": [],
            "nb02_decision_state": "ASK_FOLLOWUP",
            "nb02_hard_blockers": ["origin_city", "destination_city", "traveler_count"],
            "nb03_behavior": "Ask 3 critical questions in order: who/where is this, where are they departing from, where do they want to go.",
        },
    },

    "whatsapp_dump": {
        "fixture_id": "whatsapp_dump",
        "source_type": "freeform_text",
        "category": "messy_under_specified",
        "raw_input": (
            "ok so this family from Chennai, 3 of them I think, "
            "want to go somewhere with beaches, kids are young so nothing too adventurous, "
            "husband said they have around 2 lakhs, wife mentioned they can stretch if it's good, "
            "dates flexible around April-May, "
            "they've been to Goa already so don't suggest that, "
            "maybe Andaman or Sri Lanka?"
        ),
        "structured_input": None,
        "expected": {
            "extracted_fields": {
                "origin_city": {"value": "Chennai", "authority": "explicit_owner"},
                "traveler_count": {"value": 3, "authority": "explicit_owner"},
                "budget_range": {"value": "200000 (can stretch)", "authority": "explicit_owner"},
                "travel_dates": {"value": "April-May", "authority": "explicit_owner"},
                "destination_city": {"value": "Andaman or Sri Lanka", "authority": "explicit_owner"},
                "traveler_preferences": {"value": "beaches, nothing too adventurous, young kids", "authority": "explicit_owner"},
                "trip_purpose": {"value": "family beach vacation", "authority": "explicit_owner"},
            },
            "expected_unknowns": [],
            "expected_contradictions": [],
            "nb02_decision_state": "PROCEED_TRAVELER_SAFE",
            "nb02_hard_blockers": [],
            "nb03_behavior": "Proceed but flag ambiguous destination ('Andaman or Sri Lanka'). "
                            "Detect budget stretch signal. Ask for destination clarification after proposal.",
        },
    },

    "partial_crm_entry": {
        "fixture_id": "partial_crm_entry",
        "source_type": "hybrid",
        "category": "messy_under_specified",
        "raw_input": (
            "Reddy family called again. "
            "They want to change their original plan. "
            "Now it's 6 people instead of 4. "
            "Budget still the same though — 3 lakhs."
        ),
        "structured_input": {
            "origin_city": "Bangalore",
            "destination_city": "Singapore",
            "travel_dates": "2026-03-15 to 2026-03-20",
            "traveler_count": 4,  # Old value — contradicts new note
            "budget_range": "300000",
        },
        "expected": {
            "extracted_fields": {
                "origin_city": {"value": "Bangalore", "authority": "imported_structured"},
                "destination_city": {"value": "Singapore", "authority": "imported_structured"},
                "travel_dates": {"value": "2026-03-15 to 2026-03-20", "authority": "imported_structured"},
                "traveler_count": {"value": 6, "authority": "explicit_owner"},  # New overrides old
                "budget_range": {"value": "300000", "authority": "imported_structured"},
            },
            "expected_unknowns": [],
            "expected_contradictions": ["traveler_count_conflict"],
            "nb02_decision_state": "ASK_FOLLOWUP",
            "nb02_hard_blockers": [],
            "nb03_behavior": "ASK_FOLLOWUP due to traveler count contradiction. Ask to confirm: 4 or 6 people?",
        },
    },

    # ============================================================
    # HYBRID CONFLICT (2 fixtures)
    # ============================================================

    "confused_couple": {
        "fixture_id": "confused_couple",
        "source_type": "hybrid",
        "category": "hybrid_conflict",
        "raw_input": (
            "Husband: Singapore, 5 nights, March 15-20, 2 adults, 120k budget. "
            "Wife: Thailand would be better, April 1-6, 2 adults + baby, 200k budget."
        ),
        "structured_input": None,
        "expected": {
            "extracted_fields": {
                "origin_city": {"value": "unknown", "authority": "unknown"},
                "destination_city": {"value": "Singapore/Thailand", "authority": "explicit_owner"},
                "travel_dates": {"value": "March 15-20 OR April 1-6", "authority": "explicit_owner"},
                "traveler_count": {"value": "2 or 3", "authority": "explicit_owner"},
                "budget_range": {"value": "120000 or 200000", "authority": "explicit_owner"},
            },
            "expected_unknowns": ["origin_city"],
            "expected_contradictions": [
                "date_conflict",
                "destination_conflict",
                "budget_conflict",
                "traveler_count_conflict",
            ],
            "nb02_decision_state": "STOP_NEEDS_REVIEW",
            "nb02_hard_blockers": ["origin_city"],
            "nb03_behavior": "STOP. Date contradiction is critical. Generate human review briefing. Agent must NOT call until couple agrees.",
        },
    },

    "crm_update_new_call": {
        "fixture_id": "crm_update_new_call",
        "source_type": "hybrid",
        "category": "hybrid_conflict",
        "raw_input": (
            "Gupta family — they loved Dubai last time! "
            "Now want something new. Family of 4, international, "
            "budget flexible. They said 'surprise us!'"
        ),
        "structured_input": {
            "origin_city": "Bangalore",
            "traveler_count": 4,
            "trip_purpose": "international leisure",
            "budget_range": "flexible",
        },
        "expected": {
            "extracted_fields": {
                "origin_city": {"value": "Bangalore", "authority": "imported_structured"},
                "traveler_count": {"value": 4, "authority": "imported_structured"},
                "budget_range": {"value": "flexible", "authority": "explicit_owner"},
                "trip_purpose": {"value": "international leisure, looking for something new", "authority": "explicit_owner"},
            },
            "expected_unknowns": [
                "destination_city",
                "travel_dates",
            ],
            "expected_contradictions": [],
            "nb02_decision_state": "ASK_FOLLOWUP",
            "nb02_hard_blockers": ["destination_city", "travel_dates"],
            "nb03_behavior": "Ask where they want to go and when. Use Dubai history to suggest similar destinations (Singapore, Gold Coast).",
        },
    },

    # ============================================================
    # CONTRADICTION-HEAVY (2 fixtures)
    # ============================================================

    "dreamer_budget_vs_luxury": {
        "fixture_id": "dreamer_budget_vs_luxury",
        "source_type": "freeform_text",
        "category": "contradiction_heavy",
        "raw_input": (
            "Family of 4 from Bangalore. "
            "They want a 5-star resort in Maldives, 7 nights. "
            "Budget is 1.5 lakhs total."
        ),
        "structured_input": None,
        "expected": {
            "extracted_fields": {
                "origin_city": {"value": "Bangalore", "authority": "explicit_owner"},
                "destination_city": {"value": "Maldives", "authority": "explicit_owner"},
                "traveler_count": {"value": 4, "authority": "explicit_owner"},
                "budget_range": {"value": "150000", "authority": "explicit_owner"},
                "traveler_preferences": {"value": "5-star resort, 7 nights", "authority": "explicit_owner"},
            },
            "expected_unknowns": ["travel_dates"],
            "expected_contradictions": ["budget_conflict"],  # Budget vs hotel tier
            "nb02_decision_state": "ASK_FOLLOWUP",
            "nb02_hard_blockers": ["travel_dates"],
            "nb03_behavior": "Ask for dates first. Then address budget-vs-luxury tension: 1.5L/4 = 37.5k/person is backpacker, not 5-star Maldives.",
        },
    },

    "revision_loop_budget_impossible": {
        "fixture_id": "revision_loop_budget_impossible",
        "source_type": "freeform_text",
        "category": "contradiction_heavy",
        "raw_input": (
            "Customer changed their mind again. "
            "Now it's Maldives for 6 people. "
            "Budget still 3 lakhs. They asked 'can we do it?'"
        ),
        "structured_input": {
            "origin_city": "Bangalore",
            "destination_city": "Maldives",
            "travel_dates": "2026-04-01 to 2026-04-07",
            "traveler_count": 6,
            "budget_range": "300000",
        },
        "expected": {
            "extracted_fields": {
                "origin_city": {"value": "Bangalore", "authority": "imported_structured"},
                "destination_city": {"value": "Maldives", "authority": "imported_structured"},
                "travel_dates": {"value": "2026-04-01 to 2026-04-07", "authority": "imported_structured"},
                "traveler_count": {"value": 6, "authority": "imported_structured"},
                "budget_range": {"value": "300000", "authority": "imported_structured"},
            },
            "expected_unknowns": [],
            "expected_contradictions": ["budget_conflict"],  # 3L/6 = 50k/person, Maldives minimum ~80k
            "nb02_decision_state": "BRANCH_OPTIONS",
            "nb02_hard_blockers": [],
            "nb03_behavior": "Internal draft with budget warning. 50k/person won't cover Maldives. Suggest Andaman or budget increase.",
        },
    },

    # ============================================================
    # BRANCH-WORTHY AMBIGUITY (2 fixtures)
    # ============================================================

    "andaman_or_srilanka": {
        "fixture_id": "andaman_or_srilanka",
        "source_type": "freeform_text",
        "category": "branch_worthy_ambiguity",
        "raw_input": (
            "Couple from Mumbai, honeymoon. "
            "Thinking Andaman or Sri Lanka — haven't decided. "
            "Budget 2 lakhs, 6 nights, sometime in May. "
            "They want beaches, good food, and privacy."
        ),
        "structured_input": None,
        "expected": {
            "extracted_fields": {
                "origin_city": {"value": "Mumbai", "authority": "explicit_owner"},
                "destination_city": {"value": "Andaman or Sri Lanka", "authority": "explicit_owner"},
                "travel_dates": {"value": "May 2026", "authority": "explicit_owner"},
                "traveler_count": {"value": 2, "authority": "explicit_owner"},
                "budget_range": {"value": "200000", "authority": "explicit_owner"},
                "traveler_preferences": {"value": "beaches, good food, privacy", "authority": "explicit_owner"},
                "trip_purpose": {"value": "honeymoon", "authority": "explicit_owner"},
                "traveler_preferences": {"value": "beaches, good food, privacy", "authority": "explicit_owner"},
            },
            "expected_unknowns": [],
            "expected_contradictions": [],
            "nb02_decision_state": "PROCEED_TRAVELER_SAFE",
            "nb02_hard_blockers": [],
            "nb03_behavior": "Proceed but detect ambiguous destination ('or'). Add follow-up: 'Did you mean Andaman or Sri Lanka, or still deciding?'",
        },
    },

    "luxury_wants_budget_reality": {
        "fixture_id": "luxury_wants_budget_reality",
        "source_type": "freeform_text",
        "category": "branch_worthy_ambiguity",
        "raw_input": (
            "Family of 5 from Delhi. "
            "They want Europe — kids want to see snow in summer. "
            "Budget around 4-5 lakhs total. "
            "Parents can't walk too much, need accessible hotels. "
            "Maybe Switzerland or Austria."
        ),
        "structured_input": None,
        "expected": {
            "extracted_fields": {
                "origin_city": {"value": "Delhi", "authority": "explicit_owner"},
                "destination_city": {"value": "Switzerland or Austria", "authority": "explicit_owner"},
                "travel_dates": {"value": "summer (June/July)", "authority": "explicit_owner"},
                "traveler_count": {"value": 5, "authority": "explicit_owner"},
                "budget_range": {"value": "450000", "authority": "explicit_owner"},
                "traveler_composition": {"value": "family with elderly parents + kids", "authority": "explicit_owner"},
                "traveler_preferences": {"value": "snow, accessible hotels", "authority": "explicit_owner"},
                "trip_purpose": {"value": "family leisure", "authority": "explicit_owner"},
            },
            "expected_unknowns": [],
            "expected_contradictions": [],
            "nb02_decision_state": "PROCEED_TRAVELER_SAFE",
            "nb02_hard_blockers": [],
            "nb03_behavior": "Proceed but flag: ambiguous destination (Switzerland or Austria), budget tight for 5 in Europe peak season, "
                            "accessibility needs for elderly. Ask destination confirmation after proposal.",
        },
    },

}

# Utility: Get fixtures by category
def get_fixtures_by_category(category: str) -> dict:
    return {k: v for k, v in RAW_FIXTURES.items() if v["category"] == category}

# Utility: Get all fixture IDs
def get_all_fixture_ids() -> list:
    return list(RAW_FIXTURES.keys())

# Utility: Print fixture summary
def print_summary():
    categories = {}
    for fid, f in RAW_FIXTURES.items():
        cat = f["category"]
        categories.setdefault(cat, []).append(fid)
    print(f"Total raw fixtures: {len(RAW_FIXTURES)}")
    for cat, ids in categories.items():
        print(f"  {cat}: {len(ids)}")
        for i in ids:
            print(f"    - {i}")
