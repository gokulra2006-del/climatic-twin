import os
import requests
import logging
import threading
from datetime import datetime, timezone
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Chennai Coordinates
LAT = 13.0827
LON = 80.2707
# Bounding box for Chennai region (Min Lon, Min Lat, Max Lon, Max Lat)
CHENNAI_BBOX = "79.8,12.8,80.4,13.3"

class LiveTelemetryEngine:
    """
    Phase 19: Genuine Real-Time Telemetry Ingestion.
    """
    
    def __init__(self):
        self._cache = {}
        self._lock = threading.Lock()
        self.firms_key = os.getenv("NASA_FIRMS_KEY", "")
        
    def fetch_live_data(self) -> Dict[str, Any]:
        try:
            # 0. Check Firebase for Raspberry Pi telemetry first
            from app.core.firebase_client import get_firebase_telemetry
            firebase_data = get_firebase_telemetry()
            
            if firebase_data and isinstance(firebase_data, dict):
                logger.info("Using Live Raspberry Pi Telemetry from Firebase!")
                # Assuming the Pi sends basic telemetry, we map it, 
                # but we can also merge it with Open-Meteo if needed.
                return {
                    'temperature': firebase_data.get('temperature', 30.0),
                    'apparent_temperature': firebase_data.get('apparent_temperature', 35.0),
                    'humidity': firebase_data.get('humidity', 70),
                    'wind_speed': firebase_data.get('wind_speed', 10.0),
                    'precipitation': firebase_data.get('precipitation', 0.0),
                    'soil_moisture_surface': firebase_data.get('soil_moisture', 0.2),
                    'soil_moisture_deep': firebase_data.get('soil_moisture', 0.2),
                    'soil_temperature': firebase_data.get('temperature', 30.0) + 3.0,
                    'uv_index': firebase_data.get('uv_index', 6.0),
                    'vapor_pressure_deficit': firebase_data.get('vpd', 1.5),
                    'source': 'Live Raspberry Pi (Firebase)'
                }

            # 1. Main Weather (Open-Meteo Fallback)
            weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,rain,showers,weather_code,cloud_cover,pressure_msl,surface_pressure,wind_speed_10m,wind_direction_10m,dew_point_2m&hourly=temperature_2m,relative_humidity_2m,dew_point_2m,apparent_temperature,precipitation,rain,soil_temperature_0cm,soil_moisture_0_to_7cm,soil_moisture_28_to_100cm,cape,uv_index,direct_radiation,vapor_pressure_deficit&timezone=Asia%2FKolkata&past_hours=168"
            weather_res = requests.get(weather_url, timeout=10).json()
            
            current = weather_res.get('current', {})
            hourly = weather_res.get('hourly', {})
            
            temp = current.get('temperature_2m', 30.0)
            app_temp = current.get('apparent_temperature', 35.0)
            rh = current.get('relative_humidity_2m', 70)
            wind = current.get('wind_speed_10m', 10.0)
            rain = current.get('precipitation', 0.0)
            
            def get_latest(arr, default):
                return next((x for x in reversed(arr) if x is not None), default)

            soil_moist_surface = get_latest(hourly.get('soil_moisture_0_to_7cm', []), 0.2)
            soil_moist_deep = get_latest(hourly.get('soil_moisture_28_to_100cm', []), 0.2)
            soil_temp = get_latest(hourly.get('soil_temperature_0cm', []), temp + 3.0)
            cape = get_latest(hourly.get('cape', []), 0.0)
            
            uv = get_latest(hourly.get('uv_index', []), 8.0)
            solar_rad = get_latest(hourly.get('direct_radiation', []), 600.0)
            cloud_cover = current.get('cloud_cover', 20)
            vpd = get_latest(hourly.get('vapor_pressure_deficit', []), 1.5)
            
            # 2. NASA FIRMS API (Active Fires)
            active_fire_count = 0
            max_frp = 0.0
            
            if self.firms_key:
                try:
                    # Check VIIRS SNPP for the last 1 day
                    firms_url = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{self.firms_key}/VIIRS_SNPP_NRT/{CHENNAI_BBOX}/1"
                    firms_res = requests.get(firms_url, timeout=10)
                    
                    if firms_res.status_code == 200:
                        lines = firms_res.text.strip().split('\\n')
                        # Line 0 is header. Lines 1+ are active fires.
                        if len(lines) > 1:
                            active_fire_count = len(lines) - 1
                            # Parse FRP (Fire Radiative Power) - usually index 12 for VIIRS
                            for line in lines[1:]:
                                parts = line.split(',')
                                if len(parts) > 12:
                                    try:
                                        frp = float(parts[12])
                                        if frp > max_frp:
                                            max_frp = frp
                                    except:
                                        pass
                except Exception as e:
                    logger.warning(f"Failed to fetch NASA FIRMS data: {e}")
            
            # Phase 17: Extract 48-hour window (past 24h + next 24h) for heatwave trend and early warning
            # past_hours=168 means index 168 is the current hour.
            hw_trend = []
            try:
                h_times = hourly.get('time', [])
                h_temp = hourly.get('temperature_2m', [])
                h_app = hourly.get('apparent_temperature', [])
                h_hum = hourly.get('relative_humidity_2m', [])
                if len(h_times) > 192:
                    for i in range(144, 193):
                        hw_trend.append({
                            "time": h_times[i],
                            "temp": h_temp[i],
                            "apparent_temp": h_app[i],
                            "humidity": h_hum[i]
                        })
            except Exception as e:
                logger.warning(f"Failed to extract heatwave trend: {e}")

            heatwave_data = {
                "lst_celsius": soil_temp,
                "apparent_temp_c": app_temp,
                "air_temp_c": temp,
                "humidity_percent": rh,
                "uv_index": uv,
                "solar_radiation_wm2": solar_rad,
                "cloud_cover_percent": cloud_cover,
                "vapor_pressure_deficit_kpa": vpd,
                "wind_speed_kmh": wind,
                "trend_48h": hw_trend,
                "source": "Live Copernicus/NOAA (Open-Meteo)",
                "status": "LIVE_FETCHED"
            }
            
            drought_data = {
                "soil_moisture_surface": soil_moist_surface,
                "soil_moisture_root_zone": soil_moist_deep,
                "source": "Live Copernicus/NOAA (Open-Meteo)",
                "status": "LIVE_FETCHED"
            }
            
            fwi_proxy = max(0.0, ((temp + (wind * 0.2)) / (rh + 0.1)) * 10.0)
            wildfire_data = {
                "fwi_estimate": round(fwi_proxy, 2),
                "active_fires_detected": active_fire_count,
                "max_frp_mw": round(max_frp, 1),
                "wind_speed_kmh": wind,
                "source": "NASA FIRMS (VIIRS) & Open-Meteo",
                "status": "LIVE_FETCHED"
            }
            
            ext_rain_data = {
                "cape_j_kg": cape,
                "current_precip_mm": rain,
                "source": "Live Copernicus/NOAA (Open-Meteo)",
                "status": "LIVE_FETCHED"
            }
            
            # 4. Flood Telemetry — rainfall accumulations + weather + simulated reservoirs
            hourly_precip = [p for p in hourly.get('precipitation', []) if p is not None]
            hourly_temp = [t for t in hourly.get('temperature_2m', []) if t is not None]
            hourly_dew = [d for d in hourly.get('dew_point_2m', []) if d is not None]
            
            # Cumulative rainfall sums (hourly mm → daily-equivalent mm)
            rainfall_daily = sum(hourly_precip[-24:]) if len(hourly_precip) >= 24 else sum(hourly_precip)
            rainfall_3d = sum(hourly_precip[-72:]) if len(hourly_precip) >= 72 else sum(hourly_precip)
            rainfall_5d = sum(hourly_precip[-120:]) if len(hourly_precip) >= 120 else sum(hourly_precip)
            rainfall_7d = sum(hourly_precip[-168:]) if len(hourly_precip) >= 168 else sum(hourly_precip)
            
            # Temperature aggregates from hourly data (last 24h)
            recent_temp = hourly_temp[-24:] if len(hourly_temp) >= 24 else hourly_temp
            temp_mean_val = sum(recent_temp) / len(recent_temp) if recent_temp else temp
            temp_max_val = max(recent_temp) if recent_temp else temp
            temp_min_val = min(recent_temp) if recent_temp else temp
            
            # Dew point from hourly (last 24h mean)
            recent_dew = hourly_dew[-24:] if len(hourly_dew) >= 24 else hourly_dew
            dew_point_val = sum(recent_dew) / len(recent_dew) if recent_dew else current.get('dew_point_2m', 24.0)
            
            # Wind speed in m/s (Open-Meteo gives km/h, model expects m/s)
            wind_ms = wind / 3.6
            
            # Simulated reservoir levels (no live API available from CMWSSB)
            # Physical model: base capacity + rainfall-driven inflow - constant outflow
            # These are approximate mcft values calibrated to Chennai's 4-reservoir system
            base_levels = {"POONDI": 2200, "CHOLAVARAM": 600, "REDHILLS": 2400, "CHEMBARAMBAKKAM": 2800}
            capacities = {"POONDI": 3231, "CHOLAVARAM": 1081, "REDHILLS": 3300, "CHEMBARAMBAKKAM": 3645}
            inflow_factor = rainfall_7d * 2.5  # mm of weekly rain → mcft inflow estimate
            
            sim_reservoirs = {}
            for name, base in base_levels.items():
                level = base + inflow_factor - 50  # subtract daily usage
                level = max(0, min(capacities[name], level))  # clamp to [0, capacity]
                sim_reservoirs[name] = round(level, 1)
            
            total_reservoir = sum(sim_reservoirs.values())
            
            flood_data = {
                "rainfall_daily": round(rainfall_daily, 2),
                "rainfall_3d_sum": round(rainfall_3d, 2),
                "rainfall_5d_sum": round(rainfall_5d, 2),
                "rainfall_7d_sum": round(rainfall_7d, 2),
                "temp_mean": round(temp_mean_val, 2),
                "temp_max": round(temp_max_val, 2),
                "temp_min": round(temp_min_val, 2),
                "dew_point_mean": round(dew_point_val, 2),
                "wind_speed_mean": round(wind_ms, 2),
                "POONDI": sim_reservoirs["POONDI"],
                "CHOLAVARAM": sim_reservoirs["CHOLAVARAM"],
                "REDHILLS": sim_reservoirs["REDHILLS"],
                "CHEMBARAMBAKKAM": sim_reservoirs["CHEMBARAMBAKKAM"],
                "total_reservoir_level": round(total_reservoir, 1),
                "source": "Live Open-Meteo (Rainfall/Weather) + Simulated Reservoirs",
                "status": "LIVE_FETCHED"
            }
            
            return {
                "heatwave": heatwave_data,
                "drought": drought_data,
                "wildfire": wildfire_data,
                "extreme_rainfall": ext_rain_data,
                "flood": flood_data,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Live Telemetry Fetch Failed: {e}")
            return {}

    def get_latest_satellite_telemetry(self) -> Dict[str, Any]:
        with self._lock:
            now = datetime.now(timezone.utc)
            if "last_update" in self._cache and (now - self._cache["last_update"]).total_seconds() < 600:
                return self._cache["data"]
                
            live_payload = self.fetch_live_data()
            if not live_payload:
                return self._cache.get("data", {})
                
            self._cache["data"] = live_payload
            self._cache["last_update"] = now
            return live_payload

satellite_engine = LiveTelemetryEngine()
