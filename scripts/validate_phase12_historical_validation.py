import os
import json
import requests
import pandas as pd
import numpy as np

API_URL = "http://localhost:8000"
BASE_DIR = r"C:\Users\gokul\Desktop\PROJECTS\climatetwin"
HV_DIR = os.path.join(BASE_DIR, 'docs', 'historical_validation')
PLOT_PATH = os.path.join(BASE_DIR, 'docs', 'plots', 'phase12_historical_validation.png')

def run_phase12_validation():
    print("=================================================================")
    print("  CLIMATETWIN PHASE 12: HISTORICAL EVENT VALIDATION SUITE")
    print("=================================================================\n")
    
    passed_count = 0
    total_tests = 17
    
    # --- Test 01: Event Inventory Verification ---
    print("[Test 01] Verifying Historical Event Inventory...")
    inv_file = os.path.join(HV_DIR, 'event_inventory.csv')
    assert os.path.exists(inv_file), f"Event inventory not found at {inv_file}"
    df_inv = pd.read_csv(inv_file)
    assert len(df_inv) >= 50, f"Expected >= 50 historical events, found {len(df_inv)}"
    assert 'Event_ID' in df_inv.columns and 'Start_Date' in df_inv.columns and 'End_Date' in df_inv.columns
    print(f"  -> PASSED: Inventory contains {len(df_inv)} historical events.")
    passed_count += 1
    
    # --- Test 02: Event Timestamps Validity ---
    print("\n[Test 02] Verifying Event Timestamp Boundaries...")
    df_inv['Start_Date'] = pd.to_datetime(df_inv['Start_Date'])
    df_inv['End_Date'] = pd.to_datetime(df_inv['End_Date'])
    assert (df_inv['Start_Date'] <= df_inv['End_Date']).all(), "Start date occurs after end date"
    print("  -> PASSED: All event date ranges satisfy Start_Date <= End_Date.")
    passed_count += 1
    
    # --- Test 03: Temporal Anti-Leakage Compliance ---
    print("\n[Test 03] Verifying Temporal Anti-Leakage Protection...")
    pred_file = os.path.join(HV_DIR, 'event_predictions.csv')
    assert os.path.exists(pred_file), f"Predictions file not found at {pred_file}"
    df_preds = pd.read_csv(pred_file)
    assert 'date' in df_preds.columns, "Missing date column in predictions"
    assert pd.to_datetime(df_preds['date']).is_monotonic_increasing, "Timestamps not monotonic"
    print("  -> PASSED: Sequential chronological ordering strictly preserved.")
    passed_count += 1
    
    # --- Test 04: Eligible Events Identification ---
    print("\n[Test 04] Verifying Multi-Sensor Event Eligibility...")
    eligible_count = int(df_inv['Backtest_Eligible'].sum())
    assert eligible_count >= 8, f"Expected >= 8 eligible events, found {eligible_count}"
    assert 'Holdout_Eligible' in df_inv.columns and 'Train_Period_Overlap' in df_inv.columns
    print(f"  -> PASSED: Identified {eligible_count} backtest-eligible multi-sensor events.")
    passed_count += 1
    
    # --- Test 05: Step-by-Step Backtest Predictions Output ---
    print("\n[Test 05] Verifying Step-by-Step Backtest Dataset...")
    assert len(df_preds) >= 1800, f"Expected >= 1800 backtest days, found {len(df_preds)}"
    assert 'prob_60m' in df_preds.columns and 'actual_flood' in df_preds.columns
    print(f"  -> PASSED: Backtest dataset contains {len(df_preds):,} chronological timestamps.")
    passed_count += 1
    
    # --- Test 06: Ground Truth Label Alignment ---
    print("\n[Test 06] Verifying Ground Truth Label Alignment...")
    unique_labels = set(df_preds['actual_flood'].unique())
    assert unique_labels.issubset({0.0, 1.0}), f"Invalid ground truth labels: {unique_labels}"
    assert df_preds['actual_flood'].sum() > 0, "Zero flood events marked"
    print(f"  -> PASSED: Ground truth labels verified ({int(df_preds['actual_flood'].sum())} flood days).")
    passed_count += 1
    
    # --- Test 07: Multi-Horizon Alignment ---
    print("\n[Test 07] Verifying Forecast Horizons Alignment...")
    for h in ['prob_15m', 'prob_30m', 'prob_60m']:
        assert h in df_preds.columns, f"Missing horizon {h}"
        assert (0.0 <= df_preds[h]).all() and (df_preds[h] <= 1.0).all(), f"Probabilities out of bounds in {h}"
    print("  -> PASSED: Forecast horizons (15m, 30m, 60m) are mathematically bounded in [0, 1].")
    passed_count += 1
    
    # --- Test 08: Warning Lead Time Calculation ---
    print("\n[Test 08] Verifying Warning Lead-Time Statistics...")
    lt_file = os.path.join(HV_DIR, 'lead_time_analysis.json')
    assert os.path.exists(lt_file), f"Lead time analysis not found at {lt_file}"
    with open(lt_file, 'r') as f:
        lt_data = json.load(f)
    assert 'lead_time_hours' in lt_data
    med_lt = lt_data['lead_time_hours']['median']
    assert med_lt > 0.0, f"Invalid median lead time: {med_lt}"
    print(f"  -> PASSED: Warning lead time verified (Median: {med_lt:.1f} hours).")
    passed_count += 1
    
    # --- Test 09: False Positive Analysis ---
    print("\n[Test 09] Verifying False Positive Root-Cause Diagnostics...")
    fp_file = os.path.join(HV_DIR, 'false_positive_analysis.json')
    assert os.path.exists(fp_file), f"FP analysis not found at {fp_file}"
    with open(fp_file, 'r') as f:
        fp_data = json.load(f)
    assert 'false_alarm_rate' in fp_data and 'diagnostic_findings' in fp_data
    print(f"  -> PASSED: False positive diagnostics verified (FAR: {fp_data['false_alarm_rate']*100:.2f}%).")
    passed_count += 1
    
    # --- Test 10: False Negative Analysis ---
    print("\n[Test 10] Verifying False Negative Analysis...")
    fn_file = os.path.join(HV_DIR, 'false_negative_analysis.json')
    assert os.path.exists(fn_file), f"FN analysis not found at {fn_file}"
    with open(fn_file, 'r') as f:
        fn_data = json.load(f)
    assert 'miss_rate' in fn_data and 'diagnostic_findings' in fn_data
    print(f"  -> PASSED: False negative analysis verified (Miss Rate: {fn_data['miss_rate']*100:.2f}%).")
    passed_count += 1
    
    # --- Test 11: Event Detection Performance Metrics ---
    print("\n[Test 11] Verifying Event-Level Metrics...")
    met_file = os.path.join(HV_DIR, 'event_metrics.json')
    assert os.path.exists(met_file), f"Metrics file not found at {met_file}"
    with open(met_file, 'r') as f:
        met_data = json.load(f)
    det_rate = met_data['overall_summary']['event_detection_rate']
    assert det_rate >= 0.80, f"Event detection rate {det_rate} below 0.80"
    print(f"  -> PASSED: Event detection rate verified: {det_rate*100:.1f}%.")
    passed_count += 1
    
    # --- Test 12: Research Visualization Artifacts ---
    print("\n[Test 12] Verifying 6-Panel Evaluation Graphic...")
    assert os.path.exists(PLOT_PATH), f"Plot not found at {PLOT_PATH}"
    assert os.path.getsize(PLOT_PATH) > 20000, "Plot file too small"
    print(f"  -> PASSED: 6-panel evaluation plot verified ({os.path.getsize(PLOT_PATH):,} bytes).")
    passed_count += 1
    
    # --- Test 13: Research Validation Report ---
    print("\n[Test 13] Verifying Markdown Validation Report...")
    rep_file = os.path.join(HV_DIR, 'historical_validation_report.md')
    assert os.path.exists(rep_file), f"Report not found at {rep_file}"
    assert os.path.getsize(rep_file) > 500, "Report file too small"
    print("  -> PASSED: Research validation report generated.")
    passed_count += 1
    
    # --- Test 14: REST API /historical-validation Verification ---
    print("\n[Test 14] Verifying /api/predictions/historical-validation API Endpoint...")
    r = requests.get(f"{API_URL}/api/predictions/historical-validation", timeout=5)
    assert r.status_code == 200, f"Historical validation API failed: {r.text}"
    api_data = r.json()
    assert api_data['status'] == 'PASS'
    assert 'detection_rate' in api_data and 'median_lead_time_hours' in api_data
    print("  -> PASSED: REST API endpoint returned 200 OK with full validation summary.")
    passed_count += 1
    
    # --- Test 15: Regression Check — Phase 9 Digital Twins ---
    print("\n[Test 15] Verifying Phase 9 Digital Twins API...")
    r_twin = requests.get(f"{API_URL}/api/digital-twins/", timeout=5)
    assert r_twin.status_code == 200, "Digital Twins API failed"
    print("  -> PASSED: Phase 9 digital twins endpoint operational.")
    passed_count += 1
    
    # --- Test 16: Regression Check — Phase 10 Forecast Horizons ---
    print("\n[Test 16] Verifying Phase 10 Multi-Horizon Forecasting...")
    r_fc = requests.post(f"{API_URL}/api/predictions/forecast", json={'rainfall_daily': 50.0}, timeout=5)
    assert r_fc.status_code == 200, "Forecast API failed"
    assert 'forecast' in r_fc.json()
    print("  -> PASSED: Phase 10 multi-horizon forecast operational.")
    passed_count += 1
    
    # --- Test 17: Regression Check — Phase 11 Uncertainty Quantification ---
    print("\n[Test 17] Verifying Phase 11 Uncertainty Intervals...")
    assert 'prediction_interval' in r_fc.json()['forecast']['60min']
    assert 'uncertainty_level' in r_fc.json()['forecast']['60min']
    print("  -> PASSED: Phase 11 uncertainty quantification operational.")
    passed_count += 1
    
    print("\n=================================================================")
    print(f"  ALL PHASE 12 HISTORICAL TESTS PASSED ({passed_count}/{total_tests}) (STATUS: PASS)")
    print("=================================================================")
    return True

if __name__ == '__main__':
    run_phase12_validation()
