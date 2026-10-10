import numpy as np
import pandas as pd
import time
import sys
import os

from backend.app.core.enkf_assimilation import ReservoirEnKF
from backend.app.core.reproducibility import set_global_seed, get_logger

logger = get_logger("EnKF_Experiment")

# --- Naive Newtonian Nudging ---
class NewtonianNudging:
    def __init__(self, alpha=0.2):
        self.state = np.zeros(4)
        self.alpha = alpha
    def process_model(self):
        pass # persistence
    def assimilate(self, obs, faults=None):
        if not faults: faults = {}
        vars = ["POONDI", "CHOLAVARAM", "REDHILLS", "CHEMBARAMBAKKAM"]
        for i, var in enumerate(vars):
            if var in obs:
                if faults.get(var) in ["stuck", "biased"]: continue # Drop naive
                self.state[i] = self.state[i] + self.alpha * (obs[var] - self.state[i])
        return self.state

def run_experiment(timesteps=100, N=100, drop_sensors=0, fault_rate=0.0):
    set_global_seed(42)
    vars = ["POONDI", "CHOLAVARAM", "REDHILLS", "CHEMBARAMBAKKAM"]
    
    # Generate True State Walk
    true_state = np.zeros((timesteps, 4))
    true_state[0] = np.array([2000, 500, 1500, 2500])
    for t in range(1, timesteps):
        true_state[t] = true_state[t-1] + np.random.normal(0, 50, 4)
        true_state[t] = np.clip(true_state[t], 0, None)
        
    # Generate Observations with noise
    obs_data = []
    faults_data = []
    
    for t in range(timesteps):
        obs = {}
        faults = {}
        for i, var in enumerate(vars):
            # Drop some sensors explicitly (simulate sensor loss)
            if i < (4 - drop_sensors): 
                # Add observation noise
                val = true_state[t, i] + np.random.normal(0, [400, 150, 350, 450][i])
                
                # Introduce fault
                if np.random.rand() < fault_rate:
                    val = 5000.0 # Huge stuck value
                    faults[var] = "stuck"
                    
                obs[var] = max(0, val)
        obs_data.append(obs)
        faults_data.append(faults)
        
    # --- Run Models ---
    # 1. No Assimilation (Persistence from t=0)
    no_assimil = np.zeros((timesteps, 4))
    no_assimil[:] = true_state[0]
    
    # 2. Newtonian Nudging
    nudger = NewtonianNudging(alpha=0.3)
    nudging_track = np.zeros((timesteps, 4))
    
    t0 = time.time()
    for t in range(timesteps):
        nudger.process_model()
        nudging_track[t] = nudger.assimilate(obs_data[t], faults_data[t]).copy()
    nudging_time = time.time() - t0
        
    # 3. EnKF
    enkf = ReservoirEnKF(N=N)
    # Give EnKF the same initial mean but wide variance
    for i in range(N): enkf.ensemble[i] = true_state[0] + np.random.normal(0, 500, 4)
    enkf_track = np.zeros((timesteps, 4))
    
    import tracemalloc
    tracemalloc.start()
    t0 = time.time()
    for t in range(timesteps):
        enkf.process_model()
        enkf_track[t] = enkf.assimilate(obs_data[t], faults_data[t])
    enkf_time = time.time() - t0
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    # Calculate Errors (RMSE)
    err_no = np.sqrt(np.mean((true_state - no_assimil)**2))
    err_nudge = np.sqrt(np.mean((true_state - nudging_track)**2))
    err_enkf = np.sqrt(np.mean((true_state - enkf_track)**2))
    
    return {
        "N": N, "Dropped_Sensors": drop_sensors, "Fault_Rate": fault_rate,
        "RMSE_NoAssim": err_no, "RMSE_Nudging": err_nudge, "RMSE_EnKF": err_enkf,
        "EnKF_Time_ms": enkf_time * 1000,
        "EnKF_Memory_KB": peak / 1024
    }

def main():
    logger.info("Starting EnKF vs Nudging Assimilation Experiments...")
    results = []
    
    # Experiment 1: Ensemble Size Sweep (Baseline 0 dropped, 0 fault)
    for N in [10, 50, 100, 500]:
        res = run_experiment(N=N)
        res["Exp"] = "Ensemble_Size"
        results.append(res)
        
    # Experiment 2: Sensor Density Sweep (N=100)
    for d in [0, 1, 2, 3]:
        res = run_experiment(N=100, drop_sensors=d)
        res["Exp"] = "Sensor_Density"
        results.append(res)
        
    # Experiment 3: Fault Tolerant Test (N=100, random stuck faults)
    for f in [0.0, 0.1, 0.2, 0.5]:
        res = run_experiment(N=100, drop_sensors=0, fault_rate=f)
        res["Exp"] = "Fault_Tolerance"
        results.append(res)
        
    df = pd.DataFrame(results)
    
    # Log formatted output
    for exp_type in df["Exp"].unique():
        logger.info(f"\nExperiment: {exp_type}")
        logger.info("\n" + df[df["Exp"] == exp_type].drop(columns=["Exp"]).to_string(index=False))
        
    # Save
    out_dir = r"C:\Users\gokul\Desktop\PROJECTS\climatetwin\docs"
    df.to_csv(os.path.join(out_dir, "enkf_experiments.csv"), index=False)
    with open(os.path.join(out_dir, "enkf_experiments.tex"), "w") as f:
        f.write(df.to_latex(index=False, caption="EnKF vs Newtonian Nudging Evaluation"))

if __name__ == "__main__":
    main()
