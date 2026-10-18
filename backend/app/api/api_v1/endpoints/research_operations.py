"""Operational research workflows with explicit evidence boundaries.

This module makes the project's remaining research gaps actionable without
misrepresenting simulated, proxy, or unverified inputs as field evidence.
"""

from datetime import datetime, timezone
from json import dumps
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api import deps
from app.models.log import AuditLog

router = APIRouter()
_memory_action_outcomes: List[Dict[str, Any]] = []


class AdvisoryDraftRequest(BaseModel):
    hazard: str = Field(default="Flood", max_length=80)
    level: str = Field(default="Moderate", max_length=30)
    location: str = Field(default="Chennai", max_length=120)
    evidence_status: str = Field(default="prototype", max_length=30)


class ActionOutcomeRequest(BaseModel):
    action_type: str = Field(max_length=80)
    status: str = Field(default="planned", pattern="^(planned|approved|completed|not_completed)$")
    location: str = Field(default="Chennai", max_length=120)
    actor_name: str = Field(default="local operator", max_length=120)
    evidence_status: str = Field(default="unverified", pattern="^(historical_real|proxy|synthetic|unverified)$")
    source_url: Optional[str] = Field(default=None, max_length=500)
    outcome_note: Optional[str] = Field(default=None, max_length=1000)


def _gap(
    area: str, workflow: str, current: str, needed: List[str], boundary: str
) -> Dict[str, Any]:
    return {"area": area, "workflow": workflow, "current": current, "needed": needed, "boundary": boundary}


@router.get("/overview")
def research_operations_overview() -> Dict[str, Any]:
    """Return the actionable evidence plan for all eight research gaps."""
    items = [
        _gap("Impact-based flood warnings", "Import impact records and evaluate exported warnings", "Catalogue and warning-export workflows are implemented.", ["Traceable road-closure, waterlogging, outage, or hospital-access records", "Event-aligned warning exports"], "No impact-performance claim is valid before both sources are linked."),
        _gap("Flood inundation mapping", "Compare scenario maps with observed event evidence", "DEM-constrained susceptibility/scenario mapping is available.", ["Observed extent/depth data", "Calibrated 2-D hydraulic benchmark"], "Scenario depth remains a proxy until independently validated."),
        _gap("Infrastructure cascade modelling", "Register verified assets and dependency edges", "Cascade prototype and graph-provenance workflow are available.", ["Authoritative pump, drainage, power, hospital, and water dependencies", "Failure/restoration logs"], "Unverified graph edges cannot support a field-cascade claim."),
        _gap("GNN comparison", "Run a common chronological benchmark and topology ablation", "Synthetic benchmark and baseline comparison workflow exist.", ["Same real data and time split", "Verified topology", "LSTM/RF/XGBoost/GNN-LSTM comparison"], "Synthetic results demonstrate software behaviour, not Chennai accuracy."),
        _gap("Drought replay", "Load quality-checked 2019 hydro-climate inputs", "Reservoir-storage replay is available.", ["Daily rainfall, groundwater, and soil moisture", "Verified shortage/service outcomes"], "Current drought replay is a storage-stress proxy."),
        _gap("Decision usefulness", "Log a human-approved action and its outcome", "NOVA decision cards and an audit workflow are implemented.", ["Stakeholder review", "Response-time, cost, and outcome evidence"], "The system does not autonomously command emergency action."),
        _gap("Equity and accessibility", "Draft bilingual advisories and test usability", "Vulnerability framework and bilingual draft generator are available.", ["Ward-level indicators", "Tamil/English usability and accessibility testing", "Reach metrics"], "Draft messages are not evidence of equitable reach."),
        _gap("Security readiness", "Maintain provenance, review access, and run authorised testing", "Audit scaffold and security documentation are available.", ["Threat model", "Authorised attack testing", "Access-control and deployment review"], "Local checks are not a production security certification."),
    ]
    return {
        "title": "Evidence and action hub",
        "summary": "A research operations checklist that separates implemented workflows from evidence still required for conference or journal claims.",
        "items": items,
        "promotion_gate": [
            "Use a traceable source and licence for every imported record.",
            "Keep synthetic, proxy, unverified, and historical-real records separate.",
            "Evaluate on untouched historical event windows.",
            "Have an authorised human review any operational recommendation.",
        ],
    }


@router.post("/advisory-draft")
def create_advisory_draft(payload: AdvisoryDraftRequest) -> Dict[str, Any]:
    """Create an accessible bilingual advisory *draft*, never an issued warning."""
    hazard, level, location = payload.hazard.title(), payload.level.upper(), payload.location
    english = (
        f"Prototype advisory draft — {level} {hazard} watch for {location}. "
        "Check official local authority updates, avoid affected routes where advised, "
        "and support people who may need accessible information or assistance."
    )
    tamil = (
        f"முன்மாதிரி அறிவிப்பு வரைவு — {location} பகுதியில் {hazard} தொடர்பாக {level} கண்காணிப்பு. "
        "அதிகாரப்பூர்வ உள்ளூர் அறிவிப்புகளைப் பார்க்கவும்; அறிவுறுத்தப்பட்ட பாதைகளைத் தவிர்க்கவும்; "
        "உதவி தேவைப்படுபவர்களுக்கு தகவல் கிடைப்பதை உறுதிசெய்யவும்."
    )
    return {
        "status": "DRAFT_REQUIRES_AUTHORISED_REVIEW",
        "english": english,
        "tamil": tamil,
        "accessibility_note": "Use plain language, high contrast, screen-reader compatible text, and an authorised Tamil translation review before release.",
        "evidence_boundary": f"Input evidence status: {payload.evidence_status}. This prototype cannot issue a public warning.",
    }


@router.post("/action-outcomes")
def log_action_outcome(
    payload: ActionOutcomeRequest, db: Session = Depends(deps.get_db_optional)
) -> Dict[str, Any]:
    """Store a human-entered decision/outcome trail with provenance status."""
    timestamp = datetime.now(timezone.utc).isoformat()
    item = {**payload.model_dump(), "timestamp": timestamp, "record_type": "human_entered_action_outcome"}
    saved_to = "memory"
    if db is not None:
        try:
            db.add(AuditLog(username=payload.actor_name, action="RESEARCH_ACTION_OUTCOME", resource=payload.location, metadata_json=dumps(item)))
            db.commit()
            saved_to = "audit_log"
        except Exception:
            db.rollback()
    _memory_action_outcomes.append(item)
    return {
        "status": "LOGGED",
        "saved_to": saved_to,
        "record": item,
        "evidence_boundary": "A logged action is not a verified outcome. Attach a traceable source before using it as historical-real research evidence.",
    }


@router.get("/security-readiness")
def security_readiness() -> Dict[str, Any]:
    return {
        "implemented": ["Audit trail schema", "Role-based UI paths", "Data provenance categories", "Local documentation"],
        "required_before_deployment": ["Threat model", "Authorised penetration testing", "Access-control review", "Secrets management review", "Incident response exercise"],
        "boundary": "This is a research readiness checklist, not a security certification or live security scan.",
    }


@router.get("/live-data-status")
def live_data_status() -> Dict[str, Any]:
    """Expose exactly which inputs are live and which remain simulated/proxy.

    This endpoint deliberately avoids a single misleading 'online' flag: live
    weather availability does not turn reservoir, impact, or asset data into
    live observations.
    """
    try:
        from app.core.satellite_ingestion import satellite_engine

        telemetry = satellite_engine.get_latest_satellite_telemetry()
    except Exception as exc:
        telemetry = {}
        fetch_error = str(exc)
    else:
        fetch_error = None

    flood = telemetry.get("flood", {}) if telemetry else {}
    heat = telemetry.get("heatwave", {}) if telemetry else {}
    drought = telemetry.get("drought", {}) if telemetry else {}
    telemetry_meta = telemetry.get("telemetry_meta", {}) if telemetry else {}
    is_live_weather = telemetry_meta.get("mode") == "LIVE_WEATHER_API"
    return {
        "status": "LIVE_WEATHER_AVAILABLE" if is_live_weather else "LIVE_WEATHER_UNAVAILABLE",
        "updated_at": telemetry.get("timestamp") if telemetry else None,
        "feeds": [
            {"name": "Chennai weather and rainfall", "state": "live" if is_live_weather else "unavailable", "source": "Open-Meteo city weather API", "fields": ["temperature", "humidity", "wind", "precipitation"]},
            {"name": "Atmospheric and soil indicators", "state": "weather_model_derived" if is_live_weather else "unavailable", "source": "Open-Meteo forecast-model fields", "fields": ["soil moisture", "CAPE", "UV", "radiation"]},
            {"name": "Reservoir storage", "state": "simulated", "source": "Rainfall-driven prototype calculation", "fields": ["Poondi", "Cholavaram", "Redhills", "Chembarambakkam"]},
            {"name": "Flood impact and road disruption", "state": "curated_import_required", "source": "Impact Catalogue", "fields": ["road closure", "waterlogging", "outage", "hospital access"]},
            {"name": "Infrastructure dependencies", "state": "verified_import_required", "source": "Graph provenance workflow", "fields": ["pump", "drainage", "power", "hospital", "water"]},
        ],
        "snapshot": {
            "temperature_c": heat.get("air_temp_c"),
            "humidity_percent": heat.get("humidity_percent"),
            "rainfall_7d_mm": flood.get("rainfall_7d_sum"),
            "soil_moisture_root_zone": drought.get("soil_moisture_root_zone"),
        },
        "boundary": "Only the weather-derived feed is live when marked live. Reservoir values, spatial impact estimates, virtual stations, and risk outputs retain their stated prototype/proxy status.",
        "error": fetch_error,
    }


@router.get("/templates/{template_name}")
def download_evidence_template(template_name: str) -> Response:
    """Provide import-ready templates; blank rows are not research evidence."""
    templates = {
        "impact_catalogue": (
            "event_id,start_time,end_time,latitude,longitude,zone,impact_type,severity,source_name,source_url,evidence_status,confidence,notes\n"
        ),
        "infrastructure_dependencies": (
            "asset_id,asset_type,depends_on_asset_id,dependency_type,source_name,source_url,evidence_status,valid_from,notes\n"
            "PUMP-001,pump,SUBSTATION-001,power_supply,Authoritative owner,https://example.org/source,historical_real,YYYY-MM-DD,Verify with asset owner\n"
        ),
        "drought_replay": (
            "date,rainfall_mm,soil_moisture_root_zone,groundwater_level_m,reservoir_storage_mcft,service_outcome,source_name,source_url,evidence_status\n"
            "2019-05-01,,,,,,Authoritative source,https://example.org/source,historical_real\n"
        ),
    }
    if template_name not in templates:
        return Response(status_code=404, content="Unknown template. Use impact_catalogue, infrastructure_dependencies, or drought_replay.")
    return Response(
        content=templates[template_name],
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={template_name}_template.csv"},
    )
