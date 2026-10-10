import pandas as pd
import json
import os
import glob

def process_open_meteo():
    print("Processing Open-Meteo forecast...")
    base_dir = "data/raw/weather/open_meteo"
    out_dir = "data/processed/forecast"
    os.makedirs(out_dir, exist_ok=True)
    
    files = glob.glob(os.path.join(base_dir, "*.json"))
    if not files:
        print("No Open-Meteo files found.")
        return
        
    for f in files:
        with open(f, 'r') as file:
            data = json.load(file)
            
            if 'hourly' in data:
                df = pd.DataFrame(data['hourly'])
                # Convert time to datetime
                df['time'] = pd.to_datetime(df['time'])
                
                # Output naming
                out_name = os.path.basename(f).replace('.json', '.csv')
                out_path = os.path.join(out_dir, out_name)
                df.to_csv(out_path, index=False)
                print(f"Saved {len(df)} forecast records to {out_path}")
            else:
                print(f"Warning: No 'hourly' data found in {f}")

if __name__ == "__main__":
    process_open_meteo()
