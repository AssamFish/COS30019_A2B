"""Breadth-first tree search: FIFO queue, minimum number of moves."""
from collections import deque
from graph import Graph
from search_common import start_node, children_of, reconstruct


def search(graph: Graph):
    frontier = deque([start_node(graph)])
    created = 1
    while frontier:
        current = frontier.popleft()
        if current.state in graph.destinations:
            return current.state, created, reconstruct(current)
        children = children_of(graph, current)
        created += len(children)
        frontier.extend(children)
    return None, created, []
