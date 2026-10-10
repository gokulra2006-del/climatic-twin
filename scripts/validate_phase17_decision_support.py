import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from starlette.testclient import TestClient
from app.main import app
from app.core.decision_support import (
    DecisionSupportEngine,
    DSS_WEIGHTS,
    DECISION_THRESHOLDS,
    HYSTERESIS_BAND
)

client = TestClient(app)
passed = 0
failed = 0
total = 30


def run_test(num, name, condition, detail=''):
    global passed, failed
    if condition:
        passed += 1
        print(f'[Test {num:02d}] {name}\n  -> PASSED: {detail}')
    else:
        failed += 1
        print(f'[Test {num:02d}] {name}\n  -> FAILED: {detail}')


print('=' * 65)
print('  CLIMATETWIN PHASE 17: DECISION SUPPORT VALIDATION SUITE')
print('=' * 65)
print()

engine = DecisionSupportEngine()

# Test 01: Core decision engine exists
cond01 = isinstance(engine, DecisionSupportEngine) and hasattr(engine, 'assess') and callable(getattr(engine, 'assess'))
run_test(1, 'Core Decision Engine Instance & assess() Method', cond01, 'DecisionSupportEngine instantiated with callable assess() method')

# Test 02: Decision score bounds [0.0, 1.0]
res02 = engine.assess()
cond02 = isinstance(res02, dict) and 'decision_score' in res02 and 0.0 <= res02['decision_score'] <= 1.0
run_test(2, 'Decision Score Mathematical Bounds [0.0, 1.0]', cond02, f"Default assessment score: {res02.get('decision_score', 'N/A')} in [0.0, 1.0]")

# Test 03: Weight sum correctness
weight_sum = sum(DSS_WEIGHTS.values())
cond03 = abs(weight_sum - 1.0) < 1e-6
run_test(3, 'DSS Component Weights Sum Correctness', cond03, f"Weights sum to {weight_sum:.4f} (1.0)")

# Test 04: Hazard normalization
h_norm = engine.normalize_hazard_severity(0.5, 0.5, 0.5)
cond04 = 0.0 <= h_norm <= 1.0
run_test(4, 'Hazard Severity Normalization', cond04, f"Normalized hazard severity: {h_norm:.4f}")

# Test 05: Asset risk integration
a_norm = engine.normalize_asset_risk(0.8, 1.0, 0.9)
cond05 = 0.0 <= a_norm <= 1.0
run_test(5, 'Asset Risk Integration & Normalization', cond05, f"Normalized asset risk: {a_norm:.4f}")

# Test 06: Multi-hazard integration
c_norm = engine.normalize_compound_risk(0.75)
cond06 = c_norm == 0.75
run_test(6, 'Compound Multi-Hazard Integration', cond06, f"Normalized compound risk: {c_norm:.4f}")

# Test 07: Forecast confidence integration (high uncertainty -> low confidence)
fc_norm = engine.normalize_forecast_confidence('HIGH', 0.5, 0.05)
cond07 = 0.0 <= fc_norm <= 1.0 and fc_norm < 0.5
run_test(7, 'Forecast Confidence Integration under High Uncertainty', cond07, f"Confidence score: {fc_norm:.4f} (< 0.5 for HIGH uncertainty)")

# Test 08: Data quality integration
dq_norm = engine.normalize_data_quality(0.95, 0, 0, 0)
cond08 = 0.0 <= dq_norm <= 1.0 and dq_norm > 0.8
run_test(8, 'Data Quality Normalization for Nominal Telemetry', cond08, f"Normalized data quality: {dq_norm:.4f} (> 0.8)")

# Test 09: Persistence integration
p_rising = engine.normalize_persistence(5, 'RISING')
p_stable = engine.normalize_persistence(0, 'STABLE')
cond09 = p_rising > p_stable
run_test(9, 'Persistence & Hazard Trend Integration', cond09, f"Persistence (5, RISING)={p_rising:.2f} > (0, STABLE)={p_stable:.2f}")

# Test 10: NORMAL classification (DSS < 0.40)
cl_10 = engine.classify_decision_level(0.20)
cond10 = cl_10 == 'NORMAL'
run_test(10, 'NORMAL Decision Level Classification', cond10, f"DSS 0.20 classified as '{cl_10}'")

# Test 11: MONITOR classification (DSS 0.40 - 0.55)
cl_11 = engine.classify_decision_level(0.45)
cond11 = cl_11 == 'MONITOR'
run_test(11, 'MONITOR Decision Level Classification', cond11, f"DSS 0.45 classified as '{cl_11}'")

# Test 12: PREPARE classification (DSS 0.55 - 0.70)
cl_12 = engine.classify_decision_level(0.60)
cond12 = cl_12 == 'PREPARE'
run_test(12, 'PREPARE Decision Level Classification', cond12, f"DSS 0.60 classified as '{cl_12}'")

# Test 13: ALERT classification (DSS 0.70 - 0.85)
cl_13 = engine.classify_decision_level(0.75)
cond13 = cl_13 == 'ALERT'
run_test(13, 'ALERT Decision Level Classification', cond13, f"DSS 0.75 classified as '{cl_13}'")

# Test 14: EMERGENCY classification (DSS >= 0.85)
cl_14 = engine.classify_decision_level(0.90)
cond14 = cl_14 == 'EMERGENCY'
run_test(14, 'EMERGENCY Decision Level Classification', cond14, f"DSS 0.90 classified as '{cl_14}'")

# Test 15: High uncertainty handling
eng15 = DecisionSupportEngine()
res15 = eng15.assess(uncertainty_level='HIGH')
verif_reqs = res15.get('verification_requirements', [])
cond15 = len(verif_reqs) > 0
run_test(15, 'High Uncertainty Verification Requirement Trigger', cond15, f"{len(verif_reqs)} verification requirement(s) triggered: {verif_reqs}")

# Test 16: Degraded sensor handling
eng16 = DecisionSupportEngine()
res16 = eng16.assess(
    aggregate_shs=0.55,
    num_degraded=3,
    source_health_states=['HEALTHY', 'HEALTHY', 'DEGRADED', 'STALE', 'HEALTHY', 'DEGRADED', 'ANOMALOUS', 'HEALTHY'],
    num_anomalous=1
)
gate_state_16 = res16.get('data_quality_gate', {}).get('gate_state')
cond16 = gate_state_16 == 'DEGRADED'
run_test(16, 'Degraded Sensor Network Data Quality Gate', cond16, f"Data quality gate evaluated to '{gate_state_16}'")

# Test 17: Blocked data quality gate
eng17 = DecisionSupportEngine()
res17 = eng17.assess(
    aggregate_shs=0.30,
    num_missing=4,
    source_health_states=['MISSING', 'MISSING', 'MISSING', 'MISSING', 'HEALTHY', 'HEALTHY', 'HEALTHY', 'HEALTHY']
)
gate_state_17 = res17.get('data_quality_gate', {}).get('gate_state')
cond17 = gate_state_17 == 'BLOCKED'
run_test(17, 'Critically Impaired Telemetry BLOCKED Gate', cond17, f"Data quality gate evaluated to '{gate_state_17}'")

# Test 18: Asset prioritization
eng18 = DecisionSupportEngine()
test_assets = [
    {"code": "ASSET_LOW", "name": "Low Priority Asset", "asset_risk_index": 0.20, "criticality_weight": 0.50, "exposure_score": 0.20, "risk_level": "LOW"},
    {"code": "ASSET_HIGH", "name": "High Priority Critical Asset", "asset_risk_index": 0.90, "criticality_weight": 1.00, "exposure_score": 0.90, "risk_level": "CRITICAL"},
    {"code": "ASSET_MED", "name": "Medium Priority Asset", "asset_risk_index": 0.55, "criticality_weight": 0.75, "exposure_score": 0.50, "risk_level": "MODERATE"}
]
res18 = eng18.assess(asset_details=test_assets)
affected = res18.get('affected_assets', [])
p_scores = [a.get('priority_score', 0) for a in affected]
cond18 = len(affected) == 3 and p_scores == sorted(p_scores, reverse=True) and affected[0]['asset_code'] == 'ASSET_HIGH'
run_test(18, 'Asset Prioritization by Priority Score Descending', cond18, f"Sorted order: {[a['asset_code'] + '=' + str(a['priority_score']) for a in affected]}")

# Test 19: Escalation hysteresis (ALERT remains ALERT at DSS 0.65 >= 0.60)
eng19 = DecisionSupportEngine()
eng19.current_decision_level = 'ALERT'
cl_19 = eng19.classify_decision_level(0.65, 'ALERT')
cond19 = cl_19 == 'ALERT'
run_test(19, 'Hysteresis Retention of ALERT Status at DSS 0.65', cond19, f"Decision level maintained at '{cl_19}' (>= 0.70 - 0.10 = 0.60)")

# Test 20: De-escalation hysteresis (ALERT drops to PREPARE at DSS 0.55 < 0.60)
eng20 = DecisionSupportEngine()
eng20.current_decision_level = 'ALERT'
cl_20 = eng20.classify_decision_level(0.55, 'ALERT')
cond20 = cl_20 != 'ALERT'
run_test(20, 'Hysteresis De-escalation from ALERT at DSS 0.55', cond20, f"Decision level de-escalated to '{cl_20}' (< 0.60 threshold)")

# Benchmark Scenarios Execution
eng_scenarios = DecisionSupportEngine()
bench_results = eng_scenarios.run_benchmark_scenarios()

# Test 21: Scenario A: SCENARIO_A_NOMINAL -> NORMAL
scen_a = next((s for s in bench_results if s.get('scenario_id') == 'SCENARIO_A_NOMINAL'), None)
cond21 = scen_a is not None and scen_a.get('decision_level') == 'NORMAL'
run_test(21, 'Benchmark Scenario A: Nominal Baseline Conditions', cond21, f"Decision level: {scen_a.get('decision_level') if scen_a else 'Missing'}")

# Test 22: Scenario B: SCENARIO_B_HEAVY_RAIN -> MONITOR, PREPARE, or ALERT
scen_b = next((s for s in bench_results if s.get('scenario_id') == 'SCENARIO_B_HEAVY_RAIN'), None)
cond22 = scen_b is not None and scen_b.get('decision_level') in ['MONITOR', 'PREPARE', 'ALERT']
run_test(22, 'Benchmark Scenario B: Heavy Rainfall + Healthy Telemetry', cond22, f"Decision level: {scen_b.get('decision_level') if scen_b else 'Missing'}")

# Test 23: Scenario C: SCENARIO_C_CRITICAL_COMPOUND -> ALERT or EMERGENCY
scen_c = next((s for s in bench_results if s.get('scenario_id') == 'SCENARIO_C_CRITICAL_COMPOUND'), None)
cond23 = scen_c is not None and scen_c.get('decision_level') in ['ALERT', 'EMERGENCY']
run_test(23, 'Benchmark Scenario C: Critical Multi-Hazard Compound Event', cond23, f"Decision level: {scen_c.get('decision_level') if scen_c else 'Missing'}")

# Test 24: Scenario D: SCENARIO_D_HIGH_UNCERTAINTY -> verification_requirements not empty
scen_d = next((s for s in bench_results if s.get('scenario_id') == 'SCENARIO_D_HIGH_UNCERTAINTY'), None)
cond24 = scen_d is not None and len(scen_d.get('verification_requirements', [])) > 0
run_test(24, 'Benchmark Scenario D: High Uncertainty Verification Requirements', cond24, f"Requirements: {scen_d.get('verification_requirements') if scen_d else 'Missing'}")

# Test 25: API GET /api/decision-support/current
resp25 = client.get('/api/decision-support/current')
data25 = resp25.json() if resp25.status_code == 200 else {}
cond25 = resp25.status_code == 200 and 'decision_level' in data25 and 'decision_score' in data25
run_test(25, 'API GET /api/decision-support/current Endpoint', cond25, f"Status: {resp25.status_code}, Level: {data25.get('decision_level')}, Score: {data25.get('decision_score')}")

# Test 26: API GET /api/decision-support/policy
resp26 = client.get('/api/decision-support/policy')
data26 = resp26.json() if resp26.status_code == 200 else {}
cond26 = resp26.status_code == 200 and 'dss_weights' in data26 and 'decision_thresholds' in data26
run_test(26, 'API GET /api/decision-support/policy Endpoint', cond26, f"Status: {resp26.status_code}, Weights and thresholds present")

# Test 27: API GET /api/decision-support/scenarios
resp27 = client.get('/api/decision-support/scenarios')
data27 = resp27.json() if resp27.status_code == 200 else {}
scenarios_list = data27.get('scenarios', data27 if isinstance(data27, list) else [])
cond27 = resp27.status_code == 200 and len(scenarios_list) >= 8
run_test(27, 'API GET /api/decision-support/scenarios Endpoint', cond27, f"Status: {resp27.status_code}, {len(scenarios_list)} benchmark scenarios returned (>= 8)")

# Test 28: Explanation completeness
res28 = engine.assess()
required_keys = [
    'decision_level',
    'decision_score',
    'escalation_reasons',
    'verification_requirements',
    'recommended_action',
    'data_quality_gate',
    'affected_assets',
    'thresholds_disclaimer'
]
cond28 = all(k in res28 for k in required_keys)
run_test(28, 'Assessment Output Explanation Completeness', cond28, f"All {len(required_keys)} required operational explanation keys present")

# Test 29: Monotonicity with respect to hazard probability
eng29_low = DecisionSupportEngine()
res29_low = eng29_low.assess(flood_probability=0.20)
eng29_high = DecisionSupportEngine()
res29_high = eng29_high.assess(flood_probability=0.80)
cond29 = res29_high['decision_score'] >= res29_low['decision_score']
run_test(29, 'Score Monotonicity with Increasing Hazard Probability', cond29, f"DSS(p=0.80)={res29_high['decision_score']:.4f} >= DSS(p=0.20)={res29_low['decision_score']:.4f}")

# Test 30: Edge-case robustness
eng30 = DecisionSupportEngine()
res30 = eng30.assess(
    flood_probability=0.0,
    compound_risk_score=0.0,
    max_asset_risk_index=0.0,
    aggregate_shs=1.0
)
cond30 = res30.get('decision_level') == 'NORMAL' and res30.get('decision_score') is not None and 0.0 <= res30['decision_score'] <= 1.0
run_test(30, 'Edge-Case Zero-Hazard Robustness & Stability', cond30, f"Level: {res30.get('decision_level')}, Score: {res30.get('decision_score', 'N/A')}")

print()
print('=' * 65)
if failed == 0:
    print(f'  ALL PHASE 17 DECISION SUPPORT TESTS PASSED ({passed}/{total}) (STATUS: PASS)')
else:
    print(f'  PHASE 17 TESTS: {passed}/{total} PASSED, {failed} FAILED (STATUS: FAIL)')
print('=' * 65)
