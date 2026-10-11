# SomaiyaSat Mission Data Dashboard

## Project plan

A Python desktop dashboard for viewing and managing sample mission data for **SomaiyaSat** (the satellite) and **SomaiyaPod** (its deployer). The first version should be a small, understandable application built with **Python, SQLite, and Tkinter**, using synthetic data stored locally.

**Status:** The first version is implemented: three screens, date/mode/status filters, record notes, overview totals, and synthetic data saved in SQLite. The UI uses a dark space theme, status cards, coloured table rows, and a battery history chart drawn with Tkinter Canvas. Add/edit/delete forms and CSV export are still optional future work. The original project plan is kept below.

## Run the dashboard

From this folder, run:

```bash
python3 main.py
```

Use Python 3 with Tkinter installed. No pip packages are required. You can check Tkinter with `python3 -m tkinter`.

The first launch creates `data/mission.db` with 200 telemetry readings, 80 communication records, and six mission events. Later launches reuse that database. The database is ignored by Git so each teammate gets their own demo data.

Sample telemetry covers **15-16 January 2026 (UTC)**. Use those dates when trying filters. Refresh reads saved records; it does not simulate live updates. The demo link score, record sizes, and Safe mode threshold are illustrative assumptions.

Run the database tests with:

```bash
python3 -m unittest discover -s tests -v
```

The tests use temporary databases and do not change the dashboard's data.

## How this fits the space use case

Reference: *KJS-SRS-01 Use Case - Dr. Shinde.pdf*, use case KJS-SRS-01, supplied with the project discussion.

The document describes a complete satellite mission. Our miniproject focuses on its ground-station data visualization component (page 4, workflow E), using the mission's telemetry, communication modes, and deployment events as the data model.

| Context from the document | Proposed dashboard feature |
| --- | --- |
| Battery/power and satellite health monitoring (pages 1-2) | Latest battery and temperature readings, plus telemetry history |
| TT&C/housekeeping, SSTV, Codec2, and M17 communication (pages 1-2) | A searchable table of communication records grouped by mode and status |
| Deployment confirmation and spacecraft initialization (pages 1-2, 4) | A chronological event log for SomaiyaPod release and SomaiyaSat initialization |
| Data prioritization (page 2) | A displayed priority: TT&C first, SSTV second, Codec2/M17 third |

The PDF's broader instructions describe the mission context; they are not all requirements for this miniproject. Building satellite hardware, implementing radio codecs, receiving actual downlinks, predicting orbits, and training onboard AI are outside the proposed scope. Any priority display is a simple rule derived from the document, not an AI model.

The course-level mapping on page 8 is unfilled, so the PDF does not establish the Python lab rubric. This plan follows the requested stack and simple dashboard scope; check it against the actual rubric when available.

## Technology choices

| Tool | Purpose |
| --- | --- |
| Python | Application logic, validation, calculations, and data generation |
| `sqlite3` | Persistent local database and SQL queries |
| `tkinter` and `tkinter.ttk` | Window, navigation, labels, tables, filters, and dialogs |
| `random`, `datetime` | Repeatable synthetic readings and timestamps |
| `pathlib` | Locate the database reliably |
| `csv` (optional) | Export the displayed records |
| `unittest` (during development) | Check database operations and summary calculations |

No third-party Python packages are needed for the proposed version. NumPy, pandas, and seaborn would add dependencies without helping much at this scale. SQLite queries can calculate counts and averages, and Tkinter can display them directly. Use a Python installation with working Tk support; `python3 -m tkinter` can check this before development.

## First version: three screens

Use one Tkinter window with three navigation buttons: **Overview**, **Telemetry**, and **Communication & Events**. Switch frames inside the same window. Keep most of the interface focused on reading data.

### 1. Overview

- Show the mission names and a visible **Synthetic demo data** label.
- Show latest battery percentage, temperature in degrees Celsius, and a demo link-quality score.
- Show pending communication records and transmission success rate.
- Show the latest deployment/initialization event and the timestamp of the latest telemetry reading.
- Provide a Refresh button that reloads saved data; it should not generate new records.

Define success rate as `sent / (sent + failed) * 100`. Exclude pending records, and display `N/A` when no transmissions have been attempted. Label aggregate figures as covering all stored records.

### 2. Telemetry

- Display timestamp, battery percentage, temperature, link-quality score, and operating mode in a `ttk.Treeview` with a scrollbar.
- Add start/end date filters and Apply/Clear controls.
- Sort newest first. Validate date input and reject an end date earlier than the start date.
- Show a clear empty-state message when a filter has no matching records.

### 3. Communication & Events

- Display communication records with mode, creation time, size, derived priority, and status.
- Allow filtering by mode (`TT&C`, `SSTV`, `Codec2`, `M17`) and status (`Pending`, `Sent`, `Failed`).
- Show a second, smaller table below it for deployment and initialization events.
- Use a selected row's details to display longer notes without crowding the table.

**Minimum deliverable:** persistent storage, reliable viewing, navigation, filters, and correct summaries. This matches the requested display-focused dashboard.

**Small management extension, if required by the rubric:** add an Add/Edit dialog for communication records, plus Delete with confirmation. Keep telemetry and deployment events read-only. A status change edits a synthetic database record; it does not transmit data or control a satellite. Complete the viewing workflow before adding these forms.

## Database design

Use a single file, `data/mission.db`, and three tables. Since the demo covers one satellite/deployer pair, a separate satellite registry is unnecessary initially.

| Table | Proposed columns |
| --- | --- |
| `telemetry` | `id INTEGER PRIMARY KEY`, `recorded_at TEXT`, `battery_pct REAL`, `temperature_c REAL`, `link_quality_pct REAL`, `operating_mode TEXT` |
| `communication_records` | `id INTEGER PRIMARY KEY`, `created_at TEXT`, `mode TEXT`, `size_kb REAL`, `status TEXT`, `notes TEXT` |
| `mission_events` | `id INTEGER PRIMARY KEY`, `occurred_at TEXT`, `component TEXT`, `event_name TEXT`, `outcome TEXT`, `notes TEXT` |

Implementation rules:

- Mark essential fields `NOT NULL`. Store timestamps in one consistent UTC format, such as `YYYY-MM-DD HH:MM:SS`, and label UTC in the UI.
- Use `CHECK` constraints for battery/link scores between 0 and 100, positive record sizes, and allowed mode/status values. Also validate inputs in Python for readable error messages.
- Treat `link_quality_pct` as an invented demo score, not a measured RF quantity or a specified mission metric.
- Derive priority from communication mode instead of storing it twice: TT&C = 1, SSTV = 2, Codec2/M17 = 3. Lower numbers mean higher priority; equal priorities use creation time.
- Use SQL placeholders (`?`) for filter values and form inputs.
- Select the latest reading by timestamp, with ID as a tie-breaker. Do not assume the highest ID always has the latest timestamp.
- Calculate counts, averages, and success rate from stored records rather than hard-coding dashboard values.
- Keep database access in functions separate from Tkinter callbacks, and commit successful writes before refreshing the screen.

## Synthetic data approach

Start with a deterministic seed such as `random.Random(42)` and a fixed demo start date. Label all generated records as synthetic in the UI and project report.

Suggested starting dataset:

- **200 telemetry readings:** five-minute intervals; a battery level that changes gradually; temperature and link quality that vary over time.
- **80 communication records:** all four modes and all three statuses, with illustrative sizes in KB and readable notes.
- **6 mission events:** launch preparation, release command logged, separation confirmed, initialization started, initialization completed, and first housekeeping record received. These are invented demo events, not claims about the actual mission.

Include normal readings, a few low-battery readings, poor-link readings, and failed transmissions so the dashboard has useful examples. Any alert thresholds (for example, battery below 20%) are classroom assumptions and must be labeled as such, not mission specifications. Keep event timestamps in a coherent order, with operational records after initialization.

Seed a newly created database once in a transaction. On subsequent launches, load existing records without duplicating or replacing them. Keep reseeding as a deliberate development action so it cannot erase edits during a demo.

## Suggested file structure

```text
python-miniproject/
├── README.md
├── main.py          # Start the application and create the main window
├── database.py      # Schema, queries, and optional record edits
├── seed_data.py     # Deterministic synthetic data generation
├── dashboard.py     # Tkinter frames and navigation
├── data/
│   └── mission.db   # Generated locally on first launch
└── tests/
    └── test_database.py
```

Use functions and, if useful, one small dashboard class. There is no need to add abstract classes, decorators, or threading just to demonstrate imports. Add lab concepts only where they make the implementation clearer. Small local queries should be sufficient for the first version; Tkinter's event loop can handle ordinary button clicks without background workers.

## Build sequence and checkpoints

| Step | Work | Checkpoint |
| --- | --- | --- |
| 1. Fix the scope | Agree on the three screens, fields, synthetic data, and whether editing is required | A short feature checklist everyone can explain |
| 2. Build storage | Create tables and seed records; run queries from a small Python script | Records persist and a second launch does not duplicate them |
| 3. Build the window | Create navigation and empty frames with `ttk` widgets | All three screens open inside one window |
| 4. Connect data | Populate tables and overview labels from SQLite | Displayed values match database queries |
| 5. Add filters | Implement dates, mode, status, clear filters, and empty states | Valid searches return the right records; invalid input gets a readable message |
| 6. Add required management | Only if needed, add communication-record forms and confirmed deletion | Changes survive restart and summaries refresh correctly |
| 7. Finish the demo | Review labels, spacing, scrolling, error handling, and documentation | The app works offline and the team can demonstrate it end to end |

**Start with step 2 after agreeing on the fields.** Getting a few database rows into a Tkinter table early proves the core workflow before spending time on appearance.

## Verification and presentation

Use a temporary database for automated checks so tests never alter demo records. Useful checks include first-run setup, repeat startup, constraints, filtering, latest-reading selection, and the zero-denominator success-rate case. If editing is implemented, also check that valid edits persist and invalid edits leave the database unchanged.

Manually check navigation, scrolling, empty tables, invalid dates, and closing/reopening the application. All displayed units and timestamps should be explicit, and the UI should say that it uses synthetic data rather than suggesting a live feed.

A short demonstration can follow this sequence:

1. Open Overview and explain the satellite/deployer context and synthetic data label.
2. Open Telemetry and filter a date range.
3. Open Communication & Events and filter failed transmissions or a specific mode.
4. Explain the deployment sequence and how the data is stored in SQLite.
5. If editing is included, edit one communication record, refresh the totals, and restart to show persistence.

For the report or viva, include the problem statement, scope, table definitions, screenshots, synthetic-data method, verification results, and limitations. Describe this as a **mission data management dashboard inspired by the SomaiyaSat use case**, not a completed satellite control system.

## Optional additions after the core works

- Export the filtered table with the standard-library `csv` module.
- Implemented: a battery history chart using `tkinter.Canvas`, with an illustrative 20% threshold.
- Add a stored sample pass schedule if the instructor specifically wants communication windows.

Keep these optional. The core project is complete when the three screens display consistent persisted data, navigation and filters work, and the demo can be explained using the Python concepts taught in labs.
