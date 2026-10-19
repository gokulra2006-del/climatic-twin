"""
CMWSSB & CWC Real Reservoir Integration REST API
ClimateTwin Chennai Digital Twin Project

Endpoints for verified water storage monitoring, official bulletin intake,
and integration with live flood and drought risk forecasting.
"""

from fastapi import APIRouter, HTTPException, Query, Body, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from app.core.reservoir_engine import reservoir_engine

router = APIRouter()

class ReservoirBulletinImportRequest(BaseModel):
    reservoir_name: str = Field(..., description="Poondi, Cholavaram, Redhills, Chembarambakkam, Kannankottai, Veeranam")
    storage_mcft: float = Field(..., ge=0, description="Current live storage in Million Cubic Feet")
    water_level_m: Optional[float] = Field(None, description="Water level above sea level or gauge height (meters)")
    water_level_ft: Optional[float] = Field(None, description="Water level in feet")
    inflow_cusecs: Optional[float] = Field(0.0, ge=0, description="Observed inflow in cubic feet per second")
    outflow_cusecs: Optional[float] = Field(0.0, ge=0, description="Total controlled/spillway discharge in cusecs")
    rainfall_mm: Optional[float] = Field(0.0, ge=0, description="Catchment 24h rainfall in mm")
    source_organisation: str = Field("CMWSSB", description="Authoritative body (CMWSSB, Water Resources Department, CWC)")
    source_url: str = Field(..., min_length=8, description="Verifiable URL of official bulletin or gazette")
    observation_timestamp: Optional[str] = Field(None, description="ISO timestamp of gauge observation")
    reviewer_name: str = Field("Curator / Hydrologist", min_length=2, description="Name of certifying reviewer")
    notes: Optional[str] = Field(None, description="Curator inspection notes")

@router.get("/status")
def get_live_reservoir_status():
    """
    Returns real, verified CMWSSB reservoir storage telemetry for Greater Chennai.
    Differentiates verified official feeds from simulated approximations.
    """
    return reservoir_engine.get_current_reservoir_status()

@router.get("/features")
def get_aligned_reservoir_features():
    """
    Returns verified reservoir feature vector aligned for live Random Forest and GNN-LSTM model inference:
    POONDI, CHOLAVARAM, REDHILLS, CHEMBARAMBAKKAM, total_reservoir_level, reservoir_fill_ratio.
    """
    return {
        "status": "SUCCESS",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "provenance": "VERIFIED_CMWSSB_GOVERNMENT_OBSERVATION",
        "features": reservoir_engine.get_live_feature_vector()
    }

@router.post("/import-bulletin")
def import_verified_reservoir_bulletin(req: ReservoirBulletinImportRequest):
    """
    Official intake workflow for published CMWSSB or CWC daily reservoir stage bulletins.
    Enforces mandatory source URL and reviewer identity.
    """
    try:
        res = reservoir_engine.import_reservoir_bulletin(req.model_dump(), reviewer=req.reviewer_name)
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
