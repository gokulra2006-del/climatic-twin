import json
import os
from datetime import datetime, timezone
import dateutil.parser

FORECAST_FILE = r"C:\Users\gokul\Desktop\PROJECTS\climatetwin\data\raw\forecast\open_meteo\forecast_latest.json"

def calculate_lead_time(hazard_calc_func, base_features) -> tuple:
    """
    Simulates future risk using Open-Meteo forecast data.
    Returns (lead_time_hours: int | None, lead_time_text: str | None)
    """
    if not os.path.exists(FORECAST_FILE):
        return None, "Forecast data unavailable"

    try:
        with open(FORECAST_FILE, 'r') as f:
            forecast_data = json.load(f)
            
        hourly = forecast_data.get("hourly", {})
        times = hourly.get("time", [])
        temps = hourly.get("temperature_2m", [])
        winds = hourly.get("wind_speed_10m", [])
        rains = hourly.get("precipitation", [])
        
        now = datetime.now(timezone.utc)
        
        for i, t_str in enumerate(times):
            t = dateutil.parser.parse(t_str)
            if t.tzinfo is None:
                t = t.replace(tzinfo=timezone.utc)
                
            if t > now:
                # Prepare mock future features
                future_features = base_features.copy()
                if "max_temp_c" in future_features and i < len(temps):
                    future_features["max_temp_c"] = max(future_features["max_temp_c"], temps[i])
                if "temp_max" in future_features and i < len(temps):
                    future_features["temp_max"] = max(future_features["temp_max"], temps[i])
                if "temp_mean" in future_features and i < len(temps):
                    future_features["temp_mean"] = temps[i]
                if "wind_speed_ms" in future_features and i < len(winds):
                    # convert km/h to m/s
                    future_features["wind_speed_ms"] = winds[i] / 3.6
                if "rainfall_24h_mm" in future_features and i < len(rains):
                    future_features["rainfall_24h_mm"] += rains[i]
                if "rainfall_daily" in future_features and i < len(rains):
                    future_features["rainfall_daily"] += rains[i]
                    
                # Calculate probability with future features
                prob = hazard_calc_func(**future_features)
                
                if prob >= 0.5: # MODERATE, HIGH, CRITICAL
                    hours = int((t - now).total_seconds() / 3600)
                    level = "High" if prob >= 0.75 else "Moderate"
                    if prob >= 0.8: level = "Critical"
                    return hours, f"{level} risk expected in {hours} hours"
                    
        return None, "No threshold crossing forecast in the next 7 days"
    except Exception as e:
        return None, f"Lead time calculation error: {str(e)}"

def calculate_flood_lead_time(model, base_features_arr, feature_order) -> tuple:
    """
    Simulates future flood risk using Open-Meteo forecast data and the Random Forest model.
    """
    if not os.path.exists(FORECAST_FILE):
        return None, "Forecast data unavailable"

    try:
        with open(FORECAST_FILE, 'r') as f:
            forecast_data = json.load(f)
            
        hourly = forecast_data.get("hourly", {})
        times = hourly.get("time", [])
        temps = hourly.get("temperature_2m", [])
        winds = hourly.get("wind_speed_10m", [])
        rains = hourly.get("precipitation", [])
        
        now = datetime.now(timezone.utc)
        
        for i, t_str in enumerate(times):
            t = dateutil.parser.parse(t_str)
            if t.tzinfo is None:
                t = t.replace(tzinfo=timezone.utc)
                
            if t > now:
                # Copy current features array
                import copy
                import numpy as np
                future_features = copy.deepcopy(base_features_arr[0])
                
                # Update features based on indices
                if i < len(temps):
                    if "temp_max" in feature_order:
                        idx = feature_order.index("temp_max")
                        future_features[idx] = max(future_features[idx], temps[i])
                    if "temp_mean" in feature_order:
                        idx = feature_order.index("temp_mean")
                        future_features[idx] = temps[i]
                if i < len(winds):
                    if "wind_speed_mean" in feature_order:
                        idx = feature_order.index("wind_speed_mean")
                        future_features[idx] = winds[i] / 3.6
                if i < len(rains):
                    if "rainfall_daily" in feature_order:
                        idx = feature_order.index("rainfall_daily")
                        future_features[idx] += rains[i]
                
                features_arr = np.array(future_features).reshape(1, -1)
                prob = float(model.predict_proba(features_arr)[0, 1])
                
                if prob >= 0.5:
                    hours = int((t - now).total_seconds() / 3600)
                    level = "High" if prob >= 0.75 else "Moderate"
                    if prob >= 0.8: level = "Critical"
                    return hours, f"{level} risk expected in {hours} hours"
                    
        return None, "No threshold crossing forecast in the next 7 days"
    except Exception as e:
        return None, f"Lead time calculation error: {str(e)}"
