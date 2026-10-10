import os
import pandas as pd
from datetime import datetime, timezone
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Depends
from app.api.deps import RoleChecker
from app.api.api_v1.endpoints.hazard_prototypes import _calc_heatwave_prob, _calc_drought_prob, _calc_wildfire_prob, _calc_extreme_rain_prob, map_risk_level_generic

router = APIRouter()
PROCESSED_DIR = r"C:\Users\gokul\Desktop\PROJECTS\climatetwin\data\processed"

@router.get("/{hazard_type}", dependencies=[Depends(RoleChecker(["admin", "operator"]))])
def replay_hazard(
    hazard_type: str,
    start_date: str = Query("2015-11-01"),
    end_date: str = Query("2015-12-15")
):
    try:
        sd = pd.to_datetime(start_date)
        ed = pd.to_datetime(end_date)
        
        timeline = []
        
        if hazard_type == "flood" or hazard_type == "extreme-rainfall":
            df_imerg = pd.read_csv(os.path.join(PROCESSED_DIR, "rainfall", "imerg_chennai_daily.csv"))
            df_imerg['time'] = pd.to_datetime(df_imerg['time'])
            df_slice = df_imerg[(df_imerg['time'] >= sd) & (df_imerg['time'] <= ed)].copy()
            
            # Calculate 3-day rolling
            df_slice['rain_1d'] = df_slice['precipitation_mm_hr'] * 24
            df_slice['rain_3d'] = df_slice['rain_1d'].rolling(window=3, min_periods=1).sum()
            
            for _, row in df_slice.iterrows():
                r1 = float(row['rain_1d'])
                r3 = float(row['rain_3d'])
                
                if hazard_type == "extreme-rainfall":
                    prob = _calc_extreme_rain_prob(r1, r3)
                    state = 1 if prob >= 0.5 else 0
                    risk = map_risk_level_generic(prob)
                else: # flood proxy for replay
                    prob = min(1.0, max(0.0, r3 / 250.0))
                    state = 1 if prob >= 0.5 else 0
                    risk = map_risk_level_generic(prob)
                
                timeline.append({
                    "timestamp": row['time'].isoformat(),
                    "hazard": hazard_type,
                    "risk_score": prob,
                    "risk_level": risk,
                    "contributing_features": {
                        "rainfall_24h_mm": r1,
                        "rainfall_72h_mm": r3
                    }
                })
        else:
            raise HTTPException(status_code=501, detail=f"Replay for {hazard_type} not yet implemented")
            
        return {
            "hazard_type": hazard_type,
            "start_date": start_date,
            "end_date": end_date,
            "timeline": timeline
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Replay failed: {str(e)}")
