import tkinter as tk
from tkinter import ttk

import db
from theme import (BLACK, F_SMALL, F_SUB, F_TINY, MUTED, RED, WHITE, card,
                   section_title)
from widgets import View


class ProfileView(View):
    refresh_ms = None
    title = "User Profile"

    def __init__(self, master, app):
        super().__init__(master, app)

        panel = card(self, padding=20)
        panel.pack(fill="x")
        section_title(panel.inner, "Account Information").pack(anchor="w",
                                                               pady=(0, 14))

        grid = tk.Frame(panel.inner, bg=WHITE)
        grid.pack(fill="x")
        grid.columnconfigure(0, weight=1, uniform="p")
        grid.columnconfigure(1, weight=1, uniform="p")

        self.name = tk.StringVar()
        self.user_id = tk.StringVar()
        self.role = tk.StringVar()
        self.password = tk.StringVar()

        self._field(grid, 0, 0, "Full Name", self.name)
        self._field(grid, 0, 1, "User ID", self.user_id, readonly=True)
        self._field(grid, 1, 0, "Role", self.role, readonly=True)
        self._field(grid, 1, 1, "Password", self.password, secret=True)
        tk.Label(grid, text="Leave the password blank to keep the current one.",
                 font=F_TINY, bg=WHITE, fg=MUTED, anchor="w").grid(
            row=2, column=1, sticky="w", padx=(10, 0))

        buttons = tk.Frame(panel.inner, bg=WHITE)
        buttons.pack(fill="x", pady=(20, 0))
        ttk.Button(buttons, text="Save Changes", style="Primary.TButton",
                   command=self.save).pack(side="left")
        ttk.Button(buttons, text="Cancel", style="Outline.TButton",
                   command=self.refresh).pack(side="left", padx=8)

        self.message = tk.Label(panel.inner, text="", font=F_SMALL, bg=WHITE,
                                fg=RED, anchor="w")
        self.message.pack(fill="x", pady=(10, 0))

    def _field(self, parent, row, column, label, variable, readonly=False,
               secret=False):
        box = tk.Frame(parent, bg=WHITE)
        box.grid(row=row, column=column, sticky="ew",
                 padx=(0, 10) if column == 0 else (10, 0), pady=(0, 12))
        tk.Label(box, text=label, font=F_SUB, bg=WHITE, fg=BLACK,
                 anchor="w").pack(fill="x", pady=(0, 3))
        entry = ttk.Entry(box, textvariable=variable, show="*" if secret else "",
                          state="readonly" if readonly else "normal")
        entry.pack(fill="x")
        return entry

    def refresh(self):
        user = db.get_user(self.app.user["user_id"]) or self.app.user
        self.name.set(user["name"])
        self.user_id.set(user["user_id"])
        self.role.set(user["role"])
        self.password.set("")
        self.message.config(text="")

    def save(self):
        ok, note = db.update_profile(self.app.user["user_id"], self.name.get(),
                                     self.password.get().strip() or None)
        self.message.config(text=note, fg=BLACK if ok else RED)
        if ok:
            self.app.reload_user()
            self.refresh()
            self.message.config(text=note, fg=BLACK)