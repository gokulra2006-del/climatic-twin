from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from datetime import datetime, timezone
from app.db.base_class import Base

class ImpactRecord(Base):
    __tablename__ = "impact_records"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String, index=True, nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False, index=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    zone = Column(String, index=True, nullable=False)
    impact_type = Column(String, index=True, nullable=False)
    # Allowed: waterlogging, road_closure, flood_extent, reservoir_overflow, power_outage, hospital_access_disruption, drainage_failure
    severity = Column(String, nullable=False, default="moderate")
    # Low, Moderate, High, Critical
    source_name = Column(String, nullable=False)
    source_url = Column(String, nullable=True)
    evidence_status = Column(String, nullable=False, default="proxy")
    # Allowed: historical_real, proxy, synthetic, unverified
    confidence = Column(Float, nullable=False, default=0.8)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
