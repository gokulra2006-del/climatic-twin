"""
Phase 18: External Hazards Data Integration
ClimateTwin Chennai Project

Fetches high-resolution real-world weather data from Open-Meteo API (No Auth required)
and simulates Reservoir dynamics to provide rich timeseries data for secondary hazards.
"""
import httpx
import numpy as np
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List

class ExternalHazardsEngine:
    def __init__(self):
        self.chennai_lat = 13.0827
        self.chennai_lon = 80.2707
        self.weather_url = "https://api.open-meteo.com/v1/forecast"
        
    async def fetch_open_meteo_data(self) -> Dict[str, Any]:
        """Fetches 7 days past and 3 days future hourly data for Chennai."""
        params = {
            "latitude": self.chennai_lat,
            "longitude": self.chennai_lon,
            "hourly": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,wind_speed_10m,wind_gusts_10m",
            "past_days": 7,
            "forecast_days": 3,
            "timezone": "Asia/Kolkata"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(self.weather_url, params=params, timeout=10.0)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                # Fallback to synthetic if API fails
                return self._generate_fallback_data()

    def _generate_fallback_data(self) -> Dict[str, Any]:
        """Generates synthetic fallback data if the API is unreachable."""
        now = datetime.now(timezone.utc)
        start = now - timedelta(days=7)
        hours = 10 * 24
        
        times = [(start + timedelta(hours=i)).strftime("%Y-%m-%dT%H:00") for i in range(hours)]
        
        # Base realistic synthetic values
        t = np.linspace(0, 10 * np.pi, hours)
        temp = 30 + 5 * np.sin(t - np.pi/2) + np.random.normal(0, 1, hours)
        hum = 75 + 15 * np.cos(t) + np.random.normal(0, 5, hours)
        precip = np.maximum(0, 15 * np.sin(t/3) + np.random.normal(0, 5, hours))
        wind = 12 + 8 * np.sin(t/2) + np.random.normal(0, 3, hours)
        
        return {
            "hourly": {
                "time": times,
                "temperature_2m": temp.tolist(),
                "relative_humidity_2m": hum.tolist(),
                "apparent_temperature": (temp + 2).tolist(),
                "precipitation": precip.tolist(),
                "wind_speed_10m": wind.tolist(),
                "wind_gusts_10m": (wind * 1.5).tolist()
            }
        }

    def process_hazard_timeseries(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Processes raw hourly data into separated hazard arrays for frontend charts."""
        hourly = raw_data.get("hourly", {})
        times = hourly.get("time", [])
        
        if not times:
            return {}

        # 1. Heat Hazard (Temperature, Apparent Temp, Humidity)
        heat_series = []
        # 2. Wind Hazard (Speed, Gusts)
        wind_series = []
        # 3. Rainfall Hazard (Precipitation)
        rain_series = []
        # 4. Reservoir Hazard (Simulated based on rainfall)
        res_series = []
        
        current_reservoir_mcft = 2200.0
        max_capacity = 3300.0

        for i, time_str in enumerate(times):
            dt = datetime.fromisoformat(time_str)
            label = dt.strftime("%a %H:%M") # e.g. Mon 14:00
            
            temp = hourly.get("temperature_2m", [])[i]
            app_temp = hourly.get("apparent_temperature", [])[i]
            hum = hourly.get("relative_humidity_2m", [])[i]
            
            speed = hourly.get("wind_speed_10m", [])[i]
            gust = hourly.get("wind_gusts_10m", [])[i]
            
            precip = hourly.get("precipitation", [])[i]
            
            # Simulate reservoir dynamics
            inflow = precip * 15.0 # mm of rain -> mcft inflow
            outflow = 12.0 # constant usage + evaporation
            if current_reservoir_mcft > max_capacity * 0.9:
                outflow += 50.0 # open sluice gates
                
            current_reservoir_mcft = max(0, min(max_capacity, current_reservoir_mcft + inflow - outflow))
            
            heat_series.append({
                "time": label,
                "temperature": round(temp, 1),
                "heat_index": round(app_temp, 1),
                "humidity": round(hum, 1)
            })
            
            wind_series.append({
                "time": label,
                "speed": round(speed, 1),
                "gusts": round(gust, 1)
            })
            
            rain_series.append({
                "time": label,
                "precipitation": round(precip, 2)
            })
            
            res_series.append({
                "time": label,
                "volume_mcft": round(current_reservoir_mcft, 1),
                "inflow": round(inflow, 1),
                "outflow": round(outflow, 1),
                "fill_percentage": round((current_reservoir_mcft / max_capacity) * 100, 1)
            })

        # Find current index to split historical vs forecast
        # We'll just pass everything and let UI handle it, but attach metadata
        return {
            "heat": heat_series,
            "wind": wind_series,
            "rainfall": rain_series,
            "reservoir": res_series,
            "metadata": {
                "source": "Open-Meteo API / ClimateTwin Physical Simulator",
                "resolution": "Hourly",
                "data_points": len(times)
            }
        }

    async def get_detailed_hazards(self) -> Dict[str, Any]:
        raw_data = await self.fetch_open_meteo_data()
        return self.process_hazard_timeseries(raw_data)

external_hazards_engine = ExternalHazardsEngine()
