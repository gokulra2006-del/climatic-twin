from app.api.api_v1.endpoints.spatial import InundationScenarioRequest, create_inundation_scenario


def test_scenario_returns_geojson_and_disclaimer():
    result = create_inundation_scenario(InundationScenarioRequest(
        scenario_name="Test storm", rainfall_daily=80, rainfall_multiplier=1.2,
        runoff_indicator=0.4, flood_probability=0.5, reservoir_fill_ratio=0.8,
        drainage_efficiency=0.6,
    ))
    assert result["status"] == "SCENARIO_ONLY"
    assert result["geojson"]["type"] == "FeatureCollection"
    assert result["geojson"]["features"]
    assert "NOT OBSERVED" in result["disclaimer"]
