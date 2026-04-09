import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.filters import apply_filters
from utils.cxalloy import load_project_data

# ─── Safe Get ─────────────────────────────────────────────────────────────────
def safe_get(sheets, key):
    val = sheets.get(key) if sheets else None
    return val if val is not None else pd.DataFrame()

# ─── Chart Helpers ────────────────────────────────────────────────────────────
def plotly_bar(df, x, y, title, color=None, color_map=None, orientation='v'):
    fig = px.bar(df, x=x, y=y, title=title, color=color,
                 color_discrete_map=color_map, orientation=orientation,
                 template="plotly_dark")
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Barlow, sans-serif', size=11, color='#8A8F98'),
        title_font=dict(size=12, color='#8A8F98', family='Barlow Condensed'),
        margin=dict(t=40, b=10, l=10, r=10),
        legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(color='#8A8F98')),
        xaxis=dict(gridcolor='#3E4248', tickfont=dict(size=11, color='#8A8F98')),
        yaxis=dict(gridcolor='#3E4248', tickfont=dict(size=11, color='#8A8F98')),
    )
    return fig

def plotly_donut(labels, values, title, colors):
    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.65,
        marker_colors=colors,
        marker=dict(line=dict(color='#2D3035', width=2)),
        textinfo='none',
        hovertemplate='<b>%{label}</b><br>Count: %{value}<br>%{percent}<extra></extra>'
    ))
    fig.update_layout(
        title=dict(text=title, font=dict(size=12, color='#8A8F98', family='Barlow Condensed')),
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Barlow, sans-serif', size=11, color='#8A8F98'),
        showlegend=True,
        legend=dict(
            bgcolor='rgba(0,0,0,0)',
            font=dict(size=11, color='#8A8F98', family='Barlow, sans-serif'),
            orientation='v', x=1.02, y=0.5
        ),
        margin=dict(t=40, b=10, l=10, r=150),
    )
    return fig

def plotly_hbar_pct(df, y_col, pct_col, title):
    fig = go.Figure(go.Bar(
        x=df[pct_col], y=df[y_col], orientation='h',
        marker=dict(
            color=df[pct_col],
            colorscale=[[0, '#E04040'], [0.5, '#F4B942'], [1, '#39B54A']],
            showscale=False
        ),
        text=df[pct_col].apply(lambda x: f"{x}%"),
        textposition='inside',
        textfont=dict(color='#F0F0F0', family='Barlow, sans-serif')
    ))
    fig.update_layout(
        title=dict(text=title, font=dict(size=12, color='#8A8F98', family='Barlow Condensed')),
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Barlow, sans-serif', size=11, color='#8A8F98'),
        margin=dict(t=40, b=10, l=10, r=10),
        xaxis=dict(gridcolor='#3E4248', range=[0, 105], tickfont=dict(color='#8A8F98')),
        yaxis=dict(gridcolor='#3E4248', tickfont=dict(size=10, color='#8A8F98')),
        height=400
    )
    return fig

# ─── KPI Card ─────────────────────────────────────────────────────────────────
def kpi_card(label, value, color_class="kpi-white", sub=""):
    sub_html = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value {color_class}">{value}</div>
        {sub_html}
    </div>
    """, unsafe_allow_html=True)

def section(label):
    st.markdown(f'<div class="section-header">{label}</div>', unsafe_allow_html=True)

def format_assigned(row):
    name    = str(row.get('assigned_name', '')).strip()
    company = str(row.get('assigned_company', '')).strip()
    if name and company and name != company:
        return f"{name} ({company})"
    return company if company else name

# ─── Main Render ──────────────────────────────────────────────────────────────
def render(config: dict, filters: dict, all_sheets: dict = None):
    if all_sheets is None:
        with st.spinner("Loading data..."):
            try:
                all_sheets = load_project_data(config["project_id"])
            except Exception as e:
                st.error(f"Error loading data: {e}")
                return

    issues_raw     = safe_get(all_sheets, 'Issues')
    checklists_raw = safe_get(all_sheets, 'Checklists')
    tests_raw      = safe_get(all_sheets, 'Tests')

    issues     = apply_filters(issues_raw, filters)
    checklists = apply_filters(checklists_raw, filters)
    tests      = apply_filters(tests_raw, filters)

    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Issue Tracking",
        "✅ Checklist (PFC)",
        "🧪 Functional Tests",
        "🔧 Equipment"
    ])

    # ══════════════════════════════════════════════════════════════
    # TAB 1 — ISSUE TRACKING
    # ══════════════════════════════════════════════════════════════
    with tab1:
        if issues.empty:
            st.info("No issue data available.")
        else:
            open_issues  = issues[issues['status'] != 'Closed']
            aging_60     = open_issues[open_issues['aging_category'] == '>60 Days']
            aging_45     = open_issues[open_issues['aging_category'] == '45-60 Days']
            in_progress  = open_issues[open_issues['status'] == 'In Progress']
            high_priority = open_issues[open_issues['priority'].str.contains('High', na=False)]

            section("Key Metrics")
            c1, c2, c3, c4, c5 = st.columns(5)
            with c1:
                kpi_card("Total Open Issues", len(open_issues),
                         "kpi-red" if len(open_issues) > 10 else "kpi-yellow", "non-closed")
            with c2: kpi_card("Aging > 60 Days", len(aging_60), "kpi-red", "flagged red")
            with c3: kpi_card("Aging 45–60 Days", len(aging_45), "kpi-yellow", "warning zone")
            with c4: kpi_card("In Progress", len(in_progress), "kpi-blue", "actively worked")
            with c5: kpi_card("High Priority", len(high_priority), "kpi-red", "open & high")

            section("Issue Breakdown")
            col_l, col_r = st.columns(2)

            with col_l:
                if 'priority' in issues.columns:
                    priority_counts = issues['priority'].value_counts().reset_index()
                    priority_counts.columns = ['Priority', 'Count']
                    colors = {
                        'High (Will Impact Performance)': '#E04040',
                        'Moderate (May Impact Performance)': '#F4B942',
                        "Low (Won't Impact Performance)": '#39B54A'
                    }
                    color_list = [colors.get(p, '#8A8F98') for p in priority_counts['Priority']]
                    st.plotly_chart(plotly_donut(priority_counts['Priority'],
                                                 priority_counts['Count'],
                                                 "All Issues by Priority", color_list),
                                    use_container_width=True)

            with col_r:
                if 'status' in issues.columns:
                    status_counts = issues['status'].value_counts().reset_index()
                    status_counts.columns = ['Status', 'Count']
                    status_colors = {
                        'Open': '#E04040', 'In Progress': '#4A90D9',
                        'Pending Review': '#F4B942', 'Closed': '#39B54A',
                    }
                    st.plotly_chart(plotly_bar(status_counts, 'Status', 'Count',
                                               'All Issues by Status', color='Status',
                                               color_map=status_colors),
                                    use_container_width=True)

            section("Issues by Division")
            if 'discipline' in issues.columns:
                disc_counts = (issues.groupby('discipline')
                               .size().reset_index(name='Count')
                               .sort_values('Count', ascending=True).tail(15))
                fig = plotly_bar(disc_counts, 'Count', 'discipline',
                                 'All Issues per Division', orientation='h')
                fig.update_layout(height=400, yaxis_title="", xaxis_title="Issue Count")
                st.plotly_chart(fig, use_container_width=True)

            section("Issues by Contractor")
            if 'assigned_company' in issues.columns:
                contractor_counts = (issues.groupby('assigned_company')
                                     .size().reset_index(name='Count')
                                     .sort_values('Count', ascending=False).head(15))
                fig = plotly_bar(contractor_counts, 'assigned_company', 'Count',
                                 'All Issues per Contractor', color='Count')
                fig.update_layout(xaxis_tickangle=-35)
                st.plotly_chart(fig, use_container_width=True)

            section("Open Issues Detail")
            open_detail = issues[issues['status'] != 'Closed'].copy()
            if not open_detail.empty:
                open_detail['Aging'] = open_detail['aging_category'].apply(
                    lambda c: '🔴 >60 Days' if c == '>60 Days'
                    else '🟡 45-60 Days' if c == '45-60 Days' else '🟢 Under 45 Days'
                )
                open_detail['Assigned To'] = open_detail.apply(format_assigned, axis=1)
                display_cols = [c for c in ['name', 'Aging', 'days_open', 'priority',
                                            'discipline', 'Assigned To', 'status',
                                            'description'] if c in open_detail.columns]
                st.dataframe(open_detail[display_cols].rename(columns={
                    'name': 'Issue #', 'days_open': 'Days Open', 'priority': 'Priority',
                    'discipline': 'Division', 'status': 'Status', 'description': 'Description'
                }), use_container_width=True, hide_index=True)
            else:
                st.success("✅ No open issues with current filters.")

            with st.expander("📄 View All Issues"):
                all_issues_display = issues.copy()
                all_issues_display['Assigned To'] = all_issues_display.apply(
                    format_assigned, axis=1)
                for dc in ['date_created', 'in_progress_date', 'date_closed']:
                    if dc in all_issues_display.columns:
                        all_issues_display[dc] = pd.to_datetime(
                            all_issues_display[dc], errors='coerce'
                        ).dt.strftime('%m/%d/%Y').fillna('')
                view_cols = [c for c in ['name', 'priority', 'status', 'discipline',
                                         'Assigned To', 'date_created', 'in_progress_date',
                                         'date_closed', 'days_open',
                                         'description'] if c in all_issues_display.columns]
                st.dataframe(
                    all_issues_display[view_cols].rename(columns={
                        'name': 'Issue #', 'priority': 'Priority', 'status': 'Status',
                        'discipline': 'Division', 'days_open': 'Days Open',
                        'date_created': 'Date Created', 'in_progress_date': 'In Progress Date',
                        'date_closed': 'Date Closed', 'description': 'Description'
                    }), use_container_width=True, hide_index=True)

    # ══════════════════════════════════════════════════════════════
    # TAB 2 — CHECKLIST (PFC)
    # ══════════════════════════════════════════════════════════════
    with tab2:
        if checklists.empty:
            st.info("No checklist data available.")
        else:
            total_cl = len(checklists)
            verified_statuses = ['Checklist Complete', 'Verified',
                                  'Verified - Not Included in Sampling']
            completed    = checklists[checklists['status'].isin(verified_statuses)].shape[0]
            in_prog_cl   = checklists[checklists['status'] == 'In Progress'].shape[0]
            assigned_cl  = checklists[checklists['status'] == 'Assigned'].shape[0]
            completion_pct = f"{completed/total_cl*100:.1f}%" if total_cl > 0 else "0%"

            section("Checklist Summary")
            c1, c2, c3, c4 = st.columns(4)
            with c1: kpi_card("Total Checklists", total_cl, "kpi-white")
            with c2: kpi_card("Completed / Verified", completed, "kpi-green", completion_pct)
            with c3: kpi_card("In Progress", in_prog_cl, "kpi-blue")
            with c4: kpi_card("Assigned (Not Started)", assigned_cl, "kpi-yellow")

            col_l, col_r = st.columns(2)
            with col_r:
                section("Checklist Pipeline")
                stage_cols = [
                    ('Script in Development', 'script_in_development_date'),
                    ('Assigned', 'assigned_date'),
                    ('In Progress', 'in_progress_date'),
                    ('Contractor Complete', 'contractor_complete_date'),
                    ('Verified', 'verified_date'),
                ]
                pipeline_data = []
                total = len(checklists)
                for label, col in stage_cols:
                    if col in checklists.columns:
                        reached = checklists[col].notna().sum()
                    else:
                        reached = 0
                    pipeline_data.append({'Stage': label, 'Reached': reached})

                pipeline_df = pd.DataFrame(pipeline_data)
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=pipeline_df['Reached'], y=pipeline_df['Stage'],
                    orientation='h',
                    marker=dict(
                        color=pipeline_df['Reached'],
                        colorscale=[[0, '#3E4248'], [0.5, '#4A90D9'], [1, '#39B54A']],
                        showscale=False
                    ),
                    text=pipeline_df.apply(
                        lambda r: f"{int(r['Reached'])} / {total}  ({r['Reached']/total*100:.1f}%)"
                        if total > 0 else '0', axis=1),
                    textposition='inside',
                    textfont=dict(color='#F0F0F0', family='Barlow, sans-serif', size=12),
                ))
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(family='Barlow, sans-serif', size=11, color='#8A8F98'),
                    margin=dict(t=10, b=10, l=10, r=10),
                    xaxis=dict(gridcolor='#3E4248', tickfont=dict(color='#8A8F98'),
                               range=[0, total * 1.05]),
                    yaxis=dict(tickfont=dict(size=11, color='#8A8F98'),
                               categoryorder='array',
                               categoryarray=list(reversed(pipeline_df['Stage']))),
                    height=280
                )
                st.plotly_chart(fig, use_container_width=True)

            with col_l:
                status_counts = checklists['status'].value_counts().reset_index()
                status_counts.columns = ['Status', 'Count']
                status_colors = {
                    'Verified': '#39B54A',
                    'Checklist Complete': '#5DD96A',
                    'Verified - Not Included in Sampling': '#8AE895',
                    'Contractor Complete': '#2E8B57',
                    'In Progress': '#4A90D9',
                    'Assigned': '#F4B942',
                    'Script in Development': '#6E7FD4',
                    'Script In Development': '#6E7FD4',
                    'Removed from Scope': '#3E4248',
                }
                color_list = [status_colors.get(s, '#8A8F98') for s in status_counts['Status']]
                st.plotly_chart(plotly_donut(status_counts['Status'],
                                             status_counts['Count'],
                                             'Checklists by Current Status',
                                             color_list),
                                use_container_width=True)

            section("Completion by Discipline")
            if 'discipline' in checklists.columns:
                disc_comp = checklists.groupby('discipline').agg(
                    Total=('status', 'count'),
                    Completed=('status', lambda x: x.isin(verified_statuses).sum())
                ).reset_index()
                disc_comp['Remaining'] = disc_comp['Total'] - disc_comp['Completed']
                disc_comp['Completion %'] = (
                    disc_comp['Completed'] / disc_comp['Total'] * 100).round(1)
                disc_comp = disc_comp.sort_values('Total', ascending=True)

                fig = go.Figure()
                fig.add_trace(go.Bar(
                    y=disc_comp['discipline'], x=disc_comp['Completed'],
                    name='Completed', orientation='h',
                    marker_color='#39B54A',
                    text=disc_comp.apply(
                        lambda r: f"{int(r['Completed'])} ({r['Completion %']}%)"
                        if r['Completed'] > 0 else '', axis=1),
                    textposition='inside',
                    textfont=dict(color='#F0F0F0', family='Barlow, sans-serif', size=11)
                ))
                fig.add_trace(go.Bar(
                    y=disc_comp['discipline'], x=disc_comp['Remaining'],
                    name='Remaining', orientation='h',
                    marker_color='#3E4248',
                    text=disc_comp['Total'].apply(lambda t: str(int(t))),
                    textposition='outside',
                    textfont=dict(color='#8A8F98', family='Barlow, sans-serif', size=11)
                ))
                fig.update_layout(
                    barmode='stack',
                    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(family='Barlow, sans-serif', size=11, color='#8A8F98'),
                    margin=dict(t=10, b=10, l=10, r=40),
                    legend=dict(bgcolor='rgba(0,0,0,0)',
                                font=dict(color='#8A8F98'), orientation='h',
                                x=0.5, xanchor='center', y=-0.08),
                    xaxis=dict(gridcolor='#3E4248', tickfont=dict(color='#8A8F98')),
                    yaxis=dict(tickfont=dict(size=10, color='#8A8F98')),
                    height=max(250, len(disc_comp) * 45)
                )
                st.plotly_chart(fig, use_container_width=True)

            section("Completion by Contractor")
            if 'assigned_company' in checklists.columns:
                unassigned_vals = ['not assigned yet', 'not assigned', '', 'nan', 'none']

                def classify_assignment(row):
                    name = str(row.get('assigned_company', '')).strip().lower()
                    atype = str(row.get('assigned_type', '')).strip().lower()
                    if name in unassigned_vals:
                        return 'unassigned'
                    if atype == 'role':
                        return 'role'
                    return 'contractor'

                checklists['_assign_type'] = checklists.apply(classify_assignment, axis=1)

                # ── Contractor table (real companies only) ──
                contractor_cl = checklists[checklists['_assign_type'] == 'contractor']
                if not contractor_cl.empty:
                    contractor_summary = contractor_cl.groupby('assigned_company').agg(
                        Total=('status', 'count'),
                        Completed=('status', lambda x: x.isin(verified_statuses).sum())
                    ).reset_index()
                    contractor_summary['Completion %'] = (
                        contractor_summary['Completed'] / contractor_summary['Total'] * 100
                    ).round(1)
                    st.dataframe(
                        contractor_summary.rename(columns={'assigned_company': 'Contractor'}),
                        use_container_width=True, hide_index=True)

                # ── Role / Unassigned breakdown ──
                pending = checklists[checklists['_assign_type'].isin(['role', 'unassigned'])]
                if not pending.empty:
                    section("Pending Assignment")
                    pending_summary = pending.groupby('assigned_company').agg(
                        Count=('status', 'count')
                    ).reset_index().sort_values('Count', ascending=False)
                    pending_summary['assigned_company'] = pending_summary['assigned_company'].apply(
                        lambda x: '⚠️ No Contractor Assigned'
                        if str(x).strip().lower() in unassigned_vals else x
                    )
                    st.dataframe(
                        pending_summary.rename(columns={'assigned_company': 'Role / Status'}),
                        use_container_width=True, hide_index=True)
            # ... rest stays the same

    # ══════════════════════════════════════════════════════════════
    # TAB 3 — FUNCTIONAL TESTS
    # ══════════════════════════════════════════════════════════════
    with tab3:
        if tests.empty:
            st.info("No test data available.")
        else:
            total_tests   = len(tests)
            passed        = tests[tests['status'] == 'Passed'].shape[0]
            in_prog_tests = tests[tests['status'] == 'In Progress'].shape[0]
            assigned_tests = tests[tests['status'] == 'Assigned'].shape[0]
            deferred      = tests[tests['status'] == 'Deferred to 1B'].shape[0]
            pass_rate     = f"{passed/total_tests*100:.1f}%" if total_tests > 0 else "0%"

            section("Test Summary")
            c1, c2, c3, c4, c5 = st.columns(5)
            with c1: kpi_card("Total Tests", total_tests, "kpi-white")
            with c2:
                pct   = passed/total_tests*100 if total_tests > 0 else 0
                color = "kpi-green" if pct >= 90 else "kpi-yellow" if pct >= 70 else "kpi-red"
                kpi_card("Passed", passed, color, pass_rate)
            with c3: kpi_card("In Progress", in_prog_tests, "kpi-blue")
            with c4: kpi_card("Assigned", assigned_tests, "kpi-yellow")
            with c5: kpi_card("Deferred", deferred, "kpi-white")

            col_l, col_r = st.columns(2)
            with col_l:
                status_counts = tests['status'].value_counts().reset_index()
                status_counts.columns = ['Status', 'Count']
                status_colors = {
                    'Passed': '#39B54A',
                    'Partially Passed (Test to be Repeated)': '#F4B942',
                    'In Progress': '#4A90D9',
                    'Assigned': '#8A8F98',
                    'Script In Development': '#6E7FD4',
                    'Deferred to 1B': '#6E7FD4',
                    'Voided': '#3E4248'
                }
                color_list = [status_colors.get(s, '#8A8F98') for s in status_counts['Status']]
                st.plotly_chart(plotly_donut(status_counts['Status'], status_counts['Count'],
                                             "Tests by Status", color_list),
                                use_container_width=True)

            with col_r:
                if 'attempt_count' in tests.columns:
                    tests['attempt_count'] = pd.to_numeric(tests['attempt_count'], errors='coerce').fillna(1).astype(int)
                    attempt_col = 'asset_type' if 'asset_type' in tests.columns else 'discipline'
                    attempt_summary = tests.groupby(attempt_col).agg(
                        Total_Tests=('status', 'count'),
                        Avg_Attempts=('attempt_count', 'mean'),
                        Max_Attempts=('attempt_count', 'max'),
                        Retests=('attempt_count', lambda x: (x > 1).sum())
                    ).reset_index()
                    attempt_summary['Avg_Attempts'] = attempt_summary['Avg_Attempts'].round(2)
                    attempt_summary = attempt_summary.sort_values('Avg_Attempts', ascending=True)

                    fig = go.Figure(go.Bar(
                        y=attempt_summary[attempt_col],
                        x=attempt_summary['Avg_Attempts'],
                        orientation='h',
                        marker=dict(
                            color=attempt_summary['Avg_Attempts'],
                            colorscale=[[0, '#39B54A'], [0.5, '#F4B942'], [1, '#E04040']],
                            showscale=False
                        ),
                        text=attempt_summary.apply(
                            lambda r: f"Avg: {r['Avg_Attempts']}  |  Retests: {int(r['Retests'])}",
                            axis=1),
                        textposition='inside',
                        textfont=dict(color='#F0F0F0', family='Barlow, sans-serif', size=11)
                    ))
                    fig.update_layout(
                        title=dict(text='Avg Attempts by Equipment Type',
                                   font=dict(size=12, color='#8A8F98', family='Barlow Condensed')),
                        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(family='Barlow, sans-serif', size=11, color='#8A8F98'),
                        margin=dict(t=40, b=10, l=10, r=10),
                        xaxis=dict(gridcolor='#3E4248', tickfont=dict(color='#8A8F98')),
                        yaxis=dict(tickfont=dict(size=10, color='#8A8F98')),
                        height=300
                    )
                    st.plotly_chart(fig, use_container_width=True)

            # ── Completion by Discipline (stacked bar) ──
            section("Tests by Division")
            if 'discipline' in tests.columns:
                tests['discipline'] = tests['discipline'].fillna('Unassigned Division')
                disc_tests = tests.groupby('discipline').agg(
                    # ... rest stays the same
                    Total=('status', 'count'),
                    Passed=('status', lambda x: (x == 'Passed').sum())
                ).reset_index()
                disc_tests['Remaining'] = disc_tests['Total'] - disc_tests['Passed']
                disc_tests['Pass %'] = (
                    disc_tests['Passed'] / disc_tests['Total'] * 100).round(1)
                disc_tests = disc_tests.sort_values('Total', ascending=True)

                fig = go.Figure()
                fig.add_trace(go.Bar(
                    y=disc_tests['discipline'], x=disc_tests['Passed'],
                    name='Passed', orientation='h',
                    marker_color='#39B54A',
                    text=disc_tests.apply(
                        lambda r: f"{int(r['Passed'])} ({r['Pass %']}%)"
                        if r['Passed'] > 0 else '', axis=1),
                    textposition='inside',
                    textfont=dict(color='#F0F0F0', family='Barlow, sans-serif', size=11)
                ))
                fig.add_trace(go.Bar(
                    y=disc_tests['discipline'], x=disc_tests['Remaining'],
                    name='Remaining', orientation='h',
                    marker_color='#3E4248',
                    text=disc_tests['Total'].apply(lambda t: str(int(t))),
                    textposition='outside',
                    textfont=dict(color='#8A8F98', family='Barlow, sans-serif', size=11)
                ))
                fig.update_layout(
                    barmode='stack',
                    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(family='Barlow, sans-serif', size=11, color='#8A8F98'),
                    margin=dict(t=10, b=10, l=10, r=40),
                    legend=dict(bgcolor='rgba(0,0,0,0)',
                                font=dict(color='#8A8F98'), orientation='h',
                                x=0.5, xanchor='center', y=-0.08),
                    xaxis=dict(gridcolor='#3E4248', tickfont=dict(color='#8A8F98')),
                    yaxis=dict(tickfont=dict(size=10, color='#8A8F98')),
                    height=max(250, len(disc_tests) * 45)
                )
                st.plotly_chart(fig, use_container_width=True)
                 

            if 'asset_type' in tests.columns:
                section("Pass Rate by Equipment Type")
                asset_tests = tests.groupby('asset_type').agg(
                    Total=('status', 'count'),
                    Passed=('status', lambda x: (x == 'Passed').sum())
                ).reset_index()
                asset_tests['Pass Rate %'] = (
                    asset_tests['Passed'] / asset_tests['Total'] * 100).round(1)
                st.dataframe(asset_tests.rename(columns={'asset_type': 'Asset Type'}),
                             use_container_width=True, hide_index=True)

            with st.expander("📄 View All Tests"):
                view_cols = [c for c in ['number', 'name', 'status', 'discipline',
                                         'assigned_name', 'asset_name', 'asset_type',
                                         'attempt_count'] if c in tests.columns]
                st.dataframe(tests[view_cols], use_container_width=True, hide_index=True)

    # ══════════════════════════════════════════════════════════════
    # TAB 4 — EQUIPMENT
    # ══════════════════════════════════════════════════════════════
    with tab4:
        equipment = safe_get(all_sheets, 'Equipment')
        if equipment.empty:
            st.info("No equipment data available.")
        else:
            # ── Merge checklist/test/issue counts onto equipment ──
            eq = equipment.copy()
            eq['equipment_id'] = eq['equipment_id'].astype(str)

            verified_eq = ['Checklist Complete', 'Verified', 'Verified - Not Included in Sampling']

            if not checklists_raw.empty and 'asset_key' in checklists_raw.columns:
                cl_agg = checklists_raw.groupby(checklists_raw['asset_key'].astype(str)).agg(
                    Checklists=('status', 'count'),
                    CL_Complete=('status', lambda x: x.isin(verified_eq).sum())
                ).reset_index()
                eq = eq.merge(cl_agg, left_on='equipment_id', right_on='asset_key', how='left').drop(columns='asset_key', errors='ignore')
            else:
                eq['Checklists'] = 0; eq['CL_Complete'] = 0

            if not tests_raw.empty and 'asset_key' in tests_raw.columns:
                ts_agg = tests_raw.groupby(tests_raw['asset_key'].astype(str)).agg(
                    Tests=('status', 'count'),
                    Tests_Passed=('status', lambda x: (x == 'Passed').sum())
                ).reset_index()
                eq = eq.merge(ts_agg, left_on='equipment_id', right_on='asset_key', how='left').drop(columns='asset_key', errors='ignore')
            else:
                eq['Tests'] = 0; eq['Tests_Passed'] = 0

            if not issues_raw.empty and 'asset_key' in issues_raw.columns:
                iss_agg = issues_raw.groupby(issues_raw['asset_key'].astype(str)).agg(
                    Issues=('status', 'count'),
                    Open_Issues=('status', lambda x: (x != 'Closed').sum())
                ).reset_index()
                eq = eq.merge(iss_agg, left_on='equipment_id', right_on='asset_key', how='left').drop(columns='asset_key', errors='ignore')
            else:
                eq['Issues'] = 0; eq['Open_Issues'] = 0

            for c in ['Checklists', 'CL_Complete', 'Tests', 'Tests_Passed', 'Issues', 'Open_Issues']:
                eq[c] = eq[c].fillna(0).astype(int)

            # ── Location filters ──
            section("Equipment Overview")
            f1, f2 = st.columns(2)
            with f1:
                floors = ['All'] + sorted(eq['floor'].dropna().unique().tolist())
                sel_floor = st.selectbox("Floor", floors, key="eq_floor")
            with f2:
                spaces = ['All'] + sorted(eq['space'].dropna().unique().tolist())
                sel_space = st.selectbox("Space", spaces, key="eq_space")

            if sel_floor != 'All':
                eq = eq[eq['floor'] == sel_floor]
            if sel_space != 'All':
                eq = eq[eq['space'] == sel_space]

            # ── KPIs ──
            c1, c2, c3, c4, c5 = st.columns(5)
            with c1: kpi_card("Total Equipment", len(eq), "kpi-white")
            with c2: kpi_card("Checklists", eq['Checklists'].sum(), "kpi-blue",
                              f"{eq['CL_Complete'].sum()} complete")
            with c3: kpi_card("Tests", eq['Tests'].sum(), "kpi-blue",
                              f"{eq['Tests_Passed'].sum()} passed")
            with c4: kpi_card("Open Issues", eq['Open_Issues'].sum(),
                              "kpi-red" if eq['Open_Issues'].sum() > 0 else "kpi-green")
            with c5:
                eq_with_cl = (eq['Checklists'] > 0).sum()
                kpi_card("Has Checklists", f"{eq_with_cl}/{len(eq)}", "kpi-yellow",
                         f"{eq_with_cl/len(eq)*100:.0f}% coverage" if len(eq) > 0 else "")

            # ── Charts ──
            col_l, col_r = st.columns(2)
            with col_l:
                if 'type' in eq.columns:
                    type_summary = eq.groupby('type').agg(
                        Count=('equipment_id', 'count'),
                        Checklists=('Checklists', 'sum'),
                        Tests=('Tests', 'sum')
                    ).reset_index().sort_values('Count', ascending=True)

                    fig = go.Figure()
                    fig.add_trace(go.Bar(
                        y=type_summary['type'], x=type_summary['Count'],
                        name='Equipment', orientation='h', marker_color='#3E4248'
                    ))
                    fig.add_trace(go.Bar(
                        y=type_summary['type'], x=type_summary['Checklists'],
                        name='Checklists', orientation='h', marker_color='#4A90D9'
                    ))
                    fig.add_trace(go.Bar(
                        y=type_summary['type'], x=type_summary['Tests'],
                        name='Tests', orientation='h', marker_color='#39B54A'
                    ))
                    fig.update_layout(
                        barmode='group',
                        title=dict(text='Equipment / Checklists / Tests by Type',
                                   font=dict(size=12, color='#8A8F98', family='Barlow Condensed')),
                        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(family='Barlow, sans-serif', size=11, color='#8A8F98'),
                        margin=dict(t=40, b=10, l=10, r=10),
                        legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(color='#8A8F98'),
                                    orientation='h', x=0.5, xanchor='center', y=-0.08),
                        xaxis=dict(gridcolor='#3E4248', tickfont=dict(color='#8A8F98')),
                        yaxis=dict(tickfont=dict(size=10, color='#8A8F98')),
                        height=max(300, len(type_summary) * 40)
                    )
                    st.plotly_chart(fig, use_container_width=True)

            with col_r:
                if 'discipline' in eq.columns:
                    disc_summary = eq.groupby('discipline').agg(
                        Equipment=('equipment_id', 'count'),
                        Checklists=('Checklists', 'sum'),
                        CL_Complete=('CL_Complete', 'sum')
                    ).reset_index()
                    disc_summary['CL Completion %'] = (
                        disc_summary['CL_Complete'] / disc_summary['Checklists'] * 100
                    ).fillna(0).round(1)
                    disc_summary = disc_summary.sort_values('Equipment', ascending=True)
                    st.plotly_chart(plotly_hbar_pct(disc_summary, 'discipline', 'CL Completion %',
                                                    'Checklist Completion % by Discipline'),
                                    use_container_width=True)

            # ── Floor breakdown ──
            if 'floor' in eq.columns:
                section("By Floor")
                floor_summary = eq.groupby('floor').agg(
                    Equipment=('equipment_id', 'count'),
                    Checklists=('Checklists', 'sum'),
                    CL_Complete=('CL_Complete', 'sum'),
                    Tests=('Tests', 'sum'),
                    Tests_Passed=('Tests_Passed', 'sum'),
                    Open_Issues=('Open_Issues', 'sum')
                ).reset_index()
                floor_summary['CL %'] = (
                    floor_summary['CL_Complete'] / floor_summary['Checklists'] * 100
                ).fillna(0).round(1)
                st.dataframe(floor_summary.rename(columns={
                    'floor': 'Floor', 'CL_Complete': 'CL Done',
                    'Tests_Passed': 'Tests Passed', 'Open_Issues': 'Open Issues'
                }), use_container_width=True, hide_index=True)

            # ── Full equipment table ──
            with st.expander("📄 View All Equipment"):
                display_cols = [c for c in ['name', 'type', 'discipline', 'floor', 'space',
                                             'Checklists', 'CL_Complete', 'Tests',
                                             'Tests_Passed', 'Issues', 'Open_Issues']
                                if c in eq.columns]
                st.dataframe(eq[display_cols].rename(columns={
                    'name': 'Asset', 'type': 'Type', 'discipline': 'Discipline',
                    'floor': 'Floor', 'space': 'Space', 'CL_Complete': 'CL Done',
                    'Tests_Passed': 'Tests Passed', 'Open_Issues': 'Open Issues'
                }), use_container_width=True, hide_index=True)