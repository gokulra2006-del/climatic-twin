import pandas as pd
import os
import glob
import numpy as np

def parse_tmp(val):
    if pd.isna(val): return np.nan
    v = str(val).split(',')[0]
    if v == '+9999': return np.nan
    try:
        return float(v) / 10.0
    except:
        return np.nan

def parse_slp(val):
    if pd.isna(val): return np.nan
    v = str(val).split(',')[0]
    if v == '99999': return np.nan
    try:
        return float(v) / 10.0
    except:
        return np.nan

def parse_wnd(val):
    if pd.isna(val): return np.nan
    parts = str(val).split(',')
    if len(parts) >= 4:
        v = parts[3]
        if v == '9999': return np.nan
        try:
            return float(v) / 10.0
        except:
            return np.nan
    return np.nan

def process_noaa():
    print("Processing NOAA ISD...")
    base_dir = "data/raw/weather/noaa_isd"
    out_dir = "data/processed/weather"
    os.makedirs(out_dir, exist_ok=True)
    
    files = glob.glob(os.path.join(base_dir, "*.csv"))
    dfs = []
    for f in files:
        try:
            df = pd.read_csv(f, dtype=str, on_bad_lines='skip', engine='python')
            dfs.append(df)
        except Exception as e:
            print(f"Error reading {f}: {e}")
        
    if not dfs:
        print("No NOAA ISD files found.")
        return
        
    df_all = pd.concat(dfs, ignore_index=True)
    
    # Parse dates
    df_all['DATE'] = pd.to_datetime(df_all['DATE'], errors='coerce')
    
    # Parse variables
    df_all['temperature_c'] = df_all['TMP'].apply(parse_tmp)
    df_all['dew_point_c'] = df_all['DEW'].apply(parse_tmp)
    df_all['sea_level_pressure_hpa'] = df_all['SLP'].apply(parse_slp)
    df_all['wind_speed_ms'] = df_all['WND'].apply(parse_wnd)
    
    out_df = df_all[['DATE', 'LATITUDE', 'LONGITUDE', 'temperature_c', 'dew_point_c', 'sea_level_pressure_hpa', 'wind_speed_ms']].copy()
    out_df.sort_values('DATE', inplace=True)
    
    out_path = os.path.join(out_dir, "noaa_isd_chennai_hourly.csv")
    out_df.to_csv(out_path, index=False)
    print(f"Saved {len(out_df)} hourly weather records to {out_path}")

if __name__ == "__main__":
    process_noaa()
