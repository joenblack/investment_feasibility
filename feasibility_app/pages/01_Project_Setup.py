import streamlit as st

from ui.components import ensure_state, sidebar_nav, save_button, t, bootstrap

bootstrap(require_project=False)
sidebar_nav()

# Dynamic Title (Create vs Edit)
if st.session_state.get("project_active", False):
    st.title(t("setup_title"))
else:
    st.title(t("create_project_title"))
st.markdown("---")

c1, c2 = st.columns(2)
with c1:
    st.session_state.project.name = st.text_input(t("project_name"), value=st.session_state.project.name, help=t("project_name_help"))
    st.session_state.project.description = st.text_area(t("description"), value=st.session_state.project.description, help=t("description_help"))
    st.session_state.project.start_year = st.number_input(t("start_year"), value=st.session_state.project.start_year, help=t("start_year_help"))

with c2:
    st.session_state.project.horizon_years = st.slider(t("project_horizon"), 3, 30, st.session_state.project.horizon_years, help=t("project_horizon_help"))
    curr_opts = ["TRY", "USD", "EUR"]
    try:
        curr_idx = curr_opts.index(st.session_state.project.currency_base)
    except:
        curr_idx = 0
    st.session_state.project.currency_base = st.selectbox(t("base_currency"), curr_opts, index=curr_idx, help=t("base_currency_help"))
    
    gran_map = {"Year": t("gran_year"), "Month": t("gran_month")}
    gran_opts = ["Year", "Month"]
    gran_idx = 0 if st.session_state.project.granularity == "Year" else 1
    selected_gran = st.selectbox(
        t("granularity_label"), 
        gran_opts, 
        index=gran_idx,
        format_func=lambda x: gran_map.get(x, x)
    )
    st.session_state.project.granularity = selected_gran
    
    st.session_state.project.inflation_rate = st.number_input(t("inflation_rate"), value=st.session_state.project.inflation_rate * 100.0, help=t("inflation_rate_help")) / 100.0

st.header(t("valuation_method"))
mode_map = {"Unlevered": t("val_unlevered"), "Levered": t("val_levered")}
st.session_state.project.calculation_mode = st.radio(
    t("valuation_basis"), 
    ["Unlevered", "Levered"], 
    index=0 if st.session_state.project.calculation_mode == "Unlevered" else 1, 
    format_func=lambda x: mode_map[x],
    help=f"{t('unlevered_help')}\n{t('levered_help')}"
    help=f"{t('unlevered_help')}\n{t('levered_help')}"
)

# Valuation Method Explanation
st.info(t("calc_mode_explanation"))

# Discount Rates
with c2:
    st.subheader(t("discount_settings"))
    st.session_state.project.discount_rate_unlevered = st.number_input(t("discount_rate_wacc"), value=st.session_state.project.discount_rate_unlevered, format="%.3f", step=0.005, help=t("discount_rate_help"))
    st.session_state.project.discount_rate_levered = st.number_input(t("discount_rate_coe"), value=st.session_state.project.discount_rate_levered, format="%.3f", step=0.005, help=t("discount_rate_help"))

# --- Exchange Rates ---
st.divider()
st.subheader(t("exchange_rates"))

# Dynamic Editor for Rates
# Standard: USD, EUR, TRY
rates = st.session_state.project.exchange_rates

fx_cols = st.columns(3)

with fx_cols[0]:
    rates["USD"] = st.number_input("USD/TL", value=rates.get("USD", 35.0))
    
with fx_cols[1]:
    rates["EUR"] = st.number_input("EUR/TL", value=rates.get("EUR", 38.0))
    
with fx_cols[2]:
    rates["TRY"] = st.number_input("TRY/TL", value=rates.get("TRY", 1.0), disabled=True)
    
st.session_state.project.exchange_rates = rates

# Add newline before buttons
st.write("")

# save_button() removed to avoid duplicate ID error. One at bottom suffices.
st.header(t("tv_title"))
tv_method_map = {
    "None": "None", 
    "PerpetuityGrowth": t("tv_perpetuity"), 
    "ExitMultiple": t("tv_multiple")
}
tv_method = st.selectbox(
    t("tv_method"),
    ["None", "PerpetuityGrowth", "ExitMultiple"],
    index=["None", "PerpetuityGrowth", "ExitMultiple"].index(st.session_state.project.tv_config.method),
    format_func=lambda x: tv_method_map.get(x, x)
)
st.session_state.project.tv_config.method = tv_method

if tv_method == "PerpetuityGrowth":
    g_rate = st.number_input(
        t("tv_growth_rate"), 
        value=st.session_state.project.tv_config.growth_rate * 100.0,
        step=0.1
    )
    st.session_state.project.tv_config.growth_rate = g_rate / 100.0
elif tv_method == "ExitMultiple":
    mult = st.number_input(
        t("tv_exit_multiple"), 
        value=st.session_state.project.tv_config.exit_multiple,
        step=0.5
    )
    st.session_state.project.tv_config.exit_multiple = mult

    st.session_state.project.tv_config.exit_multiple = mult

st.header(t("tax_config"))
st.session_state.project.tax_config.vat_exemption = st.checkbox(t("vat_exemption_label"), value=st.session_state.project.tax_config.vat_exemption)

st.markdown("---")
save_button()
