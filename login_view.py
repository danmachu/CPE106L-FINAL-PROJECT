import tkinter as tk
from tkinter import ttk

import db
from theme import (BG, BLACK, BORDER, F_BODY, F_SMALL, F_SUB, F_TINY, F_TITLE,
                   MUTED, RED, WHITE, YELLOW)
from widgets import center_on, load_image


class LoginScreen(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master, bg=BG)
        self.app = app

        shell = tk.Frame(self, bg=BG)
        shell.place(relx=0.5, rely=0.5, anchor="center")

        outer = tk.Frame(shell, bg=BORDER, padx=1, pady=1)
        outer.pack()
        panel = tk.Frame(outer, bg=WHITE)
        panel.pack()

        strip = tk.Frame(panel, bg=YELLOW, height=5)
        strip.pack(fill="x")
        tk.Frame(strip, bg=RED, height=5, width=250).pack(side="left")

        body = tk.Frame(panel, bg=WHITE, padx=42, pady=30)
        body.pack()

        self.logo_image = load_image("rams_logo.png",
                                     max_width=280, max_height=160)
        if self.logo_image is not None:
            tk.Label(body, image=self.logo_image, bg=WHITE).pack(pady=(0, 10))
        else:
            logo = tk.Frame(body, bg=WHITE, highlightbackground=BORDER,
                            highlightthickness=1, width=92, height=46)
            logo.pack(pady=(0, 14))
            logo.pack_propagate(False)
            tk.Label(logo, text="LOGO", font=F_TINY, bg=WHITE,
                     fg=MUTED).pack(expand=True)

        tk.Label(body, text="Room Availability Monitoring System", font=F_TITLE,
                 bg=WHITE, fg=BLACK).pack()
        tk.Label(body, text="Sign in to continue", font=F_SMALL, bg=WHITE,
                 fg=MUTED).pack(pady=(2, 18))

        tk.Label(body, text="Login as", font=F_SUB, bg=WHITE, fg=BLACK,
                 anchor="w").pack(fill="x")
        self.role = tk.StringVar(value="Student")
        roles = tk.Frame(body, bg=WHITE)
        roles.pack(fill="x", pady=(4, 12))
        for name in ("Student", "Admin"):
            ttk.Radiobutton(roles, text=name, value=name,
                            variable=self.role).pack(side="left", padx=(0, 22))

        self.user_id = self._field(body, "User ID", "Enter your User ID")
        self.password = self._field(body, "Password", "Enter your password",
                                    secret=True)
        self.password.bind("<Return>", lambda _e: self.sign_in())

        ttk.Button(body, text="LOGIN", style="Primary.TButton",
                   command=self.sign_in).pack(fill="x", pady=(16, 6))
        tk.Label(body, text="or", font=F_TINY, bg=WHITE, fg=MUTED).pack()
        ttk.Button(body, text="CREATE ACCOUNT", style="Outline.TButton",
                   command=self.open_register).pack(fill="x", pady=(6, 4))

        self.message = tk.Label(body, text="", font=F_SMALL, bg=WHITE, fg=RED,
                                wraplength=300)
        self.message.pack(pady=(8, 0))

        self.user_id.focus_set()

    def _field(self, parent, label, placeholder, secret=False):
        tk.Label(parent, text=label, font=F_SUB, bg=WHITE, fg=BLACK,
                 anchor="w").pack(fill="x", pady=(6, 2))
        entry = ttk.Entry(parent, width=34, font=F_BODY,
                          show="*" if secret else "")
        entry.pack(fill="x")
        if not secret:
            entry.insert(0, "")
        entry.configure(foreground=BLACK)
        return entry

    def sign_in(self):
        user, error = db.login(self.user_id.get(), self.password.get(),
                               self.role.get())
        if user is None:
            self.message.config(text=error)
            self.password.delete(0, "end")
            return
        self.message.config(text="")
        self.app.open_workspace(user)

    def open_register(self):
        RegisterDialog(self, self.app, prefill=self.user_id.get(),
                       role=self.role.get())


class RegisterDialog(tk.Toplevel):

    def __init__(self, master, app, prefill="", role="Student"):
        super().__init__(master)
        self.app = app
        self.title("Create Account")
        self.configure(bg=WHITE)
        self.resizable(False, False)
        self.transient(master.winfo_toplevel())

        strip = tk.Frame(self, bg=YELLOW, height=4)
        strip.pack(fill="x")
        tk.Frame(strip, bg=RED, height=4, width=140).pack(side="left")

        body = tk.Frame(self, bg=WHITE, padx=28, pady=22)
        body.pack()
        tk.Label(body, text="Create Account", font=F_TITLE, bg=WHITE,
                 fg=BLACK).pack(anchor="w")
        tk.Label(body, text="Register a new RAMS user", font=F_SMALL, bg=WHITE,
                 fg=MUTED).pack(anchor="w", pady=(2, 14))

        self.user_id = self._row(body, "User ID  (e.g. 2024-1123)")
        self.user_id.insert(0, prefill)
        self.name = self._row(body, "Full Name")

        tk.Label(body, text="Role", font=F_SUB, bg=WHITE, fg=BLACK,
                 anchor="w").pack(fill="x", pady=(8, 2))
        self.role = tk.StringVar(value=role)
        roles = tk.Frame(body, bg=WHITE)
        roles.pack(fill="x")
        for name in ("Student", "Admin"):
            ttk.Radiobutton(roles, text=name, value=name,
                            variable=self.role).pack(side="left", padx=(0, 22))

        self.password = self._row(body, "Password", secret=True)
        self.confirm = self._row(body, "Confirm Password", secret=True)

        buttons = tk.Frame(body, bg=WHITE)
        buttons.pack(fill="x", pady=(18, 0))
        ttk.Button(buttons, text="Create Account", style="Primary.TButton",
                   command=self.submit).pack(side="left")
        ttk.Button(buttons, text="Cancel", style="Outline.TButton",
                   command=self.destroy).pack(side="left", padx=8)

        self.message = tk.Label(body, text="", font=F_SMALL, bg=WHITE, fg=RED,
                                wraplength=280, justify="left")
        self.message.pack(anchor="w", pady=(10, 0))

        center_on(self, master)
        self.grab_set()
        self.user_id.focus_set()

    def _row(self, parent, label, secret=False):
        tk.Label(parent, text=label, font=F_SUB, bg=WHITE, fg=BLACK,
                 anchor="w").pack(fill="x", pady=(8, 2))
        entry = ttk.Entry(parent, width=30, font=F_BODY,
                          show="*" if secret else "")
        entry.pack(fill="x")
        return entry

    def submit(self):
        if self.password.get() != self.confirm.get():
            self.message.config(text="The two passwords do not match.", fg=RED)
            return
        ok, note = db.create_account(self.user_id.get(), self.name.get(),
                                     self.role.get(), self.password.get())
        if not ok:
            self.message.config(text=note, fg=RED)
            return
        self.message.config(text=note, fg=BLACK)
        self.after(700, self.destroy)