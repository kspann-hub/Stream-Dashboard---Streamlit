"""
sync_job.py — Background worker that pulls CxAlloy data into a local SQLite DB.
Run in a separate terminal: python sync_job.py
"""

import time
import hmac
import hashlib
import json
import sqlite3
import requests
import pandas as pd
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from apscheduler.schedulers.blocking import BlockingScheduler

print("Starting sync job...")

# ── Config ──────────────────────────────────────────────────────────
# Read secrets the same way Streamlit does — from .streamlit/secrets.toml
import tomllib
SECRETS = tomllib.loads(Path(".streamlit/secrets.toml").read_text())
IDENTIFIER = SECRETS["cxalloy"]["identifier"]
SECRET     = SECRETS["cxalloy"]["secret"]

BASE_URL = "https://tq.cxalloy.com/api/v1"
DB_PATH  = "dashboard_data.db"

# ── Put your project IDs here ──────────────────────────────────────
# These are the projects you want pre-fetched.
# You can also pull this list dynamically from the /project endpoint.
PROJECT_IDS = []  # e.g. [101, 202, 303] — fill in your actual IDs

SYNC_INTERVAL_MINUTES = 480  # how often to re-sync - currently set to every 8 hours, but adjust as needed

# ── API helpers (same logic as your cxalloy.py, no Streamlit dependency) ──

def _make_headers(body_str: str = None) -> dict:
    timestamp = str(int(time.time()))
    message = (body_str + timestamp) if body_str else timestamp
    signature = hmac.new(
        SECRET.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return {
        "Content-Type":       "application/json",
        "cxalloy-identifier": IDENTIFIER,
        "cxalloy-signature":  signature,
        "cxalloy-timestamp":  timestamp,
        "user-agent":         "criticalarc-dashboard / v1.0",
    }

def api_get(endpoint: str, params: dict = None) -> list:
    results, page = [], 1
    while True:
        p = {**(params or {}), "page": page}
        resp = requests.get(f"{BASE_URL}/{endpoint}", headers=_make_headers(), params=p)
        if resp.status_code != 200:
            print(f"  ✗ GET {endpoint} → {resp.status_code}: {resp.text[:200]}")
            break
        data = resp.json()
        if isinstance(data, list):
            results.extend(data)
            if len(data) < 500:
                break
        else:
            break
        page += 1
    return results

def api_post(endpoint: str, body: dict, include: list = None) -> list:
    results, page = [], 1
    while True:
        payload = {**body, "page": page}
        if include:
            payload["include"] = include
        body_str = json.dumps(payload, separators=(",", ":"))
        resp = requests.post(f"{BASE_URL}/{endpoint}", headers=_make_headers(body_str), data=body_str)
        if resp.status_code != 200:
            print(f"  ✗ POST {endpoint} → {resp.status_code}: {resp.text[:200]}")
            break
        data = resp.json()
        records = data.get("records", []) if isinstance(data, dict) else data if isinstance(data, list) else []
        results.extend(records)
        if len(records) < 500:
            break
        page += 1
    return results

# ── Sync logic ──────────────────────────────────────────────────────

def save_to_db(table_name: str, project_id: int, df: pd.DataFrame):
    if df.empty:
        return
    df = df.copy()
    df["_project_id"] = project_id
    # Convert any nested dicts/lists to JSON strings
    for col in df.columns:
        if df[col].apply(lambda x: isinstance(x, (dict, list))).any():
            df[col] = df[col].apply(lambda x: json.dumps(x) if isinstance(x, (dict, list)) else x)
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(f"DELETE FROM [{table_name}] WHERE _project_id = ?", (project_id,))
    except sqlite3.OperationalError:
        pass
    df.to_sql(table_name, conn, if_exists="append", index=False)
    conn.commit()
    conn.close()

def init_db():
    """Create the sync metadata table if needed."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS _sync_log (
            project_id INTEGER,
            synced_at TEXT,
            status TEXT
        )
    """)
    conn.commit()
    conn.close()

def sync_project(project_id: int):
    print(f"  Syncing project {project_id}...")
    start = time.time()

    def fetch_issues():
        return "Issues", pd.DataFrame(api_post("issue", {"project_id": project_id}, include=["comments", "time_to_close", "extended_status", "collaborators"]))
    def fetch_checklists():
        return "Checklists", pd.DataFrame(api_post("checklist", {"project_id": project_id}, include=["time_to_close", "extended_status"]))
    def fetch_tests():
        return "Tests", pd.DataFrame(api_post("test", {"project_id": project_id}, include=["attempts"]))
    def fetch_people():
        return "People", pd.DataFrame(api_get("person", {"project_id": project_id}))
    def fetch_companies():
        return "Companies", pd.DataFrame(api_get("company", {"project_id": project_id}))
    def fetch_equipment():
        return "Equipment", pd.DataFrame(api_get("equipment", {"project_id": project_id, "include": "systems,zones,attributes,areas_served"}))

    with ThreadPoolExecutor(max_workers=6) as pool:
        results = dict(pool.map(lambda f: f(), [
            fetch_issues, fetch_checklists, fetch_tests,
            fetch_people, fetch_companies, fetch_equipment,
        ]))

    for table_name, df in results.items():
        save_to_db(table_name, project_id, df)
        print(f"    {table_name}: {len(df)} rows")

    # Log the sync
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO _sync_log (project_id, synced_at, status) VALUES (?, datetime('now'), 'ok')",
        (project_id,),
    )
    conn.commit()
    conn.close()
    print(f"  ✓ Project {project_id} done in {time.time() - start:.1f}s")

def sync_all():
    print(f"\n{'='*50}")
    print(f"Starting sync at {time.strftime('%H:%M:%S')}")
    print(f"{'='*50}")

    # If no project IDs hardcoded, fetch them all
    global PROJECT_IDS
    if not PROJECT_IDS:
        print("Fetching project list...")
        projects = api_get("project")
        PROJECT_IDS = [p["project_id"] for p in projects if "project_id" in p]
        print(f"Found {len(PROJECT_IDS)} projects")

    for pid in PROJECT_IDS:
        try:
            sync_project(pid)
        except Exception as e:
            import traceback
            traceback.print_exc()

    print(f"\nSync complete at {time.strftime('%H:%M:%S')}")

# ── Main ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()

    # Run once immediately
    sync_all()

    # Then repeat on schedule
    scheduler = BlockingScheduler()
    scheduler.add_job(sync_all, "interval", minutes=SYNC_INTERVAL_MINUTES)
    print(f"\nScheduler running — will re-sync every {SYNC_INTERVAL_MINUTES} minutes. Ctrl+C to stop.")
    scheduler.start()