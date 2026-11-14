"""Custom 1: uniform-cost tree search, uninformed minimum-cost route."""
import heapq
if __package__ == "A2A.algorithms":
    from ..graph import Graph
    from ..search_common import start_node, children_of, reconstruct
else:
    from graph import Graph
    from search_common import start_node, children_of, reconstruct


def routes(graph: Graph):
    """Yield loopless routes in ascending cost order."""
    start = start_node(graph)
    created = 1
    counter = 0  # Chronological tie-breaking for equal priorities.
    frontier = [(0.0, counter, start)]
    while frontier:
        _, _, current = heapq.heappop(frontier)
        if current.state in graph.destinations:
            yield current.state, created, reconstruct(current), current.cost
            continue
        children = children_of(graph, current)
        created += len(children)
        for child in children:
            counter += 1
            priority = child.cost
            heapq.heappush(frontier, (priority, counter, child))
    yield None, created, [], 0.0


def search(graph: Graph):
    goal, created, path, _ = next(routes(graph))
    return goal, created, path
