import os
import numpy as np
import pandas as pd
from backend.app.core.impact_warnings import ImpactBasedWarningEngine, ASSET_CATALOGUE
from backend.app.core.reproducibility import set_global_seed, get_logger

logger = get_logger("Decision_Curve_Analysis")

def simulate_predictions(n=5000):
    """Simulates a model's predicted probabilities and the true event outcomes."""
    # Beta distribution favoring lower probabilities (typical for hazards)
    y_prob = np.random.beta(a=2, b=5, size=n)
    # True outcome sampled from predicted probability
    y_true = (np.random.rand(n) < y_prob).astype(int)
    return y_prob, y_true

def compute_dca_and_utility(y_prob, y_true, asset, lead_time_hrs=24.0, uncertainty_width=0.2):
    thresholds = np.linspace(0.01, 0.99, 99)
    n = len(y_true)
    
    results = []
    for pt in thresholds:
        y_pred = (y_prob >= pt).astype(int)
        tp = np.sum((y_pred == 1) & (y_true == 1))
        fp = np.sum((y_pred == 1) & (y_true == 0))
        fn = np.sum((y_pred == 0) & (y_true == 1))
        tn = np.sum((y_pred == 0) & (y_true == 0))
        
        # Standard Clinical Net Benefit
        # NB = (TP / N) - (FP / N) * (pt / (1 - pt))
        net_benefit = (tp / n) - (fp / n) * (pt / (1 - pt))
        
        # Expected Utility (Negative Expected Cost)
        # Includes the dynamic penalty for delayed action modeled in our warnings
        delayed_penalty = asset.cost_delay * (1.0 / max(1.0, lead_time_hrs)) * uncertainty_width
        
        expected_cost = (fp * asset.cost_fa) + (fn * asset.cost_miss) + (tp * delayed_penalty)
        expected_utility = -expected_cost / n # Utility per forecast instance
        
        results.append({
            "Asset": asset.name,
            "Threshold": pt,
            "Net_Benefit": net_benefit,
            "Expected_Utility": expected_utility,
            "Cost_FA": fp * asset.cost_fa,
            "Cost_Miss": fn * asset.cost_miss
        })
    return pd.DataFrame(results)

def main():
    logger.info("Starting Cost-Sensitive Decision Curve Analysis...")
    set_global_seed(42)
    
    y_prob, y_true = simulate_predictions(n=10000)
    
    # 1. Decision Curve Analysis across Assets
    dca_frames = []
    for asset_id, asset in ASSET_CATALOGUE.items():
        df_dca = compute_dca_and_utility(y_prob, y_true, asset, lead_time_hrs=12.0)
        dca_frames.append(df_dca)
        
        # Find Optimal Threshold
        opt_row = df_dca.loc[df_dca['Expected_Utility'].idxmax()]
        logger.info(f"\n{asset.name}: Optimal Action Threshold = {opt_row['Threshold']:.2f}")
        logger.info(f"Max Expected Utility (Cost) = {opt_row['Expected_Utility']:.2f}")
        
    df_all_dca = pd.concat(dca_frames, ignore_index=True)
    
    # 2. Equity-Weighted Priority Example Traces
    logger.info("\n=== IMPACT-BASED WARNING EXAMPLES ===")
    examples = [
        {"prob": 0.85, "impact_mag": 0.9, "lead_time": 2.0, "asset": "HOSPITAL_ACCESS"},
        {"prob": 0.60, "impact_mag": 0.7, "lead_time": 6.0, "asset": "PUMP_STATION"},
        {"prob": 0.60, "impact_mag": 0.7, "lead_time": 6.0, "asset": "RESIDENTIAL_ROAD"},
        {"prob": 0.20, "impact_mag": 0.5, "lead_time": 48.0, "asset": "HOSPITAL_ACCESS"},
    ]
    
    warning_results = []
    for ex in examples:
        warn = ImpactBasedWarningEngine.generate_warning(
            prob=ex["prob"], impact_magnitude=ex["impact_mag"], 
            uncertainty_width=0.3, lead_time_hrs=ex["lead_time"], 
            asset_id=ex["asset"]
        )
        warning_results.append(warn)
        
    df_warnings = pd.DataFrame(warning_results)
    logger.info("\n" + df_warnings[['Asset', 'Warning_Class', 'Equity_Priority_Score', 'Action_Required']].to_string(index=False))

    # Export to docs
    out_dir = r"C:\Users\gokul\Desktop\PROJECTS\climatetwin\docs"
    df_all_dca.to_csv(os.path.join(out_dir, "decision_curve_analysis.csv"), index=False)
    df_warnings.to_csv(os.path.join(out_dir, "equity_warning_examples.csv"), index=False)
    
if __name__ == "__main__":
    main()
