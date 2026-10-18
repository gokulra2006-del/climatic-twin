"""
Chennai Multi-Hazard Synthetic & Historical Ground-Truth Dataset Generator
Custom-calibrated for Greater Chennai Digital Twin (ClimateTwin)
"""

import os
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

def generate_chennai_digital_twin_dataset(output_dir="data"):
    os.makedirs(output_dir, exist_ok=True)
    np.random.seed(42)
    
    print("=" * 60)
    print("CLIMATETWIN: GENERATING CHENNAI MULTI-HAZARD DATASET")
    print("=" * 60)
    
    # Date range: 3 Years (2022-01-01 to 2024-12-31 hourly = 26,304 records)
    start_time = datetime(2022, 1, 1, 0, 0, 0)
    end_time = datetime(2024, 12, 31, 23, 0, 0)
    dates = pd.date_range(start=start_time, end=end_time, freq="h")
    n = len(dates)
    
    print(f"Generating {n} hourly time points from {start_time.date()} to {end_time.date()}...")
    
    # 1. Physical Climate Signals for Chennai (13.0827 N, 80.2707 E)
    day_of_year = dates.dayofyear.values
    hour_of_day = dates.hour.values
    
    # Annual temperature wave (peak in May, minimum in Jan)
    temp_annual_wave = 28.5 + 5.5 * np.sin(2 * np.pi * (day_of_year - 70) / 365.25)
    # Diurnal temperature cycle (peaks around 14:00)
    temp_diurnal = 3.5 * np.sin(2 * np.pi * (hour_of_day - 9) / 24)
    # Base temperature
    temp_2m = temp_annual_wave + temp_diurnal + np.random.normal(0, 1.2, n)
    temp_2m = np.clip(temp_2m, 19.0, 44.5)
    
    # Relative humidity (inversely correlated with temperature, higher in winter/monsoon)
    base_rh = 75.0 - 0.8 * (temp_2m - 28.0) + np.random.normal(0, 5.0, n)
    rh = np.clip(base_rh, 35.0, 98.0)
    
    # Apparent Temperature (Rothfusz Heat Index regression formula)
    # HI = -42.379 + 2.04901523*T + 10.14333127*R - 0.22475541*T*R ...
    t_f = temp_2m * 9/5 + 32
    hi_f = (-42.379 + 2.04901523 * t_f + 10.14333127 * rh 
            - 0.22475541 * t_f * rh - 0.00683783 * (t_f**2) 
            - 0.05481717 * (rh**2) + 0.00122874 * (t_f**2) * rh 
            + 0.00085282 * t_f * (rh**2) - 0.00000199 * (t_f**2) * (rh**2))
    apparent_temp = (hi_f - 32) * 5/9
    apparent_temp = np.where(temp_2m < 27.0, temp_2m, apparent_temp)
    apparent_temp = np.clip(apparent_temp, temp_2m - 2.0, 52.0)
    
    # Dew point approximation (Magnus formula)
    b, c = 17.625, 243.04
    gamma = np.log(rh / 100.0) + (b * temp_2m) / (c + temp_2m)
    dew_point = (c * gamma) / (b - gamma)
    
    # Wind speed in m/s (coastal gusts higher in monsoon/afternoons)
    wind_speed = 3.5 + 1.5 * np.sin(2 * np.pi * (hour_of_day - 12) / 24) + np.random.exponential(1.5, n)
    wind_speed = np.clip(wind_speed, 0.5, 28.0)
    
    # Convective Available Potential Energy (CAPE)
    base_cape = np.where(rh > 70, (temp_2m - 25.0) * 120.0, 200.0)
    cape = np.clip(base_cape + np.random.normal(0, 300, n), 0.0, 3800.0)
    
    # 2. Seasonality for Precipitation in Chennai:
    # Northeast Monsoon (Oct 15 to Dec 31 -> days ~288 to 365) gives ~65% of rain
    # Southwest Monsoon (Jun 1 to Sep 30 -> days ~152 to 273) gives ~25% of rain
    rain_prob = np.zeros(n)
    is_ne_monsoon = (day_of_year >= 288) | (day_of_year <= 5)
    is_sw_monsoon = (day_of_year >= 152) & (day_of_year < 288)
    is_summer = (day_of_year >= 60) & (day_of_year < 152)
    
    rain_prob[is_ne_monsoon] = 0.22
    rain_prob[is_sw_monsoon] = 0.08
    rain_prob[is_summer] = 0.02
    
    # Base rain generation
    rain_1h = np.zeros(n)
    rain_events = np.random.random(n) < rain_prob
    rain_1h[rain_events] = np.random.exponential(6.0, np.sum(rain_events))
    
    # 3. Inject Historical Disaster Analogues:
    # A. Dec 2023 Cyclone Michaung analogue (Dec 3-5, 2023)
    michaung_mask = (dates >= '2023-12-03 00:00:00') & (dates <= '2023-12-05 12:00:00')
    rain_1h[michaung_mask] += np.random.uniform(15.0, 48.0, np.sum(michaung_mask))
    wind_speed[michaung_mask] = np.random.uniform(18.0, 26.5, np.sum(michaung_mask))
    
    # B. Nov 2022 Heavy Deluge Event (Nov 11-13, 2022)
    nov22_mask = (dates >= '2022-11-11 00:00:00') & (dates <= '2022-11-13 18:00:00')
    rain_1h[nov22_mask] += np.random.uniform(10.0, 35.0, np.sum(nov22_mask))
    
    # C. Severe Heatwave of May 2024 (May 18-24, 2024)
    hw24_mask = (dates >= '2024-05-18 10:00:00') & (dates <= '2024-05-24 17:00:00')
    temp_2m[hw24_mask] = np.clip(temp_2m[hw24_mask] + 4.5, 38.0, 44.5)
    apparent_temp[hw24_mask] = np.clip(apparent_temp[hw24_mask] + 6.0, 43.0, 51.5)
    
    # Smooth rainfall & compute rolling sums
    rain_1h = np.round(rain_1h, 2)
    s_rain = pd.Series(rain_1h, index=dates)
    rain_24h = s_rain.rolling(24, min_periods=1).sum().values
    rain_3d = s_rain.rolling(72, min_periods=1).sum().values
    rain_7d = s_rain.rolling(168, min_periods=1).sum().values
    
    # 4. Soil Moisture Dynamics (Surface 0-7cm & Root Zone 28-100cm)
    soil_surf = np.zeros(n)
    soil_root = np.zeros(n)
    curr_surf = 0.20
    curr_root = 0.22
    for i in range(n):
        # Infiltration from rain
        curr_surf += (rain_1h[i] * 0.008)
        # Drainage from surface into root zone
        curr_root += (curr_surf * 0.002)
        # Evapotranspiration loss (proportional to temp)
        evap_rate = 0.0005 * (temp_2m[i] / 30.0)
        curr_surf -= evap_rate * 1.5
        curr_root -= evap_rate * 0.7
        
        curr_surf = np.clip(curr_surf, 0.06, 0.44)
        curr_root = np.clip(curr_root, 0.11, 0.38)
        soil_surf[i] = curr_surf
        soil_root[i] = curr_root
        
    # 5. Chennai 4-Major Reservoir Hydrodynamic Twin (Total Capacity: 11,257 mcft)
    # Poondi (3231), Cholavaram (1081), Red Hills (3300), Chembarambakkam (3645)
    capacities = {"POONDI": 3231, "CHOLAVARAM": 1081, "REDHILLS": 3300, "CHEMBARAMBAKKAM": 3645}
    total_cap = sum(capacities.values())
    
    poondi = np.zeros(n)
    cholavaram = np.zeros(n)
    redhills = np.zeros(n)
    chembarambakkam = np.zeros(n)
    
    # Starting levels
    p_curr = 2100.0
    ch_curr = 600.0
    rh_curr = 2300.0
    cb_curr = 2500.0
    
    hourly_consumption = 55.0 / 24.0 # 55 mcft per day municipal drawdown
    
    for i in range(n):
        # Catchment inflow based on rainfall
        inflow = (rain_1h[i] * 2.2) # mcft inflow per mm rain
        
        # Distribute inflow across reservoirs
        p_curr += inflow * 0.30 - (hourly_consumption * 0.30)
        ch_curr += inflow * 0.10 - (hourly_consumption * 0.10)
        rh_curr += inflow * 0.30 - (hourly_consumption * 0.30)
        cb_curr += inflow * 0.30 - (hourly_consumption * 0.30)
        
        # Clamp to bounds
        p_curr = np.clip(p_curr, 80.0, capacities["POONDI"])
        ch_curr = np.clip(ch_curr, 20.0, capacities["CHOLAVARAM"])
        rh_curr = np.clip(rh_curr, 150.0, capacities["REDHILLS"])
        cb_curr = np.clip(cb_curr, 200.0, capacities["CHEMBARAMBAKKAM"])
        
        poondi[i] = p_curr
        cholavaram[i] = ch_curr
        redhills[i] = rh_curr
        chembarambakkam[i] = cb_curr
        
    total_res = poondi + cholavaram + redhills + chembarambakkam
    res_fill_ratio = np.round(total_res / total_cap, 4)
    
    # 6. Fire Weather Index (FWI) proxy
    fwi = np.clip(((temp_2m + (wind_speed * 0.3)) / (rh + 0.1)) * 12.0, 0.0, 42.0)
    
    # 7. Ground-Truth Hazard Labels (Strict Physical Logic)
    # Flood: High 24h rain or full reservoir spilling
    flood_label = ((rain_24h > 150.0) | ((rain_7d > 280.0) & (res_fill_ratio > 0.85))).astype(int)
    
    # Heatwave: Apparent temp >= 40.5 for consecutive window
    s_app = pd.Series(apparent_temp, index=dates)
    hw_cond = (s_app >= 40.5).astype(int)
    heatwave_label = (hw_cond.rolling(3, min_periods=3).min() == 1).astype(int).values
    
    # Drought: Combined storage < 22% AND root-zone moisture < 0.16
    drought_label = ((res_fill_ratio < 0.25) & (soil_root < 0.16)).astype(int)
    
    # Extreme Rainfall: Sudden cloudburst / high CAPE
    extreme_rain_label = ((rain_1h > 35.0) & (cape > 1800.0)).astype(int)
    
    # Assemble DataFrame
    df = pd.DataFrame({
        "timestamp": dates.strftime("%Y-%m-%d %H:%M:%S"),
        "rainfall_1h_mm": rain_1h,
        "rainfall_24h_sum_mm": np.round(rain_24h, 2),
        "rainfall_3d_sum_mm": np.round(rain_3d, 2),
        "rainfall_7d_sum_mm": np.round(rain_7d, 2),
        "temperature_2m_c": np.round(temp_2m, 2),
        "apparent_temperature_c": np.round(apparent_temp, 2),
        "relative_humidity_pct": np.round(rh, 1),
        "dew_point_c": np.round(dew_point, 2),
        "wind_speed_ms": np.round(wind_speed, 2),
        "soil_moisture_surface": np.round(soil_surf, 3),
        "soil_moisture_root_zone": np.round(soil_root, 3),
        "cape_convective_energy_j_kg": np.round(cape, 1),
        "fwi_fire_weather_index": np.round(fwi, 2),
        "poondi_mcft": np.round(poondi, 1),
        "cholavaram_mcft": np.round(cholavaram, 1),
        "redhills_mcft": np.round(redhills, 1),
        "chembarambakkam_mcft": np.round(chembarambakkam, 1),
        "total_reservoir_mcft": np.round(total_res, 1),
        "reservoir_fill_ratio": res_fill_ratio,
        "flood_label": flood_label,
        "heatwave_label": heatwave_label,
        "drought_label": drought_label,
        "extreme_rainfall_label": extreme_rain_label
    })
    
    csv_path = os.path.join(output_dir, "chennai_multihazard_dataset.csv")
    df.to_csv(csv_path, index=False)
    print(f"[OK] Generated {len(df)} rows -> {csv_path}")
    
    # 8. Infrastructure Causal Graph (NetworkX JSON format)
    causal_graph = {
        "metadata": {
            "city": "Chennai",
            "model": "Bayesian Directed Acyclic Causal Graph",
            "total_assets": 11
        },
        "nodes": [
            {"id": "Taramani_400kV_Substation", "category": "POWER", "importance": 0.95},
            {"id": "Koyambedu_Substation", "category": "POWER", "importance": 0.90},
            {"id": "Basin_Bridge_Thermal", "category": "POWER", "importance": 0.88},
            {"id": "Adyar_Pump_Station_1", "category": "DRAINAGE", "importance": 0.92},
            {"id": "Buckingham_Outfall_Pumps", "category": "DRAINAGE", "importance": 0.89},
            {"id": "Chembarambakkam_Sluice_Gates", "category": "RESERVOIR_OUTLET", "importance": 0.98},
            {"id": "GST_Road_Airport_Subway", "category": "TRANSPORT", "importance": 0.85},
            {"id": "Kathipara_Junction", "category": "TRANSPORT", "importance": 0.87},
            {"id": "Central_Station_Underpass", "category": "TRANSPORT", "importance": 0.80},
            {"id": "Rajiv_Gandhi_Govt_General_Hospital", "category": "HEALTHCARE", "importance": 0.99},
            {"id": "Apollo_Greams_Road", "category": "HEALTHCARE", "importance": 0.94}
        ],
        "edges": [
            {"source": "Taramani_400kV_Substation", "target": "Adyar_Pump_Station_1", "beta": 0.912, "latency_min": 15},
            {"source": "Koyambedu_Substation", "target": "Buckingham_Outfall_Pumps", "beta": 0.845, "latency_min": 20},
            {"source": "Chembarambakkam_Sluice_Gates", "target": "GST_Road_Airport_Subway", "beta": 0.882, "latency_min": 45},
            {"source": "Adyar_Pump_Station_1", "target": "Kathipara_Junction", "beta": 0.692, "latency_min": 30},
            {"source": "GST_Road_Airport_Subway", "target": "Rajiv_Gandhi_Govt_General_Hospital", "beta": 0.451, "latency_min": 60},
            {"source": "Kathipara_Junction", "target": "Apollo_Greams_Road", "beta": 0.520, "latency_min": 40},
            {"source": "Basin_Bridge_Thermal", "target": "Central_Station_Underpass", "beta": 0.765, "latency_min": 25}
        ]
    }
    
    graph_path = os.path.join(output_dir, "chennai_infrastructure_causal_graph.json")
    with open(graph_path, "w", encoding="utf-8") as f:
        json.dump(causal_graph, f, indent=4)
    print(f"[OK] Generated Infrastructure Causal Graph -> {graph_path}")
    
    # 9. Greater Chennai Corporation 15 Administrative Zones Inundation Summary
    zones_data = [
        {"zone_id": 1, "zone_name": "Tiruvottiyur", "elevation_mean_m": 4.2, "impervious_ratio": 0.68, "drainage_density_km": 1.4, "flood_vulnerability": 0.78},
        {"zone_id": 2, "zone_name": "Manali", "elevation_mean_m": 3.8, "impervious_ratio": 0.62, "drainage_density_km": 1.1, "flood_vulnerability": 0.82},
        {"zone_id": 3, "zone_name": "Madhavaram", "elevation_mean_m": 6.5, "impervious_ratio": 0.55, "drainage_density_km": 1.3, "flood_vulnerability": 0.61},
        {"zone_id": 4, "zone_name": "Tondiarpet", "elevation_mean_m": 4.5, "impervious_ratio": 0.84, "drainage_density_km": 1.6, "flood_vulnerability": 0.75},
        {"zone_id": 5, "zone_name": "Royapuram", "elevation_mean_m": 5.1, "impervious_ratio": 0.88, "drainage_density_km": 1.8, "flood_vulnerability": 0.71},
        {"zone_id": 6, "zone_name": "Thiru-Vi-Ka Nagar", "elevation_mean_m": 7.0, "impervious_ratio": 0.82, "drainage_density_km": 1.7, "flood_vulnerability": 0.65},
        {"zone_id": 7, "zone_name": "Ambattur", "elevation_mean_m": 12.4, "impervious_ratio": 0.74, "drainage_density_km": 1.5, "flood_vulnerability": 0.52},
        {"zone_id": 8, "zone_name": "Anna Nagar", "elevation_mean_m": 9.8, "impervious_ratio": 0.85, "drainage_density_km": 2.1, "flood_vulnerability": 0.58},
        {"zone_id": 9, "zone_name": "Teynampet", "elevation_mean_m": 6.2, "impervious_ratio": 0.89, "drainage_density_km": 2.0, "flood_vulnerability": 0.68},
        {"zone_id": 10, "zone_name": "Kodambakkam", "elevation_mean_m": 5.8, "impervious_ratio": 0.87, "drainage_density_km": 1.9, "flood_vulnerability": 0.73},
        {"zone_id": 11, "zone_name": "Valasaravakkam", "elevation_mean_m": 8.1, "impervious_ratio": 0.76, "drainage_density_km": 1.6, "flood_vulnerability": 0.64},
        {"zone_id": 12, "zone_name": "Alandur", "elevation_mean_m": 10.5, "impervious_ratio": 0.78, "drainage_density_km": 1.8, "flood_vulnerability": 0.59},
        {"zone_id": 13, "zone_name": "Adyar", "elevation_mean_m": 3.9, "impervious_ratio": 0.81, "drainage_density_km": 2.2, "flood_vulnerability": 0.86},
        {"zone_id": 14, "zone_name": "Perungudi", "elevation_mean_m": 2.8, "impervious_ratio": 0.69, "drainage_density_km": 1.2, "flood_vulnerability": 0.94},
        {"zone_id": 15, "zone_name": "Sholinganallur", "elevation_mean_m": 3.2, "impervious_ratio": 0.64, "drainage_density_km": 1.3, "flood_vulnerability": 0.89}
    ]
    df_zones = pd.DataFrame(zones_data)
    zones_path = os.path.join(output_dir, "chennai_zone_inundation_summary.csv")
    df_zones.to_csv(zones_path, index=False)
    print(f"[OK] Generated 15 Administrative Zones -> {zones_path}")
    
    print("\n--- VALIDATION & SUMMARY STATISTICS ---")
    print(f"Total Rows: {len(df)}")
    print(f"Flood Events Count: {df['flood_label'].sum()} ({df['flood_label'].mean()*100:.2f}%)")
    print(f"Heatwave Events Count: {df['heatwave_label'].sum()} ({df['heatwave_label'].mean()*100:.2f}%)")
    print(f"Drought Events Count: {df['drought_label'].sum()} ({df['drought_label'].mean()*100:.2f}%)")
    print(f"Max 24h Rain: {df['rainfall_24h_sum_mm'].max()} mm")
    print(f"Reservoir Range: {df['total_reservoir_mcft'].min()} - {df['total_reservoir_mcft'].max()} mcft")
    print("=" * 60)

if __name__ == "__main__":
    generate_chennai_digital_twin_dataset()
