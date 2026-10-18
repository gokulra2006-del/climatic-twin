"""Evidence-readiness checks for ClimateTwin research claims.

The endpoint intentionally reports evidence gaps instead of upgrading a
prototype claim based on synthetic or proxy material.  It is a review aid, not
an automated journal-acceptance decision.
"""

from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api import deps
from app.models.impact_record import ImpactRecord

router = APIRouter()

PROJECT_ROOT = Path(__file__).resolve().parents[5]


def _record_count(db: Session | None, evidence_status: str) -> int:
    """Count catalogue rows safely when the optional local database is present."""
    if db is None:
        return 0
    try:
        return int(
            db.query(ImpactRecord)
            .filter(ImpactRecord.evidence_status == evidence_status)
            .count()
        )
    except Exception:
        return 0


def _item(
    gap: str,
    status: str,
    evidence: str,
    required_next_evidence: List[str],
    claim_boundary: str,
) -> Dict[str, Any]:
    return {
        "gap": gap,
        "status": status,
        "evidence": evidence,
        "required_next_evidence": required_next_evidence,
        "claim_boundary": claim_boundary,
    }


@router.get("/summary")
def get_research_readiness(db: Session = Depends(deps.get_db_optional)) -> Dict[str, Any]:
    """Return an auditable status board for research-gap closure.

    ``READY`` means the supporting workflow exists. It never means a claim is
    field validated unless real, traceable evidence is also available.
    """
    historical_impacts = _record_count(db, "historical_real")
    has_historical_impacts = historical_impacts > 0
    rainfall_2019 = (PROJECT_ROOT / "data" / "processed" / "rainfall" / "imerg_chennai_daily.csv").exists()
    soil_moisture_2019 = (PROJECT_ROOT / "data" / "processed" / "soil_moisture" / "chennai_daily.csv").exists()
    dem_available = (PROJECT_ROOT / "data" / "processed" / "geospatial" / "chennai_dem_30m.tif").exists()

    items = [
        _item(
            "Hazard-to-impact validation",
            "READY_FOR_IMPORT" if not has_historical_impacts else "READY_FOR_EVALUATION",
            f"{historical_impacts} traceable historical-impact record(s) in the local catalogue.",
            ["Import independently traceable Chennai impact records.", "Export model-run warnings for the same events."],
            "Do not report impact precision, recall, or F1 until both historical impacts and model-run warnings are present.",
        ),
        _item(
            "Two-dimensional inundation",
            "SCENARIO_READY" if dem_available else "BLOCKED",
            "DEM-based zone scenario engine is available; its depth output is explicitly a proxy.",
            ["Observed 2015/2023 flood-extent polygons or depth observations.", "A hydraulic benchmark and extent/depth comparison."],
            "Do not describe scenario_depth_proxy_m as observed or hydraulically validated water depth.",
        ),
        _item(
            "2019 drought replay",
            "PARTIAL" if rainfall_2019 and not soil_moisture_2019 else "READY_FOR_CHECK" if rainfall_2019 and soil_moisture_2019 else "PARTIAL",
            "The replay contains historical reservoir storage; rainfall and soil-moisture completeness must be checked per event window.",
            ["Daily rainfall coverage for May–July 2019.", "Quality-checked soil-moisture coverage for the same window.", "Documented water-service or demand outcome labels."],
            "Current drought output is a reservoir-storage stress proxy, not a complete drought-impact model.",
        ),
        _item(
            "Extreme-event and uncertainty validation",
            "PARTIAL",
            "Chronological evaluation and uncertainty artifacts exist, but the archived report documents only two independent multi-sensor holdout events.",
            ["More untouched event windows.", "Coverage, WIS/CRPS, sharpness, reliability, and event-level confidence intervals."],
            "Do not generalize rare-event performance from the current small independent holdout.",
        ),
        _item(
            "Infrastructure topology and cascades",
            "PROVENANCE_GATED",
            "Cascade and graph-provenance modules exist; active pump, power, and drainage dependency records remain incomplete.",
            ["Authoritative GIS and dependency records.", "Time-stamped failure and restoration logs.", "An ablation using only verified graph edges."],
            "Synthetic, proxy, and unverified edges cannot support a field-validated cascade claim.",
        ),
        _item(
            "Model comparison and GNN evidence",
            "PARTIAL",
            "Baseline and GNN experiment infrastructure exists.",
            ["A common chronological split and feature set for every baseline.", "A topology ablation and uncertainty comparison on untouched events."],
            "Do not claim GNN superiority unless the fair comparison is reproduced with verified topology.",
        ),
        _item(
            "Decision usefulness",
            "PROTOTYPE_ONLY",
            "Decision support policies and synthetic scenarios are implemented.",
            ["Authority-approved action definitions and constraints.", "Observed response-time/cost records or an ethics-approved operator study."],
            "Recommended actions are decision support, not autonomous emergency commands or operationally validated advice.",
        ),
        _item(
            "Equity, accessibility, and warning reach",
            "BLOCKED",
            "Current vulnerability scores are prototype values.",
            ["Appropriate ward-level public indicators.", "Accessibility and multilingual usability evaluation.", "Privacy and governance review."],
            "Do not claim equitable warning reach or demographic validity from prototype vulnerability values.",
        ),
        _item(
            "Reproducibility and governance",
            "PARTIAL",
            "Seeds, experiment scripts, data cards, audit scaffolding, and security documentation are present.",
            ["A clean-environment reproduction log.", "Dataset version identifiers and licenses for every imported source.", "Threat-model and deployment-control review."],
            "Local security simulations are not a production security assessment.",
        ),
    ]
    counts = {status: sum(1 for item in items if item["status"] == status) for status in {item["status"] for item in items}}
    return {
        "title": "ClimateTwin research evidence readiness",
        "summary": "This board distinguishes implemented software from empirical evidence required for publication claims.",
        "items": items,
        "status_counts": counts,
        "journal_claim_policy": "Use only the claim boundaries shown here until the requested evidence has been independently verified.",
    }
