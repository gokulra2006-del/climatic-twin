import csv
import io
import os
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Response
from sqlalchemy.orm import Session

from app.api import deps
from app.models.impact_record import ImpactRecord
from app.schemas.impact_record import (
    ImpactRecordCreate,
    ImpactRecordUpdate,
    ImpactRecordResponse,
    ImpactEvaluationRequest,
    ImpactEvaluationResponse
)
from app.core.impact_evaluator import evaluate_warning_impact_alignment
from app.core.warning_ledger import add_warning, list_warnings
from app.schemas.impact_record import WarningEvidence

router = APIRouter()

# In-memory storage fallback for zero-database setups
_in_memory_records: List[Dict[str, Any]] = []

# Demonstration records keep the user interface usable before a curator imports
# an evidence-checked catalogue. They are intentionally synthetic: their names,
# locations, timings and URLs must not be cited as municipal records.
SEED_IMPACTS = [
    {
        "id": 1,
        "event_id": "IMP-CHN-2015-01",
        "start_time": "2015-12-01T12:00:00Z",
        "end_time": "2015-12-03T18:00:00Z",
        "latitude": 13.0067,
        "longitude": 80.2017,
        "zone": "Zone 13 - Adyar",
        "impact_type": "flood_extent",
        "severity": "critical",
        "source_name": "Bundled demonstration scenario — replace with a curated source",
        "source_url": None,
        "evidence_status": "synthetic",
        "confidence": 0.0,
        "notes": "Demonstration record only. It is not a verified impact observation.",
        "created_at": datetime.now(timezone.utc).isoformat()
    },
    {
        "id": 2,
        "event_id": "IMP-CHN-2015-02",
        "start_time": "2015-12-01T14:30:00Z",
        "end_time": "2015-12-02T22:00:00Z",
        "latitude": 13.0063,
        "longitude": 80.0631,
        "zone": "Zone 11 - Valasaravakkam",
        "impact_type": "reservoir_overflow",
        "severity": "critical",
        "source_name": "Bundled demonstration scenario — replace with a curated source",
        "source_url": None,
        "evidence_status": "synthetic",
        "confidence": 0.0,
        "notes": "Demonstration record only. It is not a verified impact observation.",
        "created_at": datetime.now(timezone.utc).isoformat()
    },
    {
        "id": 3,
        "event_id": "IMP-CHN-2023-01",
        "start_time": "2023-12-04T08:00:00Z",
        "end_time": "2023-12-05T16:00:00Z",
        "latitude": 12.8990,
        "longitude": 80.2280,
        "zone": "Zone 14 - Perungudi",
        "impact_type": "waterlogging",
        "severity": "high",
        "source_name": "Bundled demonstration scenario — replace with a curated source",
        "source_url": None,
        "evidence_status": "synthetic",
        "confidence": 0.0,
        "notes": "Demonstration record only. It is not a verified impact observation.",
        "created_at": datetime.now(timezone.utc).isoformat()
    },
    {
        "id": 4,
        "event_id": "IMP-CHN-2023-02",
        "start_time": "2023-12-04T10:00:00Z",
        "end_time": "2023-12-05T12:00:00Z",
        "latitude": 13.0827,
        "longitude": 80.2707,
        "zone": "Zone 5 - Royapuram",
        "impact_type": "power_outage",
        "severity": "high",
        "source_name": "Bundled demonstration scenario — replace with a curated source",
        "source_url": None,
        "evidence_status": "synthetic",
        "confidence": 0.0,
        "notes": "Demonstration record only. It is not a verified impact observation.",
        "created_at": datetime.now(timezone.utc).isoformat()
    },
    {
        "id": 5,
        "event_id": "IMP-CHN-2024-01",
        "start_time": "2024-06-15T11:00:00Z",
        "end_time": "2024-06-17T20:00:00Z",
        "latitude": 13.1900,
        "longitude": 79.8600,
        "zone": "West Reservoirs",
        "impact_type": "drainage_failure",
        "severity": "moderate",
        "source_name": "Bundled demonstration scenario — replace with a curated source",
        "source_url": None,
        "evidence_status": "synthetic",
        "confidence": 0.0,
        "notes": "Demonstration record only. It is not a verified impact observation.",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
]

if not _in_memory_records:
    _in_memory_records.extend(SEED_IMPACTS)

@router.get("/", response_model=List[Dict[str, Any]])
def list_impact_records(
    zone: Optional[str] = Query(None, description="Filter by GCC Zone"),
    impact_type: Optional[str] = Query(None, description="Filter by impact type"),
    evidence_status: Optional[str] = Query(None, description="historical_real, proxy, synthetic, unverified"),
    severity: Optional[str] = Query(None, description="low, moderate, high, critical"),
    db: Session = Depends(deps.get_db_optional)
):
    """List and filter historical impact records with provenance metadata."""
    if db:
        try:
            q = db.query(ImpactRecord)
            if zone: q = q.filter(ImpactRecord.zone == zone)
            if impact_type: q = q.filter(ImpactRecord.impact_type == impact_type)
            if evidence_status: q = q.filter(ImpactRecord.evidence_status == evidence_status)
            if severity: q = q.filter(ImpactRecord.severity == severity)
            results = q.order_by(ImpactRecord.start_time.desc()).all()
            if results:
                return results
        except Exception:
            pass

    # Fallback to in-memory store
    res = list(_in_memory_records)
    if zone: res = [r for r in res if r["zone"].lower() == zone.lower()]
    if impact_type: res = [r for r in res if r["impact_type"].lower() == impact_type.lower()]
    if evidence_status: res = [r for r in res if r["evidence_status"].lower() == evidence_status.lower()]
    if severity: res = [r for r in res if r["severity"].lower() == severity.lower()]
    return sorted(res, key=lambda x: str(x["start_time"]), reverse=True)

@router.post("/", response_model=Dict[str, Any])
def create_impact_record(
    record_in: ImpactRecordCreate,
    db: Session = Depends(deps.get_db_optional)
):
    """Add a new documented impact record into the catalogue."""
    data = record_in.model_dump()
    data["created_at"] = datetime.now(timezone.utc)
    if db:
        try:
            db_record = ImpactRecord(**data)
            db.add(db_record)
            db.commit()
            db.refresh(db_record)
            return db_record
        except Exception:
            pass

    new_id = len(_in_memory_records) + 1
    stored = {**data, "id": new_id, "start_time": data["start_time"].isoformat(), "created_at": data["created_at"].isoformat()}
    if data["end_time"]:
        stored["end_time"] = data["end_time"].isoformat()
    _in_memory_records.append(stored)
    return stored

@router.get("/export/csv")
def export_impact_records_csv(db: Session = Depends(deps.get_db_optional)):
    """Export the entire Chennai Impact Catalogue as CSV."""
    records = list_impact_records(None, None, None, None, db)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id", "event_id", "start_time", "end_time", "latitude", "longitude",
        "zone", "impact_type", "severity", "source_name", "source_url",
        "evidence_status", "confidence", "notes"
    ])
    for r in records:
        writer.writerow([
            r.get("id"), r.get("event_id"), r.get("start_time"), r.get("end_time"),
            r.get("latitude"), r.get("longitude"), r.get("zone"), r.get("impact_type"),
            r.get("severity"), r.get("source_name"), r.get("source_url"),
            r.get("evidence_status"), r.get("confidence"), r.get("notes")
        ])
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=chennai_impact_catalogue.csv"}
    )

@router.post("/import/csv")
async def import_impact_records_csv(
    file: UploadFile = File(...),
    db: Session = Depends(deps.get_db_optional)
):
    """Batch import impact records via CSV with strict schema validation."""
    content = await file.read()
    decoded = content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(decoded))
    imported = 0
    errors = []

    for idx, row in enumerate(reader):
        try:
            record_create = ImpactRecordCreate(
                event_id=row["event_id"],
                start_time=datetime.fromisoformat(row["start_time"].replace("Z", "+00:00")),
                end_time=datetime.fromisoformat(row["end_time"].replace("Z", "+00:00")) if row.get("end_time") else None,
                latitude=float(row["latitude"]),
                longitude=float(row["longitude"]),
                zone=row["zone"],
                impact_type=row["impact_type"],
                severity=row.get("severity", "moderate"),
                source_name=row["source_name"],
                source_url=row.get("source_url"),
                evidence_status=row.get("evidence_status", "unverified"),
                confidence=float(row.get("confidence", 0.7)),
                notes=row.get("notes")
            )
            create_impact_record(record_create, db)
            imported += 1
        except Exception as e:
            errors.append(f"Row {idx+1}: {str(e)}")

    return {
        "status": "SUCCESS" if imported > 0 else "FAILED",
        "imported_records_count": imported,
        "validation_errors": errors[:10]
    }

@router.post("/evaluate", response_model=ImpactEvaluationResponse)
def evaluate_warnings(
    req: ImpactEvaluationRequest,
    db: Session = Depends(deps.get_db_optional)
):
    """
    Evaluates warning predictions against ground-truth/proxy documented impacts.
    Does NOT invent synthetic performance; returns INSUFFICIENT_EVIDENCE if labels are absent.
    """
    records = list_impact_records(zone=req.target_zone, impact_type=req.target_impact_type, db=db)
    
    # Filter records strictly by requested time range
    matched_time_records = []
    for r in records:
        r_time = datetime.fromisoformat(str(r["start_time"]).replace("Z", "+00:00"))
        if req.start_time <= r_time <= req.end_time:
            matched_time_records.append(r)

    submitted_warnings = [warning.model_dump(mode="json") for warning in req.warnings]
    ledger_warnings = list_warnings() if not submitted_warnings else []
    warnings = submitted_warnings or ledger_warnings
    eligible_impacts = [record for record in matched_time_records if record.get("evidence_status") == "historical_real"]

    return evaluate_warning_impact_alignment(
        impact_records=eligible_impacts,
        warnings=[warning for warning in warnings if warning.get("probability", 0) >= req.warning_probability_threshold],
        radius_km=req.spatial_radius_km
    )


@router.post("/warnings", response_model=Dict[str, Any])
def export_model_warning(warning: WarningEvidence):
    """Store a warning exported by a declared model run for later evaluation."""
    record = add_warning(warning.model_dump(mode="json"))
    return {
        "status": "RECORDED",
        "warning": record,
        "provenance_note": "Model-run warning ledger. This record is not an impact label."
    }


@router.get("/warnings", response_model=List[Dict[str, Any]])
def get_model_warnings():
    """List reproducible warning exports available to the evaluation utility."""
    return list_warnings()
