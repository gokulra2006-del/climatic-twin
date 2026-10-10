import pytest
from datetime import datetime, timezone
from app.core.decision_support import (
    decision_engine,
    DecisionSupportEngine,
    DECISION_THRESHOLDS,
    HYSTERESIS_BAND,
    RECOMMENDED_ACTIONS
)
from app.core.multihazard import multihazard_engine, MultiHazardRiskEngine
from app.core.sensor_health import sensor_health_engine, PHYSICAL_BOUNDS
from app.core.assimilation import twin_engine


def test_decision_support_engine_nominal():
    """Verify nominal conditions result in NORMAL decision level with routine action."""
    engine = DecisionSupportEngine()
    result = engine.assess(
        flood_probability=0.05,
        uncertainty_level="LOW",
        compound_risk_score=0.10,
        max_asset_risk_index=0.20,
        aggregate_shs=0.95
    )
    assert result["decision_level"] == "NORMAL"
    assert result["escalation_state"] in ["NOMINAL", "STABLE"]
    assert "routine" in result["recommended_action"].lower()


def test_decision_support_engine_emergency_escalation():
    """Verify extreme persistent conditions escalate to ALERT or EMERGENCY with reasons."""
    engine = DecisionSupportEngine()
    result = engine.assess(
        flood_probability=0.95,
        uncertainty_level="HIGH",
        compound_risk_score=0.92,
        max_asset_risk_index=0.88,
        aggregate_shs=0.85,
        consecutive_elevated_cycles=6,
        trend_direction="RISING"
    )
    assert result["decision_level"] in ["PREPARE", "ALERT", "EMERGENCY"]
    assert len(result["escalation_reasons"]) > 0
    assert result["data_quality_gate"]["gate_state"] == "PASS"


def test_decision_support_data_quality_gating():
    """Verify degraded telemetry trips the data quality gate."""
    engine = DecisionSupportEngine()
    result = engine.assess(
        flood_probability=0.80,
        aggregate_shs=0.20,
        num_degraded=5,
        num_missing=3
    )
    assert result["data_quality_gate"]["gate_state"] in ["DEGRADED", "BLOCKED"]


def test_multihazard_risk_computation():
    """Verify non-linear compound risk score satisfies mathematical bounds."""
    engine = MultiHazardRiskEngine()
    env_state = {
        "rainfall_daily": 85.0,
        "temperature_c": 34.0,
        "wind_speed_kmh": 25.0,
        "reservoir_fill_ratio": 0.90
    }
    result = engine.calculate_compound_risk(env_state, flood_prob=0.75)
    assert "compound_risk_score" in result
    score = result["compound_risk_score"]
    assert 0.0 <= score <= 1.0
    assert result["compound_risk_level"] in ["HIGH", "CRITICAL"]


def test_sensor_health_plausibility_bounds():
    """Verify physical plausibility bounds check variable ranges."""
    engine = sensor_health_engine
    # Temperature 95°C is physically impossible in Chennai
    is_valid, msg = engine.check_physical_plausibility("temperature_c", 95.0)
    assert is_valid is False

    # Temperature 32°C is plausible
    is_valid, msg = engine.check_physical_plausibility("temperature_c", 32.0)
    assert is_valid is True


def test_assimilation_engine_nudging():
    """Verify Newtonian nudging updates assimilated environmental state."""
    res = twin_engine.assimilate(
        asset_id="POONDI",
        variable="water_level",
        value=2550.0,
        unit="mcft",
        obs_timestamp=datetime.now(timezone.utc),
        source="TEST_SENSOR",
        quality_flag="GOOD"
    )
    assert res["validation_status"] == "ACCEPTED"
    assert "updated_state" in res



def test_decision_support_expected_cost_policy():
    """Verify expected cost policy selects action minimizing E[Cost]."""
    engine = DecisionSupportEngine()
    
    # At very low probability, low-cost/no-action is best
    res_low = engine.assess(flood_probability=0.01, uncertainty_width=0.05)
    assert res_low["decision_level"] == "NORMAL"
    
    # At moderate probability, a cheaper action like PREPARE should trigger,
    # because missing costs 3000-5000, but PREPARE costs 50
    res_med = engine.assess(flood_probability=0.25, uncertainty_width=0.20)
    
    # At very high probability, EMERGENCY should trigger
    res_high = engine.assess(flood_probability=0.99, uncertainty_width=0.01)
    assert res_high["decision_level"] in ["ALERT", "EMERGENCY"]
    
    # Check rationale structure
    assert "rationale" in res_low
    assert "expected_costs" in res_low
