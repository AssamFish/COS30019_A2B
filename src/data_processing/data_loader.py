"""
data_loader.py - Load and preprocess the Boroondara SCATS traffic volume dataset.

This module handles:
- Reading raw .csv/.xlsx data files from VicRoads
- Parsing SCATS site numbers, locations, and 15-min interval traffic counts
- Cleaning missing/invalid data
- Storing processed data in structured format for ML training
"""

import pandas as pd
import numpy as np
from pathlib import Path


class TrafficDataLoader:
    """Load and preprocess VicRoads Boroondara traffic volume data."""

    def __init__(self, raw_data_path: str, processed_data_path: str):
        self.raw_data_path = Path(raw_data_path)
        self.processed_data_path = Path(processed_data_path)

    def load_raw_data(self, filename: str) -> pd.DataFrame:
        """Load raw dataset from file."""
        filepath = self.raw_data_path / filename
        if filepath.suffix == ".csv":
            return pd.read_csv(filepath)
        elif filepath.suffix in (".xlsx", ".xls"):
            return pd.read_excel(filepath)
        else:
            raise ValueError(f"Unsupported file format: {filepath.suffix}")

    def preprocess(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and preprocess the raw traffic data."""
        # TODO: Implement data cleaning
        # - Handle missing values
        # - Parse date/time columns
        # - Reshape 15-min interval columns into time series format
        # - Normalize/scale features
        raise NotImplementedError("Implement data preprocessing")

    def create_sequences(self, data: np.ndarray, seq_length: int) -> tuple:
        """Create input sequences and targets for time series prediction.

        Args:
            data: Normalized traffic flow data array
            seq_length: Number of time steps per input sequence

        Returns:
            Tuple of (X, y) where X has shape (n_samples, seq_length, n_features)
            and y has shape (n_samples, 1)
        """
        X, y = [], []
        for i in range(len(data) - seq_length):
            X.append(data[i : i + seq_length])
            y.append(data[i + seq_length])
        return np.array(X), np.array(y)

    def train_val_test_split(
        self, X: np.ndarray, y: np.ndarray, train_ratio=0.8, val_ratio=0.1
    ) -> dict:
        """Split data into train/validation/test sets (time-series aware, no shuffle)."""
        n = len(X)
        train_end = int(n * train_ratio)
        val_end = int(n * (train_ratio + val_ratio))

        return {
            "X_train": X[:train_end],
            "y_train": y[:train_end],
            "X_val": X[train_end:val_end],
            "y_val": y[train_end:val_end],
            "X_test": X[val_end:],
            "y_test": y[val_end:],
        }
