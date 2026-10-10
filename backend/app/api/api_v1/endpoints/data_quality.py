"""
Data Quality & Sensor Health REST API Endpoints (Phase 16)
ClimateTwin Chennai Project
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from app.core.sensor_health import sensor_health_engine, SOURCE_CATALOG

router = APIRouter()

class QualityCheckRequest(BaseModel):
    source_id: str = Field(..., description="Telemetry source identifier")
    variable: str = Field(..., description="Observed variable name")
    value: float = Field(..., description="Observed measurement value")
    data_age_min: Optional[float] = Field(15.0, description="Elapsed observation age in minutes")

class SimulateFailureRequest(BaseModel):
    scenario_id: str = Field(..., description="Synthetic failure scenario key (e.g., SCENARIO_1_MISSING_SENSOR, SCENARIO_8_RECOVERY_NOMINAL)")

@router.get("/summary")
def get_data_quality_summary():
    """
    Returns aggregate city-wide sensor health, telemetry quality scores, and source counts.
    """
    return sensor_health_engine.get_summary()

@router.get("/sources")
def get_all_sources():
    """
    Returns list of all 8 monitored environmental telemetry sources with diagnostic health metrics.
    """
    summary = sensor_health_engine.get_summary()
    return {
        "status": "success",
        "count": len(summary["sources"]),
        "sources": summary["sources"]
    }

@router.get("/anomalies")
def get_anomaly_feed(limit: int = Query(20, ge=1, le=100)):
    """
    Returns real-time chronological sensor anomaly event feed and failure audit trail.
    """
    feed = sensor_health_engine.anomaly_feed[:limit]
    return {
        "status": "success",
        "total_events": len(sensor_health_engine.anomaly_feed),
        "events": feed
    }

@router.get("/sources/{source_id}")
def get_source_detail(source_id: str):
    """
    Returns granular health, plausibility, and consistency metrics for a specific source.
    """
    src = next((s for s in SOURCE_CATALOG if s["source_id"] == source_id), None)
    if not src:
        raise HTTPException(status_code=404, detail=f"Telemetry source '{source_id}' not found.")
    return sensor_health_engine.evaluate_source(src)

@router.post("/check")
def check_observation_quality(payload: QualityCheckRequest):
    """
    Validates physical plausibility, temporal innovation, and quality tier for incoming observation.
    """
    src = next((s for s in SOURCE_CATALOG if s["source_id"] == payload.source_id), None)
    if not src:
        # Fallback pseudo source
        src = {
            "source_id": payload.source_id,
            "name": f"Custom Stream ({payload.source_id})",
            "source_type": "SYNTHETIC_CUSTOM",
            "variables": [payload.variable],
            "reporting_interval_minutes": 30,
            "stale_threshold_minutes": 120,
            "nominal_value": {payload.variable: payload.value}
        }
    
    eval_res = sensor_health_engine.evaluate_source(
        src,
        sim_override={"value": payload.value, "data_age_min": payload.data_age_min}
    )
    return {
        "status": "success",
        "evaluated_observation": payload.model_dump(),
        "quality_result": eval_res
    }

@router.post("/simulate-failure")
def simulate_sensor_failure(payload: SimulateFailureRequest):
    """
    Triggers controlled synthetic telemetry failure benchmarks (Phase 16 Testing).
    """
    return sensor_health_engine.simulate_failure_scenario(payload.scenario_id)
