import os
import pytest
from unittest.mock import patch

from src.agents.connectivity import (
    ConnectivityTier,
    get_global_connectivity_tier,
    get_tool_connectivity_tier,
    assert_tier_compatibility,
)
from src.agents.live_tools import (
    build_weather_tool_from_env,
    build_flight_search_tool_from_env,
    build_flight_radar_tool_from_env,
    build_ground_routing_tool_from_env,
    MockWeatherTool,
    OpenMeteoWeatherTool,
    MockFlightSearchTool,
    AmadeusFlightSearchTool,
    MockFlightRadarTool,
    OpenSkyFlightRadarTool,
    MockGroundRoutingTool,
    OSRMGroundRoutingTool,
)


def test_global_connectivity_tier_defaults_to_mock():
    with patch.dict(os.environ, {}, clear=True):
        assert get_global_connectivity_tier() == ConnectivityTier.MOCK
        assert get_tool_connectivity_tier("weather") == ConnectivityTier.MOCK


def test_global_connectivity_tier_resolution():
    with patch.dict(os.environ, {"CONNECTIVITY_TIER": "sandbox"}, clear=True):
        assert get_global_connectivity_tier() == ConnectivityTier.SANDBOX
        assert get_tool_connectivity_tier("weather") == ConnectivityTier.SANDBOX

    with patch.dict(os.environ, {"CONNECTIVITY_TIER": "live"}, clear=True):
        assert get_global_connectivity_tier() == ConnectivityTier.LIVE
        assert get_tool_connectivity_tier("weather") == ConnectivityTier.LIVE


def test_per_tool_connectivity_tier_override():
    with patch.dict(os.environ, {"CONNECTIVITY_TIER": "mock", "CONNECTIVITY_TIER_WEATHER": "sandbox"}, clear=True):
        assert get_global_connectivity_tier() == ConnectivityTier.MOCK
        assert get_tool_connectivity_tier("weather") == ConnectivityTier.SANDBOX
        assert get_tool_connectivity_tier("flight_search") == ConnectivityTier.MOCK


def test_assert_tier_compatibility_honesty_boundary():
    # MOCK allows up to DETERMINISTIC_PREVIEW
    assert_tier_compatibility(ConnectivityTier.MOCK, "DETERMINISTIC_PREVIEW")
    with pytest.raises(ValueError, match="Honesty violation"):
        assert_tier_compatibility(ConnectivityTier.MOCK, "CONNECTED_SANDBOX")
    with pytest.raises(ValueError, match="Honesty violation"):
        assert_tier_compatibility(ConnectivityTier.MOCK, "REAL")

    # SANDBOX allows up to CONNECTED_SANDBOX
    assert_tier_compatibility(ConnectivityTier.SANDBOX, "CONNECTED_SANDBOX")
    with pytest.raises(ValueError, match="Honesty violation"):
        assert_tier_compatibility(ConnectivityTier.SANDBOX, "REAL")

    # LIVE allows REAL
    assert_tier_compatibility(ConnectivityTier.LIVE, "REAL")


def test_tool_builders_respect_connectivity_tier():
    # 1. Default (MOCK) -> all mock adapters
    with patch.dict(os.environ, {}, clear=True):
        assert isinstance(build_weather_tool_from_env(), MockWeatherTool)
        assert isinstance(build_flight_search_tool_from_env(), MockFlightSearchTool)
        assert isinstance(build_flight_radar_tool_from_env(), MockFlightRadarTool)
        assert isinstance(build_ground_routing_tool_from_env(), MockGroundRoutingTool)

    # 2. SANDBOX -> live keyless / sandbox adapters
    with patch.dict(os.environ, {"CONNECTIVITY_TIER": "sandbox"}, clear=True):
        assert isinstance(build_weather_tool_from_env(), OpenMeteoWeatherTool)
        assert isinstance(build_flight_radar_tool_from_env(), OpenSkyFlightRadarTool)
        assert isinstance(build_ground_routing_tool_from_env(), OSRMGroundRoutingTool)

    # 3. Flight search with credentials in sandbox
    with patch.dict(
        os.environ,
        {
            "CONNECTIVITY_TIER": "sandbox",
            "AMADEUS_CLIENT_ID": "fake_id",
            "AMADEUS_CLIENT_SECRET": "fake_secret",
        },
        clear=True,
    ):
        tool = build_flight_search_tool_from_env()
        assert isinstance(tool, AmadeusFlightSearchTool)
        assert "test.api.amadeus.com" in tool.endpoint
