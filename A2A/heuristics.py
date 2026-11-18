"""Admissible distance-based estimates for informed searches."""
import math
if __package__:
    from .graph import Graph
else:
    from graph import Graph

def euclidean(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.dist(a, b)

def heuristics(graph: Graph, method: str) -> dict[int, float]:
    """Admissible scaled straight-line estimates: cost for AS, hops for CUS2."""
    ratios = []
    lengths = []
    for u, adjacent in graph.edges.items():
        for v, cost in adjacent:
            length = euclidean(graph.coordinates[u], graph.coordinates[v])
            if length > 0:
                ratios.append(cost / length)
                lengths.append(length)
    scale = min(ratios) if ratios else 0.0
    max_length = max(lengths, default=0.0)
    estimates = {}
    for node, xy in graph.coordinates.items():
        distance = min(euclidean(xy, graph.coordinates[goal]) for goal in graph.destinations)
        estimates[node] = distance * scale if method in ('GBFS', 'AS') else (distance / max_length if max_length else 0.0)
    return estimates

