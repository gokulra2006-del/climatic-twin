from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
from app.api.api_v1.endpoints.predictions import get_latest_prediction
from app.api.api_v1.endpoints.hazard_prototypes import (
    get_latest_heatwave,
    get_latest_drought,
    get_latest_extreme_rainfall,
    map_risk_level_generic
)
import numpy as np

router = APIRouter()

class WhatIfScenario(BaseModel):
    temperature_increase_c: float = 0.0
    rainfall_multiplier: float = 1.0
    reservoir_capacity_increase_mcft: float = 0.0

@router.post("/")
def run_what_if_scenario(scenario: WhatIfScenario):
    """
    Evaluates how risk probabilities change under a hypothetical 'What-If' scenario.
    """
    # 1. Get current baselines
    flood = get_latest_prediction()
    heat = get_latest_heatwave()
    drought = get_latest_drought()
    rain = get_latest_extreme_rainfall()
    
    f_prob = flood.get("probability", 0) if isinstance(flood, dict) else 0
    h_prob = heat.get("probability", 0)
    d_prob = drought.get("probability", 0)
    r_prob = rain.get("probability", 0)
    
    # 2. Apply Scenario Modifiers (Prototype Heuristics)
    
    # Temperature increase directly spikes heatwave and drought probabilities
    if scenario.temperature_increase_c > 0:
        h_prob = min(1.0, h_prob + (scenario.temperature_increase_c * 0.15))
        d_prob = min(1.0, d_prob + (scenario.temperature_increase_c * 0.10))
        
    # Rainfall multiplier spikes extreme rainfall and flood, but reduces drought
    if scenario.rainfall_multiplier != 1.0:
        if scenario.rainfall_multiplier > 1.0:
            r_prob = min(1.0, r_prob * scenario.rainfall_multiplier)
            f_prob = min(1.0, f_prob * (scenario.rainfall_multiplier * 1.2))
            d_prob = max(0.0, d_prob * (1.0 / scenario.rainfall_multiplier))
        else:
            r_prob = max(0.0, r_prob * scenario.rainfall_multiplier)
            f_prob = max(0.0, f_prob * scenario.rainfall_multiplier)
            d_prob = min(1.0, d_prob * (1.0 + (1.0 - scenario.rainfall_multiplier)))
            
    # New infrastructure (Reservoir) mitigates flood risk
    if scenario.reservoir_capacity_increase_mcft > 0:
        # Assuming 1000 mcft reduces flood probability by ~10%
        mitigation = (scenario.reservoir_capacity_increase_mcft / 1000.0) * 0.10
        f_prob = max(0.0, f_prob - mitigation)
        
    return {
        "scenario_applied": scenario.model_dump(),
        "modified_risks": {
            "FLOOD": {"probability": f_prob, "level": map_risk_level_generic(f_prob)},
            "HEATWAVE": {"probability": h_prob, "level": map_risk_level_generic(h_prob)},
            "DROUGHT": {"probability": d_prob, "level": map_risk_level_generic(d_prob)},
            "EXTREME_RAINFALL": {"probability": r_prob, "level": map_risk_level_generic(r_prob)}
        },
        "message": "What-If Scenario successfully simulated."
    }
