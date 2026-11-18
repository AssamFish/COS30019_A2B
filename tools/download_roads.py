"""Download OSM street snapshots around the supplied SCATS sites."""
from pathlib import Path
import json
import time
import requests
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.data_processing.data_loader import TrafficDataLoader

base = Path(__file__).resolve().parents[1]
folder = base / "data" / "roads"
folder.mkdir(parents=True, exist_ok=True)
workbook = Path(sys.argv[1])
raw = TrafficDataLoader(workbook.parent, ".").load_raw_data(workbook.name)
session = requests.Session()
session.headers["User-Agent"] = "COS30019-Boroondara-Route-Guidance/1.0"
for site, rows in raw.groupby("SCATS Number"):
    file = folder / f"site-{site}.json"
    if file.exists():
        continue
    lat, lon = rows[["NB_LATITUDE", "NB_LONGITUDE"]].median()
    bbox = f"{lon-.007:.6f},{lat-.007:.6f},{lon+.007:.6f},{lat+.007:.6f}"
    response = session.get("https://api.openstreetmap.org/api/0.6/map.json",
                           params={"bbox": bbox}, timeout=60)
    response.raise_for_status()
    file.write_text(response.text, encoding="utf-8")
    print(site, len(response.content), flush=True)
    time.sleep(1)
