import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_observed_flood_validation_uncalibrated_scenario_proxy():
    payload = {
        "event_id": "SCENARIO-TEST-01",
        "scenario_model_id": "copernicus_glo30_scenario_v1",
        "predicted_flood_extent_sqkm": 25.0,
        "observed_extent_sqkm": None,
        "observed_depth_points": []
    }
    response = client.post("/api/impacts/validate-observed-flood", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["validation_status"] == "UNVALIDATED_SCENARIO_PROXY"
    assert data["is_hydraulically_calibrated"] is False
    assert "SCENARIO ESTIMATE — NOT VALIDATED FLOOD DEPTH" in data["provenance_badge"]

def test_observed_flood_validation_with_ground_truth_metrics():
    payload = {
        "event_id": "IMP-CHN-2015-CWC-01",
        "scenario_model_id": "copernicus_glo30_scenario_v1",
        "predicted_flood_extent_sqkm": 40.0,
        "observed_extent_sqkm": 42.5,
        "sar_product": "RISAT-1 SAR Inundation Mask",
        "observed_depth_points": [
            {"latitude": 13.0067, "longitude": 80.2017, "observed_depth_m": 0.48, "location_name": "Saidapet Causeway"},
            {"latitude": 13.0116, "longitude": 80.0606, "observed_depth_m": 0.52, "location_name": "Chembarambakkam Outflow"},
            {"latitude": 13.0200, "longitude": 80.2100, "observed_depth_m": 0.44, "location_name": "Guindy Industrial Area"}
        ]
    }
    response = client.post("/api/impacts/validate-observed-flood", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_hydraulically_calibrated"] is True
    assert data["validation_status"] == "CALIBRATED_2D_VALIDATED"
    assert data["spatial_iou"] is not None
    assert data["depth_rmse_m"] is not None
    assert data["depth_rmse_m"] < 0.60
    assert data["sample_depth_points_n"] == 3

def test_drought_evidence_readiness_boundary():
    response = client.get("/api/replay/drought-readiness/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["overall_status"] == "PARTIAL_PROXY_STORAGE_REPLAY"
    assert "calibrated reservoir-storage stress proxy" in data["scientific_claim_boundary"]
    dim_names = [i["dimension"] for i in data["inputs"]]
    assert "Reservoir Storage Telemetry" in dim_names
    assert "Groundwater Table Levels" in dim_names
    assert "Soil Moisture Dynamics" in dim_names

def test_infrastructure_dependency_intake_and_review():
    # 1. Listing dependencies
    response = client.get("/api/cascade/dependencies")
    assert response.status_code == 200
    deps = response.json()
    assert len(deps) >= 3
    
    # 2. Registering a dependency without source URL must fail
    bad_dep = {
        "edge_id": "DEP-TEST-BAD",
        "source_asset": "Substation X",
        "target_asset": "Pump Y",
        "dependency_type": "power_supply",
        "responsible_agency": "TANGEDCO",
        "source_url": "",
        "validity_date": "2024-01-01"
    }
    bad_resp = client.post("/api/cascade/dependencies", json=bad_dep)
    assert bad_resp.status_code in (400, 422)

    # 3. Registering valid dependency queues as under_review
    valid_dep = {
        "edge_id": "DEP-TEST-009",
        "source_asset": "TANGEDCO Alandur 110kV Substation",
        "target_asset": "St. Thomas Mount Storm Drain Sump",
        "dependency_type": "power_supply",
        "responsible_agency": "TANGEDCO",
        "source_url": "https://www.tangedco.gov.in/alandur_schematic.pdf",
        "validity_date": "2024-05-15",
        "coupling_beta": 0.85,
        "evidence_status": "verified_real"  # Curator review gate must force under_review
    }
    create_resp = client.post("/api/cascade/dependencies", json=valid_dep)
    assert create_resp.status_code == 200
    assert create_resp.json()["evidence_status"] == "under_review"

    # 4. Curator approves edge
    review_payload = {
        "reviewer_name": "Dr. S. Ramanathan",
        "decision": "approved_verified_real",
        "review_notes": "Feeder circuit verified against GCC electrical drawings."
    }
    review_resp = client.post("/api/cascade/dependencies/DEP-TEST-009/review", json=review_payload)
    assert review_resp.status_code == 200
    assert review_resp.json()["edge"]["evidence_status"] == "verified_real"

def test_empirical_model_evaluation_chronological():
    response = client.get("/api/predictions/empirical-evaluation")
    assert response.status_code == 200
    data = response.json()
    assert data["evaluation_partition"]["strategy"] == "STRICT_CHRONOLOGICAL_EVENT_SPLIT"
    assert data["synthetic_benchmark_separated"] is True
    assert data["sample_size_warning"] is not None  # N < 10 or N < 30 warning
    model_names = [m["model_name"] for m in data["models"]]
    assert any("Random Forest" in m for m in model_names)
    assert any("XGBoost" in m for m in model_names)
    assert any("LSTM" in m for m in model_names)
    assert any("GNN-LSTM" in m for m in model_names)
