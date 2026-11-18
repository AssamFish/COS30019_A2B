"""Greedy best-first search: prioritize estimated remaining cost."""
import heapq
if __package__ == "A2A.algorithms":
    from ..graph import Graph
    from ..heuristics import heuristics
    from ..search_common import start_node, children_of, reconstruct
else:
    from graph import Graph
    from heuristics import heuristics
    from search_common import start_node, children_of, reconstruct


def routes(graph: Graph):
    start = start_node(graph)
    created = 1
    counter = 0  # Chronological tie-breaking for equal priorities.
    h = heuristics(graph, "GBFS")
    frontier = [(h[start.state], counter, start)]
    while frontier:
        _, _, current = heapq.heappop(frontier)
        if current.state in graph.destinations:
            yield current.state, created, reconstruct(current), current.cost
            continue
        children = children_of(graph, current)
        created += len(children)
        for child in children:
            counter += 1
            priority = h[child.state]
            heapq.heappush(frontier, (priority, counter, child))
    yield None, created, [], 0.0


def search(graph: Graph):
    goal, created, path, _ = next(routes(graph))
    return goal, created, path
