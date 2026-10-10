import os
import time
import numpy as np
import pandas as pd
import networkx as nx
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import mean_squared_error, confusion_matrix
import warnings
warnings.filterwarnings('ignore')

from backend.app.core.reproducibility import set_global_seed, get_logger

logger = get_logger("Sensor_Networks")

# ==========================================
# PART A: MISSING DATA RECOVERY
# ==========================================
def generate_timeseries(N=1000):
    t = np.linspace(0, 100, N)
    signal = np.sin(t) + np.sin(3*t) * 0.5 + np.random.normal(0, 0.1, N)
    hazard = (signal > 1.0).astype(int)
    return signal, hazard

def inject_missingness(signal, rate, m_type="random"):
    mask = np.ones(len(signal), dtype=bool)
    if m_type == "random":
        drop_idx = np.random.choice(len(signal), int(len(signal) * rate), replace=False)
        mask[drop_idx] = False
    elif m_type == "burst":
        n_bursts = int((len(signal) * rate) // 20) + 1
        for _ in range(n_bursts):
            start = np.random.randint(0, len(signal) - 20)
            mask[start:start+20] = False
    sig_missing = signal.copy()
    sig_missing[~mask] = np.nan
    return sig_missing, mask

def impute_data(sig_missing, method):
    s = pd.Series(sig_missing)
    if method == "lvh":
        s = s.ffill().bfill()
    elif method == "interpolation":
        s = s.interpolate(method='linear').bfill().ffill()
    elif method == "statistical":
        s = s.fillna(s.mean())
    elif method == "enkf_proxy":
        s_int = s.interpolate(method='linear').bfill().ffill()
        s = s_int.ewm(alpha=0.3).mean()
    elif method == "model_based":
        s = s.interpolate(method='polynomial', order=2).bfill().ffill()
    return s.fillna(0).values # ultimate fallback

def evaluate_imputation(y_true, hazard, y_imp):
    rmse = np.sqrt(mean_squared_error(y_true, y_imp))
    cov = np.mean((y_true >= y_imp - 0.5) & (y_true <= y_imp + 0.5))
    
    # Needs balanced classes for stable logreg
    if sum(hazard) == 0 or sum(hazard) == len(hazard): 
        return rmse, cov, 0.0, 0.0
        
    clf = LogisticRegression(class_weight='balanced').fit(y_true.reshape(-1, 1), hazard)
    haz_pred = clf.predict(y_imp.reshape(-1, 1))
    
    eps = 1e-9
    tn, fp, fn, tp = confusion_matrix(hazard, haz_pred, labels=[0, 1]).ravel()
    pod = tp / (tp + fn + eps)
    far = fp / (tp + fp + eps)
    
    return rmse, cov, pod, far

def run_part_a():
    set_global_seed(42)
    rates = [0.1, 0.3, 0.5, 0.7]
    types = ["random", "burst"]
    methods = ["lvh", "interpolation", "statistical", "enkf_proxy", "model_based"]
    
    sig_true, haz_true = generate_timeseries(2000)
    results = []
    
    for r in rates:
        for t in types:
            sig_miss, _ = inject_missingness(sig_true, r, t)
            for m in methods:
                start = time.time()
                sig_imp = impute_data(sig_miss, m)
                lat = (time.time() - start) * 1000 # ms
                
                rmse, cov, pod, far = evaluate_imputation(sig_true, haz_true, sig_imp)
                results.append({
                    "Missing_Type": t, "Rate": r, "Method": m,
                    "RMSE": round(rmse,3), "Coverage": round(cov,3), "POD": round(pod,3), "FAR": round(far,3), "Latency_ms": round(lat,2)
                })
    return pd.DataFrame(results)

# ==========================================
# PART B: SENSOR PLACEMENT
# ==========================================
def run_part_b():
    set_global_seed(42)
    N_NODES = 100
    G = nx.barabasi_albert_graph(N_NODES, 3, seed=42)
    
    risk = np.random.exponential(1.0, N_NODES)
    risk /= risk.sum()
    
    uncertainty = np.random.uniform(0, 1, N_NODES)
    centrality = np.array(list(nx.betweenness_centrality(G).values()))
    
    strategies = ["Random", "High-Risk", "Uncertainty-Reduction", "Dependency-Centrality"]
    budgets = [5, 10, 20, 30, 40, 50]
    
    results = []
    
    for budget in budgets:
        for strat in strategies:
            pods = []
            for seed in range(20):
                np.random.seed(seed)
                if strat == "Random":
                    chosen = np.random.choice(N_NODES, budget, replace=False)
                elif strat == "High-Risk":
                    chosen = np.argsort(risk)[-budget:]
                elif strat == "Uncertainty-Reduction":
                    chosen = np.argsort(uncertainty)[-budget:]
                elif strat == "Dependency-Centrality":
                    chosen = np.argsort(centrality)[-budget:]
                    
                events = np.random.choice(N_NODES, 500, p=risk)
                detected = 0
                for ev in events:
                    neighbors = list(G.neighbors(ev)) + [ev]
                    if any(c in neighbors for c in chosen):
                        detected += 1
                pods.append(detected / 500.0)
                
            results.append({
                "Strategy": strat,
                "Budget": budget,
                "POD_Mean": round(np.mean(pods),3),
                "POD_2_5": round(np.percentile(pods, 2.5),3),
                "POD_97_5": round(np.percentile(pods, 97.5),3)
            })
            
    return pd.DataFrame(results)

def main():
    logger.info("Running Missing Data Recovery (Part A)...")
    df_a = run_part_a()
    
    logger.info("Running Sensor Placement (Part B)...")
    df_b = run_part_b()
    
    out_dir = r"C:\Users\gokul\Desktop\PROJECTS\climatetwin\results"
    df_a.to_csv(os.path.join(out_dir, "missing_data_recovery.csv"), index=False)
    df_b.to_csv(os.path.join(out_dir, "sensor_placement.csv"), index=False)
    
    logger.info("Ablations complete.")

if __name__ == "__main__":
    main()
