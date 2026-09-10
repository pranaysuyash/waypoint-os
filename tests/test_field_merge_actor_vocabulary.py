"""
tests/test_field_merge_actor_vocabulary.py — TS-04 provenance actor vocabulary
(2026-09-09 training-session register).

Contract under test:
- Canonical actor vocabulary: operator, customer, system, tool, provider.
- Commercial precedence: provider > operator > tool/system > customer.
- Preference precedence: customer > operator > machines (provider/tool/system).
- Internal roles (system/tool/provider) require allow_internal_actors=True;
  a client-supplied 'provider' folds to operator (trust boundary).
- Stored provenance keeps internal-actor rank across later merges.
- Legacy operator/customer behavior unchanged.
"""

from spine_api.services.field_merge import (
    ACTOR_CUSTOMER,
    ACTOR_OPERATOR,
    ACTOR_PROVIDER,
    ACTOR_SYSTEM,
    ACTOR_TOOL,
    PROVENANCE_KEY,
    normalize_actor_role,
    resolve_field_merge,
)

NOW = "2026-09-09T12:00:00+00:00"


def _merge(packet, updates, role, actor_id=None, **kwargs):
    return resolve_field_merge(packet, updates, role, actor_id, NOW, **kwargs)


# --- vocabulary normalization -------------------------------------------------


def test_client_surface_folds_internal_roles_to_operator():
    assert normalize_actor_role("provider") == ACTOR_OPERATOR
    assert normalize_actor_role("tool") == ACTOR_OPERATOR
    assert normalize_actor_role("system") == ACTOR_OPERATOR
    assert normalize_actor_role("hacker") == ACTOR_OPERATOR
    assert normalize_actor_role(None) == ACTOR_OPERATOR
    # legacy behavior unchanged
    assert normalize_actor_role("customer") == ACTOR_CUSTOMER
    assert normalize_actor_role("Operator") == ACTOR_OPERATOR


def test_internal_surface_accepts_full_vocabulary():
    assert normalize_actor_role("provider", allow_internal=True) == ACTOR_PROVIDER
    assert normalize_actor_role("tool", allow_internal=True) == ACTOR_TOOL
    assert normalize_actor_role("system", allow_internal=True) == ACTOR_SYSTEM
    assert normalize_actor_role("nonsense", allow_internal=True) == ACTOR_OPERATOR


def test_client_claiming_provider_rank_folds_to_operator_in_merge():
    """Trust boundary: without allow_internal_actors, 'provider' is treated
    as a plain operator write — no precedence escalation via the API."""
    packet = {"budget": 400000, PROVENANCE_KEY: {"budget": {"actor": ACTOR_OPERATOR, "actor_id": "op1", "at": NOW}}}
    result = _merge(packet, {"budget": 999999}, "provider", actor_id="client-claimed")
    # operator vs operator: equal rank, newer wins — applied, but as operator
    assert result.merged_packet["budget"] == 999999
    assert result.provenance["budget"]["actor"] == ACTOR_OPERATOR


# --- commercial precedence: provider > operator > tool > customer --------------


def test_provider_fact_outranks_operator_on_commercial():
    packet = {
        "start_date": "2026-10-05",
        PROVENANCE_KEY: {"start_date": {"actor": ACTOR_OPERATOR, "actor_id": "op1", "at": NOW}},
    }
    result = _merge(packet, {"start_date": "2026-10-06"}, ACTOR_PROVIDER, actor_id="amadeus", allow_internal_actors=True)
    assert "start_date" in result.applied_fields
    assert result.merged_packet["start_date"] == "2026-10-06"
    assert result.provenance["start_date"] == {
        "actor": ACTOR_PROVIDER,
        "actor_id": "amadeus",
        "at": NOW,
        "superseded": "2026-10-05",
    }


def test_operator_cannot_overwrite_provider_fact():
    packet = {
        "start_date": "2026-10-06",
        PROVENANCE_KEY: {"start_date": {"actor": ACTOR_PROVIDER, "actor_id": "amadeus", "at": NOW}},
    }
    result = _merge(packet, {"start_date": "2026-10-05"}, ACTOR_OPERATOR, actor_id="op1")
    assert "start_date" not in result.applied_fields
    assert len(result.conflicts) == 1
    conflict = result.conflicts[0]
    assert conflict.kept_actor == ACTOR_PROVIDER
    assert conflict.kept_value == "2026-10-06"
    assert result.merged_packet["start_date"] == "2026-10-06"  # provider fact kept


def test_stored_provider_rank_survives_client_writer():
    """Stored internal-actor rank is parsed against the full vocabulary even
    when the incoming writer is a client-restricted caller."""
    packet = {
        "budget": 400000,
        PROVENANCE_KEY: {"budget": {"actor": ACTOR_PROVIDER, "actor_id": "tbo", "at": NOW}},
    }
    result = _merge(packet, {"budget": 500000}, ACTOR_OPERATOR, actor_id="op1")
    assert len(result.conflicts) == 1
    assert result.conflicts[0].kept_actor == ACTOR_PROVIDER


def test_tool_value_outranks_customer_but_not_operator():
    packet = {"party_size": 4, PROVENANCE_KEY: {"party_size": {"actor": ACTOR_TOOL, "actor_id": "extractor", "at": NOW}}}
    # customer restatement loses to the deterministic extraction
    result_customer = _merge(packet, {"party_size": 2}, ACTOR_CUSTOMER, actor_id="cust1")
    assert len(result_customer.conflicts) == 1
    assert result_customer.merged_packet["party_size"] == 4
    # operator correction wins over the tool value
    result_operator = _merge(packet, {"party_size": 5}, ACTOR_OPERATOR, actor_id="op1")
    assert "party_size" in result_operator.applied_fields
    assert result_operator.merged_packet["party_size"] == 5


def test_tool_write_on_commercial_records_provenance():
    result = _merge({"budget": None}, {"budget": 400000}, ACTOR_TOOL, actor_id="budget_extractor", allow_internal_actors=True)
    assert result.provenance["budget"]["actor"] == ACTOR_TOOL
    assert result.provenance["budget"]["actor_id"] == "budget_extractor"


def test_system_role_ranked_with_tool():
    packet = {"origin": "BLR", PROVENANCE_KEY: {"origin": {"actor": ACTOR_SYSTEM, "actor_id": "geo-normalizer", "at": NOW}}}
    result = _merge(packet, {"origin": "Chennai"}, ACTOR_CUSTOMER, actor_id="cust1")
    assert len(result.conflicts) == 1
    assert result.merged_packet["origin"] == "BLR"


# --- preference precedence: machines never override customer wants -------------


def test_provider_cannot_override_customer_preference():
    packet = {
        "hotel_preference": "4-star boutique",
        PROVENANCE_KEY: {"hotel_preference": {"actor": ACTOR_CUSTOMER, "actor_id": "cust1", "at": NOW}},
    }
    result = _merge(
        packet,
        {"hotel_preference": "whatever is cheapest"},
        ACTOR_PROVIDER,
        actor_id="tbo",
        allow_internal_actors=True,
    )
    assert len(result.conflicts) == 1
    assert result.merged_packet["hotel_preference"] == "4-star boutique"
    assert result.conflicts[0].reason.startswith("preference field")


def test_tool_write_on_preference_field_records_but_ranks_lowest():
    result = _merge({}, {"seat_preference": "aisle"}, ACTOR_TOOL, actor_id="memory-ranker", allow_internal_actors=True)
    assert result.provenance["seat_preference"]["actor"] == ACTOR_TOOL
    # and a later customer statement overrides it
    packet = result.merged_packet
    later = _merge(packet, {"seat_preference": "window"}, ACTOR_CUSTOMER, actor_id="cust1")
    assert "seat_preference" in later.applied_fields
    assert later.merged_packet["seat_preference"] == "window"


# --- legacy contract regression guards ------------------------------------------


def test_customer_still_wins_preference_over_operator():
    packet = {
        "dietary": "vegetarian",
        PROVENANCE_KEY: {"dietary": {"actor": ACTOR_OPERATOR, "actor_id": "op1", "at": NOW}},
    }
    result = _merge(packet, {"dietary": "vegan"}, ACTOR_CUSTOMER, actor_id="cust1")
    assert "dietary" in result.applied_fields
    assert result.merged_packet["dietary"] == "vegan"


def test_operator_still_wins_commercial_over_customer():
    packet = {
        "budget": 400000,
        PROVENANCE_KEY: {"budget": {"actor": ACTOR_OPERATOR, "actor_id": "op1", "at": NOW}},
    }
    result = _merge(packet, {"budget": 900000}, ACTOR_CUSTOMER, actor_id="cust1")
    assert len(result.conflicts) == 1
    assert result.merged_packet["budget"] == 400000


# --- review cycle 1: symmetric conservative guard -------------------------------


def test_tool_writer_rejected_on_unattributed_commercial_value():
    """Review cycle 1 P2 regression: an unattributed (pre-merge-system)
    commercial value is operator-owned — a tool/system writer is rejected
    just like a customer restatement; only provider facts may apply."""
    packet = {"budget": 400000}  # no _field_provenance — legacy shape
    result = _merge(packet, {"budget": 500000}, ACTOR_TOOL, actor_id="extractor", allow_internal_actors=True)
    assert len(result.conflicts) == 1
    assert result.conflicts[0].kept_value == 400000
    assert "operator-conservative default" in result.conflicts[0].reason


def test_provider_fact_applies_on_unattributed_commercial_value():
    packet = {"budget": 400000}
    result = _merge(packet, {"budget": 450000}, ACTOR_PROVIDER, actor_id="tbo", allow_internal_actors=True)
    assert "budget" in result.applied_fields
    assert result.merged_packet["budget"] == 450000
