import tkinter as tk
from tkinter import messagebox, ttk

import db
from theme import (BLACK, F_SMALL, F_SUB, F_TINY, GOLD_SOFT, MUTED, RED, WHITE,
                   card, section_title)
from widgets import View, fill_table, make_table, selected_id


class RecordsView(View):

    refresh_ms = None
    title = "Room Records Management"

    def __init__(self, master, app):
        super().__init__(master, app)
        self.editing = None

        top = card(self, padding=12)
        top.pack(fill="x")
        row = tk.Frame(top.inner, bg=WHITE)
        row.pack(fill="x")
        self.search = tk.StringVar()
        entry = ttk.Entry(row, textvariable=self.search, width=30)
        entry.pack(side="left")
        entry.bind("<Return>", lambda _e: self.refresh_now())
        tk.Label(row, text="Search room ID or name", font=F_TINY, bg=WHITE,
                 fg=MUTED).pack(side="left", padx=8)

        self.filter = tk.StringVar(value="All")
        ttk.Combobox(row, textvariable=self.filter,
                     values=["All"] + db.ROOM_STATUSES, state="readonly",
                     width=12).pack(side="left", padx=(10, 6))
        ttk.Button(row, text="Apply", style="Outline.TButton",
                   command=self.refresh_now).pack(side="left")
        ttk.Button(row, text="+  Add Room", style="Primary.TButton",
                   command=self.new_room).pack(side="right")

        body = tk.Frame(self, bg=self["bg"])
        body.pack(fill="both", expand=True, pady=12)
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=1, minsize=250)
        body.rowconfigure(0, weight=1)

        left = card(body, padding=14)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        section_title(left.inner, "Room Records").pack(anchor="w", pady=(0, 8))
        frame, self.table = make_table(left.inner, [
            ("room_id", "Room ID", 70, "center"),
            ("room_name", "Room Name", 165, "w"),
            ("status", "Status", 90, "center"),
            ("capacity", "Capacity", 75, "center"),
            ("occupancy_count", "Occupancy", 85, "center"),
        ], height=13)
        frame.pack(fill="both", expand=True)
        self.table.bind("<<TreeviewSelect>>", lambda _e: self.load_selected())
        self.count = tk.Label(left.inner, text="", font=F_TINY, bg=WHITE, fg=MUTED)
        self.count.pack(anchor="e", pady=(6, 0))

        form = card(body, padding=14)
        form.grid(row=0, column=1, sticky="nsew")
        self.form_title = section_title(form.inner, "Add Room")
        self.form_title.pack(anchor="w", pady=(0, 8))

        self.room_id = tk.StringVar()
        self.room_name = tk.StringVar()
        self.status = tk.StringVar(value="Available")
        self.capacity = tk.StringVar(value=str(db.DEFAULT_CAPACITY))
        self.occupancy = tk.StringVar(value="0")

        self._label(form.inner, "Room ID")
        ttk.Entry(form.inner, textvariable=self.room_id,
                  state="readonly").pack(fill="x")
        tk.Label(form.inner, text="Auto-generated", font=F_TINY, bg=WHITE,
                 fg=MUTED, anchor="w").pack(fill="x")

        self._label(form.inner, "Room Name")
        ttk.Entry(form.inner, textvariable=self.room_name).pack(fill="x")

        self._label(form.inner, "Availability Status")
        ttk.Combobox(form.inner, textvariable=self.status,
                     values=db.ROOM_STATUSES, state="readonly").pack(fill="x")

        self._label(form.inner, "Capacity  (how many the room seats)")
        ttk.Spinbox(form.inner, from_=1, to=db.MAX_CAPACITY,
                    textvariable=self.capacity).pack(fill="x")

        self._label(form.inner, "Occupancy Count  (people inside now)")
        ttk.Spinbox(form.inner, from_=0, to=db.MAX_CAPACITY,
                    textvariable=self.occupancy).pack(fill="x")

        tk.Label(form.inner, text="Updates reach students in near real-time.",
                 font=F_TINY, bg=GOLD_SOFT, fg=BLACK, anchor="w", padx=8,
                 pady=5).pack(fill="x", pady=(12, 10))

        ttk.Button(form.inner, text="Save Record", style="Primary.TButton",
                   command=self.save).pack(fill="x", pady=2)
        ttk.Button(form.inner, text="Clear Form", style="Outline.TButton",
                   command=self.new_room).pack(fill="x", pady=2)
        ttk.Button(form.inner, text="Delete Selected", style="Dark.TButton",
                   command=self.delete).pack(fill="x", pady=2)

        self.message = tk.Label(form.inner, text="", font=F_SMALL, bg=WHITE,
                                fg=RED, wraplength=210, justify="left")
        self.message.pack(fill="x", pady=(8, 0))

        self.new_room()

    def _label(self, parent, text):
        tk.Label(parent, text=text, font=F_SUB, bg=WHITE, fg=BLACK,
                 anchor="w").pack(fill="x", pady=(8, 2))

    def refresh(self):
        rows = db.list_rooms(self.search.get(), self.filter.get())
        fill_table(self.table, rows,
                   ["room_id", "room_name", "status", "capacity", "occupancy_count"],
                   "room_id", status_key="status")
        self.count.config(text=f"{len(rows)} room record(s)")

    def new_room(self):
        self.editing = None
        self.table.selection_remove(*self.table.selection())
        self.room_name.set("")
        self.status.set("Available")
        self.capacity.set(str(db.DEFAULT_CAPACITY))
        self.occupancy.set("0")
        self.room_id.set(db.next_room_id())
        self.form_title.config(text="Add Room")
        self.message.config(text="")

    def load_selected(self):
        room_id = selected_id(self.table)
        if not room_id:
            return
        room = db.get_room(room_id)
        if room is None:
            return
        self.editing = room_id
        self.room_id.set(room["room_id"])
        self.room_name.set(room["room_name"])
        self.status.set(room["status"])
        self.capacity.set(str(room["capacity"]))
        self.occupancy.set(str(room["occupancy_count"]))
        self.form_title.config(text="Edit Room")
        self.message.config(text="")

    def save(self):
        if self.editing:
            ok, note = db.update_room(self.editing, self.room_name.get(),
                                      self.status.get(), self.occupancy.get(),
                                      self.capacity.get())
        else:
            room_id = db.next_room_id(self.room_name.get())
            self.room_id.set(room_id)
            ok, note = db.add_room(room_id, self.room_name.get(),
                                   self.status.get(), self.occupancy.get(),
                                   self.capacity.get())
        self.message.config(text=note, fg=BLACK if ok else RED)
        if ok:
            self.refresh_now()
            if not self.editing:
                self.new_room()
                self.message.config(text=note, fg=BLACK)

    def delete(self):
        room_id = selected_id(self.table) or self.editing
        if not room_id:
            self.message.config(text="Select a room record first.", fg=RED)
            return
        room = db.get_room(room_id)
        if not messagebox.askyesno(
                "Delete room",
                f"Delete {room['room_name']} and all of its reservations?"):
            return
        db.delete_room(room_id)
        self.new_room()
        self.refresh_now()
        self.message.config(text="Room deleted.", fg=BLACK)