from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from app.db.base_class import Base

class HazardType(Base):
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    implementation_status = Column(String, nullable=True, default="PLANNED")
    
    events = relationship("HazardEvent", back_populates="hazard_type")
    predictions = relationship("HazardPrediction", back_populates="hazard_type")

class HazardEvent(Base):
    id = Column(Integer, primary_key=True, index=True)
    hazard_type_id = Column(Integer, ForeignKey("hazard_types.id"), nullable=False)
    name = Column(String, nullable=True)
    start_time = Column(DateTime(timezone=True), nullable=False, index=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    geom = Column(Geometry(geometry_type='GEOMETRY', srid=4326), nullable=True)
    severity = Column(String, nullable=True) # e.g. "Low", "Medium", "High", "Critical"
    
    hazard_type = relationship("HazardType", back_populates="events")
    historical_event = relationship("HistoricalEvent", back_populates="event", uselist=False)

class HistoricalEvent(Base):
    id = Column(Integer, primary_key=True, index=True)
    hazard_event_id = Column(Integer, ForeignKey("hazard_events.id"), nullable=False, unique=True)
    description = Column(String, nullable=True)
    impact_summary = Column(String, nullable=True)
    
    event = relationship("HazardEvent", back_populates="historical_event")

class HazardPrediction(Base):
    id = Column(Integer, primary_key=True, index=True)
    hazard_type_id = Column(Integer, ForeignKey("hazard_types.id"), nullable=False)
    prediction_time = Column(DateTime(timezone=True), nullable=False, index=True)
    forecast_horizon = Column(Integer, nullable=True) # Hours ahead
    geom = Column(Geometry(geometry_type='GEOMETRY', srid=4326), nullable=True)
    probability = Column(Float, nullable=True) # 0.0 to 1.0
    severity = Column(String, nullable=True)
    
    hazard_type = relationship("HazardType", back_populates="predictions")
