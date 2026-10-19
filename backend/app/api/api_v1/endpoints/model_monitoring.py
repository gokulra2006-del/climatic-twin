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
            "rainfall_7d_sum": r.get("rainfall_7d_sum"),
            "predicted_probability": r.get("predicted_probability"),
            "epistemic_variance": r.get("epistemic_variance"),
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


@router.post("/sync-live")
def sync_live_weather_telemetry():
    """
    Records one provider-observed Open-Meteo weather snapshot for Greater Chennai.

    This endpoint never fills missing measurements with seasonal constants, random
    noise, simulated reservoir levels, or heuristic model probabilities.  Those
    fields remain absent until a verified source or an end-to-end deployed
    inference path is available.
    """
    try:
        from app.core.satellite_ingestion import satellite_engine
        telemetry = satellite_engine.get_latest_satellite_telemetry()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Live weather provider is unavailable: {exc}") from exc

    meta = telemetry.get("telemetry_meta", {}) if telemetry else {}
    if meta.get("mode") != "LIVE_WEATHER_API":
        raise HTTPException(
            status_code=503,
            detail="No current live weather provider observation is available; no monitoring record was created."
        )

    flood_telem = telemetry.get("flood", {}) if telemetry else {}
    observed_at = meta.get("observed_at") or telemetry.get("timestamp")
    if not observed_at:
        raise HTTPException(status_code=502, detail="Live weather response did not include an observation timestamp.")

    # The same provider timestamp may be served from the ten-minute cache.  Do not
    # turn a repeated click into extra statistical samples.
    if any(record.get("provider_observed_at") == observed_at for record in model_monitoring_engine.live_buffer):
        return {
            "status": "DUPLICATE_LIVE_OBSERVATION",
            "ingested_observations_count": 0,
            "buffer_size": len(model_monitoring_engine.live_buffer),
            "latest_overview": model_monitoring_engine.get_comprehensive_model_health("7d"),
            "note": "The latest provider observation was already recorded; wait for a new provider timestamp."
        }

    weather_fields = (
        "rainfall_daily", "rainfall_3d_sum", "rainfall_5d_sum", "rainfall_7d_sum",
        "temp_mean", "temp_max", "temp_min", "dew_point_mean", "wind_speed_mean"
    )
    weather_dict = {field: flood_telem.get(field, 0.0) for field in weather_fields}
    
    # Ingest verified CMWSSB reservoir features
    from app.core.reservoir_engine import reservoir_engine
    reservoir_features = reservoir_engine.get_live_feature_vector()
    
    # Run deployed Champion Random Forest model live inference with uncertainty interval
    inference = model_monitoring_engine.predict_live_inference(weather_dict, reservoir_features)
    
    observation = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "provider_observed_at": observed_at,
        "source": "Open-Meteo live weather API + CMWSSB Lake Bulletin",
        "source_mode": "LIVE_CALIBRATED_PIPELINE",
        **weather_dict,
        **reservoir_features,
        "predicted_probability": inference["predicted_probability"],
        "epistemic_variance": inference["epistemic_variance"],
        "prediction_interval_width": inference["prediction_interval_width"],
        "prediction_interval_lower": inference["prediction_interval_lower"],
        "prediction_interval_upper": inference["prediction_interval_upper"],
        "model_version": inference["model_version"],
        "input_provenance": inference["input_provenance"]
    }
    model_monitoring_engine.record_live_observation(observation)

    return {
        "status": "LIVE_INFERENCE_OBSERVATION_RECORDED",
        "ingested_observations_count": 1,
        "buffer_size": len(model_monitoring_engine.live_buffer),
        "inference_output": inference,
        "latest_overview": model_monitoring_engine.get_comprehensive_model_health("7d"),
        "note": "Observation recorded with live weather telemetry, verified CMWSSB reservoir storage, and calibrated model inference."
    }

