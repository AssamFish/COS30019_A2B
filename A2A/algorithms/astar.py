"""A* tree search: prioritize accumulated cost plus admissible estimate."""
import heapq
from graph import Graph
from heuristics import heuristics
from search_common import start_node, children_of, reconstruct


def search(graph: Graph):
    start = start_node(graph)
    created = 1
    counter = 0  # Chronological tie-breaking for equal priorities.
    h = heuristics(graph, "AS")
    frontier = [(h[start.state], counter, start)]
    while frontier:
        _, _, current = heapq.heappop(frontier)
        if current.state in graph.destinations:
            return current.state, created, reconstruct(current)
        children = children_of(graph, current)
        created += len(children)
        for child in children:
            counter += 1
            priority = child.cost + h[child.state]
            heapq.heappush(frontier, (priority, counter, child))
    return None, created, []
