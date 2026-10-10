import os
from pathlib import Path
import hashlib
from dotenv import load_dotenv
import earthaccess

# Load credentials from .env
load_dotenv()

# Project paths
PROJECT_ROOT = Path("c:/Users/gokul/Desktop/PROJECTS/climatetwin")
IMERG_DIR = PROJECT_ROOT / "data" / "raw" / "rainfall" / "imerg_v07"

# Bounding Box (min_lon, min_lat, max_lon, max_lat)
BBOX = (79.5, 12.5, 80.5, 13.5)

# Required event windows
EVENTS = {
    "Event_1": ("2015-11-01", "2015-12-10"),
    "Event_2": ("2021-11-01", "2021-11-15"),
    "Event_3": ("2023-11-28", "2023-12-10"),
    "Event_4": ("2024-11-25", "2024-12-05")
}

def calculate_sha256(filepath):
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def process_imerg():
    os.makedirs(IMERG_DIR, exist_ok=True)
    
    # Authenticate using EARTHDATA_USERNAME and EARTHDATA_PASSWORD from .env
    print("Authenticating with NASA Earthdata...")
    try:
        earthaccess.login(strategy="environment", persist=True)
        print("Authentication successful!")
    except Exception as e:
        print(f"Authentication failed: {e}")
        return

    # Loop through events
    for event_name, (start_date, end_date) in EVENTS.items():
        print(f"\nSearching data for {event_name} ({start_date} to {end_date})...")
        
        results = earthaccess.search_data(
            short_name='GPM_3IMERGHH',
            version='07',
            temporal=(start_date, end_date),
            bounding_box=BBOX
        )
        
        if not results:
            print(f"No results found for {event_name}.")
            continue
            
        print(f"Found {len(results)} granules for {event_name}. Starting download...")
        
        # Download files
        # earthaccess handles skipping existing files automatically if we use it, 
        # but let's be explicit and download them.
        downloaded_files = earthaccess.download(
            results,
            local_path=str(IMERG_DIR)
        )
        
        print(f"Successfully downloaded {len(downloaded_files)} files for {event_name}.")

if __name__ == "__main__":
    process_imerg()
