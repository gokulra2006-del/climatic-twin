"""
Unit and integration tests for NOVA Copilot weather-question intent handling.

Tests:
1. Current observation queries: "What is the weather outside?"
2. Forecast queries: "Is there a chance of rainfall in my area?"
3. Windowed forecast queries: "Will it rain in the next 6 hours?"
4. Local micro-climate disagreement: "But it is sunny here."
5. Provider unavailable response handling without value fabrication.
6. API endpoint /api/ai/copilot intent differentiation.
"""

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app
from app.core.nova_copilot import nova_copilot, detect_weather_intent


@pytest.fixture
def sample_briefing():
    return {
        "timestamp": "2026-10-20T12:00:00Z",
        "threat_assessment": {"level": "LOW", "type": "FLOOD"},
        "live_weather": {
            "mode": "PHYSICAL_PROVIDER",
            "source": "Open-Meteo IMD 432790",
            "temperature_c": 30.5,
            "precipitation_mm": 0.0,
            "weather_code": 2,
            "weather_description": "Partly cloudy",
            "relative_humidity_pct": 72,
            "wind_speed_kmh": 14.2,
            "observed_at": "2026-10-20T12:00:00Z",
            "provider_coverage": "City-scale grid centered on Chennai (13.0827°N, 80.2707°E)",
        },
        "forecast_weather": {
            "status": "AVAILABLE",
            "source": "Open-Meteo hourly forecast",
            "forecast_generated_at": "2026-10-20T12:00:00Z",
            "windows": {
                "1h": {
                    "precipitation_probability_pct": 15,
                    "expected_rainfall_mm": 0.1,
                    "condition": "Partly cloudy",
                },
                "3h": {
                    "precipitation_probability_pct": 35,
                    "expected_rainfall_mm": 0.8,
                    "condition": "Overcast",
                },
                "6h": {
                    "precipitation_probability_pct": 70,
                    "expected_rainfall_mm": 4.5,
                    "condition": "Moderate rain",
                },
                "24h": {
                    "precipitation_probability_pct": 85,
                    "expected_rainfall_mm": 18.2,
                    "condition": "Heavy rain showers",
                },
            },
            "summary_statement": "Precipitation probability is 15% (0.1 mm) over the next 1h, peaking at 70% (4.5 mm) within 6h.",
        },
        "critical_asset_screening": {"Asset Name": "Central Station Subway"},
        "data_quality_summary": {"status": "NOMINAL"},
    }


def test_intent_detection():
    # Current observation queries
    assert detect_weather_intent("What is the weather outside?") == "CURRENT_OBSERVATION"
    assert detect_weather_intent("weather now") == "CURRENT_OBSERVATION"
    assert detect_weather_intent("rainfall right now") == "CURRENT_OBSERVATION"
    assert detect_weather_intent("what is the temperature outside?") == "CURRENT_OBSERVATION"

    # Forecast queries
    assert detect_weather_intent("Is there a chance of rainfall in my area?") == "FORECAST"
    assert detect_weather_intent("will it rain today?") == "FORECAST"
    assert detect_weather_intent("Will it rain in the next 6 hours?") == "FORECAST"
    assert detect_weather_intent("chance of rain in 3 hours") == "FORECAST"
    assert detect_weather_intent("what is the rainfall forecast for next 24 hours?") == "FORECAST"

    # Local micro-climate disagreement
    assert detect_weather_intent("But it is sunny here.") == "LOCATION_MISMATCH"
    assert detect_weather_intent("it is sunny outside my window") == "LOCATION_MISMATCH"
    assert detect_weather_intent("weather is different here") == "LOCATION_MISMATCH"
    assert detect_weather_intent("it is completely clear here") == "LOCATION_MISMATCH"

    # Non-weather queries
    assert detect_weather_intent("Why is flood risk high in Adyar?") == "NON_WEATHER"
    assert detect_weather_intent("What is the reservoir status?") == "NON_WEATHER"


@pytest.mark.anyio
async def test_current_observation_response(sample_briefing):
    question = "What is the weather outside?"
    res = await nova_copilot.answer(question, sample_briefing)

    assert res["intent"] == "CURRENT_OBSERVATION"
    assert res["badge"] == "CURRENT OBSERVATION"
    assert res["data_nature"] == "OBSERVED"
    assert "Open-Meteo" in res["source"]
    assert res["citations"] == ["Open-Meteo current observation"]

    answer = res["answer"]
    assert "30.5" in answer
    assert "0.0 mm" in answer
    assert "Partly cloudy" in answer
    assert "city-scale" in answer.lower()
    # Ensure prototype risk model or asset citations are NOT included
    assert "Prototype risk-model output" not in res["citations"]
    assert "Asset screening result" not in res["citations"]


@pytest.mark.anyio
async def test_forecast_response_chance_of_rain(sample_briefing):
    question = "Is there a chance of rainfall in my area?"
    res = await nova_copilot.answer(question, sample_briefing)

    assert res["intent"] == "FORECAST"
    assert res["badge"] == "FORECAST"
    assert res["data_nature"] == "FORECAST"
    assert "Open-Meteo" in res["source"]
    assert res["citations"] == ["Open-Meteo hourly forecast"]

    answer = res["answer"]
    # Verify windows are present
    ans_lower = answer.lower()
    assert "1 hour" in ans_lower or "1h" in ans_lower
    assert "3 hour" in ans_lower or "3h" in ans_lower
    assert "6 hour" in ans_lower or "6h" in ans_lower
    assert "24 hour" in ans_lower or "24h" in ans_lower

    # Verify probability vs rainfall separation (never reuses current precipitation 0.0 as probability)
    assert "15%" in answer or "35%" in answer or "70%" in answer
    assert "city-scale" in ans_lower

    # Verify safety notice is present
    assert "not constitute an official municipal warning" in res["safety_notice"]


@pytest.mark.anyio
async def test_forecast_response_6_hours(sample_briefing):
    question = "Will it rain in the next 6 hours?"
    res = await nova_copilot.answer(question, sample_briefing)

    assert res["intent"] == "FORECAST"
    assert res["badge"] == "FORECAST"
    assert res["data_nature"] == "FORECAST"
    assert res["citations"] == ["Open-Meteo hourly forecast"]

    answer = res["answer"]
    # 6-hour specific figures
    assert "6" in answer
    assert "70%" in answer
    assert "4.5 mm" in answer


@pytest.mark.anyio
async def test_local_disagreement_response(sample_briefing):
    question = "But it is sunny here."
    res = await nova_copilot.answer(question, sample_briefing)

    assert res["intent"] == "LOCATION_MISMATCH"
    assert res["badge"] == "LOCATION MISMATCH"
    assert res["data_nature"] == "OBSERVED"
    assert res["citations"] == ["Open-Meteo current observation", "Chennai localized micro-climate boundary"]

    answer = res["answer"]
    # Does not claim the user is wrong; acknowledges micro-climate variation
    assert "wrong" not in answer.lower()
    assert "micro" in answer.lower() or "localized" in answer.lower() or "variation" in answer.lower()
    assert "ward" in answer.lower()


@pytest.mark.anyio
async def test_provider_unavailable_observation():
    briefing = {
        "live_weather": {
            "mode": "UNAVAILABLE",
            "precipitation_mm": None,
            "temperature_c": None,
        },
        "forecast_weather": {"status": "UNAVAILABLE"},
    }
    res = await nova_copilot.answer("What is the weather outside?", briefing)

    assert res["intent"] == "CURRENT_OBSERVATION"
    assert res["data_nature"] == "UNAVAILABLE"
    assert "unavailable" in res["answer"].lower()
    # Does not invent fake numbers
    assert "°C" not in res["answer"]


@pytest.mark.anyio
async def test_provider_unavailable_forecast():
    briefing = {
        "live_weather": {"temperature_c": 30.0, "precipitation_mm": 0.0},
        "forecast_weather": {"status": "UNAVAILABLE"},
    }
    # Mock direct fetch to also return unavailable
    with patch.object(nova_copilot, "_fetch_forecast_direct", return_value={"status": "UNAVAILABLE"}):
        res = await nova_copilot.answer("Is there a chance of rainfall in my area?", briefing)

    assert res["intent"] == "FORECAST"
    assert res["data_nature"] == "UNAVAILABLE"
    assert "unavailable" in res["answer"].lower()
    # Does not fabricate rain probability
    assert "probability is" not in res["answer"].lower()


def test_copilot_api_endpoint_differentiation():
    """Verify POST /api/ai/copilot produces distinct answers for observation vs forecast."""
    client = TestClient(app)

    # 1. Observation
    res_obs = client.post("/api/ai/copilot", json={"question": "What is the weather outside?", "hazard": "FLOOD"})
    assert res_obs.status_code == 200
    data_obs = res_obs.json()
    assert data_obs["badge"] == "CURRENT OBSERVATION"
    assert data_obs["intent"] == "CURRENT_OBSERVATION"
    assert "Open-Meteo current observation" in data_obs["citations"]

    # 2. Forecast
    res_fc = client.post("/api/ai/copilot", json={"question": "Is there a chance of rainfall in my area?", "hazard": "FLOOD"})
    assert res_fc.status_code == 200
    data_fc = res_fc.json()
    assert data_fc["badge"] == "FORECAST"
    assert data_fc["intent"] == "FORECAST"
    assert "Open-Meteo hourly forecast" in data_fc["citations"]

    # Verify answers are clearly different
    assert data_obs["answer"] != data_fc["answer"]

    # 3. Disagreement
    res_mismatch = client.post("/api/ai/copilot", json={"question": "It is sunny here.", "hazard": "FLOOD"})
    assert res_mismatch.status_code == 200
    data_mismatch = res_mismatch.json()
    assert data_mismatch["badge"] == "LOCATION MISMATCH"
    assert "Chennai localized micro-climate boundary" in data_mismatch["citations"]
