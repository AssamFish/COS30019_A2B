"""Shared scenario loading, execution and independent reference checks."""

import json
from pathlib import Path
import time

from .graph import RoadNetwork

SCENARIOS = Path(__file__).resolve().parents[2] / "tests/scenarios"


def load_scenarios():
    return [json.loads(file.read_text(encoding="utf-8"))
            for file in sorted(SCENARIOS.glob("*.json"))]


def make_network(case):
    network = RoadNetwork()
    for site, (lon, lat) in case["coordinates"].items():
        network.add_site(int(site), f"Test site {site}", lat, lon)
    for first, second, seconds in case["edges"]:
        network.add_edge(first, second, seconds)
    return network


def reference_paths(case):
    """Exhaustive oracle for these deliberately bounded synthetic networks."""
    edges = {}
    for first, second, cost in case["edges"]:
        edges[first, second] = min(cost, edges.get((first, second), cost))
    pending = [([case["origin"]], 0)]
    completed = {}
    while pending:
        path, total = pending.pop()
        if path[-1] == case["destination"]:
            completed[tuple(path)] = total
            continue
        for (first, second), cost in edges.items():
            if first == path[-1] and second not in path:
                pending.append((path + [second], total + cost))
    return completed


def run_case(case, algorithm):
    network = make_network(case)
    expected = reference_paths(case)
    started = time.perf_counter()
    routes = network.find_top_k_routes(case["origin"], case["destination"],
                                      lambda _a, _b, seconds: seconds,
                                      case["k"], algorithm)
    elapsed = (time.perf_counter() - started) * 1000
    assert len(routes) == min(case["k"], len(expected)), "Incorrect alternative count"
    assert len({tuple(path) for path, _ in routes}) == len(routes), "Duplicate route"
    for path, cost in routes:
        assert tuple(path) in expected, "Invalid or cyclic route"
        assert abs(expected[tuple(path)] - cost) < 1e-8, "Incorrect path cost"
    if algorithm in ("AS", "CUS1"):
        assert [cost for _, cost in routes] == sorted(expected.values())[:case["k"]], "Cost order differs from oracle"
    if algorithm in ("BFS", "CUS2"):
        assert [len(path) for path, _ in routes] == sorted(map(len, expected))[:case["k"]], "Hop order differs from oracle"
    if algorithm == "DFS":
        assert [tuple(path) for path, _ in routes] == sorted(expected)[:case["k"]], "DFS discovery order changed"
    if case["name"] == "greedy_trap" and algorithm == "GBFS":
        assert routes[0][0] == [1, 2, 4], "Greedy search must follow the heuristic"
    row = {
        "scenario": case["name"], "algorithm": algorithm, "status": "PASS",
        "routes_returned": len(routes), "first_path": " > ".join(map(str, routes[0][0])) if routes else "",
        "first_cost_seconds": routes[0][1] if routes else "",
        "nodes_created": network.last_search["nodes_created"],
        "runtime_ms": round(elapsed, 3),
    }


    return routes, row


def check_scenario(case, algorithm):
    return run_case(case, algorithm)[1]
