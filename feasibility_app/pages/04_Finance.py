import streamlit as st

from ui.components import ensure_state, sidebar_nav, save_button, t, require_active_project, bootstrap
from core.model import Loan, Grant

bootstrap(require_project=True)
sidebar_nav()

st.title(t("finance_title"))
tab1, tab2, tab3 = st.tabs([t("tab_loans"), t("tab_tax"), t("tab_nwc")])

with tab1:
    st.header(t("debt_financing"))
    with st.expander(t("add_loan"), expanded=False):
        c1, c2, c3 = st.columns(3)
        l_name = c1.text_input(t("name"))
        l_amount = c2.number_input(t("principal_amount"), 0.0)
        l_curr = c3.selectbox(t("currency"), ["TRY", "USD", "EUR"])
        
        c4, c5, c6 = st.columns(3)
        l_rate = c4.number_input(t("interest_rate"), 0.0)
        l_term = c5.number_input(t("term_years"), 1)
        l_start = c6.number_input(t("start_year"), 1)
        
        c7, c8 = st.columns(2)
        l_grace = c7.number_input(t("grace_period"), 0)
        l_type = c8.selectbox(t("payment_type"), ["EqualPrincipal", "EqualPayment", "Bullet"])
        
        if st.button(t("add_loan")):
            loan = Loan(
                name=l_name, amount=l_amount, currency=l_curr,
                interest_rate=l_rate/100.0, term_years=int(l_term), 
                start_year=int(l_start), grace_period_years=int(l_grace),
                payment_method=l_type
            )
            st.session_state.project.loans.append(loan)
            st.rerun()
    
    for i, l in enumerate(st.session_state.project.loans):
        st.write(f"**{l.name}**: {l.amount} {l.currency} @ {l.interest_rate*100}% | {l.term_years} yrs ({l.payment_method})")
        if st.button(t("remove") + f" {l.name}", key=f"del_loan_{i}"):
            st.session_state.project.loans.pop(i)
            st.rerun()
            
    st.divider()
    st.header(t("equity_header"))
    st.info(t("equity_info"))
    st.session_state.project.equity_contribution = st.number_input(t("initial_equity"), value=st.session_state.project.equity_contribution)
    
    st.markdown("---")
    st.header(t("terminal_treatment"))
    
    # Map internal values to display labels
    treatment_map = {
        "payoff": t("payoff_debt"),
        "refinance": t("refinance_debt")
    }
    
    # Reverse map for saving
    display_options = list(treatment_map.values())
    current_val = st.session_state.project.terminal_debt_treatment
    default_idx = 0
    if current_val in treatment_map:
        default_idx = display_options.index(treatment_map[current_val])
        
    selected_option = st.radio(
        t("terminal_treatment"),
        display_options,
        index=default_idx,
        label_visibility="collapsed"
    )
    
    # Find key from value
    for k, v in treatment_map.items():
        if v == selected_option:
            st.session_state.project.terminal_debt_treatment = k
            break

with tab2:
    st.header(t("corporate_tax"))
    st.session_state.project.tax_config.corporate_tax_rate = st.number_input(t("tax_rate"), value=st.session_state.project.tax_config.corporate_tax_rate * 100.0) / 100.0
    
    st.header(t("depreciation_lives"))
    c1, c2 = st.columns(2)
    st.session_state.project.tax_config.machinery_useful_life = c1.number_input(t("machinery_years"), value=st.session_state.project.tax_config.machinery_useful_life)
    st.session_state.project.tax_config.building_useful_life = c2.number_input(t("building_years"), value=st.session_state.project.tax_config.building_useful_life)

with tab3:
    st.header(t("nwc_params"))
    c1, c2, c3 = st.columns(3)
    st.session_state.project.nwc_config.dso = c1.number_input(t("dso"), value=st.session_state.project.nwc_config.dso)
    st.session_state.project.nwc_config.dio = c2.number_input(t("dio"), value=st.session_state.project.nwc_config.dio)
    st.session_state.project.nwc_config.dpo = c3.number_input(t("dpo"), value=st.session_state.project.nwc_config.dpo)
    
    st.checkbox(t("release_nwc"), value=st.session_state.project.nwc_config.terminal_release, key="nwc_term")
    st.session_state.project.nwc_config.terminal_release = st.session_state.nwc_term

st.markdown("---")
save_button()
