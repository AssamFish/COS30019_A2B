"""COS30019 A2A command-line entry point.

Usage: python search.py <filename> <DFS|BFS|GBFS|AS|CUS1|CUS2>
"""
import sys
from graph import Graph, read_problem
from algorithms import dfs, bfs, gbfs, astar, cus1, cus2

METHODS = {
    'DFS': dfs.search,
    'BFS': bfs.search,
    'GBFS': gbfs.search,
    'AS': astar.search,
    'CUS1': cus1.search,
    'CUS2': cus2.search,
}


def run_search(graph: Graph, method: str):
    """Compatibility wrapper used by the original test_suite.py."""
    method = method.upper()
    if method not in METHODS:
        raise ValueError(f'Unknown method {method}; choose DFS BFS GBFS AS CUS1 CUS2')
    return METHODS[method](graph)


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print('Usage: python search.py <filename> <DFS|BFS|GBFS|AS|CUS1|CUS2>', file=sys.stderr)
        return 2
    filename, method = argv[1], argv[2].upper()
    try:
        graph = read_problem(filename)
        goal, count, path = run_search(graph, method)
    except (OSError, UnicodeError, ValueError) as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 2
    print(f'{filename} {method}')
    print(f'{goal if goal is not None else "No goal"} {count}')
    print(' '.join(map(str, path)) if path else 'No path')
    return 0 if goal is not None else 1


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
