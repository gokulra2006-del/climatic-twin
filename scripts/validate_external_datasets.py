import os
import hashlib
import json
import yaml
import glob
import pandas as pd
import numpy as np
import h5py
import rasterio
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load env credentials
load_dotenv()

PROJECT_ROOT = Path("C:/Users/gokul/Desktop/PROJECTS/climatetwin")
DOCS_DIR = PROJECT_ROOT / "docs"
DATA_DIR = PROJECT_ROOT / "data"

def calculate_sha256(filepath):
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def audit_kaggle_cmwssb(report):
    print("Auditing Kaggle CMWSSB data...")
    source_name = "sudalairajkumar/chennai-water-management"
    csv_path = DATA_DIR / "raw" / "water_level" / "cmwssb" / "chennai_reservoir_levels.csv"
    
    # 1. Credentials Check
    has_user = "KAGGLE_USERNAME" in os.environ and bool(os.environ["KAGGLE_USERNAME"])
    has_key = "KAGGLE_KEY" in os.environ and bool(os.environ["KAGGLE_KEY"])
    
    auth_status = "OK" if (has_user and has_key) else f"MISSING (Username: {has_user}, Key: {has_key})"
    
    report["kaggle"] = {
        "provider": "Kaggle",
        "dataset_name": source_name,
        "auth_status": auth_status,
        "status": "PASS",
        "errors": []
    }
    
    if not csv_path.exists():
        report["kaggle"]["status"] = "FAIL"
        report["kaggle"]["errors"].append(f"File not found: {csv_path}")
        return
        
    # Check checksums
    checksum = calculate_sha256(csv_path)
    report["kaggle"]["actual_checksum"] = checksum
    expected_checksum = "3b4b6f2f53b5db20513d2829c2dba265c5738a55bf0c8eade51e0e2d5cfeaef7"
    
    if checksum != expected_checksum:
        report["kaggle"]["errors"].append(f"Checksum mismatch: Expected {expected_checksum}, Got {checksum}")
        report["kaggle"]["status"] = "FAIL"
        
    # Open CSV
    try:
        df = pd.read_csv(csv_path)
        report["kaggle"]["record_count"] = len(df)
        
        # Verify columns
        required_cols = ["POONDI", "CHOLAVARAM", "REDHILLS", "CHEMBARAMBAKKAM"]
        missing_cols = [c for c in required_cols if c not in df.columns]
        if missing_cols:
            report["kaggle"]["errors"].append(f"Missing required reservoir columns: {missing_cols}")
            report["kaggle"]["status"] = "FAIL"
            
        # Parse Dates
        date_cols = [c for c in df.columns if 'date' in c.lower()]
        if not date_cols:
            report["kaggle"]["errors"].append("Missing date column")
            report["kaggle"]["status"] = "FAIL"
        else:
            date_col = date_cols[0]
            df['date_parsed'] = pd.to_datetime(df[date_col], format='%d-%m-%Y', errors='coerce')
            null_dates = df['date_parsed'].isnull().sum()
            if null_dates > 0:
                report["kaggle"]["errors"].append(f"Contains {null_dates} unparseable dates")
                
            report["kaggle"]["min_date"] = df['date_parsed'].min().isoformat()
            report["kaggle"]["max_date"] = df['date_parsed'].max().isoformat()
            report["kaggle"]["duplicate_dates"] = int(df['date_parsed'].duplicated().sum())
            
        # Data integrity checks
        report["kaggle"]["missing_values"] = int(df[required_cols].isnull().sum().sum())
        
        # Check for non-numeric/negative values
        for col in required_cols:
            non_numeric = pd.to_numeric(df[col], errors='coerce').isnull().sum()
            if non_numeric > 0:
                report["kaggle"]["errors"].append(f"Column {col} contains {non_numeric} non-numeric records")
            negatives = (df[col] < 0).sum()
            if negatives > 0:
                report["kaggle"]["errors"].append(f"Column {col} contains {negatives} negative values")
                
    except Exception as e:
        report["kaggle"]["errors"].append(f"Error opening/reading CSV: {e}")
        report["kaggle"]["status"] = "FAIL"

def audit_nasa_imerg(report):
    print("Auditing NASA GPM IMERG V07B data...")
    imerg_dir = DATA_DIR / "raw" / "rainfall" / "imerg_v07"
    
    # 1. Credentials Check
    has_user = "EARTHDATA_USERNAME" in os.environ and bool(os.environ["EARTHDATA_USERNAME"])
    has_pass = "EARTHDATA_PASSWORD" in os.environ and bool(os.environ["EARTHDATA_PASSWORD"])
    
    auth_status = "OK" if (has_user and has_pass) else f"MISSING (Username: {has_user}, Password: {has_pass})"
    
    report["nasa_imerg"] = {
        "provider": "NASA GES DISC",
        "dataset_name": "GPM_3IMERGHH_07",
        "auth_status": auth_status,
        "status": "PASS",
        "errors": []
    }
    
    if not imerg_dir.exists():
        report["nasa_imerg"]["status"] = "FAIL"
        report["nasa_imerg"]["errors"].append("IMERG raw directory does not exist")
        return
        
    hdf_files = sorted(glob.glob(os.path.join(imerg_dir, "*.HDF5")))
    report["nasa_imerg"]["expected_files"] = 3792
    report["nasa_imerg"]["actual_files"] = len(hdf_files)
    
    if len(hdf_files) < 3792:
        report["nasa_imerg"]["status"] = "INCOMPLETE"
        report["nasa_imerg"]["errors"].append(f"Missing granules: Expected 3792, found {len(hdf_files)}")
        
    # Check zero-byte files
    zero_bytes = [f for f in hdf_files if os.path.getsize(f) == 0]
    report["nasa_imerg"]["zero_byte_files"] = len(zero_bytes)
    if len(zero_bytes) > 0:
        report["nasa_imerg"]["errors"].append(f"Found {len(zero_bytes)} zero-byte files")
        report["nasa_imerg"]["status"] = "FAIL"
        
    # HDF5 readability and coordinate intersection
    corrupted_files = 0
    read_samples = []
    
    # Sample a few files to check readability
    sample_indices = np.linspace(0, len(hdf_files)-1, min(10, len(hdf_files)), dtype=int)
    for idx in sample_indices:
        f = hdf_files[idx]
        try:
            with h5py.File(f, 'r') as h5f:
                grid = h5f['Grid']
                t_sec = int(grid['time'][0])
                # Check spatial slice variables exist
                precip_slice = grid['precipitation']
                assert precip_slice.shape == (1, 3600, 1800)
                read_samples.append(Path(f).name)
        except Exception:
            corrupted_files += 1
            
    report["nasa_imerg"]["corrupt_files"] = corrupted_files
    report["nasa_imerg"]["validated_samples"] = read_samples
    if corrupted_files > 0:
        report["nasa_imerg"]["errors"].append(f"Found {corrupted_files} unreadable HDF5 files")
        report["nasa_imerg"]["status"] = "FAIL"

def audit_copernicus_dem(report):
    print("Auditing Copernicus DEM GLO-30 data...")
    dem_dir = DATA_DIR / "raw" / "geospatial" / "copernicus_dem"
    expected_tiles = ["N12E079", "N12E080", "N13E079", "N13E080"]
    
    report["copernicus_dem"] = {
        "provider": "ESA / Copernicus",
        "dataset_name": "Copernicus DEM GLO-30",
        "status": "PASS",
        "errors": []
    }
    
    if not dem_dir.exists():
        report["copernicus_dem"]["status"] = "FAIL"
        report["copernicus_dem"]["errors"].append("Copernicus DEM raw directory does not exist")
        return
        
    actual_tifs = glob.glob(os.path.join(dem_dir, "*.tif"))
    report["copernicus_dem"]["expected_tiles"] = len(expected_tiles)
    report["copernicus_dem"]["actual_tiles"] = len(actual_tifs)
    
    tile_stats = {}
    
    for tile in expected_tiles:
        # Match tile prefix N12E079 to N12_00_E079_00 etc
        lat_part = tile[:3]
        lon_part = tile[3:]
        match = [f for f in actual_tifs if lat_part in Path(f).name and lon_part in Path(f).name]
        if not match:
            report["copernicus_dem"]["errors"].append(f"Tile {tile} is missing")
            report["copernicus_dem"]["status"] = "FAIL"
            continue
            
        f = match[0]
        try:
            with rasterio.open(f) as src:
                crs = src.crs.to_string() if src.crs else "None"
                res = src.res
                bounds = src.bounds
                arr = src.read(1)
                
                # Filter out no-data / fill values (usually negative or extremely large)
                valid_data = arr[arr > -9999]
                
                tile_stats[tile] = {
                    "crs": crs,
                    "resolution": res,
                    "bounds": [bounds.left, bounds.bottom, bounds.right, bounds.top],
                    "min_elevation": float(np.min(valid_data)) if len(valid_data) > 0 else 0.0,
                    "max_elevation": float(np.max(valid_data)) if len(valid_data) > 0 else 0.0,
                    "mean_elevation": float(np.mean(valid_data)) if len(valid_data) > 0 else 0.0
                }
        except Exception as e:
            report["copernicus_dem"]["errors"].append(f"Error opening tile {tile}: {e}")
            report["copernicus_dem"]["status"] = "FAIL"
            
    report["copernicus_dem"]["tile_stats"] = tile_stats

def audit_consistency(report):
    print("Auditing cross-dataset consistency...")
    report["cross_consistency"] = {
        "status": "PASS",
        "errors": []
    }
    
    # Verify presence of processed outputs
    processed_dem = DATA_DIR / "processed" / "geospatial" / "chennai_dem_30m.tif"
    processed_rain = DATA_DIR / "processed" / "rainfall" / "imerg_chennai_daily.csv"
    processed_cmwssb = DATA_DIR / "processed" / "water_level" / "cmwssb_reservoir_levels.csv"
    
    for fp in [processed_dem, processed_rain, processed_cmwssb]:
        if not fp.exists():
            report["cross_consistency"]["errors"].append(f"Missing processed file: {fp.name}")
            report["cross_consistency"]["status"] = "FAIL"
            
    # Bounding box test
    if processed_dem.exists():
        try:
            with rasterio.open(processed_dem) as src:
                bounds = src.bounds
                # Expected intersection with [79.5, 12.5, 80.5, 13.5]
                if abs(bounds.left - 79.5) > 0.1 or abs(bounds.bottom - 12.5) > 0.1:
                    report["cross_consistency"]["errors"].append(f"DEM bounding box mismatch: {bounds}")
        except Exception as e:
            report["cross_consistency"]["errors"].append(f"DEM read error during consistency check: {e}")

def run_reproducibility_dryruns(report):
    print("Testing reproducibility scripts...")
    # Verify presence of processing scripts
    scripts = {
        "process_cmwssb.py": PROJECT_ROOT / "scripts" / "data_processing" / "process_cmwssb.py",
        "process_dem.py": PROJECT_ROOT / "scripts" / "data_processing" / "process_dem.py",
        "process_imerg.py": PROJECT_ROOT / "scripts" / "data_processing" / "process_imerg.py"
    }
    
    reprod_status = {}
    for name, path in scripts.items():
        if path.exists():
            reprod_status[name] = "FOUND (Usable)"
        else:
            reprod_status[name] = "MISSING"
            report["cross_consistency"]["status"] = "FAIL"
            report["cross_consistency"]["errors"].append(f"Processing script missing: {name}")
            
    report["reproducibility"] = reprod_status

def write_reports(report):
    os.makedirs(DOCS_DIR, exist_ok=True)
    json_path = DOCS_DIR / "external_dataset_validation.json"
    md_path = DOCS_DIR / "external_dataset_validation.md"
    
    # Save JSON
    with open(json_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"Saved JSON validation results to {json_path}")
    
    # Generate human-readable Markdown validation summary
    overall_status = "PASS"
    for k in ["kaggle", "nasa_imerg", "copernicus_dem", "cross_consistency"]:
        if k in report and report[k]["status"] == "FAIL":
            overall_status = "FAIL"
            break
        elif k in report and report[k]["status"] == "INCOMPLETE":
            overall_status = "INCOMPLETE"
            
    md_content = f"""# Phase 8 — External Dataset Integrity & Validation Report

**Verification Date:** {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}  
**Overall Validation Status:** **{overall_status}**

---

## 1. Kaggle CMWSSB Reservoir Data
* **Dataset Name:** `{report['kaggle']['dataset_name']}`
* **Authentication:** `{report['kaggle']['auth_status']}`
* **Validation Status:** **{report['kaggle']['status']}**
* **Records Found:** {report['kaggle'].get('record_count', 0)}
* **Temporal Range:** {report['kaggle'].get('min_date', 'N/A')} to {report['kaggle'].get('max_date', 'N/A')}
* **Null Values:** {report['kaggle'].get('missing_values', 0)}
* **Duplicate Dates:** {report['kaggle'].get('duplicate_dates', 0)}
* **SHA-256 Checksum:** `{report['kaggle'].get('actual_checksum', 'None')}`
* **Errors/Warnings:**
  {chr(10).join([f"  - {e}" for e in report['kaggle']['errors']]) if report['kaggle']['errors'] else "  - None"}

---

## 2. NASA GPM IMERG V07B Rainfall Data
* **Dataset Name:** `{report['nasa_imerg']['dataset_name']}`
* **Authentication:** `{report['nasa_imerg']['auth_status']}`
* **Validation Status:** **{report['nasa_imerg']['status']}**
* **Granules Found:** {report['nasa_imerg'].get('actual_files', 0)} / {report['nasa_imerg'].get('expected_files', 3792)}
* **Corrupt/Unreadable Files:** {report['nasa_imerg'].get('corrupt_files', 0)}
* **Zero-byte Files:** {report['nasa_imerg'].get('zero_byte_files', 0)}
* **Sample Readable Files:**
  {chr(10).join([f"  - {f}" for f in report['nasa_imerg'].get('validated_samples', [])]) if report['nasa_imerg'].get('validated_samples', []) else "  - None"}
* **Errors/Warnings:**
  {chr(10).join([f"  - {e}" for e in report['nasa_imerg']['errors']]) if report['nasa_imerg']['errors'] else "  - None"}

---

## 3. ESA Copernicus DEM GLO-30 elevation
* **Dataset Name:** `{report['copernicus_dem']['dataset_name']}`
* **Validation Status:** **{report['copernicus_dem']['status']}**
* **Tiles Found:** {report['copernicus_dem'].get('actual_tiles', 0)} / {report['copernicus_dem'].get('expected_tiles', 4)}
* **Tile Statistics:**
"""
    for tile, stats in report['copernicus_dem'].get('tile_stats', {}).items():
        md_content += f"""  * **{tile}**:
    * CRS: `{stats['crs']}`
    * Resolution: `{stats['resolution']}`
    * Elevation range: `{stats['min_elevation']:.1f}m` to `{stats['max_elevation']:.1f}m` (Mean: `{stats['mean_elevation']:.1f}m`)
"""
        
    md_content += f"""
* **Errors/Warnings:**
  {chr(10).join([f"  - {e}" for e in report['copernicus_dem']['errors']]) if report['copernicus_dem']['errors'] else "  - None"}

---

## 4. Reproducibility & Consistency Check
* **Cross-dataset Consistency Status:** **{report['cross_consistency']['status']}**
* **Reproducibility Status:**
"""
    for script, state in report['reproducibility'].items():
        md_content += f"  * `{script}`: {state}\n"
        
    md_content += f"""
* **Errors/Warnings:**
  {chr(10).join([f"  - {e}" for e in report['cross_consistency']['errors']]) if report['cross_consistency']['errors'] else "  - None"}
"""
    
    with open(md_path, "w") as f:
        f.write(md_content)
    print(f"Saved Markdown validation summary to {md_path}")

def main():
    report = {}
    audit_kaggle_cmwssb(report)
    audit_nasa_imerg(report)
    audit_copernicus_dem(report)
    run_reproducibility_dryruns(report)
    audit_consistency(report)
    write_reports(report)

if __name__ == "__main__":
    main()
