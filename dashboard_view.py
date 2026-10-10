import tkinter as tk
from datetime import date
from tkinter import messagebox, ttk

import db
from theme import (BLACK, F_BODY, F_SMALL, F_SUB, MUTED, RED, WHITE,
                   YELLOW_DARK, card, section_title)
from widgets import (BarChart, StatCard, View, center_on, fill_table,
                     make_table, selected_id)


class DashboardView(View):
    refresh_ms = 5000
    title = "Dashboard"

    def __init__(self, master, app):
        super().__init__(master, app)
        self.is_admin = app.user["role"] == "Admin"

        cards = tk.Frame(self, bg=self["bg"])
        cards.pack(fill="x")
        self.cards = {}
        for key, caption, colour in (
            ("total_rooms", "Total Rooms", BLACK),
            ("available_rooms", "Available", YELLOW_DARK),
            ("occupied_rooms", "Occupied", RED),
            ("reservations_today", "Reservations Today", BLACK),
        ):
            box = StatCard(cards, caption, colour)
            box.pack(side="left", fill="both", expand=True, padx=(0, 10))
            self.cards[key] = box

        chart_card = card(self, padding=14)
        chart_card.pack(fill="x", pady=(12, 0))
        head = tk.Frame(chart_card.inner, bg=WHITE)
        head.pack(fill="x")
        section_title(head, "Occupancy Count per Room").pack(side="left")
        if self.is_admin:
            ttk.Button(head, text="Update Occupancy", style="Small.Outline.TButton",
                       command=self.update_occupancy).pack(side="right")
        ttk.Button(head, text="Reserve a Room", style="Small.Primary.TButton",
                   command=lambda: self.app.go("Reserve a Room")).pack(
            side="right", padx=6)
        self.chart = BarChart(chart_card.inner, "", height=170)
        self.chart.pack(fill="both", expand=True, pady=(10, 0))

        table_card = card(self, padding=14)
        table_card.pack(fill="both", expand=True, pady=12)
        bar = tk.Frame(table_card.inner, bg=WHITE)
        bar.pack(fill="x", pady=(0, 8))
        section_title(bar, "Today's Reservations").pack(side="left")
        tk.Label(bar, text=date.today().strftime("%b %d, %Y"), font=F_SMALL,
                 bg=WHITE, fg=MUTED).pack(side="left", padx=10)
        if self.is_admin:
            ttk.Button(bar, text="Cancel Selected", style="Small.Outline.TButton",
                       command=self.cancel_selected).pack(side="right")

        frame, self.table = make_table(table_card.inner, [
            ("room_id", "Room", 90, "center"),
            ("user_id", "Reserved By", 100, "center"),
            ("date", "Date", 95, "center"),
            ("time_slot", "Time Slot", 105, "center"),
            ("status", "Status", 95, "center"),
        ], height=7)
        frame.pack(fill="both", expand=True)

    def refresh(self):
        counts = db.dashboard_counts()
        for key, box in self.cards.items():
            box.set(counts[key])
        self.chart.set_data([(r["room_id"], r["occupancy_count"])
                             for r in db.occupancy_per_room(8)])
        rows = db.list_reservations(on_date=date.today())
        fill_table(self.table, rows,
                   ["room_id", "user_id", "date", "time_slot", "status"],
                   "reservation_id", status_key="status")

    def cancel_selected(self):
        chosen = selected_id(self.table)
        if not chosen:
            messagebox.showinfo("Cancel reservation",
                                "Select a reservation from the table first.")
            return
        if not messagebox.askyesno("Cancel reservation",
                                   "Cancel this reservation?"):
            return
        ok, note = db.cancel_reservation(int(chosen))
        if ok:
            messagebox.showinfo("Cancel reservation", note)
        else:
            messagebox.showerror("Cancel reservation", note)
        self.refresh_now()

    def update_occupancy(self):
        OccupancyDialog(self, on_saved=self.refresh_now)


class OccupancyDialog(tk.Toplevel):

    def __init__(self, master, on_saved):
        super().__init__(master)
        self.on_saved = on_saved
        self.title("Update Occupancy")
        self.configure(bg=WHITE)
        self.resizable(False, False)
        self.transient(master.winfo_toplevel())

        body = tk.Frame(self, bg=WHITE, padx=24, pady=20)
        body.pack()
        tk.Label(body, text="Update Occupancy Count", font=F_SUB, bg=WHITE,
                 fg=BLACK).pack(anchor="w", pady=(0, 10))

        self.rooms = {r["room_name"]: dict(r) for r in db.list_rooms()}
        self.room = tk.StringVar(value=next(iter(self.rooms), ""))
        chooser = ttk.Combobox(body, textvariable=self.room,
                               values=list(self.rooms), state="readonly",
                               width=28)
        chooser.pack(fill="x")
        chooser.bind("<<ComboboxSelected>>", lambda _e: self.load_room())

        tk.Label(body, text="Occupancy Count", font=F_BODY, bg=WHITE, fg=BLACK,
                 anchor="w").pack(fill="x", pady=(12, 2))
        self.count = tk.StringVar(value="0")

        self.spin = ttk.Spinbox(body, from_=0, to=db.DEFAULT_CAPACITY,
                                textvariable=self.count, width=8)
        self.spin.pack(anchor="w")
        self.seats = tk.Label(body, text="", font=F_SMALL, bg=WHITE, fg=MUTED,
                              anchor="w")
        self.seats.pack(fill="x", pady=(3, 0))
        self.load_room()

        row = tk.Frame(body, bg=WHITE)
        row.pack(fill="x", pady=(16, 0))
        ttk.Button(row, text="Save", style="Primary.TButton",
                   command=self.save).pack(side="left")
        ttk.Button(row, text="Cancel", style="Outline.TButton",
                   command=self.destroy).pack(side="left", padx=8)

        center_on(self, master)
        self.grab_set()

    def load_room(self):
        room = self.rooms.get(self.room.get())
        if room is None:
            return
        self.spin.configure(to=room["capacity"])
        self.count.set(str(room["occupancy_count"]))
        self.seats.config(text=f"{room['room_id']} seats {room['capacity']} people")

    def save(self):
        room = self.rooms.get(self.room.get())
        room_id = room["room_id"] if room else None
        if not room_id:
            messagebox.showerror("Update Occupancy", "Select a room.", parent=self)
            return
        ok, note = db.set_occupancy(room_id, self.count.get())
        if not ok:
            messagebox.showerror("Update Occupancy", note, parent=self)
            return
        self.on_saved()
        self.destroy()