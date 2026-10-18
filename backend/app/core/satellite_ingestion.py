import os
import json
import requests
import logging
import threading
import copy
from datetime import datetime, timezone, timedelta
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Chennai Coordinates
LAT = 13.0827
LON = 80.2707
# Bounding box for Chennai region (Min Lon, Min Lat, Max Lon, Max Lat)
CHENNAI_BBOX = "79.8,12.8,80.4,13.3"

# Chennai Multi-Station Spatial Sensor Network Coordinates
CHENNAI_SENSOR_STATIONS = {
    "CHENNAI_CENTRAL": {"name": "Chennai Central Met Station", "lat": 13.0827, "lon": 80.2707, "zone": "Central"},
    "POONDI_CATCHMENT": {"name": "Poondi Catchment Station", "lat": 13.1900, "lon": 79.8600, "zone": "West Reservoirs"},
    "CHEMBARAMBAKKAM": {"name": "Chembarambakkam Catchment", "lat": 13.0100, "lon": 80.0600, "zone": "Southwest Basins"},
    "ADYAR_ESTUARY": {"name": "Adyar Estuary Tidal Gauge", "lat": 13.0100, "lon": 80.2600, "zone": "South Coast"},
    "SHOLINGANALLUR_OMR": {"name": "Sholinganallur Tech Corridor", "lat": 12.8990, "lon": 80.2280, "zone": "South Suburbs"},
    "ENNORE_PORT": {"name": "Ennore Marine Met Buoy", "lat": 13.2300, "lon": 80.3300, "zone": "North Coast"}
}


class LiveTelemetryEngine:
    """
    Phase 19: Genuine Real-Time Telemetry Ingestion.
    """
    
    def __init__(self):
        self._cache = {}
        self._lock = threading.Lock()
        self.firms_key = os.getenv("NASA_FIRMS_KEY", "")
        backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        self.history_path = os.getenv("LIVE_WEATHER_HISTORY_PATH", os.path.join(backend_root, "data", "runtime", "live_weather_history.json"))

    def _read_weather_history(self) -> list[Dict[str, Any]]:
        try:
            if not os.path.exists(self.history_path):
                return []
            with open(self.history_path, "r", encoding="utf-8") as history_file:
                saved = json.load(history_file)
            return saved if isinstance(saved, list) else []
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Could not read local weather backup: %s", exc)
            return []

    def _upsert_weather_history(self, records: list[Dict[str, Any]]) -> None:
        """Save provider observations locally with their source and observation time."""
        if not records:
            return
        try:
            rows = {(item.get("observed_at"), item.get("source")): item for item in self._read_weather_history() if item.get("observed_at")}
            for record in records:
                rows[(record["observed_at"], record["source"])] = record
            cutoff = (datetime.now(timezone.utc) - timedelta(days=90)).date().isoformat()
            retained = [item for item in rows.values() if item["observed_at"][:10] >= cutoff]
            retained.sort(key=lambda item: item["observed_at"])
            os.makedirs(os.path.dirname(self.history_path), exist_ok=True)
            temporary_path = f"{self.history_path}.tmp"
            with open(temporary_path, "w", encoding="utf-8") as history_file:
                json.dump(retained, history_file, ensure_ascii=False, separators=(",", ":"))
            os.replace(temporary_path, self.history_path)
        except OSError as exc:
            logger.warning("Could not save local weather backup: %s", exc)

    @staticmethod
    def _mean(values: list[Any]) -> float | None:
        numeric = [float(value) for value in values if value is not None]
        return round(sum(numeric) / len(numeric), 2) if numeric else None

    def get_weather_backup_analysis(self, days: int = 7) -> Dict[str, Any]:
        """Compare saved weather observations for today and yesterday at the same hour."""
        self.get_latest_satellite_telemetry()
        records = self._read_weather_history()
        if not records:
            return {"status": "UNAVAILABLE", "message": "No provider weather observations have been saved locally yet.", "daily": []}
        days = max(2, min(days, 30))
        latest_at = max(str(item["observed_at"]) for item in records)
        latest_day, latest_hour = latest_at[:10], latest_at[11:13]
        start_day = (datetime.fromisoformat(latest_day).date() - timedelta(days=days - 1)).isoformat()
        observed = [item for item in records if start_day <= item["observed_at"][:10] <= latest_day]
        by_day: Dict[str, list[Dict[str, Any]]] = {}
        for item in observed:
            by_day.setdefault(item["observed_at"][:10], []).append(item)

        def summarize(rows: list[Dict[str, Any]]) -> Dict[str, Any]:
            return {
                "hours": len(rows),
                "temperature_mean_c": self._mean([row.get("temperature_c") for row in rows]),
                "temperature_max_c": max((row["temperature_c"] for row in rows if row.get("temperature_c") is not None), default=None),
                "apparent_temperature_mean_c": self._mean([row.get("apparent_temperature_c") for row in rows]),
                "humidity_mean_pct": self._mean([row.get("humidity_pct") for row in rows]),
                "rainfall_total_mm": round(sum(float(row.get("precipitation_mm") or 0) for row in rows), 2),
                "wind_mean_kmh": self._mean([row.get("wind_speed_kmh") for row in rows]),
            }

        daily = [{"date": day, **summarize(rows)} for day, rows in sorted(by_day.items())]
        today_rows = [row for row in by_day.get(latest_day, []) if row["observed_at"][11:13] <= latest_hour]
        yesterday_day = (datetime.fromisoformat(latest_day).date() - timedelta(days=1)).isoformat()
        yesterday_rows = [row for row in by_day.get(yesterday_day, []) if row["observed_at"][11:13] <= latest_hour]
        today, yesterday = summarize(today_rows), summarize(yesterday_rows)
        def delta(name: str) -> float | None:
            return round(today[name] - yesterday[name], 2) if today.get(name) is not None and yesterday.get(name) is not None else None
        comparison = {
            "compared_through_hour": f"{latest_hour}:00",
            "temperature_mean_delta_c": delta("temperature_mean_c"),
            "apparent_temperature_mean_delta_c": delta("apparent_temperature_mean_c"),
            "humidity_mean_delta_pct": delta("humidity_mean_pct"),
            "rainfall_delta_mm": delta("rainfall_total_mm"),
            "wind_mean_delta_kmh": delta("wind_mean_kmh"),
        }
        temp_delta, rain_delta = comparison["temperature_mean_delta_c"], comparison["rainfall_delta_mm"]
        analysis = "Insufficient same-time observations for a yesterday comparison."
        if temp_delta is not None and rain_delta is not None:
            analysis = f"Today so far is {abs(temp_delta):.1f}°C {'warmer' if temp_delta >= 0 else 'cooler'} and {abs(rain_delta):.1f} mm {'wetter' if rain_delta >= 0 else 'drier'} than yesterday at the same hour."
        return {
            "status": "BACKUP_AVAILABLE", "source": "Local backup of Open-Meteo hourly weather observations", "retention_days": 90,
            "records_saved": len(records), "latest_observation_at": latest_at, "daily": daily,
            "today_to_now": today, "yesterday_same_time": yesterday, "comparison": comparison, "analysis": analysis,
            "boundary": "Provider observation history only; forecast hours and simulated reservoir values are excluded."
        }
        
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
            weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,rain,showers,weather_code,cloud_cover,pressure_msl,surface_pressure,wind_speed_10m,wind_direction_10m,dew_point_2m&hourly=temperature_2m,relative_humidity_2m,dew_point_2m,apparent_temperature,precipitation,rain,wind_speed_10m,soil_temperature_0cm,soil_moisture_0_to_7cm,soil_moisture_28_to_100cm,cape,uv_index,direct_radiation,vapor_pressure_deficit&timezone=Asia%2FKolkata&past_hours=168"
            weather_res = requests.get(weather_url, timeout=10).json()
            
            current = weather_res.get('current', {})
            hourly = weather_res.get('hourly', {})
            
            # Do not silently turn an unavailable provider response into "live" data.
            # These five values are the minimum observed weather inputs required by the
            # live dashboards.  If any are absent, the caller receives an unavailable
            # state instead of plausible-looking mock numbers.
            required_current = (
                'temperature_2m', 'apparent_temperature', 'relative_humidity_2m',
                'wind_speed_10m', 'precipitation'
            )
            missing_current = [field for field in required_current if current.get(field) is None]
            if missing_current:
                logger.warning("Open-Meteo response missing required current fields: %s", missing_current)
                return {}

            temp = current['temperature_2m']
            app_temp = current['apparent_temperature']
            rh = current['relative_humidity_2m']
            wind = current['wind_speed_10m']
            rain = current['precipitation']
            
            def get_latest(arr):
                return next((x for x in reversed(arr) if x is not None), None)

            soil_moist_surface = get_latest(hourly.get('soil_moisture_0_to_7cm', []))
            soil_moist_deep = get_latest(hourly.get('soil_moisture_28_to_100cm', []))
            soil_temp = get_latest(hourly.get('soil_temperature_0cm', []))
            cape = get_latest(hourly.get('cape', []))
            
            uv = get_latest(hourly.get('uv_index', []))
            solar_rad = get_latest(hourly.get('direct_radiation', []))
            cloud_cover = current.get('cloud_cover')
            vpd = get_latest(hourly.get('vapor_pressure_deficit', []))

            # Save only provider hours at or before the current observation time.
            # Later hours are forecasts and are deliberately excluded from backup.
            observed_at = current.get("time")
            hourly_times = hourly.get("time", [])
            def hourly_value(field: str, index: int):
                values = hourly.get(field, [])
                return values[index] if index < len(values) else None
            backup_records = []
            for index, time_value in enumerate(hourly_times):
                if observed_at and time_value > observed_at:
                    continue
                backup_records.append({
                    "observed_at": time_value,
                    "source": "Open-Meteo hourly weather archive",
                    "retrieved_at": datetime.now(timezone.utc).isoformat(),
                    "temperature_c": hourly_value("temperature_2m", index),
                    "apparent_temperature_c": hourly_value("apparent_temperature", index),
                    "humidity_pct": hourly_value("relative_humidity_2m", index),
                    "precipitation_mm": hourly_value("precipitation", index),
                    "wind_speed_kmh": hourly_value("wind_speed_10m", index),
                })
            self._upsert_weather_history(backup_records)
            
            # 2. NASA FIRMS API (Active Fires)
            active_fire_count = None
            max_frp = None
            
            if self.firms_key:
                active_fire_count = 0
                max_frp = 0.0
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
                "source": "Open-Meteo live weather-derived fields",
                "status": "LIVE_FETCHED"
            }
            
            # Phase 18: Extract drought moisture trend across past 7 days
            drought_trend = []
            try:
                h_times = hourly.get('time', [])
                h_sm_surf = hourly.get('soil_moisture_0_to_7cm', [])
                h_sm_deep = hourly.get('soil_moisture_28_to_100cm', [])
                h_precip = hourly.get('precipitation', [])
                if len(h_times) >= 168:
                    for i in range(0, min(len(h_times), 192), 24):
                        drought_trend.append({
                            "time": h_times[i],
                            "surface_moisture": round(h_sm_surf[i], 3) if i < len(h_sm_surf) and h_sm_surf[i] is not None else None,
                            "root_zone_moisture": round(h_sm_deep[i], 3) if i < len(h_sm_deep) and h_sm_deep[i] is not None else None,
                            "precipitation": round(h_precip[i] if i < len(h_precip) and h_precip[i] is not None else 0.0, 1)
                        })
            except Exception as e:
                logger.warning(f"Failed to extract drought trend: {e}")

            drought_data = {
                "soil_moisture_surface": soil_moist_surface,
                "soil_moisture_root_zone": soil_moist_deep,
                "trend_7d": drought_trend,
                "source": "Open-Meteo live weather-derived fields",
                "status": "LIVE_FETCHED"
            }
            
            fwi_proxy = max(0.0, ((temp + (wind * 0.2)) / (rh + 0.1)) * 10.0)
            wildfire_data = {
                "fwi_estimate": round(fwi_proxy, 2),
                "active_fires_detected": active_fire_count,
                "max_frp_mw": round(max_frp, 1) if max_frp is not None else None,
                "wind_speed_kmh": wind,
                "source": "NASA FIRMS (VIIRS) & Open-Meteo" if self.firms_key else "Open-Meteo fire-weather proxy (NASA FIRMS key not configured)",
                "status": "LIVE_FETCHED"
            }
            
            ext_rain_data = {
                "cape_j_kg": cape,
                "current_precip_mm": rain,
                "source": "Open-Meteo live weather-derived fields",
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
            
            # Spatial estimates are derived from one live weather API location, not
            # independent physical stations.  Keep them available for research UI
            # exploration, but make their provenance explicit.
            sensor_network = {}
            for s_id, s_info in CHENNAI_SENSOR_STATIONS.items():
                # Micro-climatic variance around Chennai base readings
                lat_offset = (s_info["lat"] - LAT) * 15.0
                lon_offset = (s_info["lon"] - LON) * 12.0
                
                s_temp = round(temp + lat_offset * 0.1, 1)
                s_rain = round(max(0.0, rain + abs(lon_offset) * 0.2), 1)
                s_humidity = round(min(98.0, max(40.0, rh - lat_offset * 0.4)), 1)
                s_wind = round(max(0.5, wind + (1.5 if "Coast" in s_info["zone"] else 0.0)), 1)
                s_sm_surf = round(soil_moist_surface * (1.1 if "Catchment" in s_info["name"] else 1.0), 3)
                
                status = "DERIVED"
                quality_flag = "ESTIMATED_FROM_CITY_WEATHER"
                
                sensor_network[s_id] = {
                    "station_id": s_id,
                    "name": s_info["name"],
                    "latitude": s_info["lat"],
                    "longitude": s_info["lon"],
                    "zone": s_info["zone"],
                    "readings": {
                        "temperature_c": s_temp,
                        "precipitation_mm": s_rain,
                        "humidity_pct": s_humidity,
                        "wind_speed_kmh": s_wind,
                        "soil_moisture_m3m3": s_sm_surf
                    },
                    "status": status,
                    "quality_flag": quality_flag,
                    "last_sync": datetime.now(timezone.utc).isoformat(),
                    "source_mode": "DERIVED_SPATIAL_ESTIMATE"
                }

            return {
                "heatwave": heatwave_data,
                "drought": drought_data,
                "wildfire": wildfire_data,
                "extreme_rainfall": ext_rain_data,
                "flood": flood_data,
                "sensor_network": sensor_network,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "telemetry_meta": {
                    "mode": "LIVE_WEATHER_API",
                    "provider": "Open-Meteo",
                    "observed_at": current.get("time"),
                    "retrieved_at": datetime.now(timezone.utc).isoformat(),
                    "weather_fields": "live provider observations/nowcasts",
                    "reservoir_fields": "simulated from rainfall; no verified reservoir feed is connected",
                    "station_network": "spatial estimates derived from the city weather feed; not physical station telemetry"
                }
            }
            
        except Exception as e:
            logger.error(f"Live Telemetry Fetch Failed: {e}")
            return {}

    def get_latest_satellite_telemetry(self) -> Dict[str, Any]:
        with self._lock:
            now = datetime.now(timezone.utc)
            if "last_update" in self._cache and (now - self._cache["last_update"]).total_seconds() < 600:
                return copy.deepcopy(self._cache["data"])
                
            live_payload = self.fetch_live_data()
            if not live_payload:
                cached = self._cache.get("data")
                if not cached:
                    return {
                        "telemetry_meta": {
                            "mode": "UNAVAILABLE",
                            "provider": "Open-Meteo",
                            "message": "No live weather response or cache is available."
                        }
                    }
                stale = copy.deepcopy(cached)
                age = (now - self._cache["last_update"]).total_seconds()
                stale["telemetry_meta"] = {
                    **stale.get("telemetry_meta", {}),
                    "mode": "STALE_CACHE",
                    "cache_age_seconds": round(age),
                    "message": "Live provider unavailable; displaying the last successful live-weather fetch."
                }
                return stale
                
            self._cache["data"] = live_payload
            self._cache["last_update"] = now
            return live_payload

satellite_engine = LiveTelemetryEngine()
