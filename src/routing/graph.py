"""
graph.py - Graph representation of the Boroondara road network for route guidance.

Integrates with Assignment 2A search algorithms to find optimal routes.
"""

from typing import Dict, List, Tuple, Optional
import heapq


class RoadNetwork:
    """Graph representation of the Boroondara road network using SCATS sites as nodes."""

    def __init__(self):
        # adjacency list: {scats_id: [(neighbour_scats_id, distance_km), ...]}
        self.adjacency: Dict[int, List[Tuple[int, float]]] = {}
        # SCATS site info: {scats_id: {"name": str, "lat": float, "lon": float}}
        self.sites: Dict[int, dict] = {}

    def add_site(self, scats_id: int, name: str, lat: float, lon: float):
        """Add a SCATS intersection site."""
        self.sites[scats_id] = {"name": name, "lat": lat, "lon": lon}
        if scats_id not in self.adjacency:
            self.adjacency[scats_id] = []

    def add_edge(self, from_id: int, to_id: int, distance_km: float):
        """Add a directed edge between two SCATS sites."""
        self.adjacency.setdefault(from_id, []).append((to_id, distance_km))

    def get_neighbours(self, scats_id: int) -> List[Tuple[int, float]]:
        """Get neighbouring sites and distances."""
        return self.adjacency.get(scats_id, [])

    def find_top_k_routes(
        self,
        origin: int,
        destination: int,
        travel_time_func,
        k: int = 5,
    ) -> List[Tuple[List[int], float]]:
        """Find top-k shortest routes from origin to destination.

        Args:
            origin: Origin SCATS site number
            destination: Destination SCATS site number
            travel_time_func: Function(from_id, to_id, distance) -> travel_time
            k: Number of routes to return

        Returns:
            List of (path, total_travel_time) tuples, sorted by travel time
        """
        # TODO: Integrate A2A search algorithms (A*, Dijkstra, etc.)
        # Use Yen's k-shortest paths or similar algorithm
        raise NotImplementedError("Integrate A2A search algorithms here")
