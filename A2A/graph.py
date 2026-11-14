"""Graph data types and assignment input-file parser."""
import math
import re
from dataclasses import dataclass
from pathlib import Path

NODE_RE = re.compile(r'^\s*(\d+)\s*:\s*\(\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\)\s*$')
EDGE_RE = re.compile(r'^\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)\s*:\s*(\d+(?:\.\d+)?)\s*$')

@dataclass
class Graph:
    coordinates: dict[int, tuple[float, float]]
    edges: dict[int, list[tuple[int, float]]]
    origin: int
    destinations: set[int]

@dataclass
class SearchNode:
    state: int
    parent: 'SearchNode | None'
    cost: float
    depth: int
    ancestors: frozenset[int]

def read_problem(filename: str) -> Graph:
    sections: dict[str, list[str]] = {k: [] for k in ('Nodes', 'Edges', 'Origin', 'Destinations')}
    section = None
    for line_no, raw in enumerate(Path(filename).read_text(encoding='utf-8-sig').splitlines(), 1):
        line = raw.split('#', 1)[0].strip()
        if not line:
            continue
        if line.endswith(':') and line[:-1].strip() in sections:
            section = line[:-1].strip()
            continue
        if section is None:
            raise ValueError(f'Line {line_no}: data before section heading')
        sections[section].append(line)
    if not all(sections.values()):
        raise ValueError('All four sections (Nodes, Edges, Origin, Destinations) must be nonempty')
    coordinates = {}
    for line in sections['Nodes']:
        m = NODE_RE.fullmatch(line)
        if not m:
            raise ValueError(f'Invalid node: {line}')
        node = int(m[1])
        if node in coordinates:
            raise ValueError(f'Duplicate node: {node}')
        coordinates[node] = (float(m[2]), float(m[3]))
    edges = {node: [] for node in coordinates}
    for line in sections['Edges']:
        m = EDGE_RE.fullmatch(line)
        if not m:
            raise ValueError(f'Invalid edge: {line}')
        source, target, cost = int(m[1]), int(m[2]), float(m[3])
        if source not in edges or target not in edges:
            raise ValueError(f'Unknown edge endpoint: {line}')
        if not math.isfinite(cost) or cost < 0:
            raise ValueError('Edge costs must be finite and nonnegative')
        edges[source].append((target, cost))
    for source in edges:
        edges[source].sort(key=lambda pair: pair[0])
    if len(sections['Origin']) != 1:
        raise ValueError('Origin must contain exactly one node')
    origin = int(sections['Origin'][0])
    destinations = {int(s.strip()) for s in ';'.join(sections['Destinations']).split(';') if s.strip()}
    if origin not in coordinates or not destinations or not destinations <= coordinates.keys():
        raise ValueError('Origin/destination node is missing from Nodes')
    return Graph(coordinates, edges, origin, destinations)

