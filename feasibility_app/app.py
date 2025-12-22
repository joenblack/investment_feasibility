import pandas as pd
import streamlit as st
import sys
import os

# Add root logic to path - NOT NEEDED if run as streamlit run App.py
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ui.components import ensure_state, sidebar_nav, save_button, t, bootstrap
from core.db import list_projects, load_project, delete_project
from core.auth import logout, check_permission
from core.model import ProjectModel
from core.engine import calculate_financials
from core.insights import generate_insights
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Invest Feasibility", layout="wide")

# Centralized Bootstrap (Init DB, State, Auth)
bootstrap(require_project=False) # Dashboard doesn't enforce active project immediately

# ... rest of code uses st.session_state.user which is guaranteed by bootstrap ...
    
# Logged In
user = st.session_state.user
st.sidebar.info(f"User: {user['username']} ({user['role']})")
if st.sidebar.button("Logout"):
    logout()

sidebar_nav()

st.title(t("project_dashboard"))

# Project Selection
projects = list_projects()

if not projects:
    st.info(t("no_projects")) # "No projects found" or similar key
else:
    # Selector
    selected_id = st.selectbox(
        t("select_project"), 
        options=[p['id'] for p in projects], 
        format_func=lambda x: next((f"{p['name']} ({p['updated_at']})" for p in projects if p['id'] == x), x)
    )
    
    col_load, col_del = st.columns([1, 1])
    
    # Load Logic
    with col_load:
        if st.button(t("load"), type="primary", use_container_width=True):
            st.session_state.confirm_action = 'load'
            st.session_state.confirm_id = selected_id
            
    # History View
    with st.expander(t("show_version_history")):
        from core.db import list_project_history
        hist = list_project_history(selected_id)
        if hist:
            h_df = pd.DataFrame(hist)
            # Rename columns for display
            h_df = h_df.rename(columns={
                "version_tag": t("col_version_tag"),
                "timestamp": t("col_timestamp"),
                "user": t("col_user")
            })
            st.dataframe(h_df, use_container_width=True)
        else:
            st.info(t("no_history_found"))
            
    # Delete Logic
    with col_del:
        if st.button(t("delete"), type="secondary", use_container_width=True):
            st.session_state.confirm_action = 'delete'
            st.session_state.confirm_id = selected_id
            
    # Confirmation Area
    if 'confirm_action' in st.session_state and st.session_state.confirm_id == selected_id:
        st.divider()
        if st.session_state.confirm_action == 'load':
            st.warning(t("load_confirm_msg"), icon="⚠️")
            c1, c2 = st.columns([1, 4])
            if c1.button(t("confirm_yes"), key="btn_confirm_load", type="primary"):
                loaded = load_project(selected_id)
                if loaded:
                    st.session_state.project = loaded
                    st.session_state.project_active = True
                    st.query_params["id"] = loaded.id
                    del st.session_state.confirm_action
                    st.rerun()
            if c2.button(t("confirm_cancel"), key="btn_cancel_load"):
                del st.session_state.confirm_action
                st.rerun()
                
        elif st.session_state.confirm_action == 'delete':
             st.error(t("delete_confirm_msg"), icon="🗑️")
             c1, c2 = st.columns([1, 4])
             
             # Permission Check for Delete
             if not check_permission(user['role'], 'delete_project'):
                 st.error("Access Denied: You do not have permission to delete projects.")
             else:
                 if c1.button(t("confirm_yes"), key="btn_confirm_del", type="primary"):
                     delete_project(selected_id, user['username'])
                     st.success(t("project_deleted"))
                     del st.session_state.confirm_action
                     st.rerun()
             
             if c2.button(t("confirm_cancel"), key="btn_cancel_del"):
                 del st.session_state.confirm_action
                 st.rerun()

st.divider()

if st.session_state.project and st.session_state.project.id:
    # --- Executive Dashboard ---
    st.header(t("exec_summary"))
    
    # Calculate Results
    try:
        results = calculate_financials(st.session_state.project)
        
        # 1. KPI Cards
        kpi = results.kpi
        c1, c2, c3, c4 = st.columns(4)
        
        fmt_currency = st.session_state.project.currency_base
        
        # Determine NPV Label (Equity vs Firm)
        npv_basis_label = t("npv_basis_equity") if st.session_state.project.calculation_mode == "Levered" else t("npv_basis_firm")
        
        with c1:
            st.metric(f"{t('npv_label')} ({npv_basis_label})", f"{kpi.get('npv', 0):,.0f} {fmt_currency}", help=t("npv_help"))
        with c2:
            st.metric(t("irr_label"), f"{kpi.get('irr', 0) * 100:.1f} %", help=t("irr_help"))
        with c3:
            st.metric(t("roi"), f"{kpi.get('roi', 0):.1f} %", help=t("roi_help"))
        with c4:
            st.metric(t("payback_period"), f"{kpi.get('payback', 0):.1f}", help=t("payback_help"))
            
        # --- SMART INSIGHTS ---
        insights_list = generate_insights(st.session_state.project, results)
        if insights_list:
            with st.expander(t("insights_title"), expanded=True):
                for insight in insights_list:
                    msg = t(insight["message_key"]).format(**insight["params"])
                    if insight["type"] == "warning":
                        st.warning(msg, icon="⚠️")
                    elif insight["type"] == "info":
                        st.info(msg, icon="ℹ️")
                    else:
                        st.success(msg)
            
        st.divider()
        
        # 2. Charts & Summary
        col_chart, col_table = st.columns([2, 1])
        
        with col_chart:
            st.subheader(t("chart_fcf_trend"))
            df_chart = pd.DataFrame({
                "Year": results.years,
                "FCF": results.free_cash_flow
            })
            
            # Area Chart for FCF
            fig = px.area(df_chart, x="Year", y="FCF", title=None)
            fig.update_layout(
                margin=dict(l=0, r=0, t=0, b=0),
                height=300,
                xaxis_title=None,
                yaxis_title=None,
                showlegend=False
            )
            # Add markers
            fig.update_traces(mode="lines+markers")
            st.plotly_chart(fig, use_container_width=True)
            
        with col_table:
            st.subheader(t("chart_snapshot"))
            # Show Average Revenue, EBITDA, Margin
            avg_rev = results.revenue_arr.mean() if len(results.revenue_arr) > 0 else 0
            avg_ebitda = results.ebitda_arr.mean() if len(results.ebitda_arr) > 0 else 0
            avg_margin = (avg_ebitda / avg_rev * 100) if avg_rev > 0 else 0
            
            st.metric(t("avg_revenue"), f"{avg_rev:,.0f}", help=t("avg_revenue_help"))
            st.metric(t("avg_ebitda"), f"{avg_ebitda:,.0f}", help=t("avg_ebitda_help"))
            st.metric(t("avg_margin"), f"{avg_margin:.1f}%", help=t("avg_margin_help"))
            
            st.progress(min(max(avg_margin/100, 0.0), 1.0))
            
            # Project Details
            st.caption(f"**{t('lbl_project')}:** {st.session_state.project.name}")
            st.caption(f"**{t('lbl_horizon')}:** {st.session_state.project.horizon_years} {t('year')}")
            
        # Quick Edit Name
        new_name = st.text_input(t("project_name"), value=st.session_state.project.name)
        if new_name != st.session_state.project.name:
            st.session_state.project.name = new_name
            
        save_button()
        
    except Exception as e:
         st.error(f"Error calculating dashboard: {str(e)}")
else:
    st.info(t("navigate_hint"))
