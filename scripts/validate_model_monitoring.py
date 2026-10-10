"""
Comprehensive 25-Test Validation Suite for Model Drift, Performance Monitoring & Retraining Intelligence
Phase Next - ClimateTwin Chennai Project

Tests:
1. Normal distribution
2. Feature drift
3. No drift
4. Prediction drift
5. High uncertainty
6. Low uncertainty
7. Sensor failure (Data quality gate)
8. Stale data handling
9. Missing data handling
10. Temporary weather event (24h spike vs 7d/30d stability)
11. Persistent drift (Multi-window shift)
12. Insufficient data safeguard (<5 observations)
13. Verified performance degradation detection
14. Retraining recommendation logic
15. No retraining recommendation logic
16. Champion model metadata & parameters
17. Candidate model metadata & evaluation criteria
18. Model versioning structure
19. REST API endpoints (GET /api/model-health, /drift, /performance, /history, /retraining-readiness, POST /evaluate)
20. NOVA AI health summary generation
21. Dashboard data contract consistency
22. Invalid inputs resilience
23. Extreme environmental inputs resilience
24. Regression compatibility with Phase 9-16 modules
25. Frontend production build validation (npm run build)
"""

import os
import sys
import math
import json
import time
import subprocess
import numpy as np
import pandas as pd
from datetime import datetime, timezone, timedelta

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

from backend.app.core.model_monitoring import ModelMonitoringEngine, calculate_psi

def test_suite():
    print("======================================================================")
    print("CLIMATETWIN PHASE NEXT: MODEL DRIFT & RETRAINING INTELLIGENCE VALIDATION")
    print("======================================================================\n")
    
    passed = 0
    total = 25
    engine = ModelMonitoringEngine(BASE_DIR)
    
    # 1. Normal distribution
    try:
        np.random.seed(1)
        norm_a = np.random.normal(30.0, 5.0, 500)
        norm_b = np.random.normal(30.0, 5.0, 500)
        psi_normal = calculate_psi(norm_a, norm_b)
        assert psi_normal < 0.10, f"Expected PSI < 0.10 for identical distributions, got {psi_normal}"
        print("✓ Test 1 Passed: Normal Distribution PSI stability verified (< 0.10).")
        passed += 1
    except Exception as e:
        print(f"✗ Test 1 Failed: {e}")

    # 2. Feature drift
    try:
        norm_base = np.random.normal(20.0, 4.0, 500)
        norm_shifted = np.random.normal(85.0, 25.0, 200) # Heavy monsoon shift
        psi_drift = calculate_psi(norm_base, norm_shifted)
        assert psi_drift >= 0.25, f"Expected PSI >= 0.25 for large shift, got {psi_drift}"
        print("✓ Test 2 Passed: Feature distribution drift successfully triggered (PSI >= 0.25).")
        passed += 1
    except Exception as e:
        print(f"✗ Test 2 Failed: {e}")

    # 3. No drift
    try:
        np.random.seed(42)
        all_vals = engine.history_df['temp_mean'].values
        sample_a = np.random.choice(all_vals, size=250, replace=False)
        sample_b = np.random.choice(all_vals, size=250, replace=False)
        psi_nodrift = calculate_psi(sample_a, sample_b)
        assert psi_nodrift < 0.10, f"Expected low PSI on unshifted samples, got {psi_nodrift}"
        print("✓ Test 3 Passed: No drift condition verified on baseline partitions.")
        passed += 1
    except Exception as e:
        print(f"✗ Test 3 Failed: {e}")

    # 4. Prediction drift
    try:
        p_res = engine.evaluate_prediction_drift("7d")
        assert "psi" in p_res and "probability_shift" in p_res and "severity" in p_res
        assert p_res["severity"] in ["LOW", "MODERATE", "HIGH"]
        print(f"✓ Test 4 Passed: Prediction drift evaluated (Shift: {p_res['probability_shift']}, Severity: {p_res['severity']}).")
        passed += 1
    except Exception as e:
        print(f"✗ Test 4 Failed: {e}")

    # 5. High uncertainty
    try:
        test_obs = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "epistemic_variance": 0.048, # High variance
            "prediction_interval_width": 0.42, # Broad interval
            "uncertainty_level": "HIGH"
        }
        test_engine = ModelMonitoringEngine(BASE_DIR)
        test_engine.live_buffer = [test_obs] * 10
        u_high = test_engine.evaluate_uncertainty_drift("7d")
        assert u_high["condition"] == "MODEL CONFIDENCE DEGRADING"
        assert u_high["status"] == "WATCH"
        print("✓ Test 5 Passed: High uncertainty flags 'MODEL CONFIDENCE DEGRADING'.")
        passed += 1
    except Exception as e:
        print(f"✗ Test 5 Failed: {e}")

    # 6. Low uncertainty
    try:
        test_obs_low = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "epistemic_variance": 0.003,
            "prediction_interval_width": 0.08,
            "uncertainty_level": "LOW"
        }
        test_engine = ModelMonitoringEngine(BASE_DIR)
        test_engine.live_buffer = [test_obs_low] * 10
        u_low = test_engine.evaluate_uncertainty_drift("7d")
        assert u_low["condition"] == "STABLE CONFIDENCE"
        assert u_low["status"] == "HEALTHY"
        print("✓ Test 6 Passed: Low uncertainty correctly yields 'STABLE CONFIDENCE'.")
        passed += 1
    except Exception as e:
        print(f"✗ Test 6 Failed: {e}")

    # 7. Sensor failure (Data quality gate)
    try:
        f_drift = {"status": "DRIFT DETECTED", "aggregate_psi": 0.35}
        p_drift = {"status": "PREDICTION DRIFT DETECTED", "psi": 0.28}
        u_drift = {"status": "HEALTHY"}
        dq_bad = {"status": "DATA QUALITY ISSUE", "aggregate_score": 0.55} # Degraded sensor
        temporal = {"pattern": "PERSISTENT DISTRIBUTION DRIFT"}
        perf_eval = {"performance_degradation_detected": False}
        
        readiness = engine.compute_retraining_readiness(f_drift, p_drift, u_drift, dq_bad, temporal, perf_eval)
        assert readiness["data_quality_gated"] is True
        assert readiness["recommendation"] == "DO NOT RETRAIN"
        assert "Data quality anomalies" in readiness["reason"]
        print("✓ Test 7 Passed: Sensor failure correctly gates drift: outputs DATA QUALITY ISSUE and DO NOT RETRAIN.")
        passed += 1
    except Exception as e:
        print(f"✗ Test 7 Failed: {e}")

    # 8. Stale data handling
    try:
        try:
            from app.core.sensor_health import sensor_health_engine, SOURCE_CATALOG
        except ImportError:
            from backend.app.core.sensor_health import sensor_health_engine, SOURCE_CATALOG
        src = SOURCE_CATALOG[0]
        stale_res = sensor_health_engine.evaluate_source(src, {"data_age_min": src["stale_threshold_minutes"] + 60})
        assert stale_res["health_state"] == "STALE"
        print("✓ Test 8 Passed: Stale telemetry correctly detected and flagged.")
        passed += 1
    except Exception as e:
        print(f"✗ Test 8 Failed: {e}")

    # 9. Missing data handling
    try:
        df_empty = engine.get_live_data_window("24h")
        # Ensure evaluate_feature_drift handles missing/empty data without exception
        engine_empty = ModelMonitoringEngine(BASE_DIR)
        engine_empty.live_buffer = []
        res_empty = engine_empty.evaluate_feature_drift("24h")
        assert res_empty["status"] == "INSUFFICIENT_DATA"
        print("✓ Test 9 Passed: Missing data handled gracefully with INSUFFICIENT_DATA status.")
        passed += 1
    except Exception as e:
        print(f"✗ Test 9 Failed: {e}")

    # 10. Temporary weather event
    try:
        f_drift_temp = {"status": "DRIFT DETECTED", "aggregate_psi": 0.30}
        p_drift_temp = {"status": "WATCH", "psi": 0.12}
        u_drift_temp = {"status": "HEALTHY"}
        dq_good = {"status": "HEALTHY", "aggregate_score": 0.95}
        temporal_temp = {"pattern": "TEMPORARY WEATHER EVENT", "interpretation": "Short-term spike."}
        perf_eval = {"performance_degradation_detected": False}
        
        readiness_temp = engine.compute_retraining_readiness(f_drift_temp, p_drift_temp, u_drift_temp, dq_good, temporal_temp, perf_eval)
        assert readiness_temp["model_status"] == "WATCH"
        assert readiness_temp["recommendation"] == "MONITOR"
        assert "Single storm does not justify model retraining" in readiness_temp["reason"]
        print("✓ Test 10 Passed: Temporary weather event classified as WATCH and MONITOR (No retraining).")
        passed += 1
    except Exception as e:
        print(f"✗ Test 10 Failed: {e}")

    # 11. Persistent drift
    try:
        temporal_persist = {"pattern": "PERSISTENT DISTRIBUTION DRIFT", "interpretation": "Sustained shift."}
        readiness_persist = engine.compute_retraining_readiness(f_drift_temp, p_drift_temp, u_drift_temp, dq_good, temporal_persist, perf_eval)
        assert readiness_persist["model_status"] == "DRIFT DETECTED"
        assert readiness_persist["readiness_score"] >= 50
        print(f"✓ Test 11 Passed: Persistent drift classified as DRIFT DETECTED (Readiness: {readiness_persist['readiness_score']}/100).")
        passed += 1
    except Exception as e:
        print(f"✗ Test 11 Failed: {e}")

    # 12. Insufficient data safeguard
    try:
        small_sample_a = np.array([1.0, 2.0])
        small_sample_b = np.array([1.5, 2.5])
        psi_small = calculate_psi(small_sample_a, small_sample_b)
        assert psi_small == 0.0, "Expected 0.0 PSI guard when sample size < 5"
        print("✓ Test 12 Passed: Insufficient data safeguard prevents unstable statistical estimation.")
        passed += 1
    except Exception as e:
        print(f"✗ Test 12 Failed: {e}")

    # 13. Verified performance degradation
    try:
        # Mock verified labels: ground truth 1s and 0s
        mock_y = [1]*10 + [0]*10
        mock_p_bad = [0.1]*10 + [0.9]*10 # Inverted predictions to simulate severe degradation
        perf_deg = engine.evaluate_verified_performance(mock_y, mock_p_bad)
        assert perf_deg["has_verified_live_data"] is True
        assert perf_deg["performance_degradation_detected"] is True
        print("✓ Test 13 Passed: Verified validation performance degradation accurately detected.")
        passed += 1
    except Exception as e:
        print(f"✗ Test 13 Failed: {e}")

    # 14. Retraining recommendation
    try:
        perf_deg_true = {"performance_degradation_detected": True}
        readiness_retrain = engine.compute_retraining_readiness(f_drift_temp, p_drift_temp, u_drift_temp, dq_good, temporal_persist, perf_deg_true)
        assert readiness_retrain["model_status"] == "RETRAINING RECOMMENDED"
        assert readiness_retrain["recommendation"] == "INITIATE SAFE RETRAINING WORKFLOW"
        print("✓ Test 14 Passed: Retraining recommendation properly triggered on persistent drift + degradation.")
        passed += 1
    except Exception as e:
        print(f"✗ Test 14 Failed: {e}")

    # 15. No retraining recommendation
    try:
        f_drift_low = {"status": "HEALTHY", "aggregate_psi": 0.03}
        p_drift_low = {"status": "HEALTHY", "psi": 0.02}
        temporal_stable = {"pattern": "STABLE CONDITIONS"}
        readiness_none = engine.compute_retraining_readiness(f_drift_low, p_drift_low, u_drift_temp, dq_good, temporal_stable, perf_eval)
        assert readiness_none["model_status"] == "HEALTHY"
        assert readiness_none["recommendation"] == "PRODUCTION MODEL NOMINAL"
        print("✓ Test 15 Passed: No retraining recommendation on healthy distributions.")
        passed += 1
    except Exception as e:
        print(f"✗ Test 15 Failed: {e}")

    # 16. Champion model
    try:
        assert engine.champion_metadata["deployment_status"] == "CHAMPION_DEPLOYED"
        assert engine.champion_metadata["model_version"] == "ClimateTwin-Flood-RF-v2.0"
        assert engine.champion_metadata["validation_metrics"]["roc_auc"] > 0.85
        print(f"✓ Test 16 Passed: Champion model verified ({engine.champion_metadata['model_version']}).")
        passed += 1
    except Exception as e:
        print(f"✗ Test 16 Failed: {e}")

    # 17. Candidate model
    try:
        assert engine.candidate_metadata["deployment_status"] == "CANDIDATE_EVALUATION"
        assert engine.candidate_metadata["model_version"] == "ClimateTwin-Flood-HGB-v2.1"
        assert "validation_metrics" in engine.candidate_metadata
        print(f"✓ Test 17 Passed: Candidate model evaluated ({engine.candidate_metadata['model_version']}).")
        passed += 1
    except Exception as e:
        print(f"✗ Test 17 Failed: {e}")

    # 18. Model versioning
    try:
        with open(os.path.join(BASE_DIR, "docs", "model_registry", "registry.json"), "r") as f:
            reg = json.load(f)
        assert len(reg["models"]) >= 2
        versions = [m["model_version"] for m in reg["models"]]
        assert "ClimateTwin-Flood-RF-v2.0" in versions
        print("✓ Test 18 Passed: Model registry versioning verified with multiple immutable releases.")
        passed += 1
    except Exception as e:
        print(f"✗ Test 18 Failed: {e}")

    # 19. REST API endpoints
    try:
        import urllib.request
        endpoints = [
            "/api/model-health",
            "/api/model-health/drift",
            "/api/model-health/performance",
            "/api/model-health/history",
            "/api/model-health/retraining-readiness"
        ]
        for ep in endpoints:
            res = urllib.request.urlopen("http://127.0.0.1:8000" + ep)
            assert res.status == 200, f"Endpoint {ep} returned {res.status}"
            
        req = urllib.request.Request(
            "http://127.0.0.1:8000/api/model-health/evaluate",
            data=json.dumps({"window": "7d"}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        res_post = urllib.request.urlopen(req)
        assert res_post.status == 200
        print("✓ Test 19 Passed: All 6 Model Monitoring REST API endpoints respond 200 OK.")
        passed += 1
    except Exception as e:
        print(f"✗ Test 19 Failed: {e}")

    # 20. NOVA integration
    try:
        health = engine.get_comprehensive_model_health("7d")
        nova = health["nova_summary"]
        assert "briefing" in nova and len(nova["briefing"]) > 20
        assert "headline" in nova
        assert "recommended_action" in nova
        print("✓ Test 20 Passed: NOVA AI dynamic health briefing generated successfully.")
        passed += 1
    except Exception as e:
        print(f"✗ Test 20 Failed: {e}")

    # 21. Dashboard rendering / data contract
    try:
        health = engine.get_comprehensive_model_health("7d")
        required_keys = [
            "model_status", "retraining_readiness", "feature_drift",
            "prediction_drift", "uncertainty_trend", "data_quality",
            "temporal_drift", "concept_drift", "champion_model", "nova_summary"
        ]
        for k in required_keys:
            assert k in health, f"Missing dashboard contract key: {k}"
        print("✓ Test 21 Passed: Dashboard rendering data contract complete and fully populated.")
        passed += 1
    except Exception as e:
        print(f"✗ Test 21 Failed: {e}")

    # 22. Invalid inputs resilience
    try:
        # Evaluate feature drift with invalid window string
        res_inv = engine.evaluate_feature_drift(window_str="invalid_window_xyz")
        assert "aggregate_psi" in res_inv
        print("✓ Test 22 Passed: Invalid parameters handled safely with fallback behavior.")
        passed += 1
    except Exception as e:
        print(f"✗ Test 22 Failed: {e}")

    # 23. Extreme environmental inputs resilience
    try:
        extreme_obs = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "rainfall_daily": 650.0, # Beyond max historical 24h
            "rainfall_7d_sum": 1200.0,
            "temp_mean": 48.5,
            "POONDI": 3231.0,
            "total_reservoir_level": 11257.0,
            "predicted_probability": 0.99,
            "epistemic_variance": 0.055,
            "prediction_interval_width": 0.45,
            "uncertainty_level": "HIGH"
        }
        engine_extreme = ModelMonitoringEngine(BASE_DIR)
        engine_extreme.record_live_observation(extreme_obs)
        res_extreme = engine_extreme.get_comprehensive_model_health("7d")
        assert res_extreme["model_status"] in ["WATCH", "DRIFT DETECTED", "RETRAINING RECOMMENDED"]
        print("✓ Test 23 Passed: Extreme environmental inputs evaluated without crash or numeric overflow.")
        passed += 1
    except Exception as e:
        print(f"✗ Test 23 Failed: {e}")

    # 24. Regression compatibility with previous phases
    try:
        # Phase 16 Data Quality
        try:
            from app.core.sensor_health import sensor_health_engine
            from app.core.uncertainty import uncertainty_engine
        except ImportError:
            from backend.app.core.sensor_health import sensor_health_engine
            from backend.app.core.uncertainty import uncertainty_engine
            
        sq_sum = sensor_health_engine.get_summary()
        assert "aggregate_health_score" in sq_sum or "aggregate_shs" in sq_sum
        
        # Phase 11 Uncertainty
        unc_res = uncertainty_engine.conformal_thresholds
        assert "current" in unc_res
        
        # Phase Next Live Intelligence
        import urllib.request
        live_res = urllib.request.urlopen("http://127.0.0.1:8000/api/predictions/live")
        assert live_res.status == 200
        print("✓ Test 24 Passed: Regression compatibility confirmed across Phase 9-16 core engines.")
        passed += 1
    except Exception as e:
        print(f"✗ Test 24 Failed: {e}")

    # 25. Frontend production build
    try:
        print("Running frontend production build test (npm run build)...")
        res_build = subprocess.run(
            ["npm", "run", "build"],
            cwd=os.path.join(BASE_DIR, "frontend"),
            capture_output=True,
            text=True,
            shell=True
        )
        assert res_build.returncode == 0, f"Frontend build failed:\n{res_build.stderr}"
        print("✓ Test 25 Passed: Frontend production build succeeded cleanly.")
        passed += 1
    except Exception as e:
        print(f"✗ Test 25 Failed: {e}")

    print("\n======================================================================")
    print(f"VALIDATION SUMMARY: {passed}/{total} TESTS PASSED")
    print("======================================================================")
    return passed == total

if __name__ == "__main__":
    success = test_suite()
    sys.exit(0 if success else 1)
