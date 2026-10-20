from app.core.satellite_ingestion import satellite_engine
import os
import pickle
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from typing import Dict, Any, Tuple
from fastapi import HTTPException
from pydantic import BaseModel
from app.api.api_v1.endpoints.lead_time_utils import calculate_lead_time

PROCESSED_DIR = r"C:\Users\gokul\Desktop\PROJECTS\climatetwin\data\processed"
MODELS_DIR = r"C:\Users\gokul\Desktop\PROJECTS\climatetwin\backend\app\models"

# Global Model Cache
_models = {
    "heatwave": None,
    "drought": None,
    "wildfire": None,
    "extreme_rain": None
}

# Global Data Cache to prevent reading 8MB CSVs on every request
_data_cache = {
    "noaa": None,
    "noaa_daily": None,
    "imerg": None
}

def load_model(name: str):
    if _models[name] is not None:
        return _models[name]
    path = os.path.join(MODELS_DIR, f"{name}_rf_model.pkl")
    if os.path.exists(path):
        with open(path, "rb") as f:
            _models[name] = pickle.load(f)
            return _models[name]
    return None

def get_noaa_data():
    if _data_cache["noaa"] is None:
        df = pd.read_csv(os.path.join(PROCESSED_DIR, "weather", "noaa_isd_chennai_hourly.csv"))
        df['DATE'] = pd.to_datetime(df['DATE'])
        _data_cache["noaa"] = df
        _data_cache["noaa_daily"] = df.resample('1D', on='DATE').agg({
            'temperature_c': ['max', 'mean'],
            'dew_point_c': 'mean',
            'wind_speed_ms': 'mean'
        }).dropna()
    return _data_cache["noaa"], _data_cache["noaa_daily"]

def get_imerg_data():
    if _data_cache["imerg"] is None:
        _data_cache["imerg"] = pd.read_csv(os.path.join(PROCESSED_DIR, "rainfall", "imerg_chennai_daily.csv"))
    return _data_cache["imerg"]

class HazardPrototypeResponse(BaseModel):
    predicted_state: int
    probability: float
    probability_p10: float
    probability_p50: float
    probability_p90: float
    risk_level: str
    lead_time_hours: int | None = None
    lead_time_text: str | None = None
    thresholds_disclaimer: str
    contributing_features: Dict[str, float]
    timestamp: datetime
    data_source: str
    simulation_label: str

def map_risk_level_generic(prob: float) -> str:
    if prob < 0.25: return "LOW"
    elif prob < 0.50: return "MODERATE"
    elif prob < 0.75: return "HIGH"
    else: return "CRITICAL"

def calc_heuristic_uncertainty(calc_func, base_kwargs, noise_std=0.1, n_samples=100):
    probs = []
    for _ in range(n_samples):
        noisy_kwargs = {k: v * np.random.normal(1.0, noise_std) for k, v in base_kwargs.items()}
        probs.append(calc_func(**noisy_kwargs))
    return float(np.percentile(probs, 10)), float(np.percentile(probs, 50)), float(np.percentile(probs, 90))


# --- HEATWAVE ---
def _calc_heatwave_prob(temp_max, temp_3d, humidity):
    prob = 0.0
    if temp_max > 36.0: prob += 0.3
    if temp_max > 40.0: prob += 0.3
    if temp_3d > 34.0: prob += 0.2
    if humidity > 70.0 and temp_max > 35.0: prob += 0.2 # Heat Index Effect
    return min(1.0, max(0.0, prob))

def get_latest_heatwave() -> dict:
    try:
        from app.core.satellite_ingestion import satellite_engine
        sat_data = satellite_engine.get_latest_satellite_telemetry()
        hw_live = sat_data.get('heatwave', {})
        telemetry_meta = sat_data.get('telemetry_meta', {})
        if not hw_live:
            raise HTTPException(status_code=503, detail=telemetry_meta.get("message", "Live weather telemetry is unavailable."))
        
        # Use ONLY Live Data
        temp_max_latest = hw_live.get('air_temp_c', 35.0)
        apparent_temp = hw_live.get('apparent_temp_c', 36.0)
        humidity = hw_live.get('humidity_percent', 65.0)
        lst = hw_live.get('lst_celsius')
        uv = hw_live.get('uv_index')
        solar_rad = hw_live.get('solar_radiation_wm2')
        cloud = hw_live.get('cloud_cover_percent')
        vpd = hw_live.get('vapor_pressure_deficit_kpa')
        wind = hw_live.get('wind_speed_kmh')
        
        prob = _calc_heatwave_prob(apparent_temp, temp_max_latest, humidity)
        if uv is not None and uv > 8.0: prob += 0.1
        if vpd is not None and vpd > 2.0: prob += 0.1
        prob = min(1.0, prob)
        p10, p50, p90 = max(0, prob - 0.05), prob, min(1.0, prob + 0.05)
        
        # Phase 17: Calculate 24-hour peak and early warning from trend_48h
        trend = hw_live.get('trend_48h', [])
        peak_temp = temp_max_latest
        peak_heat_index = apparent_temp
        peak_time = None
        min_temp = temp_max_latest
        early_warning_status = "NO IMMEDIATE THREAT"
        
        # The trend array has past 24h (0-23) and next 24h (24-47)
        if len(trend) > 24:
            next_24h = trend[24:]
            temps = [t['temp'] for t in next_24h if t['temp'] is not None]
            apps = [t['apparent_temp'] for t in next_24h if t['apparent_temp'] is not None]
            
            if temps:
                peak_temp = max(temps)
                min_temp = min(temps)
            
            if apps:
                peak_heat_index = max(apps)
                peak_idx = apps.index(peak_heat_index)
                peak_time = next_24h[peak_idx]['time']
                
            # Early warning logic based on heat index (apparent temp)
            if peak_heat_index >= 45:
                early_warning_status = "CRITICAL"
            elif peak_heat_index >= 40:
                early_warning_status = "HIGH RISK"
            elif peak_heat_index >= 35:
                early_warning_status = "ADVISORY"
            elif peak_heat_index >= 32:
                early_warning_status = "WATCH"
            
        return {
            "predicted_state": 1 if prob >= 0.5 else 0,
            "probability": prob,
            "probability_p10": p10,
            "probability_p50": p50,
            "probability_p90": p90,
            "risk_level": map_risk_level_generic(prob),
            "lead_time_hours": 24,
            "lead_time_text": "Live Observation Warning",
            "thresholds_disclaimer": "Live Real-Time Heat Index & LST Model",
            "contributing_features": {k: v for k, v in {
                "Apparent Temp (°C)": apparent_temp,
                "Air Temp (°C)": temp_max_latest,
                "Surface LST (°C)": lst,
                "Humidity (%)": humidity,
                "UV Index": uv,
                "Solar Radiation (W/m²)": solar_rad,
                "Cloud Cover (%)": cloud,
                "Vapor Pressure Deficit (kPa)": vpd,
                "Wind Speed (km/h)": wind
            }.items() if v is not None},
            "timestamp": datetime.now(timezone.utc),
            "data_source": hw_live.get("source", "Live Open-Meteo"),
            "simulation_label": "LIVE WEATHER + DERIVED RISK MODEL",
            "telemetry_mode": telemetry_meta.get("mode", "LIVE_WEATHER_API"),
            "forecast_metrics": {
                "peak_temp": peak_temp,
                "peak_heat_index": peak_heat_index,
                "min_temp": min_temp,
                "peak_time": peak_time,
                "early_warning_status": early_warning_status
            },
            "trend_48h": trend
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Heatwave calculation failed: {str(e)}")


# --- DROUGHT ---
def _calc_drought_prob(soil_moist_rz, reservoir_storage_pct=75.0, rain_7d=10.0):
    # Soil moisture deficit (0.30 is healthy field capacity, <0.15 is severe deficit)
    sm_deficit = max(0.0, 1.0 - (soil_moist_rz / 0.30))
    # Reservoir storage depletion penalty (below 40% escalates drought severity)
    res_deficit = max(0.0, 1.0 - (reservoir_storage_pct / 100.0))
    # Rainfall deficit indicator (normal 7d is ~25mm)
    rain_deficit = max(0.0, 1.0 - (rain_7d / 25.0))
    
    # Combined Multi-Indicator Drought Index (MIDI)
    composite_score = (sm_deficit * 0.45) + (res_deficit * 0.35) + (rain_deficit * 0.20)
    return min(1.0, max(0.0, composite_score))

def get_latest_drought() -> dict:
    try:
        from app.core.satellite_ingestion import satellite_engine
        sat_data = satellite_engine.get_latest_satellite_telemetry()
        dr_live = sat_data.get('drought', {})
        flood_live = sat_data.get('flood', {})
        telemetry_meta = sat_data.get('telemetry_meta', {})
        if not dr_live or not flood_live:
            raise HTTPException(status_code=503, detail=telemetry_meta.get("message", "Live weather telemetry is unavailable."))
        
        soil_moisture_surface = dr_live.get('soil_moisture_surface', 0.22)
        soil_moisture_rz = dr_live.get('soil_moisture_root_zone', 0.24)
        
        # Calculate reservoir storage from flood telemetry or default capacities
        total_storage = flood_live.get('total_reservoir_level', 8000.0)
        total_capacity = 11257.0  # Combined capacity of Poondi, Cholavaram, Red Hills, Chembarambakkam
        res_pct = round((total_storage / total_capacity) * 100.0, 1)
        rain_7d = flood_live.get('rainfall_7d_sum', 12.0)
        rain_30d_est = round(rain_7d * 4.2, 1)
        
        # Standardized Precipitation-Evapotranspiration & Soil Deficit Index
        smi = round(((soil_moisture_rz - 0.12) / (0.35 - 0.12)) * 100.0, 1) # Soil Water Availability %
        
        prob = _calc_drought_prob(soil_moisture_rz, res_pct, rain_7d)
        p10, p50, p90 = max(0, prob - 0.05), prob, min(1.0, prob + 0.05)
        
        # Early Warning Status
        if prob >= 0.70 or res_pct < 25.0:
            drought_phase = "EMERGENCY: STAGE 3 DROUGHT"
            action_code = "WATER_RATIONING_MANDATORY"
        elif prob >= 0.45 or res_pct < 45.0:
            drought_phase = "WARNING: STAGE 2 AGRICULTURAL STRESS"
            action_code = "GROUNDWATER_CONSERVATION_ACTIVE"
        elif prob >= 0.25:
            drought_phase = "ADVISORY: STAGE 1 WATCH"
            action_code = "VOLUNTARY_CONSERVATION"
        else:
            drought_phase = "NOMINAL: OPTIMAL WATER STORAGE"
            action_code = "STANDARD_OPERATIONS"

        trend_7d = dr_live.get('trend_7d', [])
        
        reservoirs_breakdown = {
            "POONDI": {"current_mcft": flood_live.get('POONDI', 2200), "capacity_mcft": 3231, "pct": round((flood_live.get('POONDI', 2200) / 3231) * 100, 1)},
            "CHOLAVARAM": {"current_mcft": flood_live.get('CHOLAVARAM', 600), "capacity_mcft": 1081, "pct": round((flood_live.get('CHOLAVARAM', 600) / 1081) * 100, 1)},
            "REDHILLS": {"current_mcft": flood_live.get('REDHILLS', 2400), "capacity_mcft": 3300, "pct": round((flood_live.get('REDHILLS', 2400) / 3300) * 100, 1)},
            "CHEMBARAMBAKKAM": {"current_mcft": flood_live.get('CHEMBARAMBAKKAM', 2800), "capacity_mcft": 3645, "pct": round((flood_live.get('CHEMBARAMBAKKAM', 2800) / 3645) * 100, 1)}
        }
            
        return {
            "predicted_state": 1 if prob >= 0.5 else 0,
            "probability": prob,
            "probability_p10": p10,
            "probability_p50": p50,
            "probability_p90": p90,
            "risk_level": map_risk_level_generic(prob),
            "lead_time_hours": 168,
            "lead_time_text": "7-Day Multi-Index Forecast",
            "thresholds_disclaimer": "Coupled Root-Zone Moisture & CMWSSB Reservoir Storage Twin",
            "drought_phase": drought_phase,
            "action_code": action_code,
            "contributing_features": {
                "Root Zone Moisture (m3/m3)": soil_moisture_rz,
                "Surface Moisture (m3/m3)": soil_moisture_surface,
                "Total Reservoir Storage (%)": res_pct,
                "Total Storage (mcft)": round(total_storage, 1),
                "7-Day Rainfall (mm)": rain_7d,
                "30-Day Est Rainfall (mm)": rain_30d_est,
                "Soil Water Availability (%)": max(0.0, min(100.0, smi))
            },
            "reservoirs": reservoirs_breakdown,
            "trend_7d": trend_7d,
            "timestamp": datetime.now(timezone.utc),
            "data_source": "Open-Meteo weather-derived soil fields + simulated CMWSSB reservoir model",
            "simulation_label": "LIVE WEATHER + DERIVED DROUGHT MODEL",
            "telemetry_mode": telemetry_meta.get("mode", "LIVE_WEATHER_API")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Drought calculation failed: {str(e)}")


# --- WILDFIRE ---
def _calc_wildfire_prob(fwi, wind, active_fires):
    prob = 0.0
    if fwi > 15.0: prob += 0.4
    if fwi > 30.0: prob += 0.3
    if wind > 20.0: prob += 0.2
    if active_fires > 0: prob += 0.5 # Direct hotspot detection triggers high risk
    return min(1.0, max(0.0, prob))

def get_latest_wildfire() -> dict:
    try:
        from app.core.satellite_ingestion import satellite_engine
        sat_data = satellite_engine.get_latest_satellite_telemetry()
        wf_live = sat_data.get('wildfire', {})
        telemetry_meta = sat_data.get('telemetry_meta', {})
        if not wf_live:
            raise HTTPException(status_code=503, detail=telemetry_meta.get("message", "Live weather telemetry is unavailable."))
        
        fwi = wf_live.get('fwi_estimate', 5.0)
        wind = wf_live.get('wind_speed_kmh', 10.0)
        surface_temp = wf_live.get('surface_temp_c', 30.0)
        active_fires = wf_live.get('active_fires_detected')
        max_frp = wf_live.get('max_frp_mw')
        
        # An unavailable NASA FIRMS feed is not evidence of zero hotspots.
        prob = _calc_wildfire_prob(fwi, wind, active_fires or 0)
        p10, p50, p90 = max(0, prob - 0.05), prob, min(1.0, prob + 0.05)
        
        return {
            "predicted_state": 1 if prob >= 0.5 else 0,
            "probability": prob,
            "probability_p10": p10,
            "probability_p50": p50,
            "probability_p90": p90,
            "risk_level": map_risk_level_generic(prob),
            "lead_time_hours": 48,
            "lead_time_text": "Live weather-derived fire-risk proxy",
            "thresholds_disclaimer": "Weather-derived fire-risk proxy. Hotspot evidence is shown only when NASA FIRMS is configured and returns a response.",
            "contributing_features": {k: v for k, v in {
                "Fire Weather Index (FWI)": fwi,
                "NASA Active Hotspots (VIIRS)": active_fires,
                "Max Fire Radiative Power (MW)": max_frp,
                "Wind Speed (km/h)": wind,
                "Surface Temp (°C)": surface_temp
            }.items() if v is not None},
            "timestamp": datetime.now(timezone.utc),
            "data_source": wf_live.get("source", "Live Open-Meteo"),
            "simulation_label": "LIVE WEATHER + FIRE-WEATHER PROXY",
            "telemetry_mode": telemetry_meta.get("mode", "LIVE_WEATHER_API")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Wildfire calculation failed: {str(e)}")


# --- EXTREME RAINFALL ---
def _calc_extreme_rain_prob(cape, rain):
    """Transparent short-horizon convective review proxy.

    Open-Meteo's current precipitation is an hourly amount.  The former
    50 mm-only threshold hid light and moderate observed rainfall completely.
    This remains a review proxy, not an official nowcast or public warning.
    """
    prob = 0.0
    if rain > 0.0: prob += 0.08
    if rain >= 1.0: prob += 0.12
    if rain >= 5.0: prob += 0.20
    if rain >= 10.0: prob += 0.25
    if cape >= 1000.0: prob += 0.10
    if cape >= 1800.0: prob += 0.15
    if cape >= 2500.0: prob += 0.15
    return min(1.0, max(0.0, prob))

def get_latest_extreme_rainfall() -> dict:
    try:
        from app.core.satellite_ingestion import satellite_engine
        sat_data = satellite_engine.get_latest_satellite_telemetry()
        er_live = sat_data.get('extreme_rainfall', {})
        telemetry_meta = sat_data.get('telemetry_meta', {})
        if not er_live:
            raise HTTPException(status_code=503, detail=telemetry_meta.get("message", "Live weather telemetry is unavailable."))
        
        cape = er_live.get('cape_j_kg', 0.0)
        rain = er_live.get('current_precip_mm', 0.0)
        
        prob = _calc_extreme_rain_prob(cape, rain)
        p10, p50, p90 = max(0, prob - 0.05), prob, min(1.0, prob + 0.05)
            
        return {
            "predicted_state": 1 if prob >= 0.5 else 0,
            "probability": prob,
            "probability_p10": p10,
            "probability_p50": p50,
            "probability_p90": p90,
            "risk_level": map_risk_level_generic(prob),
            "lead_time_hours": 6,
            "lead_time_text": "Live Convective Monitoring",
            "thresholds_disclaimer": "Weather-provider precipitation and CAPE review proxy; not an IMD Doppler nowcast or public warning.",
            "contributing_features": {
                "Convective Energy (CAPE)": cape,
                "Current Precipitation (mm, provider hour)": rain,
                "Weather Code": er_live.get("weather_code")
            },
            "timestamp": datetime.now(timezone.utc),
            "data_source": er_live.get("source", "Live Open-Meteo"),
            "simulation_label": "LIVE WEATHER + CONVECTIVE PROXY",
            "telemetry_mode": telemetry_meta.get("mode", "LIVE_WEATHER_API")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extreme Rainfall calculation failed: {str(e)}")
