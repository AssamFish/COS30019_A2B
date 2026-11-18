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
4. Load the prepared road network from `data/roads/network.json`. Intersection
   road names are matched to OpenStreetMap nodes to correct the workbook's
   coordinate offset. Each directed link has an OSRM-verified driving distance
   and full road geometry. Links that bypass another modeled SCATS intersection
   are split so that site's traffic can contribute to travel time.
5. Weight links with predicted destination-site hourly counts, the supplied
   quadratic conversion, a 60 km/h cap and a 30-second intersection delay.
   A2A uniform-cost search finds alternatives in this modeled network.
6. Validate each complete candidate with OSRM's driving profile and
   `continue_straight=true` to account for permitted turns across link boundaries.
   Recalculate estimates from the returned road-leg distances and sort the
   validated candidates. The GUI draws this full driving geometry. First-time
   route validation requires internet. Successful validations are cached locally
   under `artifacts/driving-routes.json`; unavailable validation reports an error.

## Road data and interpretation

The network contains 40 sites and 104 directed road links. Candidate corridors
come from the supplied road labels, with the western connections independently
checked by the driving service. Alternatives are limited to this modeled
SCATS network. The current road snapshot is combined with October 2006 traffic
counts, so the estimates describe an assignment simulation. Live incidents,
current congestion and temporary closures are outside this model.

OpenStreetMap contributors supply the streets and intersection coordinates
under the ODbL. See https://www.openstreetmap.org/copyright.
OSRM supplies driving geometry and road distances through
https://router.project-osrm.org. API documentation is at
https://project-osrm.org/docs/v5.24.0/api/.
No OSRM travel durations are substituted for the assignment's predicted costs.

To rebuild road data, `tools/download_roads.py WORKBOOK` downloads snapshots around
the SCATS sites. `tools/build_road_network.py WORKBOOK` matches intersections
and verifies candidate links. These preparation steps require internet and
respect sequential request spacing. Normal launches use the prepared
`network.json`. Raw OSM snapshots are excluded from Git.

The existing PDF report draft describes the earlier schematic network and
must be revised to reflect this implementation before submission.

## Team

| Name | Student ID | Contribution |
|------|-----------|-------------|
|      |           |             |
|      |           |             |
|      |           |             |
|      |           |             |

## License

This project is for academic purposes only (Swinburne University of Technology).


## Kuching demonstration

Click **Kuching demo** above the Boroondara map to open an additional driving
planner for Swinburne Sarawak, Kuching Waterfront and Vivacity Megamall.
The demonstration uses OpenStreetMap landmark coordinates and OSRM driving
alternatives with baseline road-speed estimates. It requires internet.
The Boroondara-trained traffic models apply to the Boroondara assignment area.
Kuching traffic forecasting would require a local training and evaluation dataset.

## Six A2A search algorithms

Choose the search algorithm independently of the traffic prediction model in the
GUI. The command line accepts `--algorithm DFS`, `BFS`, `GBFS`, `AS`, `CUS1`
or `CUS2`. The default is CUS1.

| Algorithm | Search objective |
|---|---|
| DFS | Follow a branch deeply before trying the next branch |
| BFS | Fewest road links using a FIFO queue |
| GBFS | Lowest estimated remaining travel cost |
| AS (A*) | Accumulated travel time plus an admissible heuristic |
| CUS1 | Lowest accumulated travel time using uniform-cost search |
| CUS2 | Fewest links using a hop-based admissible heuristic |

All six reuse their A2A implementations. Their `routes()` generators extend
single-result `search()` compatibility to multiple alternatives. Coordinates are
provided to the original scaled Euclidean heuristic. The scale is bounded by
the modeled edge costs, maintaining admissibility for A*.

DFS, BFS, GBFS and CUS2 can return slower driving routes than A* or CUS1.
The GUI orders the returned candidates by validated estimated time and labels
the first as the best returned option. Whole-trip driving validation can alter
leg distances and costs, so this represents the best validated candidate among
those returned by the chosen search.

Run `python -m tests.test_search_scenarios` for 15 synthetic cases across all six
algorithms and a CSV of 90 results. See [the testing notes](reports/search_testing.md)
for case purposes, expected behavior and real-workbook integration results.


## Choose real test routes in the main planner

The **Test route (15 real trips)** dropdown sits directly below **Search algorithm**.
Select a preset to fill the origin, destination, date, time and requested route
count, then click **Find routes**. Keep the preset selected while changing search
algorithms or prediction models to compare their results. Editing trip fields
changes the selector to **Custom trip**.

The 15 presets use the actual Boroondara network and historical traffic pipeline.
They include a longest modeled trip, central alternatives, short and reverse
journeys, different corridors, time-of-day comparisons, a weekend departure,
the assignment example and a zero-length journey. The longest modeled trip is
the origin/destination pair with the largest shortest-road distance in the
prepared 40-site network. It does not ask the program to maximize trip duration.

Preset settings are stored in `data/roads/test-routes.json`.
Recorded full-pipeline results are in `reports/real_route_test_results.csv`.
The synthetic scenarios remain automated regression fixtures.
