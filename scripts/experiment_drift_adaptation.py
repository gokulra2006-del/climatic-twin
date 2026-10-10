import os
import time
import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, confusion_matrix, brier_score_loss
from sklearn.neural_network import MLPClassifier
from sklearn.isotonic import IsotonicRegression
from scipy.stats import ks_2samp, wasserstein_distance
import warnings
warnings.filterwarnings('ignore')

from backend.app.core.reproducibility import set_global_seed, get_logger

logger = get_logger("Drift_Adaptation")

# --- 1. DATA GENERATION ---
def generate_drift_data(n_samples=2000, regime="base"):
    set_global_seed(42)
    # Features: Rain, Upstream
    if regime == "base":
        X = np.random.randn(n_samples, 2)
    elif regime == "synthetic_trend":
        # Slowly increasing trend in rainfall (Feature 0)
        X = np.random.randn(n_samples, 2)
        trend = np.linspace(0, 3.0, n_samples)
        X[:, 0] += trend
    elif regime == "cross_season":
        # Abrupt shift in covariance/mean
        X = np.random.randn(n_samples, 2)
        X[:, 1] += 2.5 # Upstream baseline jumps
        X[:, 0] *= 1.5 # Higher variance
        
    # True relationship
    logit = 1.5 * X[:, 0] + 0.8 * X[:, 1] - 2.0
    prob = 1 / (1 + np.exp(-logit))
    y = (prob > 0.5).astype(int)
    return X, y

# --- 2. REGIME WRAPPERS ---
class StaticModel:
    def __init__(self):
        self.model = MLPClassifier(hidden_layer_sizes=(16,), max_iter=50, random_state=42)
        self.retrain_cost = 0.0
    def fit(self, X, y):
        start = time.time()
        self.model.fit(X, y)
        self.retrain_cost += (time.time() - start)
    def predict_proba(self, X):
        return self.model.predict_proba(X)[:, 1]
    def predict(self, X):
        return self.model.predict(X)

class RecalibratedModel(StaticModel):
    def __init__(self):
        super().__init__()
        self.calibrator = None
    def adapt(self, X_buffer, y_buffer):
        start = time.time()
        base_preds = super().predict_proba(X_buffer)
        self.calibrator = IsotonicRegression(out_of_bounds='clip')
        self.calibrator.fit(base_preds, y_buffer)
        self.retrain_cost += (time.time() - start)
    def predict_proba(self, X):
        base = super().predict_proba(X)
        if self.calibrator:
            return self.calibrator.predict(base)
        return base
    def predict(self, X):
        return (self.predict_proba(X) > 0.5).astype(int)

class AdaptiveModel(StaticModel):
    def __init__(self):
        super().__init__()
        self.X_history = None
        self.y_history = None
    def fit(self, X, y):
        super().fit(X, y)
        self.X_history = X
        self.y_history = y
    def adapt(self, X_buffer, y_buffer):
        # Expanding window
        self.X_history = np.vstack([self.X_history, X_buffer])
        self.y_history = np.concatenate([self.y_history, y_buffer])
        super().fit(self.X_history, self.y_history)

# --- 3. METRICS EVALUATION ---
def evaluate_metrics(y_true, y_prob, threshold=0.5):
    y_pred = (y_prob > threshold).astype(int)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    eps = 1e-9
    far = fp / (tp + fp + eps)
    brier = brier_score_loss(y_true, y_prob)
    return f1, far, brier

# --- 4. SIMULATION LOOP ---
def run_simulation(regime_name, X_stream, y_stream, X_ref, y_ref):
    models = {
        "Static": StaticModel(),
        "Recalibrated (Isotonic)": RecalibratedModel(),
        "Retrained (Expanding)": AdaptiveModel()
    }
    
    # Initial Fit
    for m in models.values():
        m.fit(X_ref, y_ref)
        
    block_size = 100
    n_blocks = len(y_stream) // block_size
    
    metrics_log = []
    
    buffer_X, buffer_y = [], []
    in_drift = False
    drift_detected_block = -1
    
    for i in range(n_blocks):
        start = i * block_size
        end = start + block_size
        X_b, y_b = X_stream[start:end], y_stream[start:end]
        
        buffer_X.append(X_b)
        buffer_y.append(y_b)
        if len(buffer_X) > 3: # Keep sliding window
            buffer_X.pop(0)
            buffer_y.pop(0)
            
        cur_window_X = np.vstack(buffer_X)
        cur_window_y = np.concatenate(buffer_y)
        
        # Drift Detection (KS Test on Feature 0)
        ks_stat, p_val = ks_2samp(X_ref[:, 0], cur_window_X[:, 0])
        drift_trigger = (p_val < 0.01)
        
        if drift_trigger and not in_drift:
            in_drift = True
            drift_detected_block = i
            # Trigger Adaptation
            models["Recalibrated (Isotonic)"].adapt(cur_window_X, cur_window_y)
            models["Retrained (Expanding)"].adapt(cur_window_X, cur_window_y)
            
        # Record Metrics
        for name, model in models.items():
            prob = model.predict_proba(X_b)
            f1, far, brier = evaluate_metrics(y_b, prob)
            metrics_log.append({
                "Regime": regime_name,
                "Model": name,
                "Block": i,
                "F1": f1,
                "FAR": far,
                "Brier": brier,
                "Drift_Active": in_drift
            })
            
    return pd.DataFrame(metrics_log), models

def main():
    logger.info("Starting Drift Adaptation Regimes Evaluation...")
    set_global_seed(42)
    
    X_base, y_base = generate_drift_data(2000, "base")
    X_trend, y_trend = generate_drift_data(2000, "synthetic_trend")
    X_season, y_season = generate_drift_data(2000, "cross_season")
    
    # Run regimes
    df_trend, mods_trend = run_simulation("Synthetic Trend (Rain)", X_trend, y_trend, X_base[:1000], y_base[:1000])
    df_season, mods_season = run_simulation("Cross-Season (Abrupt)", X_season, y_season, X_base[:1000], y_base[:1000])
    
    df_all = pd.concat([df_trend, df_season])
    
    # Extract Before/After metrics
    summary = []
    for regime in df_all["Regime"].unique():
        for model in df_all["Model"].unique():
            subset = df_all[(df_all["Regime"] == regime) & (df_all["Model"] == model)]
            
            # First 5 blocks (Before drift impact hits hard)
            f1_before = subset.iloc[:5]["F1"].mean()
            # Last 5 blocks (After recovery)
            f1_after = subset.iloc[-5:]["F1"].mean()
            far_before = subset.iloc[:5]["FAR"].mean()
            far_after = subset.iloc[-5:]["FAR"].mean()
            calib_deg = subset.iloc[-5:]["Brier"].mean() - subset.iloc[:5]["Brier"].mean()
            
            # Catastrophic Forgetting (evaluating the adapted models on original base data)
            if regime == "Synthetic Trend (Rain)":
                model_obj = mods_trend[model]
            else:
                model_obj = mods_season[model]
                
            forget_prob = model_obj.predict_proba(X_base[-1000:])
            f1_forget, _, _ = evaluate_metrics(y_base[-1000:], forget_prob)
            
            retrain_cost = model_obj.retrain_cost
            
            summary.append({
                "Regime": regime,
                "Model": model,
                "F1_Before": round(f1_before, 3),
                "F1_After": round(f1_after, 3),
                "FAR_Change": round(far_after - far_before, 3),
                "Calib_Degradation": round(calib_deg, 3),
                "Retrain_Cost_sec": round(retrain_cost, 4),
                "Catastrophic_F1_Base": round(f1_forget, 3)
            })
            
    df_summary = pd.DataFrame(summary)
    
    out_dir = r"C:\Users\gokul\Desktop\PROJECTS\climatetwin\results"
    df_all.to_csv(os.path.join(out_dir, "drift_block_metrics.csv"), index=False)
    df_summary.to_csv(os.path.join(out_dir, "drift_adaptation_summary.csv"), index=False)
    
    logger.info("\n" + df_summary.to_string(index=False))

if __name__ == "__main__":
    main()
