import os
import json
import hashlib
from pathlib import Path
import requests
from datetime import datetime

# Project paths
PROJECT_ROOT = Path("c:/Users/gokul/Desktop/PROJECTS/climatetwin")
METEO_DIR = PROJECT_ROOT / "data" / "raw" / "forecast" / "open_meteo"

# Chennai Coordinates
LAT = 13.0827
LON = 80.2707

def calculate_sha256(filepath):
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def process_open_meteo():
    print("Starting Open-Meteo data acquisition...")
    os.makedirs(METEO_DIR, exist_ok=True)
    
    # 1. Historical Data
    # 2015-01-01 to yesterday
    end_date = datetime.utcnow().strftime("%Y-%m-%d")
    hist_url = (f"https://archive-api.open-meteo.com/v1/archive?latitude={LAT}&longitude={LON}"
                f"&start_date=2015-01-01&end_date={end_date}"
                f"&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m,wind_direction_10m,surface_pressure,precipitation")
    
    hist_file = METEO_DIR / "historical_2015_present.json"
    
    print("Downloading historical weather data (2015-present)...")
    try:
        response = requests.get(hist_url)
        response.raise_for_status()
        with open(hist_file, "w") as f:
            json.dump(response.json(), f)
        print(f"Historical data saved to {hist_file.name}")
        print(f"SHA-256: {calculate_sha256(hist_file)}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch historical data: {e}")

    # 2. Forecast Data
    forecast_url = (f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}"
                    f"&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m,wind_direction_10m,surface_pressure,precipitation")
    
    forecast_file = METEO_DIR / "forecast_latest.json"
    
    print("\nDownloading latest 7-day forecast data...")
    try:
        response = requests.get(forecast_url)
        response.raise_for_status()
        with open(forecast_file, "w") as f:
            json.dump(response.json(), f)
        print(f"Forecast data saved to {forecast_file.name}")
        print(f"SHA-256: {calculate_sha256(forecast_file)}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch forecast data: {e}")

    print("Open-Meteo acquisition complete!")

if __name__ == "__main__":
    process_open_meteo()
