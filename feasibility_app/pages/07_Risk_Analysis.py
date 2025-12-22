import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os

# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from ui.components import ensure_state, sidebar_nav, t, require_active_project, bootstrap
from core.risk import run_sensitivity_variable, run_monte_carlo, run_tornado_analysis

bootstrap(require_project=True)
sidebar_nav()

st.title(t("risk_title"))
tab_tornado, tab_mc_setup, tab_mc_res = st.tabs([t("tab_tornado"), t("setup_mc_tab"), t("mc_results_tab")])

# --- TAB 1: TORNADO / SENSITIVITY ---
with tab_tornado:
    st.subheader(t("auto_tornado_title"))
    st.info(t("auto_tornado_info"))
    
    if st.button(t("run_tornado")):
        with st.spinner(t("calc_sens")):
            df = run_tornado_analysis(st.session_state.project)
            
        # Tornado Plot
        # Plotly Express doesn't do "Base relative" easily, use Graph Objects
        fig = go.Figure()

        # Efficient approach (Relative to Zero for "Delta")
        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=df["Variable"],
            x=df["Swing Down"],
            name=t("downside_case"),
            orientation='h',
            marker=dict(color='#d62728')
        ))
        fig.add_trace(go.Bar(
            y=df["Variable"],
            x=df["Swing Up"],
            name=t("upside_case"),
            orientation='h',
            marker=dict(color='#2ca02c')
        ))
        
        fig.update_layout(
            title=t("tornado_chart_title"),
            barmode='relative', 
            xaxis_title=t("npv_change_axis"),
            yaxis_title=t("variable_config"),
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Format only numeric columns
        # Localize columns for display
        df_disp = df.rename(columns={
            "Variable": t("col_variable"),
            "Base NPV": t("col_base_npv"),
            "Downside NPV (0.9x)": t("col_downside_npv"),
            "Upside NPV (1.1x)": t("col_upside_npv"),
            "Range": t("col_range"),
            "Swing Down": t("col_swing_down"),
            "Swing Up": t("col_swing_up")
        })
        st.dataframe(df_disp.style.format("{:,.0f}", subset=df_disp.select_dtypes(include=[np.number]).columns))

# --- TAB 2: MC SETUP ---
with tab_mc_setup:
    st.subheader(t("simulation_settings"))
    
    c1, c2 = st.columns(2)
    st.session_state.project.risk_config.monte_carlo_iterations = c1.number_input(
        t("iterations"), 
        min_value=100, max_value=10000, step=100,
        value=st.session_state.project.risk_config.monte_carlo_iterations
    )
    st.session_state.project.risk_config.random_seed = c2.number_input(t("random_seed"), value=42)
    
    st.markdown(f"### {t('variable_config')}")
    vars_to_config = ["Volume", "Price", "CAPEX", "OPEX"]
    cols = st.columns(2)
    
    for i, var in enumerate(vars_to_config):
        config = st.session_state.project.risk_config.get_config(var)
        with cols[i % 2]:
            st.markdown(f"**{t('var_' + var.lower())}**")
            # Type
            new_type = st.selectbox(
                t("dist_type"), 
                ["Normal", "Triangular", "Uniform", "Lognormal"], 
                index=["Normal", "Triangular", "Uniform", "Lognormal"].index(config.dist_type),
                key=f"dist_{var}_new"
            )
            config.dist_type = new_type
            
            # Params
            if config.dist_type in ["Normal", "Lognormal"]:
                c_a, c_b = st.columns(2)
                config.mean_pct = c_a.number_input(t("mc_mean_shift"), value=config.mean_pct*100, key=f"m_{var}") / 100.0
                config.std_dev_pct = c_b.number_input(t("mc_std_dev_vol"), value=config.std_dev_pct*100, key=f"s_{var}") / 100.0
            elif config.dist_type == "Triangular":
                c_a, c_b, c_c = st.columns(3)
                config.min_pct = c_a.number_input(t("mc_min_pct"), value=config.min_pct*100, key=f"min_{var}") / 100.0
                config.mode_pct = c_b.number_input(t("mc_mode_pct"), value=config.mode_pct*100, key=f"mod_{var}") / 100.0
                config.max_pct = c_c.number_input(t("mc_max_pct"), value=config.max_pct*100, key=f"max_{var}") / 100.0
            elif config.dist_type == "Uniform":
                c_a, c_b = st.columns(2)
                config.min_pct = c_a.number_input(t("mc_min_pct"), value=config.min_pct*100, key=f"u_min_{var}") / 100.0
                config.max_pct = c_b.number_input(t("mc_max_pct"), value=config.max_pct*100, key=f"u_max_{var}") / 100.0

    st.markdown(f"### {t('correlations')}")
    st.info(t("corr_info"))
    
    corr_pv = st.slider(t("corr_price_vol"), -1.0, 1.0, st.session_state.project.risk_config.get_correlation("Price", "Volume"), 0.1)
    st.session_state.project.risk_config.set_correlation("Price", "Volume", corr_pv)
    
    if st.button(t("run_sim_btn"), type="primary"):
        with st.spinner(f"{t('running_sim')} ({st.session_state.project.risk_config.monte_carlo_iterations})"):
            mc_results = run_monte_carlo(
                st.session_state.project, 
                iterations=st.session_state.project.risk_config.monte_carlo_iterations
            )
            st.session_state['mc_results'] = mc_results
            st.success(t("sim_success"))

# --- TAB 3: MC RESULTS ---
with tab_mc_res:
    if 'mc_results' in st.session_state:
        df = st.session_state['mc_results']
        
        # KPI Cards
        mean_npv = df['NPV'].mean()
        std_npv = df['NPV'].std()
        prob_profit = (df['NPV'] > 0).mean() * 100
        p5 = np.percentile(df['NPV'], 5)
        var_95 = mean_npv - p5
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric(t("mean_npv"), f"{mean_npv:,.0f}")
        col2.metric(t("prob_profit"), f"{prob_profit:.1f}%")
        col3.metric(t("var_95"), f"{var_95:,.0f}", delta_color="inverse")
        col4.metric(t("std_dev"), f"{std_npv:,.0f}")
        
        # Advanced Histogram
        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=df['NPV'], 
            nbinsx=50, 
            name=t("npv_dist"),
            marker_color='#1f77b4',
            opacity=0.7
        ))
        
        # Add Lines
        fig.add_vline(x=0, line_width=2, line_dash="dash", line_color="black", annotation_text=t("break_even_line"))
        fig.add_vline(x=mean_npv, line_width=2, line_color="green", annotation_text=t("mean_line"))
        fig.add_vline(x=p5, line_width=2, line_dash="dot", line_color="red", annotation_text=t("var_95"))
        
        fig.update_layout(title=t("hist_title"), xaxis_title="NPV", yaxis_title="Frekans")
        st.plotly_chart(fig, use_container_width=True)
        
        # Scatter for Correlation verification
        with st.expander(t("scatter_expander")):
            fig_scat = px.scatter(
                df, 
                x="Volume_Factor", 
                y="Price_Factor", 
                color="NPV", 
                title=t("scatter_title"),
                labels={
                    "Volume_Factor": t("input_vol_factor"),
                    "Price_Factor": t("input_price_factor")
                }
            )
            st.plotly_chart(fig_scat, use_container_width=True)
            
    else:
        st.info(t("mc_run_warning"))
