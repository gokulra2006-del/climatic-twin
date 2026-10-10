import os
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, confusion_matrix

from backend.app.core.reproducibility import set_global_seed, get_logger

logger = get_logger("Physics_Constraints")

# --- 1. SYNTHETIC PHYSICS DATA GENERATOR ---
def generate_synthetic_physics_data(N=2000, ood=False):
    """
    Simulates a synthetic downstream reservoir node constrained by physics.
    Max Capacity = 100.0, Max Rate of Change = 15.0/timestep, Non-negative.
    """
    rain = np.random.exponential(5.0, N) if not ood else np.random.exponential(25.0, N)
    upstream = np.random.uniform(0, 50, N)
    pump = np.random.choice([0, 1], N) # 1 = On (drains 10.0), 0 = Off
    
    h_current = np.random.uniform(10, 80, N)
    h_next = np.zeros(N)
    
    for i in range(N):
        delta_h = 1.2 * rain[i] + 0.3 * upstream[i] - 10.0 * pump[i]
        # Physics clipping
        h_true = h_current[i] + delta_h
        h_true = max(0.0, min(100.0, h_true)) # Cap and non-negative
        # Rate limit
        if h_true - h_current[i] > 15.0: h_true = h_current[i] + 15.0
        elif h_true - h_current[i] < -15.0: h_true = h_current[i] - 15.0
        
        h_next[i] = h_true + np.random.normal(0, 1.0) # Small observation noise
        
    X = np.stack([h_current, rain, upstream, pump], axis=1)
    return torch.FloatTensor(X), torch.FloatTensor(h_next)

# --- 2. MODELS & LOSSES ---
class QuantileMLP(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(4, 32), nn.ReLU(),
            nn.Linear(32, 32), nn.ReLU(),
            nn.Linear(32, 3) # P10, P50, P90
        )
    def forward(self, x):
        return self.net(x)

def pinball_loss(pred, target, quantiles=[0.1, 0.5, 0.9]):
    loss = 0
    for i, q in enumerate(quantiles):
        errors = target - pred[:, i]
        loss += torch.mean(torch.max((q - 1) * errors, q * errors))
    # Basic non-crossing constraint
    loss += torch.mean(torch.relu(pred[:, 0] - pred[:, 1]))
    loss += torch.mean(torch.relu(pred[:, 1] - pred[:, 2]))
    return loss

def physics_loss(pred, target, h_current):
    # Base statistical loss
    base_loss = pinball_loss(pred, target)
    
    p50 = pred[:, 1]
    
    # 1. Non-negative constraint
    loss_neg = torch.mean(torch.relu(-p50))
    # 2. Max Capacity (100.0) constraint
    loss_cap = torch.mean(torch.relu(p50 - 100.0))
    # 3. Rate of change constraint (Max 15.0)
    loss_roc = torch.mean(torch.relu(torch.abs(p50 - h_current) - 15.0))
    
    return base_loss + 10.0 * loss_neg + 10.0 * loss_cap + 10.0 * loss_roc

# --- 3. EVALUATION ---
def check_violations(p50, h_current):
    neg_viol = np.sum(p50 < -0.1)
    cap_viol = np.sum(p50 > 100.1)
    roc_viol = np.sum(np.abs(p50 - h_current) > 15.1)
    return (neg_viol + cap_viol + roc_viol) / len(p50)

def compute_metrics(y_true, preds, h_current):
    p10, p50, p90 = preds[:,0], preds[:,1], preds[:,2]
    mae = mean_absolute_error(y_true, p50)
    rmse = np.sqrt(mean_squared_error(y_true, p50))
    
    coverage = np.mean((y_true >= p10) & (y_true <= p90))
    width = np.mean(p90 - p10)
    
    # Simple POD/FAR (Hazard = > 90.0)
    y_haz = (y_true > 90.0).astype(int)
    p_haz = (p50 > 90.0).astype(int)
    eps = 1e-9
    tn, fp, fn, tp = confusion_matrix(y_haz, p_haz, labels=[0, 1]).ravel()
    pod = tp / (tp + fn + eps)
    far = fp / (tp + fp + eps)
    
    violation_rate = check_violations(p50, h_current)
    return mae, rmse, coverage, width, pod, far, violation_rate

def main():
    logger.info("Starting Constraint-Aware ML Ablations...")
    set_global_seed(42)
    
    X_train, y_train = generate_synthetic_physics_data(5000, ood=False)
    X_test, y_test = generate_synthetic_physics_data(1000, ood=False)
    X_ood, y_ood = generate_synthetic_physics_data(1000, ood=True)
    
    # Train Unconstrained (a, b)
    model_uc = QuantileMLP()
    opt_uc = optim.Adam(model_uc.parameters(), lr=0.01)
    for _ in range(300):
        opt_uc.zero_grad()
        loss = pinball_loss(model_uc(X_train), y_train)
        loss.backward(); opt_uc.step()
        
    # Train Physics-Informed (c)
    model_pi = QuantileMLP()
    opt_pi = optim.Adam(model_pi.parameters(), lr=0.01)
    for _ in range(300):
        opt_pi.zero_grad()
        loss = physics_loss(model_pi(X_train), y_train, X_train[:, 0])
        loss.backward(); opt_pi.step()
        
    model_uc.eval(); model_pi.eval()
    
    def evaluate_variant(variant, X, y):
        with torch.no_grad():
            preds_uc = model_uc(X).numpy()
            preds_pi = model_pi(X).numpy()
            h_curr = X[:, 0].numpy()
            y_np = y.numpy()
            
            if variant == "Unconstrained":
                return compute_metrics(y_np, preds_uc, h_curr)
            elif variant == "Post-Hoc Clipped":
                # Apply rules explicitly
                preds_ph = preds_uc.copy()
                for i in range(len(preds_ph)):
                    p50 = preds_ph[i, 1]
                    # clip rate
                    if p50 - h_curr[i] > 15.0: p50 = h_curr[i] + 15.0
                    elif p50 - h_curr[i] < -15.0: p50 = h_curr[i] - 15.0
                    # clip min/max
                    p50 = max(0.0, min(100.0, p50))
                    preds_ph[i, 1] = p50
                return compute_metrics(y_np, preds_ph, h_curr)
            else: # Physics-Informed
                return compute_metrics(y_np, preds_pi, h_curr)

    results = []
    for var in ["Unconstrained", "Post-Hoc Clipped", "Physics-Informed"]:
        mae, rmse, cov, wid, pod, far, viol = evaluate_variant(var, X_test, y_test)
        mae_ood, rmse_ood, cov_ood, wid_ood, pod_ood, far_ood, viol_ood = evaluate_variant(var, X_ood, y_ood)
        
        results.append({
            "Variant": var,
            "Violation_Rate": f"{viol*100:.1f}%",
            "MAE_Test": round(mae, 2), "RMSE_Test": round(rmse, 2),
            "POD": round(pod, 2), "FAR": round(far, 2),
            "Coverage_Test": f"{cov*100:.1f}%",
            "OOD_Violation_Rate": f"{viol_ood*100:.1f}%",
            "OOD_RMSE": round(rmse_ood, 2),
            "OOD_Coverage": f"{cov_ood*100:.1f}%",
            "Data_Status": "SYNTHETIC Topology"
        })
        
    df = pd.DataFrame(results)
    out_dir = r"C:\Users\gokul\Desktop\PROJECTS\climatetwin\results"
    df.to_csv(os.path.join(out_dir, "physics_constraints.csv"), index=False)
    
    logger.info("\n" + df.to_string(index=False))

if __name__ == "__main__":
    main()
