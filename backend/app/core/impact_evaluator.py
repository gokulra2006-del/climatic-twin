import math
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

def evaluate_warning_impact_alignment(
    impact_records: List[Dict[str, Any]],
    warnings: List[Dict[str, Any]],
    radius_km: float = 5.0,
    time_window_hours: float = 6.0
) -> Dict[str, Any]:
    """
    Evaluates submitted model-run warnings strictly against verified ground-truth (historical_real) impact records.
    Synthetic and proxy records are strictly excluded from empirical performance metrics.
    Computes Precision, Recall, F1, Lead Time, Brier Score, and Sample Size warnings.
    """
    total_provided = len(impact_records)
    # Filter strictly for historical_real records with verified sources
    eligible_impacts = [
        r for r in impact_records 
        if str(r.get("evidence_status", "")).strip().lower() == "historical_real"
    ]
    excluded_count = total_provided - len(eligible_impacts)
    
    if not eligible_impacts:
        return {
            "status": "INSUFFICIENT_EVIDENCE",
            "total_impact_records": total_provided,
            "eligible_historical_real_records": 0,
            "excluded_synthetic_proxy_records": excluded_count,
            "matched_events_count": 0,
            "event_detection_rate": None,
            "false_alarms": None,
            "warning_lead_time_hours_mean": None,
            "precision": None,
            "recall": None,
            "f1_score": None,
            "brier_score": None,
            "sample_size_n": 0,
            "sample_size_warning": "No verified 'historical_real' impact records found in the selected temporal/spatial envelope. Synthetic/proxy records are strictly excluded from empirical performance calculation.",
            "evidence_note": f"Excluded {excluded_count} unverified/synthetic/proxy records. Empirical validation requires verified official sources.",
            "provenance": "EVALUATION UTILITY — STRICT HISTORICAL REAL BENCHMARKING"
        }

    if not warnings:
        return {
            "status": "INSUFFICIENT_EVIDENCE",
            "total_impact_records": total_provided,
            "eligible_historical_real_records": len(eligible_impacts),
            "excluded_synthetic_proxy_records": excluded_count,
            "matched_events_count": 0,
            "event_detection_rate": None,
            "false_alarms": None,
            "warning_lead_time_hours_mean": None,
            "precision": None,
            "recall": None,
            "f1_score": None,
            "brier_score": None,
            "sample_size_n": len(eligible_impacts),
            "sample_size_warning": None,
            "evidence_note": f"{len(eligible_impacts)} verified historical labels are available, but no exported model-run warnings were supplied for evaluation.",
            "provenance": "EVALUATION UTILITY — AWAITING MODEL-RUN WARNINGS"
        }

    # Match each verified impact record to nearest prior warning
    true_positives = 0
    matched_impact_ids = set()
    matched_warning_indices = set()
    lead_times = []

    for imp in eligible_impacts:
        imp_lat = float(imp["latitude"])
        imp_lon = float(imp["longitude"])
        imp_time = pd.to_datetime(imp["start_time"], utc=True)

        best_lead_time = None
        best_warning_idx = None

        for w_idx, w in enumerate(warnings):
            w_lat = float(w.get("latitude", imp_lat))
            w_lon = float(w.get("longitude", imp_lon))
            w_time = pd.to_datetime(w["timestamp"], utc=True)

            dist = haversine_distance_km(imp_lat, imp_lon, w_lat, w_lon)
            if dist <= radius_km:
                # Warning must precede or be near impact start time
                diff_hours = (imp_time - w_time).total_seconds() / 3600.0
                if 0 <= diff_hours <= time_window_hours:
                    if best_lead_time is None or diff_hours > best_lead_time:
                        best_lead_time = diff_hours
                        best_warning_idx = w_idx

        if best_lead_time is not None:
            true_positives += 1
            matched_impact_ids.add(imp["event_id"])
            matched_warning_indices.add(best_warning_idx)
            lead_times.append(best_lead_time)

    total_real_impacts = len(eligible_impacts)
    total_warnings = len(warnings)

    false_negatives = total_real_impacts - true_positives
    false_positives = max(0, total_warnings - true_positives)

    recall = float(true_positives / total_real_impacts) if total_real_impacts > 0 else 0.0
    precision = float(true_positives / (true_positives + false_positives)) if (true_positives + false_positives) > 0 else 0.0
    f1 = float(2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
    det_rate = recall
    mean_lead_time = float(np.mean(lead_times)) if lead_times else 0.0

    # Calculate Brier Score across warnings:
    # For each warning w: outcome = 1.0 if it triggered a hit, 0.0 if false alarm
    brier_sq_errors = []
    for w_idx, w in enumerate(warnings):
        prob = float(w.get("probability", 0.5))
        outcome = 1.0 if w_idx in matched_warning_indices else 0.0
        brier_sq_errors.append((prob - outcome) ** 2)
    brier_score = float(np.mean(brier_sq_errors)) if brier_sq_errors else None

    # Sample size warning
    sample_size_n = total_real_impacts
    if sample_size_n < 10:
        sample_warning = (
            f"CRITICAL RESEARCH LIMITATION: Sample size (N={sample_size_n}) is statistically underpowered for "
            "academic conference/journal performance claims. Minimum recommended N >= 30 verified historical events "
            "across multiple monsoon seasons."
        )
    elif sample_size_n < 30:
        sample_warning = (
            f"RESEARCH NOTE: Sample size (N={sample_size_n}) is exploratory. Results should be reported as case study "
            "validation rather than generalized empirical proof."
        )
    else:
        sample_warning = None

    return {
        "status": "EVALUATED",
        "total_impact_records": total_provided,
        "eligible_historical_real_records": total_real_impacts,
        "excluded_synthetic_proxy_records": excluded_count,
        "matched_events_count": true_positives,
        "event_detection_rate": round(det_rate, 4),
        "false_alarms": int(false_positives),
        "warning_lead_time_hours_mean": round(mean_lead_time, 2),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "brier_score": round(brier_score, 4) if brier_score is not None else None,
        "sample_size_n": sample_size_n,
        "sample_size_warning": sample_warning,
        "evidence_note": (
            f"Strict empirical evaluation against {total_real_impacts} verified historical real records. "
            f"Excluded {excluded_count} synthetic/proxy records. Spatial radius: {radius_km} km, time window: {time_window_hours} hrs."
        ),
        "provenance": "HISTORICAL REAL ONLY MATCHING (Empirical Benchmark)"
    }
