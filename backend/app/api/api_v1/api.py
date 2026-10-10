from fastapi import APIRouter

from app.api.api_v1.endpoints import (
    assets,
    sensors,
    sensor_readings,
    weather,
    hazards,
    digital_twins,
    predictions,
    risk,
    alerts,
    historical_events,
    metrics,
    replay,
    control,
    what_if,
    auth,
    users,
    assistant,
    spatial,
    data_quality,
    decision_support,
    external_hazards,
    explainability,
    ai,
    model_monitoring,
    cascade
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["User Management"])
api_router.include_router(assets.router, prefix="/assets", tags=["Assets"])
api_router.include_router(sensors.router, prefix="/sensors", tags=["Sensors"])
api_router.include_router(sensor_readings.router, prefix="/sensor-readings", tags=["Sensor Readings"])
api_router.include_router(weather.router, prefix="/weather", tags=["Weather"])
api_router.include_router(hazards.router, prefix="/hazards", tags=["Hazards"])
api_router.include_router(digital_twins.router, prefix="/digital-twins", tags=["Digital Twins"])
api_router.include_router(predictions.router, prefix="/predictions", tags=["Predictions"])
api_router.include_router(risk.router, prefix="/risk", tags=["Risk"])
api_router.include_router(spatial.router, prefix="/spatial", tags=["Spatial Inundation & Impact"])
api_router.include_router(data_quality.router, prefix="/data-quality", tags=["Data Quality & Sensor Health"])
api_router.include_router(decision_support.router, prefix="/decision-support", tags=["Decision Support & Policy Engine"])
api_router.include_router(external_hazards.router, prefix="/external-hazards", tags=["External High-Res Hazard Data"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
api_router.include_router(historical_events.router, prefix="/historical-events", tags=["Historical Events"])
api_router.include_router(metrics.router, prefix="/metrics", tags=["System Metrics"])
api_router.include_router(replay.router, prefix="/replay", tags=["Historical Replay"])
api_router.include_router(control.router, prefix="/control", tags=["Control Actuation"])
api_router.include_router(what_if.router, prefix="/what-if", tags=["What-If Simulator"])
api_router.include_router(cascade.router, prefix="/cascade", tags=["Causal Cascade"])
api_router.include_router(assistant.router, prefix="/assistant", tags=["AI Assistant"])
api_router.include_router(explainability.router, prefix="/explainability", tags=["Explainable AI"])
api_router.include_router(ai.router, prefix="/ai", tags=["AI Intelligence"])
api_router.include_router(model_monitoring.router, prefix="/model-health", tags=["Model Drift & Monitoring"])
