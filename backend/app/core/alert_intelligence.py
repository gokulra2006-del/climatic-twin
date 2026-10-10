import datetime
import uuid
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import timezone

# Assuming existing engines can be imported
from app.core.multihazard import multihazard_engine
from app.core.asset_risk import asset_risk_engine
from app.core.sensor_health import sensor_health_engine
from app.core.explainability import explainability_engine

# --- SCHEMAS ---
class AlertState(BaseModel):
    alert_id: str
    hazard: str
    severity: str  # INFO, WATCH, ADVISORY, WARNING, CRITICAL
    score: float
    timestamp: str
    trigger: str
    confidence: str # HIGH, MODERATE, LOW
    lead_time: str
    affected_assets: List[Dict[str, Any]]
    explanation: str
    evidence: Dict[str, Any]
    status: str # ACTIVE, ACKNOWLEDGED, RESOLVED
    previous_score: Optional[float] = None
    created_at: str

# Threshold configurations
SEVERITY_THRESHOLDS = {
    "CRITICAL": 0.85,
    "WARNING": 0.65,
    "ADVISORY": 0.45,
    "WATCH": 0.25,
    "INFO": 0.10
}

class AlertIntelligenceEngine:
    def __init__(self):
        # In-memory alert store for deduplication
        self.active_alerts: Dict[str, AlertState] = {}
        self.alert_history: List[AlertState] = []
        self.simulation_mode = False
        self.simulated_scenario = None

    def _determine_severity(self, risk_score: float) -> str:
        if risk_score >= SEVERITY_THRESHOLDS["CRITICAL"]:
            return "CRITICAL"
        elif risk_score >= SEVERITY_THRESHOLDS["WARNING"]:
            return "WARNING"
        elif risk_score >= SEVERITY_THRESHOLDS["ADVISORY"]:
            return "ADVISORY"
        elif risk_score >= SEVERITY_THRESHOLDS["WATCH"]:
            return "WATCH"
        return "INFO"

    def _determine_confidence(self, sensor_health: float, uncertainty_lower: float, uncertainty_upper: float) -> str:
        # Confidence calculation
        uncertainty_spread = abs(uncertainty_upper - uncertainty_lower)
        if sensor_health > 85.0 and uncertainty_spread < 0.15:
            return "HIGH"
        elif sensor_health > 60.0 and uncertainty_spread < 0.35:
            return "MODERATE"
        return "LOW"
        
    def _calculate_lead_time(self, forecast_data: Dict[str, Any], current_prob: float, threshold: float) -> str:
        """
        Check forecast Horizons (15, 30, 60m)
        """
        if current_prob >= threshold:
            return "THREAT ACTIVE (0 min)"
            
        if not forecast_data or 'forecast' not in forecast_data:
            return "NO THRESHOLD CROSSING DETECTED"
            
        horizons = [('15m', 15), ('30m', 30), ('60m', 60)]
        for label, mins in horizons:
            key = f"{mins}min"
            if key in forecast_data['forecast']:
                f_prob = forecast_data['forecast'][key].get('probability', current_prob)
                if f_prob >= threshold:
                    return f"{mins}–{mins+15} min"
        return "NO THRESHOLD CROSSING DETECTED"

    def _generate_nova_explanation(self, hazard: str, severity: str, prev_severity: str, score: float, 
                                   drivers: List[str], top_asset: Dict, confidence: str, 
                                   sensor_msg: str, trend: str) -> str:
        asset_name = top_asset.get('name', 'Unknown') if top_asset else 'No critical assets identified'
        
        esc_str = f"escalated from {prev_severity} to {severity}" if severity != prev_severity and prev_severity else f"is currently {severity}"
        
        return (f"{hazard} risk {esc_str} ({score:.2f}). "
                f"Trend indicates {trend}. "
                f"The highest-priority exposed asset is {asset_name}. "
                f"Confidence is {confidence}. {sensor_msg}")

    def evaluate_state(self, current_state: Dict[str, Any], forecast_data: Dict[str, Any] = None) -> List[AlertState]:
        """
        Main evaluation cycle.
        Returns a list of updated/new alerts.
        """
        if not current_state:
            return []
            
        # If in simulation mode, override current state with scenario state
        if self.simulation_mode and self.simulated_scenario:
            sim_result = multihazard_engine.simulate_scenario(self.simulated_scenario)
            # update current state to match the sim state for the rest of eval
            scenario_meta = sim_result.get('scenario_meta', {})
            # We don't overwrite the whole state but extract flood_prob
            flood_prob = sim_result.get('base_component_score', 0.5)
            mh_result = sim_result
        else:
            flood_prob = current_state.get('flood_probability', 0.0)
            mh_result = multihazard_engine.calculate_compound_risk(current_state, flood_prob)
        
        score = mh_result['compound_risk_score']
        hazard_type = mh_result.get('dominant_hazard', 'FLOOD').upper()
        severity = self._determine_severity(score)
        
        # We only generate alerts for WATCH or above, unless tracking an existing one
        if score < SEVERITY_THRESHOLDS["INFO"]:
            # Auto-resolve existing
            self._resolve_inactive()
            return []

        # 2. Asset Risk Check
        affected_assets = asset_risk_engine.assess_all_assets(current_state)
        top_asset = affected_assets[0] if affected_assets else None

        # 3. Data Trust
        health_data = sensor_health_engine.get_summary()
        sys_health = health_data.get('system_health_score', 100.0)
        
        uncert = mh_result.get('flood_uncertainty', {})
        p_int = uncert.get('prediction_interval', {'lower':0.0, 'upper':0.0})
        
        confidence = self._determine_confidence(sys_health, p_int.get('lower',0.0), p_int.get('upper',0.0))
        
        sensor_msg = "Current telemetry is fresh, multiple environmental sources agree, and forecast uncertainty is low." if sys_health > 80 and confidence == "HIGH" else "WARNING — ALERT BASED ON LIMITED OBSERVATIONS OR DEGRADED SENSOR QUALITY."
        
        # 4. Forecast Threshold Crossing
        lead_time = self._calculate_lead_time(forecast_data, flood_prob, SEVERITY_THRESHOLDS[severity])
        
        # 5. Deduplication & Escalation
        alert_key = f"{hazard_type}_COMPOUND"
        now_str = datetime.datetime.now(timezone.utc).isoformat()
        
        is_escalation = False
        prev_severity = None
        prev_score = 0.0
        
        if alert_key in self.active_alerts:
            existing_alert = self.active_alerts[alert_key]
            prev_severity = existing_alert.severity
            prev_score = existing_alert.score
            
            # Check if severity changed
            if severity != prev_severity:
                is_escalation = SEVERITY_THRESHOLDS[severity] > SEVERITY_THRESHOLDS.get(prev_severity, 0.0)
                trigger_msg = f"Alert escalated from {prev_severity} → {severity}" if is_escalation else f"Alert downgraded to {severity}"
            else:
                trigger_msg = existing_alert.trigger
        else:
            trigger_msg = f"New {severity} {hazard_type} alert generated."
            
        # 6. Generate ML/UX Explanation (Feature Attributions)
        trend_msg = "rapidly increasing" if (score - prev_score) > 0.10 else ("increasing" if score > prev_score else "stable")
        
        # Call the new operator-facing explanation layer
        hazard_payload = {
            "contributing_features": current_state,
            "risk_level": severity
        }
        xai_result = explainability_engine.explain(hazard_type, hazard_payload)
        
        # We append the sensor msg to the new plain-English explanation
        nova_explanation = f"{xai_result['explanation']} {sensor_msg}"
        
        # 7. Construct Evidence Payload
        # Use mh_result to get accurate values, even during simulations
        hazards_data = mh_result.get('hazards', {})
        rain_obs = hazards_data.get('rainfall', {}).get('observed_value', '0 mm/day')
        res_obs = hazards_data.get('reservoir_stress', {}).get('observed_value', '0% Capacity')
        
        evidence = {
            "OBSERVED": {
                "Rainfall": rain_obs,
                "Reservoir Storage": res_obs
            },
            "MODEL PREDICTED": {
                "Probability": f"{flood_prob*100:.1f}%"
            },
            "DERIVED": {
                "Compound Risk": score
            }
        }
        
        # Create alert ID or reuse existing
        aid = self.active_alerts[alert_key].alert_id if alert_key in self.active_alerts else str(uuid.uuid4())
        created = self.active_alerts[alert_key].created_at if alert_key in self.active_alerts else now_str
        
        new_alert = AlertState(
            alert_id=aid,
            hazard=hazard_type,
            severity=severity,
            score=score,
            timestamp=now_str,
            trigger=trigger_msg,
            confidence=confidence,
            lead_time=lead_time,
            affected_assets=affected_assets[:3],
            explanation=nova_explanation,
            evidence=evidence,
            status="ACTIVE",
            previous_score=prev_score,
            created_at=created
        )
        
        # Only keep alerts that are WATCH or above
        if SEVERITY_THRESHOLDS[severity] >= SEVERITY_THRESHOLDS["WATCH"]:
            # If new or escalated, prepend to history
            if alert_key not in self.active_alerts or is_escalation:
                self.alert_history.insert(0, new_alert)
            self.active_alerts[alert_key] = new_alert
                
        return [self.active_alerts[alert_key]] if alert_key in self.active_alerts else []

    def _resolve_inactive(self):
        resolved_keys = []
        now_str = datetime.datetime.now(timezone.utc).isoformat()
        for key, alert in list(self.active_alerts.items()):
            alert.status = "RESOLVED"
            alert.timestamp = now_str
            self.alert_history.insert(0, alert)
            resolved_keys.append(key)
            
        for k in resolved_keys:
            del self.active_alerts[k]

    def set_simulation(self, scenario_name: str):
        self.simulation_mode = True
        self.simulated_scenario = scenario_name

    def clear_simulation(self):
        self.simulation_mode = False
        self.simulated_scenario = None
        self.active_alerts.clear()

    def acknowledge_alert(self, alert_id: str):
        for key, alert in self.active_alerts.items():
            if alert.alert_id == alert_id:
                alert.status = "ACKNOWLEDGED"
                return alert
        return None
        
    def resolve_alert(self, alert_id: str):
        to_del = None
        for key, alert in self.active_alerts.items():
            if alert.alert_id == alert_id:
                alert.status = "RESOLVED"
                self.alert_history.insert(0, alert)
                to_del = key
                break
        if to_del:
            del self.active_alerts[to_del]
            return True
        return False

    def get_active_alerts(self) -> List[AlertState]:
        return list(self.active_alerts.values())

    def get_history(self) -> List[AlertState]:
        return self.alert_history

# Global instance
alert_engine = AlertIntelligenceEngine()
