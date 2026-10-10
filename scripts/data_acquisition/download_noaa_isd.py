import os
import hashlib
from pathlib import Path
import requests
from datetime import datetime

# Project paths
PROJECT_ROOT = Path("c:/Users/gokul/Desktop/PROJECTS/climatetwin")
NOAA_DIR = PROJECT_ROOT / "data" / "raw" / "weather" / "noaa_isd"

# Station Identity
STATION_ID = "43279099999"

def calculate_sha256(filepath):
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def process_noaa():
    print(f"Starting NOAA ISD Data acquisition for station {STATION_ID}...")
    os.makedirs(NOAA_DIR, exist_ok=True)
    
    current_year = datetime.utcnow().year
    years = list(range(2015, current_year + 1))
    
    for year in years:
        filename = f"{STATION_ID}_{year}.csv"
        filepath = NOAA_DIR / filename
        
        # NOAA NCEI global-hourly URL pattern
        url = f"https://www.ncei.noaa.gov/data/global-hourly/access/{year}/{STATION_ID}.csv"
        
        if filepath.exists():
            if filepath.stat().st_size > 0:
                print(f"File {filename} already exists and is non-empty. Skipping download.")
                continue
            else:
                print(f"File {filename} exists but is empty. Re-downloading...")
        
        print(f"Downloading data for year {year} from {url}...")
        try:
            import subprocess
            result = subprocess.run(["curl", "-s", "-f", "-o", str(filepath), url])
            if result.returncode != 0:
                print(f"Failed to download year {year} (curl exit code {result.returncode}).")
                if filepath.exists():
                    filepath.unlink()
                continue
            
            if filepath.exists() and filepath.stat().st_size == 0:
                print(f"Warning: Downloaded file {filename} is empty.")
                filepath.unlink() # delete empty file
            else:
                print(f"Successfully downloaded {filename}.")
            
        except Exception as e:
            print(f"Failed to download year {year}: {e}")

    print("NOAA ISD acquisition complete!")
    
    # Validation summary
    files = list(NOAA_DIR.glob("*.csv"))
    total_size = sum(f.stat().st_size for f in files)
    print(f"\nValidation Summary:")
    print(f"Total files: {len(files)}")
    print(f"Total size: {total_size / (1024*1024):.2f} MB")

if __name__ == "__main__":
    process_noaa()
