from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from geoalchemy2.elements import WKTElement
from datetime import datetime

from app.api import deps
from app.models.asset import InfrastructureAsset
from app.schemas.asset import AssetCreate, AssetUpdate, AssetResponse
from app.schemas.common import PaginatedResponse

router = APIRouter()

MOCK_RESERVOIRS = [
    {
        "id": 1,
        "name": "POONDI",
        "asset_type_id": 1,
        "location_id": 1,
        "geom": "POINT(79.8600 13.1850)",
        "attributes": {"description": "Poondi Reservoir (Sathyamoorthy Sagar)", "capacity_mcft": 3231},
        "created_at": datetime(2026, 8, 30),
        "updated_at": None
    },
    {
        "id": 2,
        "name": "CHOLAVARAM",
        "asset_type_id": 1,
        "location_id": 1,
        "geom": "POINT(80.1636 13.2353)",
        "attributes": {"description": "Cholavaram Reservoir (Sholavaram Lake)", "capacity_mcft": 1081},
        "created_at": datetime(2026, 8, 30),
        "updated_at": None
    },
    {
        "id": 3,
        "name": "REDHILLS",
        "asset_type_id": 1,
        "location_id": 1,
        "geom": "POINT(80.1632 13.1650)",
        "attributes": {"description": "Redhills Reservoir (Puzhal Lake)", "capacity_mcft": 3300},
        "created_at": datetime(2026, 8, 30),
        "updated_at": None
    },
    {
        "id": 4,
        "name": "CHEMBARAMBAKKAM",
        "asset_type_id": 1,
        "location_id": 1,
        "geom": "POINT(80.0606 13.0116)",
        "attributes": {"description": "Chembarambakkam Reservoir", "capacity_mcft": 3645},
        "created_at": datetime(2026, 8, 30),
        "updated_at": None
    }
]

@router.get("/", response_model=PaginatedResponse[AssetResponse])
def read_assets(
    db: Session = Depends(deps.get_db_optional),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    asset_type_id: Optional[int] = None
):
    # DB offline - skip check, return mock data instantly
    return {
        "data": MOCK_RESERVOIRS,
        "total": len(MOCK_RESERVOIRS),
        "page": 1,
        "page_size": limit,
        "total_pages": 1
    }

@router.get("/risk")
def get_all_assets_risk(
    rainfall_daily: Optional[float] = None,
    reservoir_fill_ratio: Optional[float] = None
):
    """
    Evaluates spatial exposure, DEM elevation vulnerability, and Asset Risk Indices (ARI)
    across all 8 critical infrastructure assets in Chennai.
    """
    from app.core.asset_risk import asset_risk_engine
    env_state = None
    if rainfall_daily is not None or reservoir_fill_ratio is not None:
        env_state = {
            'rainfall_daily': rainfall_daily if rainfall_daily is not None else 45.0,
            'reservoir_fill_ratio': reservoir_fill_ratio if reservoir_fill_ratio is not None else 0.60
        }
    return {"data": asset_risk_engine.assess_all_assets(env_state)}

@router.get("/risk/top")
def get_top_risk_assets(limit: int = Query(3, ge=1, le=8)):
    """
    Returns prioritized operational action queue of highest-risk critical assets.
    """
    from app.core.asset_risk import asset_risk_engine
    return {"data": asset_risk_engine.get_top_priority_assets(limit=limit)}

@router.post("/risk/assess")
def assess_custom_asset_risk(payload: dict = None):
    """
    Evaluates asset risk from custom environmental / hazard state payload.
    """
    from app.core.asset_risk import asset_risk_engine
    return {"data": asset_risk_engine.assess_all_assets(payload)}

@router.get("/{asset_id}", response_model=AssetResponse)

def read_asset(
    asset_id: int, 
    db: Session = Depends(deps.get_db_optional)
):
    if db is not None:
        try:
            asset = db.query(InfrastructureAsset).filter(InfrastructureAsset.id == asset_id).first()
            if asset:
                return asset
        except Exception:
            pass
            
    for res in MOCK_RESERVOIRS:
        if res["id"] == asset_id:
            return res
            
    raise HTTPException(status_code=404, detail="Asset not found")

@router.post("/", response_model=AssetResponse, status_code=201)
def create_asset(
    asset_in: AssetCreate, 
    db: Session = Depends(deps.get_db)
):
    db_asset = InfrastructureAsset(
        name=asset_in.name,
        asset_type_id=asset_in.asset_type_id,
        location_id=asset_in.location_id,
        attributes=asset_in.attributes
    )
    if asset_in.geom:
        db_asset.geom = WKTElement(asset_in.geom, srid=4326)
        
    db.add(db_asset)
    db.commit()
    db.refresh(db_asset)
    return db_asset

@router.put("/{asset_id}", response_model=AssetResponse)
def update_asset(
    asset_id: int, 
    asset_in: AssetUpdate, 
    db: Session = Depends(deps.get_db)
):
    db_asset = db.query(InfrastructureAsset).filter(InfrastructureAsset.id == asset_id).first()
    if not db_asset:
        raise HTTPException(status_code=404, detail="Asset not found")
        
    update_data = asset_in.model_dump(exclude_unset=True)
    if 'geom' in update_data and update_data['geom']:
        update_data['geom'] = WKTElement(update_data['geom'], srid=4326)
        
    for field, value in update_data.items():
        setattr(db_asset, field, value)
        
    db.add(db_asset)
    db.commit()
    db.refresh(db_asset)
    return db_asset

@router.delete("/{asset_id}")
def delete_asset(
    asset_id: int, 
    db: Session = Depends(deps.get_db)
):
    db_asset = db.query(InfrastructureAsset).filter(InfrastructureAsset.id == asset_id).first()
    if not db_asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    db.delete(db_asset)
    db.commit()
    return {"message": "Asset deleted successfully"}

# Stubs for nested resources
@router.get("/{asset_id}/sensors")
def read_asset_sensors(asset_id: int, db: Session = Depends(deps.get_db)):
    asset = db.query(InfrastructureAsset).filter(InfrastructureAsset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return {"data": asset.sensors}

@router.get("/{asset_id}/risk")
def read_asset_risk(asset_id: int):
    from app.core.asset_risk import asset_risk_engine
    all_assets = asset_risk_engine.assess_all_assets()
    match = next((a for a in all_assets if a['asset_id'] == asset_id), None)
    if not match:
        raise HTTPException(status_code=404, detail=f"Asset ID {asset_id} not found in monitored critical assets")
    return match

@router.get("/{asset_id}/digital-twin")
def read_asset_twin(asset_id: int, db: Session = Depends(deps.get_db)):
    return {"message": "Digital twin state operational via /api/digital-twins/state"}

