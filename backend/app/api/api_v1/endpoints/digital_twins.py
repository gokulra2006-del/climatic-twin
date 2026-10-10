from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import numpy as np

from app.api import deps
from app.models.risk import DigitalTwinState
from app.schemas.other import TwinResponse
from app.schemas.common import PaginatedResponse
from app.core.assimilation import twin_engine
from app.api.api_v1.endpoints.predictions import get_model, map_risk_level

router = APIRouter()

class ObservationInput(BaseModel):
    asset_id: str = Field(..., description="Asset identifier (e.g., 'POONDI', 'REDHILLS', 'rainfall_daily')")
    variable: str = Field(..., description="Observed variable (e.g., 'water_level', 'storage_mcft', 'rainfall_mm')")
    value: float = Field(..., description="Observed numerical sensor/telemetry value")
    sensor_id: Optional[str] = Field(None, description="Optional sensor hardware ID (e.g., 'SENSOR_POONDI_01')")
    timestamp: Optional[datetime] = Field(None, description="Timestamp of observation in UTC")
    unit: Optional[str] = Field(None, description="Measurement unit (e.g., 'mcft', 'mm', 'celsius')")
    quality_flag: str = Field("GOOD", description="Quality flag: 'EXCELLENT', 'GOOD', 'ACCEPTABLE', 'LOW_CONFIDENCE', 'WARNING'")
    source: str = Field("SIMULATION", description="Data origin (e.g., 'IOT_GATEWAY', 'SIMULATION', 'HISTORICAL_REPLAY')")

class AssimilationResponse(BaseModel):
    event_id: int
    asset_id: str
    variable: str
    observation_value: float
    prior_state: float
    assimilation_weight: float
    updated_state: float
    validation_status: str
    validation_message: str
    quality_flag: str
    source: str
    obs_timestamp: str
    assimilated_at: str
    assimilation_ms: float
    prediction_after_assimilation: Dict[str, Any]

class TwinFullStateResponse(BaseModel):
    state: Dict[str, float]
    last_update: Dict[str, str]
    quality: Dict[str, str]
    current_prediction: Dict[str, Any]

@router.post("/assimilate", response_model=AssimilationResponse)
def assimilate_sensor_observation(payload: ObservationInput):
    """
    Ingests an incoming sensor observation, validates it, assimilates it into the digital twin,
    and runs real-time flood prediction using the updated digital twin state.
    """
    # 1. Execute Data Assimilation
    obs_time = payload.timestamp or datetime.now(timezone.utc)
    event_record = twin_engine.assimilate(
        asset_id=payload.asset_id,
        variable=payload.variable,
        value=payload.value,
        obs_timestamp=obs_time,
        unit=payload.unit,
        quality_flag=payload.quality_flag,
        sensor_id=payload.sensor_id,
        source=payload.source
    )
    
    # 2. Extract Updated 14-Feature Vector
    features = twin_engine.get_feature_vector()
    features_arr = np.array(features).reshape(1, -1)
    
    # 3. Execute Model Prediction on the Updated Digital-Twin State
    model_data = get_model()
    if model_data is not None:
        try:
            model = model_data["model"]
            prob = float(model.predict_proba(features_arr)[0, 1])
            state = int(model.predict(features_arr)[0])
            risk_level = map_risk_level(prob)
        except Exception as e:
            prob = 0.5
            state = 0
            risk_level = "MODERATE"
    else:
        prob = 0.0
        state = 0
        risk_level = "LOW"
        
    pred_result = {
        "predicted_state": state,
        "probability": prob,
        "risk_level": risk_level,
        "features_used": features
    }
    
    event_record["prediction_after_assimilation"] = pred_result
    return event_record

@router.get("/state", response_model=TwinFullStateResponse)
def get_digital_twin_state():
    """
    Retrieves the current assimilated state vector of all monitored infrastructure assets.
    """
    current = twin_engine.get_current_state()
    features = twin_engine.get_feature_vector()
    features_arr = np.array(features).reshape(1, -1)
    
    model_data = get_model()
    if model_data is not None:
        try:
            model = model_data["model"]
            prob = float(model.predict_proba(features_arr)[0, 1])
            state = int(model.predict(features_arr)[0])
            risk_level = map_risk_level(prob)
        except Exception:
            prob, state, risk_level = 0.4, 0, "MODERATE"
    else:
        prob, state, risk_level = 0.0, 0, "LOW"
        
    current["current_prediction"] = {
        "probability": prob,
        "predicted_state": state,
        "risk_level": risk_level
    }
    return current

@router.get("/state/{asset_id}")
def get_asset_twin_state(asset_id: str):
    """
    Retrieves the current state of a specific asset.
    """
    current = twin_engine.get_current_state()
    target_key = asset_id if asset_id in current["state"] else asset_id.upper()
    if target_key not in current["state"]:
        raise HTTPException(status_code=404, detail=f"Asset '{asset_id}' not found in digital twin state")
        
    return {
        "asset_id": target_key,
        "state_value": current["state"][target_key],
        "last_update": current["last_update"].get(target_key),
        "quality": current["quality"].get(target_key)
    }

@router.get("/history", response_model=List[Dict[str, Any]])
def get_assimilation_history(limit: int = Query(50, ge=1, le=500)):
    """
    Returns the audit trail of recent data assimilation events.
    """
    return twin_engine.get_history(limit=limit)

@router.post("/reset")
def reset_twin_state():
    """
    Resets the digital twin state back to nominal baseline (useful for testing/simulation).
    """
    twin_engine.reset_to_baseline()
    return {"message": "Digital twin state reset to nominal baseline"}

@router.get("/", response_model=PaginatedResponse[TwinResponse])
def get_twins(
    db: Session = Depends(deps.get_db_optional),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    if db is not None:
        try:
            query = db.query(DigitalTwinState)
            total = query.count()
            twins = query.offset(skip).limit(limit).all()
            if total > 0:
                return {"data": twins, "total": total, "page": skip // limit + 1 if limit > 0 else 1, "page_size": limit, "total_pages": (total + limit - 1) // limit if limit > 0 else 0}
        except Exception:
            pass
            
    # Fallback to current twin state representation
    current = twin_engine.get_current_state()
    mock_twins = [
        {
            "id": 1,
            "asset_id": 1,
            "timestamp": datetime.now(timezone.utc),
            "state_data": current["state"]
        }
    ]
    return {"data": mock_twins, "total": len(mock_twins), "page": 1, "page_size": limit, "total_pages": 1}

@router.get("/{asset_id}", response_model=TwinResponse)
def get_twin_by_asset(asset_id: int, db: Session = Depends(deps.get_db_optional)):
    if db is not None:
        try:
            twin = db.query(DigitalTwinState).filter(DigitalTwinState.asset_id == asset_id).order_by(DigitalTwinState.timestamp.desc()).first()
            if twin:
                return twin
        except Exception:
            pass
            
    current = twin_engine.get_current_state()
    return {
        "id": asset_id,
        "asset_id": asset_id,
        "timestamp": datetime.now(timezone.utc),
        "state_data": current["state"]
    }
