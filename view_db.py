import os
import sqlite3
import sys

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rams.db")

QUERIES = {
    "1": ("Rooms that have people in them",
          "SELECT room_id, room_name, status, occupancy_count "
          "FROM Rooms WHERE occupancy_count > 0 ORDER BY room_id"),
    "2": ("All rooms",
          "SELECT room_id, room_name, status, occupancy_count "
          "FROM Rooms ORDER BY room_id"),
    "3": ("Rooms currently marked Occupied",
          "SELECT room_id, room_name, occupancy_count FROM Rooms "
          "WHERE status = 'Occupied' ORDER BY room_id"),
    "4": ("All reservations",
          "SELECT rs.reservation_id, rs.room_id, u.name AS reserved_by, "
          "       rs.date, rs.time_slot, rs.status "
          "FROM Reservations rs JOIN Users u ON u.user_id = rs.user_id "
          "ORDER BY rs.reservation_id DESC"),
    "5": ("Registered users",
          "SELECT user_id, name, role FROM Users ORDER BY role, user_id"),
    "6": ("Report summary (the v_room_summary view)",
          "SELECT * FROM v_room_summary "
          "ORDER BY total_reservations DESC, room_id LIMIT 20"),
    "7": ("How many rooms are free right now",
          "SELECT status, COUNT(*) AS rooms FROM Rooms GROUP BY status"),
}


def show(rows, headings):
    if not rows:
        print("\n(no rows matched)\n")
        return
    table = [list(headings)] + [[str(v) for v in row] for row in rows]
    widths = [max(len(r[i]) for r in table) for i in range(len(headings))]
    line = "-+-".join("-" * w for w in widths)
    print()
    print(" | ".join(h.ljust(w) for h, w in zip(table[0], widths)))
    print(line)
    for row in table[1:]:
        print(" | ".join(c.ljust(w) for c, w in zip(row, widths)))
    print(f"\n{len(rows)} row(s)\n")


def run(conn, sql):
    try:
        cursor = conn.execute(sql)
    except sqlite3.Error as error:
        print(f"\nSQL error: {error}\n")
        return
    if cursor.description is None:
        conn.commit()
        print(f"\nOK - {cursor.rowcount} row(s) changed\n")
        return
    show(cursor.fetchall(), [c[0] for c in cursor.description])


def main():
    if not os.path.exists(DB_PATH):
        print("\nCannot find rams.db next to this file.")
        print("Put view_db.py in the same folder as app.py, run the")
        print("application once so the database is created, then try again.\n")
        input("Press Enter to close...")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    print(f"\nRAMS database: {DB_PATH}")

    while True:
        print("\n" + "=" * 52)
        for key, (label, _) in QUERIES.items():
            print(f"  {key}. {label}")
        print("  S. Type my own SQL")
        print("  Q. Quit")
        print("=" * 52)

        choice = input("Choice: ").strip().upper()
        if choice == "Q":
            break
        if choice == "S":
            sql = input("SQL> ").strip().rstrip(";")
            if sql:
                run(conn, sql)
            continue
        if choice in QUERIES:
            label, sql = QUERIES[choice]
            print(f"\n{label}")
            print(f"SQL: {sql}")
            run(conn, sql)
        else:
            print("\nType one of the numbers, S, or Q.")

    conn.close()


if __name__ == "__main__":
    main()