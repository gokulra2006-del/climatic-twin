from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

ALLOWED_IMPACT_TYPES = {
    "waterlogging",
    "road_closure",
    "flood_extent",
    "reservoir_overflow",
    "reservoir_release",
    "power_outage",
    "hospital_access_disruption",
    "drainage_failure",
    "water_deficit_crisis",
    "public_complaint",
    "public_complaints"
}

ALLOWED_EVIDENCE_STATUSES = {
    "historical_real",
    "proxy",
    "synthetic",
    "unverified",
    "under_review",
    "rejected"
}

ALLOWED_SEVERITIES = {"low", "moderate", "high", "critical"}

ALLOWED_PRECISION_TYPES = {
    "exact_gps",
    "asset_landmark",
    "road_stretch",
    "ward_centroid",
    "citywide_centroid"
}

ALLOWED_REVIEW_DECISIONS = {
    "pending",
    "under_review",
    "approved_historical_real",
    "rejected",
    "revision_needed"
}

class RubricItem(BaseModel):
    points: int
    max_points: int
    achieved: bool
    evidence: str

class RubricBreakdown(BaseModel):
    authoritative_primary_source: RubricItem
    exact_datetime: RubricItem
    precise_location: RubricItem
    independent_corroborating_source: RubricItem
    observed_impact_measurement: RubricItem

class RubricResult(BaseModel):
    total_score: Optional[int] = None
    confidence_ratio: Optional[float] = None
    score_display: str
    is_synthetic: bool
    eligible_for_score: bool
    breakdown: RubricBreakdown
    missing_items: List[str]
    reviewer_name: Optional[str] = None
    review_timestamp: Optional[datetime] = None
    reason: str

class ImpactRecordBase(BaseModel):
    event_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    exact_time_verified: bool = False
    
    latitude: float
    longitude: float
    zone: str
    location_accuracy_m: Optional[float] = 1000.0
    location_precision_type: Optional[str] = "ward_centroid"
    
    impact_type: str
    severity: str = "moderate"
    severity_evidence: Optional[str] = None
    
    source_name: str
    source_org: Optional[str] = None
    source_url: Optional[str] = None
    source_ref_id: Optional[str] = None
    access_date: Optional[str] = None
    report_page: Optional[str] = None
    exact_passage: Optional[str] = None
    
    corroborating_source_name: Optional[str] = None
    corroborating_source_org: Optional[str] = None
    corroborating_source_url: Optional[str] = None
    
    observed_flood_extent_sqkm: Optional[float] = None
    observed_flood_depth_m: Optional[float] = None
    road_closure_duration_hours: Optional[float] = None
    power_outage_duration_hours: Optional[float] = None
    hospital_access_cut: Optional[bool] = None
    satellite_product: Optional[str] = None
    gauge_level_m: Optional[float] = None
    sensor_gauge_id: Optional[str] = None
    affected_critical_assets: Optional[str] = None
    observed_extent_geojson: Optional[str] = None
    
    evidence_status: str = "unverified"
    confidence: Optional[float] = None
    notes: Optional[str] = None
    
    document_hash: Optional[str] = None
    attachment_filename: Optional[str] = None
    attachment_mime_type: Optional[str] = None
    data_license: Optional[str] = "Open Government Data (OGD) India / Fair Use Research"
    privacy_notes: Optional[str] = None
    
    reviewer_name: Optional[str] = None
    review_timestamp: Optional[datetime] = None
    review_decision: Optional[str] = "pending"
    review_notes: Optional[str] = None

    @field_validator("impact_type")
    @classmethod
    def validate_impact_type(cls, v: str) -> str:
        clean = v.strip().lower()
        if clean not in ALLOWED_IMPACT_TYPES:
            raise ValueError(f"impact_type must be one of {sorted(list(ALLOWED_IMPACT_TYPES))}")
        return clean

    @field_validator("evidence_status")
    @classmethod
    def validate_evidence_status(cls, v: str) -> str:
        clean = v.strip().lower()
        if clean not in ALLOWED_EVIDENCE_STATUSES:
            raise ValueError(f"evidence_status must be one of {sorted(list(ALLOWED_EVIDENCE_STATUSES))}")
        return clean

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        clean = v.strip().lower()
        if clean not in ALLOWED_SEVERITIES:
            raise ValueError(f"severity must be one of {sorted(list(ALLOWED_SEVERITIES))}")
        return clean

    @model_validator(mode="after")
    def require_traceable_source_for_historical_evidence(self):
        if self.evidence_status == "historical_real":
            if not self.source_url:
                raise ValueError("historical_real records require a traceable source_url")
            if not self.source_org:
                raise ValueError("historical_real records require an authoritative source_org (e.g. CWC, IMD, GCC, TNSDMA)")
        return self

class ImpactRecordCreate(ImpactRecordBase):
    pass

class ImpactRecordUpdate(BaseModel):
    end_time: Optional[datetime] = None
    exact_time_verified: Optional[bool] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_accuracy_m: Optional[float] = None
    location_precision_type: Optional[str] = None
    severity: Optional[str] = None
    severity_evidence: Optional[str] = None
    confidence: Optional[float] = None
    notes: Optional[str] = None
    evidence_status: Optional[str] = None
    source_url: Optional[str] = None
    source_org: Optional[str] = None
    report_page: Optional[str] = None
    exact_passage: Optional[str] = None
    corroborating_source_url: Optional[str] = None
    corroborating_source_org: Optional[str] = None
    observed_flood_extent_sqkm: Optional[float] = None
    observed_flood_depth_m: Optional[float] = None
    road_closure_duration_hours: Optional[float] = None
    power_outage_duration_hours: Optional[float] = None
    hospital_access_cut: Optional[bool] = None
    satellite_product: Optional[str] = None
    gauge_level_m: Optional[float] = None
    affected_critical_assets: Optional[str] = None
    reviewer_name: Optional[str] = None
    review_decision: Optional[str] = None
    review_notes: Optional[str] = None

class CuratorReviewSubmission(BaseModel):
    reviewer_name: str = Field(min_length=2)
    decision: str  # approved_historical_real, rejected, under_review, revision_needed
    review_notes: str
    override_confidence: Optional[float] = None

    @field_validator("decision")
    @classmethod
    def validate_decision(cls, v: str) -> str:
        clean = v.strip().lower()
        if clean not in ALLOWED_REVIEW_DECISIONS:
            raise ValueError(f"decision must be one of {sorted(list(ALLOWED_REVIEW_DECISIONS))}")
        return clean

class ImpactRecordResponse(ImpactRecordBase):
    id: int
    created_at: datetime
    rubric: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)

class WarningEvidence(BaseModel):
    """A warning exported from a declared model run for retrospective evaluation."""
    timestamp: datetime
    latitude: float
    longitude: float
    probability: float = Field(ge=0.0, le=1.0)
    model_version: Optional[str] = None
    provenance: str = "model_run"

class ImpactEvaluationRequest(BaseModel):
    start_time: datetime
    end_time: datetime
    spatial_radius_km: float = Field(default=5.0, ge=0.1, le=50.0)
    warning_probability_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    target_impact_type: Optional[str] = None
    target_zone: Optional[str] = None
    warnings: List[WarningEvidence] = Field(default_factory=list)

class ImpactEvaluationResponse(BaseModel):
    status: str  # "EVALUATED" or "INSUFFICIENT_EVIDENCE"
    total_impact_records: int
    eligible_historical_real_records: int
    excluded_synthetic_proxy_records: int
    matched_events_count: int
    event_detection_rate: Optional[float] = None
    false_alarms: Optional[int] = None
    warning_lead_time_hours_mean: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    brier_score: Optional[float] = None
    sample_size_n: int
    sample_size_warning: Optional[str] = None
    evidence_note: str
    provenance: str = "HISTORICAL REAL ONLY MATCHING (Empirical Benchmark)"

class ValidationReadinessResponse(BaseModel):
    hydraulic_2d_validation_ready: bool
    observed_extent_records_count: int
    observed_depth_records_count: int
    gauge_measurement_records_count: int
    total_historical_real_count: int
    total_under_review_count: int
    total_synthetic_count: int
    limitation_warning: str
    next_action_recommendation: str

class ObservedFloodPoint(BaseModel):
    latitude: float
    longitude: float
    observed_depth_m: float
    location_name: Optional[str] = None

class ObservedFloodValidationRequest(BaseModel):
    event_id: str
    scenario_model_id: str = "copernicus_glo30_scenario_v1"
    predicted_flood_extent_sqkm: float = Field(ge=0.0)
    predicted_depth_points: Optional[List[Dict[str, float]]] = None
    observed_extent_sqkm: Optional[float] = None
    sar_product: Optional[str] = None
    observed_depth_points: List[ObservedFloodPoint] = Field(default_factory=list)
    gauge_level_m: Optional[float] = None

class ObservedFloodValidationResponse(BaseModel):
    event_id: str
    validation_status: str  # "UNVALIDATED_SCENARIO_PROXY" or "PRELIMINARY_SURVEY_VALIDATED" or "CALIBRATED_2D_VALIDATED"
    is_hydraulically_calibrated: bool
    spatial_iou: Optional[float] = None
    spatial_csi: Optional[float] = None
    depth_rmse_m: Optional[float] = None
    depth_mae_m: Optional[float] = None
    sample_depth_points_n: int
    sar_product_used: Optional[str] = None
    limitation_disclaimer: str
    provenance_badge: str

