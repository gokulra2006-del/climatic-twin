"""
Fetches genuine historical weather and Copernicus soil moisture reanalysis
directly from Open-Meteo's ERA5 Archive API for Chennai (13.0827 N, 80.2707 E).
"""

import os
import requests
import pandas as pd

def fetch_chennai_historical(output_dir="data"):
    os.makedirs(output_dir, exist_ok=True)
    out_file = os.path.join(output_dir, "chennai_openmeteo_historical_2015_2024.csv")
    
    print("=" * 60)
    print("OPEN-METEO ARCHIVE: FETCHING CHENNAI 2015-2024 HISTORICAL DATA")
    print("=" * 60)
    
    url = (
        "https://archive-api.open-meteo.com/v1/archive?"
        "latitude=13.0827&longitude=80.2707"
        "&start_date=2015-01-01&end_date=2024-12-31"
        "&hourly=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,rain,surface_pressure,wind_speed_10m,soil_moisture_0_to_7cm,soil_moisture_28_to_100cm"
        "&timezone=Asia%2FKolkata"
    )
    
    print("Connecting to Open-Meteo ERA5 Reanalysis endpoint...")
    try:
        res = requests.get(url, timeout=90)
        res.raise_for_status()
        data = res.json()
        
        if "hourly" in data:
            df = pd.DataFrame(data["hourly"])
            df.to_csv(out_file, index=False)
            print(f"[SUCCESS] Downloaded {len(df)} authentic hourly records!")
            print(f"Saved to: {out_file}")
            print(f"Date range: {df['time'].iloc[0]} to {df['time'].iloc[-1]}")
        else:
            print("API response error:", data)
    except Exception as e:
        print(f"[ERROR] Failed to fetch historical data: {e}")

if __name__ == "__main__":
    fetch_chennai_historical()
