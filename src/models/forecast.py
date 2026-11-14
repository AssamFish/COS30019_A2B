"""Train, compare and forecast with the same chronological data split."""

from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch import nn

from src.data_processing.data_loader import TrafficDataLoader
from src.models.gru_model import GRUModel
from src.models.lstm_model import LSTMModel
from src.models.trainer import ModelTrainer


MODELS = ("lstm", "gru", "third")


class Forecast:
    def __init__(self, config, workbook, directory):
        self.config = config
        workbook = Path(workbook)
        self.loader = TrafficDataLoader(workbook.parent, directory)
        self.raw = self.loader.load_raw_data(workbook.name)
        self.frame = self.loader.preprocess(self.raw).asfreq("15min")
        self.directory = Path(directory)
        self.length = config["data"]["sequence_length"]
        self.train_ratio = config["data"]["train_ratio"]
        self.val_ratio = config["data"]["val_ratio"]
        self.train_end = int((len(self.frame) - self.length) * self.train_ratio) + self.length
        training = self.frame.iloc[:self.train_end]
        self.scale = training.mean().clip(lower=1).to_numpy()
        filled = self.frame.ffill().fillna(0).to_numpy()
        self.values = filled / self.scale
        self.split = self.loader.train_val_test_split(
            *self.loader.create_sequences(self.values, self.length),
            self.train_ratio, self.val_ratio
        )

    def model(self, name):
        size = self.frame.shape[1]
        if name == "third":
            # Feedforward MLP on the flattened lag window.
            return nn.Sequential(nn.Flatten(), nn.Linear(self.length * size, 64),
                                 nn.ReLU(), nn.Linear(64, size))
        factory = {"lstm": LSTMModel, "gru": GRUModel}[name]
        settings = self.config["model"][name]
        return factory(size, settings["hidden_size"], settings["num_layers"],
                       output_size=size, dropout=settings["dropout"])

    def checkpoint(self, name):
        return self.directory / f"{name}.pt"

    def train(self, name, epochs=None):
        torch.manual_seed(30019)
        trainer = ModelTrainer(self.model(name))
        settings = self.config["model"]["third_model" if name == "third" else name]
        trainer.train(*(self.split[key] for key in ("X_train", "y_train", "X_val", "y_val")),
                      epochs=epochs or settings["epochs"], batch_size=settings["batch_size"],
                      learning_rate=settings["learning_rate"])
        self.directory.mkdir(parents=True, exist_ok=True)
        trainer.save_model(self.checkpoint(name))

    def load(self, name):
        trainer = ModelTrainer(self.model(name))
        trainer.load_model(self.checkpoint(name))
        return trainer

    def evaluate(self, name, horizon=1):
        inputs = self.split["X_test"]
        actual = self.frame.iloc[-len(inputs):].to_numpy()
        model = None if name == "persistence" else self.load(name)
        if horizon == 1:
            predicted = self.rollout(model, inputs, 1)
        else:
            inputs = inputs[:1 - horizon]
            actual = np.lib.stride_tricks.sliding_window_view(actual, horizon, axis=0).sum(axis=-1)
            predicted = self.rollout(model, inputs, horizon)
        observed = np.isfinite(actual)
        actual, predicted = actual[observed], predicted[observed]
        error = predicted - actual
        nonzero = actual > 0
        return {
            "MAE": np.abs(error).mean(),
            "RMSE": np.sqrt(np.square(error).mean()),
            "MAPE (%)": 100 * np.abs(error[nonzero] / actual[nonzero]).mean(),
            "R2": 1 - np.square(error).sum() / np.square(actual - actual.mean()).sum(),
        }

    def rollout(self, model, windows, steps):
        total = np.zeros((len(windows), len(self.scale)))
        for _ in range(steps):
            step = windows[:, -1] if model is None else np.maximum(model.predict(windows), 0)
            total += step * self.scale
            windows = np.concatenate((windows[:, 1:], step[:, None, :]), axis=1)
        return total

    def hourly_flow(self, name, timestamp):
        timestamp = pd.Timestamp(timestamp)
        if timestamp not in self.frame.index:
            raise ValueError("Choose a timestamp on the October 2006 quarter-hour grid")
        index = self.frame.index.get_loc(timestamp)
        if index < self.length:
            raise ValueError(f"The forecast requires {self.length} preceding intervals")
        window = self.values[index - self.length:index]
        total = self.rollout(self.load(name), window[None, ...], 4)[0]
        return dict(zip(self.frame.columns, total))
