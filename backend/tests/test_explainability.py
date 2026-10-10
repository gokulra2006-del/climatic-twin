import pytest
from app.core.explainability import explainability_engine
from app.core.alert_intelligence import alert_engine

def test_explainability_engine_top_features():
    features = {
        'rainfall_daily': 250.0,
        'total_reservoir_level': 95.0,
        'temp_mean': 28.0
    }
    hazard_payload = {
        "contributing_features": features,
        "risk_level": "CRITICAL"
    }
    
    result = explainability_engine.explain("FLOOD", hazard_payload)
    
    # We should have an explanation string
    assert "explanation" in result
    
    # Check that it contains the actual high values we fed it
    exp = result["explanation"].lower()
    
    # Even if permutation or SHAP ranks them slightly differently, 
    # rainfall and reservoir level are massively high and should appear in the top 3 drivers.
    print("Explanation generated:", exp)
    assert "rainfall" in exp
    assert "250.0" in exp
    assert "reservoir" in exp
    assert "95.0" in exp

