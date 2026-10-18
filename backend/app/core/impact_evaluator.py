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
    Evaluates submitted model-run warnings against documented impact records.
    The function deliberately refuses to compute a score when either labels or
    warnings are absent; it must never manufacture a benchmark score.
    """
    if not impact_records:
        return {
            "status": "INSUFFICIENT_EVIDENCE",
            "total_impact_records": 0,
            "matched_events_count": 0,
            "event_detection_rate": None,
            "false_alarms": None,
            "warning_lead_time_hours_mean": None,
            "precision": None,
            "recall": None,
            "f1_score": None,
            "evidence_note": "No documented impact records found in the selected temporal/spatial envelope.",
            "provenance": "EVALUATION UTILITY — RULE-BASED MATCHING"
        }

    if not warnings:
        return {
            "status": "INSUFFICIENT_EVIDENCE",
            "total_impact_records": len(impact_records),
            "matched_events_count": 0,
            "event_detection_rate": None,
            "false_alarms": None,
            "warning_lead_time_hours_mean": None,
            "precision": None,
            "recall": None,
            "f1_score": None,
            "evidence_note": "Impact labels are available, but no exported model-run warnings were supplied for evaluation.",
            "provenance": "EVALUATION UTILITY — AWAITING MODEL-RUN WARNINGS"
        }

    # Match each impact record to nearest prior warning
    true_positives = 0
    matched_impact_ids = set()
    lead_times = []

    for imp in impact_records:
        imp_lat = imp["latitude"]
        imp_lon = imp["longitude"]
        imp_time = pd.to_datetime(imp["start_time"])

        best_lead_time = None
        for w in warnings:
            w_lat = w.get("latitude", imp_lat)
            w_lon = w.get("longitude", imp_lon)
            w_time = pd.to_datetime(w["timestamp"])

            dist = haversine_distance_km(imp_lat, imp_lon, w_lat, w_lon)
            if dist <= radius_km:
                # Check time: Warning must precede or be near impact start time
                diff_hours = (imp_time - w_time).total_seconds() / 3600.0
                if 0 <= diff_hours <= time_window_hours:
                    if best_lead_time is None or diff_hours > best_lead_time:
                        best_lead_time = diff_hours

        if best_lead_time is not None:
            true_positives += 1
            matched_impact_ids.add(imp["event_id"])
            lead_times.append(best_lead_time)

    total_impacts = len(impact_records)
    total_warnings = len(warnings)

    false_negatives = total_impacts - true_positives
    false_positives = max(0, total_warnings - true_positives)

    recall = float(true_positives / total_impacts) if total_impacts > 0 else 0.0
    precision = float(true_positives / (true_positives + false_positives)) if (true_positives + false_positives) > 0 else 0.0
    f1 = float(2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
    det_rate = recall
    mean_lead_time = float(np.mean(lead_times)) if lead_times else 0.0

    return {
        "status": "EVALUATED",
        "total_impact_records": total_impacts,
        "matched_events_count": true_positives,
        "event_detection_rate": round(det_rate, 4),
        "false_alarms": int(false_positives),
        "warning_lead_time_hours_mean": round(mean_lead_time, 2),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "evidence_note": f"Evaluated against {total_impacts} recorded ground-truth/proxy events with spatial tolerance {radius_km} km.",
        "provenance": "EVALUATION UTILITY — HISTORICAL REAL & PROXY MATCHING"
    }
