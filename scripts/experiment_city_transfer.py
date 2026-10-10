import os
import json
import numpy as np
import pandas as pd
import copy
from sklearn.neural_network import MLPClassifier
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import brier_score_loss, f1_score, roc_auc_score, accuracy_score
from sklearn.preprocessing import StandardScaler
from backend.app.core.reproducibility import set_global_seed, get_logger

logger = get_logger("City_Transfer_Learning")

def generate_city_data(n, shift_mu, shift_sigma, seed=42):
    """Generates synthetic physics-informed hazard data for a specific city profile."""
    np.random.seed(seed)
    X = np.random.randn(n, 4) * shift_sigma + shift_mu
    
    # The true underlying physical relationship (Z-normalized)
    X_norm = (X - shift_mu) / shift_sigma
    logit = 1.5 * X_norm[:, 0] - 1.0 * X_norm[:, 1] + 0.5 * X_norm[:, 2] + np.random.randn(n) * 0.5
    prob = 1 / (1 + np.exp(-logit))
    
    y = (prob > 0.5).astype(int)
    return X, y

def evaluate_metrics(y_true, p_pred):
    y_pred = (p_pred >= 0.5).astype(int)
    return {
        "ROC_AUC": roc_auc_score(y_true, p_pred),
        "F1_Score": f1_score(y_true, y_pred, zero_division=0),
        "Brier_Score": brier_score_loss(y_true, p_pred)
    }

def main():
    logger.info("Starting City-Agnostic Transfer Learning Experiments...")
    set_global_seed(42)
    
    # Load configuration 
    config_path = r"C:\Users\gokul\Desktop\PROJECTS\climatetwin\backend\app\core\city_configs.json"
    with open(config_path, "r") as f:
        cities = json.load(f)
    
    logger.info(f"Loaded Configurations for: {list(cities.keys())}")
    
    # 1. Generate Domain-Shifted Data
    # City A (Chennai)
    X_A, y_A = generate_city_data(2500, shift_mu=10.0, shift_sigma=2.0, seed=42)
    X_A_train, y_A_train = X_A[:2000], y_A[:2000]
    X_A_test, y_A_test = X_A[2000:], y_A[2000:]
    
    # City B (Mumbai - Severe Covariate Shift: different means and variances)
    X_B, y_B = generate_city_data(2500, shift_mu=25.0, shift_sigma=5.0, seed=100)
    X_B_train, y_B_train = X_B[:2000], y_B[:2000]
    X_B_test, y_B_test = X_B[2000:], y_B[2000:]
    
    # Few-shot slice (50 samples)
    X_B_few, y_B_few = X_B_train[:50], y_B_train[:50]
    
    # 2. Train Base Model A (Chennai)
    scaler_A = StandardScaler().fit(X_A_train)
    model_A = MLPClassifier(hidden_layer_sizes=(16,), max_iter=500, random_state=42)
    model_A.fit(scaler_A.transform(X_A_train), y_A_train)
    
    results = []
    
    # --- Experiment 1: Same City (A -> A) ---
    p_A = model_A.predict_proba(scaler_A.transform(X_A_test))[:, 1]
    res = evaluate_metrics(y_A_test, p_A)
    results.append({"Experiment": "Same City (Train A -> Test A)", **res})
    
    # --- Experiment 2: Zero-Shot (A -> B) ---
    p_zero = model_A.predict_proba(scaler_A.transform(X_B_test))[:, 1]
    res = evaluate_metrics(y_B_test, p_zero)
    results.append({"Experiment": "Zero-Shot (Train A -> Test B)", **res})
    
    # --- Experiment 3: Unsupervised Domain Adaptation (Covariate Whitening) ---
    # We use unlabeled City B data to learn the domain shift, and map it back
    scaler_B = StandardScaler().fit(X_B_train) # Unsupervised
    p_da = model_A.predict_proba(scaler_B.transform(X_B_test))[:, 1]
    res = evaluate_metrics(y_B_test, p_da)
    results.append({"Experiment": "Domain Adaptation (Covariate Shift Alignment)", **res})
    
    # --- Experiment 4: Recalibration Without Retraining ---
    p_zero_few = model_A.predict_proba(scaler_A.transform(X_B_few))[:, 1]
    iso = IsotonicRegression(out_of_bounds='clip')
    iso.fit(p_zero_few, y_B_few)
    p_recal = iso.predict(p_zero)
    res = evaluate_metrics(y_B_test, p_recal)
    results.append({"Experiment": "Post-Hoc Recalibration (Isotonic on 50 samples)", **res})
    
    # --- Experiment 5: Few-Shot Fine-Tuning ---
    model_few = copy.deepcopy(model_A)
    # Warm start partial fit on the 50 labels
    for _ in range(20): 
        model_few.partial_fit(scaler_A.transform(X_B_few), y_B_few, classes=np.array([0, 1]))
    p_few = model_few.predict_proba(scaler_A.transform(X_B_test))[:, 1]
    res = evaluate_metrics(y_B_test, p_few)
    results.append({"Experiment": "Few-Shot Fine-Tuning (50 samples)", **res})
    
    # --- Experiment 6: Fully Trained Target Model (Upper Bound Baseline B -> B) ---
    model_B = MLPClassifier(hidden_layer_sizes=(16,), max_iter=500, random_state=42)
    model_B.fit(scaler_B.transform(X_B_train), y_B_train)
    p_B = model_B.predict_proba(scaler_B.transform(X_B_test))[:, 1]
    res = evaluate_metrics(y_B_test, p_B)
    results.append({"Experiment": "Same City Target Baseline (Train B -> Test B)", **res})
    
    # Compile and Log
    df_results = pd.DataFrame(results)
    
    logger.info("\n=== TRANSFER LEARNING & DOMAIN ADAPTATION SUITE ===")
    logger.info("\n" + df_results.to_string(index=False))
    
    # Save 
    out_dir = r"C:\Users\gokul\Desktop\PROJECTS\climatetwin\docs"
    df_results.to_csv(os.path.join(out_dir, "city_transfer_learning.csv"), index=False)

if __name__ == "__main__":
    main()
