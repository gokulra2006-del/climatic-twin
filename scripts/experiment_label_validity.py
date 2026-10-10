import os
import json
import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score, f1_score
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

from backend.app.core.reproducibility import set_global_seed, get_logger

logger = get_logger("Impact_Label_Validity")

def evaluate_threshold_sensitivity(X, y_base, X_test, y_test, title):
    # Train model on base
    clf = LogisticRegression(class_weight='balanced', random_state=42)
    clf.fit(X, y_base)
    f1 = f1_score(y_test, clf.predict(X_test), zero_division=0)
    return f1

def inject_label_noise(y, noise_level):
    y_noisy = y.copy()
    n_flips = int(len(y) * noise_level)
    flip_indices = np.random.choice(len(y), n_flips, replace=False)
    y_noisy[flip_indices] = 1 - y_noisy[flip_indices]
    return y_noisy

def main():
    logger.info("Starting Impact Label Validity Study...")
    set_global_seed(42)
    
    # 1. Generate underlying synthetic physical distribution
    N = 10000
    X = np.random.randn(N, 2)
    # Physical value (e.g., water level mm)
    physical_value = 100 + 40 * X[:, 0] + 30 * X[:, 1]
    
    # Standard threshold config: 150mm
    base_thresh = 150.0
    y_base = (physical_value > base_thresh).astype(int)
    
    # +20% / -20% thresholds
    y_high = (physical_value > (base_thresh * 1.2)).astype(int)
    y_low = (physical_value > (base_thresh * 0.8)).astype(int)
    
    # Simulated Ground Truth (Real complaint logs)
    # Assume complaint logs are basically rule-derived but have some lag/human error (~5% noise)
    y_real_complaints = inject_label_noise(y_base, 0.05)
    
    # A. Cohen's Kappa
    kappa = cohen_kappa_score(y_base, y_real_complaints)
    
    # B. Sensitivity and Label Noise effect on downstream ML
    X_train, X_test, y_base_train, y_base_test = train_test_split(X, y_base, test_size=0.2, random_state=42)
    _, _, y_high_train, _ = train_test_split(X, y_high, test_size=0.2, random_state=42)
    _, _, y_low_train, _ = train_test_split(X, y_low, test_size=0.2, random_state=42)
    
    f1_base = evaluate_threshold_sensitivity(X_train, y_base_train, X_test, y_base_test, "Base Threshold")
    f1_high = evaluate_threshold_sensitivity(X_train, y_high_train, X_test, y_base_test, "+20% Threshold")
    f1_low = evaluate_threshold_sensitivity(X_train, y_low_train, X_test, y_base_test, "-20% Threshold")
    
    f1_noise_5 = evaluate_threshold_sensitivity(X_train, inject_label_noise(y_base_train, 0.05), X_test, y_base_test, "5% Noise")
    f1_noise_10 = evaluate_threshold_sensitivity(X_train, inject_label_noise(y_base_train, 0.10), X_test, y_base_test, "10% Noise")
    f1_noise_20 = evaluate_threshold_sensitivity(X_train, inject_label_noise(y_base_train, 0.20), X_test, y_base_test, "20% Noise")
    
    results = [
        {"Experiment": "Cohen's Kappa (Rule vs Real Logs)", "Value": kappa},
        {"Experiment": "F1 (Base 150mm)", "Value": f1_base},
        {"Experiment": "F1 (Sens: +20% Thresh Train)", "Value": f1_high},
        {"Experiment": "F1 (Sens: -20% Thresh Train)", "Value": f1_low},
        {"Experiment": "F1 (Noise: 5% Training Corrupted)", "Value": f1_noise_5},
        {"Experiment": "F1 (Noise: 10% Training Corrupted)", "Value": f1_noise_10},
        {"Experiment": "F1 (Noise: 20% Training Corrupted)", "Value": f1_noise_20}
    ]
    
    df = pd.DataFrame(results)
    out_dir = r"C:\Users\gokul\Desktop\PROJECTS\climatetwin\results"
    df.to_csv(os.path.join(out_dir, "label_validity_metrics.csv"), index=False)
    
    logger.info("\n=== LABEL VALIDITY & NOISE SENSITIVITY ===")
    logger.info("\n" + df.to_string(index=False))

if __name__ == "__main__":
    main()
