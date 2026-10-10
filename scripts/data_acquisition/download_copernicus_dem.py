import os
import hashlib
from pathlib import Path
import requests
from datetime import datetime

# Project paths
PROJECT_ROOT = Path("c:/Users/gokul/Desktop/PROJECTS/climatetwin")
DEM_DIR = PROJECT_ROOT / "data" / "raw" / "geospatial" / "copernicus_dem"

# Copernicus DEM GLO-30 AWS S3 Public Registry URLs
# Bounding Box: min_lon = 79.5, max_lon = 80.5, min_lat = 12.5, max_lat = 13.5
# Requires tiles: N12E079, N12E080, N13E079, N13E080
TILES = {
    "N12E079": "https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_N12_00_E079_00_DEM/Copernicus_DSM_COG_10_N12_00_E079_00_DEM.tif",
    "N12E080": "https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_N12_00_E080_00_DEM/Copernicus_DSM_COG_10_N12_00_E080_00_DEM.tif",
    "N13E079": "https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_N13_00_E079_00_DEM/Copernicus_DSM_COG_10_N13_00_E079_00_DEM.tif",
    "N13E080": "https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_N13_00_E080_00_DEM/Copernicus_DSM_COG_10_N13_00_E080_00_DEM.tif"
}

def calculate_sha256(filepath):
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def process_dem():
    print("Starting Copernicus DEM GLO-30 acquisition...")
    os.makedirs(DEM_DIR, exist_ok=True)
    
    for tile_name, url in TILES.items():
        filename = url.split('/')[-1]
        filepath = DEM_DIR / filename
        
        if filepath.exists():
            print(f"File {filename} already exists. Skipping download.")
            checksum = calculate_sha256(filepath)
            print(f"SHA-256: {checksum}")
            continue
            
        print(f"Downloading {tile_name} from AWS Open Data...")
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            with open(filepath, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            print(f"Successfully downloaded {filename}.")
            checksum = calculate_sha256(filepath)
            print(f"SHA-256: {checksum}")
            
        except requests.exceptions.RequestException as e:
            print(f"Failed to download {tile_name}: {e}")

    print("Copernicus DEM acquisition complete!")

if __name__ == "__main__":
    process_dem()
