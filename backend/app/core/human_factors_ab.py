import time
import pandas as pd
from typing import Dict, List, Any

class ScenarioReplayLogger:
    """
    Scientific Purpose: Captures telemetry from human-in-the-loop (HITL) 
    dashboard A/B testing. Logs cognitive response metrics including 
    Response Time (RT), Confidence, and NASA-TLX workload scores.
    """
    def __init__(self):
        self.decision_logs = []
        self.tlx_logs = []
        
    def record_decision(self, operator_id: str, variant: str, scenario_id: int, 
                        true_hazard_state: int, presented_prob: float, 
                        decision_escalate: int, response_time_ms: float, confidence_1_to_5: int):
        self.decision_logs.append({
            "Operator_ID": operator_id,
            "Variant": variant,
            "Scenario_ID": scenario_id,
            "True_Hazard_State": true_hazard_state, # 1=Hazard, 0=Safe
            "Presented_Prob": presented_prob,
            "Operator_Escalated": decision_escalate,
            "Response_Time_ms": response_time_ms,
            "Confidence": confidence_1_to_5
        })

    def record_nasa_tlx(self, operator_id: str, variant: str, scores: Dict[str, int]):
        """Scores typically 0-100 for Mental, Physical, Temporal, Performance, Effort, Frustration"""
        record = {"Operator_ID": operator_id, "Variant": variant}
        record.update(scores)
        self.tlx_logs.append(record)
        
    def export(self, filepath_decisions, filepath_tlx):
        pd.DataFrame(self.decision_logs).to_csv(filepath_decisions, index=False)
        pd.DataFrame(self.tlx_logs).to_csv(filepath_tlx, index=False)


class DashboardVariants:
    @staticmethod
    def render_variant_A(prob: float):
        """Standard 3-level deterministic threshold alert."""
        if prob > 0.7: return "RED ALERT"
        elif prob > 0.4: return "ORANGE ALERT"
        else: return "GREEN ALERT"
        
    @staticmethod
    def render_variant_B(prob: float, uncertainty_width: float, impact_category: str):
        """Uncertainty-aware, impact-based probabilistic warning."""
        return {
            "Status": "CRITICAL" if prob > 0.5 else "MONITORING",
            "Probability": f"{prob*100:.1f}% ± {uncertainty_width*100:.1f}%",
            "Impact_Context": impact_category,
            "Recommendation": "Expected utility dictates action due to asymmetric costs."
        }
