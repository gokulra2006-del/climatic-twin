import os
import hashlib
from pathlib import Path
import urllib.request
import json
import csv

# Project paths
PROJECT_ROOT = Path("c:/Users/gokul/Desktop/PROJECTS/climatetwin")
IFI_DIR = PROJECT_ROOT / "data" / "raw" / "flood_events" / "ifi_impacts"
ZENODO_RECORD_ID = "11275211"

def calculate_sha256(filepath):
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def process_ifi():
    print("Starting IFI Flood Impact Data acquisition...")
    os.makedirs(IFI_DIR, exist_ok=True)
    
    files_to_download = {
        "India_Flood_Inventory_v3.csv": f"https://zenodo.org/api/records/{ZENODO_RECORD_ID}/files/India_Flood_Inventory_v3.csv/content",
        "District_FloodImpact.csv": f"https://zenodo.org/api/records/{ZENODO_RECORD_ID}/files/District_FloodImpact.csv/content",
        "District_FloodedArea.csv": f"https://zenodo.org/api/records/{ZENODO_RECORD_ID}/files/District_FloodedArea.csv/content"
    }
    
    downloaded_files = []

    for filename, download_url in files_to_download.items():
        filepath = IFI_DIR / filename
        
        if filepath.exists() and filepath.stat().st_size > 0:
            print(f"File {filename} already exists and is non-empty. Skipping download.")
            downloaded_files.append(filepath)
            continue
            
        print(f"Downloading {filename} from {download_url}...")
        try:
            import subprocess
            result = subprocess.run(["curl", "-s", "-L", "-o", str(filepath), download_url])
            if result.returncode == 0 and filepath.stat().st_size > 0:
                print(f"Successfully downloaded {filename}.")
                downloaded_files.append(filepath)
            else:
                print(f"Warning: Download failed or file {filename} is empty.")
                if filepath.exists():
                    filepath.unlink()
        except Exception as e:
            print(f"Failed to download {filename}: {e}")
                
    print("\nIFI Data acquisition complete!")
    
    # Validation summary
    total_size = sum(f.stat().st_size for f in downloaded_files)
    print(f"\nValidation Summary:")
    print(f"Total files: {len(downloaded_files)}")
    print(f"Total size: {total_size / (1024*1024):.2f} MB")
    
    # Quick record count validation
    main_csv = IFI_DIR / "India_Flood_Inventory_v3.csv"
    if main_csv.exists():
        try:
            with open(main_csv, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader)
                row_count = sum(1 for row in reader)
            print(f"Records in India_Flood_Inventory_v3.csv: {row_count}")
        except Exception as e:
            print(f"Could not count records: {e}")

if __name__ == "__main__":
    process_ifi()
