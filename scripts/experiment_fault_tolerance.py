import os
import numpy as np
import pandas as pd
import time
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, f1_score, confusion_matrix
from backend.app.core.fault_injection import FaultInjector, AdaptiveForecaster
from backend.app.core.reproducibility import set_global_seed, get_logger

logger = get_logger("Fault_Tolerance_Experiment")

def evaluate_predictions(y_true, y_prob, threshold=0.5):
    y_pred = (y_prob >= threshold).astype(int)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    brier = brier_score_loss(y_true, y_prob)
    
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0,1]).ravel()
    far = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    
    return {"F1_Warning_Acc": f1, "Brier_Calib": brier, "False_Alarm_Rate": far}

def run_fault_suite():
    set_global_seed(42)
    # Generate Synthetic Data
    N_train, N_test = 2000, 2000
    X_train = np.random.randn(N_train, 3)
    y_train = (X_train[:, 0] + X_train[:, 1]*0.5 > 0.5).astype(int)
    
    X_test_clean = np.random.randn(N_test, 3)
    y_test = (X_test_clean[:, 0] + X_test_clean[:, 1]*0.5 > 0.5).astype(int)
    
    # Train Base Static Model
    base_model = LogisticRegression()
    base_model.fit(X_train, y_train)
    
    faults = {
        "1_Clean_Baseline": X_test_clean,
        "2_Random_Missing_10%": FaultInjector.random_missing(X_test_clean, rate=0.1),
        "3_Burst_Missing_1%": FaultInjector.burst_missing(X_test_clean, prob=0.01),
        "4_Stuck_At_Zero_5%": FaultInjector.stuck_at(X_test_clean, prob=0.05),
        "5_Sensor_Bias_+2.0": FaultInjector.bias(X_test_clean, offset=2.0),
        "6_Out_Of_Order_MQTT": FaultInjector.out_of_order_mqtt(X_test_clean, prob=0.1),
        "7_Comm_Outage_50T": FaultInjector.comm_outage(X_test_clean, outage_start=500, outage_end=550),
        "8_Corrupted_Noise": FaultInjector.corrupted_values(X_test_clean, noise_scale=2.0)
    }
    
    results = []
    for fault_name, X_faulty in faults.items():
        t0 = time.time()
        
        # Inference with Naive Imputation (Mean/Zero) for missing hardware data
        X_infer = np.nan_to_num(X_faulty, nan=0.0)
        p_pred = base_model.predict_proba(X_infer)[:, 1]
        
        latency_ms = (time.time() - t0) * 1000 / N_test
        
        metrics = evaluate_predictions(y_test, p_pred)
        metrics["Fault_Type"] = fault_name
        metrics["Latency_ms_per_inference"] = latency_ms
        results.append(metrics)
        
    return pd.DataFrame(results)

def run_seasonal_drift():
    set_global_seed(42)
    # Generate 4 Seasons of Data (Concept/Covariate Drift)
    N_season = 1000
    X_seasons = []
    y_seasons = []
    
    # Base Season
    X_seasons.append(np.random.randn(N_season, 3))
    y_seasons.append((X_seasons[0][:, 0] > 0).astype(int))
    
    # Drifting Seasons (Climate change / Sensor drift)
    for s in range(1, 4):
        X_s = np.random.randn(N_season, 3) + (s * 1.5) # Covariate shift
        y_s = (X_s[:, 0] > (0 + s*0.5)).astype(int) # Concept shift
        X_seasons.append(X_s)
        y_seasons.append(y_s)
        
    X_full = np.vstack(X_seasons)
    y_full = np.concatenate(y_seasons)
    
    # Model 1: Static (Trained only on Season 1)
    static_model = LogisticRegression()
    static_model.fit(X_seasons[0], y_seasons[0])
    
    # Model 2: Adaptive
    adaptive_model = AdaptiveForecaster(buffer_size=300, drift_threshold=0.2)
    adaptive_model.fit_initial(X_seasons[0], y_seasons[0])
    
    static_preds = []
    adaptive_preds = []
    
    for i in range(len(X_full)):
        static_preds.append(static_model.predict_proba(X_full[i].reshape(1, -1))[0, 1])
        adaptive_preds.append(adaptive_model.update_and_predict_proba(X_full[i], y_full[i]))
        
    static_metrics = evaluate_predictions(y_full, np.array(static_preds))
    adapt_metrics = evaluate_predictions(y_full, np.array(adaptive_preds))
    
    return pd.DataFrame([
        {"Model": "Static (No Retraining)", **static_metrics, "Retrains_Triggered": 0},
        {"Model": "Adaptive (KS Drift Auto-Retrain)", **adapt_metrics, "Retrains_Triggered": adaptive_model.retrain_counts}
    ])

def main():
    logger.info("Starting Hardware Fault Tolerance & Drift Suite...")
    
    df_faults = run_fault_suite()
    logger.info("\n=== FAULT INJECTION DEGRADATION METRICS ===")
    logger.info("\n" + df_faults[['Fault_Type', 'F1_Warning_Acc', 'Brier_Calib', 'False_Alarm_Rate', 'Latency_ms_per_inference']].to_string(index=False))
    
    df_drift = run_seasonal_drift()
    logger.info("\n=== SEASONAL DRIFT HANDLING (Adaptive vs Static) ===")
    logger.info("\n" + df_drift[['Model', 'F1_Warning_Acc', 'Brier_Calib', 'False_Alarm_Rate', 'Retrains_Triggered']].to_string(index=False))
    
    # Export
    out_dir = r"C:\Users\gokul\Desktop\PROJECTS\climatetwin\docs"
    df_faults.to_csv(os.path.join(out_dir, "fault_tolerance_metrics.csv"), index=False)
    df_drift.to_csv(os.path.join(out_dir, "drift_adaptation_metrics.csv"), index=False)
    
if __name__ == "__main__":
    main()
