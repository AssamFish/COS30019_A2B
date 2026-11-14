"""
gru_model.py - GRU model for traffic flow prediction.
"""

import torch
import torch.nn as nn


class GRUModel(nn.Module):
    """GRU-based model for traffic flow prediction."""

    def __init__(self, input_size: int, hidden_size: int, num_layers: int, output_size: int = 1, dropout: float = 0.2):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers

        self.gru = nn.GRU(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0,
        )
        self.fc = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        # x shape: (batch_size, seq_length, input_size)
        gru_out, _ = self.gru(x)
        # Take the output from the last time step
        out = self.fc(gru_out[:, -1, :])
        return out
