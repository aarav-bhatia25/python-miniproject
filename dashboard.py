import sqlite3
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

from database import MODES, STATUSES, get_communications, get_events, get_summary, get_telemetry


BG = "#101923"
PANEL = "#192735"
TEXT = "#e5edf3"
MUTED = "#98aebf"
CYAN = "#63d4cf"
AMBER = "#f4b66a"


class Dashboard:
    def __init__(self, root, connection):
        self.root = root
        self.connection = connection
        root.title("SomaiyaSat - Mission Data Dashboard")
        root.geometry("1050x760")
        root.minsize(900, 650)
        self.set_style()

        header = ttk.Frame(root, padding=16)
        header.pack(fill="x")
        badge = tk.Canvas(header, width=76, height=64, bg=BG, highlightthickness=0)
        badge.pack(side="left", padx=(0, 14))
        badge.create_oval(8, 12, 66, 52, outline="#395366", width=2)
        badge.create_oval(22, 2, 52, 62, outline="#395366")
        badge.create_rectangle(29, 24, 45, 40, fill=AMBER, outline=AMBER)
        badge.create_rectangle(15, 27, 26, 37, fill=CYAN, outline=CYAN)
        badge.create_rectangle(48, 27, 59, 37, fill=CYAN, outline=CYAN)
        badge.create_oval(60, 17, 66, 23, fill=CYAN, outline=CYAN)
        title = ttk.Frame(header)
        title.pack(side="left")
        ttk.Label(title, text="SOMAIYASAT", font=("Arial", 24, "bold")).pack(anchor="w")
        ttk.Label(title, text="MISSION DATA  /  SomaiyaPod deployer", style="Muted.TLabel").pack(anchor="w", pady=(6, 0))
        ttk.Label(header, text="SYNTHETIC DEMO\nAll times UTC", foreground=AMBER,
                  justify="right").pack(side="right")

        navigation = ttk.Frame(root, padding=(16, 0, 16, 12))
        navigation.pack(fill="x")
        self.pages = {}
        self.buttons = {}
        for name in ("Overview", "Telemetry", "Communication & Events"):
            button = ttk.Button(navigation, text=name, command=lambda page=name: self.show_page(page))
            button.pack(side="left", padx=(0, 8))
            self.buttons[name] = button

        self.content = ttk.Frame(root, padding=(16, 0, 16, 16))
        self.content.pack(fill="both", expand=True)
        for name in self.buttons:
            self.pages[name] = ttk.Frame(self.content)

        self.build_overview()
        self.build_telemetry()
        self.build_communications()
        self.show_page("Overview")

    def set_style(self):
        self.root.configure(bg=BG)
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(".", background=BG, foreground=TEXT, font=("Arial", 11))
        style.configure("TFrame", background=BG)
        style.configure("TLabel", background=BG, foreground=TEXT)
        style.configure("Muted.TLabel", foreground=MUTED)
        style.configure("Card.TFrame", background=PANEL)
        style.configure("Card.TLabel", background=PANEL, foreground=MUTED)
        style.configure("Value.TLabel", background=PANEL, foreground=CYAN, font=("Arial", 24, "bold"))
        style.configure("TButton", background=PANEL, foreground=TEXT, padding=(14, 8),
                        borderwidth=0, focusthickness=2, focuscolor=CYAN)
        style.map("TButton", background=[("disabled", CYAN), ("pressed", "#355366"), ("active", "#293e50")],
                  foreground=[("disabled", BG)])
        style.configure("TEntry", fieldbackground=PANEL, foreground=TEXT, insertcolor=TEXT,
                        bordercolor="#395366", padding=6)
        style.configure("TCombobox", fieldbackground=PANEL, background=PANEL, foreground=TEXT,
                        arrowcolor=CYAN, bordercolor="#395366", padding=6)
        style.map("TCombobox", fieldbackground=[("readonly", PANEL)],
                  foreground=[("readonly", TEXT)], selectbackground=[("readonly", PANEL)],
                  selectforeground=[("readonly", TEXT)])
        self.root.option_add("*TCombobox*Listbox.background", PANEL)
        self.root.option_add("*TCombobox*Listbox.foreground", TEXT)
        self.root.option_add("*TCombobox*Listbox.selectBackground", "#355366")
        self.root.option_add("*TCombobox*Listbox.selectForeground", TEXT)
        style.configure("Treeview", background=PANEL, fieldbackground=PANEL, foreground=TEXT,
                        rowheight=28, borderwidth=0)
        style.configure("Treeview.Heading", background="#243747", foreground=MUTED,
                        font=("Arial", 10, "bold"), padding=(8, 9), relief="flat")
        style.map("Treeview", background=[("selected", "#355366")], foreground=[("selected", "#ffffff")])
        style.map("Treeview.Heading", background=[("active", "#304a5e")])
        style.configure("TScrollbar", background="#355366", troughcolor=BG,
                        arrowcolor=MUTED, borderwidth=0)

    def show_page(self, name):
        for page in self.pages.values():
            page.pack_forget()
        for title, button in self.buttons.items():
            button.state(["disabled"] if title == name else ["!disabled"])
        self.pages[name].pack(fill="both", expand=True)
        if name == "Overview":
            self.refresh_overview()
        elif name == "Telemetry":
            self.refresh_telemetry()
        else:
            self.refresh_communications()

    def build_overview(self):
        page = self.pages["Overview"]
        heading = ttk.Frame(page)
        heading.pack(fill="x", pady=(0, 10))
        ttk.Label(heading, text="Mission overview", font=("Arial", 16, "bold")).pack(side="left")
        self.summary = {"Latest reading (UTC)": tk.StringVar()}
        ttk.Button(heading, text="Refresh data", command=self.refresh_overview).pack(side="right")
        ttk.Label(heading, textvariable=self.summary["Latest reading (UTC)"],
                  style="Muted.TLabel").pack(side="right", padx=12)
        cards = ttk.Frame(page)
        cards.pack(fill="x")
        self.card_values = {}
        for index, title in enumerate(("Battery", "Temperature", "Link quality (demo score)",
                                       "Operating mode", "Pending records", "Transmission success rate")):
            card = ttk.Frame(cards, style="Card.TFrame", padding=(14, 10))
            card.grid(row=index // 3, column=index % 3, sticky="nsew", padx=4, pady=4)
            cards.columnconfigure(index % 3, weight=1, uniform="cards")
            ttk.Label(card, text=title, style="Card.TLabel").pack(anchor="w")
            value = tk.StringVar(value="N/A")
            label = ttk.Label(card, textvariable=value, style="Value.TLabel")
            label.pack(anchor="w", pady=(5, 0))
            self.summary[title] = value
            self.card_values[title] = label

        ttk.Label(page, text="BATTERY HISTORY  /  All stored readings", style="Muted.TLabel").pack(anchor="w", pady=(12, 4))
        self.battery_rows = []
        self.battery_chart = tk.Canvas(page, background=PANEL, highlightthickness=0, height=165)
        self.battery_chart.pack(fill="both", expand=True, padx=4)
        self.battery_chart.bind("<Configure>", self.draw_battery_chart)

        self.latest_event = tk.StringVar()
        ttk.Label(page, textvariable=self.latest_event, wraplength=820).pack(anchor="w", pady=(12, 8))
        ttk.Label(page, text="Counts cover all records. Success rate excludes pending records.",
                  style="Muted.TLabel").pack(anchor="w")
        ttk.Label(page, text="Demo assumption: battery below 20% = Safe mode; not a mission specification.",
                  style="Muted.TLabel").pack(anchor="w", pady=(4, 0))

    def refresh_overview(self):
        try:
            latest, pending, success, event = get_summary(self.connection)
            readings = get_telemetry(self.connection)
        except sqlite3.Error as error:
            self.show_error(error)
            return
        values = {
            "Latest reading (UTC)": latest["recorded_at"] if latest else "No readings",
            "Battery": f"{latest['battery_pct']:.1f}%" if latest else "N/A",
            "Temperature": f"{latest['temperature_c']:.1f} °C" if latest else "N/A",
            "Link quality (demo score)": f"{latest['link_quality_pct']:.1f}%" if latest else "N/A",
            "Operating mode": latest["operating_mode"] if latest else "N/A",
            "Pending records": str(pending),
            "Transmission success rate": f"{success:.1f}%" if success is not None else "N/A",
        }
        for title, value in values.items():
            self.summary[title].set(value)
        low_battery = latest is not None and latest["battery_pct"] < 20
        self.card_values["Battery"].configure(foreground=AMBER if low_battery else CYAN)
        self.card_values["Operating mode"].configure(
            foreground=AMBER if latest and latest["operating_mode"] == "Safe" else CYAN)
        self.card_values["Pending records"].configure(foreground=AMBER if pending else CYAN)
        self.battery_rows = list(reversed(readings))
        self.draw_battery_chart()
        self.latest_event.set(
            f"Latest event: {event['event_name']} ({event['component']}, {event['occurred_at']} UTC)"
            if event else "No mission events recorded."
        )

    def draw_battery_chart(self, event=None):
        chart = self.battery_chart
        chart.delete("all")
        width, height = chart.winfo_width(), chart.winfo_height()
        if width < 100 or height < 80:
            return
        if not self.battery_rows:
            chart.create_text(width / 2, height / 2, text="No battery readings yet", fill=MUTED)
            return
        left, right, top, bottom = 48, width - 20, 20, height - 30
        for value in (0, 50, 100):
            y = bottom - value / 100 * (bottom - top)
            chart.create_line(left, y, right, y, fill="#2b4050")
            chart.create_text(left - 8, y, text=f"{value}%", fill=MUTED, anchor="e", font=("Arial", 9))
        first = self.battery_rows[0]["recorded_at"]
        last = self.battery_rows[-1]["recorded_at"]
        start = datetime.strptime(first, "%Y-%m-%d %H:%M:%S")
        duration = (datetime.strptime(last, "%Y-%m-%d %H:%M:%S") - start).total_seconds()
        points = []
        for row in self.battery_rows:
            elapsed = (datetime.strptime(row["recorded_at"], "%Y-%m-%d %H:%M:%S") - start).total_seconds()
            x = left + elapsed / duration * (right - left) if duration else (left + right) / 2
            y = bottom - row["battery_pct"] / 100 * (bottom - top)
            points.extend((x, y))
        if len(points) > 2:
            chart.create_polygon(points[0], bottom, *points, points[-2], bottom, fill="#1d3e46", outline="")
            chart.create_line(*points, fill=CYAN, width=2)
        threshold = bottom - 0.2 * (bottom - top)
        chart.create_line(left, threshold, right, threshold, fill=AMBER, dash=(4, 5))
        chart.create_text(right - 4, threshold - 9, text="20% demo threshold", fill=AMBER, anchor="e", font=("Arial", 9))
        x, y = points[-2:]
        chart.create_oval(x - 3, y - 3, x + 3, y + 3, fill=CYAN, outline=PANEL)
        chart.create_text(left, height - 12, text=first[:16] + " UTC", fill=MUTED, anchor="w", font=("Arial", 9))
        chart.create_text(right, height - 12, text=last[:16] + " UTC", fill=MUTED, anchor="e", font=("Arial", 9))

    def make_table(self, parent, columns, height):
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True, pady=8)
        tree = ttk.Treeview(frame, columns=[name for name, width in columns], show="headings",
                            height=height, selectmode="browse")
        for name, width in columns:
            tree.heading(name, text=name)
            tree.column(name, width=width, minwidth=70, anchor="w")
        vertical = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        horizontal = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        tree.tag_configure("even", background=PANEL)
        tree.tag_configure("odd", background="#1e2f3e")
        tree.tag_configure("Sent", foreground=CYAN)
        tree.tag_configure("Complete", foreground=CYAN)
        tree.tag_configure("Pending", foreground=AMBER)
        tree.tag_configure("Failed", foreground="#f09191")
        tree.tag_configure("Safe", foreground=AMBER)
        tree.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        return tree

    def clear_table(self, tree):
        for item in tree.get_children():
            tree.delete(item)

    def build_telemetry(self):
        page = self.pages["Telemetry"]
        ttk.Label(page, text="Telemetry history", font=("Arial", 16, "bold")).pack(anchor="w", pady=(4, 12))
        filters = ttk.Frame(page)
        filters.pack(fill="x")
        self.start_date = tk.StringVar()
        self.end_date = tk.StringVar()
        for label, variable in (("From", self.start_date), ("To", self.end_date)):
            ttk.Label(filters, text=label).pack(side="left", padx=(0, 6))
            ttk.Entry(filters, textvariable=variable, width=13).pack(side="left", padx=(0, 12))
        ttk.Button(filters, text="Apply", command=self.refresh_telemetry).pack(side="left", padx=(0, 6))
        ttk.Button(filters, text="Clear", command=self.clear_dates).pack(side="left")
        ttk.Label(page, text="Dates: YYYY-MM-DD. Sample readings cover 2026-01-15 to 2026-01-16.").pack(anchor="w", pady=(8, 0))
        self.telemetry_table = self.make_table(page, [
            ("Time (UTC)", 190), ("Battery (%)", 120), ("Temperature (°C)", 150),
            ("Link score (%)", 140), ("Operating mode", 140)
        ], 8)
        self.telemetry_count = tk.StringVar()
        ttk.Label(page, textvariable=self.telemetry_count).pack(anchor="w")

    def clear_dates(self):
        self.start_date.set("")
        self.end_date.set("")
        self.refresh_telemetry()

    def refresh_telemetry(self):
        try:
            rows = get_telemetry(self.connection, self.start_date.get(), self.end_date.get())
        except ValueError as error:
            messagebox.showerror("Invalid dates", str(error), parent=self.root)
            return
        except sqlite3.Error as error:
            self.show_error(error)
            return
        self.clear_table(self.telemetry_table)
        for index, row in enumerate(rows):
            self.telemetry_table.insert("", "end", values=(row["recorded_at"], row["battery_pct"],
                row["temperature_c"], row["link_quality_pct"], row["operating_mode"]),
                tags=("odd" if index % 2 else "even", row["operating_mode"]))
        self.telemetry_count.set(f"{len(rows)} readings" if rows else "No readings match these dates.")

    def build_communications(self):
        page = self.pages["Communication & Events"]
        ttk.Label(page, text="Communication records", font=("Arial", 16, "bold")).pack(anchor="w", pady=(4, 12))
        filters = ttk.Frame(page)
        filters.pack(fill="x")
        self.mode = tk.StringVar(value="All")
        self.status = tk.StringVar(value="All")
        for label, variable, values in (("Mode", self.mode, MODES), ("Status", self.status, STATUSES)):
            ttk.Label(filters, text=label).pack(side="left", padx=(0, 6))
            ttk.Combobox(filters, textvariable=variable, values=("All",) + values,
                         state="readonly", width=12).pack(side="left", padx=(0, 12))
        ttk.Button(filters, text="Apply", command=self.refresh_communications).pack(side="left", padx=(0, 6))
        ttk.Button(filters, text="Clear", command=self.clear_communications).pack(side="left")
        self.communication_table = self.make_table(page, [
            ("Time (UTC)", 180), ("Mode", 90), ("Size (KB)", 100), ("Priority", 80), ("Status", 100)
        ], 4)
        self.communication_count = tk.StringVar()
        ttk.Label(page, textvariable=self.communication_count).pack(anchor="w")
        self.communication_notes = tk.StringVar(value="Select a communication record to view its notes.")
        ttk.Label(page, textvariable=self.communication_notes, wraplength=820).pack(anchor="w", pady=(4, 8))
        self.communication_table.bind("<<TreeviewSelect>>", self.select_communication)

        ttk.Label(page, text="Deployment & initialization events", font=("Arial", 13, "bold")).pack(anchor="w")
        self.event_table = self.make_table(page, [
            ("Time (UTC)", 180), ("Component", 120), ("Event", 260), ("Outcome", 100)
        ], 3)
        self.event_notes = tk.StringVar(value="Select an event to view its notes.")
        ttk.Label(page, textvariable=self.event_notes, wraplength=820).pack(anchor="w")
        self.event_table.bind("<<TreeviewSelect>>", self.select_event)
        self.communication_rows = {}
        self.event_rows = {}

    def clear_communications(self):
        self.mode.set("All")
        self.status.set("All")
        self.refresh_communications()

    def refresh_communications(self):
        try:
            rows = get_communications(self.connection, self.mode.get(), self.status.get())
            events = get_events(self.connection)
        except sqlite3.Error as error:
            self.show_error(error)
            return
        self.clear_table(self.communication_table)
        self.communication_rows = {str(row["id"]): row for row in rows}
        for index, row in enumerate(rows):
            self.communication_table.insert("", "end", iid=str(row["id"]), values=(row["created_at"],
                row["mode"], row["size_kb"], row["priority"], row["status"]),
                tags=("odd" if index % 2 else "even", row["status"]))
        self.communication_count.set(
            f"{len(rows)} records | Priority: 1 = TT&C, 2 = SSTV, 3 = Codec2 / M17"
            if rows else "No communication records match these filters."
        )
        self.communication_notes.set("Select a communication record to view its notes.")
        self.clear_table(self.event_table)
        self.event_rows = {str(row["id"]): row for row in events}
        for index, row in enumerate(events):
            self.event_table.insert("", "end", iid=str(row["id"]), values=(row["occurred_at"],
                row["component"], row["event_name"], row["outcome"]),
                tags=("odd" if index % 2 else "even", row["outcome"]))
        self.event_notes.set("Select an event to view its notes." if events else "No mission events recorded.")

    def select_communication(self, event):
        selected = self.communication_table.selection()
        if selected:
            self.communication_notes.set(self.communication_rows[selected[0]]["notes"])

    def select_event(self, event):
        selected = self.event_table.selection()
        if selected:
            self.event_notes.set(self.event_rows[selected[0]]["notes"])

    def show_error(self, error):
        messagebox.showerror("Database error", str(error), parent=self.root)
