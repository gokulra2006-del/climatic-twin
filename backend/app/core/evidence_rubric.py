"""
Evidence-Confidence Rubric Engine (0–100 Points)
=================================================
Calculates traceable empirical confidence scores strictly for reviewed, source-backed impact records.

Rubric criteria:
  - 25 points: Authoritative primary source (CWC, IMD, GCC, TNSDMA, CMWSSB, NDMA, Official Gazette)
  - 20 points: Exact event date/time verified (specific onset hour/minute, not vague multi-day span)
  - 20 points: Precise location or ward/road/asset coordinates (accuracy <= 500m or specific asset pin)
  - 20 points: Independent corroborating source (distinct organization / secondary official report)
  - 15 points: Observed physical impact measurement (flood extent sqkm, water depth m, road closure hrs, outage hrs, hospital access)

Total Maximum: 100 points.

Research-Integrity Rules:
  - Synthetic records receive NO score (total_score=None, display="Add verified source").
  - Never infer flood events from rainfall or drainage context alone.
  - Never convert synthetic data to Historical Real without verified primary documentation.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

AUTHORITATIVE_ORGANISATIONS = [
    "central water commission",
    "cwc",
    "india meteorological department",
    "imd",
    "greater chennai corporation",
    "gcc",
    "tamil nadu state disaster management authority",
    "tnsdma",
    "chennai metropolitan water supply and sewerage board",
    "cmwssb",
    "water resources department",
    "wrd",
    "tamil nadu generation and distribution corporation",
    "tangedco",
    "national disaster management authority",
    "ndma",
    "state disaster management authority",
    "government of tamil nadu",
    "government of india",
    "chennai traffic police",
    "108 gvk emri",
    "nrsc / isro disaster management support"
]

def is_authoritative_source(source_org: Optional[str], source_name: Optional[str], source_url: Optional[str]) -> bool:
    """Checks whether the source is from an authoritative government or municipal body."""
    combined = f"{source_org or ''} {source_name or ''} {source_url or ''}".lower()
    if not source_url:
        return False
    # Check for official domains
    if any(domain in combined for domain in [".gov.in", ".nic.in", "cwc.gov.in", "imd.gov.in", "chennaicorporation.gov.in", "tnsdma.tn.gov.in"]):
        return True
    return any(auth in combined for auth in AUTHORITATIVE_ORGANISATIONS)

def calculate_evidence_rubric(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Computes transparent evidence confidence breakdown for an impact record.
    Returns score (0-100), itemized breakdown, and missing evidence items.
    """
    status = str(record.get("evidence_status", "")).strip().lower()
    
    # Strictly exclude synthetic records from scoring
    if status == "synthetic":
        return {
            "total_score": None,
            "confidence_ratio": None,
            "score_display": "Add verified source",
            "is_synthetic": True,
            "eligible_for_score": False,
            "breakdown": {
                "authoritative_primary_source": {
                    "points": 0, "max_points": 25, "achieved": False,
                    "evidence": "Synthetic records have no authoritative primary source"
                },
                "exact_datetime": {
                    "points": 0, "max_points": 20, "achieved": False,
                    "evidence": "Synthetic timestamps are demonstration-only"
                },
                "precise_location": {
                    "points": 0, "max_points": 20, "achieved": False,
                    "evidence": "Synthetic coordinates are not verified municipal points"
                },
                "independent_corroborating_source": {
                    "points": 0, "max_points": 20, "achieved": False,
                    "evidence": "No independent corroboration"
                },
                "observed_impact_measurement": {
                    "points": 0, "max_points": 15, "achieved": False,
                    "evidence": "No observed ground-truth telemetry or survey measurement"
                }
            },
            "missing_items": [
                "Authoritative primary government/municipal source URL",
                "Curator review and verification",
                "Exact observed event timestamp",
                "Precise surveyed coordinates or ward/road/asset pin",
                "Independent corroborating source",
                "Observed physical impact measurement (depth, extent, duration)"
            ],
            "reviewer_name": record.get("reviewer_name"),
            "review_timestamp": record.get("review_timestamp"),
            "reason": "Synthetic demonstration records are strictly excluded from confidence scoring until real verified sources are attached."
        }
    
    # 1. Authoritative primary source (25 pts)
    source_url = record.get("source_url")
    source_org = record.get("source_org")
    source_name = record.get("source_name")
    
    auth_ok = is_authoritative_source(source_org, source_name, source_url)
    pts_auth = 25 if auth_ok else (10 if source_url else 0)
    
    # 2. Exact event date/time (20 pts)
    exact_time_verified = bool(record.get("exact_time_verified", False))
    start_time_raw = record.get("start_time")
    # Also grant if start_time specifies explicit non-midnight hour and end_time is documented within 48h
    if not exact_time_verified and start_time_raw:
        st_str = str(start_time_raw)
        if "T" in st_str:
            time_part = st_str.split("T")[1][:5]
            if time_part not in ("00:00", ""):
                exact_time_verified = True
    
    pts_datetime = 20 if exact_time_verified else 0
    
    # 3. Precise location or ward/road/asset coordinates (20 pts)
    prec_type = record.get("location_precision_type", "ward_centroid")
    accuracy_m = record.get("location_accuracy_m")
    
    # Exact coordinates within 500m or specific asset landmark / road stretch
    is_precise = False
    if prec_type in ["exact_gps", "asset_landmark", "road_stretch"]:
        is_precise = True
    elif accuracy_m is not None and float(accuracy_m) <= 500.0:
        is_precise = True
    elif prec_type == "ward_centroid" and accuracy_m is not None and float(accuracy_m) <= 1500.0:
        is_precise = False  # ward centroid is not precise enough for full 20 pts
        pts_loc = 10
    else:
        is_precise = False
        pts_loc = 0
        
    if is_precise:
        pts_loc = 20
        
    # 4. Independent corroborating source (20 pts)
    corrob_url = record.get("corroborating_source_url")
    has_corrob = bool(corrob_url and corrob_url.strip() and corrob_url.strip() != (source_url or "").strip())
    pts_corrob = 20 if has_corrob else 0
    
    # 5. Observed impact measurement (15 pts)
    # Check for flood extent sqkm, flood depth m, road closure hours, outage hours, hospital access cut, or gauge level
    observed_measurements = []
    if record.get("observed_flood_extent_sqkm") is not None and float(record.get("observed_flood_extent_sqkm") or 0) > 0:
        observed_measurements.append(f"Flood extent: {record['observed_flood_extent_sqkm']} sq km")
    if record.get("observed_flood_depth_m") is not None and float(record.get("observed_flood_depth_m") or 0) > 0:
        observed_measurements.append(f"Water depth: {record['observed_flood_depth_m']} m")
    if record.get("road_closure_duration_hours") is not None and float(record.get("road_closure_duration_hours") or 0) > 0:
        observed_measurements.append(f"Road closure: {record['road_closure_duration_hours']} hrs")
    if record.get("power_outage_duration_hours") is not None and float(record.get("power_outage_duration_hours") or 0) > 0:
        observed_measurements.append(f"Power outage: {record['power_outage_duration_hours']} hrs")
    if record.get("hospital_access_cut") is not None:
        observed_measurements.append(f"Hospital access disruption verified: {record['hospital_access_cut']}")
    if record.get("gauge_level_m") is not None and float(record.get("gauge_level_m") or 0) > 0:
        observed_measurements.append(f"Gauge level: {record['gauge_level_m']} m")
        
    pts_measurement = 15 if len(observed_measurements) > 0 else 0
    
    total_score = pts_auth + pts_datetime + pts_loc + pts_corrob + pts_measurement
    confidence_ratio = round(total_score / 100.0, 2)
    
    missing_items = []
    if not auth_ok:
        missing_items.append("Authoritative primary government/municipal source (CWC, IMD, GCC, TNSDMA, CMWSSB)")
    if not exact_time_verified:
        missing_items.append("Exact event onset timestamp verification (minute/hour precision)")
    if not is_precise:
        missing_items.append("Sub-500m coordinates or surveyed road/asset landmark coordinates")
    if not has_corrob:
        missing_items.append("Independent corroborating source URL from separate organization")
    if len(observed_measurements) == 0:
        missing_items.append("Observed physical measurement (flood extent sq km, water depth m, or closure duration)")
        
    # Reason explanation
    reasons = []
    if pts_auth == 25:
        reasons.append(f"Primary source '{source_org or source_name}' verified (+25 pts)")
    elif pts_auth > 0:
        reasons.append("Web source attached but agency is not primary official authority (+10 pts)")
    else:
        reasons.append("No source URL attached (+0 pts)")
        
    if pts_datetime == 20:
        reasons.append("Event onset date and time confirmed (+20 pts)")
    else:
        reasons.append("Multi-day window without exact onset timestamp (+0 pts)")
        
    if pts_loc == 20:
        reasons.append(f"Location coordinates verified ({prec_type}, <=500m) (+20 pts)")
    elif pts_loc == 10:
        reasons.append("Ward-level centroid only (+10 pts)")
    else:
        reasons.append("Citywide centroid without localized coordinates (+0 pts)")
        
    if pts_corrob == 20:
        reasons.append("Independent secondary corroborating source verified (+20 pts)")
        
    if pts_measurement == 15:
        reasons.append(f"Physical measurement recorded ({', '.join(observed_measurements)}) (+15 pts)")
        
    return {
        "total_score": total_score,
        "confidence_ratio": confidence_ratio,
        "score_display": f"{total_score}/100",
        "is_synthetic": False,
        "eligible_for_score": True,
        "breakdown": {
            "authoritative_primary_source": {
                "points": pts_auth,
                "max_points": 25,
                "achieved": auth_ok,
                "evidence": f"{source_org or source_name or 'None'} ({source_url or 'no URL'})"
            },
            "exact_datetime": {
                "points": pts_datetime,
                "max_points": 20,
                "achieved": exact_time_verified,
                "evidence": f"Verified: {exact_time_verified}; Start: {start_time_raw}"
            },
            "precise_location": {
                "points": pts_loc,
                "max_points": 20,
                "achieved": is_precise,
                "evidence": f"Precision type: {prec_type}; Accuracy: {accuracy_m}m"
            },
            "independent_corroborating_source": {
                "points": pts_corrob,
                "max_points": 20,
                "achieved": has_corrob,
                "evidence": corrob_url or "None"
            },
            "observed_impact_measurement": {
                "points": pts_measurement,
                "max_points": 15,
                "achieved": len(observed_measurements) > 0,
                "evidence": "; ".join(observed_measurements) if observed_measurements else "None"
            }
        },
        "missing_items": missing_items,
        "reviewer_name": record.get("reviewer_name"),
        "review_timestamp": record.get("review_timestamp"),
        "reason": "; ".join(reasons)
    }
