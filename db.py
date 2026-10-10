import hashlib
import os
import re
import secrets
import sqlite3
from datetime import date, datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "rams.db")
SCHEMA_PATH = os.path.join(BASE_DIR, "schema.sql")
SEED_PATH = os.path.join(BASE_DIR, "seed_rooms.sql")


TIME_SLOTS = [
    "07:30 - 09:00",
    "09:00 - 10:30",
    "10:30 - 12:00",
    "13:00 - 14:30",
    "14:30 - 16:00",
    "16:00 - 17:30",
    "17:30 - 19:00",
]

ROOM_STATUSES = ["Available", "Occupied"]
ROLES = ["Student", "Admin"]


DEFAULT_CAPACITY = 30
MAX_CAPACITY = 500


FLOORS = {"1": "First Floor", "2": "Second Floor", "3": "Third Floor"}


def floor_of(room_id):
    digits = re.search(r"\d", room_id or "")
    return FLOORS.get(digits.group(0), "") if digits else ""


def connect():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _run_sql_file(conn, path):
    with open(path, encoding="utf-8") as handle:
        conn.executescript(handle.read())


def hash_password(password, salt=None):
    salt = salt or secrets.token_hex(8)
    digest = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return f"{salt}${digest}"


def verify_password(password, stored):
    try:
        salt, _ = stored.split("$", 1)
    except ValueError:
        return False
    return secrets.compare_digest(hash_password(password, salt), stored)


def init_db():
    first_run = not os.path.exists(DB_PATH)
    with connect() as conn:
        _run_sql_file(conn, SCHEMA_PATH)
        if first_run:
            _run_sql_file(conn, SEED_PATH)
        else:

            columns = {c["name"] for c in conn.execute("PRAGMA table_info(Rooms)")}
            if "capacity" not in columns:
                conn.execute("ALTER TABLE Rooms ADD COLUMN capacity INTEGER "
                             f"NOT NULL DEFAULT {DEFAULT_CAPACITY}")
                conn.execute("UPDATE Rooms SET capacity = occupancy_count "
                             "WHERE occupancy_count > capacity")

        if not conn.execute("SELECT 1 FROM Users WHERE role = 'Admin'").fetchone():
            conn.execute(
                "INSERT INTO Users (user_id, name, role, password) VALUES (?, ?, 'Admin', ?)",
                ("ADMIN-001", "System Administrator", hash_password("admin123")),
            )
        if not conn.execute("SELECT 1 FROM Users WHERE role = 'Student'").fetchone():
            conn.execute(
                "INSERT INTO Users (user_id, name, role, password) VALUES (?, ?, 'Student', ?)",
                ("2024-1123", "Juan Dela Cruz", hash_password("student123")),
            )


def create_account(user_id, name, role, password):
    user_id, name = user_id.strip(), name.strip()
    if not user_id or not name:
        return False, "User ID and full name are required."
    if role not in ROLES:
        return False, "Select a valid role."
    if len(password) < 4:
        return False, "Password must be at least 4 characters."
    try:
        with connect() as conn:
            conn.execute(
                "INSERT INTO Users (user_id, name, role, password) VALUES (?, ?, ?, ?)",
                (user_id, name, role, hash_password(password)),
            )
    except sqlite3.IntegrityError:
        return False, "That User ID is already registered."
    return True, "Account created. You may now sign in."


def login(user_id, password, role=None):
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM Users WHERE user_id = ?", (user_id.strip(),)
        ).fetchone()
    if row is None or not verify_password(password, row["password"]):
        return None, "Invalid User ID or password."
    if role and row["role"] != role:
        return None, f"This account is registered as {row['role']}."
    return row, ""


def get_user(user_id):
    with connect() as conn:
        return conn.execute(
            "SELECT * FROM Users WHERE user_id = ?", (user_id,)
        ).fetchone()


def update_profile(user_id, name, new_password=None):
    name = name.strip()
    if not name:
        return False, "Full name cannot be empty."
    with connect() as conn:
        if new_password:
            if len(new_password) < 4:
                return False, "Password must be at least 4 characters."
            conn.execute(
                "UPDATE Users SET name = ?, password = ? WHERE user_id = ?",
                (name, hash_password(new_password), user_id),
            )
        else:
            conn.execute("UPDATE Users SET name = ? WHERE user_id = ?", (name, user_id))
    return True, "Changes saved."


def next_room_id(room_name=""):
    with connect() as conn:
        taken = {r["room_id"] for r in conn.execute("SELECT room_id FROM Rooms")}
    match = re.search(r"\b([A-Za-z]{1,3})\s*-?\s*(\d{3,4})\b", room_name)
    if match is None:
        match = re.search(r"()(\d{3,4})", room_name)
    if match:
        letters, digits = match.group(1).upper(), match.group(2)
        candidate = f"{letters}{digits}" if letters else f"R-{digits}"
        if candidate not in taken:
            return candidate
    counter = 1
    while f"R-{counter:03d}" in taken:
        counter += 1
    return f"R-{counter:03d}"


def list_rooms(search="", status_filter="All"):
    query = "SELECT * FROM Rooms WHERE 1 = 1"
    params = []
    if search.strip():
        query += " AND (room_id LIKE ? OR room_name LIKE ?)"
        term = f"%{search.strip()}%"
        params += [term, term]
    if status_filter in ROOM_STATUSES:
        query += " AND status = ?"
        params.append(status_filter)

    query += " ORDER BY room_id"
    with connect() as conn:
        return conn.execute(query, params).fetchall()


def get_room(room_id):
    with connect() as conn:
        return conn.execute(
            "SELECT * FROM Rooms WHERE room_id = ?", (room_id,)
        ).fetchone()


def _validate_room(room_name, status, occupancy, capacity):
    if not room_name.strip():
        return "Room name is required."
    if status not in ROOM_STATUSES:
        return "Select a valid availability status."
    try:
        seats = int(capacity)
    except (TypeError, ValueError):
        return "Capacity must be a whole number."
    if seats < 1 or seats > MAX_CAPACITY:
        return f"Capacity must be between 1 and {MAX_CAPACITY}."
    try:
        people = int(occupancy)
    except (TypeError, ValueError):
        return "Occupancy count must be a whole number."
    if people < 0:
        return "Occupancy count cannot be negative."
    if people > seats:
        return (f"Occupancy cannot be more than the capacity. "
                f"This room seats {seats}.")
    return None


def add_room(room_id, room_name, status, occupancy, capacity=DEFAULT_CAPACITY):
    error = _validate_room(room_name, status, occupancy, capacity)
    if error:
        return False, error
    try:
        with connect() as conn:
            conn.execute(
                "INSERT INTO Rooms (room_id, room_name, status, capacity, "
                "occupancy_count) VALUES (?, ?, ?, ?, ?)",
                (room_id.strip(), room_name.strip(), status, int(capacity),
                 int(occupancy)),
            )
            _sync_status(conn, room_id.strip(), status == "Occupied")
    except sqlite3.IntegrityError:
        return False, "That room ID or room name already exists."
    return True, f"{room_name.strip()} saved."


def update_room(room_id, room_name, status, occupancy, capacity=DEFAULT_CAPACITY):
    error = _validate_room(room_name, status, occupancy, capacity)
    if error:
        return False, error
    try:
        with connect() as conn:
            conn.execute(
                "UPDATE Rooms SET room_name = ?, status = ?, capacity = ?, "
                "occupancy_count = ? WHERE room_id = ?",
                (room_name.strip(), status, int(capacity), int(occupancy),
                 room_id),
            )
            _sync_status(conn, room_id, status == "Occupied")
    except sqlite3.IntegrityError:
        return False, "Another room already uses that name."
    return True, f"{room_name.strip()} updated."


def set_occupancy(room_id, occupancy):
    try:
        value = int(occupancy)
    except (TypeError, ValueError):
        return False, "Occupancy count must be a whole number."
    if value < 0:
        return False, "Occupancy count cannot be negative."
    with connect() as conn:
        room = conn.execute(
            "SELECT * FROM Rooms WHERE room_id = ?", (room_id,)
        ).fetchone()
        if room is None:
            return False, "Room not found."
        if value > room["capacity"]:
            return False, (f"{room['room_id']} seats {room['capacity']} people. "
                           f"Enter {room['capacity']} or fewer.")
        conn.execute(
            "UPDATE Rooms SET occupancy_count = ? WHERE room_id = ?", (value, room_id)
        )
        _sync_status(conn, room_id)
    return True, f"{room['room_id']} now holds {value} of {room['capacity']}."


def delete_room(room_id):
    with connect() as conn:
        conn.execute("DELETE FROM Rooms WHERE room_id = ?", (room_id,))
    return True, "Room deleted."


def parse_date(text):
    text = (text or "").strip()
    for pattern in ("%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y"):
        try:
            return datetime.strptime(text, pattern).date()
        except ValueError:
            continue
    return None


def rooms_for_slot(on_date=None, time_slot=None, search=""):
    rows = list_rooms(search=search)
    booked = set()
    if on_date and time_slot:
        with connect() as conn:
            booked = {
                r["room_id"]
                for r in conn.execute(
                    "SELECT room_id FROM Reservations "
                    "WHERE date = ? AND time_slot = ? AND status <> 'Cancelled'",
                    (on_date.isoformat(), time_slot),
                )
            }
    result = []
    for row in rows:
        item = dict(row)
        item["floor"] = floor_of(item["room_id"])
        item["occupancy"] = f"{item['occupancy_count']} / {item['capacity']}"
        if item["room_id"] in booked:
            item["status"] = "Occupied"
        result.append(item)
    return result


def reserve_room(room_id, user_id, date_text, time_slot):
    on_date = parse_date(date_text)
    if on_date is None:
        return False, "Enter the date as YYYY-MM-DD."
    if on_date < date.today():
        return False, "The date has already passed."
    if time_slot not in TIME_SLOTS:
        return False, "Select a time slot."

    conn = connect()
    try:
        conn.execute("BEGIN IMMEDIATE")
        room = conn.execute(
            "SELECT * FROM Rooms WHERE room_id = ?", (room_id,)
        ).fetchone()
        if room is None:
            conn.rollback()
            return False, "Room not found."
        if room["status"] != "Available":
            conn.rollback()
            return False, "Room Unavailable - please select another room."
        conn.execute(
            "INSERT INTO Reservations (room_id, user_id, date, time_slot, status) "
            "VALUES (?, ?, ?, ?, 'Confirmed')",
            (room_id, user_id, on_date.isoformat(), time_slot),
        )
        conn.execute(
            "UPDATE Rooms SET status = 'Occupied' WHERE room_id = ?", (room_id,)
        )
        conn.commit()
        return True, f"Reservation confirmed. {room['room_name']} is now marked Occupied."
    except sqlite3.IntegrityError:
        conn.rollback()
        return False, "That slot was just taken by another user."
    finally:
        conn.close()


def _sync_status(conn, room_id, force_occupied=False):
    room = conn.execute(
        "SELECT occupancy_count FROM Rooms WHERE room_id = ?", (room_id,)
    ).fetchone()
    if room is None:
        return
    booked = conn.execute(
        "SELECT 1 FROM Reservations WHERE room_id = ? "
        "AND status IN ('Confirmed', 'Checked-in')",
        (room_id,),
    ).fetchone()
    occupied = bool(booked) or room["occupancy_count"] > 0 or force_occupied
    conn.execute(
        "UPDATE Rooms SET status = ? WHERE room_id = ?",
        ("Occupied" if occupied else "Available", room_id),
    )


def list_reservations(user_id=None, on_date=None, include_cancelled=True):
    query = (
        "SELECT rs.reservation_id, rs.room_id, rm.room_name, rs.user_id, "
        "       u.name AS user_name, rs.date, rs.time_slot, rs.status "
        "FROM Reservations rs "
        "JOIN Rooms rm ON rm.room_id = rs.room_id "
        "JOIN Users u ON u.user_id = rs.user_id "
        "WHERE 1 = 1"
    )
    params = []
    if user_id:
        query += " AND rs.user_id = ?"
        params.append(user_id)
    if on_date:
        query += " AND rs.date = ?"
        params.append(on_date.isoformat())
    if not include_cancelled:
        query += " AND rs.status <> 'Cancelled'"
    query += " ORDER BY rs.date DESC, rs.time_slot"
    with connect() as conn:
        return conn.execute(query, params).fetchall()


def check_in(reservation_id, user_id=None):
    with connect() as conn:
        res = conn.execute(
            "SELECT * FROM Reservations WHERE reservation_id = ?", (reservation_id,)
        ).fetchone()
        if res is None or (user_id and res["user_id"] != user_id):
            return False, "Reservation not found."
        if res["status"] != "Confirmed":
            return False, f"Reservation is already {res['status'].lower()}."
        room = conn.execute(
            "SELECT * FROM Rooms WHERE room_id = ?", (res["room_id"],)
        ).fetchone()
        if room["occupancy_count"] >= room["capacity"]:
            return False, (f"{room['room_id']} is full "
                           f"({room['capacity']} people). Cannot check in.")
        conn.execute(
            "UPDATE Reservations SET status = 'Checked-in' WHERE reservation_id = ?",
            (reservation_id,),
        )
        conn.execute(
            "UPDATE Rooms SET occupancy_count = occupancy_count + 1 WHERE room_id = ?",
            (res["room_id"],),
        )
        _sync_status(conn, res["room_id"])
    return True, (f"Checked in. {room['room_id']} now holds "
                  f"{room['occupancy_count'] + 1} of {room['capacity']}.")


def cancel_reservation(reservation_id, user_id=None):
    with connect() as conn:
        res = conn.execute(
            "SELECT * FROM Reservations WHERE reservation_id = ?", (reservation_id,)
        ).fetchone()
        if res is None or (user_id and res["user_id"] != user_id):
            return False, "Reservation not found."
        if res["status"] == "Cancelled":
            return False, "That reservation is already cancelled."
        if res["status"] == "Checked-in":
            conn.execute(
                "UPDATE Rooms SET occupancy_count = MAX(occupancy_count - 1, 0) "
                "WHERE room_id = ?",
                (res["room_id"],),
            )
        conn.execute(
            "UPDATE Reservations SET status = 'Cancelled' WHERE reservation_id = ?",
            (reservation_id,),
        )
        _sync_status(conn, res["room_id"])
    return True, "Reservation cancelled."


def dashboard_counts():
    with connect() as conn:
        return conn.execute("SELECT * FROM v_dashboard_counts").fetchone()


def occupancy_per_room(limit=8):
    with connect() as conn:
        return conn.execute(
            "SELECT room_id, room_name, occupancy_count FROM Rooms "
            "ORDER BY occupancy_count DESC, room_id LIMIT ?",
            (limit,),
        ).fetchall()


def report_summary(date_from=None, date_to=None):
    window, params = "", []
    if date_from:
        window += " AND x.date >= ?"
        params.append(date_from.isoformat())
    if date_to:
        window += " AND x.date <= ?"
        params.append(date_to.isoformat())
    query = f"""
        SELECT r.room_id, r.room_name, r.status, r.capacity, r.occupancy_count,
               (SELECT COUNT(*) FROM Reservations x
                 WHERE x.room_id = r.room_id
                   AND x.status <> 'Cancelled'{window})   AS total_reservations,
               (SELECT COUNT(*) FROM Reservations x
                 WHERE x.room_id = r.room_id
                   AND x.status = 'Checked-in'{window})   AS check_ins
        FROM Rooms r
        ORDER BY r.room_id
    """
    with connect() as conn:
        return conn.execute(query, params + params).fetchall()


def reservations_per_day(date_from=None, date_to=None):
    query = "SELECT date AS day, COUNT(*) AS total FROM Reservations WHERE status <> 'Cancelled'"
    params = []
    if date_from:
        query += " AND date >= ?"
        params.append(date_from.isoformat())
    if date_to:
        query += " AND date <= ?"
        params.append(date_to.isoformat())
    query += " GROUP BY date ORDER BY date"
    with connect() as conn:
        return conn.execute(query, params).fetchall()


def check_ins_per_room(date_from=None, date_to=None):
    query = (
        "SELECT rm.room_id, rm.room_name, COUNT(*) AS total FROM Reservations rs "
        "JOIN Rooms rm ON rm.room_id = rs.room_id "
        "WHERE rs.status = 'Checked-in'"
    )
    params = []
    if date_from:
        query += " AND rs.date >= ?"
        params.append(date_from.isoformat())
    if date_to:
        query += " AND rs.date <= ?"
        params.append(date_to.isoformat())
    query += " GROUP BY rm.room_id, rm.room_name ORDER BY total DESC, rm.room_id"
    with connect() as conn:
        return conn.execute(query, params).fetchall()