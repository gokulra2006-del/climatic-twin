import os
import math
import itertools
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.inspection import permutation_importance
import warnings
warnings.filterwarnings('ignore')

from backend.app.core.reproducibility import set_global_seed, get_logger
logger = get_logger("Explainability_Verification")

def generate_tabular_data(N=1000):
    set_global_seed(42)
    X = np.random.randn(N, 5)
    X[:, 1] = X[:, 0] * 0.8 + np.random.randn(N) * 0.2 
    logit = 2.0 * X[:, 0] + 0.5 * X[:, 1] + 1.5 * X[:, 2] - 1.0 * X[:, 3] + 0.1 * X[:, 4] - 0.5
    prob = 1 / (1 + np.exp(-logit))
    y = (prob > 0.5).astype(int)
    feature_names = ["Rain_1h", "Rain_24h", "Upstream", "Pump", "Slope"]
    return pd.DataFrame(X, columns=feature_names), y

def exact_shapley(model, x_instance, X_background):
    n_features = len(x_instance)
    shap_vals = np.zeros(n_features)
    bg_mean = X_background.mean().values
    
    for i in range(n_features):
        marginal_contributions = []
        other_features = [f for f in range(n_features) if f != i]
        for size in range(len(other_features) + 1):
            for subset in itertools.combinations(other_features, size):
                subset = list(subset)
                
                x_without = bg_mean.copy()
                x_without[subset] = x_instance[subset]
                
                x_with = x_without.copy()
                x_with[i] = x_instance[i]
                
                p_without = model.predict_proba(x_without.reshape(1, -1))[0, 1]
                p_with = model.predict_proba(x_with.reshape(1, -1))[0, 1]
                
                weight = (math.factorial(size) * math.factorial(n_features - size - 1)) / math.factorial(n_features)
                marginal_contributions.append(weight * (p_with - p_without))
                
        shap_vals[i] = np.sum(marginal_contributions)
    return shap_vals

def get_global_shap(model, X_sample, X_bg):
    shaps = np.array([exact_shapley(model, x.values, X_bg) for _, x in X_sample.iterrows()])
    return np.abs(shaps).mean(axis=0)

def main():
    logger.info("Starting Explainability Verification...")
    X, y = generate_tabular_data(2000)
    
    X_train, y_train = X.iloc[:1500], y[:1500]
    X_test, y_test = X.iloc[1500:], y[1500:]
    
    rf = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42)
    rf.fit(X_train, y_train)
    
    lr = LogisticRegression(random_state=42)
    lr.fit(X_train, y_train)
    
    # Use 15 samples to make it lightning fast
    sample_idx = np.random.choice(len(X_test), 15, replace=False)
    X_sample = X_test.iloc[sample_idx]
    
    perm_rf = permutation_importance(rf, X_test, y_test, n_repeats=5, random_state=42).importances_mean
    shap_rf = get_global_shap(rf, X_sample, X_train)
    
    rank_perm = np.argsort(np.argsort(perm_rf))
    rank_shap = np.argsort(np.argsort(shap_rf))
    rho_shap_perm, _ = spearmanr(rank_perm, rank_shap)
    
    shap_lr = get_global_shap(lr, X_sample, X_train)
    rank_shap_lr = np.argsort(np.argsort(shap_lr))
    rho_rf_lr, _ = spearmanr(rank_shap, rank_shap_lr)
    
    preds_rf = rf.predict(X_sample)
    
    # FIX: y_test is numpy array
    tps = X_sample[(y_test[sample_idx] == 1) & (preds_rf == 1)]
    
    flips = 0
    bg_means = X_train.mean()
    for idx, row in tps.iterrows():
        shaps = exact_shapley(rf, row.values, X_train)
        top_idx = np.argmax(np.abs(shaps))
        
        row_pert = row.copy()
        row_pert.iloc[top_idx] = bg_means.iloc[top_idx] 
        if rf.predict(row_pert.values.reshape(1, -1))[0] == 0:
            flips += 1
    counterfactual_rate = flips / max(1, len(tps))
    
    X_noise = X_sample + np.random.normal(0, 0.05, X_sample.shape)
    shap_noise = get_global_shap(rf, X_noise, X_train)
    rank_noise = np.argsort(np.argsort(shap_noise))
    rho_noise, _ = spearmanr(rank_shap, rank_noise)
    
    X_fault = X_sample.copy()
    X_fault.iloc[:, 0] = 0.0
    shap_fault = get_global_shap(rf, X_fault, X_train)
    rank_fault = np.argsort(np.argsort(shap_fault))
    rho_fault, _ = spearmanr(rank_shap, rank_fault)
    
    results = [
        {"Test": "Rank Corr: SHAP vs Permutation (Internal Consistency)", "Spearman_Rho": round(rho_shap_perm, 3)},
        {"Test": "Rank Corr: RF vs LogReg (Model Agreement)", "Spearman_Rho": round(rho_rf_lr, 3)},
        {"Test": "Rank Corr: Clean vs 5% Noise (Stability)", "Spearman_Rho": round(rho_noise, 3)},
        {"Test": "Rank Corr: Clean vs Sensor Fault (Drift Resilience)", "Spearman_Rho": round(rho_fault, 3)},
        {"Test": "Counterfactual Prediction Flip Rate", "Spearman_Rho": round(counterfactual_rate, 3)}
    ]
    
    df = pd.DataFrame(results)
    out_dir = r"C:\Users\gokul\Desktop\PROJECTS\climatetwin\results"
    df.to_csv(os.path.join(out_dir, "explainability_metrics.csv"), index=False)
    
    logger.info("\n" + df.to_string(index=False))

if __name__ == "__main__":
    main()
