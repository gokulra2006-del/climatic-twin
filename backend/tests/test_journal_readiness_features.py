import pytest
from app.core.reservoir_engine import reservoir_engine
from app.core.action_tracker import action_tracker
from app.core.sensor_health import sensor_health_engine
from app.core.alert_intelligence import alert_engine
from app.services.ai_assistant import generate_assistant_response
from app.api.api_v1.endpoints.data_quality import get_multi_domain_confidence

def test_reservoir_engine_status():
    status = reservoir_engine.get_current_reservoir_status()
    assert status["status"] == "SUCCESS"
    assert status["combined_storage_mcft"] > 0
    assert status["data_source_mode"] in ("VERIFIED_GOVERNMENT_OBSERVATION", "SIMULATED_APPROXIMATION")
    features = reservoir_engine.get_live_feature_vector()
    assert "POONDI" in features
    assert "total_reservoir_level" in features

def test_action_tracker_lifecycle():
    summary = action_tracker.get_summary()
    assert summary["total_actions"] >= 4
    assert summary["completed_actions"] >= 1

    # Test update
    actions = action_tracker.list_actions()
    first_id = actions[0]["action_id"]
    updated = action_tracker.update_action(
        action_id=first_id,
        status="effective",
        reviewer_name="Field Auditor Test",
        outcome_evidence="Verified dewatering sensor drop."
    )
    assert updated["status"] == "effective"
    assert updated["outcome_evidence"] == "Verified dewatering sensor drop."

def test_multi_domain_confidence_penalty_rule():
    conf = get_multi_domain_confidence()
    assert conf["status"] == "success"
    pillars = conf["pillars"]
    assert "weather_feed_quality" in pillars
    assert "reservoir_source_quality" in pillars
    assert "impact_evidence_quality" in pillars
    assert "model_uncertainty" in pillars
    overall = conf["overall_decision_readiness"]
    assert "score" in overall
    assert "tier" in overall
    # Missing evidence rule verification
    min_p = min(p["score"] for p in pillars.values())
    if min_p < 40.0:
        assert overall["score"] <= min_p

def test_bilingual_alert_cards():
    alert_engine.set_simulation("SCENARIO_B_HEAVY_RAIN")
    alerts = alert_engine.evaluate_state({"flood_probability": 0.85})
    assert len(alerts) > 0
    first = alerts[0]
    assert first.title_en is not None
    assert first.title_ta is not None
    assert first.action_recommendation_en is not None
    assert first.action_recommendation_ta is not None
    assert first.location_en is not None
    assert first.location_ta is not None
    alert_engine.clear_simulation()

def test_ai_assistant_grounded_queries():
    # 1. Adyar risk query
    res_adyar = generate_assistant_response(None, "Why is Adyar at risk?", "operator")
    assert "Chembarambakkam" in res_adyar["answer"] or "Adyar" in res_adyar["answer"]
    assert "confidence" in res_adyar
    assert "evidence_boundary" in res_adyar

    # 2. What changed query
    res_change = generate_assistant_response(None, "What changed in the last 24 hours?", "research")
    assert "rainfall" in res_change["answer"].lower() or "precipitation" in res_change["answer"].lower()
