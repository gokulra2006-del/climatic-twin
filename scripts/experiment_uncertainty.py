import os
import torch
import torch.nn as nn
import numpy as np
import pandas as pd
from backend.app.core.uncertainty_eval import UncertaintyEvaluator, UncertaintyRecalibrator, EpistemicTracker
from backend.app.core.reproducibility import set_global_seed, get_logger

logger = get_logger("Uncertainty_Experiment")

# --- Simple network with Dropout to demonstrate Epistemic MC Dropout ---
class MCDropoutForecaster(nn.Module):
    def __init__(self, in_dim=4, hidden=16):
        super().__init__()
        self.fc1 = nn.Linear(in_dim, hidden)
        self.drop = nn.Dropout(p=0.3)
        self.fc2 = nn.Linear(hidden, 3) # Predicts P10, P50, P90
        
    def forward(self, x):
        h = torch.relu(self.fc1(x))
        h = self.drop(h)
        return self.fc2(h)

def pinball_loss(preds, target, quantiles=[0.1, 0.5, 0.9]):
    loss = 0.0
    for i, q in enumerate(quantiles):
        err = target.squeeze(-1) - preds[:, i]
        loss += torch.mean(torch.max(q * err, (q - 1) * err))
    return loss

def main():
    set_global_seed(42)
    logger.info("Starting Uncertainty Evaluation & Decomposition Suite...")

    # 1. Synthesize Data
    N_train, N_val, N_test = 2000, 500, 500
    X_train = torch.randn(N_train, 4)
    y_train = (X_train[:, 0] * 2.0 + torch.sin(X_train[:, 1]) + torch.randn(N_train)*0.5).unsqueeze(-1)
    
    X_val = torch.randn(N_val, 4)
    y_val = (X_val[:, 0] * 2.0 + torch.sin(X_val[:, 1]) + torch.randn(N_val)*0.5).unsqueeze(-1)
    
    X_test = torch.randn(N_test, 4)
    # Add extreme events in test
    X_test[400:, 0] += 5.0
    y_test = (X_test[:, 0] * 2.0 + torch.sin(X_test[:, 1]) + torch.randn(N_test)*1.5).unsqueeze(-1)

    # 2. Train Base Model
    model = MCDropoutForecaster()
    opt = torch.optim.Adam(model.parameters(), lr=0.01)
    for _ in range(200):
        opt.zero_grad()
        loss = pinball_loss(model(X_train), y_train)
        loss.backward()
        opt.step()
        
    # 3. Post-Hoc Recalibration (Split-Conformal) on Val
    model.eval()
    with torch.no_grad():
        val_preds = model(X_val).numpy()
        val_y = y_val.numpy().flatten()
        val_p10, val_p50, val_p90 = val_preds[:,0], val_preds[:,1], val_preds[:,2]
        
    recal = UncertaintyRecalibrator()
    recal.fit_conformal(val_p10, val_p90, val_y, alpha=0.2)
    recal.fit_isotonic(val_p50, val_y)
    
    # 4. Test Evaluation & Uncertainty Decomposition
    # Scenario uncertainty: Assume 2 scenarios (Normal vs High Rain)
    X_test_scenario2 = X_test.clone()
    X_test_scenario2[:, 0] += 2.0 
    
    model.eval()
    with torch.no_grad():
        test_y = y_test.numpy().flatten()
        
        # Base deterministic pass (Aleatoric estimated by P90 - P10)
        base_preds = model(X_test).numpy()
        base_p10, base_p50, base_p90 = base_preds[:,0], base_preds[:,1], base_preds[:,2]
        
        # Epistemic pass (MC Dropout)
        mc_mean, mc_std = EpistemicTracker.mc_dropout_predict(model, X_test, num_samples=50)
        mc_mean = mc_mean.numpy()
        epistemic_std = mc_std[:, 1].numpy() # Std dev of P50 across dropout passes
        
        # Scenario pass
        scen_preds = model(X_test_scenario2).numpy()
        scen_p50 = scen_preds[:, 1]
        scenario_std = np.std([base_p50, scen_p50], axis=0)
        
    aleatoric_std = (base_p90 - base_p10) / 2.56 # Approx converting 80% CI to std
    observation_std = np.ones_like(aleatoric_std) * 0.1 # Fixed sensor noise floor
    
    # 5. Extreme Event Mask
    # Define extremes as true values > 95th percentile
    extreme_thresh = np.percentile(test_y, 95)
    ext_mask = test_y > extreme_thresh
    
    # 6. Apply Recalibration
    calib_p10, calib_p90 = recal.predict_conformal(base_p10, base_p90)
    iso_p50 = recal.predict_isotonic(base_p50)
    
    # 7. Compute Metrics
    metrics = []
    for name, mask, p10, p50, p90 in [
        ("Base (All)", np.ones_like(test_y, dtype=bool), base_p10, base_p50, base_p90),
        ("Recalibrated (All)", np.ones_like(test_y, dtype=bool), calib_p10, iso_p50, calib_p90),
        ("Base (Extremes)", ext_mask, base_p10, base_p50, base_p90),
        ("Recalibrated (Extremes)", ext_mask, calib_p10, iso_p50, calib_p90),
    ]:
        cov, sharp = UncertaintyEvaluator.coverage_and_sharpness(test_y[mask], p10[mask], p90[mask])
        wis = UncertaintyEvaluator.weighted_interval_score(test_y[mask], p10[mask], p50[mask], p90[mask])
        crps = UncertaintyEvaluator.crps_gaussian_approx(test_y[mask], p50[mask], (p90[mask]-p10[mask])/2.56)
        
        metrics.append({
            "Evaluation_Subset": name,
            "Coverage_P10_P90": cov,
            "Sharpness_Width": sharp,
            "WIS": wis,
            "CRPS": crps
        })
        
    df_metrics = pd.DataFrame(metrics)
    
    decomp_df = pd.DataFrame({
        "Observation_Uncertainty_Std": observation_std.mean(),
        "Aleatoric_Uncertainty_Std": aleatoric_std.mean(),
        "Epistemic_Uncertainty_Std": epistemic_std.mean(),
        "Scenario_Uncertainty_Std": scenario_std.mean()
    }, index=[0])

    logger.info("\n=== UNCERTAINTY METRICS ===")
    logger.info("\n" + df_metrics.to_string(index=False))
    
    logger.info("\n=== UNCERTAINTY DECOMPOSITION ===")
    logger.info("\n" + decomp_df.to_string(index=False))
    
    # Output to docs
    out_dir = r"C:\Users\gokul\Desktop\PROJECTS\climatetwin\docs"
    df_metrics.to_csv(os.path.join(out_dir, "uncertainty_metrics.csv"), index=False)
    decomp_df.to_csv(os.path.join(out_dir, "uncertainty_decomposition.csv"), index=False)
    
if __name__ == "__main__":
    main()
