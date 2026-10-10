import tkinter as tk
from datetime import date, timedelta
from tkinter import ttk

import db
from theme import (BLACK, F_SUB, F_TINY, MUTED, WHITE, card, section_title)
from widgets import BarChart, LineChart, View, fill_table, make_table

REPORT_TYPES = [
    "Room Status & Occupancy",
    "Reservations per Day",
    "Check-ins per Room",
]


class ReportsView(View):
    refresh_ms = None
    title = "Reports"

    def __init__(self, master, app):
        super().__init__(master, app)

        filters = card(self, padding=14)
        filters.pack(fill="x")
        section_title(filters.inner, "Report Filters").pack(anchor="w",
                                                            pady=(0, 8))
        row = tk.Frame(filters.inner, bg=WHITE)
        row.pack(fill="x")

        tk.Label(row, text="Report Type", font=F_SUB, bg=WHITE,
                 fg=BLACK).pack(side="left")
        self.kind = tk.StringVar(value=REPORT_TYPES[0])
        ttk.Combobox(row, textvariable=self.kind, values=REPORT_TYPES,
                     state="readonly", width=24).pack(side="left", padx=(8, 20))

        today = date.today()
        self.date_from = tk.StringVar(value=(today - timedelta(days=6)).isoformat())
        self.date_to = tk.StringVar(value=today.isoformat())
        tk.Label(row, text="From", font=F_SUB, bg=WHITE, fg=BLACK).pack(side="left")
        ttk.Entry(row, textvariable=self.date_from, width=13).pack(side="left", padx=8)
        tk.Label(row, text="To", font=F_SUB, bg=WHITE, fg=BLACK).pack(side="left")
        ttk.Entry(row, textvariable=self.date_to, width=13).pack(side="left", padx=8)
        ttk.Button(row, text="Generate", style="Primary.TButton",
                   command=self.refresh_now).pack(side="left", padx=12)
        self.note = tk.Label(filters.inner, text="", font=F_TINY, bg=WHITE,
                             fg=MUTED, anchor="w")
        self.note.pack(fill="x", pady=(6, 0))

        charts = tk.Frame(self, bg=self["bg"])
        charts.pack(fill="x", pady=12)
        charts.columnconfigure(0, weight=1, uniform="c")
        charts.columnconfigure(1, weight=1, uniform="c")

        left = card(charts, padding=14)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.line = LineChart(left.inner, "Reservations per Day", height=180)
        self.line.pack(fill="both", expand=True)

        right = card(charts, padding=14)
        right.grid(row=0, column=1, sticky="nsew")
        self.bar = BarChart(right.inner, "Occupancy Count per Room", height=180,
                            orient="horizontal")
        self.bar.pack(fill="both", expand=True)

        table_card = card(self, padding=14)
        table_card.pack(fill="both", expand=True)
        section_title(table_card.inner, "Summary Table").pack(anchor="w",
                                                              pady=(0, 8))
        frame, self.table = make_table(table_card.inner, [
            ("room_id", "Room", 95, "center"),
            ("status", "Status", 95, "center"),
            ("occupancy_count", "Occupancy Count", 115, "center"),
            ("total_reservations", "Total Reservations", 125, "center"),
            ("check_ins", "Check-ins", 90, "center"),
        ], height=8)
        frame.pack(fill="both", expand=True)

    def refresh(self):
        start = db.parse_date(self.date_from.get())
        end = db.parse_date(self.date_to.get())
        if self.date_from.get().strip() and start is None:
            self.note.config(text="'From' is not a valid date (YYYY-MM-DD).")
            return
        if self.date_to.get().strip() and end is None:
            self.note.config(text="'To' is not a valid date (YYYY-MM-DD).")
            return

        rows = db.report_summary(start, end)
        fill_table(self.table, rows,
                   ["room_id", "status", "occupancy_count",
                    "total_reservations", "check_ins"],
                   "room_id", status_key="status")

        self.line.set_data([(r["day"][5:], r["total"])
                            for r in db.reservations_per_day(start, end)])

        kind = self.kind.get()
        if kind == "Check-ins per Room":
            data = [(r["room_id"], r["total"])
                    for r in db.check_ins_per_room(start, end)][:8]
            caption = "Check-ins per Room"
        elif kind == "Reservations per Day":
            data = [(r["room_id"], r["total_reservations"]) for r in rows
                    if r["total_reservations"]][:8]
            caption = "Reservations per Room"
        else:
            data = [(r["room_id"], r["occupancy_count"])
                    for r in db.occupancy_per_room(8)]
            caption = "Occupancy Count per Room"
        self.bar.set_data(data)
        self.bar.title_text(caption)

        span = f"{start or 'start'} to {end or 'today'}"
        self.note.config(text=f"{kind}  -  {span}  -  {len(rows)} room(s)")
