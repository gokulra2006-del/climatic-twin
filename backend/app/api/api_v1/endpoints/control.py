from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime, timezone
import json
from sqlalchemy.orm import Session
from app.api import deps
from app.api.deps import RoleChecker, get_current_user
from app.models.log import AuditLog
from app.models.user import User
router = APIRouter()
class SimulateControlRequest(BaseModel):
    simulation_mode: bool
    hazard_type: str
    risk_level: str
    risk_probability: float
    triggering_features: dict
class SimulateControlResponse(BaseModel):
    timestamp: str
    command: str
    hazard: str
    risk_level: str
    probability: float
    action_result: str
    disclaimer: str = "SIMULATION ONLY — NO REAL INFRASTRUCTURE CONTROL"
@router.post("/simulate", response_model=SimulateControlResponse, dependencies=[Depends(RoleChecker(["admin", "operator"]))])
def simulate_actuation(payload: SimulateControlRequest, db: Session = Depends(deps.get_db), current_user: User = Depends(get_current_user)):
    if not payload.simulation_mode:
        raise HTTPException(status_code=400, detail="simulation_mode must be True. Real control is strictly prohibited.")
        
    if payload.hazard_type.lower() == "flood" and payload.risk_level.upper() == "CRITICAL":
        command = "OPEN_POONDI_FLOODGATE"
        action_result = "Simulated floodgate release authorized based on critical flood risk."
    elif payload.hazard_type.lower() == "wildfire" and payload.risk_level.upper() == "CRITICAL":
        command = "DISPATCH_EMERGENCY_RESPONSE"
        action_result = "Simulated dispatch of local fire units."
    else:
        command = "NO_ACTION_REQUIRED"
        action_result = f"No automated actuation configured for {payload.hazard_type} at {payload.risk_level} level."
        
    audit = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="SIMULATED_ACTUATION_TRIGGERED",
        resource=payload.hazard_type,
        metadata_json=json.dumps({"command": command, "risk_level": payload.risk_level})
    )
    db.add(audit)
    db.commit()
        
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "command": command,
        "hazard": payload.hazard_type,
        "risk_level": payload.risk_level,
        "probability": payload.risk_probability,
        "action_result": action_result
    }