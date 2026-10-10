import os
import torch
import torch.optim as optim
import numpy as np
import pandas as pd
from backend.app.core.gnn_lstm_forecaster import DynamicGNNLSTM, quantile_loss_with_non_crossing
from backend.app.core.reproducibility import set_global_seed, get_logger

logger = get_logger("GNN_LSTM_Ablations")

def build_synthetic_chennai_graphs(B, T, N=5):
    """
    Builds synthetic typed dynamic graphs for Chennai prototyping.
    Relations: 0=Drainage (directed), 1=Power (tree), 2=Road (grid), 3=Water.
    Includes dynamic masking to simulate missing/broken infrastructure edges.
    """
    relations = 4
    adj_seq = []
    for k in range(relations):
        base_adj = torch.rand(N, N) > 0.6  # Random sparse graph
        if k == 0:  # Drainage is strictly directed (lower triangular mock)
            base_adj = torch.tril(base_adj, diagonal=-1)
        base_adj = base_adj.float()
        
        # Expand over Batch and Time
        adj_t = base_adj.unsqueeze(0).unsqueeze(0).repeat(B, T, 1, 1)
        
        # Introduce dynamic edge drops (e.g., roads flooded, pumps failed)
        edge_drops = (torch.rand(B, T, N, N) > 0.05).float()
        adj_t = adj_t * edge_drops
        adj_seq.append(adj_t)
        
    return adj_seq

def generate_data(B=32, T=10, N=5, F=4):
    """
    Synthetic multi-variate sequences.
    Simulates Assimilation by generating 'clean' data vs 'noisy' (no assimilation) data.
    """
    x_clean = torch.randn(B, T, N, F)
    x_noisy = x_clean + torch.randn(B, T, N, F) * 2.0  # High variance if no EnKF
    
    # Target is some spatial-temporal diffusion of x
    target = x_clean.sum(dim=-1, keepdim=True) * 0.5 + torch.randn(B, T, N, 1) * 0.1
    return x_clean, x_noisy, target

def run_ablation(model_name, model_kwargs, x_data, adj_seq, target, epochs=10):
    model = DynamicGNNLSTM(in_dim=4, hidden_dim=16, num_relations=4, **model_kwargs)
    optimizer = optim.Adam(model.parameters(), lr=0.01)
    
    model.train()
    for e in range(epochs):
        optimizer.zero_grad()
        preds = model(x_data, adj_seq)
        loss = quantile_loss_with_non_crossing(preds, target)
        loss.backward()
        optimizer.step()
        
    # Evaluate Non-Crossing Constraint (P10 <= P50 <= P90)
    model.eval()
    with torch.no_grad():
        preds = model(x_data, adj_seq)
        # Check crossings
        cross_10_50 = (preds[:, :, :, 0] > preds[:, :, :, 1]).sum().item()
        cross_50_90 = (preds[:, :, :, 1] > preds[:, :, :, 2]).sum().item()
        final_loss = quantile_loss_with_non_crossing(preds, target).item()
        
        # RMSE of P50 against target
        rmse = torch.sqrt(torch.mean((preds[:, :, :, 1] - target.squeeze(-1))**2)).item()
        
    return {
        "Ablation": model_name,
        "Quantile Loss": final_loss,
        "P50 RMSE": rmse,
        "Constraint Violations": cross_10_50 + cross_50_90
    }

def main():
    logger.info("Starting GNN-LSTM Forecaster Ablations...")
    set_global_seed(42)
    
    B, T, N, F = 100, 10, 5, 4
    x_assimilated, x_no_assim, target = generate_data(B, T, N, F)
    adj_seq = build_synthetic_chennai_graphs(B, T, N)
    
    experiments = [
        {"name": "1. LSTM Only (No Spatial)", "kwargs": {"use_gnn": False, "use_lstm": True, "merged_graph": False}, "data": x_assimilated},
        {"name": "2. GNN Only (No Temporal)", "kwargs": {"use_gnn": True, "use_lstm": False, "merged_graph": False}, "data": x_assimilated},
        {"name": "3. Single Merged Graph", "kwargs": {"use_gnn": True, "use_lstm": True, "merged_graph": True}, "data": x_assimilated},
        {"name": "4. GNN-LSTM (No Assimilation)", "kwargs": {"use_gnn": True, "use_lstm": True, "merged_graph": False}, "data": x_no_assim},
        {"name": "5. FULL MODEL (Typed + Assimilated)", "kwargs": {"use_gnn": True, "use_lstm": True, "merged_graph": False}, "data": x_assimilated},
    ]
    
    results = []
    for exp in experiments:
        logger.info(f"Running {exp['name']}...")
        res = run_ablation(exp["name"], exp["kwargs"], exp["data"], adj_seq, target, epochs=30)
        results.append(res)
        
    df = pd.DataFrame(results)
    logger.info("\n" + df.to_string(index=False))
    
    out_dir = r"C:\Users\gokul\Desktop\PROJECTS\climatetwin\docs"
    os.makedirs(out_dir, exist_ok=True)
    df.to_csv(os.path.join(out_dir, "gnn_lstm_ablations.csv"), index=False)
    with open(os.path.join(out_dir, "gnn_lstm_ablations.tex"), "w") as f:
        f.write(df.to_latex(index=False, caption="GNN-LSTM Multi-Relational Ablations with Quantile Constraints"))

if __name__ == "__main__":
    main()
