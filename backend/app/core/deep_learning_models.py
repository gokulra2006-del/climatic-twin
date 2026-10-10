import torch
import torch.nn as nn
import torch.nn.functional as F

class FloodLSTM(nn.Module):
    """
    Deep Learning LSTM architecture for temporal flood forecasting.
    Significantly increases specifications (specs/accuracy) over standard Random Forests
    by capturing sequential weather patterns and reservoir accumulation over time.
    """
    def __init__(self, input_dim=14, hidden_dim=64, num_layers=2, output_dim=1):
        super(FloodLSTM, self).__init__()
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        
        self.lstm = nn.LSTM(
            input_size=input_dim, 
            hidden_size=hidden_dim, 
            num_layers=num_layers, 
            batch_first=True,
            dropout=0.2
        )
        
        self.fc1 = nn.Linear(hidden_dim, 32)
        self.fc2 = nn.Linear(32, output_dim)
        
    def forward(self, x):
        # x shape: (batch_size, sequence_length, input_dim)
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_dim).to(x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_dim).to(x.device)
        
        # Forward propagate LSTM
        out, _ = self.lstm(x, (h0, c0))
        
        # Decode the hidden state of the last time step
        out = out[:, -1, :]
        
        out = F.relu(self.fc1(out))
        out = torch.sigmoid(self.fc2(out))  # Bound between 0 and 1 for flood probability
        return out

class HazardMLP(nn.Module):
    """
    Deep Learning MLP for tabular hazard classification.
    Can be used as a drop-in replacement for the core tabular Random Forests 
    when complex non-linear interactions exist between climate features.
    """
    def __init__(self, input_dim=14, hidden_sizes=[128, 64, 32], output_dim=1):
        super(HazardMLP, self).__init__()
        layers = []
        in_size = input_dim
        for h in hidden_sizes:
            layers.append(nn.Linear(in_size, h))
            layers.append(nn.BatchNorm1d(h))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(0.3))
            in_size = h
        
        layers.append(nn.Linear(in_size, output_dim))
        layers.append(nn.Sigmoid())
        
        self.network = nn.Sequential(*layers)
        
    def forward(self, x):
        # x shape: (batch_size, input_dim)
        return self.network(x)
