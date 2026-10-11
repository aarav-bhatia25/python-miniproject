import random
from datetime import datetime, timedelta


def seed_database(connection):
    rng = random.Random(42)
    start = datetime(2026, 1, 15, 8, 0)
    telemetry = []
    battery = 76.0
    for i in range(200):
        change = -rng.uniform(0.5, 1.2) if i % 140 < 80 else rng.uniform(0.8, 1.6)
        battery = round(max(10, min(100, battery + change)), 1)
        temperature = round(18 + 12 * ((i % 40) / 40) + rng.uniform(-2, 2), 1)
        link = round(rng.uniform(10, 35) if i % 30 < 6 else rng.uniform(65, 98), 1)
        time = start + timedelta(minutes=5 * i)
        telemetry.append((time.strftime("%Y-%m-%d %H:%M:%S"), battery, temperature,
                          link, "Safe" if battery < 20 else "Normal"))
    connection.executemany(
        """INSERT INTO telemetry
           (recorded_at, battery_pct, temperature_c, link_quality_pct, operating_mode)
           VALUES (?, ?, ?, ?, ?)""", telemetry
    )

    records = []
    modes = ("TT&C", "SSTV", "Codec2", "M17")
    sizes = {"TT&C": (1, 5), "SSTV": (80, 200), "Codec2": (10, 40), "M17": (20, 60)}
    notes = {"Sent": "Sample transfer completed.", "Failed": "Sample transfer failed during a weak link.",
             "Pending": "Sample record waiting for a communication window."}
    for i in range(80):
        mode = modes[i % 4]
        status = "Pending" if i >= 64 else ("Failed" if i % 7 == 0 else "Sent")
        time = start + timedelta(minutes=12 * i)
        records.append((time.strftime("%Y-%m-%d %H:%M:%S"), mode,
                        round(rng.uniform(*sizes[mode]), 1), status, notes[status]))
    connection.executemany(
        """INSERT INTO communication_records (created_at, mode, size_kb, status, notes)
           VALUES (?, ?, ?, ?, ?)""", records
    )

    events = [
        (-30, "SomaiyaPod", "Launch preparation", "Complete", "Demo satellite secured in deployer."),
        (-20, "SomaiyaPod", "Release command logged", "Complete", "Demo release sequence started."),
        (-19, "SomaiyaPod", "Separation confirmed", "Complete", "Demo separation switch activated."),
        (-18, "SomaiyaSat", "Initialization started", "Complete", "Demo onboard systems powered on."),
        (-5, "SomaiyaSat", "Initialization completed", "Complete", "Demo systems ready for operations."),
        (0, "SomaiyaSat", "First housekeeping received", "Complete", "First synthetic telemetry record received."),
    ]
    connection.executemany(
        """INSERT INTO mission_events (occurred_at, component, event_name, outcome, notes)
           VALUES (?, ?, ?, ?, ?)""",
        [((start + timedelta(minutes=offset)).strftime("%Y-%m-%d %H:%M:%S"),
          component, name, outcome, note) for offset, component, name, outcome, note in events]
    )
