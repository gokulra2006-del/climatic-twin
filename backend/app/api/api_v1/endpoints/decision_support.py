"""
Decision Support & Adaptive Early-Warning Policy REST API Endpoints (Phase 17)
ClimateTwin Chennai Project

SCIENTIFIC TRANSPARENCY:
- Decision Support Score (DSS) uses PROTOTYPE weights requiring domain-expert calibration.
- Operational actions are RECOMMENDATIONS, not autonomous emergency commands.
- Synthetic benchmark scenarios are labeled SIMULATED DECISION-SUPPORT BENCHMARK.
- This system is DECISION SUPPORT, not an autonomous emergency authority.
- All outputs are RULE-BASED and DERIVED from upstream phase outputs.
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.decision_support import decision_engine
from app.core.action_tracker import action_tracker

router = APIRouter()


class DecisionAssessRequest(BaseModel):
    """
    Request model for custom decision assessment scenario.
    All fields are optional with standard baseline defaults.
    """
    flood_probability: Optional[float] = Field(0.10, description="Predicted flood probability [0.0 - 1.0]")
    uncertainty_level: Optional[str] = Field("LOW", description="Forecast uncertainty tier (LOW, MODERATE, HIGH)")
    uncertainty_width: Optional[float] = Field(0.15, description="90% prediction interval width [0.0 - 1.0]")
    epistemic_variance: Optional[float] = Field(0.01, description="Model epistemic uncertainty variance")
    compound_risk_score: Optional[float] = Field(0.15, description="Compound multi-hazard risk score [0.0 - 1.0]")
    compound_risk_level: Optional[str] = Field("LOW", description="Compound risk classification level")
    dominant_hazard: Optional[str] = Field("FLOOD_INUNDATION", description="Dominant hazard identifier")
    dominant_hazard_intensity: Optional[float] = Field(0.10, description="Dominant hazard severity intensity [0.0 - 1.0]")
    max_asset_risk_index: Optional[float] = Field(0.30, description="Maximum asset risk index among monitored infrastructure")
    mean_criticality_weight: Optional[float] = Field(0.50, description="Mean criticality weight of exposed assets")
    max_exposure_score: Optional[float] = Field(0.30, description="Maximum exposure score across city assets")
    aggregate_shs: Optional[float] = Field(0.95, description="Aggregate sensor health score [0.0 - 1.0]")
    num_degraded: Optional[int] = Field(0, description="Count of degraded/stale telemetry sources")
    num_anomalous: Optional[int] = Field(0, description="Count of anomalous telemetry observations")
    num_missing: Optional[int] = Field(0, description="Count of missing/offline telemetry sources")
    consecutive_elevated_cycles: Optional[int] = Field(0, description="Number of consecutive cycles above alert threshold")
    trend_direction: Optional[str] = Field("STABLE", description="Risk trend trajectory: RISING, STABLE, FALLING")
    forecast_horizon: Optional[str] = Field("current", description="Forecast horizon label (e.g. current, +1h, +6h)")
    active_interactions: Optional[List[str]] = Field(None, description="Active multi-hazard compounding interactions")
    source_health_states: Optional[List[str]] = Field(None, description="Health states list across monitored telemetry sources")
    asset_details: Optional[List[Dict[str, Any]]] = Field(None, description="List of granular asset objects for priority evaluation")


class ActionUpdateRequest(BaseModel):
    status: str = Field(..., description="suggested, acknowledged, in_progress, completed, effective, ineffective")
    reviewer_name: str = Field(..., description="Name and designation of the responding officer")
    effectiveness_rating: Optional[str] = Field(None, description="HIGHLY_EFFECTIVE, MODERATELY_EFFECTIVE, INEFFECTIVE, PENDING_ASSESSMENT")
    outcome_evidence: Optional[str] = Field(None, description="Measurable outcome description or sensor verification")
    verified_source_url: Optional[str] = Field(None, description="Official report/log URL")
    notes: Optional[str] = Field(None, description="Operational notes")


class ActionCreateRequest(BaseModel):
    action_type: str
    title_en: str
    title_ta: Optional[str] = ""
    target_location: str
    zone: str
    latitude: float
    longitude: float
    department: str
    urgency: str = "HIGH"
    suggested_by: str = "NOVA Decision Intelligence"
    verified_source_url: Optional[str] = None
    notes: Optional[str] = None


@router.get("/current")
def get_current_decision_state():
    """
    Returns current city-wide decision state, DSS score breakdown,
    data quality gate status, escalation posture, and recommended actions.
    """
    return decision_engine.assess()


@router.post("/assess")
def assess_custom_scenario(payload: DecisionAssessRequest):
    """
    Custom scenario assessment. Evaluates Decision Support Score (DSS),
    decision level, data quality gate, uncertainty modifier, and recommended actions
    for user-specified or what-if scenario parameters.
    """
    params = payload.model_dump()
    return decision_engine.assess(**params)


@router.get("/policy")
def get_decision_policy():
    """
    Returns complete transparent rule-based policy configuration including DSS weights,
    decision level thresholds, uncertainty decision matrix, data quality gate thresholds,
    and research disclaimers.
    """
    return decision_engine.get_policy()


@router.get("/scenarios")
def get_benchmark_scenarios():
    """
    Executes and returns the full suite of research-grade synthetic benchmark scenarios
    (Scenarios A through H) evaluating adaptive decision support behavior under varied conditions.
    """
    scenarios = decision_engine.run_benchmark_scenarios()
    return {
        "scenarios": scenarios,
        "label": "SIMULATED DECISION-SUPPORT BENCHMARK"
    }


@router.get("/priority")
def get_priority_assets():
    """
    Returns prioritized critical infrastructure assets, current city-wide decision level,
    and decision score under baseline telemetry.
    """
    result = decision_engine.assess()
    return {
        "priority_assets": result["affected_assets"],
        "decision_level": result["decision_level"],
        "decision_score": result["decision_score"]
    }


# =========================================================================
# ACTION EFFECTIVENESS TRACKER ENDPOINTS
# =========================================================================

@router.get("/actions")
def list_actions(
    status: Optional[str] = None,
    department: Optional[str] = None,
    action_type: Optional[str] = None
):
    """
    Retrieves operational interventions suggested by NOVA with lifecycle status,
    response times, agency acknowledgment, and field outcome evidence.
    """
    actions = action_tracker.list_actions(status=status, department=department, action_type=action_type)
    return {
        "status": "success",
        "count": len(actions),
        "actions": actions
    }


@router.get("/actions/summary")
def get_action_effectiveness_summary():
    """
    Returns high-level effectiveness rate, average response latency,
    and department-level operational dispatch metrics.
    """
    return {
        "status": "success",
        "summary": action_tracker.get_summary()
    }


@router.post("/actions")
def create_action(payload: ActionCreateRequest):
    """
    Dispatches a new suggested operational action to municipal responders.
    """
    record = action_tracker.create_action(payload.model_dump())
    return {
        "status": "success",
        "action": record
    }


@router.post("/actions/{action_id}/update")
def update_action_lifecycle(action_id: str, payload: ActionUpdateRequest):
    """
    Updates the execution status and outcome verification of an intervention
    (e.g., Acknowledged, Completed, Effective).
    """
    try:
        updated = action_tracker.update_action(
            action_id=action_id,
            status=payload.status,
            reviewer_name=payload.reviewer_name,
            effectiveness_rating=payload.effectiveness_rating,
            outcome_evidence=payload.outcome_evidence,
            verified_source_url=payload.verified_source_url,
            notes=payload.notes
        )
        return {"status": "success", "action": updated}
    except ValueError as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=str(e))
