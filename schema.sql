PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS Users (
    user_id   TEXT PRIMARY KEY,
    name      TEXT NOT NULL,
    role      TEXT NOT NULL CHECK (role IN ('Admin', 'Student')),
    password  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS Rooms (
    room_id          TEXT PRIMARY KEY,
    room_name        TEXT NOT NULL UNIQUE,
    status           TEXT NOT NULL DEFAULT 'Available'
                     CHECK (status IN ('Available', 'Occupied')),
    capacity         INTEGER NOT NULL DEFAULT 30
                     CHECK (capacity > 0 AND capacity <= 500),
    occupancy_count  INTEGER NOT NULL DEFAULT 0
                     CHECK (occupancy_count >= 0),
    CHECK (occupancy_count <= capacity)
);

CREATE TABLE IF NOT EXISTS Reservations (
    reservation_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id         TEXT NOT NULL REFERENCES Rooms(room_id) ON DELETE CASCADE,
    user_id         TEXT NOT NULL REFERENCES Users(user_id) ON DELETE CASCADE,
    date            TEXT NOT NULL,
    time_slot       TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'Confirmed'
                    CHECK (status IN ('Confirmed', 'Checked-in', 'Cancelled')),
    created_at      TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_no_double_booking
    ON Reservations (room_id, date, time_slot)
    WHERE status IN ('Confirmed', 'Checked-in');

CREATE INDEX IF NOT EXISTS idx_res_user ON Reservations (user_id);
CREATE INDEX IF NOT EXISTS idx_res_date ON Reservations (date);


CREATE VIEW IF NOT EXISTS v_room_summary AS
SELECT
    r.room_id,
    r.room_name,
    r.status,
    r.capacity,
    r.occupancy_count,
    (SELECT COUNT(*) FROM Reservations x
      WHERE x.room_id = r.room_id AND x.status <> 'Cancelled')   AS total_reservations,
    (SELECT COUNT(*) FROM Reservations x
      WHERE x.room_id = r.room_id AND x.status = 'Checked-in')   AS check_ins
FROM Rooms r;

CREATE VIEW IF NOT EXISTS v_reservations_per_day AS
SELECT date AS day, COUNT(*) AS total
FROM Reservations
WHERE status <> 'Cancelled'
GROUP BY date;

CREATE VIEW IF NOT EXISTS v_dashboard_counts AS
SELECT
    (SELECT COUNT(*) FROM Rooms)                               AS total_rooms,
    (SELECT COUNT(*) FROM Rooms WHERE status = 'Available')    AS available_rooms,
    (SELECT COUNT(*) FROM Rooms WHERE status = 'Occupied')     AS occupied_rooms,
    (SELECT COUNT(*) FROM Reservations
      WHERE date = date('now', 'localtime')
        AND status <> 'Cancelled')                             AS reservations_today;