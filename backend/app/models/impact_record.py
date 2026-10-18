from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
from datetime import datetime, timezone
from app.db.base_class import Base

class ImpactRecord(Base):
    __tablename__ = "impact_records"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String, index=True, nullable=False, unique=True)
    start_time = Column(DateTime(timezone=True), nullable=False, index=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    exact_time_verified = Column(Boolean, default=False, nullable=False)
    
    # Spatial coordinates & precision
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    zone = Column(String, index=True, nullable=False)
    location_accuracy_m = Column(Float, nullable=True, default=1000.0)
    location_precision_type = Column(String, nullable=True, default="ward_centroid")
    # Allowed location_precision_type: exact_gps, asset_landmark, road_stretch, ward_centroid, citywide_centroid
    
    # Impact categorization
    impact_type = Column(String, index=True, nullable=False)
    # Allowed: waterlogging, road_closure, flood_extent, reservoir_overflow, power_outage, hospital_access_disruption, drainage_failure
    severity = Column(String, nullable=False, default="moderate")
    # Allowed: low, moderate, high, critical
    severity_evidence = Column(Text, nullable=True)
    
    # Primary source intake & provenance
    source_name = Column(String, nullable=False)
    source_org = Column(String, nullable=True)
    source_url = Column(String, nullable=True)
    source_ref_id = Column(String, nullable=True)
    access_date = Column(String, nullable=True)
    report_page = Column(String, nullable=True)
    exact_passage = Column(Text, nullable=True)
    
    # Corroborating source
    corroborating_source_name = Column(String, nullable=True)
    corroborating_source_org = Column(String, nullable=True)
    corroborating_source_url = Column(String, nullable=True)
    
    # Observed physical measurements (for 2D hydraulic validation readiness)
    observed_flood_extent_sqkm = Column(Float, nullable=True)
    observed_flood_depth_m = Column(Float, nullable=True)
    road_closure_duration_hours = Column(Float, nullable=True)
    power_outage_duration_hours = Column(Float, nullable=True)
    hospital_access_cut = Column(Boolean, nullable=True)
    satellite_product = Column(String, nullable=True)
    gauge_level_m = Column(Float, nullable=True)
    affected_critical_assets = Column(Text, nullable=True)
    
    # Evidence & review status
    evidence_status = Column(String, nullable=False, default="unverified")
    # Allowed: historical_real, proxy, synthetic, unverified, under_review, rejected
    confidence = Column(Float, nullable=True, default=None)  # None for synthetic, 0.0 - 1.0 (or 0-100)
    confidence_score_breakdown = Column(Text, nullable=True)  # JSON-encoded rubric breakdown
    rubric_reason = Column(Text, nullable=True)
    
    # Attachment & document provenance
    document_hash = Column(String, nullable=True)  # SHA-256
    attachment_filename = Column(String, nullable=True)
    attachment_mime_type = Column(String, nullable=True)
    data_license = Column(String, nullable=True, default="Open Government Data (OGD) India / Fair Use Research")
    privacy_notes = Column(Text, nullable=True)
    
    # Curator review log
    reviewer_name = Column(String, nullable=True)
    review_timestamp = Column(DateTime(timezone=True), nullable=True)
    review_decision = Column(String, nullable=True, default="pending")
    # Allowed: pending, under_review, approved_historical_real, rejected, revision_needed
    review_notes = Column(Text, nullable=True)
    review_history = Column(Text, nullable=True)  # JSON-encoded array of change logs
    
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
