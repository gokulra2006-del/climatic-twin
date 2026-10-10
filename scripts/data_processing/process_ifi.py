import pandas as pd
import os
import glob

def process_ifi():
    print("Processing IFI...")
    base_dir = "data/raw/flood_events/ifi_impacts"
    out_dir = "data/processed/flood_events"
    os.makedirs(out_dir, exist_ok=True)
    
    # 1. Main Events File
    events_file = os.path.join(base_dir, "India_Flood_Inventory_v3.csv")
    if os.path.exists(events_file):
        df_events = pd.read_csv(events_file)
        
        # Filter for Chennai (case-insensitive, handling NaNs)
        chennai_mask = (
            df_events['Districts'].fillna('').str.contains('Chennai', case=False) |
            df_events['Location'].fillna('').str.contains('Chennai', case=False)
        )
        chennai_events = df_events[chennai_mask].copy()
        
        # Standardize dates
        chennai_events['Start Date'] = pd.to_datetime(chennai_events['Start Date'], format='%d-%m-%Y %H:%M', errors='coerce')
        chennai_events['End Date'] = pd.to_datetime(chennai_events['End Date'], format='%d-%m-%Y %H:%M', errors='coerce')
        
        out_path = os.path.join(out_dir, "chennai_flood_events.csv")
        chennai_events.to_csv(out_path, index=False)
        print(f"Saved {len(chennai_events)} Chennai flood events to {out_path}")
    else:
        print(f"Warning: Main events file not found at {events_file}")

    # 2. District Impacts File
    impacts_file = os.path.join(base_dir, "District_FloodImpact.csv")
    if os.path.exists(impacts_file):
        df_impacts = pd.read_csv(impacts_file)
        chennai_impacts = df_impacts[df_impacts['Dist_Name'].fillna('').str.contains('Chennai', case=False)].copy()
        out_path = os.path.join(out_dir, "chennai_flood_impacts.csv")
        chennai_impacts.to_csv(out_path, index=False)
        print(f"Saved {len(chennai_impacts)} Chennai impact records to {out_path}")
        
    # 3. District Flooded Area File
    area_file = os.path.join(base_dir, "District_FloodedArea.csv")
    if os.path.exists(area_file):
        df_area = pd.read_csv(area_file)
        chennai_area = df_area[df_area['Dist_Name'].fillna('').str.contains('Chennai', case=False)].copy()
        out_path = os.path.join(out_dir, "chennai_flooded_area.csv")
        chennai_area.to_csv(out_path, index=False)
        print(f"Saved {len(chennai_area)} Chennai area records to {out_path}")

if __name__ == "__main__":
    process_ifi()
