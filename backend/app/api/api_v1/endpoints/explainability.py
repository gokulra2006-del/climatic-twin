from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any

from app.core.explainability import explainability_engine
from app.api.api_v1.endpoints.hazards import read_hazard_predictions

router = APIRouter()

@router.get("/current")
def get_current_explainability():
    # Example multi-hazard wrapper if required
    return {"status": "Use specific hazard routes for now."}

@router.get("/{hazard_type}")
def get_hazard_explainability(hazard_type: str):
    hazard_type = hazard_type.upper()
    try:
        # Fetch current payload
        hazard_payload = read_hazard_predictions(hazard_type=hazard_type, db=None)
        
        # Call the engine
        xai_payload = explainability_engine.explain(hazard_type, hazard_payload)
        return xai_payload
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
