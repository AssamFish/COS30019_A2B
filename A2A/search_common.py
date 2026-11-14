"""Shared search-tree node structure and expansion helpers."""
from dataclasses import dataclass
if __package__:
    from .graph import Graph
else:
    from graph import Graph

@dataclass
class SearchNode:
    state: int
    parent: 'SearchNode | None'
    cost: float
    depth: int
    ancestors: frozenset[int]


def start_node(graph: Graph) -> SearchNode:
    return SearchNode(graph.origin, None, 0.0, 0, frozenset({graph.origin}))


def children_of(graph: Graph, current: SearchNode) -> list[SearchNode]:
    """Generate child tree nodes in ascending ID order; block path cycles only."""
    children = []
    for next_id, weight in graph.edges[current.state]:
        if next_id in current.ancestors:
            continue
        children.append(SearchNode(next_id, current, current.cost + weight,
                                   current.depth + 1, current.ancestors | {next_id}))
    return children


def reconstruct(node: SearchNode) -> list[int]:
    path = []
    while node is not None:
        path.append(node.state)
        node = node.parent
    return path[::-1]
