"""Prepare corrected SCATS positions and road geometry from OpenStreetMap."""
import json
import re
import sys
import time
import requests
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.data_processing.data_loader import TrafficDataLoader
from src.routing.network import distance_km

BASE = Path(__file__).resolve().parents[1]


def road_name(name):
    name = re.sub(r"[^A-Z0-9]+", " ", name.upper()).strip()
    for full, short in (("ROAD", "RD"), ("STREET", "ST"), ("HIGHWAY", "HWY"),
                        ("GROVE", "GV"), ("FREEWAY", "FWY")):
        name = re.sub(r"\b" + full + r"\b", short, name)
    return {"MAROONDAH HWY": "WHITEHORSE RD", "S E ARTERIAL": "MONASH FWY",
            "HARP ST": "HARP RD"}.get(name, name)


def read_streets():
    elements = {}
    for file in sorted((BASE / "data/roads").glob("site-*.json")):
        for element in json.loads(file.read_text(encoding="utf-8"))["elements"]:
            elements[element["type"], element["id"]] = element
    nodes = {i: e for (kind, i), e in elements.items() if kind == "node"}
    ways = {}
    names = defaultdict(set)
    allowed = {"primary", "secondary", "tertiary", "trunk", "motorway",
               "primary_link", "secondary_link", "tertiary_link", "trunk_link",
               "motorway_link", "residential", "unclassified", "living_street"}
    for (kind, i), e in elements.items():
        tags = e.get("tags", {})
        if kind != "way" or tags.get("highway") not in allowed:
            continue
        if tags.get("motor_vehicle", tags.get("vehicle", tags.get("access"))) in {"no", "private"}:
            continue
        ways[i] = e
        if "name" in tags:
            for node in e["nodes"]:
                names[node].add(road_name(tags["name"]))
    return nodes, ways, names


def locate_sites(raw, nodes, names):
    sites = {}
    for site, rows in raw.groupby("SCATS Number"):
        original = tuple(rows[["NB_LATITUDE", "NB_LONGITUDE"]].median())
        labels = list(rows.Location.dropna().unique())
        expected = set()
        for label in labels:
            expected.update(road_name(part) for part in re.split(
                r"\s+(?:N|S|E|W|NE|NW|SE|SW)\s+OF\s+", label.upper()))
        choices = []
        for node, road_names in names.items():
            match = len(expected & road_names)
            if not match or node not in nodes:
                continue
            point = (nodes[node]["lat"], nodes[node]["lon"])
            distance = distance_km(original, point)
            if distance < 1.5:
                choices.append((match, distance, node))
        if not choices:
            raise ValueError(f"No named road match for SCATS {site}")
        if int(site) == 2825:
            # Burke Road crosses the freeway on a bridge, rather than sharing
            # an OSM junction node with the freeway below.
            choices = [c for c in choices if "BURKE RD" in names[c[2]]]
        best_match = max(c[0] for c in choices)
        eligible = [c for c in choices if c[0] == best_match]
        # Prefer a shared-road intersection over a point on just one approach.
        _, distance, node = min(eligible, key=lambda c: c[1])
        point = nodes[node]
        sites[int(site)] = {"name": labels[0], "lat": point["lat"], "lon": point["lon"],
                            "osm_node": node, "original": original,
                            "matched_roads": sorted(expected & names[node]),
                            "offset_m": round(distance * 1000)}
    return sites


if __name__ == "__main__":
    workbook = Path(sys.argv[1])
    raw = TrafficDataLoader(workbook.parent, ".").load_raw_data(workbook.name)
    nodes, ways, names = read_streets()
    sites = locate_sites(raw, nodes, names)
    folder = BASE / "data/roads"
    cache = folder / "validated-links.json"
    validated = json.loads(cache.read_text()) if cache.exists() else {}
    session = requests.Session()
    session.headers["User-Agent"] = "COS30019-Boroondara-Route-Guidance/1.0"
    candidates = json.loads((folder / "candidate-links.json").read_text())
    queued = {tuple(pair) for pair in candidates}

    def add_intermediate_links(link):
        visits = []
        for site, info in sites.items():
            if site in {link["from"], link["to"]}:
                continue
            closest = min(
                (distance_km((info["lat"], info["lon"]), point), index)
                for index, point in enumerate(link["geometry"])
            )
            if closest[0] < .025:
                visits.append((closest[1], site))
        chain = [link["from"]] + [site for _, site in sorted(visits)] + [link["to"]]
        for first, second in zip(chain, chain[1:]):
            if (first, second) not in queued:
                queued.add((first, second))
                candidates.append([first, second])

    for index, (first, second) in enumerate(candidates):
        a, b = sites[first], sites[second]
        key = f"{first}-{second}"
        if key in validated:
            add_intermediate_links(validated[key])
            continue
        coordinates = f"{a['lon']},{a['lat']};{b['lon']},{b['lat']}"
        response = session.get(
            f"https://router.project-osrm.org/route/v1/driving/{coordinates}",
            params={"overview": "full", "geometries": "geojson", "steps": "false",
                    "continue_straight": "true"}, timeout=45)
        response.raise_for_status()
        result = response.json()
        if result["code"] != "Ok":
            raise ValueError(f"No driving route for {key}: {result['code']}")
        route = result["routes"][0]
        validated[key] = {
            "from": first, "to": second, "distance_km": route["distance"] / 1000,
            "geometry": [[lat, lon] for lon, lat in route["geometry"]["coordinates"]],
            "snap_distance_m": [w["distance"] for w in result["waypoints"]],
        }
        add_intermediate_links(validated[key])
        cache.write_text(json.dumps(validated), encoding="utf-8")
        print(index + 1, len(candidates), key, round(route["distance"]), flush=True)
        time.sleep(1)
    links = []
    skipped = []
    for link in validated.values():
        endpoints = {link["from"], link["to"]}
        interior = link["geometry"][1:-1]
        passes_site = any(
            distance_km((info["lat"], info["lon"]), point) < .025
            for site, info in sites.items() if site not in endpoints
            for point in interior
        )
        if passes_site:
            skipped.append([link["from"], link["to"]])
        else:
            links.append(link)
    output = {
        "schema": 1, "source": "OpenStreetMap intersection nodes and OSRM driving routes",
        "retrieved": "2026-11-18",
        "sites": sites, "links": links, "excluded_links_passing_other_sites": skipped
    }
    (folder / "network.json").write_text(json.dumps(output), encoding="utf-8")
    print("Wrote network.json", flush=True)
