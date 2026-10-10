import math
import os
import tkinter as tk
from tkinter import ttk

from theme import (BG, BLACK, BLACK_HOVER, BLACK_SOFT, BORDER, F_BODY, F_BRAND,
                   F_SMALL, F_STAT, F_SUB, F_TINY, F_TITLE, MUTED, RED, WHITE,
                   YELLOW, status_tags, tag_for)


ASSET_DIR = os.path.dirname(os.path.abspath(__file__))


def load_image(filename, max_width=None, max_height=None):
    path = os.path.join(ASSET_DIR, filename)
    if not os.path.exists(path):
        print(f"[RAMS] image not found, using text instead: {path}")
        return None
    try:
        image = tk.PhotoImage(file=path)
    except tk.TclError as error:
        print(f"[RAMS] could not read {path}: {error}")
        return None

    if not _oversized(image, max_width, max_height):
        return image

    try:
        from PIL import Image, ImageTk
        source = Image.open(path)
        source.thumbnail((max_width or source.width,
                          max_height or source.height), Image.LANCZOS)
        print(f"[RAMS] {filename} is larger than needed; resized to "
              f"{source.width}x{source.height}")
        return ImageTk.PhotoImage(source)
    except ImportError:
        pass

    factor = 1
    if max_width:
        factor = max(factor, math.ceil(image.width() / max_width))
    if max_height:
        factor = max(factor, math.ceil(image.height() / max_height))
    image = image.subsample(factor)
    print(f"[RAMS] {filename} is {factor}x larger than needed; shown at "
          f"{image.width()}x{image.height()}. For a sharp logo use the "
          f"supplied file, or run: pip install pillow")
    return image


def _oversized(image, max_width, max_height):
    return bool((max_width and image.width() > max_width)
                or (max_height and image.height() > max_height))


class View(tk.Frame):

    refresh_ms = None

    def __init__(self, master, app):
        super().__init__(master, bg=BG)
        self.app = app
        self._job = None

    def start(self):
        self.refresh()
        if self.refresh_ms:
            self._job = self.after(self.refresh_ms, self._tick)

    def _tick(self):
        if not self.winfo_exists():
            return
        self.refresh()
        self._job = self.after(self.refresh_ms, self._tick)

    def refresh_now(self):
        if self._job is not None:
            self.after_cancel(self._job)
            self._job = None
        self.start()

    def destroy(self):
        if self._job is not None:
            try:
                self.after_cancel(self._job)
            except tk.TclError:
                pass
            self._job = None
        super().destroy()

    def refresh(self):
        pass


class Sidebar(tk.Frame):

    def __init__(self, master, items, on_select, on_logout):
        super().__init__(master, bg=BLACK, width=196)
        self.pack_propagate(False)
        self.on_select = on_select
        self.labels = {}

        brand = tk.Frame(self, bg=BLACK, padx=16, pady=14)
        brand.pack(fill="x")
        self.brand_image = load_image("rams_logo_small.png",
                                     max_width=160, max_height=100)
        if self.brand_image is not None:
            tk.Label(brand, image=self.brand_image, bg=BLACK).pack(anchor="w")
        else:
            tk.Label(brand, text="RAMS", font=F_BRAND, bg=BLACK,
                     fg=YELLOW).pack(anchor="w")
        tk.Label(brand, text="Room Availability Monitoring", font=F_TINY,
                 bg=BLACK, fg="#9A9A9A").pack(anchor="w", pady=(2, 0))

        tk.Frame(self, bg=BLACK_HOVER, height=1).pack(fill="x", padx=12)

        menu = tk.Frame(self, bg=BLACK, pady=8)
        menu.pack(fill="both", expand=True)
        for name in items:
            row = tk.Label(menu, text=f"  ▪  {name}", font=F_BODY, bg=BLACK,
                           fg="#DADADA", anchor="w", padx=10, pady=9)
            row.pack(fill="x", padx=8, pady=1)
            row.bind("<Button-1>", lambda _e, n=name: self.on_select(n))
            row.bind("<Enter>", lambda _e, r=row: self._hover(r, True))
            row.bind("<Leave>", lambda _e, r=row: self._hover(r, False))
            self.labels[name] = row

        footer = tk.Frame(self, bg=BLACK, padx=12, pady=14)
        footer.pack(fill="x", side="bottom")
        tk.Frame(self, bg=BLACK_HOVER, height=1).pack(
            fill="x", side="bottom", padx=12)

        out = tk.Label(footer, text="Log out", font=F_SUB, bg=BLACK_SOFT,
                       fg=WHITE, padx=12, pady=9, cursor="hand2",
                       highlightbackground=BLACK_HOVER, highlightthickness=1)
        out.pack(fill="x")
        out.bind("<Button-1>", lambda _e: on_logout())
        out.bind("<Enter>", lambda _e: out.config(bg=RED))
        out.bind("<Leave>", lambda _e: out.config(bg=BLACK_SOFT))

        self.active = None

    def _hover(self, row, entering):
        if row is self.labels.get(self.active):
            return
        row.config(bg=BLACK_HOVER if entering else BLACK)

    def set_active(self, name):
        self.active = name
        for key, row in self.labels.items():
            if key == name:
                row.config(bg=RED, fg=WHITE, font=F_SUB)
            else:
                row.config(bg=BLACK, fg="#DADADA", font=F_BODY)


class TopBar(tk.Frame):

    def __init__(self, master, user):
        super().__init__(master, bg=WHITE)
        bar = tk.Frame(self, bg=WHITE, padx=18, pady=12)
        bar.pack(fill="x")
        self.title = tk.Label(bar, text="", font=F_TITLE, bg=WHITE, fg=BLACK)
        self.title.pack(side="left")

        chip = tk.Frame(bar, bg=WHITE)
        chip.pack(side="right")
        avatar = tk.Canvas(chip, width=24, height=24, bg=WHITE, highlightthickness=0)
        avatar.pack(side="left", padx=(0, 8))
        avatar.create_oval(2, 2, 22, 22, fill=BLACK_SOFT, outline="")
        self.who = tk.Label(chip, text="", font=F_SMALL, bg=WHITE, fg=BLACK)
        self.who.pack(side="left")
        self.set_user(user)

        accent = tk.Frame(self, bg=YELLOW, height=3)
        accent.pack(fill="x")
        tk.Frame(accent, bg=RED, height=3, width=170).pack(side="left")

    def set_title(self, text):
        self.title.config(text=text)

    def set_user(self, user):
        self.who.config(text=f"{user['name']}  |  {user['role']}")


class StatCard(tk.Frame):

    def __init__(self, master, caption, colour=RED):
        super().__init__(master, bg=BORDER, padx=1, pady=1)
        inner = tk.Frame(self, bg=WHITE, padx=16, pady=12)
        inner.pack(fill="both", expand=True)
        tk.Label(inner, text=caption.upper(), font=F_TINY, bg=WHITE,
                 fg=MUTED, anchor="w").pack(fill="x")
        self.value = tk.Label(inner, text="0", font=F_STAT, bg=WHITE,
                              fg=colour, anchor="w")
        self.value.pack(fill="x")

    def set(self, value):
        self.value.config(text=str(value))


def make_table(parent, columns, height=10):
    frame = tk.Frame(parent, bg=WHITE)
    keys = [c[0] for c in columns]
    tree = ttk.Treeview(frame, columns=keys, show="headings",
                        height=height, selectmode="browse")
    for key, heading, width, anchor in columns:
        tree.heading(key, text=heading)

        tree.column(key, width=width, minwidth=45, anchor=anchor, stretch=True)
    bar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=bar.set)
    tree.pack(side="left", fill="both", expand=True)
    bar.pack(side="right", fill="y")
    status_tags(tree)
    return frame, tree


def fill_table(tree, rows, keys, iid_key, status_key=None):
    chosen = tree.selection()
    keep = chosen[0] if chosen else None
    tree.delete(*tree.get_children())
    for row in rows:
        data = dict(row)
        tags = (tag_for(data.get(status_key)),) if status_key else ()
        tree.insert("", "end", iid=str(data[iid_key]),
                    values=[data.get(k, "") for k in keys], tags=tags)
    if keep and tree.exists(keep):
        tree.selection_set(keep)


def selected_id(tree):
    chosen = tree.selection()
    return chosen[0] if chosen else None


def center_on(window, parent):
    window.update_idletasks()
    root = parent.winfo_toplevel()
    x = root.winfo_rootx() + (root.winfo_width() - window.winfo_width()) // 2
    y = root.winfo_rooty() + (root.winfo_height() - window.winfo_height()) // 3
    window.geometry(f"+{max(x, 0)}+{max(y, 0)}")


class _Chart(tk.Frame):
    def __init__(self, master, title, height=190):
        super().__init__(master, bg=WHITE)
        self.title_label = None
        if title:
            self.title_label = tk.Label(self, text=title, font=F_SUB, bg=WHITE,
                                        fg=BLACK, anchor="w")
            self.title_label.pack(fill="x", pady=(0, 6))
        self.canvas = tk.Canvas(self, bg=WHITE, height=height,
                                highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda _e: self.draw())
        self.data = []

    def set_data(self, data):
        self.data = [(str(a), float(b or 0)) for a, b in data]
        self.draw()

    def title_text(self, text):
        if self.title_label is not None:
            self.title_label.config(text=text)

    def _empty(self, w, h):
        self.canvas.create_text(w / 2, h / 2, text="No data for this selection",
                                font=F_SMALL, fill=MUTED)

    @staticmethod
    def _short(text, limit=11):
        return text if len(text) <= limit else text[: limit - 1] + "."

    @staticmethod
    def _axis(top):
        top = max(top, 1)
        if top <= 5:
            whole = int(math.ceil(top))
            return float(whole), whole
        for step in (2, 5, 10, 20, 25, 50, 100, 200, 250, 500, 1000, 2500, 5000):
            if step * 4 >= top:
                return float(step * 4), 4
        return float(top), 4

    def draw(self):
        raise NotImplementedError


class BarChart(_Chart):

    def __init__(self, master, title, height=190, orient="vertical"):
        super().__init__(master, title, height)
        self.orient = orient

    def draw(self):
        c = self.canvas
        c.delete("all")
        w, h = c.winfo_width(), c.winfo_height()
        if w < 60 or h < 50:
            return
        if not self.data:
            self._empty(w, h)
            return
        top = max(v for _, v in self.data) or 1

        if self.orient == "horizontal":
            left, right, pad = 92, 44, 6
            n = len(self.data)
            band = (h - 2 * pad) / n
            thick = min(18, band * 0.62)
            for i, (label, value) in enumerate(self.data):
                cy = pad + band * (i + 0.5)
                length = (value / top) * (w - left - right)
                c.create_text(left - 8, cy, text=self._short(label, 13), anchor="e",
                              font=F_TINY, fill=BLACK)
                c.create_rectangle(left, cy - thick / 2, left + max(length, 1),
                                   cy + thick / 2, fill=RED, outline="")
                c.create_text(left + length + 6, cy, text=f"{value:g}", anchor="w",
                              font=F_TINY, fill=BLACK)
            return

        left, right, top_pad, bottom = 38, 12, 18, 32
        pw, ph = w - left - right, h - top_pad - bottom
        top, ticks = self._axis(top)
        for i in range(ticks + 1):
            y = top_pad + ph - ph * i / ticks
            c.create_line(left, y, w - right, y, fill="#EEEEEE")
            c.create_text(left - 6, y, text=f"{top * i / ticks:.0f}", anchor="e",
                          font=F_TINY, fill=MUTED)
        n = len(self.data)
        slot = pw / n
        width = min(46, slot * 0.58)
        for i, (label, value) in enumerate(self.data):
            cx = left + slot * (i + 0.5)
            bar = (value / top) * ph
            y0 = top_pad + ph - bar
            c.create_rectangle(cx - width / 2, y0, cx + width / 2, top_pad + ph,
                               fill=RED, outline="")
            if bar > 20:
                c.create_text(cx, y0 + 10, text=f"{value:g}", font=F_TINY, fill=WHITE)
            else:
                c.create_text(cx, y0 - 8, text=f"{value:g}", font=F_TINY, fill=BLACK)
            c.create_text(cx, top_pad + ph + 12, text=self._short(label),
                          font=F_TINY, fill=MUTED)
        c.create_line(left, top_pad + ph, w - right, top_pad + ph, fill=BORDER)


class LineChart(_Chart):

    def draw(self):
        c = self.canvas
        c.delete("all")
        w, h = c.winfo_width(), c.winfo_height()
        if w < 60 or h < 50:
            return
        if not self.data:
            self._empty(w, h)
            return
        left, right, top_pad, bottom = 38, 14, 18, 32
        pw, ph = w - left - right, h - top_pad - bottom
        top, ticks = self._axis(max(v for _, v in self.data))
        for i in range(ticks + 1):
            y = top_pad + ph - ph * i / ticks
            c.create_line(left, y, w - right, y, fill="#EEEEEE")
            c.create_text(left - 6, y, text=f"{top * i / ticks:.0f}", anchor="e",
                          font=F_TINY, fill=MUTED)
        n = len(self.data)
        step = pw / max(n - 1, 1)
        points = []
        for i, (label, value) in enumerate(self.data):
            x = left + (step * i if n > 1 else pw / 2)
            y = top_pad + ph - (value / top) * ph
            points.append((x, y, label, value))
        if len(points) > 1:
            c.create_line([(p[0], p[1]) for p in points], fill=RED, width=2,
                          smooth=False)
        for x, y, label, value in points:
            c.create_oval(x - 3.5, y - 3.5, x + 3.5, y + 3.5, fill=WHITE,
                          outline=RED, width=2)
            c.create_text(x, top_pad + ph + 12, text=self._short(label, 10),
                          font=F_TINY, fill=MUTED)
        c.create_line(left, top_pad + ph, w - right, top_pad + ph, fill=BORDER)