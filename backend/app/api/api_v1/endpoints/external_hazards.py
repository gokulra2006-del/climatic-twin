from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from app.core.external_hazards import external_hazards_engine

router = APIRouter()

@router.get("/detailed", response_model=Dict[str, Any])
async def get_detailed_hazards():
    """
    Fetch high-resolution hourly timeseries data for secondary hazards
    (Heat, Wind, Rainfall, Reservoirs) covering 7 days past and 3 days forecast.
    """
    try:
        data = await external_hazards_engine.get_detailed_hazards()
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
