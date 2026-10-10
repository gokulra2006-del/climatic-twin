import torch
import torch.nn as nn
import numpy as np
import logging

logger = logging.getLogger(__name__)

def quantile_loss_with_non_crossing(preds, target, quantiles=[0.1, 0.5, 0.9], penalty_weight=10.0):
    """
    Computes pinball/quantile loss for P10, P50, P90 and applies a strictly 
    positive ReLU penalty if the non-crossing constraint (P10 <= P50 <= P90) is violated.
    preds: (Batch, Nodes, 3)
    target: (Batch, Nodes, 1)
    """
    loss = 0.0
    # Pinball loss
    for i, q in enumerate(quantiles):
        err = target.squeeze(-1) - preds[:, :, i]
        loss += torch.mean(torch.max(q * err, (q - 1) * err))
        
    # Non-crossing penalty
    penalty = torch.mean(torch.relu(preds[:, :, 0] - preds[:, :, 1])) + \
              torch.mean(torch.relu(preds[:, :, 1] - preds[:, :, 2]))
              
    return loss + penalty_weight * penalty

class MultiRelationalGCN(nn.Module):
    def __init__(self, in_dim, out_dim, num_relations):
        super().__init__()
        self.num_relations = num_relations
        # One weight matrix per edge type
        self.weights = nn.ParameterList([
            nn.Parameter(torch.randn(in_dim, out_dim) * 0.1) for _ in range(num_relations)
        ])
        
    def forward(self, x, adj_matrices):
        """
        x: (Batch, Nodes, in_dim)
        adj_matrices: List of length 
um_relations with tensors (Batch, Nodes, Nodes)
        """
        out = 0
        for k in range(self.num_relations):
            # Message passing: A * X * W
            msg = torch.bmm(adj_matrices[k], x)
            out = out + torch.matmul(msg, self.weights[k])
        return out

class DynamicGNNLSTM(nn.Module):
    def __init__(self, in_dim, hidden_dim, num_relations, use_lstm=True, use_gnn=True, merged_graph=False):
        """
        Ablation-aware architecture.
        use_lstm: If False, ignores temporal hidden state (GNN only).
        use_gnn: If False, overrides adjacency matrices with Identity (LSTM only).
        merged_graph: If True, squashes all relations into a single matrix.
        """
        super().__init__()
        self.hidden_dim = hidden_dim
        self.use_lstm = use_lstm
        self.use_gnn = use_gnn
        self.merged_graph = merged_graph
        self.eff_relations = 1 if merged_graph else num_relations
        
        # Spatial encoder
        self.gcn = MultiRelationalGCN(in_dim, hidden_dim, self.eff_relations)
        
        # Temporal encoder
        if self.use_lstm:
            self.lstm_cell = nn.LSTMCell(hidden_dim, hidden_dim)
            
        # Output Head predicting [P10, P50, P90]
        self.head = nn.Linear(hidden_dim, 3)
        
    def forward(self, x_seq, adj_seq):
        """
        x_seq: (Batch, Time, Nodes, Features)
        adj_seq: list of relation tensors, each (Batch, Time, Nodes, Nodes)
        """
        B, T, N, F = x_seq.shape
        
        if self.use_lstm:
            # Flatten B*N for LSTM cell processing
            h = torch.zeros(B * N, self.hidden_dim, device=x_seq.device)
            c = torch.zeros(B * N, self.hidden_dim, device=x_seq.device)
            
        outputs = []
        
        for t in range(T):
            x_t = x_seq[:, t, :, :] # (B, N, F)
            
            # Extract dynamic adjacency matrices for time t
            adj_t = [adj[:, t, :, :] for adj in adj_seq]
            
            # Ablation: LSTM only -> Identity matrices (no spatial messaging)
            if not self.use_gnn:
                adj_t = [torch.eye(N).unsqueeze(0).repeat(B, 1, 1).to(x_seq.device) for _ in adj_t]
                
            # Ablation: Merged graph -> Sum all relations into one
            if self.merged_graph:
                merged_adj = sum(adj_t)
                merged_adj = torch.clamp(merged_adj, 0, 1) # simple unweighted union
                adj_t = [merged_adj]
                
            # Spatial convolution
            gcn_out = self.gcn(x_t, adj_t) # (B, N, hidden)
            
            if self.use_lstm:
                gcn_out_flat = gcn_out.view(B * N, -1)
                h, c = self.lstm_cell(gcn_out_flat, (h, c))
                node_emb = h.view(B, N, -1)
            else:
                node_emb = torch.relu(gcn_out)
                
            # Predict P10, P50, P90
            out_t = self.head(node_emb)
            outputs.append(out_t.unsqueeze(1)) # (B, 1, N, 3)
            
        return torch.cat(outputs, dim=1) # (B, T, N, 3)
