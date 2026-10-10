import tkinter as tk
from datetime import date
from tkinter import messagebox, ttk

import db
from theme import (BLACK, F_SMALL, F_SUB, F_TINY, GOLD_SOFT, MUTED,
                   RED, WHITE, YELLOW_DARK, card, section_title)
from widgets import View, fill_table, make_table, selected_id


class ReserveView(View):
    refresh_ms = 5000
    title = "Room Reservation (Main Transaction)"

    def __init__(self, master, app):
        super().__init__(master, app)
        self.pending = None

        finder = card(self, padding=14)
        finder.pack(fill="x")
        head = tk.Frame(finder.inner, bg=WHITE)
        head.pack(fill="x", pady=(0, 8))
        section_title(head, "Find a Room").pack(side="left")
        tk.Label(head, text="dates are YYYY-MM-DD", font=F_TINY, bg=WHITE,
                 fg=MUTED).pack(side="left", padx=8)

        row = tk.Frame(finder.inner, bg=WHITE)
        row.pack(fill="x")
        tk.Label(row, text="Date", font=F_SUB, bg=WHITE, fg=BLACK).pack(side="left")
        self.date_var = tk.StringVar(value=date.today().isoformat())
        ttk.Entry(row, textvariable=self.date_var, width=12).pack(
            side="left", padx=(8, 18))

        tk.Label(row, text="Time Slot", font=F_SUB, bg=WHITE, fg=BLACK).pack(side="left")
        self.slot_var = tk.StringVar(value=db.TIME_SLOTS[1])
        ttk.Combobox(row, textvariable=self.slot_var, values=db.TIME_SLOTS,
                     state="readonly", width=13).pack(side="left", padx=8)

        ttk.Button(row, text="Clear", style="Outline.TButton",
                   command=self.clear_search).pack(side="right")
        ttk.Button(row, text="Search", style="Primary.TButton",
                   command=self.refresh_now).pack(side="right", padx=6)

        body = tk.Frame(self, bg=self["bg"])
        body.pack(fill="both", expand=True, pady=12)
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=2, minsize=260)
        body.rowconfigure(0, weight=1)

        left = card(body, padding=14)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        section_title(left.inner, "Available Rooms  (auto-refresh)").pack(
            anchor="w", pady=(0, 8))
        frame, self.table = make_table(left.inner, [
            ("room_id", "Room", 80, "center"),
            ("floor", "Floor", 110, "center"),
            ("occupancy", "Occupancy", 90, "center"),
            ("status", "Status", 85, "center"),
        ], height=9)
        self.table.bind("<Double-1>", lambda _e: self.choose_room())

        actions = tk.Frame(left.inner, bg=WHITE)
        actions.pack(side="bottom", fill="x", pady=(10, 0))
        ttk.Button(actions, text="Reserve", style="Primary.TButton",
                   command=self.choose_room).pack(side="left")
        self.notice = tk.Label(actions, text="", font=F_SMALL, bg=WHITE, fg=RED,
                               anchor="w")
        self.notice.pack(side="left", padx=12, fill="x", expand=True)
        frame.pack(fill="both", expand=True)

        right = tk.Frame(body, bg=self["bg"])
        right.grid(row=0, column=1, sticky="nsew")

        summary = card(right, padding=14)
        summary.pack(fill="x")
        section_title(summary.inner, "Reservation Summary").pack(anchor="w",
                                                                 pady=(0, 8))
        self.summary = {}
        for key, label in (("room", "Room"), ("date", "Date"),
                           ("slot", "Time Slot"), ("by", "Reserved by")):
            line = tk.Frame(summary.inner, bg=WHITE)
            line.pack(fill="x", pady=1)
            tk.Label(line, text=label, font=F_SMALL, bg=WHITE, fg=MUTED,
                     width=11, anchor="w").pack(side="left")
            value = tk.Label(line, text="-", font=F_SUB, bg=WHITE, fg=BLACK,
                             anchor="w")
            value.pack(side="left", fill="x", expand=True)
            self.summary[key] = value

        tk.Label(summary.inner,
                 text="Slot is checked for double-booking on confirm.",
                 font=F_TINY, bg=GOLD_SOFT, fg=BLACK, anchor="w",
                 padx=8, pady=5).pack(fill="x", pady=(10, 10))

        buttons = tk.Frame(summary.inner, bg=WHITE)
        buttons.pack(fill="x")
        ttk.Button(buttons, text="Confirm", style="Primary.TButton",
                   command=self.confirm).pack(side="left")
        ttk.Button(buttons, text="Cancel", style="Outline.TButton",
                   command=self.clear_pending).pack(side="left", padx=8)

        mine = card(right, padding=14)
        mine.pack(fill="both", expand=True, pady=(12, 0))
        section_title(mine.inner, "My Reservations").pack(anchor="w", pady=(0, 8))
        frame2, self.mine = make_table(mine.inner, [
            ("room_id", "Room", 80, "center"),
            ("time_slot", "Time Slot", 95, "center"),
            ("status", "Status", 80, "center"),
        ], height=4)

        row2 = tk.Frame(mine.inner, bg=WHITE)
        row2.pack(side="bottom", fill="x", pady=(10, 0))
        ttk.Button(row2, text="Check In", style="Gold.TButton",
                   command=self.check_in).pack(side="left")
        ttk.Button(row2, text="Cancel Reservation", style="Outline.TButton",
                   command=self.cancel_mine).pack(side="left", padx=8)
        frame2.pack(fill="both", expand=True)

    @property
    def chosen_date(self):
        return db.parse_date(self.date_var.get())

    def clear_search(self):
        self.date_var.set(date.today().isoformat())
        self.slot_var.set(db.TIME_SLOTS[1])
        self.clear_pending()
        self.refresh_now()

    def refresh(self):
        rows = db.rooms_for_slot(self.chosen_date, self.slot_var.get())
        fill_table(self.table, rows,
                   ["room_id", "floor", "occupancy", "status"],
                   "room_id", status_key="status")
        own = db.list_reservations(user_id=self.app.user["user_id"],
                                   include_cancelled=False)
        fill_table(self.mine, own, ["room_id", "time_slot", "status"],
                   "reservation_id", status_key="status")

    def choose_room(self):
        room_id = selected_id(self.table)
        if not room_id:
            self.notice.config(text="Select a room from the table first.", fg=RED)
            return
        if self.chosen_date is None:
            self.notice.config(text="Enter the date as YYYY-MM-DD.", fg=RED)
            return
        values = self.table.item(room_id, "values")
        if values and values[3] != "Available":
            self.notice.config(
                text="Room Unavailable - please select another room.", fg=RED)
            return
        self.pending = room_id
        self.summary["room"].config(
            text=f"{room_id}  ({db.floor_of(room_id)})")
        self.summary["date"].config(text=self.chosen_date.isoformat())
        self.summary["slot"].config(text=self.slot_var.get())
        self.summary["by"].config(text=self.app.user["user_id"])
        self.notice.config(text="Review the summary, then press Confirm.",
                           fg=YELLOW_DARK)

    def clear_pending(self):
        self.pending = None
        for value in self.summary.values():
            value.config(text="-")
        self.notice.config(text="")

    def confirm(self):
        if not self.pending:
            self.notice.config(text="Press Reserve on a room first.", fg=RED)
            return
        ok, note = db.reserve_room(self.pending, self.app.user["user_id"],
                                   self.date_var.get(), self.slot_var.get())
        self.notice.config(text=note, fg=YELLOW_DARK if ok else RED)
        if ok:
            self.clear_pending()
            self.notice.config(text="Reservation confirmed. Room status updated.",
                               fg=YELLOW_DARK)
        self.refresh_now()

    def check_in(self):
        chosen = selected_id(self.mine)
        if not chosen:
            messagebox.showinfo("Check In", "Select one of your reservations.")
            return
        ok, note = db.check_in(int(chosen), self.app.user["user_id"])
        if ok:
            messagebox.showinfo("Check In", note)
        else:
            messagebox.showerror("Check In", note)
        self.refresh_now()

    def cancel_mine(self):
        chosen = selected_id(self.mine)
        if not chosen:
            messagebox.showinfo("Cancel Reservation",
                                "Select one of your reservations.")
            return
        if not messagebox.askyesno("Cancel Reservation",
                                   "Cancel this reservation?"):
            return
        ok, note = db.cancel_reservation(int(chosen), self.app.user["user_id"])
        if ok:
            messagebox.showinfo("Cancel Reservation", note)
        else:
            messagebox.showerror("Cancel Reservation", note)
        self.refresh_now()