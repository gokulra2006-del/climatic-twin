from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

from app.core.causal_cascade import causal_engine
from app.core.graph_provenance import GraphProvenance

router = APIRouter()

class WhatIfRequest(BaseModel):
    intrinsic_probs: Dict[str, float]
    interventions: Dict[str, float]

class WhatIfResponse(BaseModel):
    metadata: Dict[str, Any]
    baseline_probs: Dict[str, float]
    intervened_probs: Dict[str, float]
    delta: Dict[str, float]
    net_risk_delta: float

@router.post("/whatif", response_model=WhatIfResponse)
def simulate_cascade_intervention(request: WhatIfRequest):
    """
    Simulates a counterfactual intervention (do-operation) on the multi-hazard cascade graph.
    Provides the delta in downstream failure probabilities based on the causal edges.
    """
    try:
        result = causal_engine.simulate_intervention(
            intrinsic_probs=request.intrinsic_probs,
            interventions=request.interventions
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Cascade Engine Error")


@router.get("/provenance")
def get_cascade_graph_provenance():
    """Expose graph evidence maturity before interpreting a cascade/GNN result."""
    return GraphProvenance(
        causal_engine.graph,
        name="ClimateTwin provisional causal cascade",
        source=str(causal_engine.metadata.get("source", "Repository configuration")),
    ).get_report()
