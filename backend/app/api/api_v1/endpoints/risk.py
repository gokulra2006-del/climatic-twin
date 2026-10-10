from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.models.risk import RiskAssessment, DigitalTwinState
from app.schemas.other import RiskResponse
from app.schemas.common import PaginatedResponse

router = APIRouter()

@router.get("/", response_model=PaginatedResponse[RiskResponse])
def get_risks(
    db: Session = Depends(deps.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    if db is not None:
        try:
            query = db.query(RiskAssessment)
            total = query.count()
            risks = query.offset(skip).limit(limit).all()
            return {"data": risks, "total": total, "page": skip // limit + 1 if limit > 0 else 1, "page_size": limit, "total_pages": (total + limit - 1) // limit if limit > 0 else 0}
        except Exception:
            pass
    return {"data": [], "total": 0, "page": 1, "page_size": limit, "total_pages": 0}

@router.get("/{asset_id}", response_model=RiskResponse)
def get_risk_by_asset(asset_id: int, db: Session = Depends(deps.get_db)):
    if db is not None:
        try:
            risk = db.query(RiskAssessment).join(DigitalTwinState).filter(DigitalTwinState.asset_id == asset_id).order_by(RiskAssessment.timestamp.desc()).first()
            if risk:
                return risk
        except Exception:
            pass
    raise HTTPException(status_code=404, detail="Risk assessment not found for asset")


@router.get("/history/{asset_id}", response_model=PaginatedResponse[RiskResponse])
def get_risk_history_by_asset(
    asset_id: int, 
    db: Session = Depends(deps.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    query = db.query(RiskAssessment).join(DigitalTwinState).filter(DigitalTwinState.asset_id == asset_id).order_by(RiskAssessment.timestamp.desc())
    total = query.count()
    risks = query.offset(skip).limit(limit).all()
    return {"data": risks, "total": total, "page": skip // limit + 1 if limit > 0 else 1, "page_size": limit, "total_pages": (total + limit - 1) // limit if limit > 0 else 0}

@router.post("/multihazard")
def compute_multihazard_risk(payload: dict = None):
    """
    Evaluates multi-hazard states, non-linear interactions, compound risk (CRS),
    and causal cascading dynamics from assimilated environmental telemetry.
    """
    from app.core.multihazard import multihazard_engine
    env_state = payload or {
        'rainfall_daily': 35.0,
        'rainfall_rate_1h': 3.5,
        'total_reservoir_level': 5800.0,
        'reservoir_fill_ratio': 0.515,
        'temp_max': 31.0,
        'dew_point_mean': 23.5,
        'wind_speed_mean': 6.0,
        'elevation_m': 8.0
    }
    flood_prob = float(env_state.get('flood_probability', 0.25))
    return multihazard_engine.calculate_compound_risk(env_state, flood_prob)

@router.get("/multihazard/scenarios")
def get_multihazard_scenarios():
    """
    Returns verified controlled benchmark scenario simulations (A, B, C, D).
    """
    from app.core.multihazard import multihazard_engine
    return {
        'scenarios': [
            multihazard_engine.simulate_scenario('SCENARIO_A_NOMINAL'),
            multihazard_engine.simulate_scenario('SCENARIO_B_HEAVY_RAIN'),
            multihazard_engine.simulate_scenario('SCENARIO_C_RAIN_PLUS_FULL_RESERVOIR'),
            multihazard_engine.simulate_scenario('SCENARIO_D_EXTREME_CYCLONIC_DELUGE')
        ]
    }

@router.get("/multihazard/sensitivity")
def get_multihazard_sensitivity():
    """
    Returns environmental driver sensitivity analysis and interaction coupling matrix.
    """
    from app.core.multihazard import multihazard_engine
    return multihazard_engine.perform_sensitivity_analysis()

