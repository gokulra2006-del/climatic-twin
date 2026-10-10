import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict
from datetime import datetime

from app.api import deps
from app.models.user import User
from app.models.log import AuditLog
from app.core import security

logger = logging.getLogger(__name__)
router = APIRouter()


class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: str

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    role: str
    is_active: bool

class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: Optional[int] = None
    username: Optional[str] = None
    action: str
    resource: Optional[str] = None
    metadata_json: Optional[str] = None
    ip_address: Optional[str] = None
    timestamp: datetime

@router.get("/", response_model=List[UserResponse], dependencies=[Depends(deps.RoleChecker(["admin"]))])
def get_users(db: Session = Depends(deps.get_db_optional)):
    """Admin only: list all users."""
    if db:
        try:
            return db.query(User).all()
        except Exception as e:
            logger.warning(f"DB Error fetching users: {e}")
            
    # Mock fallback
    return [
        {"id": 1, "username": "admin", "email": "admin@climatetwin.local", "role": "admin", "is_active": True},
        {"id": 2, "username": "operator_1", "email": "op1@climatetwin.local", "role": "operator", "is_active": True},
        {"id": 3, "username": "viewer", "email": "viewer@climatetwin.local", "role": "viewer", "is_active": True}
    ]

@router.post("/", response_model=UserResponse, dependencies=[Depends(deps.RoleChecker(["admin"]))])
def create_user(user_in: UserCreate, db: Session = Depends(deps.get_db)):
    """Admin only: create a new user."""
    if user_in.role not in ["admin", "operator", "viewer"]:
        raise HTTPException(status_code=400, detail="Invalid role")
        
    user = db.query(User).filter(User.username == user_in.username).first()
    if user:
        raise HTTPException(status_code=400, detail="Username already exists")
        
    new_user = User(
        username=user_in.username,
        email=user_in.email,
        role=user_in.role,
        hashed_password=security.get_password_hash(user_in.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.get("/logs", response_model=List[AuditLogResponse], dependencies=[Depends(deps.RoleChecker(["admin"]))])
def get_audit_logs(db: Session = Depends(deps.get_db_optional)):
    """Admin only: list audit logs."""
    if db:
        try:
            logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(100).all()
            return logs
        except Exception as e:
            logger.warning(f"DB Error fetching logs: {e}")
            
    # Mock fallback
    return [
        {"id": 1, "user_id": 1, "username": "admin", "action": "LOGIN_SUCCESS", "resource": "SYSTEM", "metadata_json": '{"ip": "127.0.0.1"}', "ip_address": "127.0.0.1", "timestamp": datetime.now()},
        {"id": 2, "user_id": 1, "username": "admin", "action": "SIMULATED_ACTUATION_TRIGGERED", "resource": "FLOOD", "metadata_json": '{"command": "OPEN_POONDI_FLOODGATE", "risk_level": "CRITICAL"}', "ip_address": "127.0.0.1", "timestamp": datetime.now()},
    ]
