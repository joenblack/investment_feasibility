import streamlit as st
import pandas as pd

from ui.components import ensure_state, sidebar_nav, save_button, t, require_active_project, bootstrap
from core.model import CAPEXItem

bootstrap(require_project=True)
sidebar_nav()

st.title(t("capex_title"))
st.info(t("capex_info"))

# Add New Item Form
with st.expander(t("add_new_capex"), expanded=False):
    c1, c2, c3 = st.columns(3)
    new_name = c1.text_input(t("item_name"))
    
    cat_opts = ["Machinery", "Building/Construction", "Infrastructure", "Land", "Software", "Installation", "Other"]
    cat_map = {
        "Machinery": t("cat_machinery"),
        "Building/Construction": t("cat_building"),
        "Infrastructure": t("cat_infrastructure"),
        "Land": t("cat_land"),
        "Software": t("cat_software"),
        "Installation": t("cat_installation"),
        "Other": t("cat_other")
    }
    
    new_cat = c2.selectbox(t("category"), cat_opts, format_func=lambda x: cat_map.get(x, x))
    new_amount = c3.number_input(t("amount"), min_value=0.0)
    
    c4, c5 = st.columns(2)
    new_year = c4.number_input(t("investment_year"), min_value=1, max_value=st.session_state.project.horizon_years, value=1)
    new_vat = c5.number_input(t("vat_rate"), value=20.0)
    
    if st.button(t("add_item")):
        item = CAPEXItem(name=new_name, category=new_cat, amount=new_amount, year=int(new_year), vat_rate=new_vat/100.0)
        st.session_state.project.capex_items.append(item)
        st.success(t("item_name") + " added!")
        st.rerun()

# List Items
items = st.session_state.project.capex_items
if items:
    df = pd.DataFrame([i.dict() for i in items])
    # Map category values to localized strings
    df['category'] = df['category'].map(lambda x: cat_map.get(x, x))
    
    # Simplified view
    view_df = df[['name', 'category', 'amount', 'year', 'vat_rate']]
    
    # Rename columns
    view_df = view_df.rename(columns={
        "name": t("item_name"),
        "category": t("category"),
        "amount": t("amount"),
        "year": t("year"),
        "vat_rate": t("vat_rate")
    })
    
    st.dataframe(view_df, use_container_width=True)
    
    if st.button(t("clear_all")):
        st.session_state.project.capex_items = []
        st.rerun()
else:
    st.write(t("no_items"))

st.divider()

# --- Incentives / Grants ---
from core.model import Grant
st.header(t("incentives_title"))

with st.expander(t("inc_add"), expanded=False):
    c1, c2 = st.columns(2)
    i_name = c1.text_input(t("inc_name"), "Incentive 1")
    # Mapping for selection
    inc_types = {t("inc_type_capex"): True, t("inc_type_opex"): False}
    i_type_label = c2.selectbox(t("inc_type"), list(inc_types.keys()))
    is_capex_red = inc_types[i_type_label]
    
    c3, c4 = st.columns(2)
    i_amt = c3.number_input(t("inc_amount"), min_value=0.0, key="input_inc_amount")
    i_yr = c4.number_input(t("inc_year"), min_value=1, max_value=st.session_state.project.horizon_years, value=1, key="input_inc_year")
    
    if st.button(t("inc_add"), key="btn_add_inc"):
        grant = Grant(
            name=i_name,
            amount=i_amt,
            year=int(i_yr),
            is_capex_reduction=is_capex_red
        )
        st.session_state.project.grants.append(grant)
        st.success("Incentive added!")
        st.rerun()

# List Incentives
if st.session_state.project.grants:
    g_df = pd.DataFrame([g.dict() for g in st.session_state.project.grants])
    
    # Map boolean to string
    type_map = {True: t("inc_type_capex"), False: t("inc_type_opex")}
    g_df['is_capex_reduction'] = g_df['is_capex_reduction'].map(type_map)
    
    view_gdf = g_df[["name", "amount", "year", "is_capex_reduction"]]
    view_gdf = view_gdf.rename(columns={
        "name": t("inc_name"),
        "amount": t("inc_amount"),
        "year": t("inc_year"),
        "is_capex_reduction": t("inc_type")
    })
    
    st.dataframe(view_gdf, use_container_width=True)
    if st.button(t("clear_all"), key="btn_clr_inc"):
        st.session_state.project.grants = []
        st.rerun()

save_button()
