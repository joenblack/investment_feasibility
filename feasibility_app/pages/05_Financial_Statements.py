import streamlit as st
import pandas as pd

from ui.components import ensure_state, sidebar_nav, format_currency, t, require_active_project, bootstrap
from core.engine import calculate_financials
from core.quality import calculate_data_health
from core.reporting import export_to_excel

bootstrap(require_project=True)
sidebar_nav()

st.title(t("financial_stmts_title"))

if st.button(t("calc_refresh")):
    st.rerun()

    discount_label = f"{t('discount_rate_wacc')} ({st.session_state.project.discount_rate_unlevered*100:.1f}%)"
else:
    mode_label = t("mode_badge_fcfe")
    discount_label = f"{t('discount_rate_coe')} ({st.session_state.project.discount_rate_levered*100:.1f}%)"

st.caption(f"**Mode:** {mode_label} | **{discount_label}**")

# Calculate Results
results = calculate_financials(st.session_state.project)

# Metric Columns
c1, c2, c3, c4 = st.columns(4)

# Determine NPV Label (Equity vs Firm)
npv_basis_label = t("npv_basis_equity") if st.session_state.project.calculation_mode == "Levered" else t("npv_basis_firm")

c1.metric(f"NPV ({npv_basis_label})", format_currency(results.kpi['npv'], st.session_state.project.currency_base), help=t("npv_help"))
c2.metric("IRR", f"{results.kpi['irr']*100:.2f}%", help=t("irr_help"))
c3.metric("Payback", f"{results.kpi['payback']:.1f} " + t("year"), help=t("payback_help"))
# Placeholder for DSCR - will update engine next
dscr_val = results.kpi.get('dscr_min', 0)
c4.metric(t("dscr_label"), f"{dscr_val:.2f}x" if dscr_val > 0 else "N/A", help=t("dscr_help"))

# Terminal Debt Visibility
st.divider()
st.subheader("Terminal Debt & KPI")
k1, k2, k3 = st.columns(3)
k1.metric(t("ending_debt_kpi"), format_currency(results.kpi.get('ending_debt_balance', 0), st.session_state.project.currency_base), help=t("ending_debt_help"))
k2.metric(t("term_treat_kpi"), t("val_refinance") if results.kpi.get('terminal_debt_treatment') == "refinance" else t("val_payoff"))    

# Show Payoff amount if Payoff selected
if results.kpi.get('terminal_debt_treatment') == "payoff":
    # Calculate payoff amount implicitly? It's ending_debt_balance basically, but logic clears it.
    # Engine does: principal_payment[-1] += terminal_payoff_amount.
    # The 'ending_debt_balance' in KPI is likely 0 if payoff happened.
    # To show what WAS paid off, we might need to deduce it or pass it explicitly.
    # Engine log: "ending_debt = 0.0" after payoff.
    # So results.kpi['ending_debt_balance'] is 0.
    # We should show the amount that was paid.
    # Wait, engine kpi['ending_debt_balance'] is assigned `ending_debt` (line 328), which is 0.0 after payoff.
    # So we see 0.
    # User might want to see HOW MUCH was paid.
    # Engine doesn't export `terminal_payoff_amount`. I need to export it in Engine first?
    # Or just say "Paid".
    # User Request: "terminal_debt_payoff (sadece treatment=Payoff ise, son yıl düşülen tutar; refinance ise 0)"
    # I need to add `terminal_debt_payoff` to KPI in Engine.
    k3.metric(t("term_payoff_kpi"), format_currency(results.kpi.get('terminal_debt_payoff', 0), st.session_state.project.currency_base))
else:
    k3.metric(t("term_payoff_kpi"), "—")

tab1, tab2 = st.tabs([t("tab_income"), t("tab_cashflow")])

# Define Column Translations
col_map = {
    "Revenue": t("th_revenue"),
    "COGS": t("th_cogs"),
    "Gross Profit": t("th_gross_profit"),
    "OPEX": t("th_opex"),
    "EBITDA": t("th_ebitda"),
    "Depreciation": t("th_depreciation"),
    "Grant Income": t("th_grant_income"),
    "EBIT": t("th_ebit"),
    "Interest": t("th_interest"),
    "EBT": t("th_ebt"),
    "Tax": t("th_tax"),
    "Net Income": t("th_net_income"),
    "Cash Flow": t("th_cash_flow"),
    "CAPEX (w/ VAT)": t("th_capex_vat"),
    "Delta NWC": t("th_delta_nwc"),
    "Principal Repayment": t("th_debt_principal"),
    "Debt Drawdown": t("th_debt_proceeds"),
    "Equity Injection": t("th_equity_inject"),
    "Free Cash Flow": t("th_fcf"),
    "Lease Downpayment": t("th_lease_down"),
    "Lease Repayment": t("th_lease_repay"),
    "Grants (Cash)": t("th_grants_cash"),
    "FCFE": t("th_fcfe"),
    "FCFF": t("th_fcff"),
}

with tab1:
    df_is = results.income_statement.rename(columns=col_map)
    st.dataframe(df_is.style.format("{:,.0f}"), use_container_width=True, height=600)

with tab2:
    df_cf = results.cash_flow_statement.rename(columns=col_map)
    st.dataframe(df_cf.style.format("{:,.0f}"), use_container_width=True, height=600)

st.divider()
st.subheader("Export")

# Excel Button
excel_data = export_to_excel(st.session_state.project, results)
st.download_button(
    label=t("download_excel"),
    data=excel_data,
    file_name=f"{st.session_state.project.name}_financials.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
