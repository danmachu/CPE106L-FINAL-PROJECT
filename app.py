import tkinter as tk
from tkinter import messagebox

import db
import theme
from dashboard_view import DashboardView
from login_view import LoginScreen
from profile_view import ProfileView
from records_view import RecordsView
from reports_view import ReportsView
from reserve_view import ReserveView
from widgets import Sidebar, TopBar, load_image

STUDENT_MENU = ["Dashboard", "Reserve a Room", "My Profile"]
ADMIN_MENU = ["Dashboard", "Reserve a Room", "Room Records", "Reports",
              "My Profile"]

SCREENS = {
    "Dashboard": DashboardView,
    "Reserve a Room": ReserveView,
    "Room Records": RecordsView,
    "Reports": ReportsView,
    "My Profile": ProfileView,
}


class RamsApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("RAMS: Room Availability Monitoring System")
        self.geometry("1140x720")
        self.minsize(1000, 660)
        theme.apply_theme(self)

        self.icon_image = load_image("rams_icon.png", max_width=72,
                                     max_height=72)
        if self.icon_image is not None:
            try:
                self.iconphoto(True, self.icon_image)
            except tk.TclError:
                pass

        self.user = None
        self.view = None
        self.sidebar = None
        self.topbar = None
        self.content = None

        self.show_login()

    def _clear_window(self):
        for child in list(self.winfo_children()):
            if isinstance(child, tk.Toplevel):
                continue
            child.destroy()
        self.view = None

    def show_login(self):
        self.user = None
        self._clear_window()
        LoginScreen(self, self).pack(fill="both", expand=True)

    def open_workspace(self, user):
        self.user = user
        self._clear_window()

        menu = ADMIN_MENU if user["role"] == "Admin" else STUDENT_MENU
        self.sidebar = Sidebar(self, menu, self.go, self.logout)
        self.sidebar.pack(side="left", fill="y")

        right = tk.Frame(self, bg=theme.BG)
        right.pack(side="left", fill="both", expand=True)

        self.topbar = TopBar(right, user)
        self.topbar.pack(fill="x")

        self.content = tk.Frame(right, bg=theme.BG, padx=18, pady=16)
        self.content.pack(fill="both", expand=True)

        self.go("Dashboard")

    def go(self, name):
        screen = SCREENS.get(name)
        if screen is None or self.content is None:
            return
        if self.view is not None:
            self.view.destroy()
        self.view = screen(self.content, self)
        self.view.pack(fill="both", expand=True)
        self.topbar.set_title(getattr(self.view, "title", name))
        self.sidebar.set_active(name)
        self.view.start()

    def reload_user(self):
        fresh = db.get_user(self.user["user_id"])
        if fresh is not None:
            self.user = fresh
            self.topbar.set_user(fresh)

    def logout(self):
        if messagebox.askyesno("Logout", "Sign out of RAMS?"):
            self.show_login()


def main():
    db.init_db()
    RamsApp().mainloop()


if __name__ == "__main__":
    main()