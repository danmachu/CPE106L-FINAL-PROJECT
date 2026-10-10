import os
import re
import sqlite3
import sys

FOLDER = os.path.dirname(os.path.abspath(__file__))

REQUIRED = [
    "app.py", "db.py", "schema.sql", "seed_rooms.sql", "theme.py",
    "widgets.py", "login_view.py", "dashboard_view.py", "reserve_view.py",
    "records_view.py", "reports_view.py", "profile_view.py",
]
IMAGES = ["rams_logo.png", "rams_logo_small.png", "rams_icon.png"]

print(f"\nChecking folder:\n  {FOLDER}\n")

present = os.listdir(FOLDER)
missing = [f for f in REQUIRED if f not in present]
no_image = [f for f in IMAGES if f not in present]

for name in REQUIRED + IMAGES:
    mark = "OK     " if name in present else "MISSING"
    print(f"  [{mark}] {name}")


WANTED = set(REQUIRED + IMAGES)
EXTRAS = {"view_db.py", "check_setup.py", "README.md", "rams.db", "__pycache__"}


def tidy(name):
    name = re.sub(r" ?\(\d+\)", "", name)
    while name.count(".") > 1:
        name = name[: name.rfind(".")]
    return name


suspects = [n for n in present
            if n not in WANTED and n not in EXTRAS and tidy(n) in WANTED]
if suspects:
    print("\nThese look like renamed copies - rename them to the exact")
    print("names above, or delete them:")
    for name in sorted(set(suspects)):
        print(f"  - {name}")

print(f"\nPython: {sys.version.split()[0]}")
try:
    import tkinter
    print(f"Tkinter: available (Tk {tkinter.TkVersion})")
except ImportError:
    print("Tkinter: MISSING - reinstall Python with the tcl/tk option ticked")
print(f"SQLite: {sqlite3.sqlite_version}")

if os.path.exists(os.path.join(FOLDER, "rams.db")):
    print("Database: rams.db exists")
else:
    print("Database: not created yet (it appears the first time you run app.py)")

print()
if missing:
    print("The application will NOT run - missing:", ", ".join(missing))
elif no_image:
    print("The application will run, but the logo will fall back to text.")
    print("Missing images:", ", ".join(no_image))
else:
    print("Everything is in place. Run:  python app.py")
print()
input("Press Enter to close...")