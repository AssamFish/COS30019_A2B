"""
trainer.py - Training and evaluation pipeline for ML models.
"""

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
import numpy as np
from pathlib import Path


class ModelTrainer:
    """Handles training, validation, and evaluation of traffic prediction models."""

    def __init__(self, model: nn.Module, device: str = "cpu"):
        self.model = model.to(device)
        self.device = device
        self.train_losses = []
        self.val_losses = []

    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
        epochs: int = 100,
        batch_size: int = 32,
        learning_rate: float = 0.001,
    ) -> dict:
        """Train the model and return training history."""
        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=learning_rate)

        train_dataset = TensorDataset(
            torch.FloatTensor(X_train), torch.FloatTensor(y_train)
        )
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)

        for epoch in range(epochs):
            self.model.train()
            epoch_loss = 0.0
            for X_batch, y_batch in train_loader:
                X_batch, y_batch = X_batch.to(self.device), y_batch.to(self.device)
                optimizer.zero_grad()
                predictions = self.model(X_batch)
                loss = criterion(predictions, y_batch)
                loss.backward()
                optimizer.step()
                epoch_loss += loss.item()

            avg_train_loss = epoch_loss / len(train_loader)
            self.train_losses.append(avg_train_loss)

            # Validation
            val_loss = self.evaluate_loss(X_val, y_val, criterion)
            self.val_losses.append(val_loss)

            if (epoch + 1) % 10 == 0:
                print(f"Epoch [{epoch+1}/{epochs}] Train Loss: {avg_train_loss:.6f} | Val Loss: {val_loss:.6f}")

        return {"train_losses": self.train_losses, "val_losses": self.val_losses}

    def evaluate_loss(self, X: np.ndarray, y: np.ndarray, criterion) -> float:
        """Compute loss on a dataset."""
        self.model.eval()
        with torch.no_grad():
            X_tensor = torch.FloatTensor(X).to(self.device)
            y_tensor = torch.FloatTensor(y).to(self.device)
            predictions = self.model(X_tensor)
            loss = criterion(predictions, y_tensor)
        return loss.item()

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Generate predictions."""
        self.model.eval()
        with torch.no_grad():
            X_tensor = torch.FloatTensor(X).to(self.device)
            predictions = self.model(X_tensor)
        return predictions.cpu().numpy()

    def save_model(self, path: str):
        """Save model checkpoint."""
        torch.save(self.model.state_dict(), path)

    def load_model(self, path: str):
        """Load model checkpoint."""
        self.model.load_state_dict(torch.load(path, map_location=self.device))
