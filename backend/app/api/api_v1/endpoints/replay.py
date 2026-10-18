import os
import pandas as pd
from datetime import datetime, timezone
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from app.api.api_v1.endpoints.hazard_prototypes import _calc_heatwave_prob, _calc_drought_prob, _calc_wildfire_prob, _calc_extreme_rain_prob, map_risk_level_generic

router = APIRouter()
PROCESSED_DIR = r"C:\Users\gokul\Desktop\PROJECTS\climatetwin\data\processed"

@router.get("/{hazard_type}")
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
            
            # The archived IMERG export is one row per day; despite the legacy
            # column name, values are daily accumulations in millimetres.
            # Do not multiply by 24, which would inflate replay severity.
            df_slice['rain_1d'] = df_slice['precipitation_mm_hr']
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
        elif hazard_type == "drought":
            reservoir_path = os.path.join(PROCESSED_DIR, "water_level", "cmwssb_reservoir_levels.csv")
            df_reservoirs = pd.read_csv(reservoir_path)
            df_reservoirs["date_standard"] = pd.to_datetime(df_reservoirs["date_standard"])
            storage_columns = ["POONDI", "CHOLAVARAM", "REDHILLS", "CHEMBARAMBAKKAM"]
            for column in storage_columns:
                df_reservoirs[column] = pd.to_numeric(df_reservoirs[column], errors="coerce").fillna(0.0)

            df_slice = df_reservoirs[
                (df_reservoirs["date_standard"] >= sd) & (df_reservoirs["date_standard"] <= ed)
            ].copy()
            if df_slice.empty:
                raise HTTPException(status_code=404, detail="No reservoir archive records exist for this replay window")

            # Some historical imports contain a zero-valued duplicate for the same day.
            # Daily maxima preserve the recorded storage observation without summing duplicates.
            df_daily = df_slice.groupby("date_standard", as_index=False)[storage_columns].max()
            df_daily["total_storage_mcft"] = df_daily[storage_columns].sum(axis=1)
            total_capacity_mcft = 11257.0
            df_daily["storage_pct"] = (df_daily["total_storage_mcft"] / total_capacity_mcft * 100.0).clip(0.0, 100.0)
            df_daily["storage_change_7d_mcft"] = df_daily["total_storage_mcft"].diff(7).fillna(0.0)

            for _, row in df_daily.iterrows():
                # This is deliberately a reservoir-storage stress proxy. Historical rainfall and
                # soil-moisture inputs are not available in this local replay archive.
                prob = float(min(1.0, max(0.0, 1.0 - (row["storage_pct"] / 100.0))))
                timeline.append({
                    "timestamp": row["date_standard"].isoformat(),
                    "hazard": "drought",
                    "risk_score": prob,
                    "risk_level": map_risk_level_generic(prob),
                    "contributing_features": {
                        "total_reservoir_storage_mcft": round(float(row["total_storage_mcft"]), 1),
                        "total_reservoir_storage_pct": round(float(row["storage_pct"]), 1),
                        "storage_change_7d_mcft": round(float(row["storage_change_7d_mcft"]), 1),
                        "historical_rainfall_available": False,
                        "historical_soil_moisture_available": False,
                    },
                })
        else:
            raise HTTPException(status_code=501, detail=f"Replay for {hazard_type} not yet implemented")
            
        return {
            "hazard_type": hazard_type,
            "start_date": start_date,
            "end_date": end_date,
            "timeline": timeline,
            "method_note": (
                "Rainfall-driven flood-risk proxy using archived daily precipitation."
                if hazard_type != "drought"
                else "Reservoir-storage drought-stress proxy. Historical rainfall and soil-moisture observations are unavailable in this local replay archive."
            ),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Replay failed: {str(e)}")
