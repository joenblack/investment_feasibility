import streamlit as st
import pandas as pd
import sys
import os
import copy
import plotly.express as px

# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from ui.components import ensure_state, sidebar_nav, t, require_active_project, bootstrap
from core.engine import calculate_financials

bootstrap(require_project=True)
sidebar_nav()

st.title(t("scenario_title"))

if st.session_state.project and st.session_state.project.id:
    # --- SPRINT 2: BASELINE vs INVESTMENT COMPARISON ---
    if getattr(st.session_state.project, 'baseline_enabled', False):
        st.subheader(t("growth_analysis_title"))
        
        from core.engine import calculate_baseline
        
        with st.spinner("Calculating Baseline Scenario..."):
            res_baseline = calculate_baseline(st.session_state.project)
            res_current = calculate_financials(st.session_state.project)
            
        # Comparison Metrics (Totals for Horizon)
        # Revenue, EBITDA, Free Cash Flow (Firm or Equity based on mode), NPV
        
        def get_total(res, metric_key):
             if metric_key == "Revenue":
                 return res.revenue_arr.sum()
             elif metric_key == "EBITDA":
                 return res.ebitda_arr.sum()
             elif metric_key == "Avg EBITDA":
                 return res.ebitda_arr.mean() if len(res.ebitda_arr) > 0 else 0
             elif metric_key == "NPV":
                 return res.kpi.get('npv', 0)
             elif metric_key == "Net Cash":
                 # Use Sum of FCF
                 return res.free_cash_flow.sum()
             return 0
             
        metric_defs = [
            ("Revenue", t("th_revenue")),
            ("EBITDA", t("th_ebitda")),
            ("Avg EBITDA", t("th_avg_ebitda")), # Added New Metric
            ("Net Cash", t("th_cash_flow")),
            ("NPV", t("npv_label"))
        ]
        data = []
        
        for key, label in metric_defs:
            val_base = get_total(res_baseline, key)
            val_curr = get_total(res_current, key)
            diff = val_curr - val_base
            data.append({
                t("col_metric"): label,
                t("col_without_inv"): val_base,
                t("col_with_inv"): val_curr,
                t("col_difference"): diff
            })
            
        df_comp = pd.DataFrame(data)
        
        # Display with Styler
        # Highlight Difference: Green if > 0, Red if < 0 (assuming higher is better for these metrics)
        def color_diff(val):
            color = 'green' if val > 0 else 'red' if val < 0 else 'gray'
            return f'color: {color}'
            
        st.dataframe(
            df_comp.style.format({
                t("col_without_inv"): "{:,.0f}",
                t("col_with_inv"): "{:,.0f}",
                t("col_difference"): "{:+,.0f}"
            }).map(color_diff, subset=[t("col_difference")]),
            use_container_width=True
        )
        st.divider()
    else:
        # CTA to enable Growth Mode
        with st.container():
            st.info(f"💡 **{t('growth_analysis_title')}**: " + t("enable_growth_hint"))


    # 1. Configuration
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader(t("best_case"))
        b_vol = st.number_input(f"{t('vol_impact')} ({t('best_case')})", value=20.0, step=5.0, key="b_vol")
        b_price = st.number_input(f"{t('price_impact')} ({t('best_case')})", value=10.0, step=5.0, key="b_price")
        b_cost = st.number_input(f"{t('cost_impact')} ({t('best_case')})", value=-5.0, step=1.0, key="b_cost") # Lower cost is better
        b_capex = st.number_input(f"{t('capex_impact')} ({t('best_case')})", value=0.0, step=5.0, key="b_capex")

    with c2:
        st.subheader(t("worst_case"))
        w_vol = st.number_input(f"{t('vol_impact')} ({t('worst_case')})", value=-20.0, step=5.0, key="w_vol")
        w_price = st.number_input(f"{t('price_impact')} ({t('worst_case')})", value=-10.0, step=5.0, key="w_price")
        w_cost = st.number_input(f"{t('cost_impact')} ({t('worst_case')})", value=10.0, step=1.0, key="w_cost") # Higher cost is worse
        w_capex = st.number_input(f"{t('capex_impact')} ({t('worst_case')})", value=10.0, step=5.0, key="w_capex")

    if st.button(t("compare_btn"), type="primary"):
        st.divider()
        st.subheader(t("comparison_results"))
        
        # 2. Simulation Logic
        # Helper to run scenario
        def run_scenario(vol_pct, price_pct, cost_pct, capex_pct):
            proj = copy.deepcopy(st.session_state.project)
            
            # Apply shocks
            for p in proj.products:
                p.initial_volume *= (1 + vol_pct/100)
                p.unit_price *= (1 + price_pct/100)
                p.unit_cost *= (1 + cost_pct/100)
                
            for c in proj.capex_items:
                c.amount *= (1 + capex_pct/100)
                
            return calculate_financials(proj)
            
        # Base
        res_base = calculate_financials(st.session_state.project)
        
        # Best
        res_best = run_scenario(b_vol, b_price, b_cost, b_capex)
        
        # Worst
        res_worst = run_scenario(w_vol, w_price, w_cost, w_capex)
        
        # 3. Output
        data = {
            t("col_metric"): [t("npv_label"), t("irr_label"), t("payback_period")],
            t("base_case"): [
                res_base.kpi.get("npv", 0), 
                res_base.kpi.get("irr", 0)*100, 
                res_base.kpi.get("payback", 0)
            ],
            t("best_case"): [
                res_best.kpi.get("npv", 0), 
                res_best.kpi.get("irr", 0)*100, 
                res_best.kpi.get("payback", 0)
            ],
            t("worst_case"): [
                res_worst.kpi.get("npv", 0), 
                res_worst.kpi.get("irr", 0)*100, 
                res_worst.kpi.get("payback", 0)
            ]
        }
        
        df_res = pd.DataFrame(data)
        
        # formatting
        # Display as dataframe with style? Or simple
        st.dataframe(df_res.style.format({t("base_case"): "{:,.1f}", t("best_case"): "{:,.1f}", t("worst_case"): "{:,.1f}"}))
        
        # Chart: NPV Comparison
        df_chart = pd.DataFrame({
            t("col_scenario"): [t("worst_case"), t("base_case"), t("best_case")],
            "NPV": [res_worst.kpi.get("npv", 0), res_base.kpi.get("npv", 0), res_best.kpi.get("npv", 0)],
            "Color": ["red", "grey", "green"]
        })
        
        fig = px.bar(df_chart, x=t("col_scenario"), y="NPV", color=t("col_scenario"), color_discrete_map={
            t("worst_case"): "red",
            t("base_case"): "grey", 
            t("best_case"): "green"
        }, text_auto=".2s")
        st.plotly_chart(fig, use_container_width=True)
        
        # Overlay Line Chart: Cumulative Discounted Cash Flow
        st.subheader(t("cf_trajectory_title"))
        
        # Prepare time series data
        def get_cum_dcf(res):
            # Assuming 'Free Cash Flow' or similar exists. Engine returns 'df' usually? 
            # Engine result has .financial_statements DataFrame.
            # Need to re-calculate DCF vector or use available one.
            # kpi['npv'] is sum. 
            # core/engine.py: calculate_financials returns FinancialResults(kpi, financial_statements)
            # Statement has "Free Cash Flow (Unlevered)" usually.
            
            # res.financial_statements does not exist. Use cash_flow_statement.
            
            # Let's use "FCFF" or "FCFE" based on what we want. Usually Cash Flow trajectory = Cumulative FCF.
            df = res.cash_flow_statement
            col = "FCFF" if "FCFF" in df.columns else "Net Cash Flow"
            if col in df.columns:
                return df[col].cumsum()
            return []

        # Extract time
        years = res_base.years
        
        df_overlay = pd.DataFrame({t("year"): years})
        df_overlay[t("base_case")] = get_cum_dcf(res_base)
        df_overlay[t("best_case")] = get_cum_dcf(res_best)
        df_overlay[t("worst_case")] = get_cum_dcf(res_worst)
        
        # Melt for Plotly
        df_melt = df_overlay.melt(id_vars=t("year"), var_name=t("col_scenario"), value_name=t("cumulative_fcf"))
        
        fig_line = px.line(df_melt, x=t("year"), y=t("cumulative_fcf"), color=t("col_scenario"), 
                          color_discrete_map={
                                t("worst_case"): "red",
                                t("base_case"): "grey", 
                                t("best_case"): "green"
                          }, markers=True)
        st.plotly_chart(fig_line, use_container_width=True)

else:
    st.info(t("navigate_hint"))
