import pytest
from datetime import datetime, timezone
from app.core.evidence_rubric import calculate_evidence_rubric, is_authoritative_source
from app.api.api_v1.endpoints.impact_catalogue import (
    get_impact_record,
    review_impact_record,
    get_validation_readiness,
    export_evidence_card
)
from app.schemas.impact_record import CuratorReviewSubmission
from fastapi import HTTPException

def test_synthetic_record_receives_no_score():
    record = {
        "event_id": "SYNTH-DEMO-01",
        "evidence_status": "synthetic",
        "source_name": "Demo record",
        "start_time": "2024-06-15T11:00:00Z",
        "latitude": 13.08,
        "longitude": 80.27
    }
    rubric = calculate_evidence_rubric(record)
    assert rubric["total_score"] is None
    assert rubric["confidence_ratio"] is None
    assert rubric["is_synthetic"] is True
    assert rubric["score_display"] == "Add verified source"
    assert "Synthetic demonstration records are strictly excluded" in rubric["reason"]
    assert len(rubric["missing_items"]) > 0

def test_full_rubric_100_points():
    record = {
        "event_id": "PERFECT-01",
        "evidence_status": "historical_real",
        "source_name": "Central Water Commission Annual Flood Report",
        "source_org": "Central Water Commission",
        "source_url": "https://www.cwc.gov.in/report.pdf",
        "exact_time_verified": True,
        "start_time": "2015-12-01T15:30:00Z",
        "location_precision_type": "asset_landmark",
        "location_accuracy_m": 50.0,
        "corroborating_source_name": "IMD Rainfall Bulletin",
        "corroborating_source_url": "https://mausam.imd.gov.in/bulletin.pdf",
        "observed_flood_extent_sqkm": 24.5,
        "observed_flood_depth_m": 1.5
    }
    rubric = calculate_evidence_rubric(record)
    assert rubric["total_score"] == 100
    assert rubric["confidence_ratio"] == 1.0
    assert rubric["breakdown"]["authoritative_primary_source"]["points"] == 25
    assert rubric["breakdown"]["exact_datetime"]["points"] == 20
    assert rubric["breakdown"]["precise_location"]["points"] == 20
    assert rubric["breakdown"]["independent_corroborating_source"]["points"] == 20
    assert rubric["breakdown"]["observed_impact_measurement"]["points"] == 15
    assert len(rubric["missing_items"]) == 0

def test_partial_rubric_missing_items():
    # Record has CWC source (25 pts), multi-day window without exact time (0 pts),
    # ward centroid (10 pts), no corroboration (0 pts), water depth measured (15 pts).
    record = {
        "event_id": "PARTIAL-01",
        "evidence_status": "historical_real",
        "source_name": "CWC Flood Bulletin",
        "source_org": "Central Water Commission",
        "source_url": "https://cwc.gov.in/doc.pdf",
        "exact_time_verified": False,
        "start_time": "2015-12-01T00:00:00Z",
        "location_precision_type": "ward_centroid",
        "location_accuracy_m": 1200.0,
        "corroborating_source_url": None,
        "observed_flood_depth_m": 1.2
    }
    rubric = calculate_evidence_rubric(record)
    assert rubric["total_score"] == 50  # 25 + 0 + 10 + 0 + 15 = 50
    assert rubric["confidence_ratio"] == 0.5
    assert any("Exact event onset" in item for item in rubric["missing_items"])
    assert any("Independent corroborating source" in item for item in rubric["missing_items"])

def test_authoritative_source_checker():
    assert is_authoritative_source("Central Water Commission", "CWC Report", "https://cwc.gov.in/rep.pdf") is True
    assert is_authoritative_source("Greater Chennai Corporation", "GCC SWD", "https://chennaicorporation.gov.in") is True
    assert is_authoritative_source(None, "Personal Blog", "https://mychennaiblog.wordpress.com") is False
    assert is_authoritative_source(None, "None", None) is False

def test_curator_review_workflow():
    # Seed record #201 is currently 'under_review'
    sub = CuratorReviewSubmission(
        reviewer_name="Prof. A. Krishnan",
        decision="approved_historical_real",
        review_notes="Verified against official Greater Chennai Corporation grievance ledger."
    )
    # Reviewing record 201: has source_url and source_org GCC
    res = review_impact_record(record_id=201, review_in=sub, db=None)
    assert res["evidence_status"] == "historical_real"
    assert res["reviewer_name"] == "Prof. A. Krishnan"
    assert res["review_decision"] == "approved_historical_real"

def test_curator_cannot_approve_without_traceable_source():
    # If a record has no source_url, approval as historical_real must be rejected
    from app.api.api_v1.endpoints.impact_catalogue import _in_memory_records
    _in_memory_records.append({
        "id": 999,
        "event_id": "TEST-NO-SOURCE",
        "start_time": "2024-01-01T00:00:00Z",
        "latitude": 13.0,
        "longitude": 80.0,
        "zone": "Zone 1",
        "impact_type": "waterlogging",
        "source_name": "No source attached",
        "source_url": None,
        "source_org": None,
        "evidence_status": "unverified"
    })
    sub = CuratorReviewSubmission(
        reviewer_name="Dr. Tester",
        decision="approved_historical_real",
        review_notes="Attempting approval without source"
    )
    with pytest.raises(HTTPException) as excinfo:
        review_impact_record(record_id=999, review_in=sub, db=None)
    assert excinfo.value.status_code == 400
    assert "traceable source_url" in excinfo.value.detail

def test_validation_readiness_and_evidence_card():
    readiness = get_validation_readiness(db=None)
    assert readiness.total_historical_real_count >= 1
    # Check exportable evidence card
    card = export_evidence_card(record_id=100, db=None)
    assert "event_id" in card
    assert "latex_snippet" in card
    assert "markdown_card" in card
    assert "\\textbf{IMP-CHN-2015-CWC-01}" in card["latex_snippet"]
