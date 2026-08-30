"""
tests/test_constraints_router.py — Verification suite for Constraints API Router (PER-0711).
"""

def test_list_constraint_rules_endpoint(session_client):
    response = session_client.get("/api/v1/constraints/rules")
    assert response.status_code == 200
    data = response.json()
    assert "active_rules" in data
    assert data["total_rules"] >= 4
    rule_ids = [r["rule_id"] for r in data["active_rules"]]
    assert "RULE_TEMPORAL_MCT" in rule_ids
    assert "RULE_REGULATORY_PASSPORT" in rule_ids


def test_evaluate_trip_constraints_endpoint(session_client):
    # 1. Create inbound trip
    inbound_res = session_client.post(
        "/api/v1/inbound/parse",
        json={
            "channel": "email",
            "raw_text": "2-week tour in Italy and France for 2 adults starting Nov 1 2026 to Nov 15 2026. Budget 8000 USD.",
            "customer_name": "Marco Polo",
        },
    ).json()

    trip_id = inbound_res["trip_id"]

    # 2. Evaluate constraints
    eval_res = session_client.post(
        f"/api/v1/constraints/evaluate/{trip_id}",
    )
    assert eval_res.status_code == 200
    eval_data = eval_res.json()
    assert eval_data["trip_id"] == trip_id
    assert "is_feasible" in eval_data
    assert "hard_violations" in eval_data
    assert "soft_violations" in eval_data
    assert "relaxation_hierarchy" in eval_data
