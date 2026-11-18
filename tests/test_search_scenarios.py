"""Run fifteen deterministic A2B routing scenarios against all six A2A methods.

python -m tests.test_search_scenarios writes a 90-run CSV for inspection.
"""
import csv
import json
from pathlib import Path
import unittest

from src.routing.graph import SEARCH_ALGORITHMS
from src.routing.scenarios import make_network, reference_paths, check_scenario

SCENARIOS = Path(__file__).parent / "scenarios"


class SearchScenarioTests(unittest.TestCase):
    def test_fifteen_scenarios_across_six_algorithms(self):
        files = sorted(SCENARIOS.glob("*.json"))
        self.assertEqual(len(files), 15)
        for file in files:
            case = json.loads(file.read_text())
            for algorithm in SEARCH_ALGORITHMS:
                with self.subTest(scenario=case["name"], algorithm=algorithm):
                    check_scenario(case, algorithm)


if __name__ == "__main__":
    rows = []
    for file in sorted(SCENARIOS.glob("*.json")):
        case = json.loads(file.read_text())
        for algorithm in SEARCH_ALGORITHMS:
            rows.append(check_scenario(case, algorithm))
    output = Path(__file__).resolve().parents[1] / "reports/search_scenario_results.csv"
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"PASS: 15 scenarios x 6 algorithms = {len(rows)} runs. Results in {output}")
