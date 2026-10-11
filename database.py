import sqlite3
from datetime import datetime
from pathlib import Path

from seed_data import seed_database


DB_PATH = Path(__file__).parent / "data" / "mission.db"
MODES = ("TT&C", "SSTV", "Codec2", "M17")
STATUSES = ("Pending", "Sent", "Failed")


def open_database(path=DB_PATH):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    try:
        with connection:
            connection.execute("BEGIN")
            existing = connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'telemetry'"
            ).fetchone()
            connection.execute("""
                CREATE TABLE IF NOT EXISTS telemetry (
                    id INTEGER PRIMARY KEY,
                    recorded_at TEXT NOT NULL,
                    battery_pct REAL NOT NULL CHECK (battery_pct BETWEEN 0 AND 100),
                    temperature_c REAL NOT NULL,
                    link_quality_pct REAL NOT NULL CHECK (link_quality_pct BETWEEN 0 AND 100),
                    operating_mode TEXT NOT NULL CHECK (operating_mode IN ('Normal', 'Safe'))
                )
            """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS communication_records (
                    id INTEGER PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    mode TEXT NOT NULL CHECK (mode IN ('TT&C', 'SSTV', 'Codec2', 'M17')),
                    size_kb REAL NOT NULL CHECK (size_kb > 0),
                    status TEXT NOT NULL CHECK (status IN ('Pending', 'Sent', 'Failed')),
                    notes TEXT NOT NULL DEFAULT ''
                )
            """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS mission_events (
                    id INTEGER PRIMARY KEY,
                    occurred_at TEXT NOT NULL,
                    component TEXT NOT NULL CHECK (component IN ('SomaiyaPod', 'SomaiyaSat')),
                    event_name TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    notes TEXT NOT NULL DEFAULT ''
                )
            """)
            if not existing:
                seed_database(connection)
    except Exception:
        connection.close()
        raise
    return connection


def get_summary(connection):
    latest = connection.execute(
        "SELECT * FROM telemetry ORDER BY recorded_at DESC, id DESC LIMIT 1"
    ).fetchone()
    counts = dict(connection.execute(
        "SELECT status, COUNT(*) FROM communication_records GROUP BY status"
    ).fetchall())
    attempted = counts.get("Sent", 0) + counts.get("Failed", 0)
    success_rate = counts.get("Sent", 0) / attempted * 100 if attempted else None
    event = connection.execute(
        "SELECT * FROM mission_events ORDER BY occurred_at DESC, id DESC LIMIT 1"
    ).fetchone()
    return latest, counts.get("Pending", 0), success_rate, event


def get_telemetry(connection, start="", end=""):
    dates = []
    for value in (start.strip(), end.strip()):
        try:
            date = datetime.strptime(value, "%Y-%m-%d") if value else None
        except ValueError:
            raise ValueError("Enter dates as YYYY-MM-DD, for example 2026-01-15.") from None
        dates.append(date.strftime("%Y-%m-%d") if date else "")
    start, end = dates
    if start and end and start > end:
        raise ValueError("The end date must be on or after the start date.")

    query = "SELECT * FROM telemetry WHERE 1 = 1"
    values = []
    if start:
        query += " AND recorded_at >= ?"
        values.append(start + " 00:00:00")
    if end:
        query += " AND recorded_at <= ?"
        values.append(end + " 23:59:59")
    query += " ORDER BY recorded_at DESC, id DESC"
    return connection.execute(query, values).fetchall()


def get_communications(connection, mode="All", status="All"):
    query = """
        SELECT *, CASE mode WHEN 'TT&C' THEN 1 WHEN 'SSTV' THEN 2 ELSE 3 END AS priority
        FROM communication_records WHERE 1 = 1
    """
    values = []
    if mode != "All":
        query += " AND mode = ?"
        values.append(mode)
    if status != "All":
        query += " AND status = ?"
        values.append(status)
    query += " ORDER BY priority, created_at, id"
    return connection.execute(query, values).fetchall()


def get_events(connection):
    return connection.execute(
        "SELECT * FROM mission_events ORDER BY occurred_at, id"
    ).fetchall()
