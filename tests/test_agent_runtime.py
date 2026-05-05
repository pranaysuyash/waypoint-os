from __future__ import annotations

from datetime import datetime, timedelta, timezone

from src.agents.tool_contracts import ToolFreshnessPolicy, ToolResult
from src.agents.runtime import (
    AgentSupervisor,
    BookingReadinessAgent,
    ConstraintFeasibilityAgent,
    DestinationIntelligenceAgent,
    DocumentReadinessAgent,
    FlightStatusAgent,
    FrontDoorAgent,
    FollowUpAgent,
    GDSSchemaBridgeAgent,
    InMemoryWorkCoordinator,
    PNRShadowAgent,
    ProposalReadinessAgent,
    QualityEscalationAgent,
    SafetyAlertAgent,
    SalesActivationAgent,
    SupplierIntelligenceAgent,
    TicketPriceWatchAgent,
    WeatherPivotAgent,
    WorkItem,
    WorkStatus,
    build_default_registry,
)


class _Repo:
    def __init__(self, trips):
        self.trips = {trip["id"]: dict(trip) for trip in trips}
        self.update_calls = []
        self.fail_updates_for: set[str] = set()

    def list_active(self):
        return list(self.trips.values())

    def update_trip(self, trip_id: str, updates: dict):
        self.update_calls.append((trip_id, updates))
        if trip_id in self.fail_updates_for:
            return None
        trip = self.trips.get(trip_id)
        if not trip:
            return None
        trip.update(updates)
        return trip


class _Audit:
    def __init__(self):
        self.events = []

    def log(self, event_type: str, trip_id: str, payload: dict, user_id: str | None = None):
        self.events.append({"event_type": event_type, "trip_id": trip_id, "payload": payload, "user_id": user_id})


def test_default_registry_exposes_operational_product_agents_beyond_recovery():
    definitions = build_default_registry().definitions()
    names = {definition["name"] for definition in definitions}

    assert {
        "front_door_agent",
        "sales_activation_agent",
        "document_readiness_agent",
        "destination_intelligence_agent",
        "weather_pivot_agent",
        "constraint_feasibility_agent",
        "proposal_readiness_agent",
        "booking_readiness_agent",
        "flight_status_agent",
        "ticket_price_watch_agent",
        "safety_alert_agent",
        "gds_schema_bridge_agent",
        "pnr_shadow_agent",
        "supplier_intelligence_agent",
        "follow_up_agent",
        "quality_escalation_agent",
    } <= names
    for definition in definitions:
        assert definition["trigger_contract"]
        assert definition["input_contract"]
        assert definition["output_contract"]
        assert definition["idempotency_contract"]
        assert definition["failure_contract"]


def test_happy_path_orchestration_runs_both_product_agents():
    now = datetime.now(timezone.utc)
    repo = _Repo([
        {"id": "trip_follow", "status": "in_progress", "follow_up_due_date": (now - timedelta(hours=1)).isoformat()},
        {"id": "trip_quality", "status": "new", "decision_state": "ESCALATED", "front_door_assessment": {"assessed_at": "2026-05-04T00:00:00+00:00"}},
    ])
    audit = _Audit()
    supervisor = AgentSupervisor(build_default_registry(), repo, audit, interval_seconds=1)

    results = supervisor.run_once()

    assert len(results) == 2
    assert {result.work_item.agent_name for result in results} == {"follow_up_agent", "quality_escalation_agent"}
    assert repo.trips["trip_follow"]["follow_up_status"] == "due"
    assert repo.trips["trip_quality"]["review_status"] == "escalated"
    assert {event["payload"]["event_type"] for event in audit.events} >= {"agent_decision", "agent_action"}


def test_front_door_agent_classifies_incomplete_inquiry_and_drafts_acknowledgment():
    repo = _Repo([
        {
            "id": "trip_front",
            "status": "new",
            "raw_input": {"raw_note": "Need Singapore trip for family next month"},
            "extracted": {"facts": {"destination": {"value": "Singapore"}}},
        },
    ])
    agent = FrontDoorAgent()

    result = agent.execute(next(agent.scan(repo)), repo)

    assert result.success is True
    assessment = repo.trips["trip_front"]["front_door_assessment"]
    assert assessment["is_real_lead"] is True
    assert assessment["priority"] == "high"
    assert "budget" in assessment["missing_fields"]
    assert repo.trips["trip_front"]["recommended_next_action"] == "clarify_missing_trip_details"
    assert "Singapore" in assessment["acknowledgment_draft"]


def test_sales_activation_agent_schedules_follow_up_for_idle_lead():
    repo = _Repo([
        {
            "id": "trip_sales",
            "status": "quoted",
            "updated_at": (datetime.now(timezone.utc) - timedelta(hours=60)).isoformat(),
        },
    ])
    agent = SalesActivationAgent()

    result = agent.execute(next(agent.scan(repo)), repo)

    assert result.success is True
    assert repo.trips["trip_sales"]["follow_up_status"] == "pending"
    assert repo.trips["trip_sales"]["follow_up_due_date"]
    assert "proposal" in repo.trips["trip_sales"]["follow_up_draft"].lower()


def test_sales_activation_agent_skips_when_follow_up_already_pending():
    repo = _Repo([
        {
            "id": "trip_pending",
            "status": "quoted",
            "updated_at": (datetime.now(timezone.utc) - timedelta(hours=60)).isoformat(),
            "follow_up_due_date": (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat(),
            "follow_up_status": "pending",
        },
    ])

    assert list(SalesActivationAgent().scan(repo)) == []


def test_tool_result_marks_stale_evidence_not_fresh():
    fetched_at = datetime(2026, 5, 4, tzinfo=timezone.utc)
    result = ToolResult.from_static(
        tool_name="document_rules_static_seed",
        query={"destination": "canada"},
        data={"rule_set": "test"},
        source="unit_test",
        freshness=ToolFreshnessPolicy(max_age_seconds=60),
        now=fetched_at,
    )

    assert result.is_fresh(now=fetched_at + timedelta(seconds=30)) is True
    assert result.is_fresh(now=fetched_at + timedelta(seconds=61)) is False
    assert result.to_dict()["evidence"]["source"] == "unit_test"


def test_document_readiness_agent_builds_visa_passport_transit_checklist():
    repo = _Repo([
        {
            "id": "trip_docs",
            "stage": "proposal",
            "raw_input": {"raw_note": "Indian passports, senior traveler, USA and Canada with Amsterdam transit"},
            "extracted": {
                "facts": {
                    "destination_candidates": {"value": ["United States", "Canada"]},
                    "date_window": {"value": "2026-11-05 to 2026-11-18"},
                }
            },
            "traveler_nationalities": ["Indian"],
            "transit_points": ["Doha", "Amsterdam"],
            "travelers": [{"name": "Adult 1"}, {"name": "Senior", "traveler_type": "senior"}],
        },
    ])
    agent = DocumentReadinessAgent()

    result = agent.execute(next(agent.scan(repo)), repo)

    assert result.success is True
    checklist = repo.trips["trip_docs"]["document_readiness_checklist"]
    assert checklist["risk_level"] == "high"
    assert repo.trips["trip_docs"]["document_risk_level"] == "high"
    assert any("united states" in item["message"].lower() for item in checklist["items"])
    assert any("canada" in item["message"].lower() for item in checklist["items"])
    assert any("amsterdam" in item["message"].lower() for item in checklist["items"])
    assert any("passport expiry" in value for value in checklist["must_confirm"])
    assert checklist["tool_evidence"][0]["tool_name"] == "document_rules_static_seed"
    assert "authoritative sources" in checklist["disclaimer"]


def test_document_readiness_agent_skips_when_checklist_exists():
    repo = _Repo([
        {
            "id": "trip_docs_done",
            "stage": "proposal",
            "destination": "Singapore",
            "document_readiness_checklist": {"checked_at": "2026-05-04T00:00:00+00:00"},
        },
    ])

    assert list(DocumentReadinessAgent().scan(repo)) == []


class _FakeWeatherTool:
    def __init__(self, result: ToolResult):
        self.result = result
        self.queries = []

    def current_conditions(self, destination: str) -> ToolResult:
        self.queries.append(destination)
        return self.result


def test_destination_intelligence_agent_attaches_fresh_weather_snapshot():
    fetched_at = datetime(2026, 5, 4, tzinfo=timezone.utc)
    tool_result = ToolResult.from_static(
        tool_name="open_meteo_weather",
        query={"destination": "Singapore"},
        data={
            "location": {"name": "Singapore", "latitude": 1.29, "longitude": 103.85},
            "current": {"temperature_c": 31.5, "wind_speed_kmh": 16.0, "precipitation_mm": 0.2},
            "daily": {"precipitation_probability_max": 82, "uv_index_max": 9.1},
        },
        source="unit_test_weather",
        freshness=ToolFreshnessPolicy(max_age_seconds=3600),
        confidence=0.9,
        now=fetched_at,
    )
    repo = _Repo([
        {
            "id": "trip_destination",
            "stage": "proposal",
            "extracted": {"facts": {"destination": {"value": "Singapore"}}},
        },
    ])
    agent = DestinationIntelligenceAgent(weather_tool=_FakeWeatherTool(tool_result), now_provider=lambda: fetched_at + timedelta(minutes=10))

    result = agent.execute(next(agent.scan(repo)), repo)

    assert result.success is True
    snapshot = repo.trips["trip_destination"]["destination_intelligence_snapshot"]
    assert snapshot["risk_level"] == "medium"
    assert snapshot["destinations"][0]["destination"] == "singapore"
    assert snapshot["destinations"][0]["tool_evidence"][0]["fresh"] is True
    assert any("rain" in recommendation.lower() for recommendation in snapshot["recommendations"])
    assert repo.trips["trip_destination"]["destination_risk_level"] == "medium"


def test_destination_intelligence_agent_refuses_stale_weather_as_current_evidence():
    fetched_at = datetime(2026, 5, 4, tzinfo=timezone.utc)
    tool_result = ToolResult.from_static(
        tool_name="open_meteo_weather",
        query={"destination": "Tokyo"},
        data={"current": {"temperature_c": 22.0}},
        source="unit_test_weather",
        freshness=ToolFreshnessPolicy(max_age_seconds=60),
        now=fetched_at,
    )
    repo = _Repo([
        {
            "id": "trip_stale_destination",
            "stage": "proposal",
            "destination": "Tokyo",
        },
    ])
    agent = DestinationIntelligenceAgent(weather_tool=_FakeWeatherTool(tool_result), now_provider=lambda: fetched_at + timedelta(seconds=90))

    result = agent.execute(next(agent.scan(repo)), repo)

    assert result.success is True
    snapshot = repo.trips["trip_stale_destination"]["destination_intelligence_snapshot"]
    assert snapshot["risk_level"] == "unknown"
    assert snapshot["destinations"][0]["status"] == "stale"
    assert "Refresh destination intelligence" in snapshot["recommendations"][0]
    assert repo.trips["trip_stale_destination"]["destination_risk_level"] == "unknown"


def test_weather_pivot_agent_builds_activity_and_transfer_pivot_packet():
    fetched_at = datetime(2026, 5, 4, tzinfo=timezone.utc)
    evidence = ToolResult.from_static(
        tool_name="open_meteo_weather",
        query={"destination": "Singapore"},
        data={
            "daily": {"precipitation_probability_max": 86, "uv_index_max": 9.4},
            "current": {"wind_speed_kmh": 18},
        },
        source="unit_test_weather",
        freshness=ToolFreshnessPolicy(max_age_seconds=3600),
        now=fetched_at,
    ).to_dict(now=fetched_at + timedelta(minutes=5))
    repo = _Repo([
        {
            "id": "trip_weather_pivot",
            "stage": "proposal",
            "destination_intelligence_snapshot": {
                "checked_at": (fetched_at + timedelta(minutes=5)).isoformat(),
                "risk_level": "medium",
                "destinations": [
                    {
                        "destination": "singapore",
                        "status": "fresh",
                        "risk_level": "medium",
                        "signals": [
                            {"category": "weather", "severity": "medium", "message": "Rain probability is 86%."},
                            {"category": "weather", "severity": "medium", "message": "UV index max is 9.4."},
                        ],
                        "tool_evidence": [evidence],
                    }
                ],
            },
            "itinerary_items": [
                {"title": "Gardens by the Bay walk", "type": "outdoor"},
                {"title": "Airport transfer", "type": "transfer"},
            ],
        },
    ])
    agent = WeatherPivotAgent(now_provider=lambda: fetched_at + timedelta(minutes=10))

    result = agent.execute(next(agent.scan(repo)), repo)

    assert result.success is True
    packet = repo.trips["trip_weather_pivot"]["weather_pivot_packet"]
    assert packet["risk_level"] == "medium"
    assert any(item["title"] == "Gardens by the Bay walk" for item in packet["affected_activities"])
    assert any(item["title"] == "Airport transfer" for item in packet["transport_risks"])
    assert any("indoor" in option.lower() for option in packet["pivot_options"])
    assert packet["operator_next_action"] == "review_weather_pivots"


def test_weather_pivot_agent_refuses_stale_destination_evidence():
    fetched_at = datetime(2026, 5, 4, tzinfo=timezone.utc)
    stale_evidence = ToolResult.from_static(
        tool_name="open_meteo_weather",
        query={"destination": "Tokyo"},
        data={"daily": {"precipitation_probability_max": 75}},
        source="unit_test_weather",
        freshness=ToolFreshnessPolicy(max_age_seconds=60),
        now=fetched_at,
    ).to_dict(now=fetched_at + timedelta(seconds=90))
    repo = _Repo([
        {
            "id": "trip_stale_weather_pivot",
            "stage": "proposal",
            "destination_intelligence_snapshot": {
                "checked_at": (fetched_at + timedelta(seconds=90)).isoformat(),
                "risk_level": "unknown",
                "destinations": [
                    {
                        "destination": "tokyo",
                        "status": "stale",
                        "risk_level": "unknown",
                        "tool_evidence": [stale_evidence],
                    }
                ],
            },
        },
    ])
    agent = WeatherPivotAgent(now_provider=lambda: fetched_at + timedelta(seconds=90))

    result = agent.execute(next(agent.scan(repo)), repo)

    assert result.success is True
    packet = repo.trips["trip_stale_weather_pivot"]["weather_pivot_packet"]
    assert packet["risk_level"] == "unknown"
    assert packet["operator_next_action"] == "refresh_destination_intelligence"
    assert "stale" in packet["summary"].lower()


def test_constraint_feasibility_agent_flags_hard_and_soft_blockers():
    repo = _Repo([
        {
            "id": "trip_feasibility",
            "stage": "proposal",
            "raw_input": {"raw_note": "Need fast-paced Singapore trip for senior traveler, wheelchair access, budget $800"},
            "extracted": {
                "facts": {
                    "destination": {"value": "Singapore"},
                    "date_window": {"value": "2026-05-10 to 2026-05-12"},
                    "budget": {"value": "$800"},
                    "travelers": {"value": 4},
                }
            },
            "travelers": [{"traveler_type": "senior"}],
            "document_readiness_checklist": {
                "risk_level": "high",
                "must_confirm": ["passport expiry for traveler 1", "current visa/entry requirement"],
            },
            "weather_pivot_packet": {
                "risk_level": "medium",
                "operator_next_action": "review_weather_pivots",
            },
        },
    ])
    agent = ConstraintFeasibilityAgent(now_provider=lambda: datetime(2026, 5, 4, tzinfo=timezone.utc))

    result = agent.execute(next(agent.scan(repo)), repo)

    assert result.success is True
    assessment = repo.trips["trip_feasibility"]["constraint_feasibility_assessment"]
    assert assessment["status"] == "blocked"
    assert repo.trips["trip_feasibility"]["feasibility_status"] == "blocked"
    assert any(blocker["category"] == "document_readiness" for blocker in assessment["hard_blockers"])
    assert any(blocker["category"] == "budget" for blocker in assessment["hard_blockers"])
    assert any(flag["category"] == "accessibility" for flag in assessment["soft_constraints"])
    assert assessment["operator_next_action"] == "human_feasibility_review"


def test_constraint_feasibility_agent_skips_when_current_assessment_exists():
    repo = _Repo([
        {
            "id": "trip_feasibility_done",
            "stage": "proposal",
            "destination": "Singapore",
            "constraint_feasibility_assessment": {
                "assessed_at": "2026-05-04T00:00:00+00:00",
                "facts_marker": "proposal|singapore|no_date_window|no_budget|no_travelers|0|0|0|0|0|0",
            },
        },
    ])

    assert list(ConstraintFeasibilityAgent().scan(repo)) == []


def test_constraint_feasibility_agent_flags_route_fatigue_and_toddler_extreme_activity():
    repo = _Repo([
        {
            "id": "trip_route_activity_risk",
            "stage": "proposal",
            "raw_input": {"raw_note": "Family inquiry with elderly parents and toddler, wants mountain trek loop"},
            "extracted": {
                "facts": {
                    "destination": {"value": "Nepal"},
                    "date_window": {"value": "2026-09-10 to 2026-09-20"},
                    "budget": {"value": "$9000"},
                    "travelers": {"value": 5},
                    "party_composition": {"value": {"adults": 2, "toddlers": 1, "elderly": 2}},
                }
            },
            "flights": [
                {"carrier": "SQ", "flight_number": "406"},
                {"carrier": "AI", "flight_number": "215"},
                {"carrier": "RA", "flight_number": "229"},
                {"carrier": "RA", "flight_number": "230"},
            ],
            "itinerary_items": [
                {"title": "Kathmandu airport transfer", "type": "transfer"},
                {"title": "Annapurna basecamp trek", "type": "outdoor"},
            ],
        },
    ])
    agent = ConstraintFeasibilityAgent(now_provider=lambda: datetime(2026, 5, 4, tzinfo=timezone.utc))

    result = agent.execute(next(agent.scan(repo)), repo)

    assert result.success is True
    assessment = repo.trips["trip_route_activity_risk"]["constraint_feasibility_assessment"]
    assert assessment["status"] == "blocked"
    assert isinstance(assessment.get("structured_risks"), list) and assessment["structured_risks"]
    assert any(
        blocker["category"] == "routing" and "flight legs" in blocker["message"].lower()
        for blocker in assessment["hard_blockers"]
    )
    assert any(
        blocker["category"] == "activity" and "toddler" in blocker["message"].lower()
        for blocker in assessment["hard_blockers"]
    )
    assert any(risk.get("category") == "routing" for risk in assessment["structured_risks"])


def test_constraint_feasibility_agent_flags_safety_and_flight_disruption_for_active_trip():
    now = datetime(2026, 5, 4, 12, 0, tzinfo=timezone.utc)
    repo = _Repo([
        {
            "id": "trip_live_risk",
            "stage": "in_progress",
            "extracted": {
                "facts": {
                    "destination": {"value": "Paris"},
                    "date_window": {"value": "2026-05-01 to 2026-05-07"},
                    "budget": {"value": "$5000"},
                    "travelers": {"value": 2},
                }
            },
            "safety_alert_packet": {"risk_level": "high"},
            "flight_status_snapshot": {"risk_level": "medium"},
        },
    ])
    agent = ConstraintFeasibilityAgent(now_provider=lambda: now)
    result = agent.execute(next(agent.scan(repo)), repo)
    assert result.success is True
    assessment = repo.trips["trip_live_risk"]["constraint_feasibility_assessment"]
    assert any(blocker["category"] == "safety" for blocker in assessment["hard_blockers"])
    assert any(flag["category"] == "flight_disruption" for flag in assessment["soft_constraints"])


def test_constraint_feasibility_agent_refreshes_active_stage_on_age():
    now = datetime(2026, 5, 4, 12, 0, tzinfo=timezone.utc)
    old_assessed = (now - timedelta(hours=8)).isoformat()
    repo = _Repo([
        {
            "id": "trip_refresh_active",
            "stage": "in_progress",
            "destination": "Singapore",
            "constraint_feasibility_assessment": {
                "assessed_at": old_assessed,
                "facts_marker": "in_progress|singapore|no_date_window|no_budget|no_travelers|0|0|0|0|0|0",
            },
        }
    ])
    agent = ConstraintFeasibilityAgent(now_provider=lambda: now)
    items = list(agent.scan(repo))
    assert len(items) == 1


def test_constraint_feasibility_uses_itinerary_text_when_structured_route_missing():
    repo = _Repo([
        {
            "id": "trip_text_route",
            "stage": "proposal",
            "raw_input": {
                "raw_note": (
                    "2 elderly travelers and 1 toddler. "
                    "Fly Paris to Zurich then Milan then Prague in 4 days. "
                    "Airport transfer each stop and mountain trek day."
                )
            },
            "extracted": {
                "facts": {
                    "destination": {"value": "Europe"},
                    "date_window": {"value": "2026-06-10 to 2026-06-13"},
                    "budget": {"value": "$7000"},
                    "travelers": {"value": 3},
                    "party_composition": {"value": {"elderly": 2, "toddlers": 1}},
                }
            },
        },
    ])
    agent = ConstraintFeasibilityAgent(now_provider=lambda: datetime(2026, 5, 4, tzinfo=timezone.utc))
    result = agent.execute(next(agent.scan(repo)), repo)
    assert result.success is True
    assessment = repo.trips["trip_text_route"]["constraint_feasibility_assessment"]
    assert assessment["status"] in {"review", "blocked"}
    assert any(item["category"] == "routing" for item in [*assessment["hard_blockers"], *assessment["soft_constraints"]])


def test_constraint_feasibility_does_not_assume_parents_are_elderly():
    repo = _Repo([
        {
            "id": "trip_parents_not_elderly",
            "stage": "proposal",
            "raw_input": {
                "raw_note": (
                    "I am 19 booking for my parents (44 and 46). "
                    "Fly Paris to Zurich then Milan then Prague. airport transfers included."
                )
            },
            "extracted": {
                "facts": {
                    "destination": {"value": "Europe"},
                    "date_window": {"value": "2026-07-10 to 2026-07-16"},
                    "budget": {"value": "$6000"},
                    "travelers": {"value": 3},
                }
            },
            "travelers": [
                {"name": "Booker", "age": 19},
                {"name": "Parent A", "age": 44},
                {"name": "Parent B", "age": 46},
            ],
        }
    ])
    agent = ConstraintFeasibilityAgent(now_provider=lambda: datetime(2026, 5, 4, tzinfo=timezone.utc))
    result = agent.execute(next(agent.scan(repo)), repo)
    assert result.success is True
    assessment = repo.trips["trip_parents_not_elderly"]["constraint_feasibility_assessment"]
    # Should review due to route density/ambiguity, but must not trigger elderly hard blocker.
    assert not any(
        item["category"] == "routing" and "elderly traveler context" in item["message"].lower()
        for item in assessment["hard_blockers"]
    )
    assert any(
        item["category"] == "routing" and "parent cohort" in item["message"].lower()
        for item in assessment["soft_constraints"]
    )


def test_constraint_feasibility_flags_infant_pacing_sensitivity():
    repo = _Repo([
        {
            "id": "trip_infant_pacing",
            "stage": "proposal",
            "raw_input": {
                "raw_note": (
                    "Traveling with a baby. Fly Paris to Zurich then Milan then Prague. "
                    "Airport transfer at each stop."
                )
            },
            "extracted": {
                "facts": {
                    "destination": {"value": "Europe"},
                    "date_window": {"value": "2026-07-10 to 2026-07-16"},
                    "budget": {"value": "$7000"},
                    "travelers": {"value": 3},
                }
            },
            "travelers": [{"name": "Parent", "age": 33}, {"name": "Baby", "age": 1}],
        }
    ])
    agent = ConstraintFeasibilityAgent(now_provider=lambda: datetime(2026, 5, 4, tzinfo=timezone.utc))
    result = agent.execute(next(agent.scan(repo)), repo)
    assert result.success is True
    assessment = repo.trips["trip_infant_pacing"]["constraint_feasibility_assessment"]
    assert any(item["category"] == "pace" and "infant traveler context" in item["message"].lower() for item in assessment["soft_constraints"])


def test_constraint_feasibility_flags_grandparents_as_elderly_context():
    repo = _Repo([
        {
            "id": "trip_grandparents",
            "stage": "proposal",
            "raw_input": {
                "raw_note": (
                    "Traveling with grandparents. Fly Paris to Zurich then Milan then Prague then Vienna."
                )
            },
            "extracted": {
                "facts": {
                    "destination": {"value": "Europe"},
                    "date_window": {"value": "2026-07-10 to 2026-07-18"},
                    "budget": {"value": "$9000"},
                    "travelers": {"value": 4},
                }
            },
        }
    ])
    agent = ConstraintFeasibilityAgent(now_provider=lambda: datetime(2026, 5, 4, tzinfo=timezone.utc))
    result = agent.execute(next(agent.scan(repo)), repo)
    assert result.success is True
    assessment = repo.trips["trip_grandparents"]["constraint_feasibility_assessment"]
    assert any(
        item["category"] == "routing" and "elderly traveler context" in item["message"].lower()
        for item in [*assessment["hard_blockers"], *assessment["soft_constraints"]]
    )


def test_constraint_feasibility_tight_connection_stress_hub_threshold():
    now = datetime(2026, 5, 4, 12, 0, tzinfo=timezone.utc)
    repo = _Repo([
        {
            "id": "trip_stress_hub_connection",
            "stage": "proposal",
            "raw_input": {"raw_note": "Family with toddler"},
            "extracted": {
                "facts": {
                    "destination": {"value": "Europe"},
                    "date_window": {"value": "2026-07-10 to 2026-07-14"},
                    "budget": {"value": "$7000"},
                    "travelers": {"value": 3},
                    "party_composition": {"value": {"toddlers": 1}},
                }
            },
            "flights": [
                {"departure_airport": "DEL", "arrival_airport": "CDG", "arrival_time": "2026-07-10T10:00:00+00:00"},
                {"departure_airport": "CDG", "arrival_airport": "ZRH", "departure_time": "2026-07-10T11:35:00+00:00"},
            ],
        }
    ])
    agent = ConstraintFeasibilityAgent(now_provider=lambda: now)
    result = agent.execute(next(agent.scan(repo)), repo)
    assert result.success is True
    assessment = repo.trips["trip_stress_hub_connection"]["constraint_feasibility_assessment"]
    assert any(
        blocker["category"] == "routing" and "tight flight connection" in blocker["message"].lower()
        for blocker in assessment["hard_blockers"]
    )


def test_constraint_feasibility_adds_regional_disruption_pressure_for_europe_hubs():
    now = datetime(2026, 5, 4, 12, 0, tzinfo=timezone.utc)
    repo = _Repo([
        {
            "id": "trip_europe_hub_pressure",
            "stage": "proposal",
            "raw_input": {"raw_note": "Europe summer hop itinerary"},
            "extracted": {
                "facts": {
                    "destination_candidates": {"value": ["France", "Italy", "Switzerland"]},
                    "date_window": {"value": "2026-08-10 to 2026-08-15"},
                    "budget": {"value": "$9000"},
                    "travelers": {"value": 2},
                }
            },
            "flights": [
                {"departure_airport": "DEL", "arrival_airport": "CDG"},
                {"departure_airport": "CDG", "arrival_airport": "FRA"},
                {"departure_airport": "FRA", "arrival_airport": "ZRH"},
                {"departure_airport": "ZRH", "arrival_airport": "MXP"},
            ],
        }
    ])
    agent = ConstraintFeasibilityAgent(now_provider=lambda: now)
    result = agent.execute(next(agent.scan(repo)), repo)
    assert result.success is True
    assessment = repo.trips["trip_europe_hub_pressure"]["constraint_feasibility_assessment"]
    assert any(
        item["category"] in {"routing", "safety"} and "regional disruption pressure" in item["message"].lower()
        for item in assessment["soft_constraints"]
    )


def test_proposal_readiness_agent_blocks_thin_or_risky_proposal():
    repo = _Repo([
        {
            "id": "trip_proposal",
            "stage": "proposal",
            "proposal": {
                "options": [{"title": "Singapore quick trip"}],
                "budget_summary": "",
                "next_action": "",
            },
            "document_readiness_checklist": {"risk_level": "high"},
            "constraint_feasibility_assessment": {"status": "blocked", "hard_blockers": [{"category": "budget"}]},
            "weather_pivot_packet": {"risk_level": "medium"},
        },
    ])
    agent = ProposalReadinessAgent()

    result = agent.execute(next(agent.scan(repo)), repo)

    assert result.success is True
    readiness = repo.trips["trip_proposal"]["proposal_readiness_assessment"]
    assert readiness["status"] == "blocked"
    assert repo.trips["trip_proposal"]["proposal_readiness_status"] == "blocked"
    assert "at least two proposal options" in readiness["missing_elements"]
    assert any(risk["category"] == "feasibility" for risk in readiness["unresolved_risks"])
    assert readiness["operator_next_action"] == "revise_proposal_before_review"


def test_proposal_readiness_agent_marks_complete_proposal_reviewable():
    repo = _Repo([
        {
            "id": "trip_proposal_ready",
            "stage": "proposal",
            "proposal": {
                "options": [{"title": "Option A"}, {"title": "Option B"}],
                "budget_summary": "Includes hotel and transfers, excludes flights.",
                "risk_notes": "Weather and visa checks reviewed.",
                "next_action": "Operator review then send to customer.",
            },
            "document_readiness_checklist": {"risk_level": "low"},
            "constraint_feasibility_assessment": {"status": "feasible"},
            "weather_pivot_packet": {"risk_level": "low"},
        },
    ])
    agent = ProposalReadinessAgent()

    result = agent.execute(next(agent.scan(repo)), repo)

    assert result.success is True
    readiness = repo.trips["trip_proposal_ready"]["proposal_readiness_assessment"]
    assert readiness["status"] == "ready_for_operator_review"
    assert readiness["missing_elements"] == []
    assert readiness["operator_next_action"] == "operator_review_proposal"


def test_booking_readiness_agent_blocks_missing_traveler_and_payer_data():
    repo = _Repo([
        {
            "id": "trip_booking",
            "stage": "booking",
            "booking_data": {
                "travelers": [{"name": "Adult 1"}, {"date_of_birth": "1990-01-01", "passport_number": "P123"}],
                "payer": {},
                "contact": {"email": "lead@example.com"},
            },
            "proposal_readiness_assessment": {"status": "blocked"},
            "document_readiness_checklist": {"risk_level": "high"},
        },
    ])
    agent = BookingReadinessAgent()

    result = agent.execute(next(agent.scan(repo)), repo)

    assert result.success is True
    readiness = repo.trips["trip_booking"]["booking_readiness_assessment"]
    assert readiness["status"] == "blocked"
    assert repo.trips["trip_booking"]["booking_readiness_status"] == "blocked"
    assert any("traveler 1 date of birth" in item for item in readiness["missing_elements"])
    assert any("payer" in item for item in readiness["missing_elements"])
    assert any(risk["category"] == "document_readiness" for risk in readiness["blocking_risks"])
    assert readiness["operator_next_action"] == "collect_booking_details"


def test_booking_readiness_agent_marks_complete_data_ready_for_human_booking():
    repo = _Repo([
        {
            "id": "trip_booking_ready",
            "stage": "booking",
            "booking_data": {
                "travelers": [
                    {"name": "Adult 1", "date_of_birth": "1990-01-01", "passport_number": "P123", "passport_expiry": "2030-01-01"}
                ],
                "payer": {"name": "Adult 1", "email": "lead@example.com"},
                "contact": {"email": "lead@example.com", "phone": "+1 555 0100"},
                "special_requirements": "Vegetarian meal",
            },
            "proposal_readiness_assessment": {"status": "ready_for_operator_review"},
            "document_readiness_checklist": {"risk_level": "low"},
            "constraint_feasibility_assessment": {"status": "feasible"},
        },
    ])
    agent = BookingReadinessAgent()

    result = agent.execute(next(agent.scan(repo)), repo)

    assert result.success is True
    readiness = repo.trips["trip_booking_ready"]["booking_readiness_assessment"]
    assert readiness["status"] == "ready_for_human_booking"
    assert readiness["missing_elements"] == []
    assert readiness["operator_next_action"] == "human_booking_review"


class _FakeFlightStatusTool:
    def __init__(self, result: ToolResult):
        self.result = result

    def flight_status(self, flight: dict):
        return self.result


class _FakePriceWatchTool:
    def __init__(self, result: ToolResult):
        self.result = result

    def quote_price(self, quote: dict):
        return self.result


def test_flight_status_agent_attaches_delay_snapshot_and_escalates():
    fetched_at = datetime(2026, 5, 4, tzinfo=timezone.utc)
    tool_result = ToolResult.from_static(
        tool_name="mock_flight_status",
        query={"carrier": "SQ", "flight_number": "321"},
        data={"status": "delayed", "delay_minutes": 95, "route": "LHR-SIN"},
        source="unit_test_flight",
        freshness=ToolFreshnessPolicy(max_age_seconds=1800),
        now=fetched_at,
    )
    repo = _Repo([
        {
            "id": "trip_flight",
            "stage": "booking",
            "flights": [{"carrier": "SQ", "flight_number": "321"}],
        },
    ])
    agent = FlightStatusAgent(flight_tool=_FakeFlightStatusTool(tool_result), now_provider=lambda: fetched_at + timedelta(minutes=5))

    result = agent.execute(next(agent.scan(repo)), repo)

    assert result.success is True
    snapshot = repo.trips["trip_flight"]["flight_status_snapshot"]
    assert snapshot["risk_level"] == "high"
    assert snapshot["operator_next_action"] == "review_flight_disruption"
    assert snapshot["flights"][0]["tool_evidence"][0]["fresh"] is True


def test_ticket_price_watch_agent_flags_quote_drift():
    fetched_at = datetime(2026, 5, 4, tzinfo=timezone.utc)
    tool_result = ToolResult.from_static(
        tool_name="mock_price_watch",
        query={"quote_id": "quote_1"},
        data={"current_price": 1250, "quoted_price": 1000, "currency": "USD", "drift_percent": 25.0},
        source="unit_test_price",
        freshness=ToolFreshnessPolicy(max_age_seconds=1800),
        now=fetched_at,
    )
    repo = _Repo([
        {
            "id": "trip_price",
            "stage": "quoted",
            "quote": {"id": "quote_1", "price": 1000, "currency": "USD"},
        },
    ])
    agent = TicketPriceWatchAgent(price_tool=_FakePriceWatchTool(tool_result), now_provider=lambda: fetched_at + timedelta(minutes=5))

    result = agent.execute(next(agent.scan(repo)), repo)

    assert result.success is True
    alert = repo.trips["trip_price"]["ticket_price_watch_alert"]
    assert alert["risk_level"] == "high"
    assert alert["operator_next_action"] == "revalidate_quote_before_payment"
    assert alert["tool_evidence"][0]["fresh"] is True


class _FakeSafetyAlertTool:
    def __init__(self, result: ToolResult):
        self.result = result

    def destination_alerts(self, destination: str):
        return self.result


def test_safety_alert_agent_attaches_alert_packet():
    fetched_at = datetime(2026, 5, 4, tzinfo=timezone.utc)
    tool_result = ToolResult.from_static(
        tool_name="mock_safety_alerts",
        query={"destination": "Haiti"},
        data={"alerts": [{"severity": "high", "category": "security", "message": "Review active advisory."}]},
        source="unit_test_safety",
        freshness=ToolFreshnessPolicy(max_age_seconds=3600),
        now=fetched_at,
    )
    repo = _Repo([
        {
            "id": "trip_safety",
            "stage": "proposal",
            "destination": "Haiti",
            "travelers": [{"name": "Adult 1"}, {"name": "Adult 2"}],
        },
    ])
    agent = SafetyAlertAgent(safety_tool=_FakeSafetyAlertTool(tool_result), now_provider=lambda: fetched_at + timedelta(minutes=5))

    result = agent.execute(next(agent.scan(repo)), repo)

    assert result.success is True
    packet = repo.trips["trip_safety"]["safety_alert_packet"]
    assert packet["risk_level"] == "high"
    assert len(packet["affected_travelers"]) == 2
    assert packet["operator_next_action"] == "human_safety_review"


def test_gds_schema_bridge_agent_normalizes_provider_records():
    repo = _Repo([
        {
            "id": "trip_gds",
            "stage": "booking",
            "provider_records": [
                {"kind": "flight", "carrier": "SQ", "flight_number": "321", "origin": "LHR", "destination": "SIN"},
                {"kind": "hotel", "name": "Marina Bay", "check_in": "2026-05-10"},
            ],
        },
    ])
    agent = GDSSchemaBridgeAgent()

    result = agent.execute(next(agent.scan(repo)), repo)

    assert result.success is True
    bridge = repo.trips["trip_gds"]["gds_schema_bridge"]
    assert len(bridge["canonical_objects"]) == 2
    assert bridge["canonical_objects"][0]["type"] == "flight"
    assert bridge["operator_next_action"] == "review_canonical_travel_objects"


def test_pnr_shadow_agent_flags_name_mismatch():
    repo = _Repo([
        {
            "id": "trip_pnr",
            "stage": "booking",
            "booking_data": {"travelers": [{"name": "Pranay Test"}]},
            "pnr_record": {"travelers": [{"name": "P Test"}], "segments": [{"carrier": "SQ", "flight_number": "321"}]},
        },
    ])
    agent = PNRShadowAgent()

    result = agent.execute(next(agent.scan(repo)), repo)

    assert result.success is True
    shadow = repo.trips["trip_pnr"]["pnr_shadow_check"]
    assert shadow["risk_level"] == "high"
    assert any(issue["category"] == "traveler_names" for issue in shadow["issues"])


def test_supplier_intelligence_agent_flags_low_reliability_supplier():
    repo = _Repo([
        {
            "id": "trip_supplier",
            "stage": "proposal",
            "supplier_records": [
                {"name": "Slow Hotel DMC", "response_hours": 72, "failure_count": 2},
                {"name": "Fast Transfer", "response_hours": 4, "failure_count": 0},
            ],
        },
    ])
    agent = SupplierIntelligenceAgent()

    result = agent.execute(next(agent.scan(repo)), repo)

    assert result.success is True
    intel = repo.trips["trip_supplier"]["supplier_intelligence_snapshot"]
    assert intel["risk_level"] == "high"
    assert any(item["supplier"] == "Slow Hotel DMC" for item in intel["supplier_risks"])


def test_transient_dependency_failure_retries_then_succeeds():
    now = datetime.now(timezone.utc)
    repo = _Repo([
        {"id": "trip_retry", "status": "in_progress", "follow_up_due_date": (now - timedelta(hours=1)).isoformat()},
    ])
    audit = _Audit()
    supervisor = AgentSupervisor(build_default_registry(), repo, audit, interval_seconds=1)

    repo.fail_updates_for.add("trip_retry")
    first = supervisor.run_once(agent_name="follow_up_agent")
    repo.fail_updates_for.clear()
    second = supervisor.run_once(agent_name="follow_up_agent")

    assert first[0].success is False
    assert first[0].status == WorkStatus.RETRY_PENDING
    assert second[0].success is True
    assert second[0].status == WorkStatus.COMPLETED
    assert repo.trips["trip_retry"]["follow_up_status"] == "due"


def test_terminal_failure_poisons_and_escalates_after_retry_budget():
    repo = _Repo([
        {"id": "trip_poison", "status": "new", "decision_state": "ESCALATED"},
    ])
    repo.fail_updates_for.add("trip_poison")
    audit = _Audit()
    supervisor = AgentSupervisor(build_default_registry(), repo, audit, interval_seconds=1)

    first = supervisor.run_once(agent_name="quality_escalation_agent")
    second = supervisor.run_once(agent_name="quality_escalation_agent")
    third = supervisor.run_once(agent_name="quality_escalation_agent")

    assert first[0].status == WorkStatus.RETRY_PENDING
    assert second[0].status == WorkStatus.POISONED
    assert third == []
    assert any(event["payload"]["event_type"] == "agent_escalated" for event in audit.events)


def test_ownership_collision_prevention_and_idempotent_reentry():
    coordinator = InMemoryWorkCoordinator(lease_seconds=60)
    item = WorkItem(
        agent_name="follow_up_agent",
        trip_id="trip_lock",
        action="mark_follow_up_due",
        idempotency_key="follow_up_agent:trip_lock:2026-05-04T00:00:00+00:00",
    )
    policy = FollowUpAgent.definition.retry_policy

    acquired, reason, attempt = coordinator.acquire(item, owner="follow_up_agent", retry_policy=policy)
    second_acquired, second_reason, _ = coordinator.acquire(item, owner="follow_up_agent", retry_policy=policy)
    coordinator.complete(item, "done")
    third_acquired, third_reason, _ = coordinator.acquire(item, owner="follow_up_agent", retry_policy=policy)

    assert acquired is True
    assert reason == "acquired"
    assert attempt == 1
    assert second_acquired is False
    assert second_reason.startswith("owned_by:")
    assert third_acquired is False
    assert third_reason == "idempotent_reentry_completed"


def test_quality_agent_escalates_high_suitability_flags():
    repo = _Repo([
        {
            "id": "trip_flag",
            "status": "new",
            "decision": {"suitability_flags": [{"severity": "high", "reason": "mobility"}]},
        },
    ])
    result = QualityEscalationAgent().execute(next(QualityEscalationAgent().scan(repo)), repo)

    assert result.success is True
    assert repo.trips["trip_flag"]["review_status"] == "escalated"
    assert repo.trips["trip_flag"]["escalation_reason"] == "suitability_flag:high"
