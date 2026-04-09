import streamlit as st
import os
import pandas as pd
import importlib.util
from datetime import datetime

from utils.cxalloy import load_all_projects, load_project_data

# ─── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CriticalArc Dashboard",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Global CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Barlow:wght@400;500;600&family=Barlow+Condensed:wght@500;600;700&family=DM+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'Barlow', sans-serif;
        color: #F0F0F0;
    }
    .main { background-color: #23262B; }

    section[data-testid="stSidebar"] {
        background-color: #2D3035;
        border-right: 1px solid #3E4248;
    }
    section[data-testid="stSidebar"] * { color: #C8CDD4 !important; }
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] .element-container p,
    section[data-testid="stSidebar"] .stMarkdown p {
        font-size: 11px !important;
        letter-spacing: 1px !important;
    }
    section[data-testid="stSidebar"] .stSelectbox div {
        font-size: 13px !important;
    }

    .kpi-card {
        background: #2D3035;
        border: 1px solid #3E4248;
        border-radius: 10px;
        padding: 20px 24px;
        text-align: center;
        transition: border-color 0.2s;
    }
    .kpi-card:hover { border-color: #8A8F98; }
    .kpi-label {
        font-family: 'Barlow Condensed', sans-serif;
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        color: #8A8F98;
        margin-bottom: 8px;
    }
    .kpi-value {
        font-family: 'DM Mono', monospace;
        font-size: 32px;
        font-weight: 500;
        line-height: 1;
        margin-bottom: 4px;
    }
    .kpi-sub { font-size: 12px; color: #8A8F98; }
    .kpi-red    { color: #E04040; }
    .kpi-yellow { color: #F4B942; }
    .kpi-green  { color: #39B54A; }
    .kpi-blue   { color: #4A90D9; }
    .kpi-white  { color: #F0F0F0; }

    .section-header {
        font-family: 'Barlow Condensed', sans-serif;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 2px;
        text-transform: uppercase;
        color: #39B54A;
        margin: 24px 0 12px 0;
        padding-bottom: 8px;
        border-bottom: 1px solid #3E4248;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: #2D3035;
        padding: 4px;
        border-radius: 10px;
        border: 1px solid #3E4248;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 6px;
        color: #8A8F98;
        font-family: 'Barlow Condensed', sans-serif;
        font-weight: 600;
        font-size: 13px;
        letter-spacing: 0.5px;
        padding: 8px 16px;
    }
    .stTabs [aria-selected="true"] {
        background: #34383E !important;
        color: #39B54A !important;
    }

    .stButton > button {
        font-family: 'Barlow Condensed', sans-serif;
        font-weight: 700;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        background: transparent;
        color: #F0F0F0;
        border: 1px solid #3E4248;
        border-radius: 6px;
        transition: background 0.15s, border-color 0.15s;
    }
    .stButton > button:hover {
        background: #34383E;
        border-color: #8A8F98;
        color: #F0F0F0;
    }

    .ca-brand {
        font-family: 'Barlow Condensed', sans-serif;
        font-size: 20px;
        font-weight: 700;
        letter-spacing: 1px;
        text-transform: uppercase;
        color: #F0F0F0;
        border-bottom: 2px solid #39B54A;
        padding-bottom: 12px;
        margin-bottom: 20px;
    }
    .ca-brand-sub {
        font-size: 11px;
        color: #8A8F98;
        letter-spacing: 1px;
        margin-top: 2px;
    }
</style>
""", unsafe_allow_html=True)

# ─── Utils ────────────────────────────────────────────────────────────────────
def safe_get(sheets, key):
    val = sheets.get(key) if sheets else None
    return val if val is not None else pd.DataFrame()

# ─── Load Projects ────────────────────────────────────────────────────────────
projects_df = load_all_projects()

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="ca-brand">
        CriticalArc
        <div class="ca-brand-sub">Project Dashboard Platform</div>
    </div>
    """, unsafe_allow_html=True)

    if projects_df.empty:
        st.error("No projects found.")
        st.stop()

    project_names = dict(zip(projects_df['project_id'], projects_df['name']))

    selected_project_id = st.selectbox(
        "Select Project",
        options=list(project_names.keys()),
        format_func=lambda k: project_names[k]
    )

    st.markdown("---")
    st.markdown("**Filters**")

    try:
        with st.spinner("Loading data..."):
            all_sheets     = load_project_data(selected_project_id)
            issues_raw     = safe_get(all_sheets, 'Issues')
            checklists_raw = safe_get(all_sheets, 'Checklists')
            tests_raw      = safe_get(all_sheets, 'Tests')
            equipment_raw  = safe_get(all_sheets, 'Equipment')
            companies_raw  = safe_get(all_sheets, 'Companies')
    except Exception as e:
        st.warning(f"Could not load data: {e}")
        issues_raw     = pd.DataFrame()
        checklists_raw = pd.DataFrame()
        tests_raw      = pd.DataFrame()
        equipment_raw  = pd.DataFrame()
        companies_raw  = pd.DataFrame()
        all_sheets     = {}

    # Disciplines from equipment
    disciplines = ["All"]
    if not equipment_raw.empty and "discipline" in equipment_raw.columns:
        disciplines += sorted([
            d for d in equipment_raw["discipline"].dropna().unique()
            if d and str(d) not in ['0', 'nan', 'None', '']
        ])

    # Contractors from companies tab
    contractors = ["All"]
    if not companies_raw.empty and "name" in companies_raw.columns:
        contractors += sorted([
            c for c in companies_raw["name"].dropna().unique()
            if c and str(c) not in ['0', 'nan', 'None', '']
        ])

    filters = {
        "discipline": st.selectbox("Division / Discipline", disciplines, key="filter_discipline"),
        "contractor": st.selectbox("Contractor / Assigned To", contractors, key="filter_contractor"),
        "status":     st.selectbox("Status", ["All", "Open", "In Progress", "Pending Review", "Closed"], key="filter_status"),
    }

    st.markdown("---")
    st.markdown(
        f"<div style='font-size:11px; color:#8A8F98;'>Refreshed: {datetime.now().strftime('%b %d %H:%M')}</div>",
        unsafe_allow_html=True
    )
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()

# ─── Header ───────────────────────────────────────────────────────────────────
project_name = project_names.get(selected_project_id, "Project Dashboard")

st.html(f"""
<div style="padding: 8px 0 0 0;">
    <div style="
        font-family: 'Barlow Condensed', sans-serif;
        font-size: 42px;
        font-weight: 700;
        letter-spacing: 1px;
        color: #2D3035;
        text-transform: uppercase;
        line-height: 1.1;
    ">{project_name}</div>
    <div style="
        font-family: 'Barlow', sans-serif;
        font-size: 14px;
        color: #8A8F98;
        margin-top: 4px;
        letter-spacing: 0.5px;
    ">Commissioning Progress Dashboard</div>
    <div style="
        font-family: 'Barlow', sans-serif;
        font-size: 12px;
        color: #5A5F68;
        margin-top: 6px;
        letter-spacing: 0.5px;
    ">Data last refreshed: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</div>
    <hr style="border: none; border-top: 1px solid #3E4248; margin-top: 16px;">
</div>
""")

# ─── Render Layout ────────────────────────────────────────────────────────────
layout_path = os.path.join(os.path.dirname(__file__), "layout.py")
spec = importlib.util.spec_from_file_location("layout", layout_path)
layout_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(layout_mod)
layout_mod.render(
    {"project_id": selected_project_id, "project_name": project_names[selected_project_id]},
    filters,
    all_sheets
)