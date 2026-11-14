"""Depth-first tree search: LIFO stack."""
from graph import Graph
from search_common import start_node, children_of, reconstruct


def search(graph: Graph):
    frontier = [start_node(graph)]
    created = 1  # Includes origin and every generated child search node.
    while frontier:
        current = frontier.pop()
        if current.state in graph.destinations:
            return current.state, created, reconstruct(current)
        children = children_of(graph, current)
        created += len(children)
        # Reverse insertion: smallest child is popped first.
        frontier.extend(reversed(children))
    return None, created, []
