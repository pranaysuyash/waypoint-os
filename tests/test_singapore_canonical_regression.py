import time


def test_singapore_canonical_async_run_regression(session_client):
    payload = {
        "raw_note": (
            "Hi Ravi, I got your number from my wife who is a colleague of Divya. "
            "We are planning to visit Singapore sometime in Jan or Feb 2025. "
            "Tentative dates around 9th to 14th Feb, approx 5 days. "
            "Me, my wife, our 1.7 year old kid, and my parents would be going. "
            "We don't want it rushed. Interested in Universal Studios and nature parks."
        ),
        "owner_note": "Late-Nov call context; budget-conscious family, relaxed pace.",
        "structured_json": None,
        "itinerary_text": None,
        "stage": "discovery",
        "operating_mode": "copilot",
        "strict_leakage": False,
        "scenario_id": "SC-901",
    }

    accepted = session_client.post("/run", json=payload)
    assert accepted.status_code == 200, accepted.text
    run_id = accepted.json()["run_id"]

    terminal = None
    for _ in range(30):
        status = session_client.get(f"/runs/{run_id}")
        assert status.status_code == 200, status.text
        data = status.json()
        if data["state"] in {"completed", "failed", "blocked"}:
            terminal = data
            break
        time.sleep(0.5)

    assert terminal is not None, "Run did not reach terminal state in expected window"
    assert terminal["state"] == "completed", terminal

    # Canonical quality checks
    assert terminal.get("decision_state") == "ASK_FOLLOWUP", terminal
    assert "decision" in terminal.get("steps_completed", []), terminal
    assert "strategy" in terminal.get("steps_completed", []), terminal

    packet_step = session_client.get(f"/runs/{run_id}/steps/packet")
    assert packet_step.status_code == 200, packet_step.text
    packet = packet_step.json()["data"]
    assert packet["facts"]["destination_status"]["value"] == "definite"

    soft = packet["facts"].get("soft_preferences", {}).get("value", [])
    assert "it rushed" not in [str(x).lower() for x in soft]
