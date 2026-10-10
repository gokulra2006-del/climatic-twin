"""
Model Drift, Performance Monitoring & Retraining Intelligence REST API Endpoints (Phase Next)
ClimateTwin Chennai Project
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from app.core.model_monitoring import model_monitoring_engine

router = APIRouter()


class EvaluateLiveTelemetryRequest(BaseModel):
    observations: Optional[List[Dict[str, Any]]] = Field(None, description="List of custom observations to record & evaluate")
    window: Optional[str] = Field("7d", description="Temporal evaluation window ('24h', '7d', '30d')")
    verified_labels: Optional[List[int]] = Field(None, description="Optional ground-truth binary flood labels for verified performance check")
    verified_preds: Optional[List[float]] = Field(None, description="Optional model predicted probabilities corresponding to verified labels")


@router.get("")
@router.get("/")
def get_model_health_overview(window: str = Query("7d", pattern="^(24h|7d|30d)$")):
    """
    Returns comprehensive model health status including feature drift, prediction drift,
    uncertainty trend, sensor data quality, temporal windows, and NOVA AI summary.
    """
    return model_monitoring_engine.get_comprehensive_model_health(window_str=window)


@router.get("/drift")
def get_drift_details(window: str = Query("7d", pattern="^(24h|7d|30d)$")):
    """
    Returns granular feature drift metrics (PSI, KS-statistic, Wasserstein distance)
    and prediction distribution drift across historical training vs recent live observations.
    """
    f_drift = model_monitoring_engine.evaluate_feature_drift(window_str=window)
    p_drift = model_monitoring_engine.evaluate_prediction_drift(window_str=window)
    t_drift = model_monitoring_engine.evaluate_temporal_drift()
    
    return {
        "status": "success",
        "window": window,
        "feature_drift": f_drift,
        "prediction_drift": p_drift,
        "temporal_drift": t_drift
    }


@router.get("/performance")
def get_model_performance():
    """
    Returns model validation metrics comparing historical training/validation baseline
    against latest verified post-event evaluations.
    """
    perf = model_monitoring_engine.evaluate_verified_performance()
    concept = model_monitoring_engine.evaluate_concept_drift()
    
    return {
        "status": "success",
        "champion_model": model_monitoring_engine.champion_metadata,
        "candidate_model": model_monitoring_engine.candidate_metadata,
        "performance": perf,
        "concept_drift": concept
    }


@router.get("/history")
def get_drift_history(limit: int = Query(30, ge=1, le=100)):
    """
    Returns historical drift monitoring timeline observations for longitudinal tracking.
    """
    buffer_records = model_monitoring_engine.live_buffer[-limit:]
    timeline = []
    
    for r in buffer_records:
        timeline.append({
            "timestamp": r.get("timestamp"),
            "rainfall_7d_sum": r.get("rainfall_7d_sum", 0.0),
            "predicted_probability": r.get("predicted_probability", 0.0),
            "epistemic_variance": r.get("epistemic_variance", 0.0),
            "uncertainty_level": r.get("uncertainty_level", "LOW")
        })
        
    return {
        "status": "success",
        "total_records": len(timeline),
        "timeline": timeline
    }


@router.get("/retraining-readiness")
def get_retraining_readiness(window: str = Query("7d", pattern="^(24h|7d|30d)$")):
    """
    Returns Retraining Readiness Score (0-100), transparent decision reasoning,
    and gating state based on sensor data quality and distribution persistence.
    """
    f_drift = model_monitoring_engine.evaluate_feature_drift(window_str=window)
    p_drift = model_monitoring_engine.evaluate_prediction_drift(window_str=window)
    u_drift = model_monitoring_engine.evaluate_uncertainty_drift(window_str=window)
    dq_eval = model_monitoring_engine.evaluate_data_quality()
    t_drift = model_monitoring_engine.evaluate_temporal_drift()
    perf_eval = model_monitoring_engine.evaluate_verified_performance()
    
    readiness = model_monitoring_engine.compute_retraining_readiness(
        f_drift, p_drift, u_drift, dq_eval, t_drift, perf_eval
    )
    
    return {
        "status": "success",
        "readiness": readiness,
        "champion_version": model_monitoring_engine.champion_version,
        "candidate_version": model_monitoring_engine.candidate_version
    }


@router.post("/evaluate")
def evaluate_custom_telemetry(payload: EvaluateLiveTelemetryRequest):
    """
    Injects custom live observation vectors or verified labels and returns immediate
    re-evaluation of drift, data quality gating, and retraining readiness.
    """
    if payload.observations:
        for obs in payload.observations:
            model_monitoring_engine.record_live_observation(obs)
            
    f_drift = model_monitoring_engine.evaluate_feature_drift(window_str=payload.window)
    p_drift = model_monitoring_engine.evaluate_prediction_drift(window_str=payload.window)
    u_drift = model_monitoring_engine.evaluate_uncertainty_drift(window_str=payload.window)
    dq_eval = model_monitoring_engine.evaluate_data_quality()
    t_drift = model_monitoring_engine.evaluate_temporal_drift()
    
    perf_eval = model_monitoring_engine.evaluate_verified_performance(
        verified_labels=payload.verified_labels,
        verified_preds=payload.verified_preds
    )
    
    readiness = model_monitoring_engine.compute_retraining_readiness(
        f_drift, p_drift, u_drift, dq_eval, t_drift, perf_eval
    )
    
    overall_status = readiness["model_status"]
    nova = model_monitoring_engine.generate_nova_health_summary(
        overall_status, readiness, t_drift, u_drift, dq_eval
    )
    
    return {
        "status": "success",
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "model_status": overall_status,
        "retraining_readiness": readiness,
        "feature_drift": f_drift,
        "prediction_drift": p_drift,
        "uncertainty_trend": u_drift,
        "data_quality": dq_eval,
        "temporal_drift": t_drift,
        "verified_performance": perf_eval,
        "nova_summary": nova
    }
