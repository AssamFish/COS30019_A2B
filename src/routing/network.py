"""Load the locally prepared, road-validated SCATS network."""

import hashlib
import json
from math import asin, cos, radians, sin, sqrt
from pathlib import Path

import requests

from .graph import RoadNetwork

NETWORK_FILE = Path(__file__).resolve().parents[2] / "data/roads/network.json"


def distance_km(first, second):
    lat1, lon1 = map(radians, first)
    lat2, lon2 = map(radians, second)
    a = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2) ** 2
    return 6371 * 2 * asin(min(1, sqrt(a)))


class DrivingNetwork(RoadNetwork):
    """SCATS links backed by road geometry, with whole-route turn validation."""

    def __init__(self):
        super().__init__()
        self.link_geometry = {}
        self.route_geometry = {}
        self.cache_file = Path(__file__).resolve().parents[2] / "artifacts/driving-routes.json"
        self.route_cache = json.loads(self.cache_file.read_text()) if self.cache_file.exists() else {}

    def driving_route(self, path):
        if len(path) < 2:
            return {"legs": [], "geometry": []}
        positions = [(self.sites[s]["lon"], self.sites[s]["lat"]) for s in path]
        coordinates = ";".join(f"{lon},{lat}" for lon, lat in positions)
        key = hashlib.sha256(coordinates.encode()).hexdigest()
        if key not in self.route_cache:
            try:
                response = requests.get(
                    f"https://router.project-osrm.org/route/v1/driving/{coordinates}",
                    params={"overview": "full", "geometries": "geojson",
                            "continue_straight": "true"},
                    headers={"User-Agent": "COS30019-Boroondara-Route-Guidance/1.0"},
                    timeout=30)
                response.raise_for_status()
                result = response.json()
            except requests.RequestException as exc:
                raise ValueError("Road validation is unavailable. Connect to the internet and try again.") from exc
            if result.get("code") != "Ok" or not result.get("routes"):
                raise ValueError("No drivable route could be verified through these sites.")
            route = result["routes"][0]
            self.route_cache[key] = {
                "legs": [leg["distance"] / 1000 for leg in route["legs"]],
                "geometry": [[lat, lon] for lon, lat in route["geometry"]["coordinates"]],
            }
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.cache_file.with_suffix(".tmp")
            temporary.write_text(json.dumps(self.route_cache), encoding="utf-8")
            temporary.replace(self.cache_file)
        return self.route_cache[key]


def build_network(raw):
    if not NETWORK_FILE.exists():
        raise ValueError("The prepared road network is missing. Restore data/roads/network.json.")
    data = json.loads(NETWORK_FILE.read_text(encoding="utf-8"))
    network = DrivingNetwork()
    for site in sorted(set(raw["SCATS Number"])):
        info = data["sites"].get(str(site))
        if info is None:
            raise ValueError(f"SCATS {site} is missing from the prepared road network.")
        network.add_site(int(site), info["name"], info["lat"], info["lon"])
    for link in data["links"]:
        first, second = link["from"], link["to"]
        if first in network.sites and second in network.sites:
            network.add_edge(first, second, link["distance_km"])
            network.link_geometry[first, second] = link["geometry"]
    return network
