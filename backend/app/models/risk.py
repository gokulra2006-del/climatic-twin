from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base

class DigitalTwinState(Base):
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("infrastructure_assets.id"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    state_data = Column(JSON, nullable=False) # Store complex state representation
    
    asset = relationship("InfrastructureAsset", back_populates="twin_states")
    risk_assessments = relationship("RiskAssessment", back_populates="twin_state")

class RiskAssessment(Base):
    id = Column(Integer, primary_key=True, index=True)
    twin_state_id = Column(Integer, ForeignKey("digital_twin_states.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    risk_score = Column(Float, nullable=False)
    details = Column(JSON, nullable=True)
    
    twin_state = relationship("DigitalTwinState", back_populates="risk_assessments")
    alerts = relationship("Alert", back_populates="risk_assessment")

class WarningLevel(Base):
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    severity_level = Column(Integer, nullable=False) # 1 (low) to 5 (extreme)
    color = Column(String, nullable=True) # Hex code for UI
    description = Column(String, nullable=True)
    
    alerts = relationship("Alert", back_populates="warning_level")

class Alert(Base):
    id = Column(Integer, primary_key=True, index=True)
    risk_assessment_id = Column(Integer, ForeignKey("risk_assessments.id"), nullable=True)
    warning_level_id = Column(Integer, ForeignKey("warning_levels.id"), nullable=False)
    message = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    risk_assessment = relationship("RiskAssessment", back_populates="alerts")
    warning_level = relationship("WarningLevel", back_populates="alerts")
