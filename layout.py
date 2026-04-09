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
        "✅ Checklists",
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

                    # Sort so highest severity is first (gets red)
                    priority_counts['_sort'] = priority_counts['Priority'].str.lower().map(
                        lambda p: 0 if any(x in p for x in ['critical', 'p0', 'high']) else
                                  1 if any(x in p for x in ['moderate', 'p1', 'medium']) else
                                  2 if any(x in p for x in ['low', 'p2', 'minor']) else 3
                    )
                    priority_counts = priority_counts.sort_values('_sort').drop(columns='_sort')

                    priority_scale = ['#E04040', '#F4B942', '#39B54A', '#4A90D9', '#8A8F98']
                    color_list = [priority_scale[i % len(priority_scale)]
                                  for i in range(len(priority_counts))]
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
            from config import checklist_complete_statuses
            complete_statuses = checklist_complete_statuses()

            # Derive active levels
            levels_ordered = ['L2', 'L3', 'L4', 'FAT']
            active_levels = [lv for lv in levels_ordered if lv in checklists['level'].values]

            # Dynamic color palettes

            DISCIPLINE_PALETTE = px.colors.qualitative.Set2
            disc_names = sorted(checklists['discipline'].dropna().unique())
            disc_colors = {name: DISCIPLINE_PALETTE[i % len(DISCIPLINE_PALETTE)]
                           for i, name in enumerate(disc_names)}

            LEVEL_PALETTE = ['#7F77DD', '#1D9E75', '#5DCAA5', '#85B7EB']
            level_colors = {lv: LEVEL_PALETTE[i % len(LEVEL_PALETTE)]
                            for i, lv in enumerate(active_levels)}


            section("Checklist Status by Level")

            dc_status_colors = {
                'Not Started':  '#8A8F98',
                'In Progress':  '#F5A623',
                'GC to Verify': '#4A90D9',
                'Finished':     '#39B54A',
            }

            donut_cols = st.columns(len(active_levels))

            donut_cols = st.columns(len(active_levels))
            for i, lv in enumerate(active_levels):
                with donut_cols[i]:
                    lv_df = checklists[checklists['level'] == lv]
                    status_cts = lv_df['status'].value_counts().reset_index()
                    status_cts.columns = ['Status', 'Count']
                    total = len(lv_df)

                    colors = [dc_status_colors.get(s, '#3E4248') for s in status_cts['Status']]

                    fig_donut = go.Figure(go.Pie(
                        labels=status_cts['Status'],
                        values=status_cts['Count'],
                        hole=0.65,
                        marker=dict(colors=colors),
                        textinfo='percent',
                        textfont=dict(size=11, color='#3E4248', family='Barlow, sans-serif'),
                        hovertemplate='%{label}: %{value}<extra></extra>',
                    ))
                    fig_donut.update_layout(
                        title=dict(
                            text=f"{lv}",
                            font=dict(size=16, color=level_colors.get(lv, '#F0F0F0'),
                                      family='Barlow Condensed, sans-serif'),
                            x=0.5, xanchor='center'
                        ),
                        annotations=[dict(
                            text=f"<b>{total:,}</b>",
                            x=0.5, y=0.5, font=dict(size=20, color='#F0F0F0',
                                                      family='Barlow Condensed, sans-serif'),
                            showarrow=False
                        )],
                        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(family='Barlow, sans-serif', color='#3E4248'),
                        margin=dict(t=40, b=10, l=10, r=10),
                        showlegend=True,
                        legend=dict(
                            font=dict(size=10, color='#3E4248'),
                            orientation='h', yanchor='top', y=-0.05,
                            xanchor='center', x=0.5
                        ),
                        height=280,
                    )
                    st.plotly_chart(fig_donut, use_container_width=True)

            # ── Completion by Discipline ─────────────────────────────────
            section("Completion by Discipline")
            if 'discipline' in checklists.columns:
                disc_comp = checklists.groupby('discipline').agg(
                    Total=('status', 'count'),
                    Completed=('status', lambda x: x.isin(complete_statuses).sum())
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


            # ── Checklists by Level & Discipline ─────────────────────────
            section("Checklists by Level & Discipline")

            level_disc = checklists.groupby(['level', 'discipline']).size().reset_index(name='Count')
            level_disc = level_disc[level_disc['level'].isin(active_levels)]

            disc_colors = {
                'Mechanical':                          '#E74C3C',
                'Electrical':                          '#F5A623',
                'Electrical Power Monitoring System':   '#4A90D9',
                'Fire Protection':                     '#39B54A',
            }

            fig_disc = go.Figure()
            for disc in level_disc['discipline'].unique():
                disc_df = level_disc[level_disc['discipline'] == disc]
                fig_disc.add_trace(go.Bar(
                    y=disc_df['level'], x=disc_df['Count'],
                    orientation='h', name=disc,
                    marker=dict(color=disc_colors.get(disc, '#8A8F98')),
                    text=disc_df['Count'], textposition='inside',
                    textfont=dict(color="#2B2828", family='Barlow, sans-serif', size=11),
                ))

            fig_disc.update_layout(
                barmode='stack',
                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family='Barlow, sans-serif', size=11, color='#8A8F98'),
                margin=dict(t=10, b=10, l=10, r=30),
                xaxis=dict(gridcolor='#3E4248', tickfont=dict(color='#3E4248')),
                yaxis=dict(
                    tickfont=dict(size=13, color="#2B2828"),
                    categoryorder='array',
                    categoryarray=list(reversed(active_levels))
                ),
                legend=dict(
                    orientation='h', yanchor='bottom', y=1.02,
                    xanchor='left', x=0,
                    font=dict(color='#8A8F98', size=11)
                ),
                height=50 + len(active_levels) * 60,
            )
            st.plotly_chart(fig_disc, use_container_width=True)


            # ── Open Checklists by Company & Level ───────────────────────
            section("Open Checklists by Company & Level")

            open_mask = ~checklists['status'].isin(complete_statuses)
            open_cl = checklists[open_mask & checklists['level'].isin(active_levels)]

            if 'assigned_company' in open_cl.columns and not open_cl.empty:
                co_level = open_cl.groupby(['assigned_company', 'level']).size().reset_index(name='Count')
                top_cos = (co_level.groupby('assigned_company')['Count'].sum()
                           .nlargest(10).index.tolist())
                co_level = co_level[co_level['assigned_company'].isin(top_cos)]

                level_colors = {
                    'L2': '#7F77DD',
                    'L3': '#1D9E75',
                    'L4': '#5DCAA5',
                    'FAT': '#85B7EB'
                }

                fig_co = go.Figure()
                for lv in active_levels:
                    lv_data = co_level[co_level['level'] == lv]
                    fig_co.add_trace(go.Bar(
                        x=lv_data['assigned_company'], y=lv_data['Count'],
                        name=lv,
                        marker=dict(color=level_colors.get(lv, '#8A8F98')),
                        text=lv_data['Count'], textposition='outside',
                        textfont=dict(color=level_colors.get(lv, '#8A8F98'),
                                      family='Barlow, sans-serif', size=11),
                    ))

                fig_co.update_layout(
                    barmode='group',
                    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(family='Barlow, sans-serif', size=11, color='#8A8F98'),
                    margin=dict(t=10, b=80, l=10, r=10),
                    xaxis=dict(
                        tickfont=dict(size=11, color='#8A8F98'),
                        tickangle=-35
                    ),
                    yaxis=dict(gridcolor='#3E4248', tickfont=dict(color='#8A8F98')),
                    legend=dict(
                        orientation='h', yanchor='bottom', y=1.02,
                        xanchor='left', x=0,
                        font=dict(color='#8A8F98', size=11)
                    ),
                    height=400,
                )
                st.plotly_chart(fig_co, use_container_width=True)

             # ── Completion by Contractor ─────────────────────────────────
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

                # Contractor table (real companies only)
                contractor_cl = checklists[checklists['_assign_type'] == 'contractor']
                if not contractor_cl.empty:
                    contractor_summary = contractor_cl.groupby('assigned_company').agg(
                        Total=('status', 'count'),
                        Completed=('status', lambda x: x.isin(complete_statuses).sum())
                    ).reset_index()
                    contractor_summary['Completion %'] = (
                        contractor_summary['Completed'] / contractor_summary['Total'] * 100
                    ).round(1)
                    st.dataframe(
                        contractor_summary.rename(columns={'assigned_company': 'Contractor'}),
                        use_container_width=True, hide_index=True)

                # Role / Unassigned breakdown
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

    # ══════════════════════════════════════════════════════════════
    # TAB 3 — FUNCTIONAL TESTS
    # ══════════════════════════════════════════════════════════════
    with tab3:
        if tests.empty:
            st.info("No functional test data available.")
        else:
            total_tests = len(tests)
            passed  = (tests['status'] == 'Passed').sum()
            failed  = (tests['status'] == 'Failed').sum()
            not_started = (tests['status'] == 'Not Started').sum()
            in_prog = total_tests - passed - failed - not_started
            pass_rate = (passed / total_tests * 100) if total_tests > 0 else 0

            section("Functional Test Summary")

            # ── KPI Cards ────────────────────────────────────────────────
            kpi_data = [
                ("Total Tests", total_tests, '#F0F0F0'),
                ("Passed",      passed,      '#39B54A'),
                ("Failed",      failed,      '#E04040'),
                ("Not Started", not_started, '#8A8F98'),
            ]
            kpi_cols = st.columns(len(kpi_data))
            for i, (label, value, color) in enumerate(kpi_data):
                with kpi_cols[i]:
                    st.markdown(f"""
                    <div style="
                        background: #2D3035; border: 1px solid #3E4248;
                        border-radius: 10px; padding: 16px; text-align: center;
                    ">
                        <div style="font-family: 'Barlow Condensed', sans-serif;
                            font-size: 14px; color: #8A8F98; text-transform: uppercase;
                            letter-spacing: 1px;">{label}</div>
                        <div style="font-family: 'Barlow Condensed', sans-serif;
                            font-size: 32px; font-weight: 700; color: {color};
                            margin: 4px 0;">{value}</div>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown("<div style='height: 16px'></div>", unsafe_allow_html=True)

            # ── Status Donut + Pass Rate Gauge side by side ──────────────
            col_l, col_r = st.columns(2)

            with col_l:
                section("Tests by Status")
                status_counts = tests['status'].value_counts().reset_index()
                status_counts.columns = ['Status', 'Count']

                test_status_colors = {
                    'Passed':      '#39B54A',
                    'Failed':      '#E04040',
                    'Not Started': '#3E4248',
                    'In Progress': '#4A90D9',
                }
                color_list = [test_status_colors.get(s, '#8A8F98') for s in status_counts['Status']]

                fig_donut = go.Figure(go.Pie(
                    labels=status_counts['Status'],
                    values=status_counts['Count'],
                    hole=0.65,
                    marker=dict(colors=color_list),
                    textinfo='percent',
                    textfont=dict(size=12, color='#F0F0F0', family='Barlow, sans-serif'),
                    hovertemplate='%{label}: %{value}<extra></extra>',
                ))
                fig_donut.update_layout(
                    annotations=[dict(
                        text=f"<b>{total_tests}</b>",
                        x=0.5, y=0.5,
                        font=dict(size=22, color='#F0F0F0', family='Barlow Condensed, sans-serif'),
                        showarrow=False
                    )],
                    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(family='Barlow, sans-serif', color='#8A8F98'),
                    margin=dict(t=10, b=10, l=10, r=10),
                    showlegend=True,
                    legend=dict(
                        font=dict(size=11, color='#8A8F98'),
                        orientation='h', yanchor='top', y=-0.05,
                        xanchor='center', x=0.5
                    ),
                    height=300,
                )
                st.plotly_chart(fig_donut, use_container_width=True)

            with col_r:
                section("Pass Rate")
                fig_gauge = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=pass_rate,
                    number=dict(suffix="%", font=dict(size=36, color='#F0F0F0',
                                                       family='Barlow Condensed, sans-serif')),
                    gauge=dict(
                        axis=dict(range=[0, 100], tickfont=dict(color='#8A8F98', size=11)),
                        bar=dict(color='#39B54A'),
                        bgcolor='#3E4248',
                        borderwidth=0,
                        steps=[
                            dict(range=[0, 50], color='#3E4248'),
                            dict(range=[50, 80], color='#3E4248'),
                            dict(range=[80, 100], color='#3E4248'),
                        ],
                        threshold=dict(
                            line=dict(color='#F0F0F0', width=2),
                            thickness=0.75,
                            value=pass_rate
                        ),
                    ),
                ))
                fig_gauge.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(family='Barlow, sans-serif', color='#8A8F98'),
                    margin=dict(t=40, b=10, l=30, r=30),
                    height=300,
                )
                st.plotly_chart(fig_gauge, use_container_width=True)

            # ── Pass/Fail by Equipment Unit ──────────────────────────────
            section("Results by Equipment Unit")

            # Extract unit from asset_name (e.g., DH101.P1-USB → DH101)
            tests['_unit'] = tests['asset_name'].str.extract(r'^([A-Za-z]+\d+)', expand=False)

            if tests['_unit'].notna().any():
                unit_summary = tests.groupby('_unit').agg(
                    Total=('status', 'count'),
                    Passed=('status', lambda x: (x == 'Passed').sum()),
                    Failed=('status', lambda x: (x == 'Failed').sum()),
                    Not_Started=('status', lambda x: (x == 'Not Started').sum()),
                ).reset_index().rename(columns={'_unit': 'Unit'})
                unit_summary = unit_summary.sort_values('Unit')

                fig_unit = go.Figure()
                fig_unit.add_trace(go.Bar(
                    x=unit_summary['Unit'], y=unit_summary['Passed'],
                    name='Passed', marker=dict(color='#39B54A'),
                    text=unit_summary['Passed'].apply(lambda v: str(v) if v > 0 else ''),
                    textposition='inside',
                    textfont=dict(color='#F0F0F0', family='Barlow, sans-serif', size=12),
                ))
                fig_unit.add_trace(go.Bar(
                    x=unit_summary['Unit'], y=unit_summary['Failed'],
                    name='Failed', marker=dict(color='#E04040'),
                    text=unit_summary['Failed'].apply(lambda v: str(v) if v > 0 else ''),
                    textposition='inside',
                    textfont=dict(color='#F0F0F0', family='Barlow, sans-serif', size=12),
                ))
                fig_unit.add_trace(go.Bar(
                    x=unit_summary['Unit'], y=unit_summary['Not_Started'],
                    name='Not Started', marker=dict(color='#3E4248'),
                    text=unit_summary['Not_Started'].apply(lambda v: str(v) if v > 0 else ''),
                    textposition='inside',
                    textfont=dict(color='#8A8F98', family='Barlow, sans-serif', size=12),
                ))
                fig_unit.update_layout(
                    barmode='stack',
                    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(family='Barlow, sans-serif', size=11, color='#8A8F98'),
                    margin=dict(t=10, b=10, l=10, r=10),
                    xaxis=dict(tickfont=dict(size=12, color='#F0F0F0')),
                    yaxis=dict(gridcolor='#3E4248', tickfont=dict(color='#8A8F98')),
                    legend=dict(
                        orientation='h', yanchor='bottom', y=1.02,
                        xanchor='left', x=0,
                        font=dict(color='#8A8F98', size=11)
                    ),
                    height=350,
                )
                st.plotly_chart(fig_unit, use_container_width=True)

            # ── Results by Contractor ────────────────────────────────────
            if 'assigned_company' in tests.columns:
                section("Results by Contractor")

                co_summary = tests.groupby('assigned_company').agg(
                    Total=('status', 'count'),
                    Passed=('status', lambda x: (x == 'Passed').sum()),
                    Failed=('status', lambda x: (x == 'Failed').sum()),
                ).reset_index()
                co_summary['Pass Rate %'] = (
                    co_summary['Passed'] / co_summary['Total'] * 100
                ).round(1)
                co_summary = co_summary.sort_values('Total', ascending=True)

                fig_co = go.Figure()
                fig_co.add_trace(go.Bar(
                    y=co_summary['assigned_company'], x=co_summary['Passed'],
                    name='Passed', orientation='h',
                    marker=dict(color='#39B54A'),
                    text=co_summary['Passed'].apply(lambda v: str(v) if v > 0 else ''),
                    textposition='inside',
                    textfont=dict(color='#F0F0F0', family='Barlow, sans-serif', size=12),
                ))
                fig_co.add_trace(go.Bar(
                    y=co_summary['assigned_company'], x=co_summary['Failed'],
                    name='Failed', orientation='h',
                    marker=dict(color='#E04040'),
                    text=co_summary['Failed'].apply(lambda v: str(v) if v > 0 else ''),
                    textposition='inside',
                    textfont=dict(color='#F0F0F0', family='Barlow, sans-serif', size=12),
                ))
                fig_co.add_trace(go.Bar(
                    y=co_summary['assigned_company'],
                    x=co_summary['Total'] - co_summary['Passed'] - co_summary['Failed'],
                    name='Not Started / In Progress', orientation='h',
                    marker=dict(color='#3E4248'),
                ))
                fig_co.update_layout(
                    barmode='stack',
                    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(family='Barlow, sans-serif', size=11, color='#8A8F98'),
                    margin=dict(t=10, b=10, l=10, r=40),
                    xaxis=dict(gridcolor='#3E4248', tickfont=dict(color='#8A8F98')),
                    yaxis=dict(tickfont=dict(size=11, color='#F0F0F0')),
                    legend=dict(
                        orientation='h', yanchor='bottom', y=1.02,
                        xanchor='left', x=0,
                        font=dict(color='#8A8F98', size=11)
                    ),
                    height=max(200, len(co_summary) * 60),
                )
                st.plotly_chart(fig_co, use_container_width=True)

            # ── Full Test Detail (expandable) ────────────────────────────
            with st.expander("View All Tests"):
                display_cols = ['name', 'status', 'assigned_name', 'discipline',
                                'attempt_count', 'asset_name']
                available = [c for c in display_cols if c in tests.columns]
                st.dataframe(tests[available], use_container_width=True, hide_index=True)

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