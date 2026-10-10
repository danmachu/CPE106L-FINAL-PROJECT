import tkinter as tk
from tkinter import ttk


RED = "#A6192E"
RED_HOVER = "#C01F38"
RED_DARK = "#7E1322"
BLACK = "#161616"
BLACK_SOFT = "#242424"
BLACK_HOVER = "#333333"
YELLOW = "#F5B301"
YELLOW_DARK = "#B98500"
GOLD_SOFT = "#F7E3B0"
WHITE = "#FFFFFF"

BG = "#F2F3F5"
BORDER = "#D9D9D9"
TEXT = "#161616"
MUTED = "#6E6E6E"


FAMILY = "Arial"
F_TITLE = (FAMILY, 17, "bold")
F_HEAD = (FAMILY, 12, "bold")
F_SUB = (FAMILY, 10, "bold")
F_BODY = (FAMILY, 10)
F_SMALL = (FAMILY, 9)
F_TINY = (FAMILY, 8)
F_STAT = (FAMILY, 24, "bold")
F_BRAND = (FAMILY, 19, "bold")


def apply_theme(root):
    root.configure(bg=BG)
    style = ttk.Style(root)
    style.theme_use("clam")

    style.configure("TFrame", background=BG)
    style.configure("Card.TFrame", background=WHITE)
    style.configure("TLabel", background=BG, foreground=TEXT, font=F_BODY)

    base = dict(font=F_SUB, borderwidth=1, focusthickness=0, padding=(14, 7))

    style.configure("Primary.TButton", background=RED, foreground=WHITE,
                    bordercolor=RED, lightcolor=RED, darkcolor=RED, **base)
    style.map("Primary.TButton",
              background=[("pressed", RED_DARK), ("active", RED_HOVER)],
              bordercolor=[("pressed", RED_DARK), ("active", RED_HOVER)],
              lightcolor=[("active", RED_HOVER)], darkcolor=[("active", RED_HOVER)],
              foreground=[("disabled", "#E3B9C0")])

    style.configure("Gold.TButton", background=YELLOW, foreground=BLACK,
                    bordercolor=YELLOW, lightcolor=YELLOW, darkcolor=YELLOW, **base)
    style.map("Gold.TButton",
              background=[("pressed", YELLOW_DARK), ("active", "#FFC42E")],
              bordercolor=[("active", YELLOW_DARK)],
              lightcolor=[("active", "#FFC42E")], darkcolor=[("active", "#FFC42E")])

    style.configure("Outline.TButton", background=WHITE, foreground=RED,
                    bordercolor=RED, lightcolor=WHITE, darkcolor=WHITE, **base)
    style.map("Outline.TButton",
              background=[("pressed", "#F6E7EA"), ("active", "#FBF2F4")],
              lightcolor=[("active", "#FBF2F4")], darkcolor=[("active", "#FBF2F4")])

    style.configure("Dark.TButton", background=BLACK_SOFT, foreground=WHITE,
                    bordercolor=BLACK_SOFT, lightcolor=BLACK_SOFT,
                    darkcolor=BLACK_SOFT, **base)
    style.map("Dark.TButton",
              background=[("pressed", BLACK), ("active", BLACK_HOVER)],
              lightcolor=[("active", BLACK_HOVER)], darkcolor=[("active", BLACK_HOVER)])

    style.configure("Small.Primary.TButton", padding=(8, 3), font=F_SMALL)
    style.configure("Small.Outline.TButton", padding=(8, 3), font=F_SMALL)

    for name in ("TEntry", "TCombobox", "TSpinbox"):
        style.configure(name, fieldbackground=WHITE, background=WHITE,
                        foreground=TEXT, bordercolor=BORDER, lightcolor=BORDER,
                        darkcolor=BORDER, arrowcolor=RED, insertcolor=TEXT,
                        padding=5, font=F_BODY)
        style.map(name,
                  bordercolor=[("focus", RED)],
                  lightcolor=[("focus", RED)], darkcolor=[("focus", RED)],
                  fieldbackground=[("readonly", "#EFEFEF"), ("disabled", "#EFEFEF")],
                  foreground=[("disabled", MUTED)])

    style.configure("TRadiobutton", background=WHITE, foreground=TEXT, font=F_BODY)
    style.map("TRadiobutton",
              background=[("active", WHITE)],
              indicatorcolor=[("selected", RED), ("!selected", WHITE)])

    style.configure("Treeview", background=WHITE, fieldbackground=WHITE,
                    foreground=TEXT, rowheight=27, font=F_BODY,
                    bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER)
    style.configure("Treeview.Heading", background=GOLD_SOFT, foreground=BLACK,
                    font=F_SUB, relief="flat", padding=6, bordercolor=BORDER)
    style.map("Treeview.Heading", background=[("active", YELLOW)])
    style.map("Treeview",
              background=[("selected", RED)],
              foreground=[("selected", WHITE)])

    style.configure("Vertical.TScrollbar", background=BORDER, troughcolor=BG,
                    bordercolor=BG, arrowcolor=BLACK)
    style.map("Vertical.TScrollbar", background=[("active", MUTED)])

    return style


def card(parent, padding=14, bg=WHITE):
    outer = tk.Frame(parent, bg=BORDER, padx=1, pady=1)
    inner = tk.Frame(outer, bg=bg, padx=padding, pady=padding)
    inner.pack(fill="both", expand=True)
    outer.inner = inner
    return outer


def section_title(parent, text, bg=WHITE):
    return tk.Label(parent, text=text, font=F_HEAD, bg=bg, fg=BLACK, anchor="w")


def status_tags(tree):
    tree.tag_configure("available", foreground=YELLOW_DARK)
    tree.tag_configure("occupied", foreground=RED)
    tree.tag_configure("confirmed", foreground=YELLOW_DARK)
    tree.tag_configure("checked-in", foreground=BLACK)
    tree.tag_configure("cancelled", foreground=MUTED)


def tag_for(status):
    return (status or "").strip().lower()