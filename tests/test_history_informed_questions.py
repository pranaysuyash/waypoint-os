"""History-informed destination questions.

Past-trip memories feed the ASK, never the answer (owner request
2026-09-13: "can it help ask something like based on the past do they
prefer East Asian nations?"). Memories must never be suggested as
destination values — that would re-introduce the past-trip contamination
the extraction guards remove.
"""

from src.intake.decision import history_informed_destination_question


JAPAN_KOREA = [
    {
        "place": "Japan",
        "clause": "we went to japan, korea last year and loved it",
        "sentiment": "positive",
        "region": "East Asia",
    },
    {
        "place": "Korea",
        "clause": "we went to japan, korea last year and loved it",
        "sentiment": "positive",
        "region": "East Asia",
    },
]


def test_positive_multi_place_same_region_names_region():
    question = history_informed_destination_question(JAPAN_KOREA)
    assert "Japan and Korea" in question
    assert "East Asia" in question
    assert "loving" in question


def test_single_place_without_region_still_asks():
    question = history_informed_destination_question(
        [{"place": "Goa", "sentiment": None, "region": None}]
    )
    assert "Goa" in question
    assert "region" not in question.lower()


def test_neutral_sentiment_does_not_claim_love():
    question = history_informed_destination_question(
        [{"place": "Thailand", "sentiment": None, "region": "Southeast Asia"}]
    )
    assert question.startswith("You've been to Thailand before")
    assert "Southeast Asia" in question


def test_no_usable_history_returns_none():
    assert history_informed_destination_question([]) is None
    assert history_informed_destination_question([{"clause": "x"}]) is None
    assert history_informed_destination_question(["not-a-dict"]) is None


def test_memory_never_appears_as_suggested_value():
    """The question may name past places; the suggested_values lane must
    stay empty for a destination ask built from history (contract enforced
    at the call site — this test pins the helper's documentation)."""
    question = history_informed_destination_question(JAPAN_KOREA)
    assert isinstance(question, str)
    assert "suggest" not in question.lower()
