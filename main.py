"""
COS30019 Assignment 2B - Traffic-Based Route Guidance System (TBRGS)
Main entry point for the application.
"""

import argparse


def main():
    parser = argparse.ArgumentParser(
        description="Traffic-Based Route Guidance System (TBRGS) for Boroondara"
    )
    parser.add_argument(
        "--mode",
        choices=["gui", "train", "evaluate", "route"],
        default="gui",
        help="Run mode: gui (default), train, evaluate, or route",
    )
    parser.add_argument("--config", type=str, default="configs/default.yaml", help="Path to config file")
    parser.add_argument("--model", type=str, choices=["lstm", "gru", "third"], help="Model to train/evaluate")
    parser.add_argument("--origin", type=int, help="Origin SCATS site number (e.g., 2000)")
    parser.add_argument("--destination", type=int, help="Destination SCATS site number (e.g., 3002)")
    parser.add_argument("--top-k", type=int, default=5, help="Number of routes to return (default: 5)")

    args = parser.parse_args()

    if args.mode == "gui":
        # Launch GUI
        print("Launching TBRGS GUI...")
        # from src.gui.app import TBRGSApp
        # app = TBRGSApp(config_path=args.config)
        # app.run()
    elif args.mode == "train":
        print(f"Training {args.model} model...")
        # TODO: implement training pipeline
    elif args.mode == "evaluate":
        print("Evaluating models...")
        # TODO: implement evaluation pipeline
    elif args.mode == "route":
        if args.origin and args.destination:
            print(f"Finding top-{args.top_k} routes from {args.origin} to {args.destination}...")
            # TODO: implement route finding
        else:
            print("Error: --origin and --destination are required for route mode")


if __name__ == "__main__":
    main()
