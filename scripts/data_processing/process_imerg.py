import h5py
import os
import glob
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def process_imerg():
    print("Processing IMERG V07...")
    base_dir = "data/raw/rainfall/imerg_v07"
    out_dir = "data/processed/rainfall"
    os.makedirs(out_dir, exist_ok=True)
    
    files = sorted(glob.glob(os.path.join(base_dir, "*.HDF5")))
    if not files:
        print("No IMERG files found.")
        return
        
    print(f"Found {len(files)} files. Processing sequentially with h5py to extract Chennai bounding box...")
    
    records = []
    
    for i, f in enumerate(files):
        if i % 500 == 0:
            print(f"Processed {i}/{len(files)} files...")
            
        try:
            with h5py.File(f, 'r') as h5f:
                grid = h5f['Grid']
                t_sec = int(grid['time'][0])
                t = datetime(1980, 1, 6) + timedelta(seconds=t_sec)
                
                # Extract precipitation slice: lon_idx (2595:2605), lat_idx (1025:1035)
                # Precipitation shape is (time, lon, lat) -> (1, 3600, 1800)
                precip_slice = grid['precipitation'][0, 2595:2605, 1025:1035]
                mean_precip = float(precip_slice.mean())
                
                # Check for fill values (usually negative numbers like -9999.9 or -9999.0)
                if mean_precip < 0:
                    mean_precip = 0.0
                
                records.append({'time': t, 'precipitation_mm_hr': mean_precip})
                
        except Exception as e:
            print(f"Error reading {f}: {e}")
            
    if not records:
        print("No records extracted.")
        return
        
    df = pd.DataFrame(records)
    df['time'] = pd.to_datetime(df['time'])
    df.set_index('time', inplace=True)
    
    # Resample to hourly and daily
    df_hourly = df.resample('1h').mean()
    df_daily = df.resample('1D').mean() * 24.0
    
    df_hourly.to_csv(os.path.join(out_dir, "imerg_chennai_hourly.csv"))
    df_daily.to_csv(os.path.join(out_dir, "imerg_chennai_daily.csv"))
    
    print(f"Saved {len(df_daily)} daily records to {out_dir}/imerg_chennai_daily.csv")

if __name__ == "__main__":
    process_imerg()
