from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from geoalchemy2.elements import WKTElement
from typing import List, Dict, Any

from app.api import deps
from app.models.hazard import HazardEvent, HazardType
from app.schemas.other import HazardEventCreate, HazardEventResponse, HazardTypeResponse
from app.schemas.common import PaginatedResponse
from app.api.api_v1.endpoints.predictions import get_latest_prediction
from app.core.vulnerability import get_vulnerability_index

router = APIRouter()

from app.api.api_v1.endpoints.hazard_prototypes import (
    get_latest_heatwave,
    get_latest_drought,
    get_latest_wildfire,
    get_latest_extreme_rainfall
)

@router.get("/types", response_model=List[Dict[str, str]])
def read_hazard_types(db: Session = Depends(deps.get_db)):
    """Returns all supported hazard types and their implementation status."""
    return [
        {"name": "FLOOD", "status": "IMPLEMENTED"},
        {"name": "HEATWAVE", "status": "IMPLEMENTED"},
        {"name": "DROUGHT", "status": "IMPLEMENTED"},
        {"name": "WILDFIRE", "status": "IMPLEMENTED"},
        {"name": "EXTREME_RAINFALL", "status": "IMPLEMENTED"},
    ]

@router.get("/{hazard_type}/predictions")
def read_hazard_predictions(hazard_type: str, db: Session = Depends(deps.get_db)):
    """Routes predictions based on hazard type."""
    hazard_type = hazard_type.upper()
    if hazard_type == "FLOOD":
        return get_latest_prediction()
    elif hazard_type == "HEATWAVE":
        return get_latest_heatwave()
    elif hazard_type == "DROUGHT":
        return get_latest_drought()
    elif hazard_type == "WILDFIRE":
        return get_latest_wildfire()
    elif hazard_type == "EXTREME_RAINFALL":
        return get_latest_extreme_rainfall()
        
    return {
        "status": "FRAMEWORK READY",
        "message": f"{hazard_type} predictions are planned for a future implementation phase.",
        "data": None
    }

@router.get("/{hazard_type}/alerts")
def read_hazard_alerts(hazard_type: str, db: Session = Depends(deps.get_db)):
    """Routes alerts based on hazard type."""
    # Since we are returning prototype scores without DB alerts, we just return an empty list.
    return []

@router.get("/compound-risk")
def get_compound_risk(db: Session = Depends(deps.get_db)):
    """Computes a multi-hazard compound risk score."""
    flood = get_latest_prediction()
    heatwave = get_latest_heatwave()
    drought = get_latest_drought()
    wildfire = get_latest_wildfire()
    ext_rain = get_latest_extreme_rainfall()
    
    # Simple weighted aggregation
    f_prob = flood.get("probability", 0) if isinstance(flood, dict) else 0
    h_prob = heatwave.get("probability", 0)
    d_prob = drought.get("probability", 0)
    w_prob = wildfire.get("probability", 0)
    er_prob = ext_rain.get("probability", 0)
    
    compound_score = (f_prob * 0.4) + (er_prob * 0.3) + (h_prob * 0.1) + (d_prob * 0.1) + (w_prob * 0.1)
    
    if compound_score < 0.25: risk_level = "LOW"
    elif compound_score < 0.50: risk_level = "MODERATE"
    elif compound_score < 0.75: risk_level = "HIGH"
    else: risk_level = "CRITICAL"
    
    contributing = []
    for hazard, prob in [("Flood", f_prob), ("Extreme Rainfall", er_prob), ("Heatwave", h_prob), ("Drought", d_prob), ("Wildfire", w_prob)]:
        if prob > 0.4:
            contributing.append(hazard)
            
    return {
        "compound_score": compound_score,
        "compound_level": risk_level,
        "contributing_hazards": contributing,
        "methodology": "Weighted aggregation: Flood(40%), Ext. Rain(30%), Heatwave(10%), Drought(10%), Wildfire(10%)"
    }

@router.get("/cascading-risk")
def get_cascading_risk(db: Session = Depends(deps.get_db)):
    """Simulates inter-hazard cascading effects (domino effects)."""
    # In a real system, this would be computed by a spatiotemporal graph model.
    # We output a prototype cascading influence graph based on current states.
    heatwave = get_latest_heatwave()
    drought = get_latest_drought()
    ext_rain = get_latest_extreme_rainfall()
    
    h_prob = heatwave.get("probability", 0)
    d_prob = drought.get("probability", 0)
    er_prob = ext_rain.get("probability", 0)
    
    # Define cascading edges
    edges = []
    if h_prob > 0.4:
        edges.append({"source": "Heatwave", "target": "Drought", "amplification_factor": 1.25, "reason": "Accelerated soil moisture evaporation"})
        edges.append({"source": "Heatwave", "target": "Wildfire", "amplification_factor": 1.40, "reason": "Dry vegetation acts as tinder"})
        
    if d_prob > 0.4:
        edges.append({"source": "Drought", "target": "Wildfire", "amplification_factor": 1.50, "reason": "Prolonged dry fuel load"})
        edges.append({"source": "Drought", "target": "Flood", "amplification_factor": 1.15, "reason": "Soil hardening reduces absorption capacity"})
        
    if er_prob > 0.5:
        edges.append({"source": "Extreme Rainfall", "target": "Flood", "amplification_factor": 1.80, "reason": "Overwhelmed urban drainage capacity"})
        
    return {
        "active_cascades": edges,
        "vulnerability_multiplier": 1.0 + (len(edges) * 0.1) # Compound penalty
    }

@router.get("/vulnerability")
def get_vulnerability():
    """Returns socio-economic vulnerability data for Human Impact mapping."""
    return get_vulnerability_index()

@router.get("/", response_model=PaginatedResponse[HazardEventResponse])
def read_hazards(
    db: Session = Depends(deps.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    if db is not None:
        try:
            query = db.query(HazardEvent)
            total = query.count()
            events = query.offset(skip).limit(limit).all()
            return {"data": events, "total": total, "page": skip // limit + 1 if limit > 0 else 1, "page_size": limit, "total_pages": (total + limit - 1) // limit if limit > 0 else 0}
        except Exception:
            pass
    return {"data": [], "total": 0, "page": 1, "page_size": limit, "total_pages": 0}

@router.get("/event/{hazard_id}", response_model=HazardEventResponse)
def read_hazard(hazard_id: int, db: Session = Depends(deps.get_db)):
    if db is not None:
        try:
            event = db.query(HazardEvent).filter(HazardEvent.id == hazard_id).first()
            if event:
                return event
        except Exception:
            pass
    raise HTTPException(status_code=404, detail="Hazard event not found")


@router.post("/", response_model=HazardEventResponse, status_code=201)
def create_hazard(event_in: HazardEventCreate, db: Session = Depends(deps.get_db)):
    db_event = HazardEvent(
        hazard_type_id=event_in.hazard_type_id,
        name=event_in.name,
        start_time=event_in.start_time,
        end_time=event_in.end_time,
        severity=event_in.severity
    )
    if event_in.geom:
        db_event.geom = WKTElement(event_in.geom, srid=4326)
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event
