import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from ui.components import ensure_state, sidebar_nav, t, require_active_project, bootstrap
from core.engine import calculate_financials

bootstrap(require_project=True)
sidebar_nav()

st.title(t("charts_title"))
results = calculate_financials(st.session_state.project)
years = results.years

# 1. Cash Flow Waterfall or Bar
st.subheader(t("fcf_profile"))
df_cf = pd.DataFrame({
    "Year": years,
    "FCF": results.free_cash_flow,
    "Cumulative FCF": results.free_cash_flow.cumsum()
})

fig_cf = go.Figure()
fig_cf.add_trace(go.Bar(x=df_cf["Year"], y=df_cf["FCF"], name=t("annual_fcf")))
fig_cf.add_trace(go.Scatter(x=df_cf["Year"], y=df_cf["Cumulative FCF"], name=t("cumulative_fcf"), mode="lines+markers", yaxis="y2"))

fig_cf.update_layout(
    xaxis_title=t("year"),
    yaxis_title=t("chart_fcf_trend"),
    yaxis2=dict(title=t("cumulative_fcf"), overlaying="y", side="right"),
    legend=dict(x=0, y=1.1, orientation="h")
)
st.plotly_chart(fig_cf, use_container_width=True)

# 2. EBITDA vs Net Income
st.subheader(t("prof_evolution"))
df_prof = pd.DataFrame({
    "Year": years,
    "EBITDA": results.ebitda_arr,
    "Net Income": results.income_statement["Net Income"].values
})
fig_prof = px.line(
    df_prof, 
    x="Year", 
    y=["EBITDA", "Net Income"], 
    markers=True,
    labels={"Year": t("year"), "value": t("amount"), "variable": t("category")}
)
st.plotly_chart(fig_prof, use_container_width=True)

# 3. Cost Structure (Year 1 vs Peak Year)
# Keep it simple: Just look at Year 2 (assuming full ops)
# 3. Waterfall Chart (Total Project Cash Flow Walk)
st.subheader(t("waterfall_title"))

# Aggregate totals
total_rev = results.income_statement["Revenue"].sum()
total_cogs = results.income_statement["COGS"].sum() # Negative
total_opex = results.income_statement["OPEX"].sum() # Negative
total_tax = results.income_statement["Tax"].sum()   # Negative
total_capex = results.cash_flow_statement["CAPEX (w/ VAT)"].sum() # Negative
total_nwc = results.cash_flow_statement["Delta NWC"].sum() # Negative/Positive
total_fcf = results.free_cash_flow.sum()

# Measure: absolute, relative...
fig_water = go.Figure(go.Waterfall(
    name = "20", orientation = "v",
    measure = ["absolute", "relative", "relative", "relative", "relative", "relative", "total"],
    x = [t("th_revenue"), t("th_cogs"), t("th_opex"), t("th_tax"), "CAPEX", "NWC", "Total FCF"],
    textposition = "outside",
    text = [f"{val/1_000_000:.1f}M" for val in [total_rev, total_cogs, total_opex, total_tax, total_capex, total_nwc, total_fcf]],
    y = [total_rev, total_cogs, total_opex, total_tax, total_capex, total_nwc, total_fcf],
    connector = {"line":{"color":"rgb(63, 63, 63)"}},
))

fig_water.update_layout(
        title = t("waterfall_title"),
        showlegend = False
)
st.plotly_chart(fig_water, use_container_width=True)

# 4. Break-even Analysis (Year 2 Steady State)
st.subheader(t("breakeven_title"))
try:
    # Use Year 2 data
    y_idx = 1
    if len(results.revenue_arr) > y_idx:
        # Fixed Costs: OPEX (assuming mostly fixed for this viz, though model has fixed/variable split, we treated summary as OPEX)
        # Actually in Model: OPEX is Fixed + Personnel. COGS includes Variable.
        # Fixed = OPEX + Depreciation + Interest?
        # Let's approximate: Fixed = OPEX + Personnel (which is in OPEX). Variable = COGS.
        
        fixed_cost = -results.income_statement["OPEX"].values[y_idx]
        # Variable Cost Ratio = COGS / Revenue
        rev_y2 = results.revenue_arr[y_idx]
        if rev_y2 > 0:
            cogs_y2 = -results.income_statement["COGS"].values[y_idx]
            vc_ratio = cogs_y2 / rev_y2
            
            # Simulation range: 0 to 150% of current revenue
            sim_rev = np.linspace(0, rev_y2 * 1.5, 50)
            sim_vc = sim_rev * vc_ratio
            sim_tc = fixed_cost + sim_vc
            
            df_be = pd.DataFrame({
                "Revenue": sim_rev,
                "Total Cost": sim_tc,
                "Fixed Cost": fixed_cost
            })
            
            fig_be = go.Figure()
            fig_be.add_trace(go.Scatter(x=df_be["Revenue"], y=df_be["Revenue"], name=t("th_revenue"), mode="lines"))
            fig_be.add_trace(go.Scatter(x=df_be["Revenue"], y=df_be["Total Cost"], name=t("cost_structure"), mode="lines"))
            fig_be.add_trace(go.Scatter(x=df_be["Revenue"], y=[fixed_cost]*len(df_be), name=t("tab_fixed_exp"), mode="lines", line=dict(dash="dash")))
            
            # Intersection (Approx)
            # Revenue = Fixed + Rev*VC_Ratio  => Rev * (1 - VC) = Fixed => Rev_BE = Fixed / (1 - VC)
            if (1 - vc_ratio) > 0:
                be_point = fixed_cost / (1 - vc_ratio)
                fig_be.add_vline(x=be_point, line_dash="dot", annotation_text=f"BEP: {be_point:,.0f}")
            
            fig_be.update_layout(title=t("breakeven_title"), xaxis_title=t("th_revenue"), yaxis_title=t("amount"))
            st.plotly_chart(fig_be, use_container_width=True)
        else:
            st.info(t("no_rev_year_2"))
except Exception as e:
    st.write(f"Could not calculate break-even: {e}")
