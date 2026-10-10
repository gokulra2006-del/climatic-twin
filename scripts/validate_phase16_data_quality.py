"""
Automated Validation Suite for Phase 16: Real-Time Sensor Health & Data Quality Intelligence
ClimateTwin Chennai Project
"""

import sys
import os
import json
from fastapi.testclient import TestClient

BASE_DIR = r"C:\Users\gokul\Desktop\PROJECTS\climatetwin"
sys.path.insert(0, os.path.join(BASE_DIR, 'backend'))

from app.main import app
from app.core.sensor_health import sensor_health_engine, SOURCE_CATALOG, PHYSICAL_BOUNDS

client = TestClient(app)

def run_tests():
    print("=================================================================")
    print("  CLIMATETWIN PHASE 16: DATA QUALITY VALIDATION SUITE")
    print("=================================================================\n")

    # Test 01: Telemetry Source Inventory
    print("[Test 01] Verifying Telemetry Source Inventory...")
    assert len(SOURCE_CATALOG) == 8, f"Expected 8 telemetry sources, got {len(SOURCE_CATALOG)}"
    for s in SOURCE_CATALOG:
        assert "source_id" in s and "variables" in s and "source_type" in s
    print("  -> PASSED: All 8 Greater Chennai telemetry sources verified.")

    # Test 02: Physical Plausibility - Valid Rainfall
    print("\n[Test 02] Verifying Plausibility - Valid Rainfall (45.0 mm)...")
    is_valid, msg = sensor_health_engine.check_physical_plausibility("rainfall", 45.0)
    assert is_valid, msg
    print("  -> PASSED: Valid rainfall confirmed physically plausible.")

    # Test 03: Physical Plausibility - Negative Rainfall Rejection
    print("\n[Test 03] Verifying Plausibility - Negative Rainfall Rejection (-15.0 mm)...")
    is_valid, msg = sensor_health_engine.check_physical_plausibility("rainfall", -15.0)
    assert not is_valid
    print(f"  -> PASSED: Negative rainfall rejected: {msg}")

    # Test 04: Physical Plausibility - Valid Temperature (32.0°C)
    print("\n[Test 04] Verifying Plausibility - Valid Temperature...")
    is_valid, msg = sensor_health_engine.check_physical_plausibility("temperature", 32.0)
    assert is_valid
    print("  -> PASSED: Valid temperature confirmed physically plausible.")

    # Test 05: Physical Plausibility - Impossible Extreme Temperature (85.0°C)
    print("\n[Test 05] Verifying Plausibility - Extreme Temperature Rejection (85.0°C)...")
    is_valid, msg = sensor_health_engine.check_physical_plausibility("temperature", 85.0)
    assert not is_valid
    print(f"  -> PASSED: Unphysical temperature rejected: {msg}")

    # Test 06: Physical Plausibility - Reservoir Capacity Bounds
    print("\n[Test 06] Verifying Plausibility - Redhills Reservoir Capacity Limits...")
    is_valid_nom, _ = sensor_health_engine.check_physical_plausibility("water_level_REDHILLS", 2900.0)
    is_valid_ovf, msg = sensor_health_engine.check_physical_plausibility("water_level_REDHILLS", 9500.0)
    assert is_valid_nom and not is_valid_ovf
    print(f"  -> PASSED: Reservoir overflow bounds enforced (>3300 mcft): {msg}")

    # Test 07: Temporal Innovation & Rate of Change Check
    print("\n[Test 07] Verifying Temporal Innovation & Rate-of-Change...")
    is_anom_nom, z_nom, _ = sensor_health_engine.check_temporal_anomaly("NASA_IMERG_CHENNAI", "rainfall", 48.0)
    is_anom_spike, z_spike, msg = sensor_health_engine.check_temporal_anomaly("NASA_IMERG_CHENNAI", "rainfall", 350.0)
    assert not is_anom_nom and is_anom_spike
    print(f"  -> PASSED: 350mm sudden spike flagged as temporal anomaly (z={z_spike}): {msg}")

    # Test 08: Stuck Sensor Detection
    print("\n[Test 08] Verifying Stuck Sensor Detection...")
    sensor_health_engine.history_buffer["TEST_STUCK_val"] = [30.0] * 7
    is_stuck, msg = sensor_health_engine.check_stuck_sensor("TEST", "STUCK_val", 30.0)
    assert is_stuck
    print(f"  -> PASSED: Stuck static sensor detected: {msg}")

    # Test 09: Cross-Source Environmental Consistency
    print("\n[Test 09] Verifying Cross-Source Environmental Consistency...")
    cc = sensor_health_engine.check_cross_source_consistency()
    assert "temperature_check" in cc and "rainfall_check" in cc
    assert cc["temperature_check"]["agreement_status"] in ["EXCELLENT", "GOOD"]
    print(f"  -> PASSED: Cross-source consistency confirmed (Temp Diff={cc['temperature_check']['difference']}C, Score={cc['temperature_check']['consistency_score']}).")

    # Test 10: Sensor Health Score (SHS) Mathematical Bounds
    print("\n[Test 10] Verifying Sensor Health Score (SHS) Bounds...")
    summary = sensor_health_engine.get_summary()
    for s in summary["sources"]:
        assert 0.0 <= s["sensor_health_score"] <= 1.0
        assert s["quality_tier"] in ["EXCELLENT", "GOOD", "DEGRADED", "POOR", "UNUSABLE"]
    print("  -> PASSED: SHS strictly bounded in [0.0, 1.0] across all sources.")

    # Test 11: City-Wide Aggregate Telemetry Health Summary
    print("\n[Test 11] Verifying City-Wide Telemetry Health Summary...")
    assert summary["city_wide_telemetry_health"] in ["EXCELLENT", "GOOD"]
    assert summary["source_counts"]["total_sources"] == 8
    print(f"  -> PASSED: Summary verified: {summary['city_wide_telemetry_health']} (Mean SHS: {summary['aggregate_health_score']:.3f}).")

    # Test 12: Synthetic Scenario 1 - Missing Sensor
    print("\n[Test 12] Testing Synthetic Scenario 1 (Missing Sensor)...")
    res1 = sensor_health_engine.simulate_failure_scenario("SCENARIO_1_MISSING_SENSOR")
    target1 = next(s for s in res1["resulting_summary"]["sources"] if s["source_id"] == "CMWSSB_CHOLAVARAM")
    assert target1["health_state"] == "MISSING" and target1["sensor_health_score"] == 0.0
    print("  -> PASSED: Missing sensor scenario produced HEALTH_STATE=MISSING (SHS=0.0).")

    # Test 13: Synthetic Scenario 2 - Stale Sensor
    print("\n[Test 13] Testing Synthetic Scenario 2 (Stale Sensor)...")
    res2 = sensor_health_engine.simulate_failure_scenario("SCENARIO_2_STALE_SENSOR")
    target2 = next(s for s in res2["resulting_summary"]["sources"] if s["source_id"] == "NASA_IMERG_CHENNAI")
    assert target2["health_state"] == "STALE"
    print("  -> PASSED: Stale sensor scenario produced HEALTH_STATE=STALE.")

    # Test 14: Synthetic Scenario 3 - Stuck Sensor
    print("\n[Test 14] Testing Synthetic Scenario 3 (Stuck Sensor)...")
    res3 = sensor_health_engine.simulate_failure_scenario("SCENARIO_3_STUCK_SENSOR")
    target3 = next(s for s in res3["resulting_summary"]["sources"] if s["source_id"] == "NOAA_ISD_432790")
    assert target3["health_state"] == "DEGRADED" and target3["stuck_sensor"]["is_stuck"]
    print("  -> PASSED: Stuck sensor scenario detected static reading.")

    # Test 15: Synthetic Scenario 4 - Sudden Spike Anomaly
    print("\n[Test 15] Testing Synthetic Scenario 4 (Sudden Spike)...")
    res4 = sensor_health_engine.simulate_failure_scenario("SCENARIO_4_SUDDEN_SPIKE")
    target4 = next(s for s in res4["resulting_summary"]["sources"] if s["source_id"] == "CMWSSB_REDHILLS")
    assert target4["health_state"] == "ANOMALOUS"
    print("  -> PASSED: Sudden spike scenario flagged ANOMALOUS.")

    # Test 16: Synthetic Scenario 5 - Impossible Out-of-Bounds Value
    print("\n[Test 16] Testing Synthetic Scenario 5 (Impossible Value)...")
    res5 = sensor_health_engine.simulate_failure_scenario("SCENARIO_5_IMPOSSIBLE_VALUE")
    target5 = next(s for s in res5["resulting_summary"]["sources"] if s["source_id"] == "NASA_IMERG_CHENNAI")
    assert not target5["physical_plausibility"]["is_valid"]
    print("  -> PASSED: Impossible value scenario failed physical plausibility check.")

    # Test 17: Synthetic Scenario 8 - Recovery to Nominal
    print("\n[Test 17] Testing Synthetic Scenario 8 (Full Recovery)...")
    res8 = sensor_health_engine.simulate_failure_scenario("SCENARIO_8_RECOVERY_NOMINAL")
    assert res8["resulting_summary"]["source_counts"]["healthy"] >= 7
    print("  -> PASSED: Full recovery restored nominal telemetry health.")

    # Test 18: Real-Time Anomaly Event Feed
    print("\n[Test 18] Verifying Anomaly Event Feed...")
    assert len(sensor_health_engine.anomaly_feed) >= 5
    print(f"  -> PASSED: Anomaly event feed recorded {len(sensor_health_engine.anomaly_feed)} audit events.")

    # Test 19: REST API - GET /api/data-quality/summary
    print("\n[Test 19] Verifying GET /api/data-quality/summary Endpoint...")
    res = client.get("/api/data-quality/summary")
    assert res.status_code == 200
    assert "aggregate_health_score" in res.json()
    print("  -> PASSED: GET /api/data-quality/summary returned 200 OK.")

    # Test 20: REST API - GET /api/data-quality/sources
    print("\n[Test 20] Verifying GET /api/data-quality/sources Endpoint...")
    res = client.get("/api/data-quality/sources")
    assert res.status_code == 200
    assert res.json()["count"] == 8
    print("  -> PASSED: GET /api/data-quality/sources returned 8 sources.")

    # Test 21: REST API - GET /api/data-quality/sources/{source_id}
    print("\n[Test 21] Verifying GET /api/data-quality/sources/{id} Endpoint...")
    res = client.get("/api/data-quality/sources/NOAA_ISD_432790")
    assert res.status_code == 200
    assert res.json()["source_id"] == "NOAA_ISD_432790"
    print("  -> PASSED: GET /api/data-quality/sources/NOAA_ISD_432790 returned 200 OK.")

    # Test 22: REST API - GET /api/data-quality/anomalies
    print("\n[Test 22] Verifying GET /api/data-quality/anomalies Endpoint...")
    res = client.get("/api/data-quality/anomalies")
    assert res.status_code == 200
    assert "events" in res.json()
    print("  -> PASSED: GET /api/data-quality/anomalies returned 200 OK.")

    # Test 23: REST API - POST /api/data-quality/check
    print("\n[Test 23] Verifying POST /api/data-quality/check Endpoint...")
    check_payload = {"source_id": "NASA_IMERG_CHENNAI", "variable": "rainfall", "value": 55.0}
    res = client.post("/api/data-quality/check", json=check_payload)
    assert res.status_code == 200
    assert res.json()["quality_result"]["physical_plausibility"]["is_valid"]
    print("  -> PASSED: POST /api/data-quality/check validated observation.")

    # Test 24: REST API - POST /api/data-quality/simulate-failure
    print("\n[Test 24] Verifying POST /api/data-quality/simulate-failure Endpoint...")
    sim_payload = {"scenario_id": "SCENARIO_8_RECOVERY_NOMINAL"}
    res = client.post("/api/data-quality/simulate-failure", json=sim_payload)
    assert res.status_code == 200
    assert res.json()["simulation_label"] == "CONTROLLED_SYNTHETIC_TEST"
    print("  -> PASSED: POST /api/data-quality/simulate-failure returned 200 OK.")

    # Test 25: Telemetry Pipeline Quality Hook
    print("\n[Test 25] Verifying Telemetry Pipeline Quality Hook...")
    import time
    telemetry_res = client.post("/api/predictions/telemetry", json={
        "source_timestamp": time.time(),
        "rainfall_daily": 45.0,
        "rainfall_3d_sum": 110.0,
        "rainfall_5d_sum": 160.0,
        "rainfall_7d_sum": 210.0,
        "temp_mean": 30.5,
        "temp_max": 34.2,
        "temp_min": 26.8,
        "dew_point_mean": 24.5,
        "wind_speed_mean": 4.8,
        "POONDI": 2820.0,
        "CHOLAVARAM": 820.0,
        "REDHILLS": 2910.0,
        "CHEMBARAMBAKKAM": 3120.0
    })
    assert telemetry_res.status_code == 200, f"Expected 200, got {telemetry_res.status_code}: {telemetry_res.text}"
    print("  -> PASSED: Core telemetry prediction pipeline verified with quality integration.")

    print("\n=================================================================")
    print("  ALL PHASE 16 DATA QUALITY TESTS PASSED (25/25) (STATUS: PASS)")
    print("=================================================================\n")

if __name__ == '__main__':
    run_tests()
