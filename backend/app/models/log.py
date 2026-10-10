from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.db.base_class import Base

class SystemLog(Base):
    id = Column(Integer, primary_key=True, index=True)
    level = Column(String, index=True, nullable=False) # INFO, WARNING, ERROR, CRITICAL
    message = Column(String, nullable=False)
    source = Column(String, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)

class AuditLog(Base):
    """
    Security audit log for tracking authenticated actions (RBAC).
    Records who did what, when, and from where.
    """
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    username = Column(String, nullable=True)
    action = Column(String, nullable=False, index=True) # e.g., "LOGIN_SUCCESS", "SIMULATED_ACTUATION_APPROVED"
    resource = Column(String, nullable=True) # e.g., "POONDI_FLOODGATE"
    metadata_json = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
