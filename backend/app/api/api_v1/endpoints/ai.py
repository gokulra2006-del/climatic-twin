from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.api import deps
from datetime import datetime, timezone

from app.core.multihazard import MultiHazardRiskEngine
from app.core.asset_risk import AssetRiskEngine
from app.core.sensor_health import SensorHealthEngine
from app.core.uncertainty import UncertaintyQuantificationEngine
from app.core.assimilation import twin_engine
from app.core.nova_copilot import nova_copilot

from app.api.api_v1.endpoints.predictions import get_model
import numpy as np
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


class CopilotQuestion(BaseModel):
    question: str = Field(min_length=3, max_length=1000)
    hazard: str = Field(default="FLOOD", max_length=50)

@router.get("/command-summary")
def get_ai_command_summary(hazard: str = "FLOOD"):
    """
    Generate an AI Command Summary using existing core engines, tailored to the selected dashboard.
    """
    # Pull the live, assimilated physical state of the city
    twin_data = twin_engine.get_current_state()
    env_state = twin_data.get("state", {})
    
    # Obtain precise live flood probability from the ML model
    features = twin_engine.get_feature_vector()
    features_arr = np.array(features).reshape(1, -1)
    
    model_data = get_model()
    flood_prob = None
    flood_model_status = "UNAVAILABLE"
    if model_data is not None:
        try:
            model = model_data["model"]
            flood_prob = float(model.predict_proba(features_arr)[0, 1])
            flood_model_status = "AVAILABLE"
        except Exception as exc:
            logger.warning("NOVA could not evaluate the flood model: %s", exc)
            
    mh_engine = MultiHazardRiskEngine()
    # Keep the compound-risk engine operational when the model artifact is not
    # available, but never present an invented numeric probability as a result.
    mh_result = mh_engine.calculate_compound_risk(env_state, flood_prob=flood_prob or 0.0)
    
    # Extract specific hazards
    raw_hazards = mh_engine.normalize_hazard_states(env_state, flood_prob or 0.0)
    
    target = hazard.upper()
    override_hazard = None
    if target == "FLOOD":
        override_hazard = raw_hazards.get("flood")
    elif target == "HEATWAVE":
        override_hazard = raw_hazards.get("heat")
    elif target == "EXTREME_RAINFALL":
        override_hazard = raw_hazards.get("rainfall")
    elif target == "DROUGHT":
        override_hazard = raw_hazards.get("reservoir_stress")
        
    if override_hazard:
        # Override the top priority threat to match the user's current context
        mh_result["dominant_hazard"] = override_hazard["hazard_name"]
        mh_result["compound_risk_level"] = override_hazard["hazard_level"]
        mh_result["compound_risk_score"] = override_hazard["normalized_intensity"]
    
    asset_engine = AssetRiskEngine()
    asset_result = asset_engine.assess_all_assets(env_state)
    
    sensor_monitor = SensorHealthEngine()
    dq_summary = sensor_monitor.get_summary()
    
    # Priority Threat
    priority_threat = {
        "type": mh_result.get("dominant_hazard", "UNKNOWN"),
        "level": mh_result.get("compound_risk_level", "LOW"),
        "score": round(mh_result.get("compound_risk_score", 0.0), 2),
        "reason": mh_result.get("cascade_explanation", "Routine monitoring."),
        "recommended_action": "Maintain routine surveillance."
    }
    
    if priority_threat["level"] in ["HIGH", "CRITICAL"]:
        priority_threat["recommended_action"] = "Prioritize monitoring and prepare response resources."

    action_by_level = {
        "LOW": ("NORMAL", "Continue routine monitoring; no emergency action is recommended.", "Duty analyst", 60),
        "MODERATE": ("MONITOR", "Check the named drivers and verify the next telemetry cycle before escalating.", "Duty analyst", 30),
        "HIGH": ("PREPARE", "Notify the operations lead and verify critical telemetry before activating field resources.", "Operations lead", 15),
        "CRITICAL": ("ESCALATE", "Start the approved emergency protocol and obtain a human situation assessment.", "Incident commander", 5),
    }
    operating_mode, decision_action, decision_owner, review_minutes = action_by_level.get(
        priority_threat["level"], action_by_level["LOW"]
    )
        
    # Highest Priority Asset
    highest_priority_asset = {}
    if asset_result and len(asset_result) > 0:
        top_asset = sorted(asset_result, key=lambda x: x.get("asset_risk_index", 0.0), reverse=True)[0]
        highest_priority_asset = {
            "Asset Name": top_asset.get("name"),
            "Asset Risk Index": top_asset.get("asset_risk_index"),
            "Risk Level": top_asset.get("risk_level"),
            "Primary Threat": priority_threat["type"],
            "Recommended Protection": top_asset.get("recommended_action")
        }
        
    # Data Trust
    data_trust = {
        "score": dq_summary.get("aggregate_health_score", 1.0),
        "status": dq_summary.get("city_wide_telemetry_health", "UNKNOWN"),
        "explanation": f"{dq_summary.get('source_counts', {}).get('healthy', 0)} sources healthy. {dq_summary.get('source_counts', {}).get('stale', 0)} stale."
    }
    
    # Confidence
    confidence = {
        "level": "HIGH" if data_trust["score"] > 0.8 else ("MODERATE" if data_trust["score"] > 0.5 else "LOW"),
        "explanation": f"Confidence is based on a data trust score of {round(data_trust['score']*100)}% with {dq_summary.get('source_counts', {}).get('healthy', 0)} active telemetry sources."
    }
    
    # This is a status-hold outlook, not a numerical nowcast. Keeping that
    # distinction explicit prevents the interface from overstating capability.
    next_60_minutes = [
        {"horizon": "Now", "risk": priority_threat["level"], "trend": "Current assessed state"},
        {"horizon": f"+{review_minutes} min", "risk": "REVIEW", "trend": "Refresh telemetry and reassess"},
    ]
    
    # Causal Chain
    causal_chain = [
        "Environmental Drivers Detected",
        f"Hazard Indicator: {priority_threat['type']}",
        f"Compound Risk Level: {priority_threat['level']}",
        f"Vulnerable Asset: {highest_priority_asset.get('Asset Name', 'None')}",
        priority_threat["recommended_action"]
    ]
    
    # Refine the conversational AI outputs for the UI
    drivers_str = mh_result.get("cascade_explanation", "")
    
    why_now = [
        f"Dynamic Compound Risk Score elevated to {priority_threat['score']}.",
        f"Dominant physical driver identified as {priority_threat['type'].replace('_', ' ')}."
    ]
    if "Contributing conditions" in drivers_str:
        conds = drivers_str.split("Contributing conditions: ")[-1].split(". Interacting")[0]
        why_now.append(f"Key drivers: {conds}.")
        
    what_changed = [
        f"Latest telemetry health is {data_trust['score'] * 100:.0f}% ({data_trust['status']}).",
        (f"Flood-model probability is {flood_prob * 100:.1f}% (shown for context)."
         if flood_prob is not None else "Flood-model probability is unavailable; NOVA is not substituting a fallback value."),
        "Asset prioritisation is a prototype screening result, not a verified field-impact record."
    ]

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "system_status": "ONLINE",
        "priority_threat": priority_threat,
        "current_situation": f"The intelligence engine detects a {priority_threat['level']} level risk centered primarily around {priority_threat['type'].replace('_', ' ')}.",
        "why_now": why_now,
        "what_changed": what_changed,
        "next_60_minutes": next_60_minutes,
        "highest_priority_asset": highest_priority_asset,
        "data_trust": data_trust,
        "confidence": confidence,
        "recommended_action": priority_threat["recommended_action"],
        "causal_chain": causal_chain,
        "decision_brief": {
            "operating_mode": operating_mode,
            "action": decision_action,
            "owner": decision_owner,
            "review_in_minutes": review_minutes,
            "escalation_trigger": "Escalate if the assessed risk level rises, data quality degrades, or an authorised field report confirms impact.",
            "evidence_boundary": "Prototype decision support. It does not replace an official warning, field verification, or emergency authority."
        },
        "method_note": "NOVA organises existing model and telemetry outputs; it does not generate an independent forecast or validate impacts."
        ,"source_ledger": {
            "telemetry": "Current telemetry and quality summary",
            "flood_model": flood_model_status,
            "asset_priority": "Prototype screening result — requires field verification",
            "ai_mode": nova_copilot.provider_status()["provider"],
        },
        "recommended_checks": [
            "Refresh telemetry before escalating an operational action.",
            "Verify any reported impact with an authorised field or agency source.",
            "Record the operator decision and review time in the audit workflow.",
        ],
    }


@router.get("/provider-status")
def get_provider_status():
    """Reveal only provider configuration state, never a secret key."""
    return nova_copilot.provider_status()


@router.post("/copilot")
async def ask_nova_copilot(payload: CopilotQuestion):
    """Answer against the current command summary with a safe local fallback."""
    briefing = get_ai_command_summary(payload.hazard)
    result = await nova_copilot.answer(payload.question, briefing)
    return {
        **result,
        "question": payload.question,
        "hazard": payload.hazard.upper(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
