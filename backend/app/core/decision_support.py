"""
Research-Grade Decision Support & Adaptive Early-Warning Policy Engine (Phase 17)
ClimateTwin Chennai Project

SCIENTIFIC TRANSPARENCY:
- Decision Support Score (DSS) uses PROTOTYPE weights requiring domain-expert calibration.
- Operational actions are RECOMMENDATIONS, not autonomous emergency commands.
- Synthetic benchmark scenarios are labeled SIMULATED DECISION-SUPPORT BENCHMARK.
- This system is DECISION SUPPORT, not an autonomous emergency authority.
- All outputs are RULE-BASED and DERIVED from upstream phase outputs.

CONSUMED UPSTREAM PHASES:
- Phase 10: Flood probability & forecast horizons
- Phase 11: Uncertainty level, width, epistemic variance
- Phase 13: Compound risk score, dominant hazard, active interactions
- Phase 14: Asset Risk Index (ARI), criticality weight, exposure score
- Phase 15: Spatial flood impact index, zone priority
- Phase 16: Sensor health score, quality tier, data quality gate
"""

import os
import json
import logging
import numpy as np
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from copy import deepcopy

logger = logging.getLogger(__name__)

# ============================================================
# CONFIGURATION — All weights and thresholds stored explicitly
# ============================================================

MODEL_VERSION = "CLIMATETWIN_DSS_v1.0_PROTOTYPE"

# Documented Expert Fallback Defaults
EXPERT_DSS_WEIGHTS = {
    "hazard_severity": 0.30,
    "asset_risk": 0.20,
    "compound_risk": 0.15,
    "forecast_confidence": 0.15,
    "data_quality": 0.10,
    "persistence": 0.10
}

EXPERT_DECISION_THRESHOLDS = {
    "NORMAL": {"min": 0.00, "max": 0.40},
    "MONITOR": {"min": 0.40, "max": 0.55},
    "PREPARE": {"min": 0.55, "max": 0.70},
    "ALERT":  {"min": 0.70, "max": 0.85},
    "EMERGENCY": {"min": 0.85, "max": 1.00}
}

EXPERT_CASCADE_STRENGTHS = {
    "cascade_reservoir": 0.15,
    "cascade_deluge": 0.10
}

# Runtime weights (initialized with expert values, overwritten if calibrated params exist)
DSS_WEIGHTS = dict(EXPERT_DSS_WEIGHTS)
DECISION_THRESHOLDS = deepcopy(EXPERT_DECISION_THRESHOLDS)
CASCADE_STRENGTHS = dict(EXPERT_CASCADE_STRENGTHS)
PARAMETER_SOURCE = "EXPERT_FALLBACK"

def _load_calibrated_decision_params():
    global DSS_WEIGHTS, DECISION_THRESHOLDS, CASCADE_STRENGTHS, PARAMETER_SOURCE
    params_file = os.path.join(os.path.dirname(__file__), "calibrated_params.json")
    if os.path.exists(params_file):
        try:
            with open(params_file, "r", encoding="utf-8") as f:
                calibrated = json.load(f)
            if "decision_support" in calibrated:
                ds = calibrated["decision_support"]
                if "dss_weights" in ds:
                    DSS_WEIGHTS.update(ds["dss_weights"])
                if "decision_thresholds" in ds:
                    DECISION_THRESHOLDS.update(ds["decision_thresholds"])
                if "cascade_strengths" in ds:
                    CASCADE_STRENGTHS.update(ds["cascade_strengths"])
                PARAMETER_SOURCE = "CALIBRATED_DATA_FIT"
                logger.info("Loaded calibrated decision support weights from calibrated_params.json")
        except Exception as e:
            logger.warning(f"Failed to load calibrated_params.json for decision support; using expert fallback: {e}")

_load_calibrated_decision_params()

HYSTERESIS_BAND = 0.10

UNCERTAINTY_DECISION_MATRIX = {
    ("HIGH", "LOW"):      {"modifier": "STRONG_ESCALATION", "confidence": "HIGH", "action": "Immediate escalation with high confidence"},
    ("HIGH", "MODERATE"):  {"modifier": "ESCALATION", "confidence": "MODERATE", "action": "Escalation with moderate verification"},
    ("HIGH", "HIGH"):     {"modifier": "PRECAUTIONARY_ESCALATION", "confidence": "LOW", "action": "Precautionary escalation; verification required"},
    ("MODERATE", "LOW"):  {"modifier": "PREPAREDNESS", "confidence": "HIGH", "action": "Monitoring and preparedness activation"},
    ("MODERATE", "MODERATE"): {"modifier": "ENHANCED_MONITORING", "confidence": "MODERATE", "action": "Enhanced monitoring with local verification"},
    ("MODERATE", "HIGH"): {"modifier": "VERIFICATION_REQUIRED", "confidence": "LOW", "action": "Enhanced monitoring; local verification required"},
    ("LOW", "LOW"):       {"modifier": "NOMINAL", "confidence": "HIGH", "action": "Routine surveillance"},
    ("LOW", "MODERATE"):  {"modifier": "NOMINAL_WATCH", "confidence": "MODERATE", "action": "Routine surveillance with periodic check"},
    ("LOW", "HIGH"):      {"modifier": "SAFETY_UNCONFIRMED", "confidence": "LOW", "action": "Do not declare safety; request telemetry verification"}
}

DQ_GATE_THRESHOLDS = {
    "PASS": {"min_aggregate_shs": 0.70, "max_degraded_critical": 0},
    "DEGRADED": {"min_aggregate_shs": 0.45, "max_degraded_critical": 2},
    "BLOCKED": {"min_aggregate_shs": 0.00, "max_degraded_critical": 99}
}

RECOMMENDED_ACTIONS = {
    "NORMAL": "Maintain routine environmental surveillance. No immediate action required.",
    "MONITOR": "Increase telemetry sampling frequency. Monitor weather forecasts and reservoir levels.",
    "PREPARE": "Activate preparedness protocols. Pre-position flood response teams. Alert vulnerable communities.",
    "ALERT": "Deploy local flood response teams. Issue public warnings for high-risk zones. Verify reservoir telemetry.",
    "EMERGENCY": "Full emergency mobilization. Evacuate high-risk low-lying areas. Open emergency operations center."
}

VERIFICATION_TEMPLATES = {
    "HIGH_UNCERTAINTY": "Verify prediction with independent meteorological source before full escalation",
    "DEGRADED_TELEMETRY": "Confirm observation data from backup or manual field verification",
    "STALE_RESERVOIR": "Request manual reservoir gauge reading from CMWSSB field operator",
    "CROSS_SOURCE_DISAGREEMENT": "Reconcile conflicting satellite and ground station measurements",
    "ANOMALY_DETECTED": "Inspect flagged anomalous sensor reading for hardware fault or extreme event",
    "CRITICAL_ASSET_EXPOSED": "Dispatch rapid infrastructure assessment team to high-risk asset",
    "BLOCKED_DATA": "Decision confidence severely degraded; require manual situation assessment before action"
}

THRESHOLDS_DISCLAIMER = (
    "PROTOTYPE RESEARCH THRESHOLDS: These decision thresholds are preliminary research values. "
    "Operational deployment requires calibration by domain experts, emergency management authorities, "
    "and local stakeholders. This system provides decision support only and is not an autonomous "
    "emergency authority. Synthetic scenarios do not represent real emergency decisions."
)


class DecisionSupportEngine:
    """
    Phase 17 Decision Support & Adaptive Early-Warning Policy Engine.
    """

    def __init__(self):
        self.decision_history: List[Dict[str, Any]] = []
        self.current_decision_level: str = "NORMAL"
        self.current_dss: float = 0.0
        self.parameter_source = PARAMETER_SOURCE

    def normalize_hazard_severity(self, flood_probability=0.10, compound_risk_score=0.15, dominant_hazard_intensity=0.10):
        h = flood_probability * 0.50 + compound_risk_score * 0.30 + dominant_hazard_intensity * 0.20
        return float(np.clip(h, 0.0, 1.0))

    def normalize_asset_risk(self, max_asset_risk_index=0.30, mean_criticality_weight=0.50, max_exposure_score=0.30):
        a = max_asset_risk_index * 0.50 + mean_criticality_weight * 0.25 + max_exposure_score * 0.25
        return float(np.clip(a, 0.0, 1.0))

    def normalize_compound_risk(self, compound_risk_score=0.15):
        return float(np.clip(compound_risk_score, 0.0, 1.0))

    def normalize_forecast_confidence(self, uncertainty_level="LOW", uncertainty_width=0.15, epistemic_variance=0.01):
        level_map = {"LOW": 0.90, "MODERATE": 0.60, "HIGH": 0.25}
        base = level_map.get(uncertainty_level, 0.50)
        width_penalty = min(0.30, uncertainty_width * 0.40)
        var_penalty = min(0.20, epistemic_variance * 2.0)
        confidence = base - width_penalty - var_penalty
        return float(np.clip(confidence, 0.0, 1.0))

    def normalize_data_quality(self, aggregate_shs=0.95, num_degraded=0, num_anomalous=0, num_missing=0):
        base = aggregate_shs
        penalty = num_degraded * 0.05 + num_anomalous * 0.08 + num_missing * 0.12
        return float(np.clip(base - penalty, 0.0, 1.0))

    def normalize_persistence(self, consecutive_elevated_cycles=0, trend_direction="STABLE"):
        base = min(1.0, consecutive_elevated_cycles * 0.15)
        if trend_direction == "RISING":
            base = min(1.0, base + 0.20)
        elif trend_direction == "FALLING":
            base = max(0.0, base - 0.15)
        return float(np.clip(base, 0.0, 1.0))

    def evaluate_data_quality_gate(self, aggregate_shs=0.95, source_health_states=None, num_anomalous=0):
        if source_health_states is None:
            source_health_states = ["HEALTHY"] * 8
        degraded_count = sum(1 for s in source_health_states if s in ["DEGRADED", "STALE"])
        anomalous_in_states = sum(1 for s in source_health_states if s == "ANOMALOUS")
        eff_anomalous = max(num_anomalous, anomalous_in_states)
        missing_count = sum(1 for s in source_health_states if s in ["MISSING", "OFFLINE"])
        total_unhealthy = degraded_count + missing_count + eff_anomalous
        reasons = []
        if aggregate_shs >= 0.70 and total_unhealthy <= 1:
            gate_state = "PASS"
            reasons.append("All critical telemetry sources operational")
        elif aggregate_shs >= 0.45 and total_unhealthy <= 4:
            gate_state = "DEGRADED"
            if degraded_count > 0:
                reasons.append(f"{degraded_count} source(s) degraded or stale")
            if eff_anomalous > 0:
                reasons.append(f"{eff_anomalous} anomalous reading(s) detected")
            reasons.append("Decision confidence downgraded; verification recommended")
        else:
            gate_state = "BLOCKED"
            reasons.append(f"Critical telemetry failure: {missing_count} offline, {degraded_count} degraded")
            reasons.append("Automatic all-clear BLOCKED; require manual situation assessment")
        return {
            "gate_state": gate_state,
            "aggregate_shs": round(aggregate_shs, 3),
            "degraded_sources": degraded_count,
            "missing_sources": missing_count,
            "anomalous_readings": eff_anomalous,
            "gate_reasons": reasons
        }

    def evaluate_uncertainty_modifier(self, probability_level="LOW", uncertainty_level="LOW"):
        key = (probability_level, uncertainty_level)
        result = UNCERTAINTY_DECISION_MATRIX.get(key, {"modifier": "NOMINAL", "confidence": "MODERATE", "action": "Standard monitoring"})
        return deepcopy(result)

    def calculate_dss(self, hazard_severity, asset_risk, compound_risk, forecast_confidence, data_quality, persistence):
        dss = (
            DSS_WEIGHTS["hazard_severity"] * hazard_severity +
            DSS_WEIGHTS["asset_risk"] * asset_risk +
            DSS_WEIGHTS["compound_risk"] * compound_risk +
            DSS_WEIGHTS["forecast_confidence"] * forecast_confidence +
            DSS_WEIGHTS["data_quality"] * data_quality +
            DSS_WEIGHTS["persistence"] * persistence
        )
        return float(np.clip(dss, 0.0, 1.0))

    def classify_decision_level(self, dss, previous_level=None):
        levels = ["NORMAL", "MONITOR", "PREPARE", "ALERT", "EMERGENCY"]
        raw_level = "NORMAL"
        for level_name in levels:
            t = DECISION_THRESHOLDS[level_name]
            if t["min"] <= dss < t["max"]:
                raw_level = level_name
                break
        if dss >= 1.0:
            raw_level = "EMERGENCY"
        if previous_level is None:
            return raw_level
        prev_idx = levels.index(previous_level)
        raw_idx = levels.index(raw_level)
        if raw_idx > prev_idx:
            return raw_level
        if raw_idx < prev_idx:
            prev_threshold_min = DECISION_THRESHOLDS[previous_level]["min"]
            deescalation_threshold = prev_threshold_min - HYSTERESIS_BAND
            if dss < deescalation_threshold:
                return raw_level
            else:
                return previous_level
        return raw_level

    def evaluate_asset_decision(self, asset_code, asset_name, asset_risk_index, criticality_weight, exposure_score, risk_level, city_decision_level, uncertainty_level="LOW", dq_gate="PASS"):
        priority_score = round(asset_risk_index * criticality_weight, 3)
        if asset_risk_index >= 0.75 and criticality_weight >= 0.75:
            asset_decision = "EMERGENCY"
            action = f"IMMEDIATE emergency inspection and response at {asset_name}"
        elif asset_risk_index >= 0.50 and criticality_weight >= 0.75:
            asset_decision = "ALERT"
            action = f"Deploy response team and increase monitoring at {asset_name}"
        elif asset_risk_index >= 0.50:
            asset_decision = "PREPARE"
            action = f"Activate preparedness protocols for {asset_name}"
        elif asset_risk_index >= 0.30:
            asset_decision = "MONITOR"
            action = f"Increase telemetry sampling for {asset_name}"
        else:
            asset_decision = "NORMAL"
            action = f"Routine surveillance of {asset_name}"
        verification = []
        if uncertainty_level == "HIGH":
            verification.append(f"Verify hazard forecast affecting {asset_code} with independent source")
        if dq_gate == "DEGRADED":
            verification.append(f"Confirm telemetry readings near {asset_code}")
        if dq_gate == "BLOCKED":
            verification.append(f"Manual field assessment required for {asset_code}")
            action = f"CANNOT confirm safety of {asset_name}; manual assessment required"
        return {
            "asset_code": asset_code, "asset_name": asset_name,
            "asset_risk_index": round(asset_risk_index, 3), "criticality_weight": criticality_weight,
            "exposure_score": round(exposure_score, 3), "risk_level": risk_level,
            "priority_score": priority_score, "asset_decision_level": asset_decision,
            "recommended_action": action, "verification_requirements": verification
        }

    def generate_escalation_reasons(self, hazard_severity, asset_risk, compound_risk, forecast_confidence, data_quality, persistence, uncertainty_level, dq_gate_state, dominant_hazard="FLOOD_INUNDATION"):
        esc = []
        sup = []
        ver = []
        if hazard_severity >= 0.60:
            esc.append(f"High hazard severity ({hazard_severity:.2f}): dominant hazard is {dominant_hazard}")
        elif hazard_severity >= 0.40:
            esc.append(f"Elevated hazard severity ({hazard_severity:.2f})")
        if compound_risk >= 0.60:
            esc.append(f"High compound multi-hazard risk ({compound_risk:.2f})")
        elif compound_risk >= 0.40:
            esc.append(f"Elevated compound risk ({compound_risk:.2f})")
        if asset_risk >= 0.60:
            esc.append(f"Critical infrastructure asset exposure detected (ARI: {asset_risk:.2f})")
        elif asset_risk >= 0.40:
            esc.append(f"Elevated asset risk (ARI: {asset_risk:.2f})")
        if persistence >= 0.40:
            esc.append(f"Sustained hazard persistence over multiple cycles ({persistence:.2f})")
        if forecast_confidence >= 0.70:
            esc.append(f"High forecast confidence ({forecast_confidence:.2f}) supports escalation")
        if forecast_confidence < 0.40:
            sup.append(f"Low forecast confidence ({forecast_confidence:.2f}) limits escalation reliability")
        if dq_gate_state == "DEGRADED":
            sup.append("Telemetry quality degraded; automatic confidence downgraded")
        elif dq_gate_state == "BLOCKED":
            sup.append("Telemetry critically impaired; automatic all-clear BLOCKED")
        if uncertainty_level == "HIGH":
            sup.append("High prediction uncertainty; precautionary posture required")
        if hazard_severity < 0.20 and compound_risk < 0.20:
            sup.append("Low hazard severity and compound risk support nominal status")
        if uncertainty_level == "HIGH":
            ver.append(VERIFICATION_TEMPLATES["HIGH_UNCERTAINTY"])
        if dq_gate_state == "DEGRADED":
            ver.append(VERIFICATION_TEMPLATES["DEGRADED_TELEMETRY"])
        if dq_gate_state == "BLOCKED":
            ver.append(VERIFICATION_TEMPLATES["BLOCKED_DATA"])
        if asset_risk >= 0.60:
            ver.append(VERIFICATION_TEMPLATES["CRITICAL_ASSET_EXPOSED"])
        return esc, sup, ver

    def assess(self, flood_probability=0.10, forecast_horizon="current", uncertainty_level="LOW",
               uncertainty_width=0.15, epistemic_variance=0.01, compound_risk_score=0.15,
               compound_risk_level="LOW", dominant_hazard="FLOOD_INUNDATION",
               dominant_hazard_intensity=0.10, active_interactions=None,
               max_asset_risk_index=0.30, mean_criticality_weight=0.50, max_exposure_score=0.30,
               aggregate_shs=0.95, source_health_states=None,
               num_degraded=0, num_anomalous=0, num_missing=0,
               consecutive_elevated_cycles=0, trend_direction="STABLE",
               asset_details=None):
        now = datetime.now(timezone.utc)
        h_severity = self.normalize_hazard_severity(flood_probability, compound_risk_score, dominant_hazard_intensity)
        a_risk = self.normalize_asset_risk(max_asset_risk_index, mean_criticality_weight, max_exposure_score)
        c_risk = self.normalize_compound_risk(compound_risk_score)
        f_confidence = self.normalize_forecast_confidence(uncertainty_level, uncertainty_width, epistemic_variance)
        d_quality = self.normalize_data_quality(aggregate_shs, num_degraded, num_anomalous, num_missing)
        p_score = self.normalize_persistence(consecutive_elevated_cycles, trend_direction)

        dss = self.calculate_dss(h_severity, a_risk, c_risk, f_confidence, d_quality, p_score)
        decision_level = self.classify_decision_level(dss, self.current_decision_level)
        dq_gate = self.evaluate_data_quality_gate(aggregate_shs, source_health_states, num_anomalous)

        prob_level = "HIGH" if flood_probability >= 0.50 else "MODERATE" if flood_probability >= 0.20 else "LOW"
        uncertainty_mod = self.evaluate_uncertainty_modifier(prob_level, uncertainty_level)

        esc_reasons, sup_reasons, verif_reqs = self.generate_escalation_reasons(
            h_severity, a_risk, c_risk, f_confidence, d_quality, p_score,
            uncertainty_level, dq_gate["gate_state"], dominant_hazard
        )

        recommended_action = RECOMMENDED_ACTIONS.get(decision_level, "Standard monitoring")
        decision_confidence = uncertainty_mod["confidence"]
        if dq_gate["gate_state"] == "DEGRADED" and decision_confidence == "HIGH":
            decision_confidence = "MODERATE"
        elif dq_gate["gate_state"] == "BLOCKED":
            decision_confidence = "LOW"

        affected_assets = []
        if asset_details:
            for asset in asset_details:
                ad = self.evaluate_asset_decision(
                    asset.get("code", "UNKNOWN"), asset.get("name", "Unknown Asset"),
                    asset.get("asset_risk_index", 0.30), asset.get("criticality_weight", 0.50),
                    asset.get("exposure_score", 0.30), asset.get("risk_level", "LOW"),
                    decision_level, uncertainty_level, dq_gate["gate_state"]
                )
                affected_assets.append(ad)
            affected_assets.sort(key=lambda x: x["priority_score"], reverse=True)

        prev_level = self.current_decision_level
        levels_order = ["NORMAL", "MONITOR", "PREPARE", "ALERT", "EMERGENCY"]
        prev_idx = levels_order.index(prev_level)
        curr_idx = levels_order.index(decision_level)
        if curr_idx > prev_idx:
            escalation_state = "ESCALATING"
        elif curr_idx < prev_idx:
            escalation_state = "DE-ESCALATING"
        else:
            escalation_state = "STABLE"

        self.current_decision_level = decision_level
        self.current_dss = dss

        decision_record = {
            "decision_level": decision_level,
            "decision_score": round(dss, 4),
            "decision_confidence": decision_confidence,
            "escalation_state": escalation_state,
            "previous_decision_level": prev_level,
            "components": {
                "hazard_severity": round(h_severity, 4),
                "asset_risk": round(a_risk, 4),
                "compound_risk": round(c_risk, 4),
                "forecast_confidence": round(f_confidence, 4),
                "data_quality": round(d_quality, 4),
                "persistence": round(p_score, 4)
            },
            "component_weights": deepcopy(DSS_WEIGHTS),
            "context": {
                "flood_probability": round(flood_probability, 4),
                "forecast_horizon": forecast_horizon,
                "uncertainty_level": uncertainty_level,
                "uncertainty_width": round(uncertainty_width, 4),
                "compound_risk_score": round(compound_risk_score, 4),
                "compound_risk_level": compound_risk_level,
                "dominant_hazard": dominant_hazard,
                "active_interactions": active_interactions or [],
                "aggregate_sensor_health": round(aggregate_shs, 3),
                "trend_direction": trend_direction,
                "consecutive_elevated_cycles": consecutive_elevated_cycles
            },
            "data_quality_gate": dq_gate,
            "uncertainty_modifier": uncertainty_mod,
            "recommended_action": recommended_action,
            "escalation_reasons": esc_reasons,
            "suppression_reasons": sup_reasons,
            "verification_requirements": verif_reqs,
            "affected_assets": affected_assets,
            "model_version": MODEL_VERSION,
            "thresholds_disclaimer": THRESHOLDS_DISCLAIMER,
            "output_classification": "RULE-BASED / DERIVED",
            "timestamp": now.isoformat()
        }

        timeline_entry = {
            "timestamp": now.isoformat(),
            "decision_level": decision_level,
            "decision_score": round(dss, 4),
            "dominant_driver": "hazard_severity" if h_severity >= max(a_risk, c_risk, f_confidence) else
                              "asset_risk" if a_risk >= max(c_risk, f_confidence) else
                              "compound_risk" if c_risk >= f_confidence else "forecast_confidence",
            "data_quality_gate": dq_gate["gate_state"],
            "uncertainty_level": uncertainty_level,
            "escalation_state": escalation_state,
            "recommended_action": recommended_action
        }
        self.decision_history.append(timeline_entry)
        if len(self.decision_history) > 100:
            self.decision_history = self.decision_history[-100:]
        decision_record["decision_timeline"] = list(self.decision_history[-10:])
        return decision_record

    def get_policy(self):
        return {
            "model_version": MODEL_VERSION,
            "parameter_source": self.parameter_source,
            "dss_weights": deepcopy(DSS_WEIGHTS),
            "decision_thresholds": deepcopy(DECISION_THRESHOLDS),
            "cascade_strengths": deepcopy(CASCADE_STRENGTHS),
            "hysteresis_band": HYSTERESIS_BAND,
            "uncertainty_decision_matrix": {f"{k[0]}_{k[1]}": v for k, v in UNCERTAINTY_DECISION_MATRIX.items()},
            "data_quality_gate_thresholds": deepcopy(DQ_GATE_THRESHOLDS),
            "recommended_actions": deepcopy(RECOMMENDED_ACTIONS),
            "verification_templates": deepcopy(VERIFICATION_TEMPLATES),
            "thresholds_disclaimer": THRESHOLDS_DISCLAIMER,
            "output_classification": "RULE-BASED / DERIVED"
        }

    def run_benchmark_scenarios(self):
        self.current_decision_level = "NORMAL"
        self.current_dss = 0.0
        self.decision_history = []
        default_assets = [
            {"code": "ADYAR_OUTFALL", "name": "Adyar River Coastal Outfall", "asset_risk_index": 0.30, "criticality_weight": 1.00, "exposure_score": 0.30, "risk_level": "LOW"},
            {"code": "REDHILLS", "name": "Redhills Reservoir", "asset_risk_index": 0.25, "criticality_weight": 1.00, "exposure_score": 0.25, "risk_level": "LOW"},
            {"code": "CENTRAL_SUBSTATION", "name": "Chennai Central Power Substation", "asset_risk_index": 0.28, "criticality_weight": 1.00, "exposure_score": 0.28, "risk_level": "LOW"}
        ]
        scenarios = [
            {"scenario_id": "SCENARIO_A_NOMINAL", "scenario_name": "Nominal Baseline Conditions", "label": "SIMULATED DECISION-SUPPORT BENCHMARK",
             "params": {"flood_probability": 0.08, "uncertainty_level": "LOW", "uncertainty_width": 0.12, "epistemic_variance": 0.005, "compound_risk_score": 0.12, "compound_risk_level": "LOW", "dominant_hazard": "FLOOD_INUNDATION", "dominant_hazard_intensity": 0.08, "max_asset_risk_index": 0.25, "mean_criticality_weight": 0.75, "max_exposure_score": 0.25, "aggregate_shs": 0.97, "source_health_states": ["HEALTHY"] * 8, "consecutive_elevated_cycles": 0, "trend_direction": "STABLE", "asset_details": default_assets}},
            {"scenario_id": "SCENARIO_B_HEAVY_RAIN", "scenario_name": "Heavy Rainfall + Healthy Telemetry", "label": "SIMULATED DECISION-SUPPORT BENCHMARK",
             "params": {"flood_probability": 0.45, "uncertainty_level": "LOW", "uncertainty_width": 0.18, "epistemic_variance": 0.01, "compound_risk_score": 0.50, "compound_risk_level": "HIGH", "dominant_hazard": "EXTREME_RAINFALL", "dominant_hazard_intensity": 0.65, "max_asset_risk_index": 0.55, "mean_criticality_weight": 0.80, "max_exposure_score": 0.60, "aggregate_shs": 0.96, "source_health_states": ["HEALTHY"] * 8, "consecutive_elevated_cycles": 2, "trend_direction": "RISING", "asset_details": [{"code": "ADYAR_OUTFALL", "name": "Adyar River Coastal Outfall", "asset_risk_index": 0.62, "criticality_weight": 1.00, "exposure_score": 0.70, "risk_level": "HIGH"}, {"code": "REDHILLS", "name": "Redhills Reservoir", "asset_risk_index": 0.54, "criticality_weight": 1.00, "exposure_score": 0.52, "risk_level": "HIGH"}, {"code": "NAPIER_BRIDGE", "name": "Napier Bridge", "asset_risk_index": 0.48, "criticality_weight": 0.75, "exposure_score": 0.55, "risk_level": "MODERATE"}]}},
            {"scenario_id": "SCENARIO_C_CRITICAL_COMPOUND", "scenario_name": "Heavy Rainfall + Saturated Reservoir + Critical Asset", "label": "SIMULATED DECISION-SUPPORT BENCHMARK",
             "params": {"flood_probability": 0.82, "uncertainty_level": "LOW", "uncertainty_width": 0.15, "epistemic_variance": 0.008, "compound_risk_score": 0.92, "compound_risk_level": "CRITICAL", "dominant_hazard": "EXTREME_RAINFALL", "dominant_hazard_intensity": 0.95, "max_asset_risk_index": 0.91, "mean_criticality_weight": 1.00, "max_exposure_score": 0.90, "aggregate_shs": 0.95, "source_health_states": ["HEALTHY"] * 8, "consecutive_elevated_cycles": 5, "trend_direction": "RISING", "asset_details": [{"code": "ADYAR_OUTFALL", "name": "Adyar River Coastal Outfall", "asset_risk_index": 0.95, "criticality_weight": 1.00, "exposure_score": 0.92, "risk_level": "CRITICAL"}, {"code": "CHEMBARAMBAKKAM", "name": "Chembarambakkam Reservoir", "asset_risk_index": 0.88, "criticality_weight": 1.00, "exposure_score": 0.85, "risk_level": "CRITICAL"}, {"code": "CENTRAL_SUBSTATION", "name": "Chennai Central Power Substation", "asset_risk_index": 0.78, "criticality_weight": 1.00, "exposure_score": 0.75, "risk_level": "CRITICAL"}]}},
            {"scenario_id": "SCENARIO_D_HIGH_UNCERTAINTY", "scenario_name": "High Hazard + High Uncertainty", "label": "SIMULATED DECISION-SUPPORT BENCHMARK",
             "params": {"flood_probability": 0.65, "uncertainty_level": "HIGH", "uncertainty_width": 0.55, "epistemic_variance": 0.08, "compound_risk_score": 0.60, "compound_risk_level": "HIGH", "dominant_hazard": "FLOOD_INUNDATION", "dominant_hazard_intensity": 0.55, "max_asset_risk_index": 0.60, "mean_criticality_weight": 0.80, "max_exposure_score": 0.55, "aggregate_shs": 0.94, "source_health_states": ["HEALTHY"] * 8, "consecutive_elevated_cycles": 1, "trend_direction": "RISING", "asset_details": [{"code": "ADYAR_OUTFALL", "name": "Adyar River Coastal Outfall", "asset_risk_index": 0.65, "criticality_weight": 1.00, "exposure_score": 0.60, "risk_level": "HIGH"}, {"code": "REDHILLS", "name": "Redhills Reservoir", "asset_risk_index": 0.50, "criticality_weight": 1.00, "exposure_score": 0.48, "risk_level": "HIGH"}]}},
            {"scenario_id": "SCENARIO_E_DEGRADED_SENSORS", "scenario_name": "High Hazard + Degraded Sensor Network", "label": "SIMULATED DECISION-SUPPORT BENCHMARK",
             "params": {"flood_probability": 0.70, "uncertainty_level": "MODERATE", "uncertainty_width": 0.35, "epistemic_variance": 0.04, "compound_risk_score": 0.65, "compound_risk_level": "HIGH", "dominant_hazard": "EXTREME_RAINFALL", "dominant_hazard_intensity": 0.60, "max_asset_risk_index": 0.58, "mean_criticality_weight": 0.80, "max_exposure_score": 0.55, "aggregate_shs": 0.55, "num_degraded": 3, "num_anomalous": 1, "source_health_states": ["HEALTHY", "HEALTHY", "DEGRADED", "STALE", "HEALTHY", "DEGRADED", "ANOMALOUS", "HEALTHY"], "consecutive_elevated_cycles": 2, "trend_direction": "RISING", "asset_details": [{"code": "ADYAR_OUTFALL", "name": "Adyar River Coastal Outfall", "asset_risk_index": 0.62, "criticality_weight": 1.00, "exposure_score": 0.58, "risk_level": "HIGH"}]}},
            {"scenario_id": "SCENARIO_F_MODERATE_CRITICAL_ASSET", "scenario_name": "Moderate Hazard + Critical Infrastructure", "label": "SIMULATED DECISION-SUPPORT BENCHMARK",
             "params": {"flood_probability": 0.35, "uncertainty_level": "MODERATE", "uncertainty_width": 0.30, "epistemic_variance": 0.03, "compound_risk_score": 0.40, "compound_risk_level": "MODERATE", "dominant_hazard": "RESERVOIR_HYDROLOGICAL_STRESS", "dominant_hazard_intensity": 0.45, "max_asset_risk_index": 0.55, "mean_criticality_weight": 1.00, "max_exposure_score": 0.50, "aggregate_shs": 0.92, "source_health_states": ["HEALTHY"] * 8, "consecutive_elevated_cycles": 1, "trend_direction": "STABLE", "asset_details": [{"code": "CHEMBARAMBAKKAM", "name": "Chembarambakkam Reservoir", "asset_risk_index": 0.55, "criticality_weight": 1.00, "exposure_score": 0.50, "risk_level": "HIGH"}, {"code": "KILPAUK_WTP", "name": "Kilpauk Water Treatment Plant", "asset_risk_index": 0.42, "criticality_weight": 0.75, "exposure_score": 0.40, "risk_level": "MODERATE"}]}},
            {"scenario_id": "SCENARIO_G_LOW_HIGH_UNCERTAINTY", "scenario_name": "Low Hazard + High Uncertainty", "label": "SIMULATED DECISION-SUPPORT BENCHMARK",
             "params": {"flood_probability": 0.12, "uncertainty_level": "HIGH", "uncertainty_width": 0.60, "epistemic_variance": 0.10, "compound_risk_score": 0.18, "compound_risk_level": "LOW", "dominant_hazard": "FLOOD_INUNDATION", "dominant_hazard_intensity": 0.15, "max_asset_risk_index": 0.28, "mean_criticality_weight": 0.60, "max_exposure_score": 0.25, "aggregate_shs": 0.93, "source_health_states": ["HEALTHY"] * 8, "consecutive_elevated_cycles": 0, "trend_direction": "STABLE", "asset_details": default_assets}},
            {"scenario_id": "SCENARIO_H_RECOVERY", "scenario_name": "Hazard Recovery / De-escalation", "label": "SIMULATED DECISION-SUPPORT BENCHMARK",
             "params": {"flood_probability": 0.10, "uncertainty_level": "LOW", "uncertainty_width": 0.10, "epistemic_variance": 0.003, "compound_risk_score": 0.10, "compound_risk_level": "LOW", "dominant_hazard": "FLOOD_INUNDATION", "dominant_hazard_intensity": 0.08, "max_asset_risk_index": 0.22, "mean_criticality_weight": 0.60, "max_exposure_score": 0.20, "aggregate_shs": 0.97, "source_health_states": ["HEALTHY"] * 8, "consecutive_elevated_cycles": 0, "trend_direction": "FALLING", "asset_details": default_assets}}
        ]
        results = []
        for scenario in scenarios:
            if scenario["scenario_id"] == "SCENARIO_H_RECOVERY":
                self.current_decision_level = "ALERT"
                self.current_dss = 0.72
            elif scenario["scenario_id"] != "SCENARIO_B_HEAVY_RAIN":
                self.current_decision_level = "NORMAL"
                self.current_dss = 0.0
            result = self.assess(**scenario["params"])
            results.append({
                "scenario_id": scenario["scenario_id"], "scenario_name": scenario["scenario_name"],
                "label": scenario["label"],
                "inputs_summary": {
                    "flood_probability": scenario["params"]["flood_probability"],
                    "uncertainty_level": scenario["params"]["uncertainty_level"],
                    "compound_risk_score": scenario["params"]["compound_risk_score"],
                    "aggregate_shs": scenario["params"]["aggregate_shs"],
                    "max_asset_risk_index": scenario["params"]["max_asset_risk_index"],
                    "trend_direction": scenario["params"]["trend_direction"]
                },
                "decision_level": result["decision_level"], "decision_score": result["decision_score"],
                "decision_confidence": result["decision_confidence"],
                "data_quality_gate": result["data_quality_gate"]["gate_state"],
                "escalation_state": result["escalation_state"],
                "recommended_action": result["recommended_action"],
                "escalation_reasons": result["escalation_reasons"],
                "verification_requirements": result["verification_requirements"],
                "affected_assets_count": len(result["affected_assets"]),
                "top_priority_asset": result["affected_assets"][0]["asset_code"] if result["affected_assets"] else "N/A"
            })
        self.current_decision_level = "NORMAL"
        self.current_dss = 0.0
        self.decision_history = []
        return results


decision_engine = DecisionSupportEngine()
