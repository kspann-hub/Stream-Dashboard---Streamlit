import requests
import pandas as pd
import os
import time
import hmac
import hashlib
import json
import re
from datetime import datetime

# --- Credentials ---
import toml
secrets = toml.load(".streamlit/secrets.toml")
CXALLOY_SECRET_KEY = secrets["cxalloy"]["secret"]
CXALLOY_IDENTIFIER  = secrets["cxalloy"]["identifier"]

BASE_URL = "https://tq.cxalloy.com/api/v1"
DATA_FOLDER = "data"

def make_headers(body_str=None):
    timestamp = str(int(time.time()))
    message = (body_str + timestamp) if body_str else timestamp
    signature = hmac.new(
        CXALLOY_SECRET_KEY.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()
    return {
        "Content-Type":       "application/json",
        "cxalloy-identifier": CXALLOY_IDENTIFIER,
        "cxalloy-signature":  signature,
        "cxalloy-timestamp":  timestamp,
        "user-agent":         "criticalarc-dashboard/v1.0"
    }

def safe_folder_name(name):
    return re.sub(r'[^a-zA-Z0-9_\-]', '_', name).strip('_')

def fetch_get(endpoint, project_id, extra_params=""):
    """Paginated GET request"""
    all_data = []
    page = 1
    while True:
        url = f"{BASE_URL}/{endpoint}?project_id={project_id}&page={page}{extra_params}"
        r = requests.get(url, headers=make_headers())
        r.raise_for_status()
        data = r.json()
        records = data if isinstance(data, list) else []
        all_data.extend(records)
        if len(records) < 500:
            break
        page += 1
    return all_data

def fetch_post(endpoint, project_id, include=None):
    """Paginated POST request"""
    all_data = []
    page = 1
    while True:
        body = {"project_id": project_id, "page": page}
        if include:
            body["include"] = include
        body_str = json.dumps(body, separators=(',', ':'))
        r = requests.post(
            f"{BASE_URL}/{endpoint}",
            headers=make_headers(body_str=body_str),
            data=body_str
        )
        r.raise_for_status()
        data = r.json()
        records = data.get("records", [])
        print(f"    page {page}: {len(records)} records")
        all_data.extend(records)
        if len(records) < 500:
            break
        page += 1
    return all_data

def flatten_issues(data):
    for row in data:
        # Flatten extended_status
        es = row.get("extended_status") or {}
        row["open_date"]             = es.get("open_date", "")
        row["open_person"]           = es.get("open_person", "")
        row["in_progress_date"]      = es.get("in_progress_date", "")
        row["in_progress_person"]    = es.get("in_progress_person", "")
        row["pending_review_date"]   = es.get("pending_review_date", "")
        row["pending_review_person"] = es.get("pending_review_person", "")
        row["closed_date"]           = es.get("closed_date", "")
        row["closed_person"]         = es.get("closed_person", "")
        # Flatten first comment
        comments = row.get("comments") or []
        comment = comments[0] if comments else {}
        row["created_name"]      = comment.get("created_name", "")
        row["comment"]           = comment.get("comment", "")
        row["issuecomment_id"]   = comment.get("issuecomment_id", "")
        row["fk_issue"]          = comment.get("fk_issue", "")
    return data

def flatten_checklists(data):
    for row in data:
        es = row.get("extended_status") or {}
        row["script_in_development_date"]                    = es.get("script_in_development_date", "")
        row["assigned_date"]                                 = es.get("assigned_date", "")
        row["in_progress_date"]                              = es.get("in_progress_date", "")
        row["installation_ready_(pre-energization)_date"]    = es.get("installation_ready_(pre-energization)_date", "")
        row["de-energized_inspection_complete_(cxa)_date"]   = es.get("de-energized_inspection_complete_(cxa)_date", "")
        row["contractor_complete_date"]                      = es.get("contractor_complete_date", "")
        row["verified_date"]                                 = es.get("verified_date", "")
        row["removed_from_scope_date"]                       = es.get("removed_from_scope_date", "")
    return data

def flatten_tests(data):
    for row in data:
        attempts = row.get("attempts") or []
        row["status_change_date"] = attempts[-1]["status_change_date"] if attempts else ""
        es = row.get("extended_status") or {}
        row["script_in_development_date"] = es.get("script_in_development_date", "")
        row["assigned_date"]              = es.get("assigned_date", "")
        row["in_progress_date"]           = es.get("in_progress_date", "")
        row["failed_date"]                = es.get("failed_date", "")
        row["passed_date"]                = es.get("passed_date", "")
    return data

# --- Fetch all projects ---
print("Fetching all projects...\n")
r = requests.get(f"{BASE_URL}/project", headers=make_headers())
r.raise_for_status()
projects = r.json()

print("Found projects:")
for p in projects:
    print(f"  [{p['project_id']}] {p['name']}")

# --- Loop each project ---
for p in projects:
    pid    = p["project_id"]
    pname  = p["name"]
    folder = os.path.join(DATA_FOLDER, safe_folder_name(pname))
    os.makedirs(folder, exist_ok=True)

    log_entries = []
    pull_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"\n{'='*50}")
    print(f"Project: {pname} (ID: {pid})")
    print(f"Saving to: {folder}/")
    print('='*50)

    # Define endpoints: (filename, fetch_fn, args, flatten_fn)
    endpoints = [
        ("issues",      lambda pid=pid: flatten_issues(fetch_post("issue", pid, include=["comments","time_to_close","extended_status","collaborators"]))),
        ("checklists",  lambda pid=pid: flatten_checklists(fetch_post("checklist", pid, include=["time_to_close","extended_status"]))),
        ("tests",       lambda pid=pid: flatten_tests(fetch_post("test", pid, include=["attempts"]))),
        ("equipment",   lambda pid=pid: fetch_get("equipment", pid, "&include=systems,zones,attributes,areas_served")),
        ("people",      lambda pid=pid: fetch_get("person", pid)),
        ("companies",   lambda pid=pid: fetch_get("company", pid)),
    ]

    for name, fetch_fn in endpoints:
        print(f"\n  Fetching {name}...")
        try:
            records = fetch_fn()
            df = pd.DataFrame(records)
            filepath = os.path.join(folder, f"{name}.csv")
            df.to_csv(filepath, index=False)
            print(f"  ✓ {name}.csv  ({len(df)} rows)")
            log_entries.append({"file": f"{name}.csv", "rows": len(df), "status": "success", "pulled_at": pull_time})
        except Exception as e:
            print(f"  ✗ {name}: {e}")
            log_entries.append({"file": f"{name}.csv", "rows": 0, "status": f"error: {e}", "pulled_at": pull_time})

    pd.DataFrame(log_entries).to_csv(os.path.join(folder, "_last_pulled.csv"), index=False)
    print(f"\n  → Log saved: _last_pulled.csv")

print("\n✓ All done! Check your data/ folder.")