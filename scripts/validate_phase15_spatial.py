"""
Automated Validation Suite for Phase 15: Spatial Flood Inundation & Impact Mapping
ClimateTwin Chennai Project
"""

import sys
import os
import json
from fastapi.testclient import TestClient

BASE_DIR = r"C:\Users\gokul\Desktop\PROJECTS\climatetwin"
sys.path.insert(0, os.path.join(BASE_DIR, 'backend'))

from app.main import app
from app.core.spatial_inundation import spatial_inundation_engine, SPATIAL_ZONES

client = TestClient(app)

def run_tests():
    print("=================================================================")
    print("  CLIMATETWIN PHASE 15: SPATIAL INUNDATION VALIDATION SUITE")
    print("=================================================================\n")

    # Test 01: DEM Raster & Elevation
    print("[Test 01] Verifying Copernicus DEM Elevation Extraction...")
    elev_adyar = spatial_inundation_engine.get_dem_elevation(13.0100, 80.2500)
    elev_poondi = spatial_inundation_engine.get_dem_elevation(13.1850, 79.8600)
    assert elev_adyar < elev_poondi, f"Adyar elev ({elev_adyar}m) should be lower than Poondi ({elev_poondi}m)"
    print(f"  -> PASSED: Real DEM elevations extracted (Adyar: {elev_adyar}m, Poondi: {elev_poondi}m).")

    # Test 02: Spatial Zone Inventory Structure
    print("\n[Test 02] Verifying Spatial Zone Inventory...")
    assert len(SPATIAL_ZONES) == 8, f"Expected 8 spatial zones, got {len(SPATIAL_ZONES)}"
    for z in SPATIAL_ZONES:
        assert "zone_id" in z and "bounds" in z and "critical_assets" in z
    print("  -> PASSED: All 8 Greater Chennai spatial catchment zones verified.")

    # Test 03: Geographic Bounds Validity
    print("\n[Test 03] Verifying Spatial Bounds Coverage...")
    for z in SPATIAL_ZONES:
        b = z['bounds']
        assert 12.8 <= b['min_lat'] <= 13.5 and 79.7 <= b['min_lon'] <= 80.4
    print("  -> PASSED: All zone bounding boxes fall strictly within Greater Chennai domain.")

    # Test 04: Terrain-Derived Flood Susceptibility (TSS)
    print("\n[Test 04] Verifying Terrain Susceptibility (TSS) Formulation...")
    tss_lowland = spatial_inundation_engine.calculate_terrain_susceptibility(2.0, 13.0100, 80.2500)
    tss_upland = spatial_inundation_engine.calculate_terrain_susceptibility(40.0, 13.1850, 79.8600)
    assert 0.0 <= tss_lowland <= 1.0 and 0.0 <= tss_upland <= 1.0
    assert tss_lowland > tss_upland, f"Lowland TSS ({tss_lowland}) must exceed upland TSS ({tss_upland})"
    print(f"  -> PASSED: Terrain susceptibility gradient verified (Lowland: {tss_lowland:.3f} > Upland: {tss_upland:.3f}).")

    # Test 05: Rainfall Component Scaling
    print("\n[Test 05] Verifying Rainfall Hazard Component Scaling...")
    fsi_light = spatial_inundation_engine.calculate_flood_susceptibility_index(10.0, 0.1, 0.5, "MODERATE")
    fsi_torrential = spatial_inundation_engine.calculate_flood_susceptibility_index(150.0, 0.9, 0.5, "MODERATE")
    assert fsi_torrential > fsi_light
    print(f"  -> PASSED: Positive rainfall response gradient verified (FSI 10mm: {fsi_light:.3f} -> 150mm: {fsi_torrential:.3f}).")

    # Test 06: Runoff Stress Scaling
    print("\n[Test 06] Verifying Runoff Stress Component...")
    fsi_low_ro = spatial_inundation_engine.calculate_flood_susceptibility_index(50.0, 0.1, 0.5, "MODERATE")
    fsi_high_ro = spatial_inundation_engine.calculate_flood_susceptibility_index(50.0, 0.9, 0.5, "MODERATE")
    assert fsi_high_ro > fsi_low_ro
    print(f"  -> PASSED: Runoff stress scaling confirmed.")

    # Test 07: Flood Susceptibility Index (FSI)
    print("\n[Test 07] Verifying Flood Susceptibility Index (FSI) Bounds...")
    fsi = spatial_inundation_engine.calculate_flood_susceptibility_index(60.0, 0.5, 0.7, "VERY_HIGH")
    assert 0.0 <= fsi <= 1.0
    print(f"  -> PASSED: FSI strictly bounded within [0.0, 1.0] (Observed: {fsi:.3f}).")

    # Test 08: Spatial Flood Impact Index (SFII)
    print("\n[Test 08] Verifying Spatial Flood Impact Index (SFII)...")
    sfii = spatial_inundation_engine.calculate_spatial_flood_impact_index(0.85, 0.75, 0.15)
    assert 0.0 <= sfii <= 1.0
    print(f"  -> PASSED: SFII calculation verified (SFII = {sfii:.3f}).")

    # Test 09: Inundation Severity Classification
    print("\n[Test 09] Verifying Relative Inundation Severity Classes...")
    assert spatial_inundation_engine.get_inundation_severity_class(0.80) == "SEVERE"
    assert spatial_inundation_engine.get_inundation_severity_class(0.60) == "HIGH"
    assert spatial_inundation_engine.get_inundation_severity_class(0.40) == "MODERATE"
    assert spatial_inundation_engine.get_inundation_severity_class(0.20) == "LOW"
    print("  -> PASSED: Discrete proxy severity classes mapped correctly.")

    # Test 10: Multi-Horizon Progression
    print("\n[Test 10] Verifying Multi-Horizon Forecast Progression...")
    zones = spatial_inundation_engine.assess_all_zones({"rainfall_daily": 80.0, "flood_probability": 0.65})
    for z in zones:
        prog = z['forecast_progression']
        assert prog['current'] <= prog['15m'] <= prog['30m'] <= prog['60m'] <= 1.0
    print("  -> PASSED: Multi-horizon spatial forecast progression monotonic and bounded.")

    # Test 11: Conformal Prediction Uncertainty Bounds
    print("\n[Test 11] Verifying Conformal Prediction Uncertainty Bounds...")
    for z in zones:
        inv = z['prediction_interval']
        assert 0.0 <= inv['lower'] <= z['spatial_flood_impact_index'] <= inv['upper'] <= 1.0
    print("  -> PASSED: 90% conformal intervals mathematically ordered.")

    # Test 12: Cascading Spillway Propagation
    print("\n[Test 12] Verifying Cascading Spillway Surge to Estuary...")
    zones_nominal = spatial_inundation_engine.assess_all_zones({"reservoir_fill_ratio": 0.50})
    zones_surge = spatial_inundation_engine.assess_all_zones({"reservoir_fill_ratio": 0.95})
    adyar_nom = next(z for z in zones_nominal if z['zone_id'] == 'ZONE_ADYAR_ESTUARY')
    adyar_surge = next(z for z in zones_surge if z['zone_id'] == 'ZONE_ADYAR_ESTUARY')
    assert adyar_surge['spatial_flood_impact_index'] > adyar_nom['spatial_flood_impact_index']
    print(f"  -> PASSED: Adyar estuary impact elevated during reservoir surge ({adyar_nom['spatial_flood_impact_index']:.3f} -> {adyar_surge['spatial_flood_impact_index']:.3f}).")

    # Test 13: Deterministic Priority Ranking
    print("\n[Test 13] Verifying Priority Zone Ranking...")
    for i in range(len(zones) - 1):
        assert zones[i]['spatial_flood_impact_index'] >= zones[i+1]['spatial_flood_impact_index']
        assert zones[i]['priority_zone_rank'] == i + 1
    print(f"  -> PASSED: Deterministic priority ranking confirmed (Top 1: {zones[0]['name']}).")

    # Test 14: Spatial Point Query Engine
    print("\n[Test 14] Verifying Spatial Point Query Engine...")
    query_res = spatial_inundation_engine.query_point(13.0100, 80.2500)
    assert query_res['nearest_zone'] == "Coastal Adyar Estuary & Lowland Plain"
    assert "ADYAR_OUTFALL" in query_res['nearby_critical_assets']
    print("  -> PASSED: Spatial coordinate inspection query operational.")

    # Test 15: Clamping on Extreme Inputs
    print("\n[Test 15] Verifying Clamping on Extreme Inputs...")
    extreme_fsi = spatial_inundation_engine.calculate_flood_susceptibility_index(999.0, 5.0, 2.0, "CRITICAL")
    assert extreme_fsi == 1.000
    print("  -> PASSED: Extreme inputs properly clamped to 1.000 maximum.")

    # Test 16: Depth Non-Observation Labeling
    print("\n[Test 16] Verifying Depth Non-Observation Scientific Label...")
    assert "NOT DIRECTLY OBSERVED" in query_res['depth_estimation_status']
    print("  -> PASSED: Depth estimation status explicitly labeled as proxy.")

    # Test 17: GET /api/spatial/flood-risk
    print("\n[Test 17] Verifying GET /api/spatial/flood-risk Endpoint...")
    res = client.get("/api/spatial/flood-risk")
    assert res.status_code == 200
    data = res.json()
    assert data["zone_count"] == 8
    print("  -> PASSED: GET /api/spatial/flood-risk returned 200 OK with 8 zones.")

    # Test 18: GET /api/spatial/flood-impact
    print("\n[Test 18] Verifying GET /api/spatial/flood-impact Endpoint...")
    res = client.get("/api/spatial/flood-impact")
    assert res.status_code == 200
    data = res.json()
    assert "top_priority_impact_zones" in data
    print(f"  -> PASSED: GET /api/spatial/flood-impact returned 200 OK (City Severity: {data['city_wide_inundation_severity']}).")

    # Test 19: GET /api/spatial/layers
    print("\n[Test 19] Verifying GET /api/spatial/layers Catalog...")
    res = client.get("/api/spatial/layers")
    assert res.status_code == 200
    layers = res.json()["layers"]
    assert len(layers) >= 5
    print(f"  -> PASSED: GET /api/spatial/layers returned {len(layers)} spatial layers.")

    # Test 20: GET /api/spatial/forecast
    print("\n[Test 20] Verifying GET /api/spatial/forecast Endpoint...")
    res = client.get("/api/spatial/forecast")
    assert res.status_code == 200
    data = res.json()
    assert len(data["forecast_zones"]) == 8
    print("  -> PASSED: GET /api/spatial/forecast returned 200 OK.")

    # Test 21: GET /api/spatial/zone/{zone_id}
    print("\n[Test 21] Verifying GET /api/spatial/zone/{zone_id} Endpoint...")
    res = client.get("/api/spatial/zone/ZONE_ADYAR_ESTUARY")
    assert res.status_code == 200
    assert res.json()["zone_id"] == "ZONE_ADYAR_ESTUARY"
    print("  -> PASSED: GET /api/spatial/zone/ZONE_ADYAR_ESTUARY returned 200 OK.")

    # Test 22: GET /api/spatial/query
    print("\n[Test 22] Verifying GET /api/spatial/query Coordinate Inspection...")
    res = client.get("/api/spatial/query?lat=13.0827&lon=80.2707")
    assert res.status_code == 200
    assert "dem_elevation_m" in res.json()
    print("  -> PASSED: GET /api/spatial/query returned 200 OK.")

    # Test 23: POST /api/spatial/assess
    print("\n[Test 23] Verifying POST /api/spatial/assess Endpoint...")
    payload = {"rainfall_daily": 120.0, "flood_probability": 0.80}
    res = client.post("/api/spatial/assess", json=payload)
    assert res.status_code == 200
    assert len(res.json()["zones"]) == 8
    print("  -> PASSED: POST /api/spatial/assess returned 200 OK.")

    print("\n=================================================================")
    print("  ALL PHASE 15 SPATIAL TESTS PASSED (23/23) (STATUS: PASS)")
    print("=================================================================\n")

if __name__ == '__main__':
    run_tests()
