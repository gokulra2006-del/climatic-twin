import os
import hashlib
from pathlib import Path
from dotenv import load_dotenv

# Load env variables from .env (for Kaggle auth)
load_dotenv()

# Project paths
PROJECT_ROOT = Path("c:/Users/gokul/Desktop/PROJECTS/climatetwin")
CMWSSB_DIR = PROJECT_ROOT / "data" / "raw" / "water_level" / "cmwssb"
FILENAME = "chennai_reservoir_levels.csv"

def calculate_sha256(filepath):
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def process_cmwssb():
    print("Starting CMWSSB Reservoir Data acquisition...")
    os.makedirs(CMWSSB_DIR, exist_ok=True)
    filepath = CMWSSB_DIR / FILENAME
    
    if filepath.exists():
        print(f"File {FILENAME} already exists. Skipping download.")
        checksum = calculate_sha256(filepath)
        print(f"SHA-256: {checksum}")
        return

    print("Downloading CMWSSB data using Kaggle API...")
    
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
        api = KaggleApi()
        api.authenticate()
        
        print("Authenticated with Kaggle. Downloading dataset...")
        api.dataset_download_files('sudalairajkumar/chennai-water-management', path=str(CMWSSB_DIR), unzip=True)
        
        if filepath.exists():
            print(f"Successfully downloaded {FILENAME}.")
            checksum = calculate_sha256(filepath)
            print(f"SHA-256: {checksum}")
        else:
            print("Download succeeded, but expected file was not found.")
            
    except Exception as e:
        print(f"Failed to download CMWSSB data via Kaggle: {e}")
        print("\nPlease ensure KAGGLE_USERNAME and KAGGLE_KEY are correctly set in your .env file.")

if __name__ == "__main__":
    process_cmwssb()
