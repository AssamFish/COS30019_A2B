"""Additional Kuching driving demo using OSRM baseline travel times."""

from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import tkinter as tk
from tkinter import ttk

import requests
from tkintermapview import TkinterMapView

BASE = Path(__file__).resolve().parents[2]


def load_places():
    records = json.loads((BASE / "data/roads/kuching-places.json").read_text())
    return {record[0]["name"]: (float(record[0]["lat"]), float(record[0]["lon"]))
            for record in records if record}


def driving_options(origin, destination):
    if origin == destination:
        raise ValueError("Choose two different places.")
    coordinates = ";".join(f"{lon},{lat}" for lat, lon in (origin, destination))
    try:
        response = requests.get(
            f"https://router.project-osrm.org/route/v1/driving/{coordinates}",
            params={"overview": "full", "geometries": "geojson", "alternatives": "true"},
            headers={"User-Agent": "COS30019-Kuching-Demo/1.0"}, timeout=30)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        raise ValueError("Unable to load driving routes. Check your internet connection and try again.") from exc
    if data.get("code") != "Ok" or not data.get("routes"):
        raise ValueError("No driving route was found between these locations.")
    endpoints = [(point["location"][1], point["location"][0]) for point in data["waypoints"]]
    return sorted([
        {"seconds": route["duration"], "km": route["distance"] / 1000,
         "geometry": [(lat, lon) for lon, lat in route["geometry"]["coordinates"]],
         "endpoints": endpoints}
        for route in data["routes"]
    ], key=lambda route: route["seconds"])


def open_demo(parent):
    from .app import BG, PANEL, TEXT, MUTED, ACCENT, FONT, label

    window = tk.Toplevel(parent)
    window.title("Kuching, Sarawak | Driving demo")
    window.geometry("1100x760")
    window.minsize(800, 600)
    window.configure(bg=BG)
    places = load_places()
    body = tk.Frame(window, bg=PANEL, padx=16, pady=12)
    body.pack(fill="both", expand=True, padx=16, pady=16)
    label(body, "Explore Kuching, Sarawak", 20, bold=True).pack(fill="x")
    label(body, "Driving time estimates from OSRM. Local traffic forecasting needs a Kuching dataset.",
          10, MUTED, wraplength=740, justify="left").pack(fill="x", pady=(4, 10))
    controls = tk.Frame(body, bg=PANEL)
    controls.pack(fill="x")
    origin = tk.StringVar(value=next(name for name in places if "Swinburne" in name))
    destination = tk.StringVar(value=next(name for name in places if "Waterfront" in name))
    for title, variable in (("From", origin), ("To", destination)):
        cell = tk.Frame(controls, bg=PANEL)
        cell.pack(side="left", fill="x", expand=True, padx=(0, 12))
        label(cell, title, 10, MUTED, True).pack(fill="x")
        ttk.Combobox(cell, textvariable=variable, values=tuple(places),
                     state="readonly", style="Trip.TCombobox", width=35).pack(fill="x")
    status = tk.StringVar(value="Choose two places and find driving routes.")
    label(body, textvariable=status, size=10, color=MUTED).pack(fill="x", pady=8)
    table = ttk.Treeview(body, columns=("option", "minutes", "km"), show="headings",
                         height=3, selectmode="browse", style="Route.Treeview")
    for key, title in (("option", "Route option"), ("minutes", "Estimated minutes"), ("km", "Distance (km)")):
        table.heading(key, text=title)
        table.column(key, width=140, anchor="center")
    table.pack(fill="x", pady=(0, 8))
    footer = label(body, "Map data (c) OpenStreetMap contributors | OSRM driving estimates | Internet required",
                   9, MUTED)
    footer.pack(side="bottom", fill="x", pady=(6, 0))
    view = TkinterMapView(body, corner_radius=0, user_agent="COS30019-Kuching-Demo/1.0")
    view.set_tile_server("https://tile.openstreetmap.org/{z}/{x}/{y}.png", max_zoom=19)
    view.pack(fill="both", expand=True)
    view.set_position(1.545, 110.351)
    view.set_zoom(13)
    executor = ThreadPoolExecutor(max_workers=1)
    options = []
    painting = False

    def draw(event=None):
        nonlocal painting
        selected = table.selection()
        if painting or not selected:
            return
        painting = True
        try:
            route = options[int(selected[0])]
            view.delete_all_path()
            view.delete_all_marker()
            for title, color, point in zip(("A", "B"), ("#168447", "#d45716"), route["endpoints"]):
                view.set_marker(*point, text=title, marker_color_outside=color,
                                marker_color_circle="#ffffff", text_color=color, font=(FONT, 12, "bold"))
            view.set_path(route["geometry"], color="#008c83", width=5)
            geometry = route["geometry"]
            view.fit_bounding_box((max(p[0] for p in geometry) + .002, min(p[1] for p in geometry) - .002),
                                  (min(p[0] for p in geometry) - .002, max(p[1] for p in geometry) + .002))
        finally:
            painting = False

    def finish(future):
        if not window.winfo_exists():
            return
        if not future.done():
            window.after(100, lambda: finish(future))
            return
        button.configure(state="normal")
        try:
            options[:] = future.result()
        except ValueError as exc:
            status.set(str(exc))
            return
        table.delete(*table.get_children())
        for index, route in enumerate(options):
            table.insert("", "end", iid=str(index), values=(
                "1  Fastest" if index == 0 else index + 1,
                f"{route['seconds'] / 60:.1f}", f"{route['km']:.2f}"))
        table.selection_set("0")
        status.set(f"{len(options)} driving option(s). Times use typical road speeds; live congestion is excluded.")
        draw()

    def find():
        if button["state"] == "disabled":
            return
        button.configure(state="disabled")
        status.set("Checking driving roads in Kuching...")
        future = executor.submit(driving_options, places[origin.get()], places[destination.get()])
        window.after(100, lambda: finish(future))

    button = tk.Button(controls, text="Find routes", command=find, bg=ACCENT, fg=BG,
                       relief="flat", font=(FONT, 10, "bold"), padx=12, pady=6)
    button.pack(side="left", pady=(16, 0))
    table.bind("<<TreeviewSelect>>", draw)
    window.bind("<Destroy>", lambda event: executor.shutdown(wait=False, cancel_futures=True)
                if event.widget is window else None)
    return window
