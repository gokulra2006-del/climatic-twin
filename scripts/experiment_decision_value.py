import os
import json
import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix
import warnings
warnings.filterwarnings('ignore')

from backend.app.core.reproducibility import set_global_seed, get_logger

logger = get_logger("Decision_Evaluation")

# --- 1. CONFIG & DATA ---
COST_CONFIG = {
    "C_FA": 100.0,       # Cost of false alarm (wasted deployment)
    "C_MISS": 1000.0,    # Cost of a completely missed event (damage)
    "C_INT": 150.0,      # Cost of intervention (preventive)
    "C_DELAY": 50.0,     # Cost per hour of delayed intervention
    "sensitivity_ranges": {
        "C_FA": [50.0, 500.0],
        "C_MISS": [500.0, 5000.0]
    }
}

def generate_decision_timeseries(N=1000):
    set_global_seed(42)
    t = np.arange(N)
    # Generate ~10 events
    y_true = np.zeros(N)
    for _ in range(10):
        onset = np.random.randint(50, N-50)
        y_true[onset:onset+10] = 1
    
    # Forecast probability (anticipates event + noise)
    p_forecast = np.zeros(N)
    for i in range(N):
        if y_true[i] == 1:
            p_forecast[i] = np.random.uniform(0.6, 0.95)
        elif i < N-10 and np.any(y_true[i:i+10] == 1):
            p_forecast[i] = np.random.uniform(0.4, 0.8) # anticipatory
        else:
            p_forecast[i] = np.random.uniform(0.0, 0.5)
            
    # Add random spikes to cause flapping
    spikes = np.random.choice(N, 50, replace=False)
    p_forecast[spikes] += 0.3
    p_forecast = np.clip(p_forecast, 0, 1)
    
    return y_true, p_forecast

# --- 2. ALERT LOGIC ---
def simulate_alerts(p_forecast, thresh_on, thresh_off=None, cooldown=0):
    if thresh_off is None:
        thresh_off = thresh_on
        
    alerts = np.zeros(len(p_forecast))
    is_active = False
    cooldown_timer = 0
    
    for i, p in enumerate(p_forecast):
        if cooldown_timer > 0:
            cooldown_timer -= 1
            
        if not is_active:
            if p >= thresh_on and cooldown_timer == 0:
                is_active = True
                alerts[i] = 1
        else:
            if p <= thresh_off:
                is_active = False
                cooldown_timer = cooldown
            else:
                alerts[i] = 1
    return alerts

# --- 3. METRICS ---
def count_flapping(alerts):
    # Number of times alert turns on, off, and on within 4 hours
    flaps = 0
    changes = np.where(np.diff(alerts) != 0)[0]
    for i in range(len(changes)-2):
        if changes[i+2] - changes[i] <= 4:
            flaps += 1
    return flaps // 2 # pairs of on-off-on

def evaluate_decision_regret(y_true, alerts, config):
    cost = 0.0
    oracle_cost = 0.0
    
    # Simple block logic
    events = np.where(np.diff(np.pad(y_true, (1, 1))) != 0)[0].reshape(-1, 2)
    pred_events = np.where(np.diff(np.pad(alerts, (1, 1))) != 0)[0].reshape(-1, 2)
    
    tp_events = 0
    fatigue_proxy = 0 # FP events
    
    # Missed/Hits
    for t_s, t_e in events:
        oracle_cost += config["C_INT"] # Oracle always intervenes perfectly
        detected = False
        delay = 0
        for p_s, p_e in pred_events:
            if p_s <= t_e and p_e >= (t_s - 5):
                detected = True
                if p_s > t_s: delay = (p_s - t_s)
                break
        if detected:
            cost += config["C_INT"] + delay * config["C_DELAY"]
            tp_events += 1
        else:
            cost += config["C_MISS"]
            
    for p_s, p_e in pred_events:
        fa = True
        for t_s, t_e in events:
            if p_s <= t_e and p_e >= (t_s - 5):
                fa = False
                break
        if fa:
            fatigue_proxy += 1
            cost += config["C_FA"]
            
    regret = cost - oracle_cost
    return regret, tp_events, fatigue_proxy, cost

def main():
    logger.info("Starting Decision Value Evaluation (SIMULATED)...")
    y_true, p_forecast = generate_decision_timeseries(2000)
    
    # Decision Curve Analysis (DCA) - Expected Utility at various thresholds
    dca_results = []
    opt_thresh_base = COST_CONFIG["C_FA"] / (COST_CONFIG["C_FA"] + COST_CONFIG["C_MISS"])
    
    for t in np.arange(0.1, 1.0, 0.1):
        alerts = simulate_alerts(p_forecast, thresh_on=t)
        regret, tps, fps, total_cost = evaluate_decision_regret(y_true, alerts, COST_CONFIG)
        dca_results.append({
            "Threshold": round(t, 2),
            "Total_Cost": total_cost,
            "Regret_vs_Oracle": regret,
            "False_Alarm_Events": fps,
            "Flapping_Count": count_flapping(alerts)
        })
        
    df_dca = pd.DataFrame(dca_results)
    
    # Hysteresis Comparison at optimal threshold
    naive_alerts = simulate_alerts(p_forecast, thresh_on=0.6)
    hyst_alerts = simulate_alerts(p_forecast, thresh_on=0.6, thresh_off=0.4, cooldown=4)
    
    reg_n, tp_n, fp_n, cost_n = evaluate_decision_regret(y_true, naive_alerts, COST_CONFIG)
    reg_h, tp_h, fp_h, cost_h = evaluate_decision_regret(y_true, hyst_alerts, COST_CONFIG)
    
    hyst_results = pd.DataFrame([{
        "Policy": "Naive (Strict Threshold)",
        "Flapping_Count": count_flapping(naive_alerts),
        "Alert_Fatigue (FPs)": fp_n,
        "Regret": reg_n,
        "Expected_Cost": cost_n
    }, {
        "Policy": "Hysteresis (0.6 ON, 0.4 OFF, 4h Cooldown)",
        "Flapping_Count": count_flapping(hyst_alerts),
        "Alert_Fatigue (FPs)": fp_h,
        "Regret": reg_h,
        "Expected_Cost": cost_h
    }])
    
    out_dir = r"C:\Users\gokul\Desktop\PROJECTS\climatetwin\results"
    df_dca.to_csv(os.path.join(out_dir, "decision_dca.csv"), index=False)
    hyst_results.to_csv(os.path.join(out_dir, "alert_hysteresis.csv"), index=False)
    
    logger.info("\n=== HYSTERESIS / FLAPPING EFFECT ===")
    logger.info("\n" + hyst_results.to_string(index=False))

if __name__ == "__main__":
    main()
