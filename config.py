# ─── config.py ─────────────────────────────────────────────────────────────────
# Central configuration for the CriticalArc Commissioning Dashboard.
# When starting a new project, set PROJECT_TYPE and update secrets.toml.
# Everything else adapts automatically.
# ───────────────────────────────────────────────────────────────────────────────

# ━━━ Step 1: Set your project type ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Options: "aviation", "data_center"
PROJECT_TYPE = "data_center"

# ━━━ Branding (shared across all projects) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BRAND_NAME = "CriticalArc"
BRAND_COLOR = "#39B54A"
ACCENT_COLOR = "#4A90D9"

# ━━━ Project-Type Definitions ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PROJECTS = {

    # ── Aviation ────────────────────────────────────────────────────────────
    "aviation": {

        # How the pipeline chart is built: "date" uses timestamp columns,
        # "status" counts rows by their current status value.
        "pipeline_mode": "date",

        # Checklist pipeline stages (date-based)
        # Each tuple: (display label, date column name in the cleaned data)
        "checklist_pipeline": [
            ("Script in Development", "script_in_development_date"),
            ("Assigned",             "assigned_date"),
            ("In Progress",          "in_progress_date"),
            ("Contractor Complete",  "contractor_complete_date"),
            ("Verified",             "verified_date"),
        ],

        # Which statuses count as "complete" for KPI cards
        "checklist_complete_statuses": [
            "Checklist Complete",
            "Verified",
            "Verified - Not Included in Sampling",
        ],

        # All expected checklist statuses (for donut chart ordering)
        "checklist_statuses": [
            "Script in Development",
            "Assigned",
            "In Progress",
            "Contractor Complete",
            "Verified",
            "Removed from Scope",
        ],

        # Extended status date fields to flatten in cleaning.py
        "checklist_date_fields": [
            "script_in_development_date",
            "assigned_date",
            "in_progress_date",
            "installation_ready_(pre-energization)_date",
            "de-energized_inspection_complete_(cxa)_date",
            "contractor_complete_date",
            "verified_date",
            "removed_from_scope_date",
        ],

        # ── Issues ──────────────────────────────────────────────────────────
        "issue_statuses": ["Open", "In Progress", "Pending Review", "Closed"],

        "issue_status_colors": {
            "Open":           "#E74C3C",
            "In Progress":    "#4A90D9",
            "Pending Review": "#F5A623",
            "Closed":         "#39B54A",
        },

        "issue_priorities": ["1", "2", "3", "4", "5"],

        "issue_priority_colors": {
            "1": "#E74C3C",
            "2": "#F5A623",
            "3": "#4A90D9",
            "4": "#8A8F98",
            "5": "#3E4248",
        },

        # ── Tests ───────────────────────────────────────────────────────────
        "test_statuses": [
            "Script in Development",
            "Assigned",
            "In Progress",
            "Passed",
            "Failed",
            "Deferred to 1B",
            "Voided",
        ],

        "test_status_colors": {
            "Passed":              "#39B54A",
            "Failed":              "#E74C3C",
            "In Progress":         "#4A90D9",
            "Assigned":            "#8A8F98",
            "Script in Development":"#3E4248",
            "Deferred to 1B":      "#6E7FD4",
            "Voided":              "#3E4248",
        },

        # ── Equipment / Location ────────────────────────────────────────────
        "location_filters": ["building", "floor", "space"],
        "tab4_label": "Equipment",
    },

    # ── Data Center ─────────────────────────────────────────────────────────
    "data_center": {

        # Status-based pipeline (date columns are mostly empty)
        "pipeline_mode": "status",

        # Checklist pipeline stages (status-based)
        # Each tuple: (display label, status value to count)
        "checklist_pipeline": [
            ("Not Started",  "Not Started"),
            ("In Progress",  "In Progress"),
            ("GC to Verify", "GC to Verify"),
            ("Finished",     "Finished"),
        ],

        "checklist_complete_statuses": [
            "Finished",
        ],

        "checklist_statuses": [
            "Not Started",
            "In Progress",
            "GC to Verify",
            "Finished",
        ],

        # Still flatten these in case future projects populate them
        "checklist_date_fields": [
            "script_in_development_date",
            "assigned_date",
            "in_progress_date",
            "installation_ready_(pre-energization)_date",
            "de-energized_inspection_complete_(cxa)_date",
            "contractor_complete_date",
            "verified_date",
            "removed_from_scope_date",
        ],

        # ── Issues ──────────────────────────────────────────────────────────
        "issue_statuses": [
            "Open",
            "In Progress",
            "Pending Verification",
            "Closed",
            "Void",
        ],

        "issue_status_colors": {
            "Open":                 "#E74C3C",
            "In Progress":          "#4A90D9",
            "Pending Verification": "#F5A623",
            "Closed":               "#39B54A",
            "Void":                 "#3E4248",
        },

        "issue_priorities": ["High", "Moderate", "Low"],

        "issue_priority_colors": {
            "High":     "#E74C3C",
            "Moderate": "#F5A623",
            "Low":      "#8A8F98",
        },

        # ── Tests ───────────────────────────────────────────────────────────
        "test_statuses": [
            "Not Started",
            "In Progress",
            "Passed",
            "Failed",
        ],

        "test_status_colors": {
            "Passed":      "#39B54A",
            "Failed":      "#E74C3C",
            "In Progress": "#4A90D9",
            "Not Started": "#3E4248",
        },

        # ── Equipment / Location ────────────────────────────────────────────
        # No floor/building data — filter by space only
        "location_filters": ["space"],
        "tab4_label": "Equipment",
    },
}


# ━━━ Helper: get current project config ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def get_config():
    """Return the config dict for the active PROJECT_TYPE."""
    return PROJECTS[PROJECT_TYPE]


# ━━━ Convenience accessors (import these in layout.py / cleaning.py) ━━━━━━━━
def pipeline_mode():
    return get_config()["pipeline_mode"]

def checklist_pipeline():
    return get_config()["checklist_pipeline"]

def checklist_complete_statuses():
    return get_config()["checklist_complete_statuses"]

def checklist_date_fields():
    return get_config()["checklist_date_fields"]

def issue_statuses():
    return get_config()["issue_statuses"]

def issue_status_colors():
    return get_config()["issue_status_colors"]

def issue_priorities():
    return get_config()["issue_priorities"]

def issue_priority_colors():
    return get_config()["issue_priority_colors"]

def test_statuses():
    return get_config()["test_statuses"]

def test_status_colors():
    return get_config()["test_status_colors"]

def location_filters():
    return get_config()["location_filters"]

def tab4_label():
    return get_config()["tab4_label"]

def sidebar_status_options():
    """Status options for the sidebar filter dropdown."""
    return ["All"] + get_config()["issue_statuses"]