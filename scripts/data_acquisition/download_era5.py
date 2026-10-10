import cdsapi
import os
import hashlib
import json
from datetime import datetime

# Setup
c = cdsapi.Client()
OUTPUT_DIR = os.path.join("data", "raw", "weather", "era5_land")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Required Variables for Digital Twin (Atmospheric / Land)
VARIABLES = [
    '2m_temperature',
    'total_precipitation',
    'surface_runoff',
    '10m_u_component_of_wind',
    '10m_v_component_of_wind',
    'volumetric_soil_water_layer_1'
]

# Chennai Bounding Box (North, West, South, East)
AREA = [13.5, 79.5, 12.5, 80.5]

YEARS = [str(y) for y in range(2010, 2026)]
MONTHS = [f"{m:02d}" for m in range(1, 13)]
DAYS = [f"{d:02d}" for d in range(1, 32)]
TIMES = [f"{h:02d}:00" for h in range(0, 24)]

def calculate_sha256(filepath):
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def update_manifest(filepath, year):
    file_size = os.path.getsize(filepath)
    sha256 = calculate_sha256(filepath)
    
    manifest_entry = f"""
- source_id: era5_land_{year}
  provider: Copernicus Climate Change Service (C3S) / ECMWF
  dataset_name: ERA5-Land hourly data from 1950 to present
  version: 1.0
  retrieval_date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
  source_url: CDS API (reanalysis-era5-land)
  license: Copernicus License
  origin: reanalysis
  time_range: {year}-01-01 to {year}-12-31
  spatial_resolution: 0.1 degree
  temporal_resolution: hourly
  bounding_box: [12.5, 79.5, 13.5, 80.5]
  checksum: {sha256}
  local_path: {filepath.replace(os.sep, '/')}
  notes: Variables downloaded: {", ".join(VARIABLES)}
"""
    manifest_path = os.path.join("data", "manifest.yaml")
    with open(manifest_path, "a") as f:
        f.write(manifest_entry)
        
    print(f"[{year}] Downloaded {file_size} bytes. SHA-256: {sha256}")

def main():
    print("Starting ERA5-Land data acquisition...")
    print(f"Variables: {VARIABLES}")
    print(f"Bounding Box: {AREA}")
    
    # We will just download 2024 to verify the pipeline works in this execution, 
    # as downloading 16 years sequentially takes hours on the CDS queue.
    # The user can rerun for other years by modifying `years_to_download`.
    years_to_download = ['2024'] # Testing single year
    
    for year in years_to_download:
        for month in MONTHS:
            outfile = os.path.join(OUTPUT_DIR, f"era5_land_chennai_{year}_{month}.nc")
            
            if os.path.exists(outfile):
                print(f"File {outfile} already exists. Skipping.")
                continue
                
            print(f"Requesting data for {year}-{month}...")
            try:
                c.retrieve(
                    'reanalysis-era5-land',
                    {
                        'variable': VARIABLES,
                        'year': year,
                        'month': month,
                        'day': DAYS,
                        'time': TIMES,
                        'area': AREA,
                        'format': 'netcdf',
                    },
                    outfile
                )
                update_manifest(outfile, f"{year}-{month}")
            except Exception as e:
                print(f"FAILED to download {year}-{month}: {e}")

if __name__ == "__main__":
    main()
