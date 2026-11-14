import unittest

import numpy as np
import pandas as pd

from src.data_processing.data_loader import TrafficDataLoader
from src.routing.graph import RoadNetwork
from src.routing.travel_time import flow_to_travel_time


class TrafficTests(unittest.TestCase):
    def setUp(self):
        self.loader = TrafficDataLoader(".", ".")
        self.raw = pd.DataFrame([{
            "SCATS Number": 2000, "Location": label, "Date": "2006-10-01 00:15",
            **{f"V{i:02}": value for i in range(96)},
        } for label, value in (("N", 1), ("S", 2), ("N", 1))])

    def test_sums_distinct_movements(self):
        self.assertEqual(self.loader.preprocess(self.raw).iloc[0, 0], 3)

    def test_daily_grid(self):
        self.assertEqual(len(self.loader.preprocess(self.raw)), 96)

    def test_date_normalized_to_midnight(self):
        self.assertEqual(self.loader.preprocess(self.raw).index[0].hour, 0)
        self.assertEqual(self.loader.preprocess(self.raw).index[0].minute, 0)

    def test_negative_count_ignored(self):
        self.raw.loc[1, "V00"] = -3
        self.assertEqual(self.loader.preprocess(self.raw).iloc[0, 0], 1)

    def test_window_targets_next_step(self):
        x, y = self.loader.create_sequences(np.arange(6), 2)
        np.testing.assert_array_equal(x[0], [0, 1])
        self.assertEqual(y[0], 2)

    def test_split_retains_chronology(self):
        data = np.arange(10)
        split = self.loader.train_val_test_split(data, data)
        self.assertEqual(split["y_train"][-1], 7)
        self.assertEqual(split["y_val"][0], 8)
        self.assertEqual(split["y_test"][0], 9)


class RouteTests(unittest.TestCase):
    def setUp(self):
        self.network = RoadNetwork()
        for site in range(1, 6):
            self.network.add_site(site, "", 0, 0)
        for edge in ((1, 4, 9), (1, 2, 2), (2, 4, 2), (1, 3, 3),
                     (3, 4, 2), (2, 1, 1), (1, 2, 8)):
            self.network.add_edge(*edge)

    def route(self, start=1, end=4, k=5):
        return self.network.find_top_k_routes(start, end, lambda _, __, cost: cost, k)

    def test_weighted_alternatives_sorted(self):
        self.assertEqual(self.route(), [([1, 2, 4], 4), ([1, 3, 4], 5), ([1, 4], 9)])

    def test_route_limit(self):
        self.assertEqual(len(self.route(k=2)), 2)

    def test_cycle_excluded(self):
        for path, _ in self.route():
            self.assertEqual(len(path), len(set(path)))

    def test_directed_edges(self):
        self.assertEqual(self.route(4, 1), [])

    def test_disconnected_destination(self):
        self.assertEqual(self.route(1, 5), [])

    def test_origin_is_destination(self):
        self.assertEqual(self.route(1, 1), [([1], 0)])

    def test_unknown_site(self):
        with self.assertRaises(ValueError):
            self.route(99, 1)

    def test_invalid_limit(self):
        with self.assertRaises(ValueError):
            self.route(k=6)

    def test_free_flow_with_delay(self):
        self.assertEqual(flow_to_travel_time(0, 1), 90)

    def test_volume_increases_travel_time(self):
        self.assertGreater(flow_to_travel_time(1300, 1), flow_to_travel_time(500, 1))

    def test_above_capacity_is_finite(self):
        self.assertAlmostEqual(flow_to_travel_time(2000, 1), 142.5, places=1)

    def test_invalid_flow(self):
        with self.assertRaises(ValueError):
            flow_to_travel_time(-1, 1)
