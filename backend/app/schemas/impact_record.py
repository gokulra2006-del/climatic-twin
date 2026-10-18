from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List
from datetime import datetime

ALLOWED_IMPACT_TYPES = {
    "waterlogging",
    "road_closure",
    "flood_extent",
    "reservoir_overflow",
    "power_outage",
    "hospital_access_disruption",
    "drainage_failure"
}

ALLOWED_EVIDENCE_STATUSES = {
    "historical_real",
    "proxy",
    "synthetic",
    "unverified"
}

ALLOWED_SEVERITIES = {"low", "moderate", "high", "critical"}

class ImpactRecordBase(BaseModel):
    event_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    latitude: float
    longitude: float
    zone: str
    impact_type: str
    severity: str = "moderate"
    source_name: str
    source_url: Optional[str] = None
    evidence_status: str = "proxy"
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    notes: Optional[str] = None

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
        if self.evidence_status == "historical_real" and not self.source_url:
            raise ValueError("historical_real records require a traceable source_url")
        return self

class ImpactRecordCreate(ImpactRecordBase):
    pass

class ImpactRecordUpdate(BaseModel):
    end_time: Optional[datetime] = None
    severity: Optional[str] = None
    confidence: Optional[float] = None
    notes: Optional[str] = None
    evidence_status: Optional[str] = None

class ImpactRecordResponse(ImpactRecordBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class ImpactEvaluationRequest(BaseModel):
    start_time: datetime
    end_time: datetime
    spatial_radius_km: float = Field(default=5.0, ge=0.1, le=50.0)
    warning_probability_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    target_impact_type: Optional[str] = None
    target_zone: Optional[str] = None
    warnings: List["WarningEvidence"] = Field(default_factory=list)


class WarningEvidence(BaseModel):
    """A warning exported from a declared model run for retrospective evaluation."""
    timestamp: datetime
    latitude: float
    longitude: float
    probability: float = Field(ge=0.0, le=1.0)
    model_version: Optional[str] = None
    provenance: str = "model_run"

class ImpactEvaluationResponse(BaseModel):
    status: str  # "EVALUATED" or "INSUFFICIENT_EVIDENCE"
    total_impact_records: int
    matched_events_count: int
    event_detection_rate: Optional[float] = None
    false_alarms: Optional[int] = None
    warning_lead_time_hours_mean: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    evidence_note: str
    provenance: str = "HISTORICAL REAL & PROXY MATCHING"
