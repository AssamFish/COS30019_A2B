"""Regression checks for road-based distances and geometry."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import requests

from src.routing.network import DrivingNetwork, NETWORK_FILE, build_network, distance_km


class DrivingRoadTests(unittest.TestCase):
    def test_prepared_links_follow_detailed_geometry(self):
        data = json.loads(NETWORK_FILE.read_text())
        for link in data["links"]:
            self.assertGreater(len(link["geometry"]), 2)
            geometry = link["geometry"]
            measured = sum(distance_km(a, b) for a, b in zip(geometry, geometry[1:]))
            self.assertAlmostEqual(measured, link["distance_km"], delta=max(.03, measured * .025))

    def test_all_prepared_sites_reachable_in_both_directions(self):
        data = json.loads(NETWORK_FILE.read_text())
        network = build_network(pd.DataFrame({"SCATS Number": [int(s) for s in data["sites"]]}))
        for origin in network.sites:
            seen = {origin}
            pending = [origin]
            for current in pending:
                for target, _ in network.get_neighbours(current):
                    if target not in seen:
                        seen.add(target)
                        pending.append(target)
            self.assertEqual(seen, set(network.sites), origin)

    def test_original_misplaced_destination_corrected(self):
        data = json.loads(NETWORK_FILE.read_text())
        site = data["sites"]["3127"]
        self.assertIn("BALWYN RD", site["matched_roads"])
        self.assertIn("CANTERBURY RD", site["matched_roads"])
        self.assertGreater(site["offset_m"], 100)

    def test_failed_validation_never_returns_straight_line(self):
        network = DrivingNetwork()
        network.route_cache = {}
        network.add_site(1, "", -37.8, 145)
        network.add_site(2, "", -37.9, 145.1)
        with patch("src.routing.network.requests.get", side_effect=requests.ConnectionError()):
            with self.assertRaisesRegex(ValueError, "validation is unavailable"):
                network.driving_route([1, 2])

    def test_whole_trip_validates_turns_and_uses_road_leg_distances(self):
        network = DrivingNetwork()
        network.route_cache = {}
        network.add_site(1, "", -37.8, 145)
        network.add_site(2, "", -37.9, 145.1)
        payload = {"code": "Ok", "routes": [{"legs": [{"distance": 2500}],
                   "geometry": {"coordinates": [[145, -37.8], [145, -37.9], [145.1, -37.9]]}}]}
        with tempfile.TemporaryDirectory() as folder:
            network.cache_file = Path(folder) / "route.json"
            with patch("src.routing.network.requests.get") as get:
                get.return_value.json.return_value = payload
                result = network.driving_route([1, 2])
                self.assertEqual(result["legs"], [2.5])
                self.assertEqual(len(result["geometry"]), 3)
                self.assertEqual(get.call_args.kwargs["params"]["continue_straight"], "true")
                self.assertEqual(network.driving_route([1, 2]), result)
                self.assertEqual(get.call_count, 1)
