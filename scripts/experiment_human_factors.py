import os
import numpy as np
import pandas as pd
from backend.app.core.human_factors_ab import ScenarioReplayLogger, DashboardVariants
from backend.app.core.reproducibility import set_global_seed, get_logger

logger = get_logger("Human_Factors_Experiment")

def simulate_operator_cohort(logger_db, n_operators=20, n_scenarios=50):
    for op in range(n_operators):
        variant = "A_Standard_3Level" if op % 2 == 0 else "B_Uncertainty_Impact"
        operator_id = f"OP_{op:03d}"
        consecutive_false_alarms = 0
        
        if variant == "A_Standard_3Level":
            logger_db.record_nasa_tlx(operator_id, variant, {
                "Mental_Demand": np.random.normal(70, 10),
                "Physical_Demand": np.random.normal(20, 5),
                "Temporal_Demand": np.random.normal(75, 10),
                "Performance": np.random.normal(40, 15), 
                "Effort": np.random.normal(80, 10),
                "Frustration": np.random.normal(65, 15)
            })
        else:
            logger_db.record_nasa_tlx(operator_id, variant, {
                "Mental_Demand": np.random.normal(45, 10),
                "Physical_Demand": np.random.normal(20, 5),
                "Temporal_Demand": np.random.normal(50, 10),
                "Performance": np.random.normal(85, 10), 
                "Effort": np.random.normal(50, 10),
                "Frustration": np.random.normal(30, 10)
            })
            
        for sc in range(n_scenarios):
            true_state = np.random.choice([0, 1], p=[0.7, 0.3]) 
            prob = np.random.beta(5, 2) if true_state == 1 else np.random.beta(2, 5)
            
            if variant == "A_Standard_3Level":
                rt_ms = np.random.lognormal(mean=8.0, sigma=0.5)
                confidence = np.random.randint(1, 4)
                if consecutive_false_alarms >= 2 and prob > 0.4: escalate = 0
                else: escalate = 1 if prob > 0.4 else 0
            else:
                rt_ms = np.random.lognormal(mean=7.2, sigma=0.3)
                confidence = np.random.randint(3, 6)
                escalate = 1 if prob > 0.35 else 0 
                
            model_alerted = (prob > 0.4)
            if model_alerted and true_state == 0: consecutive_false_alarms += 1
            elif true_state == 1: consecutive_false_alarms = 0
                
            logger_db.record_decision(operator_id, variant, sc, true_state, prob, escalate, rt_ms, confidence)


def analyze_human_performance(df_decisions):
    results = []
    for variant, grp in df_decisions.groupby("Variant"):
        correct_escalation = ((grp["Operator_Escalated"] == 1) & (grp["True_Hazard_State"] == 1)).sum()
        correct_ignore = ((grp["Operator_Escalated"] == 0) & (grp["True_Hazard_State"] == 0)).sum()
        false_escalation = ((grp["Operator_Escalated"] == 1) & (grp["True_Hazard_State"] == 0)).sum()
        missed_escalation = ((grp["Operator_Escalated"] == 0) & (grp["True_Hazard_State"] == 1)).sum()
        accuracy = (correct_escalation + correct_ignore) / len(grp)
        
        high_prob_mask = grp["Presented_Prob"] > 0.6
        fatigue_misses = ((grp[high_prob_mask]["Operator_Escalated"] == 0) & 
                          (grp[high_prob_mask]["True_Hazard_State"] == 1)).sum()
        total_high_prob_hazards = (grp[high_prob_mask]["True_Hazard_State"] == 1).sum()
        fatigue_proxy = fatigue_misses / total_high_prob_hazards if total_high_prob_hazards > 0 else 0
        
        results.append({
            "Variant": variant,
            "Decision_Accuracy": accuracy,
            "False_Escalations": false_escalation,
            "Missed_Escalations": missed_escalation,
            "Alert_Fatigue_Proxy_Rate": fatigue_proxy,
            "Avg_Response_Time_ms": grp["Response_Time_ms"].mean(),
            "Avg_Confidence_Score": grp["Confidence"].mean()
        })
    return pd.DataFrame(results)

def analyze_nasa_tlx(df_tlx):
    df_res = df_tlx.groupby("Variant").mean(numeric_only=True).reset_index()
    return df_res

def main():
    logger.info("Starting Dashboard A/B Human Factors Experiment...")
    set_global_seed(42)
    
    harness = ScenarioReplayLogger()
    simulate_operator_cohort(harness, n_operators=40, n_scenarios=100)
    
    out_dir = r"C:\Users\gokul\Desktop\PROJECTS\climatetwin\docs"
    harness.export(
        os.path.join(out_dir, "replay_decisions.csv"),
        os.path.join(out_dir, "replay_nasa_tlx.csv")
    )
    
    df_decisions = pd.read_csv(os.path.join(out_dir, "replay_decisions.csv"))
    df_tlx = pd.read_csv(os.path.join(out_dir, "replay_nasa_tlx.csv"))
    
    df_perf = analyze_human_performance(df_decisions)
    df_tlx_res = analyze_nasa_tlx(df_tlx)
    
    logger.info("\n=== A/B DECISION PERFORMANCE & ESCALATION METRICS ===")
    logger.info("\n" + df_perf.to_string(index=False))
    
    logger.info("\n=== NASA-TLX MENTAL WORKLOAD SCORES (Lower = Better Workload) ===")
    logger.info("\n" + df_tlx_res.to_string(index=False))
    
    df_perf.to_csv(os.path.join(out_dir, "ab_performance_analysis.csv"), index=False)
    df_tlx_res.to_csv(os.path.join(out_dir, "ab_nasa_tlx_analysis.csv"), index=False)

if __name__ == "__main__":
    main()
