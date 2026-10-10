import os
import pandas as pd
import numpy as np
import json
import logging
from datetime import datetime, timedelta

# Enforce logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("EventCataloguePipeline")

CONFIG = {
    "SEED": 42,
    "THRESHOLDS": {
        "FLOOD": {
            "rainfall_72h_mm": 80.0,
            "reservoir_level_pct": 30.0
        },
        "HEATWAVE": {
            "temp_max_c": 38.0,
            "consecutive_days": 2
        },
        "GRID_OVERLOAD": {
            "load_mw": 3500.0
        },
        "PUMP_FAILURE": {
            "status_code": 0
        }
    },
    "SPLITS": {
        "TRAIN_END": "2018-12-31",
        "VAL_END": "2020-12-31"
    },
    "PATHS": {
        "RAW_WEATHER": r"C:\Users\gokul\Desktop\PROJECTS\climatetwin\data\processed\weather\noaa_isd_chennai_hourly.csv",
        "RAW_RAIN": r"C:\Users\gokul\Desktop\PROJECTS\climatetwin\data\processed\rainfall\imerg_chennai_daily.csv",
        "RAW_RES": r"C:\Users\gokul\Desktop\PROJECTS\climatetwin\data\processed\water_level\cmwssb_reservoir_levels.csv",
        "OUT_DIR": r"C:\Users\gokul\Desktop\PROJECTS\climatetwin\data\processed\catalogue_v1"
    }
}

np.random.seed(CONFIG["SEED"])

def generate_synthetic_infrastructure(df_index, temp_series, rain_series):
    logger.info("Generating SYNTHETIC infrastructure data...")
    n = len(df_index)
    base_load = 2000 + (temp_series.fillna(30) - 25).clip(lower=0) * 80
    grid_load = base_load + np.random.normal(0, 100, n)
    failure_prob = 0.001 + (rain_series.fillna(0) > 50).astype(float) * 0.05
    pump_status = np.random.binomial(1, 1 - failure_prob)
    outages = (grid_load > CONFIG["THRESHOLDS"]["GRID_OVERLOAD"]["load_mw"]) | (pump_status == 0)
    
    syn_df = pd.DataFrame({
        "time": df_index,
        "grid_load_mw_SYNTHETIC": grid_load,
        "pump_status_SYNTHETIC": pump_status,
        "outage_active_SYNTHETIC": outages.astype(int)
    })
    return syn_df

def run_pipeline():
    os.makedirs(CONFIG["PATHS"]["OUT_DIR"], exist_ok=True)
    
    # A. Load Datasets
    logger.info("Loading base datasets...")
    df_rain = pd.read_csv(CONFIG["PATHS"]["RAW_RAIN"])
    df_rain['time'] = pd.to_datetime(df_rain['time']).dt.normalize()
        
    df_weather = pd.read_csv(CONFIG["PATHS"]["RAW_WEATHER"])
    df_weather['time'] = pd.to_datetime(df_weather['DATE']).dt.normalize()
    df_weather_daily = df_weather.groupby('time').agg(
        temp_mean=('temperature_c', 'mean'),
        temp_max=('temperature_c', 'max')
    ).reset_index()

    df_res = pd.read_csv(CONFIG["PATHS"]["RAW_RES"])
    df_res['time'] = pd.to_datetime(df_res['date_standard']).dt.normalize()
    df_res = df_res.groupby('time')[['POONDI', 'CHOLAVARAM', 'REDHILLS', 'CHEMBARAMBAKKAM']].mean().reset_index()
    df_res['total_res_pct'] = df_res[['POONDI', 'CHOLAVARAM', 'REDHILLS', 'CHEMBARAMBAKKAM']].mean(axis=1)

    # B. Merge
    logger.info("Merging datasets...")
    df = pd.merge(df_rain, df_weather_daily, on='time', how='inner')
    df = pd.merge(df, df_res, on='time', how='left')
    df['rainfall_daily'] = df['precipitationCal']
    
    # C. Add Synthetic Infra
    syn_df = generate_synthetic_infrastructure(df['time'], df['temp_max'], df['rainfall_daily'])
    df = pd.merge(df, syn_df, on='time', how='left')
    df = df.sort_values('time').reset_index(drop=True)
    
    # D. Feature Engineering
    df['rainfall_72h'] = df['rainfall_daily'].rolling(3, min_periods=1).sum()
    df['temp_max_2d_min'] = df['temp_max'].rolling(2, min_periods=1).min()
    
    # E. Label Events
    logger.info("Labeling events based on strict configuration thresholds...")
    df['event_flood'] = ((df['rainfall_72h'] >= CONFIG["THRESHOLDS"]["FLOOD"]["rainfall_72h_mm"]) & 
                         (df['total_res_pct'].fillna(0) >= CONFIG["THRESHOLDS"]["FLOOD"]["reservoir_level_pct"])).astype(int)
    
    df['event_heatwave'] = (df['temp_max_2d_min'] >= CONFIG["THRESHOLDS"]["HEATWAVE"]["temp_max_c"]).astype(int)
    df['event_grid_overload'] = (df['grid_load_mw_SYNTHETIC'] >= CONFIG["THRESHOLDS"]["GRID_OVERLOAD"]["load_mw"]).astype(int)
    df['event_pump_failure'] = (df['pump_status_SYNTHETIC'] == CONFIG["THRESHOLDS"]["PUMP_FAILURE"]["status_code"]).astype(int)
    
    # Extract multiple hazard types into a unified catalogue
    catalogue = []
    
    for h_type, col in [('FLOOD', 'event_flood'), ('HEATWAVE', 'event_heatwave')]:
        in_event = False
        start_date = None
        for idx, row in df.iterrows():
            if row[col] == 1 and not in_event:
                in_event = True
                start_date = row['time']
            elif row[col] == 0 and in_event:
                in_event = False
                end_date = df.iloc[idx-1]['time']
                
                # Expand end_date backwards to find real duration
                duration = (end_date - start_date).days + 1
                
                # Extract metrics
                mask = (df['time'] >= start_date) & (df['time'] <= end_date)
                catalogue.append({
                    "event_id": f"{h_type}_{start_date.strftime('%Y%m%d')}",
                    "hazard_type": h_type,
                    "start_time": start_date.strftime('%Y-%m-%d'),
                    "end_time": end_date.strftime('%Y-%m-%d'),
                    "duration_days": duration,
                    "peak_72h_rain_mm": float(df.loc[mask, 'rainfall_72h'].max()),
                    "peak_temp_c": float(df.loc[mask, 'temp_max'].max()),
                    "synthetic_infra_impact": bool(df.loc[mask, 'outage_active_SYNTHETIC'].max())
                })
        # If event hits end of time series
        if in_event:
             end_date = df.iloc[-1]['time']
             duration = (end_date - start_date).days + 1
             mask = (df['time'] >= start_date) & (df['time'] <= end_date)
             catalogue.append({
                 "event_id": f"{h_type}_{start_date.strftime('%Y%m%d')}",
                 "hazard_type": h_type,
                 "start_time": start_date.strftime('%Y-%m-%d'),
                 "end_time": end_date.strftime('%Y-%m-%d'),
                 "duration_days": duration,
                 "peak_72h_rain_mm": float(df.loc[mask, 'rainfall_72h'].max()),
                 "peak_temp_c": float(df.loc[mask, 'temp_max'].max()),
                 "synthetic_infra_impact": bool(df.loc[mask, 'outage_active_SYNTHETIC'].max())
             })
             
    cat_df = pd.DataFrame(catalogue)
    cat_path = os.path.join(CONFIG["PATHS"]["OUT_DIR"], "event_catalogue.csv")
    cat_df.to_csv(cat_path, index=False)
    logger.info(f"Generated catalogue with {len(cat_df)} events. Saved to {cat_path}")

    # G. Quality Report
    dq_report = {
        "total_records": len(df),
        "date_range": [str(df['time'].min()), str(df['time'].max())],
        "missing_values": df.isnull().sum().to_dict(),
        "synthetic_flags": ["grid_load_mw_SYNTHETIC", "pump_status_SYNTHETIC", "outage_active_SYNTHETIC"],
        "provenance": "Merged IMD/IMERG + NOAA + CMWSSB + Synthetic Generator V1"
    }
    with open(os.path.join(CONFIG["PATHS"]["OUT_DIR"], "data_quality_report.json"), "w") as f:
        json.dump(dq_report, f, indent=4)
        
    # H. Strict Chronological Splits
    logger.info("Executing strict chronological splits...")
    train_mask = df['time'] <= CONFIG["SPLITS"]["TRAIN_END"]
    val_mask = (df['time'] > CONFIG["SPLITS"]["TRAIN_END"]) & (df['time'] <= CONFIG["SPLITS"]["VAL_END"])
    test_mask = df['time'] > CONFIG["SPLITS"]["VAL_END"]
    
    df[train_mask].to_csv(os.path.join(CONFIG["PATHS"]["OUT_DIR"], "train_split.csv"), index=False)
    df[val_mask].to_csv(os.path.join(CONFIG["PATHS"]["OUT_DIR"], "val_split.csv"), index=False)
    df[test_mask].to_csv(os.path.join(CONFIG["PATHS"]["OUT_DIR"], "test_split.csv"), index=False)
    
    logger.info(f"Saved splits: Train={train_mask.sum()}, Val={val_mask.sum()}, Test={test_mask.sum()}")
    
if __name__ == '__main__':
    run_pipeline()
