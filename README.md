# COS30019 Assignment 2B — Traffic-Based Route Guidance System (TBRGS)

## Overview

This project implements a **Traffic-Based Route Guidance System (TBRGS)** for the City of Boroondara, Melbourne. It uses machine learning models to predict traffic flow and integrates with graph-based search algorithms (from Assignment 2A) to find optimal routes between intersections.

## Features

- **Data Processing**: Extract and preprocess traffic volume data from the VicRoads Boroondara dataset (SCATS site data, 15-min intervals)
- **ML Models for Traffic Prediction**:
  - LSTM (Long Short-Term Memory)
  - GRU (Gated Recurrent Unit)
  - A lag-window multilayer perceptron (MLP)
- **Model Evaluation**: Comprehensive comparison of ML models (MAE, RMSE, MAPE, R²)
- **Travel Time Estimation**: Convert predicted traffic flow to travel time using the provided formula
- **Route Guidance**: Find top-K (up to 5) optimal routes between any two SCATS sites
- **GUI**: User interface for origin/destination input, parameter settings, and visualisation

## Project Structure

```
A2B/
├── src/
│   ├── data_processing/    # Data loading, cleaning, feature engineering
│   ├── models/             # LSTM, GRU, and third ML model implementations
│   ├── routing/            # Graph search, travel time estimation, A2A integration
│   ├── gui/                # GUI application
│   └── utils/              # Helper functions, metrics, plotting
├── data/
│   ├── raw/                # Original Boroondara dataset
│   └── processed/          # Preprocessed/split data
├── configs/                # Default configuration files
├── tests/                  # Test cases (minimum 15)
├── notebooks/              # Jupyter notebooks for exploration & analysis
├── reports/                # Assignment report
├── requirements.txt
└── main.py                 # Entry point
```

## Run from the project folder

Install dependencies once, then set the path to the supplied workbook in your VS Code
PowerShell terminal. Adjust the path if your files are arranged differently.

```powershell
python -m pip install -r requirements.txt
$workbook = "../Intro to Ai assignemtn 2B/Scats Data October 2006.xls"
python main.py --mode train --epochs 20 --workbook $workbook
python main.py --mode evaluate --workbook $workbook
python main.py --mode route --origin 2000 --destination 3002 --workbook $workbook
python main.py --workbook $workbook
python -m unittest discover -v
```

Supply the same workbook and configuration for training, evaluation, and routing.
Checkpoints are stored locally under `artifacts/`. The GUI accepts a date and time
on the October 2006 quarter-hour grid, with three hours of prior data required.

## How the pipeline works

1. Read the workbook Data sheet and convert `V00` through `V95` into quarter-hour
   counts. Remove exact duplicate count records and sum movement counts by site.
2. Form 12-interval windows and split targets chronologically into train,
   validation, and test. Normalization uses training means. Missing inputs are
   forward-filled and missing held-out targets are omitted from the scores.
3. Train the LSTM, GRU, and lag-window MLP (`third`) with the same windows. The MLP
   is the proposed third technique and requires tutor approval. Compare against
   persistence at 15 minutes and on the sum of four recursive forecasts.
4. Infer a graph by linking consecutive sites with shared road names. Treat
   Maroondah Highway and Whitehorse Road as one corridor. Include approximate
   western connections 4262?4812 and 3001?4821 to join the workbook coverage.
   Links are bidirectional, with straight-line distances. Verify these
   approximations before interpreting results as actual road itineraries.
5. Weight links using the destination's predicted hourly count as specified
   in the brief. Use the conversion handout's higher-speed root capped at
   60 km/h and apply a 30-second delay per link. Flows above capacity use
   the turning-point speed. Reused A2A uniform-cost search yields up to five
   loopless routes in travel-time order. Each query uses a fixed hourly snapshot.

## Team

| Name | Student ID | Contribution |
|------|-----------|-------------|
|      |           |             |
|      |           |             |
|      |           |             |
|      |           |             |

## License

This project is for academic purposes only (Swinburne University of Technology).
