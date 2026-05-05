"""
intake.scenario_policy — configurable thresholds and vocab for scenario checks.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _set_env(name: str, default_values: set[str]) -> set[str]:
    raw = os.getenv(name, "").strip()
    if not raw:
        return set(default_values)
    values = {item.strip().lower() for item in raw.split(",") if item.strip()}
    return values or set(default_values)


@dataclass(frozen=True, slots=True)
class ScenarioPolicy:
    elderly_hard_flight_leg_threshold: int
    elderly_soft_flight_leg_threshold: int
    elderly_soft_transfer_threshold: int
    tight_connection_minutes_threshold: int
    transfer_terms: set[str]
    extreme_activity_terms: set[str]
    elderly_water_risk_terms: set[str]
    feasibility_refresh_hours_active: int
    stress_hub_airports: set[str]
    feasibility_refresh_hours_pre_departure: int
    feasibility_refresh_hours_in_progress: int


def load_scenario_policy() -> ScenarioPolicy:
    return ScenarioPolicy(
        elderly_hard_flight_leg_threshold=_int_env("TRAVEL_AGENT_ELDERLY_HARD_FLIGHT_LEGS", 4),
        elderly_soft_flight_leg_threshold=_int_env("TRAVEL_AGENT_ELDERLY_SOFT_FLIGHT_LEGS", 3),
        elderly_soft_transfer_threshold=_int_env("TRAVEL_AGENT_ELDERLY_SOFT_TRANSFER_ITEMS", 3),
        tight_connection_minutes_threshold=_int_env("TRAVEL_AGENT_TIGHT_CONNECTION_MINUTES", 90),
        transfer_terms=_set_env(
            "TRAVEL_AGENT_TRANSFER_TERMS",
            {"transfer", "airport", "drive", "driver", "car", "ferry", "boat", "rail", "train", "layover", "connection"},
        ),
        extreme_activity_terms=_set_env(
            "TRAVEL_AGENT_EXTREME_ACTIVITY_TERMS",
            {"trek", "trekking", "hike", "hiking", "summit", "mountain", "glacier", "high altitude", "expedition", "ski", "climb", "climbing", "via ferrata", "canyon"},
        ),
        elderly_water_risk_terms=_set_env(
            "TRAVEL_AGENT_ELDERLY_WATER_RISK_TERMS",
            {"snorkel", "snorkeling", "scuba", "open water", "parasail", "rafting", "jet ski"},
        ),
        feasibility_refresh_hours_active=_int_env("TRAVEL_AGENT_FEASIBILITY_REFRESH_HOURS_ACTIVE", 6),
        stress_hub_airports=_set_env(
            "TRAVEL_AGENT_STRESS_HUB_AIRPORTS",
            {"CDG", "JFK", "LHR", "FRA", "AMS"},
        ),
        feasibility_refresh_hours_pre_departure=_int_env("TRAVEL_AGENT_FEASIBILITY_REFRESH_HOURS_PRE_DEPARTURE", 4),
        feasibility_refresh_hours_in_progress=_int_env("TRAVEL_AGENT_FEASIBILITY_REFRESH_HOURS_IN_PROGRESS", 2),
    )
