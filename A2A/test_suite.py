"""Generate 16 reproducible scenarios and verify all six search methods."""
import csv
import heapq
from collections import deque
from pathlib import Path
from search import read_problem, run_search

ROOT = Path(__file__).resolve().parent
TESTS = ROOT / 'tests'
RESULTS = ROOT / 'results'
METHODS = ('DFS', 'BFS', 'GBFS', 'AS', 'CUS1', 'CUS2')

def write_case(name, nodes, edges, origin, goals):
    lines = ['Nodes:'] + [f'{n}: ({x},{y})' for n,(x,y) in nodes.items()]
    lines += ['Edges:'] + [f'({u},{v}): {w}' for u,v,w in edges]
    lines += ['Origin:', str(origin), 'Destinations:', '; '.join(map(str, goals))]
    (TESTS / f'{name}.txt').write_text('\n'.join(lines)+'\n', encoding='utf-8')

def build_complex_cases():
    """Six reproducible, moderately sized directed weighted graphs.

    Every case uses the assignment's Nodes/Edges/Origin/Destinations format.
    Multiple destinations mean reach ANY goal, not visit ALL goals.
    """
    def grid(cols, rows, *, start_id=1):
        return {start_id + r * cols + c: (c * 2, r * 2)
                for r in range(rows) for c in range(cols)}

    # 15 nodes: layered directed DAG with several alternate paths.
    nodes = grid(5, 3)
    edges = []
    for r in range(3):
        for c in range(4):
            u = 1 + r * 5 + c
            edges.append((u, u + 1, 2 + (u % 4)))
            if r < 2:
                edges.append((u, u + 5, 2 + (u % 3)))
    edges += [(5, 10, 4), (10, 15, 4), (6, 12, 3), (7, 13, 5), (9, 15, 9)]
    chain = ('simple_chain', nodes, edges, 1, [15])

    # 16 nodes: four possible goals, different depths and edge costs.
    nodes = grid(4, 4)
    edges = []
    for r in range(4):
        for c in range(4):
            u = 1 + r * 4 + c
            if c < 3:
                edges.append((u, u + 1, 2 + (u % 5)))
            if r < 3:
                edges.append((u, u + 4, 1 + ((u * 2) % 6)))
    edges += [(1, 7, 13), (3, 12, 5), (6, 15, 4), (9, 16, 6)]
    multi = ('two_goals', nodes, edges, 1, [8, 12, 14, 16])

    # 16 nodes: cheap multi-hop route competes with expensive shortcuts.
    nodes = grid(4, 4)
    edges = []
    for r in range(4):
        for c in range(4):
            u = 1 + r * 4 + c
            if c < 3:
                edges.append((u, u + 1, 1 if r == 2 else 7 + r))
            if r < 3:
                edges.append((u, u + 4, 1 if c == 0 else 5 + c))
    edges += [(1, 16, 60), (1, 8, 22), (5, 13, 2), (9, 15, 3), (12, 16, 18)]
    weighted = ('weighted_detour', nodes, edges, 1, [16])

    # 14 nodes: cyclic directed graph, cross links, and multiple exits.
    nodes = {i: ((i - 1) % 7 * 2, (i - 1) // 7 * 3) for i in range(1, 15)}
    edges = [(i, i + 1, 1 + (i % 4)) for i in range(1, 14)]
    edges += [(i + 1, i, 2 + (i % 3)) for i in (2, 4, 6, 8, 10)]
    edges += [(1, 5, 8), (2, 8, 6), (3, 9, 4), (4, 11, 7),
              (5, 2, 2), (7, 3, 5), (8, 12, 3), (9, 6, 2),
              (10, 14, 6), (11, 7, 3), (12, 9, 2)]
    cycles = ('cycles', nodes, edges, 1, [13, 14])

    # 15 nodes: branches lead to traps; the goal is only on one branch.
    nodes = grid(5, 3)
    edges = [(1, 2, 2), (1, 6, 3), (1, 11, 5),
             (2, 3, 2), (3, 4, 2), (4, 5, 1), (3, 8, 4),
             (6, 7, 2), (7, 8, 2), (8, 9, 2), (9, 10, 2),
             (11, 12, 2), (12, 13, 2), (13, 14, 2), (14, 15, 2),
             (7, 3, 8), (9, 4, 6), (12, 7, 5)]
    dead_end = ('dead_end', nodes, edges, 1, [10])

    # 18 nodes: three destinations at different distances and costs.
    nodes = grid(6, 3)
    edges = []
    for r in range(3):
        for c in range(6):
            u = 1 + r * 6 + c
            if c < 5:
                edges.append((u, u + 1, 2 + ((r + c) % 5)))
            if r < 2:
                edges.append((u, u + 6, 1 + ((u + c) % 5)))
    edges += [(1, 9, 11), (2, 13, 7), (4, 17, 12),
              (7, 14, 3), (8, 16, 5), (11, 18, 8)]
    multiple = ('multiple_destinations', nodes, edges, 1, [6, 15, 18])

    return {case[0]: case for case in
            (chain, multi, weighted, cycles, dead_end, multiple)}


def make_cases():
    TESTS.mkdir(exist_ok=True)
    line = {i: (i,0) for i in range(1,7)}
    cases = [
        ('direct', {1:(0,0),2:(1,0)}, [(1,2,3)],1,[2]),
        ('origin_is_goal', {1:(0,0),2:(1,0)}, [(1,2,1)],1,[1]),
        ('unreachable', {1:(0,0),2:(1,0),3:(2,0)}, [(1,2,1)],1,[3]),
        ('one_way_block', {1:(0,0),2:(1,0)}, [(2,1,1)],1,[2]),
        ('simple_chain', line, [(i,i+1,1) for i in range(1,6)],1,[6]),
        ('two_goals', {1:(0,0),2:(1,0),3:(0,1)}, [(1,2,2),(1,3,3)],1,[2,3]),
        ('weighted_detour', {1:(0,0),2:(1,0),3:(0,1),4:(2,0)}, [(1,2,20),(2,4,20),(1,3,1),(3,4,1)],1,[4]),
        ('cycles', {1:(0,0),2:(1,0),3:(1,1)}, [(1,2,1),(2,3,1),(3,1,1),(2,1,1)],1,[3]),
        ('zero_cost', {1:(0,0),2:(1,0),3:(2,0)}, [(1,2,0),(2,3,0),(1,3,2)],1,[3]),
        ('dead_end', {1:(0,0),2:(1,0),3:(0,1),4:(0,2)}, [(1,2,1),(1,3,1),(3,4,1)],1,[4]),
        ('equal_paths', {1:(0,0),2:(1,1),3:(1,-1),4:(2,0)}, [(1,2,1),(1,3,1),(2,4,1),(3,4,1)],1,[4]),
        ('reverse_edges', {1:(0,0),2:(1,0),3:(2,0)}, [(3,2,1),(2,1,1)],3,[1]),
        ('nonconsecutive_ids', {10:(0,0),20:(1,0),99:(2,0)}, [(10,20,1),(20,99,2)],10,[99]),
        ('multiple_destinations', {1:(0,0),2:(1,0),3:(2,0),4:(0,1),5:(0,2)}, [(1,2,1),(2,3,1),(1,4,1),(4,5,1)],1,[3,5]),
        ('longer_cheaper', {1:(0,0),2:(1,0),3:(2,0),4:(3,0),5:(4,0)}, [(1,5,20),(1,2,1),(2,3,1),(3,4,1),(4,5,1)],1,[5]),
    ]
    # Six upgraded scenarios requested after the tutor check-in. Keep the
    # remaining ten baseline/edge cases so the suite still covers 16 cases.
    complex_cases = build_complex_cases()
    cases = [complex_cases.get(case[0], case) for case in cases]
    for case in cases:
        write_case(*case)

def oracle(g, unit=False):
    queue = [(0, g.origin)]
    best = {g.origin: 0}
    while queue:
        d,u = heapq.heappop(queue)
        if d != best[u]:
            continue
        if u in g.destinations:
            return d
        for v,c in g.edges[u]:
            nd = d + (1 if unit else c)
            if nd < best.get(v, float('inf')):
                best[v] = nd
                heapq.heappush(queue,(nd,v))
    return None

def run():
    make_cases()
    RESULTS.mkdir(exist_ok=True)
    rows = []
    for path in sorted(TESTS.glob('*.txt')):
        g = read_problem(str(path))
        min_cost, min_hops = oracle(g), oracle(g, True)
        for method in METHODS:
            goal, created, route = run_search(g, method)
            reached = goal is not None
            valid = (not reached and min_cost is None) or (reached and route[0] == g.origin and route[-1] in g.destinations)
            cost = 0
            if reached:
                for u,v in zip(route, route[1:]):
                    weights = [w for target,w in g.edges[u] if target == v]
                    if not weights:
                        valid = False
                        break
                    cost += min(weights)
            if method in ('AS','CUS1') and reached and abs(cost-min_cost)>1e-8:
                valid = False
            if method in ('BFS','CUS2') and reached and len(route)-1 != min_hops:
                valid = False
            rows.append({'case':path.stem,'method':method,'goal':goal if reached else 'unreachable',
                         'nodes_created':created,'path':' -> '.join(map(str,route)) if reached else '-',
                         'path_cost':cost if reached else '-', 'moves':len(route)-1 if reached else '-',
                         'status':'PASS' if valid else 'FAIL'})
    csv_path = RESULTS / 'test_results.csv'
    try:
        with csv_path.open('w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
    except PermissionError:
        print(f"Warning: Could not write to '{csv_path}' because it is open in another program (e.g. Excel).")
        print("Please close the file and re-run to update the CSV.")
    failures = [r for r in rows if r['status'] != 'PASS']
    print(f'Tested {len(rows)//6} scenarios x 6 methods = {len(rows)} runs; failures: {len(failures)}')
    for failure in failures:
        print(failure)
    return len(failures)

if __name__ == '__main__':
    raise SystemExit(1 if run() else 0)
