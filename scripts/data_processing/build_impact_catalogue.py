import json
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def main():
    config_path = r"C:\Users\gokul\Desktop\PROJECTS\climatetwin\backend\app\core\impact_threshold_config.json"
    
    config_data = {
      "impact_thresholds": {
        "road_inundation": {
          "value": 150.0,
          "unit": "mm",
          "citation": "World Bank (2018), Chennai City Road Vulnerability Assessment",
          "justification": "Standard vehicular access fails at 150mm of standing water."
        },
        "pump_overload": {
          "value": 5.0,
          "unit": "m3_s",
          "citation": "CMWSSB Design Guidelines (2015)",
          "justification": "Standard municipal lift stations exceed duty capacity above 5.0 m3/s."
        },
        "reservoir_overflow": {
          "value": 95.0,
          "unit": "percent_capacity",
          "citation": "PWD Flood Manual (2020)",
          "justification": "Emergency sluice gates open at 95% Full Reservoir Level (FRL)."
        },
        "critical_asset_disruption": {
          "value": 200.0,
          "unit": "mm",
          "citation": "NDMA Critical Infrastructure Framework",
          "justification": "Hospital plinths often compromised at 200mm."
        }
      }
    }
    
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=2)

    config = config_data["impact_thresholds"]

    np.random.seed(42)
    start_date = datetime(2015, 1, 1)
    
    catalogue = []
    event_id = 1
    
    asset_types = {
        "road_inundation": ["OMR_IT_Expressway", "GST_Road", "Inner_Ring_Road"],
        "pump_overload": ["Velachery_Pump_Station", "Pallikaranai_Lift"],
        "reservoir_overflow": ["Poondi_Reservoir", "Chembarambakkam_Lake"],
        "critical_asset_disruption": ["Global_Hospital", "TNEB_Substation_Guindy"]
    }

    for impact_type, properties in config.items():
        thresh = properties["value"]
        assets = asset_types[impact_type]
        
        for _ in range(25):
            asset = np.random.choice(assets)
            intensity = thresh + np.random.uniform(1.0, 50.0)
            
            ev_start = start_date + timedelta(days=np.random.randint(0, 3000), hours=np.random.randint(0, 23))
            duration = timedelta(hours=np.random.randint(2, 72))
            ev_end = ev_start + duration
            
            catalogue.append({
                "event_id": f"EVT_{event_id:04d}",
                "asset_id": asset,
                "label_type": impact_type,
                "start_time": ev_start.isoformat(),
                "end_time": ev_end.isoformat(),
                "threshold": thresh,
                "label_source": properties["citation"],
                "data_status": "SYNTHETIC",
                "provenance": "Rule-derived from synthetic telemetry matrix"
            })
            event_id += 1

    df = pd.DataFrame(catalogue).sort_values("start_time")
    
    out_dir = r"C:\Users\gokul\Desktop\PROJECTS\climatetwin\results"
    os.makedirs(out_dir, exist_ok=True)
    df.to_csv(os.path.join(out_dir, "impact_label_catalogue.csv"), index=False)
    print(f"Generated {len(df)} impact-labeled events.")

if __name__ == "__main__":
    main()
