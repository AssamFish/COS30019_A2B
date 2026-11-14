"""Estimate connections from shared road names and the workbook coordinates."""

from collections import defaultdict
from itertools import pairwise
from math import asin, cos, radians, sin, sqrt
import re

from .graph import RoadNetwork


def distance_km(first, second):
    lat1, lon1 = map(radians, first)
    lat2, lon2 = map(radians, second)
    a = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2) ** 2
    return 6371 * 2 * asin(min(1, sqrt(a)))


def build_network(raw):
    network = RoadNetwork()
    roads = defaultdict(set)
    points = {}
    for site, rows in raw.groupby("SCATS Number"):
        coords = rows[["NB_LATITUDE", "NB_LONGITUDE"]].dropna().drop_duplicates()
        if coords.empty:
            continue
        points[site] = tuple(coords.median())
        labels = rows["Location"].dropna().unique()
        if not len(labels):
            continue
        network.add_site(site, labels[0], *points[site])
        for label in labels:
            parts = re.split(r"\s+(?:N|S|E|W|NE|NW|SE|SW)\s+OF\s+", label.upper())
            for part in parts:
                name = re.sub(r"[^A-Z0-9]+", " ", part).strip()
                name = re.sub(r"\bROAD$", "RD", name)
                name = re.sub(r"\bSTREET$", "ST", name)
                if name:
                    roads[name].add(site)

    # Maroondah Highway is labelled Whitehorse Road farther west.
    roads["WHITEHORSE RD"].update(roads.pop("MAROONDAH HWY", set()))
    edges = set()
    for sites in roads.values():
        lat_range = max(points[s][0] for s in sites) - min(points[s][0] for s in sites)
        lon_range = max(points[s][1] for s in sites) - min(points[s][1] for s in sites)
        axis = 0 if lat_range > 0.79 * lon_range else 1
        ordered = sorted(sites, key=lambda s: (points[s][axis], s))
        edges.update(tuple(sorted(pair)) for pair in pairwise(ordered))
    # Workbook road labels leave two western sites without shared-road neighbors.
    # These approximate arterial connections bridge intersections absent from SCATS.
    edges.update({(4262, 4812), (3001, 4821)})
    for first, second in sorted(edges):
        if first not in network.sites or second not in network.sites:
            continue
        distance = distance_km(points[first], points[second])
        network.add_edge(first, second, distance)
        network.add_edge(second, first, distance)
    return network
