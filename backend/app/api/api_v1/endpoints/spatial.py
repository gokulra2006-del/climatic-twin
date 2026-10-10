"""
Spatial Inundation & Impact Mapping REST API Endpoints (Phase 15)
ClimateTwin Chennai Project
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from app.core.spatial_inundation import spatial_inundation_engine, SPATIAL_ZONES

router = APIRouter()

class SpatialAssessRequest(BaseModel):
    rainfall_daily: Optional[float] = Field(35.0, description="Daily rainfall in mm")
    runoff_indicator: Optional[float] = Field(0.30, description="Surface runoff indicator [0.0, 1.0]")
    flood_probability: Optional[float] = Field(0.28, description="ML flood probability [0.0, 1.0]")
    reservoir_fill_ratio: Optional[float] = Field(0.65, description="Aggregate reservoir fill ratio [0.0, 1.0]")

@router.get("/flood-risk")
def get_spatial_flood_risk():
    """
    Returns spatial flood susceptibility and impact zones across Greater Chennai.
    """
    zones = spatial_inundation_engine.assess_all_zones()
    return {
        "status": "success",
        "catchment_area": "Greater Chennai Metropolitan Area",
        "zone_count": len(zones),
        "zones": zones,
        "data_provenance": {
            "source_type": "DERIVED_SUSCEPTIBILITY_INDEX",
            "dem_source": "Copernicus DEM GLO-30 (30m)",
            "rainfall_source": "NASA GPM IMERG V07B (0.1 deg)",
            "runoff_source": "ERA5-Land",
            "depth_status": "NOT DIRECTLY OBSERVED (Relative Proxy)"
        }
    }

@router.get("/flood-impact")
def get_spatial_flood_impact():
    """
    Returns current spatial flood impact summary and top priority impacted zones.
    """
    zones = spatial_inundation_engine.assess_all_zones()
    top_zones = zones[:3]
    mean_sfii = sum(z['spatial_flood_impact_index'] for z in zones) / len(zones)
    return {
        "status": "success",
        "mean_spatial_flood_impact_index": round(mean_sfii, 3),
        "city_wide_inundation_severity": spatial_inundation_engine.get_inundation_severity_class(mean_sfii),
        "top_priority_impact_zones": top_zones,
        "depth_estimation_status": "NOT DIRECTLY OBSERVED"
    }

@router.get("/layers")
def get_spatial_layers():
    """
    Returns available spatial GIS layers and metadata catalog.
    """
    return {
        "layers": [
            {"id": "terrain_susceptibility", "name": "Copernicus DEM Terrain Susceptibility (TSS)", "type": "DERIVED", "resolution": "30m", "units": "Normalized [0, 1]"},
            {"id": "rainfall_hazard", "name": "NASA IMERG Precipitation Accumulation", "type": "OBSERVED_SATELLITE", "resolution": "0.1 deg (~10km)", "units": "mm/day"},
            {"id": "runoff_stress", "name": "ERA5-Land Surface Runoff Indicator", "type": "REANALYSIS_DERIVED", "resolution": "0.1 deg", "units": "Normalized [0, 1]"},
            {"id": "flood_susceptibility", "name": "Flood Susceptibility Index (FSI)", "type": "DERIVED_INDEX", "resolution": "Micro-Catchment", "units": "Normalized [0, 1]"},
            {"id": "spatial_flood_impact", "name": "Spatial Flood Impact Index (SFII)", "type": "MODEL_PREDICTED_SPATIAL", "resolution": "Micro-Catchment", "units": "Normalized [0, 1]"},
            {"id": "asset_intersection", "name": "Critical Infrastructure Risk Intersection", "type": "RULE_BASED", "resolution": "Point Asset", "units": "Asset Risk Index [0, 1]"}
        ]
    }

@router.get("/forecast")
def get_spatial_forecast():
    """
    Returns multi-horizon spatial impact forecast progression across all zones.
    """
    zones = spatial_inundation_engine.assess_all_zones()
    return {
        "status": "success",
        "horizons": ["current", "15m", "30m", "60m"],
        "forecast_zones": [
            {
                "zone_id": z['zone_id'],
                "name": z['name'],
                "current_sfii": z['spatial_flood_impact_index'],
                "forecast_progression": z['forecast_progression'],
                "prediction_interval": z['prediction_interval'],
                "uncertainty_level": z['uncertainty_level']
            }
            for z in zones
        ]
    }

@router.get("/zone/{zone_id}")
def get_zone_detail(zone_id: str):
    """
    Returns comprehensive spatial and environmental analytics for a specific zone.
    """
    zones = spatial_inundation_engine.assess_all_zones()
    match = next((z for z in zones if z['zone_id'] == zone_id), None)
    if not match:
        raise HTTPException(status_code=404, detail=f"Zone '{zone_id}' not found.")
    return match

@router.get("/query")
def query_spatial_point(
    lat: float = Query(..., ge=12.5, le=13.8, description="Latitude in decimal degrees"),
    lon: float = Query(..., ge=79.5, le=80.6, description="Longitude in decimal degrees")
):
    """
    Executes a spatial digital-twin inspection query at specific lat/lon coordinates.
    """
    return spatial_inundation_engine.query_point(lat, lon)

@router.post("/assess")
def assess_custom_spatial_scenario(payload: SpatialAssessRequest):
    """
    Evaluates spatial flood susceptibility and impact under custom environmental parameters.
    """
    env_state = payload.model_dump()
    zones = spatial_inundation_engine.assess_all_zones(env_state)
    return {
        "status": "success",
        "evaluated_parameters": env_state,
        "zones": zones
    }
