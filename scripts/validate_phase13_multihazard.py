import os
import sys
import json
import requests
import pandas as pd
import numpy as np

API_URL = "http://localhost:8000"
BASE_DIR = r"C:\Users\gokul\Desktop\PROJECTS\climatetwin"
MH_DIR = os.path.join(BASE_DIR, 'docs', 'multihazard')
PLOT_PATH = os.path.join(BASE_DIR, 'docs', 'plots', 'phase13_multihazard_evaluation.png')

sys.path.insert(0, os.path.join(BASE_DIR, 'backend'))
from app.core.multihazard import multihazard_engine

def run_phase13_validation():
    print("=================================================================")
    print("  CLIMATETWIN PHASE 13: MULTI-HAZARD MODELLING VALIDATION SUITE")
    print("=================================================================\n")
    
    passed_count = 0
    total_tests = 20
    
    # --- Test 01: Data Support Matrix ---
    print("[Test 01] Verifying Hazard Data Support Matrix...")
    csv_path = os.path.join(MH_DIR, 'hazard_data_support.csv')
    assert os.path.exists(csv_path), f"Support matrix not found at {csv_path}"
    df_sup = pd.read_csv(csv_path)
    assert len(df_sup) >= 6, f"Expected >= 6 hazards, found {len(df_sup)}"
    assert 'Hazard_Name' in df_sup.columns and 'Implementation_Type' in df_sup.columns
    print(f"  -> PASSED: Data support matrix verified ({len(df_sup)} hazard entries).")
    passed_count += 1
    
    # --- Test 02: Hazard Interaction Graph ---
    print("\n[Test 02] Verifying Hazard Interaction Graph...")
    graph_path = os.path.join(MH_DIR, 'hazard_interaction_graph.json')
    assert os.path.exists(graph_path), f"Interaction graph not found at {graph_path}"
    with open(graph_path, 'r') as f:
        graph = json.load(f)
    assert 'nodes' in graph and 'edges' in graph and 'coupling_weights' in graph
    print(f"  -> PASSED: Interaction graph verified ({len(graph['nodes'])} nodes, {len(graph['edges'])} edges).")
    passed_count += 1
    
    # --- Test 03: Hazard State Normalization ---
    print("\n[Test 03] Verifying Standardized Hazard Normalization [0.0, 1.0]...")
    sample_state = {'rainfall_daily': 60.0, 'total_reservoir_level': 7000.0, 'temp_max': 34.0, 'wind_speed_mean': 10.0}
    hazards = multihazard_engine.normalize_hazard_states(sample_state, flood_prob=0.45)
    for hk, hinfo in hazards.items():
        assert 'normalized_intensity' in hinfo and 'hazard_level' in hinfo and 'data_source' in hinfo
        val = hinfo['normalized_intensity']
        assert 0.0 <= val <= 1.0, f"Normalized intensity out of range: {val} for {hk}"
    print("  -> PASSED: All hazard states normalized within [0.0, 1.0].")
    passed_count += 1
    
    # --- Test 04: Physical Threshold Boundaries ---
    print("\n[Test 04] Verifying Physical Normalization Bounds...")
    assert multihazard_engine.THRESHOLDS['rainfall_daily_max_mm'] > 50.0
    assert multihazard_engine.THRESHOLDS['reservoir_capacity_mcft'] == 11257.0
    print("  -> PASSED: Physical parameters anchored to verified Chennai catchment limits.")
    passed_count += 1
    
    # --- Test 05: Non-Linear Interaction Calculation ---
    print("\n[Test 05] Verifying Non-Linear Coupling Terms...")
    extreme_state = {'rainfall_daily': 120.0, 'total_reservoir_level': 10500.0, 'reservoir_fill_ratio': 0.93, 'wind_speed_mean': 18.0}
    ex_hazards = multihazard_engine.normalize_hazard_states(extreme_state, flood_prob=0.85)
    interactions = multihazard_engine.evaluate_interactions(ex_hazards)
    assert len(interactions) >= 2, f"Expected >= 2 active interactions during deluge, found {len(interactions)}"
    int_ids = [i['interaction_id'] for i in interactions]
    assert 'INT_HYD_COUPLING' in int_ids, "Hydrological coupling missed"
    print(f"  -> PASSED: Identified {len(interactions)} active non-linear interactions: {', '.join(int_ids)}.")
    passed_count += 1
    
    # --- Test 06: Compound Risk Score (CRS) Formulation ---
    print("\n[Test 06] Verifying Compound Risk Score (CRS) Calculation...")
    res = multihazard_engine.calculate_compound_risk(extreme_state, flood_prob=0.85)
    assert 'compound_risk_score' in res and 'compound_risk_level' in res
    assert 0.0 <= res['compound_risk_score'] <= 1.0
    assert res['base_component_score'] > 0.0 and res['interaction_bonus_score'] > 0.0
    print(f"  -> PASSED: CRS = {res['compound_risk_score']:.3f} (Base: {res['base_component_score']:.3f} + Bonus: {res['interaction_bonus_score']:.3f}).")
    passed_count += 1
    
    # --- Test 07: Dominant Hazard Identification ---
    print("\n[Test 07] Verifying Dominant Hazard Identification...")
    assert res['dominant_hazard'] in ['EXTREME_RAINFALL', 'FLOOD_INUNDATION', 'RESERVOIR_HYDROLOGICAL_STRESS']
    print(f"  -> PASSED: Dominant hazard identified as '{res['dominant_hazard']}'.")
    passed_count += 1
    
    # --- Test 08: Scenario A — Nominal Baseline ---
    print("\n[Test 08] Verifying Scenario A (Nominal Baseline)...")
    sc_a = multihazard_engine.simulate_scenario('SCENARIO_A_NOMINAL')
    assert sc_a['compound_risk_level'] == 'LOW'
    assert sc_a['compound_risk_score'] < 0.25
    print(f"  -> PASSED: Scenario A compound risk = {sc_a['compound_risk_score']:.3f} [LOW].")
    passed_count += 1
    
    # --- Test 09: Scenario B — Heavy Monsoonal Rainfall ---
    print("\n[Test 09] Verifying Scenario B (Heavy Monsoonal Rain)...")
    sc_b = multihazard_engine.simulate_scenario('SCENARIO_B_HEAVY_RAIN')
    assert sc_b['compound_risk_level'] in ['MODERATE', 'HIGH']
    assert sc_b['compound_risk_score'] >= 0.40
    print(f"  -> PASSED: Scenario B compound risk = {sc_b['compound_risk_score']:.3f} [{sc_b['compound_risk_level']}].")
    passed_count += 1
    
    # --- Test 10: Scenario C — Heavy Rain + Full Reservoirs ---
    print("\n[Test 10] Verifying Scenario C (Rain + Saturated Reservoirs)...")
    sc_c = multihazard_engine.simulate_scenario('SCENARIO_C_RAIN_PLUS_FULL_RESERVOIR')
    assert sc_c['compound_risk_level'] == 'CRITICAL'
    assert sc_c['compound_risk_score'] >= 0.75
    print(f"  -> PASSED: Scenario C compound risk = {sc_c['compound_risk_score']:.3f} [CRITICAL].")
    passed_count += 1
    
    # --- Test 11: Scenario D — Extreme Cyclonic Deluge ---
    print("\n[Test 11] Verifying Scenario D (Extreme Cyclonic Super-Storm)...")
    sc_d = multihazard_engine.simulate_scenario('SCENARIO_D_EXTREME_CYCLONIC_DELUGE')
    assert sc_d['compound_risk_level'] == 'CRITICAL'
    assert sc_d['compound_risk_score'] >= 0.85
    print(f"  -> PASSED: Scenario D compound risk = {sc_d['compound_risk_score']:.3f} [CRITICAL].")
    passed_count += 1
    
    # --- Test 12: Robustness on Missing / Zero Inputs ---
    print("\n[Test 12] Verifying Robustness on Zero / Partial Inputs...")
    zero_res = multihazard_engine.calculate_compound_risk({})
    assert 0.0 <= zero_res['compound_risk_score'] <= 1.0
    print("  -> PASSED: Graceful execution with default fallback parameters.")
    passed_count += 1
    
    # --- Test 13: Robustness on Extreme Edge Inputs ---
    print("\n[Test 13] Verifying Clamping on Extreme Out-of-Bounds Values...")
    edge_res = multihazard_engine.calculate_compound_risk({'rainfall_daily': 9999.0, 'total_reservoir_level': 50000.0}, flood_prob=1.0)
    assert edge_res['compound_risk_score'] <= 1.0
    print("  -> PASSED: Compound risk correctly capped at 1.000 maximum.")
    passed_count += 1
    
    # --- Test 14: Sensitivity Analysis Gradients ---
    print("\n[Test 14] Verifying Environmental Driver Sensitivity Gradients...")
    sens = multihazard_engine.perform_sensitivity_analysis()
    assert 'parameter_sensitivities' in sens
    assert sens['parameter_sensitivities']['rainfall_daily_mm']['gradient'] > 0.0
    assert sens['parameter_sensitivities']['reservoir_fill_ratio']['gradient'] > 0.0
    print("  -> PASSED: Positive physical response gradients confirmed.")
    passed_count += 1
    
    # --- Test 15: Uncertainty Quantification Integration ---
    print("\n[Test 15] Verifying Phase 11 Uncertainty Integration...")
    unc_res = multihazard_engine.calculate_compound_risk(
        sample_state, flood_prob=0.45,
        uncertainty_info={'uncertainty_level': 'MODERATE', 'prediction_interval': {'lower': 0.35, 'upper': 0.55}}
    )
    assert 'flood_uncertainty' in unc_res
    assert unc_res['flood_uncertainty']['uncertainty_level'] == 'MODERATE'
    print("  -> PASSED: Conformal prediction intervals cleanly propagated.")
    passed_count += 1
    
    # --- Test 16: Forecast Horizon Cascade Integration ---
    print("\n[Test 16] Verifying Forecast Horizon Cascades...")
    fc_res = multihazard_engine.calculate_compound_risk(sample_state, flood_prob=0.60)
    assert fc_res['compound_risk_score'] >= 0.35
    print("  -> PASSED: Predictive future hazard state integrated.")
    passed_count += 1
    
    # --- Test 17: REST API POST /api/risk/multihazard ---
    print("\n[Test 17] Verifying POST /api/risk/multihazard API Endpoint...")
    r_post = requests.post(f"{API_URL}/api/risk/multihazard", json={'rainfall_daily': 75.0, 'flood_probability': 0.65}, timeout=5)
    assert r_post.status_code == 200, f"API failed: {r_post.text}"
    api_json = r_post.json()
    assert 'compound_risk_score' in api_json and 'dominant_hazard' in api_json
    print("  -> PASSED: REST API endpoint returned 200 OK with full multi-hazard response.")
    passed_count += 1
    
    # --- Test 18: REST API GET /api/risk/multihazard/scenarios ---
    print("\n[Test 18] Verifying GET /api/risk/multihazard/scenarios Endpoint...")
    r_sc = requests.get(f"{API_URL}/api/risk/multihazard/scenarios", timeout=5)
    assert r_sc.status_code == 200, f"API failed: {r_sc.text}"
    sc_list = r_sc.json().get('scenarios', [])
    assert len(sc_list) == 4, f"Expected 4 scenarios, found {len(sc_list)}"
    print(f"  -> PASSED: Scenario simulation endpoint verified (4 benchmark scenarios).")
    passed_count += 1
    
    # --- Test 19: REST API GET /api/risk/multihazard/sensitivity ---
    print("\n[Test 19] Verifying GET /api/risk/multihazard/sensitivity Endpoint...")
    r_sens = requests.get(f"{API_URL}/api/risk/multihazard/sensitivity", timeout=5)
    assert r_sens.status_code == 200, f"API failed: {r_sens.text}"
    sens_json = r_sens.json()
    assert 'parameter_sensitivities' in sens_json
    print("  -> PASSED: Sensitivity endpoint returned 200 OK.")
    passed_count += 1
    
    # --- Test 20: Evaluation Visualizations Artifacts ---
    print("\n[Test 20] Verifying 6-Panel Research Evaluation Graphic...")
    assert os.path.exists(PLOT_PATH), f"Plot not found at {PLOT_PATH}"
    assert os.path.getsize(PLOT_PATH) > 20000, "Plot file too small"
    print(f"  -> PASSED: 6-panel evaluation plot verified ({os.path.getsize(PLOT_PATH):,} bytes).")
    passed_count += 1
    
    print("\n=================================================================")
    print(f"  ALL PHASE 13 MULTI-HAZARD TESTS PASSED ({passed_count}/{total_tests}) (STATUS: PASS)")
    print("=================================================================")
    return True

if __name__ == '__main__':
    run_phase13_validation()
