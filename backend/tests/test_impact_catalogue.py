import pytest
from datetime import datetime, timezone
from app.schemas.impact_record import ImpactRecordCreate
from app.core.impact_evaluator import evaluate_warning_impact_alignment, haversine_distance_km

def test_haversine_distance():
    # Central Chennai (13.0827, 80.2707) to Adyar Estuary (13.0100, 80.2600) ~ 8.1 km
    d = haversine_distance_km(13.0827, 80.2707, 13.0100, 80.2600)
    assert 7.5 < d < 9.0

def test_impact_record_validation():
    # Valid record
    valid = ImpactRecordCreate(
        event_id="TEST-01",
        start_time=datetime.now(timezone.utc),
        latitude=13.08,
        longitude=80.27,
        zone="Zone 5",
        impact_type="waterlogging",
        severity="high",
        source_name="Test Source",
        source_url="https://example.org/traceable-source",
        evidence_status="historical_real",
        confidence=0.9
    )
    assert valid.impact_type == "waterlogging"

    # Invalid impact_type
    with pytest.raises(ValueError):
        ImpactRecordCreate(
            event_id="TEST-02",
            start_time=datetime.now(timezone.utc),
            latitude=13.08,
            longitude=80.27,
            zone="Zone 5",
            impact_type="tornado", # Not allowed
            source_name="Test Source"
        )

    with pytest.raises(ValueError):
        ImpactRecordCreate(
            event_id="TEST-03", start_time=datetime.now(timezone.utc), latitude=13.08,
            longitude=80.27, zone="Zone 5", impact_type="waterlogging",
            source_name="Unlinked source", evidence_status="historical_real"
        )

def test_evaluate_insufficient_evidence():
    # When no impact records exist, must return INSUFFICIENT_EVIDENCE, not fake F1
    res = evaluate_warning_impact_alignment([], [{"timestamp": "2023-12-04T08:00:00Z"}])
    assert res["status"] == "INSUFFICIENT_EVIDENCE"
    assert res["f1_score"] is None
    assert res["precision"] is None

def test_evaluate_warning_match():
    impacts = [{
        "event_id": "IMP-01",
        "latitude": 13.08,
        "longitude": 80.27,
        "start_time": "2023-12-04T12:00:00Z"
    }]
    warnings = [{
        "latitude": 13.08,
        "longitude": 80.27,
        "timestamp": "2023-12-04T08:00:00Z" # 4h lead time
    }]
    res = evaluate_warning_impact_alignment(impacts, warnings, radius_km=5.0, time_window_hours=6.0)
    assert res["status"] == "EVALUATED"
    assert res["matched_events_count"] == 1
    assert res["recall"] == 1.0
    assert res["warning_lead_time_hours_mean"] == 4.0

def test_evaluate_requires_warning_evidence():
    impacts = [{"event_id": "IMP-01", "latitude": 13.08, "longitude": 80.27, "start_time": "2023-12-04T12:00:00Z"}]
    res = evaluate_warning_impact_alignment(impacts, [])
    assert res["status"] == "INSUFFICIENT_EVIDENCE"
    assert res["precision"] is None
