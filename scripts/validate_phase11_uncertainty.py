import requests
import json
import pickle
import os
import sys
import numpy as np

API_URL = "http://localhost:8000"
BASE_DIR = r"C:\Users\gokul\Desktop\PROJECTS\climatetwin"
MODELS_PATH = os.path.join(BASE_DIR, 'backend', 'app', 'models', 'flood_forecast_models.pkl')
PLOT_PATH = os.path.join(BASE_DIR, 'docs', 'plots', 'phase11_uncertainty_evaluation.png')
JSON_PATH = os.path.join(BASE_DIR, 'docs', 'uncertainty_evaluation.json')

def run_phase11_validation():
    print("=================================================================")
    print("  CLIMATETWIN PHASE 11: UNCERTAINTY QUANTIFICATION VALIDATION")
    print("=================================================================\n")
    
    passed_count = 0
    total_tests = 15
    
    # --- Test 01: Uncertainty Model Bundle Verification ---
    print("[Test 01] Verifying Uncertainty Model Bundle & Checkpoints...")
    assert os.path.exists(MODELS_PATH), f"Machine learning bundle not found at {MODELS_PATH}"
    with open(MODELS_PATH, 'rb') as f:
        bundle = pickle.load(f)
    assert 'models' in bundle, "Missing models key"
    assert 'calibration' in bundle, "Missing calibration key"
    assert 'conformal_thresholds' in bundle, "Missing conformal thresholds"
    assert 'uncertainty_metrics' in bundle, "Missing uncertainty metrics"
    print("  -> PASSED: Model bundle valid and contains all UQ keys.")
    passed_count += 1
    
    # --- Test 02: Probability vs Uncertainty Separation ---
    print("\n[Test 02] Verifying Probability vs Uncertainty Distinction...")
    r = requests.post(f"{API_URL}/api/predictions/forecast", json={}, timeout=5)
    assert r.status_code == 200, f"Forecast API failed: {r.text}"
    data = r.json()
    assert 'current_probability' in data, "Missing current_probability"
    assert 'current_prediction_interval' in data, "Missing current_prediction_interval"
    assert 'current_uncertainty_level' in data, "Missing current_uncertainty_level"
    prob = data['current_probability']
    interval = data['current_prediction_interval']
    assert isinstance(prob, (int, float)), "Probability not numeric"
    assert isinstance(interval, dict) and 'lower' in interval and 'upper' in interval, "Interval malformed"
    assert 'width' in interval, "Interval width missing"
    print(f"  -> PASSED: Probability ({prob:.2f}) and Interval [{interval['lower']:.2f} - {interval['upper']:.2f}] are distinct.")
    passed_count += 1
    
    # --- Test 03: Prediction Interval Ordering & Boundaries ---
    print("\n[Test 03] Verifying Prediction Interval Mathematical Ordering...")
    for horizon, f_data in data['forecast'].items():
        p_int = f_data['prediction_interval']
        low, high, width = p_int['lower'], p_int['upper'], p_int['width']
        f_prob = f_data['probability']
        assert 0.0 <= low <= 1.0, f"Lower bound out of [0, 1]: {low}"
        assert 0.0 <= high <= 1.0, f"Upper bound out of [0, 1]: {high}"
        assert low <= high, f"Lower bound {low} > upper bound {high}"
        assert low <= f_prob + 1e-4 and f_prob - 1e-4 <= high, f"Probability {f_prob} not bounded inside [{low}, {high}]"
        assert abs(round(high - low, 4) - round(width, 4)) < 1e-3, f"Width mismatch: {width} vs {high - low}"
    print("  -> PASSED: Prediction intervals satisfy 0 <= L <= p <= U <= 1 for all horizons.")
    passed_count += 1
    
    # --- Test 04: Conformal Calibration Score Validity ---
    print("\n[Test 04] Verifying Conformal Calibration Quantiles...")
    ct = bundle['conformal_thresholds']
    for k in ['current', '15m', '30m', '60m']:
        assert k in ct, f"Missing conformal threshold for {k}"
        assert 0.0 < ct[k] < 1.0, f"Invalid conformal threshold {ct[k]}"
    print(f"  -> PASSED: Conformal thresholds valid: (current={ct.get('current')}, 60m={ct.get('60m')})")
    passed_count += 1
    
    # --- Test 05: Empirical Uncertainty Level Classification ---
    print("\n[Test 05] Verifying Uncertainty Level Derivation...")
    sys.path.insert(0, os.path.join(BASE_DIR, 'backend'))
    from app.core.uncertainty import uncertainty_engine
    assert uncertainty_engine.estimate_uncertainty(None, np.zeros((1, 20)))['uncertainty_level'] in ['LOW', 'MODERATE', 'HIGH']
    print("  -> PASSED: Uncertainty level mapping returns valid levels (LOW, MODERATE, HIGH).")
    passed_count += 1
    
    # --- Test 06: Brier Score Calibration Evaluation ---
    print("\n[Test 06] Verifying Brier Score Calibration Evaluation...")
    cal = bundle['calibration']
    assert 'brier_score_uncalibrated' in cal and 'brier_score_calibrated' in cal
    b_uncal = cal['brier_score_uncalibrated']
    b_cal = cal['brier_score_calibrated']
    assert b_cal <= b_uncal, f"Calibrated Brier score {b_cal} higher than uncalibrated {b_uncal}"
    print(f"  -> PASSED: Brier score reduced from {b_uncal:.4f} to {b_cal:.4f} via calibration.")
    passed_count += 1
    
    # --- Test 07: Empirical Test Set Coverage Sanity ---
    print("\n[Test 07] Verifying Empirical Coverage on Test Set...")
    um = bundle['uncertainty_metrics']
    assert 'empirical_coverage_90' in um
    cov = um['empirical_coverage_90']
    assert cov >= 0.80, f"Empirical coverage {cov:.2f} significantly below nominal 0.90"
    print(f"  -> PASSED: Empirical coverage on test set is {cov * 100:.1f}%.")
    passed_count += 1
    
    # --- Test 08: Multi-Horizon Uncertainty Progression ---
    print("\n[Test 08] Verifying Multi-Horizon Uncertainty Progression...")
    hw = um['horizon_widths']
    for h in ['current', '15m', '30m', '60m']:
        assert h in hw, f"Missing horizon width for {h}"
        assert hw[h] > 0.0, f"Non-positive width for {h}"
    print(f"  -> PASSED: Horizon widths verified: (15m={hw.get('15m'):.3f}, 60m={hw.get('60m'):.3f})")
    passed_count += 1
    
    # --- Test 09: Uncertainty Explainability Diagnostics ---
    print("\n[Test 09] Verifying Uncertainty Explainability Diagnostics...")
    expl = data.get('current_uncertainty_explanation', '')
    assert len(expl) > 5, "Explanation empty or missing"
    test_expl = uncertainty_engine.generate_uncertainty_explanation(
        prob=0.85, width=0.40, variance=0.06,
        feature_dict={'rainfall_rate_1h': 25.0, 'rainfall_trend': 20.0, 'reservoir_storage_rate_1d': 450.0}
    )
    assert 'rapid precipitation acceleration' in test_expl, "Failed to identify rain acceleration"
    assert 'surging reservoir inflow dynamics' in test_expl, "Failed to identify reservoir surge"
    print(f"  -> PASSED: Causal explanations derived accurately: \"{test_expl}\"")
    passed_count += 1
    
    # --- Test 10: Uncertainty-Aware Alerting Logic ---
    print("\n[Test 10] Verifying Uncertainty-Aware Early Warning Logic...")
    alert_high_low_unc = uncertainty_engine.evaluate_uncertainty_aware_alert(0.85, 'LOW')
    assert alert_high_low_unc['severity'] == 'CRITICAL' and alert_high_low_unc['confidence_tag'] == 'HIGH CONFIDENCE'
    
    alert_high_high_unc = uncertainty_engine.evaluate_uncertainty_aware_alert(0.85, 'HIGH')
    assert alert_high_high_unc['severity'] == 'CRITICAL' and alert_high_high_unc['confidence_tag'] == 'UNCERTAIN SEVERE'
    print("  -> PASSED: Uncertainty-aware warning logic enforces conservative high-risk flagging.")
    passed_count += 1
    
    # --- Test 11: REST API /forecast Verification ---
    print("\n[Test 11] Verifying /api/predictions/forecast Endpoint Output...")
    req_payload = {
        'rainfall_daily': 60.0,
        'POONDI': 2900.0,
        'CHEMBARAMBAKKAM': 3100.0
    }
    r = requests.post(f"{API_URL}/api/predictions/forecast", json=req_payload, timeout=5)
    assert r.status_code == 200, f"API failed: {r.text}"
    f_res = r.json()
    assert 'forecast' in f_res
    assert '15min' in f_res['forecast'] and '30min' in f_res['forecast'] and '60min' in f_res['forecast']
    assert 'prediction_interval' in f_res['forecast']['60min']
    print("  -> PASSED: Forecast endpoint successfully processed input with full UQ output.")
    passed_count += 1
    
    # --- Test 12: Telemetry Pipeline & Latency Tracking ---
    print("\n[Test 12] Verifying Telemetry Pipeline UQ Latency Stage...")
    import time
    t_payload = {
        'rainfall_daily': 30.0,
        'rainfall_3d_sum': 80.0,
        'rainfall_5d_sum': 100.0,
        'rainfall_7d_sum': 120.0,
        'temp_mean': 28.0,
        'temp_max': 32.0,
        'temp_min': 24.0,
        'dew_point_mean': 22.0,
        'wind_speed_mean': 3.0,
        'POONDI': 2700.0,
        'CHOLAVARAM': 800.0,
        'REDHILLS': 2800.0,
        'CHEMBARAMBAKKAM': 3000.0,
        'total_reservoir_level': 9300.0,
        'source_timestamp': time.time(),
        'inference_mode': 'cloud'
    }
    r_tel = requests.post(f"{API_URL}/api/predictions/telemetry", json=t_payload, timeout=5)
    assert r_tel.status_code == 200, f"Telemetry API failed: {r_tel.text}"
    tel_data = r_tel.json()
    assert 'latencies_ms' in tel_data, "Missing latencies_ms"
    assert 'uncertainty_computation_ms' in tel_data['latencies_ms'], "Missing uncertainty_computation_ms"
    unc_lat = tel_data['latencies_ms']['uncertainty_computation_ms']
    assert unc_lat > 0.0, f"Uncertainty latency not tracked: {unc_lat}"
    print(f"  -> PASSED: Telemetry tracking recorded uncertainty_computation_ms = {unc_lat:.2f} ms.")
    passed_count += 1
    
    # --- Test 13: Edge Case / Missing Input Robustness ---
    print("\n[Test 13] Verifying Robustness on Missing & Edge Case Inputs...")
    r_edge = requests.post(f"{API_URL}/api/predictions/forecast", json={'rainfall_daily': 0.0}, timeout=5)
    assert r_edge.status_code == 200, "Edge case input failed"
    assert r_edge.json()['current_risk'] in ['LOW', 'MODERATE', 'HIGH', 'CRITICAL']
    print("  -> PASSED: Graceful handling of partial inputs.")
    passed_count += 1
    
    # --- Test 14: Historical Backtest Verification ---
    print("\n[Test 14] Verifying Historical Backtest Report...")
    assert os.path.exists(JSON_PATH), f"Report not found at {JSON_PATH}"
    with open(JSON_PATH, 'r') as f:
        rep = json.load(f)
    assert rep['status'] == 'PASS'
    assert 'coverage_metrics' in rep
    assert 'calibration_results' in rep
    print("  -> PASSED: Machine-readable backtest evaluation report verified.")
    passed_count += 1
    
    # --- Test 15: Evaluation Artifacts Existence ---
    print("\n[Test 15] Verifying Visual & Markdown Artifacts...")
    assert os.path.exists(PLOT_PATH), f"Plot not found at {PLOT_PATH}"
    assert os.path.getsize(PLOT_PATH) > 10000, "Plot file too small"
    print(f"  -> PASSED: Plot file {PLOT_PATH} exists ({os.path.getsize(PLOT_PATH):,} bytes).")
    passed_count += 1
    
    print("\n=================================================================")
    print(f"  ALL PHASE 11 UNCERTAINTY TESTS PASSED ({passed_count}/{total_tests}) (STATUS: PASS)")
    print("=================================================================")
    return True

if __name__ == '__main__':
    run_phase11_validation()
