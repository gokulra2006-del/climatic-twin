import pytest
from datetime import datetime, timezone
from app.schemas.impact_record import ImpactRecordCreate
from app.core.impact_evaluator import evaluate_warning_impact_alignment, haversine_distance_km

def test_haversine_distance():
    # Central Chennai (13.0827, 80.2707) to Adyar Estuary (13.0100, 80.2600) ~ 8.1 km
    d = haversine_distance_km(13.0827, 80.2707, 13.0100, 80.2600)
    assert 7.5 < d < 9.0

def test_impact_record_validation():
    # Valid record with required authoritative source_org and source_url
    valid = ImpactRecordCreate(
        event_id="TEST-01",
        start_time=datetime.now(timezone.utc),
        latitude=13.08,
        longitude=80.27,
        zone="Zone 5",
        impact_type="waterlogging",
        severity="high",
        source_name="GCC Stormwater Report",
        source_org="Greater Chennai Corporation",
        source_url="https://chennaicorporation.gov.in/report.pdf",
        evidence_status="historical_real",
        confidence=0.9
    )
    assert valid.impact_type == "waterlogging"
    assert valid.source_org == "Greater Chennai Corporation"

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

    # Missing source_url for historical_real must fail
    with pytest.raises(ValueError):
        ImpactRecordCreate(
            event_id="TEST-03", start_time=datetime.now(timezone.utc), latitude=13.08,
            longitude=80.27, zone="Zone 5", impact_type="waterlogging",
            source_name="Unlinked source", evidence_status="historical_real"
        )

    # Missing source_org for historical_real must fail
    with pytest.raises(ValueError):
        ImpactRecordCreate(
            event_id="TEST-04", start_time=datetime.now(timezone.utc), latitude=13.08,
            longitude=80.27, zone="Zone 5", impact_type="waterlogging",
            source_name="Linked source without org",
            source_url="https://example.org/source",
            evidence_status="historical_real"
        )

def test_evaluate_insufficient_evidence():
    # When no impact records exist, must return INSUFFICIENT_EVIDENCE, not fake F1
    res = evaluate_warning_impact_alignment([], [{"timestamp": "2023-12-04T08:00:00Z"}])
    assert res["status"] == "INSUFFICIENT_EVIDENCE"
    assert res["f1_score"] is None
    assert res["precision"] is None

def test_evaluate_warning_match():
    # Only historical_real records are evaluated
    impacts = [{
        "event_id": "IMP-01",
        "latitude": 13.08,
        "longitude": 80.27,
        "start_time": "2023-12-04T12:00:00Z",
        "evidence_status": "historical_real"
    }]
    warnings = [{
        "latitude": 13.08,
        "longitude": 80.27,
        "timestamp": "2023-12-04T08:00:00Z", # 4h lead time
        "probability": 0.85
    }]
    res = evaluate_warning_impact_alignment(impacts, warnings, radius_km=5.0, time_window_hours=6.0)
    assert res["status"] == "EVALUATED"
    assert res["matched_events_count"] == 1
    assert res["recall"] == 1.0
    assert res["warning_lead_time_hours_mean"] == 4.0
    assert res["brier_score"] is not None
    assert res["sample_size_n"] == 1
    assert "CRITICAL RESEARCH LIMITATION" in res["sample_size_warning"]

def test_evaluate_synthetic_records_are_strictly_excluded():
    # Test that synthetic records are not counted in empirical evaluation
    impacts = [
        {"event_id": "IMP-SYNTH-01", "latitude": 13.08, "longitude": 80.27, "start_time": "2023-12-04T12:00:00Z", "evidence_status": "synthetic"},
        {"event_id": "IMP-PROXY-01", "latitude": 13.08, "longitude": 80.27, "start_time": "2023-12-04T12:00:00Z", "evidence_status": "proxy"}
    ]
    warnings = [{"latitude": 13.08, "longitude": 80.27, "timestamp": "2023-12-04T08:00:00Z", "probability": 0.9}]
    res = evaluate_warning_impact_alignment(impacts, warnings)
    assert res["status"] == "INSUFFICIENT_EVIDENCE"
    assert res["eligible_historical_real_records"] == 0
    assert res["excluded_synthetic_proxy_records"] == 2

def test_evaluate_requires_warning_evidence():
    impacts = [{"event_id": "IMP-01", "latitude": 13.08, "longitude": 80.27, "start_time": "2023-12-04T12:00:00Z", "evidence_status": "historical_real"}]
    res = evaluate_warning_impact_alignment(impacts, [])
    assert res["status"] == "INSUFFICIENT_EVIDENCE"
    assert res["precision"] is None
