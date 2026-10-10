import os
import hashlib
from pathlib import Path
import requests

# Project paths
PROJECT_ROOT = Path("c:/Users/gokul/Desktop/PROJECTS/climatetwin")
OSM_DIR = PROJECT_ROOT / "data" / "raw" / "geospatial" / "osm"
OSM_URL = "https://download.geofabrik.de/asia/india/southern-zone-latest.osm.pbf"
FILENAME = "southern-zone-latest.osm.pbf"

def calculate_sha256(filepath):
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def process_osm():
    print("Starting OpenStreetMap acquisition...")
    os.makedirs(OSM_DIR, exist_ok=True)
    filepath = OSM_DIR / FILENAME
    
    print("Downloading Southern Zone India PBF from Geofabrik...")
    try:
        import subprocess
        # Server does not support byte ranges, must download from scratch
        result = subprocess.run(["curl", "-L", "-o", str(filepath), OSM_URL])
        if result.returncode == 0:
            print(f"Successfully downloaded {FILENAME}.")
            checksum = calculate_sha256(filepath)
            print(f"SHA-256: {checksum}")
        else:
            print(f"Failed to download OSM data (curl exit code {result.returncode}).")
            if filepath.exists() and filepath.stat().st_size == 0:
                filepath.unlink()
    except Exception as e:
        print(f"Failed to download OSM data: {e}")

if __name__ == "__main__":
    process_osm()
