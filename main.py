"""Traffic-based route guidance command line and GUI entry point."""

import argparse
from pathlib import Path

import torch
import yaml

from src.models.forecast import Forecast, MODELS
from src.routing.network import build_network
from src.routing.travel_time import flow_to_travel_time


def recommend(forecast, network, model, origin, destination, timestamp, top_k, algorithm="CUS1"):
    flow = forecast.hourly_flow(model, timestamp)
    settings = forecast.config["routing"]
    candidates = network.find_top_k_routes(
        origin, destination,
        lambda _, target, distance: flow_to_travel_time(
            flow[target], distance, settings["speed_limit_kmh"], settings["intersection_delay_sec"]
        ),
        top_k,
        algorithm,
    )
    validated = []
    for path, _ in candidates:
        road = network.driving_route(path)
        seconds = sum(
            flow_to_travel_time(flow[target], distance, settings["speed_limit_kmh"],
                                settings["intersection_delay_sec"])
            for target, distance in zip(path[1:], road["legs"])
        )
        network.route_geometry[tuple(path)] = road["geometry"]
        validated.append((path, seconds))
    return sorted(validated, key=lambda result: result[1])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("gui", "train", "evaluate", "route"), default="gui")
    parser.add_argument("--config", type=Path, default=Path("configs/default.yaml"))
    parser.add_argument("--workbook", type=Path)
    parser.add_argument("--model", choices=MODELS)
    parser.add_argument("--epochs", type=int)
    parser.add_argument("--origin", type=int)
    parser.add_argument("--destination", type=int)
    parser.add_argument("--time")
    parser.add_argument("--algorithm", choices=("DFS", "BFS", "GBFS", "AS", "CUS1", "CUS2"), default="CUS1")
    parser.add_argument("--top-k", type=int, choices=range(1, 6))
    args = parser.parse_args()
    if args.epochs is not None and args.epochs < 1:
        parser.error("--epochs must be positive")

    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    workbook = args.workbook or Path(config["data"]["raw_path"]) / "Scats Data October 2006.xls"
    if not workbook.is_file():
        parser.error("Supply the traffic workbook with --workbook")
    torch.set_num_threads(2)
    forecast = Forecast(config, workbook, Path(__file__).resolve().parent / "artifacts")
    models = (args.model,) if args.model else MODELS
    if args.mode == "train":
        for model in models:
            print(f"Training {model}", flush=True)
            forecast.train(model, args.epochs)
    elif args.mode == "evaluate":
        for model in ("persistence", *models):
            for horizon in (1, 4):
                metrics = forecast.evaluate(model, horizon)
                print(f"{model} {15 * horizon} min",
                      " ".join(f"{key}={value:.4f}" for key, value in metrics.items()))
    else:
        network = build_network(forecast.raw)
        model = args.model or "gru"
        top_k = args.top_k or config["routing"]["top_k"]
        timestamp = args.time or config["routing"]["departure"]
        if args.mode == "gui":
            from src.gui.app import run
            run(network, lambda *query: recommend(forecast, network, *query), model, timestamp, top_k, args.algorithm)
        else:
            if args.origin is None or args.destination is None:
                parser.error("--origin and --destination are required in route mode")
            results = recommend(forecast, network, model, args.origin, args.destination, timestamp, top_k, args.algorithm)
            for path, seconds in results:
                print(f"{' -> '.join(map(str, path))}  ({seconds / 60:.2f} min)")
            if not results:
                print("No connection in the estimated road network")


if __name__ == "__main__":
    main()
