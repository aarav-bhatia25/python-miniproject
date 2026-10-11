import sqlite3
import tempfile
import unittest
from pathlib import Path

from database import get_communications, get_events, get_summary, get_telemetry, open_database


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.path = Path(self.folder.name) / "mission.db"
        self.connection = open_database(self.path)

    def tearDown(self):
        self.connection.close()
        self.folder.cleanup()

    def test_seed_and_restart(self):
        self.assertEqual(len(get_telemetry(self.connection)), 200)
        self.assertEqual(len(get_communications(self.connection)), 80)
        self.assertEqual(len(get_events(self.connection)), 6)
        with self.connection:
            self.connection.execute("UPDATE communication_records SET notes = 'Saved note' WHERE id = 1")
        self.connection.close()
        self.connection = open_database(self.path)
        self.assertEqual(len(get_telemetry(self.connection)), 200)
        self.assertEqual(len(get_communications(self.connection)), 80)
        note = self.connection.execute("SELECT notes FROM communication_records WHERE id = 1").fetchone()[0]
        self.assertEqual(note, "Saved note")

    def test_seed_is_repeatable_and_has_example_cases(self):
        second = open_database(Path(self.folder.name) / "second.db")
        try:
            self.assertEqual([tuple(row) for row in get_telemetry(self.connection)],
                             [tuple(row) for row in get_telemetry(second)])
        finally:
            second.close()
        readings = get_telemetry(self.connection)
        self.assertTrue(any(row["battery_pct"] < 20 for row in readings))
        self.assertTrue(any(row["link_quality_pct"] < 35 for row in readings))
        self.assertLess(get_events(self.connection)[-2]["occurred_at"], readings[-1]["recorded_at"])

    def test_date_filters_include_whole_day(self):
        rows = get_telemetry(self.connection, "2026-01-15", "2026-01-15")
        self.assertEqual(len(rows), 192)
        self.assertEqual(rows[0]["recorded_at"], "2026-01-15 23:55:00")
        self.assertEqual(rows[-1]["recorded_at"], "2026-01-15 08:00:00")
        self.assertEqual(len(get_telemetry(self.connection, "2026-01-16")), 8)
        self.assertEqual(len(get_telemetry(self.connection, end="2026-01-15")), 192)
        self.assertEqual(get_telemetry(self.connection, "2027-01-01"), [])

    def test_invalid_dates(self):
        for start, end in (("wrong", ""), ("2026-02-30", ""), ("2026-01-16", "2026-01-15")):
            with self.subTest(start=start, end=end):
                with self.assertRaises(ValueError):
                    get_telemetry(self.connection, start, end)

    def test_communication_filters_and_priority(self):
        rows = get_communications(self.connection, "SSTV", "Pending")
        self.assertEqual(len(rows), 4)
        self.assertTrue(all(row["mode"] == "SSTV" and row["status"] == "Pending" for row in rows))
        all_rows = get_communications(self.connection)
        order = [(row["priority"], row["created_at"], row["id"]) for row in all_rows]
        self.assertEqual(order, sorted(order))
        self.assertEqual(get_communications(self.connection, "' OR 1=1 --"), [])

    def test_summary_excludes_pending(self):
        latest, pending, rate, event = get_summary(self.connection)
        self.assertEqual(latest["recorded_at"], "2026-01-16 00:35:00")
        self.assertEqual(pending, 16)
        self.assertAlmostEqual(rate, 54 / 64 * 100)
        self.assertEqual(event["event_name"], "First housekeeping received")
        with self.connection:
            self.connection.execute("UPDATE communication_records SET status = 'Pending'")
        self.assertIsNone(get_summary(self.connection)[2])

    def test_latest_uses_timestamp_and_tie_breaker(self):
        with self.connection:
            self.connection.execute("""INSERT INTO telemetry VALUES
                (201, '2020-01-01 00:00:00', 50, 20, 80, 'Normal')""")
        self.assertEqual(get_summary(self.connection)[0]["id"], 200)
        with self.connection:
            self.connection.execute("""INSERT INTO telemetry VALUES
                (202, '2026-01-16 00:35:00', 50, 20, 80, 'Normal')""")
        self.assertEqual(get_summary(self.connection)[0]["id"], 202)

    def test_invalid_records_are_rejected(self):
        queries = [
            "UPDATE telemetry SET battery_pct = 101 WHERE id = 1",
            "UPDATE telemetry SET link_quality_pct = -1 WHERE id = 1",
            "UPDATE communication_records SET size_kb = 0 WHERE id = 1",
            "UPDATE communication_records SET mode = 'Other' WHERE id = 1",
            "UPDATE communication_records SET status = 'Other' WHERE id = 1",
        ]
        for query in queries:
            with self.subTest(query=query):
                with self.assertRaises(sqlite3.IntegrityError):
                    with self.connection:
                        self.connection.execute(query)

    def test_empty_database_stays_empty_on_restart(self):
        with self.connection:
            for table in ("telemetry", "communication_records", "mission_events"):
                self.connection.execute(f"DELETE FROM {table}")
        self.connection.close()
        self.connection = open_database(self.path)
        self.assertEqual(get_summary(self.connection), (None, 0, None, None))
        self.assertEqual(get_telemetry(self.connection), [])
        self.assertEqual(get_communications(self.connection), [])
        self.assertEqual(get_events(self.connection), [])


if __name__ == "__main__":
    unittest.main()
