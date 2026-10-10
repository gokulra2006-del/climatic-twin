from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from app.api import deps
from app.schemas.common import PaginatedResponse
from app.core.alert_intelligence import alert_engine
from app.core.assimilation import twin_engine

router = APIRouter()

@router.get("/")
def get_alerts():
    # Return all alerts (active + history) for simplicity, or just history
    return {
        "active": [a.dict() for a in alert_engine.get_active_alerts()],
        "history": [a.dict() for a in alert_engine.get_history()]
    }

@router.get("/active")
def get_active_alerts():
    return [a.dict() for a in alert_engine.get_active_alerts()]

@router.get("/history")
def get_alert_history():
    return [a.dict() for a in alert_engine.get_history()]

@router.get("/{alert_id}")
def get_alert(alert_id: str):
    for a in alert_engine.get_active_alerts():
        if a.alert_id == alert_id:
            return a.dict()
    for a in alert_engine.get_history():
        if a.alert_id == alert_id:
            return a.dict()
    raise HTTPException(status_code=404, detail="Alert not found")

@router.post("/evaluate")
def evaluate_alerts():
    state = twin_engine.get_current_state()
    # In a real system, we'd also fetch forecast_data from the model
    # For now, pass an empty dict or mock forecast
    forecast_data = {"forecast": {"30min": {"probability": state.get("flood_probability", 0.0) + 0.2}}}
    
    updated_alerts = alert_engine.evaluate_state(state, forecast_data)
    return [a.dict() for a in updated_alerts]

@router.post("/{alert_id}/acknowledge")
def acknowledge_alert(alert_id: str):
    res = alert_engine.acknowledge_alert(alert_id)
    if not res:
        raise HTTPException(status_code=404, detail="Active alert not found")
    return res.dict()

@router.post("/{alert_id}/resolve")
def resolve_alert(alert_id: str):
    success = alert_engine.resolve_alert(alert_id)
    if not success:
        raise HTTPException(status_code=404, detail="Active alert not found")
    return {"status": "resolved"}

@router.post("/simulate")
def simulate_emergency(scenario: dict):
    """
    Expects {"scenario": "SCENARIO_B_HEAVY_RAIN"} etc.
    Send {"scenario": "RESET"} to clear simulation.
    """
    scen = scenario.get("scenario")
    if scen == "RESET":
        alert_engine.clear_simulation()
        return {"status": "Live data restored"}
    else:
        alert_engine.set_simulation(scen)
        # Force evaluation immediately
        evaluate_alerts()
        return {"status": f"Simulation {scen} active"}
