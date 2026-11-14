"""Tk interface for selecting and plotting SCATS routes."""

from tkinter import Canvas, StringVar, Tk, messagebox, ttk


def run(network, recommend, model, timestamp, top_k):
    root = Tk()
    root.title("Boroondara Traffic Route Guidance")
    panel = ttk.Frame(root, padding=14)
    panel.pack(fill="both", expand=True)
    site_ids = sorted(network.sites)
    fields = {}
    for row, (label, default, choices) in enumerate((
        ("Origin SCATS", "2000", site_ids),
        ("Destination SCATS", "3002", site_ids),
        ("Departure", timestamp, ()),
        ("Forecast model", model, ("lstm", "gru", "third")),
        ("Maximum routes", top_k, tuple(range(1, 6))),
    )):
        ttk.Label(panel, text=label).grid(row=row, column=0, sticky="w")
        variable = fields[label] = StringVar(value=default)
        widget = (ttk.Combobox(panel, textvariable=variable, values=choices, state="readonly")
                  if choices else ttk.Entry(panel, textvariable=variable))
        widget.grid(row=row, column=1, sticky="ew")

    results = ttk.Treeview(panel, columns=("route", "minutes"), show="headings", height=5)
    results.heading("route", text="SCATS route")
    results.heading("minutes", text="Estimated minutes")
    results.column("minutes", width=125)
    results.grid(row=6, columnspan=2, sticky="ew")
    canvas = Canvas(panel, width=720, height=420, background="white")
    canvas.grid(row=7, columnspan=2, sticky="nsew")
    panel.columnconfigure(1, weight=1)
    panel.rowconfigure(7, weight=1)
    status = StringVar()
    ttk.Label(panel, textvariable=status).grid(row=8, columnspan=2, sticky="w")

    min_lon = min(site["lon"] for site in network.sites.values())
    max_lon = max(site["lon"] for site in network.sites.values())
    min_lat = min(site["lat"] for site in network.sites.values())
    max_lat = max(site["lat"] for site in network.sites.values())
    display = []

    def draw(event=None):
        width = max(canvas.winfo_width(), 100)
        height = max(canvas.winfo_height(), 100)
        points = {s: (24 + (width - 48) * (p["lon"] - min_lon) / (max_lon - min_lon),
                      24 + (height - 48) * (max_lat - p["lat"]) / (max_lat - min_lat))
                  for s, p in network.sites.items()}
        canvas.delete("all")
        for site in points:
            for neighbor, _ in network.get_neighbours(site):
                if site < neighbor:
                    canvas.create_line(*points[site], *points[neighbor], fill="#c2ccd4")
        selection = results.selection()
        if selection:
            path, _ = display[int(selection[0])]
            if len(path) > 1:
                canvas.create_line(*(coord for site in path for coord in points[site]),
                                   fill="#096789", width=4)
        for site, (x, y) in points.items():
            canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill="#18374b", outline="")
            canvas.create_text(x + 5, y - 5, anchor="sw", text=site, fill="#18374b")

    def update():
        values = {name: item.get() for name, item in fields.items()}
        try:
            routes = recommend(values["Forecast model"], int(values["Origin SCATS"]),
                               int(values["Destination SCATS"]), values["Departure"],
                               int(values["Maximum routes"]))
        except (ValueError, OSError) as exc:
            messagebox.showerror("Unable to find routes", str(exc))
            return
        display[:] = routes
        results.delete(*results.get_children())
        for i, (path, seconds) in enumerate(routes):
            results.insert("", "end", iid=str(i), values=(" > ".join(map(str, path)), f"{seconds / 60:.2f}"))
        if routes:
            results.selection_set("0")
        status.set(f"{len(routes)} route(s) found" if routes else "No connection in the estimated road network")
        draw()

    ttk.Button(panel, text="Find routes", command=update).grid(row=5, columnspan=2, pady=8)
    results.bind("<<TreeviewSelect>>", draw)
    canvas.bind("<Configure>", draw)
    root.mainloop()
