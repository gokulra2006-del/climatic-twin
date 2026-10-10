import pandas as pd
import os
import glob

def process_cmwssb():
    print("Processing CMWSSB Water Levels...")
    base_dir = "data/raw/water_level/cmwssb"
    out_dir = "data/processed/water_level"
    os.makedirs(out_dir, exist_ok=True)
    
    files = glob.glob(os.path.join(base_dir, "*.csv"))
    if not files:
        print("No CMWSSB files found.")
        return
        
    dfs = []
    for f in files:
        df = pd.read_csv(f)
        dfs.append(df)
        
    if not dfs:
        return
        
    df_all = pd.concat(dfs, ignore_index=True)
    
    # Check for date columns and standardize
    # Usually "Date" or "DATE"
    date_cols = [c for c in df_all.columns if 'date' in c.lower()]
    if date_cols:
        date_col = date_cols[0]
        df_all['date_standard'] = pd.to_datetime(df_all[date_col], errors='coerce')
        df_all.sort_values('date_standard', inplace=True)
        
    out_path = os.path.join(out_dir, "cmwssb_reservoir_levels.csv")
    df_all.to_csv(out_path, index=False)
    print(f"Saved {len(df_all)} reservoir level records to {out_path}")

if __name__ == "__main__":
    process_cmwssb()
