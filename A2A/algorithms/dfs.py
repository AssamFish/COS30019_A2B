"""Depth-first tree search: LIFO stack."""
if __package__ == "A2A.algorithms":
    from ..graph import Graph
    from ..search_common import start_node, children_of, reconstruct
else:
    from graph import Graph
    from search_common import start_node, children_of, reconstruct


def routes(graph: Graph):
    frontier = [start_node(graph)]
    created = 1  # Includes origin and every generated child search node.
    while frontier:
        current = frontier.pop()
        if current.state in graph.destinations:
            yield current.state, created, reconstruct(current), current.cost
            continue
        children = children_of(graph, current)
        created += len(children)
        # Reverse insertion: smallest child is popped first.
        frontier.extend(reversed(children))
    yield None, created, [], 0.0


def search(graph: Graph):
    goal, created, path, _ = next(routes(graph))
    return goal, created, path
