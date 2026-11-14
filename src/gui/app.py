"""Desktop trip planner and schematic SCATS network."""

from datetime import datetime, timedelta
from math import cos, radians
import re
import tkinter as tk
from tkinter import ttk


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


def draw_network(canvas, network, path, zoom, offset, focused):
    canvas.delete("all")
    width, height = canvas.winfo_width(), canvas.winfo_height()
    if width < 80 or height < 80 or not network.sites:
        return
    sites = network.sites
    min_lat, max_lat = min(p["lat"] for p in sites.values()), max(p["lat"] for p in sites.values())
    min_lon, max_lon = min(p["lon"] for p in sites.values()), max(p["lon"] for p in sites.values())
    longitude_scale = cos(radians((min_lat + max_lat) / 2))
    span_x = (max_lon - min_lon) * longitude_scale
    span_y = max_lat - min_lat
    scale = min((width - 76) / max(span_x, 1e-9), (height - 76) / max(span_y, 1e-9))
    scale *= zoom
    points = {
        site: (width / 2 + offset[0] + (p["lon"] - (min_lon + max_lon) / 2) * longitude_scale * scale,
               height / 2 + offset[1] - (p["lat"] - (min_lat + max_lat) / 2) * scale)
        for site, p in sites.items()
    }

    for x in range(20, width, 32):
        for y in range(20, height, 32):
            canvas.create_oval(x, y, x + 2, y + 2, fill="#243849", outline="")
    for site in points:
        for neighbor, _ in network.get_neighbours(site):
            if site < neighbor:
                canvas.create_line(*points[site], *points[neighbor], fill="#3c5468", width=2)
    if len(path) > 1:
        coords = [value for site in path for value in points[site]]
        canvas.create_line(*coords, fill="#235762", width=11, joinstyle=tk.ROUND, capstyle=tk.ROUND)
        canvas.create_line(*coords, fill=ACCENT, width=4, joinstyle=tk.ROUND, capstyle=tk.ROUND)

    for site, (x, y) in points.items():
        active = site in path
        radius = 6 if active else 4
        canvas.create_oval(x - radius, y - radius, x + radius, y + radius,
                           fill=ACCENT if active else "#93adc0", outline=MAP, width=1, tags=(f"site:{site}",))
    occupied = [(x - 11, y - 11, x + 11, y + 11) for x, y in points.values()]
    for site in sorted(points, key=lambda site: (site != focused, site not in path, site)):
        x, y = points[site]
        if not (0 <= x <= width and 0 <= y <= height):
            continue
        name = intersection_name(sites[site]["name"])
        item = canvas.create_text(x, y, text=f"{site}  {name}", width=135,
                                  fill=TEXT if site in path else MUTED, font=(FONT, 8),
                                  tags=(f"site:{site}",))
        for dx, dy, anchor in ((13, -7, "sw"), (-13, -7, "se"), (13, 7, "nw"),
                               (-13, 7, "ne"), (0, -15, "s"), (0, 15, "n")):
            canvas.coords(item, x + dx, y + dy)
            canvas.itemconfigure(item, anchor=anchor)
            left, top, right, bottom = canvas.bbox(item)
            if (left >= 4 and top >= 4 and right <= width - 4 and bottom <= height - 4
                    and all(right + 3 < l or left - 3 > r or bottom + 3 < t or top - 3 > b
                            for l, t, r, b in occupied)):
                occupied.append((left, top, right, bottom))
                break
        else:
            canvas.delete(item)
    if path:
        for site, marker in {path[0]: "A", path[-1]: "A" if len(path) == 1 else "B"}.items():
            x, y = points[site]
            canvas.create_oval(x - 10, y - 10, x + 10, y + 10, fill=ACCENT, outline=MAP, width=2, tags=(f"site:{site}",))
            canvas.create_text(x, y, text=marker, fill=BG, font=(FONT, 9, "bold"), tags=(f"site:{site}",))
    if focused in points:
        x, y = points[focused]
        canvas.create_oval(x - 14, y - 14, x + 14, y + 14, outline="#ffd580", width=2)


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
    label(map_header, "SCATS network", 14, bold=True).pack(side="left")
    label(map_header, "A  Start     B  Destination", 9, MUTED).pack(side="right")
    toolbar = tk.Frame(map_panel, bg=PANEL)
    toolbar.pack(fill="x", pady=(0, 8))
    canvas = tk.Canvas(map_panel, bg=MAP, width=1, height=1, highlightthickness=0)
    selection = tk.StringVar(value="The map shows estimated connections between traffic signals.")
    detail = label(map_panel, size=10, color=MUTED, textvariable=selection, justify="left")
    detail.pack(side="bottom", fill="x", pady=(4, 0))
    detail.bind("<Configure>", lambda event: detail.configure(wraplength=max(100, event.width - 8)))
    point_info = tk.StringVar(value="Click any point for its name and coordinates. Zoom in to see more labels.")
    point_detail = label(map_panel, size=10, textvariable=point_info, justify="left")
    point_detail.pack(side="bottom", fill="x", pady=(5, 0))
    canvas.pack(fill="both", expand=True)
    point_detail.bind("<Configure>", lambda event: point_detail.configure(wraplength=max(100, event.width - 8)))
    display = []
    zoom = 1.0
    offset = [0, 0]
    focused = None
    drag = None

    def change_zoom(factor):
        nonlocal zoom
        zoom = max(1.0, min(4.0, zoom * factor))
        if zoom == 1:
            offset[:] = [0, 0]
        draw()

    def reset_map():
        nonlocal zoom, focused
        zoom, focused = 1.0, None
        offset[:] = [0, 0]
        point_info.set("Click any point for its name and coordinates. Zoom in to see more labels.")
        draw()

    def start_pan(event):
        nonlocal drag
        drag = (event.x, event.y, *offset)

    def pan(event):
        if drag and zoom > 1:
            offset[:] = [drag[2] + event.x - drag[0], drag[3] + event.y - drag[1]]
            draw()

    def inspect(event):
        nonlocal focused, drag
        if drag and abs(event.x - drag[0]) + abs(event.y - drag[1]) < 5:
            for item in reversed(canvas.find_overlapping(event.x - 5, event.y - 5,
                                                        event.x + 5, event.y + 5)):
                tag = next((tag for tag in canvas.gettags(item) if tag.startswith("site:")), None)
                if tag:
                    focused = int(tag.split(":")[1])
                    site = network.sites[focused]
                    point_info.set(f"SCATS {focused} | {names[focused]}\n"
                                   f"Latitude {site['lat']:.5f}   Longitude {site['lon']:.5f}")
                    draw()
                    break
        drag = None

    for title, action in (("+", lambda: change_zoom(1.4)),
                          ("-", lambda: change_zoom(1 / 1.4)), ("Reset view", reset_map)):
        tk.Button(toolbar, text=title, command=action, bg=INPUT, fg=TEXT,
                  activebackground=ACCENT, relief="flat", padx=8).pack(side="left", padx=(0, 5))
    label(toolbar, "Scroll to zoom | Drag to move", 9, MUTED).pack(side="left", padx=5)
    canvas.bind("<MouseWheel>", lambda event: change_zoom(1.4 if event.delta > 0 else 1 / 1.4))
    canvas.bind("<ButtonPress-1>", start_pan)
    canvas.bind("<B1-Motion>", pan)
    canvas.bind("<ButtonRelease-1>", inspect)

    def draw(event=None):
        selected = results.selection()
        path = display[int(selected[0])][0] if selected else ()
        draw_network(canvas, network, path, zoom, offset, focused)
        if path:
            index = int(selected[0])
            selection.set(f"{'Fastest route' if index == 0 else f'Route {index + 1}'}"
                          f" | {display[index][1] / 60:.2f} min\n"
                          f"{names[path[0]]} to {names[path[-1]]}\n"
                          + "  >  ".join(map(str, path)))
        else:
            selection.set("Select a route to highlight it on the map.")

    status = tk.StringVar(value="Choose your trip settings, then find routes.")

    def update():
        values = {key: field.get() for key, field in fields.items()}
        try:
            routes = recommend(model_names[values["model"]], site_options[values["origin"]],
                               site_options[values["destination"]], f"{values['date']} {values['time']}", int(values["limit"]))
        except FileNotFoundError:
            status.set(f"Train the {values['model']} model before using it to find routes.")
            return
        except (ValueError, OSError, KeyError) as exc:
            status.set(str(exc))
            return
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

    tk.Button(form, text="Find routes", command=update, bg=ACCENT, fg=BG,
              activebackground="#9af2e3", activeforeground=BG, relief="flat",
              font=(FONT, 11, "bold"), cursor="hand2", pady=4).pack(fill="x", pady=(8, 4))
    label(form, size=9, color=MUTED, textvariable=status, wraplength=210,
          justify="left").pack(fill="x")
    results.bind("<<TreeviewSelect>>", draw)
    canvas.bind("<Configure>", draw)
    root.bind("<Return>", lambda event: update())
    root.mainloop()
