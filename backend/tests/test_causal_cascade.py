import pytest
from app.core.causal_cascade import CausalCascadeEngine
from fastapi.testclient import TestClient
from app.main import app

def test_causal_cascade_forward():
    # Uses the provisional config loaded by default
    engine = CausalCascadeEngine()
    
    # Test 1: No intrinsic failures -> everything 0
    intrinsic = {
        "Reservoir_Dam": 0.0,
        "Substation_A": 0.0,
        "Pump_Station_1": 0.0,
        "Hospital_Backup": 0.0,
        "Road_Network_East": 0.0
    }
    baseline = engine.forward_cascade(intrinsic)
    assert all(abs(v) < 1e-6 for v in baseline.values())

    # Test 2: Only Reservoir_Dam fails (prob 1.0)
    intrinsic["Reservoir_Dam"] = 1.0
    probs = engine.forward_cascade(intrinsic)
    
    assert probs["Reservoir_Dam"] == 1.0
    # Substation_A has edge from Reservoir_Dam (beta=0.85)
    assert abs(probs["Substation_A"] - engine.graph["Reservoir_Dam"]["Substation_A"]["beta"]) < 1e-6
    # Pump_Station_1 has edge from Substation_A (beta=0.95)
    # P(Pump) = 1 - (1-0)*(1 - 0.95 * 0.85) = 0.95 * 0.85 = 0.8075
    beta1 = engine.graph["Reservoir_Dam"]["Substation_A"]["beta"]; beta2 = engine.graph["Substation_A"]["Pump_Station_1"]["beta"]; assert abs(probs["Pump_Station_1"] - (beta1 * beta2)) < 1e-6

def test_causal_cascade_intervention():
    engine = CausalCascadeEngine()
    
    intrinsic = {
        "Reservoir_Dam": 1.0,
        "Substation_A": 0.2  # Also has some intrinsic failure
    }
    
    # Baseline total risk should be high
    baseline = engine.forward_cascade(intrinsic)
    
    # Counterfactual: Intervene on Substation_A to never fail (0.0)
    interventions = {"Substation_A": 0.0}
    
    res = engine.simulate_intervention(intrinsic, interventions)
    intervened = res["intervened_probs"]
    
    assert intervened["Substation_A"] == 0.0
    # Because Substation_A is 0.0, downstream Pump_Station_1 intrinsic is 0.0, it should be 0.0
    assert intervened["Pump_Station_1"] == 0.0
    assert res["net_risk_delta"] < 0.0 # Intervention reduced risk

def test_cascade_endpoint():
    client = TestClient(app)
    payload = {
        "intrinsic_probs": {
            "Reservoir_Dam": 1.0
        },
        "interventions": {
            "Substation_A": 0.0
        }
    }
    response = client.post("/api/cascade/whatif", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "delta" in data
    assert data["intervened_probs"]["Substation_A"] == 0.0
