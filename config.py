PROJECT_TYPE = "aviation"  # or "data_center"
BRAND_NAME = "CriticalArc"
BRAND_COLOR = "#39B54A"

ISSUE_STATUSES = ["Open", "In Progress", "Pending Review", "Closed"]
CHECKLIST_VERIFIED = ["Checklist Complete", "Verified", "Verified - Not Included in Sampling"]
CHECKLIST_PIPELINE = [
    ("Script in Development", "script_in_development_date"),
    ("Assigned", "assigned_date"),
    ("In Progress", "in_progress_date"),
    ("Contractor Complete", "contractor_complete_date"),
    ("Verified", "verified_date"),
]