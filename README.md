# COS30019 Assignment 2B — Traffic-Based Route Guidance System (TBRGS)

## Overview

This project implements a **Traffic-Based Route Guidance System (TBRGS)** for the City of Boroondara, Melbourne. It uses machine learning models to predict traffic flow and integrates with graph-based search algorithms (from Assignment 2A) to find optimal routes between intersections.

## Features

- **Data Processing**: Extract and preprocess traffic volume data from the VicRoads Boroondara dataset (SCATS site data, 15-min intervals)
- **ML Models for Traffic Prediction**:
  - LSTM (Long Short-Term Memory)
  - GRU (Gated Recurrent Unit)
  - A third model of choice (e.g., Transformer, CNN-LSTM, etc.)
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

## Setup

### Prerequisites

- Python 3.10+
- pip

### Installation

```bash
git clone https://github.com/<your-username>/COS30019-A2B.git
cd COS30019-A2B
pip install -r requirements.txt
```

### Running

```bash
python main.py
```

## Dataset

The system uses the VicRoads Boroondara traffic volume dataset containing SCATS site data with traffic flow counts (number of vehicles) recorded every 15 minutes.

## Assumptions

1. Speed limit on every link is **60 km/h**
2. Travel time from SCATS site A to B is approximated using accumulated volume per hour at site B and the distance between A and B
3. Average delay of **30 seconds** at each controlled intersection

## Team

| Name | Student ID | Contribution |
|------|-----------|-------------|
|      |           |             |
|      |           |             |
|      |           |             |
|      |           |             |

## License

This project is for academic purposes only (Swinburne University of Technology).
