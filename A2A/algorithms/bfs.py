"""Breadth-first tree search: FIFO queue, minimum number of moves."""
from collections import deque
if __package__ == "A2A.algorithms":
    from ..graph import Graph
    from ..search_common import start_node, children_of, reconstruct
else:
    from graph import Graph
    from search_common import start_node, children_of, reconstruct


def routes(graph: Graph):
    frontier = deque([start_node(graph)])
    created = 1
    while frontier:
        current = frontier.popleft()
        if current.state in graph.destinations:
            yield current.state, created, reconstruct(current), current.cost
            continue
        children = children_of(graph, current)
        created += len(children)
        frontier.extend(children)
    yield None, created, [], 0.0


def search(graph: Graph):
    goal, created, path, _ = next(routes(graph))
    return goal, created, path
