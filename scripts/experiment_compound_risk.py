import os
import numpy as np
import pandas as pd
from sklearn.metrics import log_loss, brier_score_loss
from sklearn.calibration import calibration_curve
from backend.app.core.probabilistic_risk import ProbabilisticCompoundRiskEngine
from backend.app.core.reproducibility import set_global_seed, get_logger

logger = get_logger("Compound_Risk_Experiment")

def generate_compound_hazard_data(n_samples=5000):
    """
    Generates synthetic multi-hazard data with known interaction effects.
    Includes a 'protective' / negative interaction to prove the regularized
    regression can discover it (e.g. high wind evaporates minor flooding).
    """
    # Features: Rain, Reservoir, Wind, Heat
    X = np.random.uniform(0, 1, size=(n_samples, 4))
    
    # True data generation logic
    # Base risk:
    logit = -3.0 + 2.5 * X[:, 0] + 1.5 * X[:, 1] + 0.5 * X[:, 2] + 0.5 * X[:, 3]
    
    # Positive Synergistic Interaction: Rain x Reservoir (Overflow)
    logit += 3.0 * (X[:, 0] * X[:, 1])
    
    # Negative / Protective Interaction: Wind x Rain (Wind blows storm fast, less pooling)
    logit -= 2.0 * (X[:, 0] * X[:, 2])
    
    # Probability of impact
    prob = 1.0 / (1.0 + np.exp(-logit))
    
    # Rare events: ensure low base rate
    y = (np.random.rand(n_samples) < prob).astype(int)
    
    return X, y

def main():
    logger.info("Starting Compound Risk Probabilistic Evaluation...")
    set_global_seed(42)
    
    feature_names = ["Rain", "Reservoir", "Wind", "Heat"]
    
    X, y = generate_compound_hazard_data(n_samples=10000)
    logger.info(f"Target Base Rate (Rare Event Prevalence): {np.mean(y)*100:.2f}%")
    
    # Chronological Split Mock
    train_idx = int(0.7 * len(X))
    X_train, y_train = X[:train_idx], y[:train_idx]
    X_test, y_test = X[train_idx:], y[train_idx:]
    
    # 1. Additive Model (Baseline)
    additive_model = ProbabilisticCompoundRiskEngine(use_interactions=False, penalty='l2', C=1.0)
    additive_model.fit(X_train, y_train, feature_names)
    p_additive = additive_model.predict_proba(X_test)
    
    # 2. Interacting Model (Refit)
    interact_model = ProbabilisticCompoundRiskEngine(use_interactions=True, penalty='l2', C=1.0)
    interact_model.fit(X_train, y_train, feature_names)
    p_interact = interact_model.predict_proba(X_test)
    
    # Metrics
    results = []
    for name, p_pred in [("Additive_Only", p_additive), ("Interacting_Model", p_interact)]:
        ll = log_loss(y_test, p_pred)
        bs = brier_score_loss(y_test, p_pred)
        results.append({
            "Model": name,
            "Log_Loss": ll,
            "Brier_Score": bs
        })
        
    df_metrics = pd.DataFrame(results)
    logger.info("\n=== EVALUATION METRICS ===")
    logger.info("\n" + df_metrics.to_string(index=False))
    
    # Calibration Curve (Reliability Diagram calculation)
    logger.info("\n=== RELIABILITY / CALIBRATION CURVES ===")
    calib_data = []
    for name, p_pred in [("Additive_Only", p_additive), ("Interacting_Model", p_interact)]:
        prob_true, prob_pred = calibration_curve(y_test, p_pred, n_bins=5)
        for i in range(len(prob_true)):
            calib_data.append({
                "Model": name,
                "Bin": i+1,
                "Predicted_Prob": prob_pred[i],
                "True_Empirical_Prob": prob_true[i]
            })
            
    df_calib = pd.DataFrame(calib_data)
    # Pivot for easier logging
    df_calib_pivot = df_calib.pivot(index="Bin", columns="Model", values=["Predicted_Prob", "True_Empirical_Prob"])
    logger.info("\n" + df_calib_pivot.to_string())

    # Discovered Coefficients
    coeffs = interact_model.get_coefficients()
    df_coeff = pd.DataFrame(list(coeffs.items()), columns=["Feature", "Learned_Weight_w_i"])
    df_coeff = df_coeff.sort_values(by="Learned_Weight_w_i", ascending=False)
    logger.info("\n=== LEARNED COEFFICIENTS (w_i and gamma_ij) ===")
    logger.info("\n" + df_coeff.to_string(index=False))
    
    # Export
    out_dir = r"C:\Users\gokul\Desktop\PROJECTS\climatetwin\docs"
    df_metrics.to_csv(os.path.join(out_dir, "compound_risk_metrics.csv"), index=False)
    df_calib.to_csv(os.path.join(out_dir, "compound_risk_calibration.csv"), index=False)
    df_coeff.to_csv(os.path.join(out_dir, "compound_risk_coefficients.csv"), index=False)

if __name__ == "__main__":
    main()
