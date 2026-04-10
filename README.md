# CriticalArc Commissioning Dashboard

A Streamlit dashboard for tracking commissioning progress on data center (and aviation) projects. Pulls data from the CxAlloy API, syncs it to a local SQLite database, and renders interactive visualizations — loading in seconds instead of minutes.

---

## Table of Contents

1. [How It Works](#how-it-works)
2. [Data Flow](#data-flow)
3. [Project Structure](#project-structure)
4. [File-by-File Breakdown](#file-by-file-breakdown)
5. [Setup](#setup)
6. [Running the Dashboard](#running-the-dashboard)
7. [Understanding the Data](#understanding-the-data)
8. [Dashboard Tabs & Analysis](#dashboard-tabs--analysis)
9. [Configuration](#configuration)
10. [Deploying to Streamlit Cloud](#deploying-to-streamlit-cloud)
11. [Troubleshooting](#troubleshooting)

---

## How It Works

The dashboard solves a core problem: the CxAlloy API can take several minutes to return data for large projects. Instead of making users wait on every page load, we sync data in the background and serve it from a local SQLite database.

```
CxAlloy API → sync_logic.py → dashboard_data.db → cxalloy.py reads DB → cleaning.py → layout.py renders
```

The first time the app runs, data is pulled from the API and stored locally. Every subsequent page load reads from SQLite in milliseconds. The sync repeats every 12 hours to keep data fresh.

---

## Data Flow

Here is the complete journey of data from CxAlloy to your browser:

### Step 1: Sync (sync_logic.py)

The sync process authenticates with CxAlloy using HMAC-SHA256 signatures, then pulls six datasets for each project:

| Endpoint | Method | Dataset | What It Contains |
|----------|--------|---------|------------------|
| `/project` | GET | Projects | Project list with IDs, names, status |
| `/issue` | POST | Issues | Deficiencies, punch list items, RFIs |
| `/checklist` | POST | Checklists | Pre-functional checklists (L2, L3, L4, FAT) |
| `/test` | POST | Tests | Functional performance tests |
| `/person` | GET | People | Team members assigned to the project |
| `/company` | GET | Companies | Contractor and subcontractor firms |
| `/equipment` | GET | Equipment | Mechanical/electrical units with attributes |

Each dataset is paginated (500 records per page). The sync fetches all pages, then writes the results to SQLite tables. Nested JSON fields (like `extended_status`, `comments`, `collaborators`) are serialized as JSON strings for storage.

### Step 2: Read (utils/cxalloy.py)

When the dashboard loads, `load_project_data()` checks if `dashboard_data.db` exists:

- **If yes** → reads from SQLite (fast, milliseconds)
- **If no** → falls back to live API calls (slow, minutes)

JSON strings are parsed back into dicts/lists so downstream code works the same either way.

### Step 3: Clean (utils/cleaning.py)

Raw data goes through `clean_all()`, which calls specialized cleaners for each dataset:

- **Standardize columns** — lowercase, strip whitespace, consistent naming
- **Flatten extended_status** — extracts date fields like `in_progress_date`, `finished_date` from nested JSON into flat columns
- **Resolve assigned companies** — maps `assigned_key` IDs back to person/company names using the People and Companies lookup tables
- **Calculate aging** — computes `days_open` and `aging_category` for issues based on creation date
- **Parse dates** — converts date strings to proper datetime objects

### Step 4: Filter (utils/filters.py)

The sidebar lets users filter by discipline, status, contractor, and date range. `apply_filters()` takes the cleaned DataFrames and returns filtered subsets.

### Step 5: Render (layout.py)

The filtered data is passed to `render()`, which builds four tabs of interactive Plotly charts, KPI cards, and data tables.

---

## Project Structure

```
Stream-Dashboard---Streamlit/
│
├── app.py                   # Entry point — config, sidebar, CSS, launches everything
├── layout.py                # All visualizations — charts, KPIs, tables across 4 tabs
├── config.py                # Project-specific settings (statuses, colors, pipeline)
│
├── sync_logic.py            # Core sync engine — API calls + SQLite writes
├── sync_job.py              # Local runner — calls sync_logic on a timer
├── background_sync.py       # Cloud runner — daemon thread for Streamlit Cloud
│
├── utils/
│   ├── cxalloy.py           # Data loader — reads SQLite or falls back to API
│   ├── cleaning.py          # Data transformation — standardize, flatten, resolve lookups
│   └── filters.py           # Sidebar filter application
│
├── .streamlit/
│   └── secrets.toml         # API credentials (NEVER commit this)
│
├── data/                    # CSV exports from inspect_data.py (for debugging)
├── dashboard_data.db        # SQLite database (auto-generated, do NOT commit)
├── inspect_data.py          # Debug utility — dumps raw API data to CSVs
├── requirements.txt         # Python dependencies
├── .gitignore
└── README.md
```

---

## File-by-File Breakdown

### app.py — The Entry Point

This is what Streamlit runs. It handles:

1. **Page config** — sets title, layout, favicon
2. **Starts background sync** — calls `background_sync.start_background_sync()` so data stays fresh
3. **Loads project list** — calls `load_all_projects()` to populate the sidebar dropdown
4. **Sidebar** — project selector, discipline/status/contractor filters, date range
5. **Global CSS** — dark theme styling, KPI card styles, fonts
6. **Calls layout.render()** — passes config, filters, and data to the rendering engine

Run with: `streamlit run app.py`

### layout.py — All Visualizations

The `render()` function receives cleaned data and builds four tabs. Each tab follows the same pattern: extract data → compute metrics → render KPI cards → render charts → render tables. Uses Plotly for all charts (dark theme, consistent styling).

Helper functions:
- `plotly_bar()` / `plotly_donut()` / `plotly_hbar_pct()` — chart builders with consistent theming
- `kpi_card()` — renders styled metric cards
- `section()` — renders section headers
- `format_assigned()` — combines person name + company for display

### config.py — Project Configuration

Controls project-specific behavior without touching code:

```python
PROJECT_TYPE = "data_center"          # or "aviation"
BRAND_NAME = "CriticalArc"
BRAND_COLOR = "#39B54A"

ISSUE_STATUSES = [...]                # valid issue statuses
checklist_complete_statuses = [...]   # which statuses count as "done"
CHECKLIST_PIPELINE = [...]            # workflow stages with their date field names
```

When setting up a new project, this is the first file to update.

### sync_logic.py — The Sync Engine

Contains all shared logic used by both local and cloud sync:

- `_make_headers()` — generates HMAC-SHA256 auth headers for CxAlloy
- `api_get()` / `api_post()` — paginated API callers (auto-fetches all pages)
- `save_to_db()` — writes a DataFrame to SQLite, replacing old data for that project
- `sync_project()` — pulls all 6 datasets for one project using parallel threads
- `sync_all()` — fetches the project list, then syncs each project

Reads credentials from Streamlit secrets (Cloud) or `.streamlit/secrets.toml` (local).

### sync_job.py — Local Sync Runner

A simple wrapper around `sync_logic.py` for running locally:

```bash
python sync_job.py
```

Runs `sync_all()` immediately, then repeats every 12 hours using APScheduler. Use this when you want to manually control when syncs happen, or when developing locally.

### background_sync.py — Cloud Sync Runner

Starts a daemon thread that runs `sync_all()` in the background. Called from `app.py` on startup. The thread:

1. Runs once immediately when the app starts
2. Sleeps for 12 hours
3. Repeats

The `daemon=True` flag means it dies when the main app stops — no orphan processes. The `_sync_started` flag prevents multiple threads if Streamlit re-runs the script.

### utils/cxalloy.py — Data Loader

Two main functions:

- `load_all_projects()` — returns a DataFrame of all projects (for the sidebar dropdown)
- `load_project_data()` — returns a dict of 6 DataFrames for one project

`load_project_data()` checks for `dashboard_data.db` first. If it exists, reads from SQLite (fast). If not, calls the CxAlloy API directly (slow fallback). Results are cached with `@st.cache_data(ttl=60)` so repeated Streamlit reruns within 60 seconds don't re-read the database.

### utils/cleaning.py — Data Cleaning

The `clean_all()` function orchestrates cleaning across all datasets:

- `clean_issues()` — adds aging calculations, parses dates, resolves companies
- `clean_checklists()` — flattens extended_status dates, derives checklist level from type_name
- `clean_tests()` — counts attempts, resolves companies
- `clean_equipment()` — parses attributes JSON for building phase, floor, zones

Key helper functions:
- `standardize_columns()` — consistent column naming
- `flatten_extended_status()` — extracts workflow dates from nested JSON
- `resolve_assigned_company()` — maps person/role IDs to company names

### utils/filters.py — Sidebar Filters

`apply_filters()` takes a DataFrame and a filter dict, returning rows that match all active filters. Supports filtering by: discipline, status, assigned company, date range, and priority.

### inspect_data.py — Debug Utility

Dumps raw API data to CSV files in the `data/` folder for manual inspection:

```bash
python inspect_data.py
```

Useful for understanding what the API returns, checking column names, and debugging data issues. Output goes to `data/{project_name}/issues.csv`, `data/{project_name}/checklists.csv`, etc.

---

## Setup

### Prerequisites

- Python 3.11+
- A CxAlloy API account with identifier and secret
- VS Code (recommended)

### Installation

1. Clone the repo:
   ```bash
   git clone https://github.com/YOUR_USERNAME/Stream-Dashboard---Streamlit.git
   cd Stream-Dashboard---Streamlit
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create your secrets file at `.streamlit/secrets.toml`:
   ```toml
   [cxalloy]
   identifier = "your-identifier-here"
   secret = "your-secret-here"
   ```

### Recommended VS Code Extensions

- **Python** (Microsoft) — language support, linting, debugging
- **SQLite Viewer** — click `dashboard_data.db` to browse synced data visually

---

## Running the Dashboard

### Quick Start (single terminal)

```bash
streamlit run app.py
```

The background sync thread starts automatically. First load takes a few minutes while data syncs. After that, every load is instant.

### Development Mode (two terminals)

For more control during development, run sync and dashboard separately:

```bash
# Terminal 1 — sync data (split terminal with Ctrl+Shift+5 in VS Code)
python sync_job.py

# Terminal 2 — run dashboard
streamlit run app.py
```

This lets you watch sync progress in real time and restart either process independently.

### Inspecting Raw Data

To dump raw API data to CSV for analysis or debugging:

```bash
python inspect_data.py
```

CSVs are saved to the `data/` folder. Open them in Excel or VS Code to inspect column names, values, and data quality.

### Querying the SQLite Database Directly

You can query synced data without running the dashboard:

```bash
# See all tables
python -c "
import sqlite3
conn = sqlite3.connect('dashboard_data.db')
tables = conn.execute(\"SELECT name FROM sqlite_master WHERE type='table'\").fetchall()
print([t[0] for t in tables])
"

# Check row counts
python -c "
import sqlite3
conn = sqlite3.connect('dashboard_data.db')
for table in ['Issues', 'Checklists', 'Tests', 'People', 'Companies', 'Equipment']:
    try:
        count = conn.execute(f'SELECT COUNT(*) FROM [{table}]').fetchone()[0]
        print(f'{table}: {count} rows')
    except: pass
"

# Check unique statuses
python -c "
import sqlite3, pandas as pd
conn = sqlite3.connect('dashboard_data.db')
print(pd.read_sql('SELECT DISTINCT status FROM [Issues]', conn))
print(pd.read_sql('SELECT DISTINCT status FROM [Checklists]', conn))
"

# Check when data was last synced
python -c "
import sqlite3, pandas as pd
conn = sqlite3.connect('dashboard_data.db')
print(pd.read_sql('SELECT * FROM _sync_log ORDER BY synced_at DESC LIMIT 5', conn))
"
```

Or use the SQLite Viewer VS Code extension to browse `dashboard_data.db` visually.

---

## Understanding the Data

### Issues

Issues represent deficiencies, punch list items, or problems found during commissioning. Key fields:

| Field | Description |
|-------|-------------|
| `name` | Issue identifier (e.g., "ISS-001") |
| `status` | Open, In Progress, Pending Verification, Closed, Void |
| `priority` | Severity level |
| `discipline` | Trade/division (Mechanical, Electrical, etc.) |
| `assigned_name` | Person or role assigned |
| `assigned_company` | Contractor company (resolved from lookup) |
| `date_created` | When the issue was opened |
| `days_open` | Calculated age in days |
| `aging_category` | ">60 Days", "45-60 Days", or "Under 45 Days" |

### Checklists

Pre-functional checklists verify that equipment is installed correctly before functional testing. Key fields:

| Field | Description |
|-------|-------------|
| `status` | Not Started, In Progress, GC to Verify, Finished |
| `level` | Derived from type_name — L2, L3, L4, or FAT |
| `discipline` | Trade responsible |
| `assigned_company` | Contractor assigned |
| `not_started_date` | When checklist entered this stage |
| `in_progress_date` | When work began |
| `gc_to_verify_date` | When submitted for GC review |
| `finished_date` | When completed |

The `level` field is derived from `type_name`:
- **L2** — Installation Verification
- **L3** — Prefunctional
- **L4** — Component Verification
- **FAT** — Factory Acceptance Test

### Tests

Functional performance tests run after checklists are complete. Key fields:

| Field | Description |
|-------|-------------|
| `status` | Passed, Failed, Not Started, In Progress |
| `asset_name` | Equipment unit being tested |
| `assigned_company` | Contractor running the test |
| `attempt_count` | Number of test attempts |

### Equipment

Physical equipment units tracked in the project. Key fields:

| Field | Description |
|-------|-------------|
| `name` | Equipment tag/identifier |
| `type` | Equipment category |
| `discipline` | Trade |
| `status` | Delivered, Installation in Progress, Released, etc. |
| `attributes` | JSON containing Building Phase, Floor, and other metadata |
| `cl_total` / `cl_done` | Linked checklist counts (joined in layout.py) |
| `ts_total` / `ts_passed` | Linked test counts (joined in layout.py) |
| `iss_total` / `iss_open` | Linked issue counts (joined in layout.py) |

---

## Dashboard Tabs & Analysis

### Tab 1: Issue Tracking

**Purpose:** Monitor open deficiencies and identify bottlenecks.

What you'll see:
- **KPI cards** — total open issues, aging >60 days (red), aging 45-60 days (yellow), in progress, high priority
- **Priority donut** — distribution of all issues by severity
- **Status bar chart** — Open vs In Progress vs Pending Verification vs Closed
- **Issues by Division** — which trades have the most issues
- **Issues by Contractor** — which companies have the most issues
- **Open Issues table** — sortable detail view with aging indicators
- **All Issues expandable** — full dataset with dates and descriptions

**Key analysis questions this answers:**
- Which contractors have the most unresolved issues?
- Are issues being closed on time or aging out?
- Which disciplines are generating the most deficiencies?

### Tab 2: Checklists

**Purpose:** Track pre-functional checklist completion across all levels.

What you'll see:
- **Status donuts by level** — one donut per active level (L2, L3, L4, FAT) showing Not Started / In Progress / GC to Verify / Finished
- **Completion by Discipline** — stacked bar showing how far each trade has progressed
- **Checklists by Level & Discipline** — stacked bar showing volume distribution
- **Open Checklists by Company & Level** — which contractors have the most incomplete checklists
- **Completion by Contractor** — table with total, completed, and completion percentage
- **Pending Assignment** — checklists assigned to roles instead of actual contractors

**Key analysis questions this answers:**
- What percentage of checklists are complete for each trade?
- Which contractors are falling behind?
- Are there checklists still unassigned to a real company?

### Tab 3: Functional Tests

**Purpose:** Monitor test execution and pass rates.

What you'll see:
- **KPI cards** — total tests, passed, failed, not started
- **Status donut** — overall distribution
- **Pass rate gauge** — percentage of tests that have passed
- **Results by Equipment Unit** — stacked bar showing pass/fail/not started per unit
- **Results by Contractor** — which companies have the best/worst pass rates
- **All Tests expandable** — full dataset

**Key analysis questions this answers:**
- What is the overall pass rate?
- Which equipment units are failing tests?
- Which contractors are producing the best test results?

### Tab 4: Equipment

**Purpose:** Equipment-level view linking checklists, tests, and issues to physical units.

What you'll see:
- **KPI cards** — total equipment, released, delivered, installing
- **Filters** — narrow by Building Phase and Floor
- **Equipment by Type** — volume of each equipment category
- **Checklist Completion by Type** — how complete are checklists for each equipment type
- **Issues by Equipment Type** — open vs closed issues per type
- **Equipment by Building Phase** — summary with checklist % and open issue counts
- **All Equipment expandable** — full table with linked checklist/test/issue counts

**Key analysis questions this answers:**
- Which equipment types have the most incomplete checklists?
- Which building phases are furthest behind?
- Which equipment has open issues blocking progress?

---

## Configuration

### Updating for a New Project

Edit `config.py` to match your project's data. To discover what values exist:

```bash
python -c "
import sqlite3, pandas as pd
conn = sqlite3.connect('dashboard_data.db')
print('=== Issue Statuses ===')
print(pd.read_sql('SELECT DISTINCT status FROM [Issues]', conn))
print()
print('=== Checklist Statuses ===')
print(pd.read_sql('SELECT DISTINCT status FROM [Checklists]', conn))
print()
print('=== Checklist Types ===')
try: print(pd.read_sql('SELECT DISTINCT type_name FROM [Checklists]', conn))
except: print('no type_name column')
print()
print('=== Extended Status Fields ===')
import json
df = pd.read_sql('SELECT extended_status FROM [Checklists] LIMIT 5', conn)
for val in df['extended_status']:
    try:
        print(list(json.loads(val).keys()))
        break
    except: pass
"
```

Then update `config.py` accordingly:

```python
PROJECT_TYPE = "data_center"
BRAND_NAME = "CriticalArc"
BRAND_COLOR = "#39B54A"

ISSUE_STATUSES = ["Open", "In Progress", "Pending Verification", "Closed", "Void"]
CHECKLIST_VERIFIED = ["Finished", "GC to Verify"]
checklist_complete_statuses = ["Finished"]

CHECKLIST_PIPELINE = [
    ("Not Started", "not_started_date"),
    ("In Progress", "in_progress_date"),
    ("GC to Verify", "gc_to_verify_date"),
    ("Finished", "finished_date"),
]
```

Also update the `flatten_extended_status` call in `cleaning.py` to match the pipeline date fields.

### Sync Interval

To change how often data refreshes:

- **Local:** edit `SYNC_INTERVAL_MINUTES` in `sync_job.py`
- **Cloud:** edit `interval_hours` in the `start_background_sync()` call in `app.py`

---

## Deploying to Streamlit Cloud

1. Push all files to GitHub (make sure `secrets.toml` and `dashboard_data.db` are in `.gitignore`)
2. Connect your repo in [Streamlit Cloud](https://share.streamlit.io)
3. Add your CxAlloy credentials under **Settings → Secrets**:
   ```toml
   [cxalloy]
   identifier = "your-identifier-here"
   secret = "your-secret-here"
   ```
4. Deploy — the background sync starts automatically

**First visit behavior:** The first visitor after a deploy triggers the initial sync. They'll see data load via the API fallback (slow). Once the background sync completes, all subsequent visitors get instant loads from SQLite.

**Note:** Streamlit Cloud apps can go to sleep after inactivity. When they wake up, the database is gone (ephemeral filesystem). The background sync will rebuild it automatically — the first visitor just waits for one sync cycle.

---

## Troubleshooting

**Dashboard shows "No data available" on all tabs**
- The sync hasn't finished yet. Check logs for sync progress.
- Verify credentials in `secrets.toml` are correct.
- Run `python sync_job.py` manually and watch for errors.

**Sync says "Found 0 projects"**
- Check that your API credentials have access to at least one project.
- Run the direct API test:
  ```bash
  python -c "
  from sync_logic import api_get
  projects = api_get('project')
  print(f'Found {len(projects)} projects')
  for p in projects: print(p.get('project_id'), p.get('name'))
  "
  ```

**"type dict is not supported" error during sync**
- Nested JSON fields aren't being serialized. Make sure `save_to_db()` in `sync_logic.py` converts dicts/lists to JSON strings before writing.

**"UnboundLocalError: cannot access local variable 'equipment'"**
- A dataset is missing from `all_sheets`. Make sure all six keys are extracted at the top of `layout.py`'s `render()` function with `.get()` fallbacks.

**Dashboard is slow despite sync completing**
- Check that `dashboard_data.db` exists in your project folder.
- Verify `load_project_data()` in `cxalloy.py` is reading from SQLite (not falling back to API).
- Check `@st.cache_data` TTL — if set too low, it re-reads the database too often.

**Charts show 0% or 100% incorrectly**
- Check that `config.py` statuses match your actual data.
- Empty strings from `flatten_extended_status` may need to be converted to `pd.NA` — check `cleaning.py`.

---

## .gitignore

Make sure these are in your `.gitignore`:

```
.streamlit/secrets.toml
dashboard_data.db
__pycache__/
*.pyc
data/
```