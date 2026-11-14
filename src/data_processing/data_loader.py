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
            if filepath.suffix == ".xls":
                return pd.read_excel(filepath, sheet_name="Data", header=1)
            return pd.read_excel(filepath)
        else:
            raise ValueError(f"Unsupported file format: {filepath.suffix}")

    def preprocess(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and preprocess the raw traffic data."""
        intervals = [f"V{i:02}" for i in range(96)]
        keys = ["SCATS Number", "Location", "Date"]
        frame = df[keys + intervals].copy()
        frame["Location"] = frame["Location"].str.strip().str.upper()
        frame["Date"] = pd.to_datetime(frame["Date"]).dt.normalize()
        frame[intervals] = frame[intervals].apply(pd.to_numeric, errors="coerce")
        frame[intervals] = frame[intervals].where(frame[intervals] >= 0)
        # Some site/date labels repeat for movements with distinct volume records.
        frame = frame.dropna(subset=keys).drop_duplicates()
        long = frame.melt(keys, intervals, "interval", "volume")
        long["timestamp"] = long["Date"] + pd.to_timedelta(
            long["interval"].str[1:].astype(int) * 15, unit="min"
        )
        return long.groupby(["timestamp", "SCATS Number"])["volume"].sum(min_count=1).unstack()

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
