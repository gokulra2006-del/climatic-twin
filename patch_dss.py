import os
import re

path = 'backend/app/core/decision_support.py'
with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

# Add the expected cost policy method
cost_method = '''
    def expected_cost_policy(self, flood_probability, uncertainty_width, previous_level=None):
        levels = ["NORMAL", "MONITOR", "PREPARE", "ALERT", "EMERGENCY"]
        p50 = max(0.0, min(1.0, flood_probability))
        p10 = max(0.0, p50 - uncertainty_width / 2.0)
        p90 = min(1.0, p50 + uncertainty_width / 2.0)
        
        # Risk-averse weighting across the uncertainty band
        p_effective = 0.2 * p10 + 0.5 * p50 + 0.3 * p90
        
        expected_costs = {}
        for lvl in levels:
            c_action = PROVISIONAL_ACTION_COSTS[lvl]
            c_loss = PROVISIONAL_OUTCOME_LOSS[lvl]
            expected_costs[lvl] = c_action + p_effective * c_loss
            
        optimal_level = min(expected_costs, key=expected_costs.get)
        
        # Hysteresis
        if previous_level is None:
            return optimal_level, expected_costs
        
        prev_idx = levels.index(previous_level)
        opt_idx = levels.index(optimal_level)
        
        HYSTERESIS_COST_MARGIN = 50.0
        if opt_idx < prev_idx:
            # We only de-escalate if the cost benefit exceeds the hysteresis margin
            if expected_costs[optimal_level] < expected_costs[previous_level] - HYSTERESIS_COST_MARGIN:
                return optimal_level, expected_costs
            else:
                return previous_level, expected_costs
                
        return optimal_level, expected_costs

    def classify_decision_level(self, dss, previous_level=None):'''

code = code.replace('    def classify_decision_level(self, dss, previous_level=None):', cost_method)

# Now modify assess
assess_search = '''dss = self.calculate_dss(h_severity, a_risk, c_risk, f_confidence, d_quality, p_score)
        decision_level = self.classify_decision_level(dss, self.current_decision_level)
        dq_gate = self.evaluate_data_quality_gate(aggregate_shs, source_health_states, num_anomalous)'''

assess_replace = '''dss = self.calculate_dss(h_severity, a_risk, c_risk, f_confidence, d_quality, p_score)
        
        # FEATURE 2: EXPECTED COST POLICY (Minimizing Cost vs Act/Not-Act)
        decision_level, expected_costs = self.expected_cost_policy(flood_probability, uncertainty_width, self.current_decision_level)
        
        dq_gate = self.evaluate_data_quality_gate(aggregate_shs, source_health_states, num_anomalous)'''

code = code.replace(assess_search, assess_replace)

# Now append cost rationale to return
return_search = '''"decision_level": decision_level,
            "decision_score": dss,
            "decision_confidence": decision_confidence,'''

return_replace = '''"decision_level": decision_level,
            "decision_score": dss,
            "decision_confidence": decision_confidence,
            "expected_costs": expected_costs,
            "rationale": f"Selected {decision_level} by minimizing expected cost (P50={flood_probability:.2f}, Width={uncertainty_width:.2f}).",'''

code = code.replace(return_search, return_replace)

with open(path, 'w', encoding='utf-8') as f:
    f.write(code)
