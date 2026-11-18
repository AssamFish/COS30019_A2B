"""Desktop trip planner with a geographical SCATS map."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
import re
import tkinter as tk
from tkinter import ttk
from tkintermapview import TkinterMapView


BG = "#101923"
PANEL = "#172432"
INPUT = "#213344"
TEXT = "#edf5fa"
MUTED = "#9bb3c7"
ACCENT = "#60e4ce"
MAP = "#111e2a"
FONT = "Segoe UI"


def label(parent, text="", size=10, color=TEXT, bold=False, **options):
    weight = "bold" if bold else "normal"
    return tk.Label(parent, text=text, bg=parent["bg"], fg=color,
                    font=(FONT, size, weight), anchor="w", **options)


def configure_styles(root):
    style = ttk.Style(root)
    style.theme_use("clam")
    for kind in ("TCombobox", "TEntry"):
        name = f"Trip.{kind}"
        style.configure(name, fieldbackground=INPUT, foreground=TEXT,
                        background=INPUT, bordercolor="#344b60", arrowcolor=TEXT,
                        lightcolor=INPUT, darkcolor=INPUT, padding=3)
        style.map(name, fieldbackground=[("readonly", INPUT)],
                  foreground=[("readonly", TEXT)], bordercolor=[("focus", ACCENT)])
    style.configure("Route.Treeview", background=PANEL, fieldbackground=PANEL,
                    foreground=TEXT, borderwidth=0, rowheight=23, font=(FONT, 10))
    style.configure("Route.Treeview.Heading", background=INPUT, foreground=MUTED,
                    borderwidth=0, padding=5, font=(FONT, 9, "bold"))
    style.map("Route.Treeview", background=[("selected", "#284d57")],
              foreground=[("selected", "#ffffff")])
    root.option_add("*TCombobox*Listbox.background", INPUT)
    root.option_add("*TCombobox*Listbox.foreground", TEXT)
    root.option_add("*TCombobox*Listbox.selectBackground", "#284d57")


def intersection_name(description):
    parts = re.split(r"\s+(?:N|S|E|W|NE|NW|SE|SW)\s+of\s+", description,
                     maxsplit=1, flags=re.IGNORECASE)
    return " & ".join(part.replace("_", " ").title() for part in parts)


def run(network, recommend, model, timestamp, top_k):
    root = tk.Tk()
    root.title("Boroondara Traffic Route Guidance")
    root.configure(bg=BG)
    root.geometry("1320x820")
    root.minsize(850, 700)
    configure_styles(root)

    header = tk.Frame(root, bg=BG)
    header.pack(fill="x", padx=24, pady=(10, 8))
    label(header, "Boroondara Traffic Route Guidance", 23, bold=True).pack(anchor="w")
    label(header, "Historical SCATS forecasts  /  October 2006", 10, MUTED).pack(anchor="w", pady=(3, 0))

    layout = tk.Frame(root, bg=BG)
    layout.pack(fill="both", expand=True, padx=24, pady=(0, 12))
    sidebar = tk.Frame(layout, bg=BG, width=304)
    sidebar.pack(side="left", fill="y", padx=(0, 14))
    sidebar.pack_propagate(False)
    form = tk.Frame(sidebar, bg=PANEL, padx=14, pady=8)
    form.pack(fill="x")
    label(form, "Plan a trip", 16, bold=True).pack(fill="x", pady=(0, 7))

    names = {site: intersection_name(info["name"]) for site, info in network.sites.items()}
    site_options = {f"{site} | {names[site]}": site for site in sorted(names)}
    site_labels = {site: option for option, site in site_options.items()}
    model_names = {"LSTM": "lstm", "GRU": "gru", "MLP": "third"}
    display_model = next(name for name, key in model_names.items() if key == model)
    departure = datetime.fromisoformat(str(timestamp))
    first_day = departure.replace(day=1)
    dates = tuple((first_day + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(31))
    times = tuple(f"{hour:02d}:{minute:02d}" for hour in range(24) for minute in (0, 15, 30, 45))
    fields = {}
    departure_row = tk.Frame(form, bg=PANEL)
    settings_row = tk.Frame(form, bg=PANEL)
    for key, title, default, choices in (
        ("origin", "From", site_labels.get(2000, next(iter(site_options), "")), tuple(site_options)),
        ("destination", "To", site_labels.get(3002, next(iter(site_options), "")), tuple(site_options)),
        ("date", "Departure date", departure.strftime("%Y-%m-%d"), dates),
        ("time", "Departure time", departure.strftime("%H:%M"), times),
        ("model", "Forecast model", display_model, tuple(model_names)),
        ("limit", "Maximum routes", top_k, tuple(range(1, 6))),
    ):
        field = form
        if key in ("date", "time", "model", "limit"):
            row = departure_row if key in ("date", "time") else settings_row
            if key in ("date", "model"):
                row.pack(fill="x")
            field = tk.Frame(row, bg=PANEL)
            field.pack(side="left", fill="x", expand=True, padx=(0, 5) if key in ("date", "model") else 0)
        label(field, title, 10, MUTED, True).pack(fill="x", pady=(5, 2))
        variable = fields[key] = tk.StringVar(value=str(default))
        if choices:
            widget = ttk.Combobox(field, textvariable=variable, values=choices,
                                  width=30 if field is form else 10,
                                  state="readonly", style="Trip.TCombobox")
        else:
            widget = ttk.Entry(form, textvariable=variable, width=30, style="Trip.TEntry")
        widget.pack(fill="x")

    results_panel = tk.Frame(sidebar, bg=PANEL, padx=14, pady=10)
    results_panel.pack(fill="both", expand=True, pady=(8, 0))
    label(results_panel, "Route options", 13, bold=True).pack(fill="x")
    summary = tk.StringVar(value="Find routes to compare estimated travel times.")
    label(results_panel, size=9, color=MUTED, textvariable=summary).pack(fill="x", pady=(2, 6))
    results = ttk.Treeview(results_panel, columns=("route", "minutes"), show="headings",
                           height=5, selectmode="browse", style="Route.Treeview")
    results.heading("route", text="Option", anchor="w")
    results.heading("minutes", text="Est. minutes", anchor="e")
    results.column("route", minwidth=90, width=140)
    results.column("minutes", width=94, stretch=False, anchor="e")
    results.pack(fill="x")
    results.tag_configure("alternate", background="#1c2c3c")

    map_panel = tk.Frame(layout, bg=PANEL, padx=14, pady=10)
    map_panel.pack_propagate(False)
    map_panel.pack(side="left", fill="both", expand=True)
    map_header = tk.Frame(map_panel, bg=PANEL)
    map_header.pack(fill="x", pady=(0, 8))
    label(map_header, "Boroondara street map", 14, bold=True).pack(side="left")
    label(map_header, "B  Destination", 10, "#ffad76", True).pack(side="right")
    label(map_header, "A  Start", 10, "#77e3a4", True).pack(side="right", padx=(0, 18))
    toolbar = tk.Frame(map_panel, bg=PANEL)
    toolbar.pack(fill="x", pady=(0, 8))
    map_view = TkinterMapView(map_panel, corner_radius=0,
                             user_agent="COS30019-Boroondara-Route-Guidance/1.0")
    map_view.set_tile_server("https://tile.openstreetmap.org/{z}/{x}/{y}.png", max_zoom=19)
    selection = tk.StringVar(value="Choose a trip to show its estimated route.")
    detail = label(map_panel, size=10, color=MUTED, textvariable=selection, justify="left")
    detail.pack(side="bottom", fill="x", pady=(4, 0))
    detail.bind("<Configure>", lambda event: detail.configure(wraplength=max(100, event.width - 8)))
    point_info = tk.StringVar(value="Click a SCATS pin for its intersection name. Selected routes follow mapped driving roads.")
    point_detail = label(map_panel, size=10, textvariable=point_info, justify="left")
    point_detail.pack(side="bottom", fill="x", pady=(5, 0))
    map_view.pack(fill="both", expand=True)
    attribution = label(map_panel, "Map data (c) OpenStreetMap contributors | Internet required for street tiles",
                        8, MUTED, cursor="hand2")
    attribution.pack(side="bottom", fill="x")
    attribution.bind("<Button-1>", lambda event: __import__("webbrowser").open(
        "https://www.openstreetmap.org/copyright"))
    point_detail.bind("<Configure>", lambda event: point_detail.configure(wraplength=max(100, event.width - 8)))
    display = []
    markers = {}
    route_line = None
    dot = tk.PhotoImage(master=root, width=12, height=12)
    for y in range(12):
        for x in range(12):
            radius_squared = (x - 5.5) ** 2 + (y - 5.5) ** 2
            if radius_squared <= 30:
                dot.put("#ffffff" if radius_squared > 16 else "#246b86", (x, y))

    def inspect_site(site_id):
        site = network.sites[site_id]
        point_info.set(f"SCATS {site_id} | {names[site_id]}\n"
                       f"Latitude {site['lat']:.5f}   Longitude {site['lon']:.5f}")

    for site_id, site in network.sites.items():
        markers[site_id] = map_view.set_marker(
            site["lat"], site["lon"], text="", icon=dot,
            command=lambda marker, site_id=site_id: inspect_site(site_id))

    def reset_map():
        sites = list(network.sites.values())
        if sites:
            map_view.fit_bounding_box(
                (max(s["lat"] for s in sites) + .005, min(s["lon"] for s in sites) - .005),
                (min(s["lat"] for s in sites) - .005, max(s["lon"] for s in sites) + .005))

    for title, action in (
        ("Boroondara", reset_map),
    ):
        tk.Button(toolbar, text=title, command=action, bg=INPUT, fg=TEXT,
                  activebackground=ACCENT, relief="flat", padx=8).pack(side="left", padx=(0, 5))
    root.after(250, reset_map)

    drawing = False

    def draw(event=None):
        nonlocal drawing
        if drawing:
            return
        drawing = True
        try:
            redraw()
        finally:
            drawing = False

    def redraw():
        selected = results.selection()
        path = display[int(selected[0])][0] if selected else ()
        nonlocal route_line
        if route_line is not None:
            route_line.delete()
            route_line = None
        for site_id, marker in list(markers.items()):
            start = bool(path) and site_id == path[0]
            destination = bool(path) and site_id == path[-1]
            title = "A / B" if start and destination else "A" if start else "B" if destination else ""
            color = "#168447" if start else "#d45716" if destination else "#246b86"
            site = network.sites[site_id]
            marker.delete()
            markers[site_id] = map_view.set_marker(
                site["lat"], site["lon"],
                text=title, icon=None if title else dot,
                marker_color_circle="#ffffff", marker_color_outside=color,
                text_color=color if title else "#16384a",
                font=(FONT, 12, "bold") if title else (FONT, 9),
                command=lambda marker, site_id=site_id: inspect_site(site_id))
        if len(path) > 1:
            route_line = map_view.set_path(
                network.route_geometry[tuple(path)],
                color="#008c83", width=5)
        if path:
            index = int(selected[0])
            selection.set(f"{'Fastest route' if index == 0 else f'Route {index + 1}'}"
                          f" | {display[index][1] / 60:.2f} min\n"
                          f"{names[path[0]]} to {names[path[-1]]}\n"
                          + "  >  ".join(map(str, path)))
        else:
            selection.set("Select a route to highlight it on the map.")

    status = tk.StringVar(value="Choose your trip settings, then find routes.")

    worker = ThreadPoolExecutor(max_workers=1)

    def finish(future):
        if not future.done():
            root.after(100, lambda: finish(future))
            return
        find_button.configure(state="normal")
        try:
            routes = future.result()
        except FileNotFoundError:
            status.set("Train the selected model before finding routes.")
            return
        except (ValueError, OSError, KeyError) as exc:
            status.set(str(exc))
            return
        show_routes(routes)

    def update():
        if find_button["state"] == "disabled":
            return
        values = {key: field.get() for key, field in fields.items()}
        find_button.configure(state="disabled")
        status.set("Predicting traffic and checking driving roads...")
        future = worker.submit(
            recommend, model_names[values["model"]], site_options[values["origin"]],
            site_options[values["destination"]], f"{values['date']} {values['time']}",
            int(values["limit"]))
        root.after(100, lambda: finish(future))

    def show_routes(routes):
        results.delete(*results.get_children())
        display[:] = routes
        for index, (path, seconds) in enumerate(routes):
            results.insert("", "end", iid=str(index),
                           values=("1   Fastest" if index == 0 else str(index + 1), f"{seconds / 60:.2f}"),
                           tags=("alternate",) if index % 2 else ())
        if routes:
            results.selection_set("0")
        if routes:
            count = "1 route" if len(routes) == 1 else f"{len(routes)} routes"
            summary.set(f"{count} found | Fastest {routes[0][1] / 60:.2f} min")
            status.set("Select any route in the table to see it on the map.")
        else:
            summary.set("No route found for this trip.")
            status.set("Try a different origin or destination.")
        draw()

    find_button = tk.Button(form, text="Find routes", command=update, bg=ACCENT, fg=BG,
              activebackground="#9af2e3", activeforeground=BG, relief="flat",
              font=(FONT, 11, "bold"), cursor="hand2", pady=4)
    find_button.pack(fill="x", pady=(8, 4))
    label(form, size=9, color=MUTED, textvariable=status, wraplength=210,
          justify="left").pack(fill="x")
    results.bind("<<TreeviewSelect>>", draw)
    root.bind("<Return>", lambda event: update())
    try:
        root.mainloop()
    finally:
        worker.shutdown(wait=False, cancel_futures=True)
