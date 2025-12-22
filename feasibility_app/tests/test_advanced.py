import pytest
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from core.model import ProjectModel, Product, CAPEXItem, Loan
from core.engine import calculate_financials

def test_multi_currency_capex():
    p = ProjectModel()
    p.currency_base = "TRY"
    p.exchange_rates = {"USD": 30.0, "EUR": 35.0, "TRY": 1.0}
    
    # item in USD
    p.capex_items.append(CAPEXItem(amount=1000, currency="USD", year=1))
    
    res = calculate_financials(p)
    
    # Expect 1000 * 30 = 30,000 TRY outflow
    # Engine output is strictly Annual?
    # capex_a uses sum.
    # Check Cash Flow Statement CAPEX line
    capex_flow = res.cash_flow_statement["CAPEX (w/ VAT)"].values[0] # Year 1 index 0
    
    # Default VAT is 20%.
    # Base = 30,000. VAT = 6,000. Total = 36,000.
    # Outflow is negative.
    assert capex_flow == -36000.0
    
def test_multi_currency_revenue():
    p = ProjectModel()
    p.currency_base = "TRY"
    p.exchange_rates = {"USD": 30.0, "TRY": 1.0}
    
    p.products.append(Product(name="Exp", unit_price=10.0, initial_volume=100, currency="USD"))
    
    res = calculate_financials(p)
    
    # Rev = 10 * 100 * 30 = 30,000 TRY.
    rev = res.revenue_arr[0]
    assert rev == 30000.0

def test_production_constraints():
    p = ProjectModel()
    p.currency_base = "TRY"
    
    # Demand 1000. Cap 500. OEE 100%. Scrap 0%.
    # Should sell 500.
    prod = Product(
        name="Constrained", 
        unit_price=10.0, 
        unit_cost=5.0, 
        initial_volume=1000.0, 
        production_capacity_per_year=500.0,
        oee_percent=1.0,
        scrap_rate=0.0
    )
    p.products.append(prod)
    
    res = calculate_financials(p)
    expected_rev = 500.0 * 10.0
    assert res.revenue_arr[0] == expected_rev
    
    # Scrap Test
    # Demand 100. Cap 1000. Scrap 10%.
    # Needed: 100 / (1-0.1) = 111.11 Gross.
    # Cost = 111.11 * 5 = 555.55
    # Rev = 100 * 10 = 1000
    p2 = ProjectModel()
    prod2 = Product(
        name="Scrap", 
        unit_price=10.0, 
        unit_cost=5.0, 
        initial_volume=100.0,
        production_capacity_per_year=1000.0,
        oee_percent=1.0,
        scrap_rate=0.10
    )
    p2.products.append(prod2)
    res2 = calculate_financials(p2)
    
    rev2 = res2.revenue_arr[0]
    cogs2 = res2.income_statement["COGS"].values[0] # Negative in statement usually? Or positive in arr?
    # In engine: cogs[i] += ...
    # income_statement: "COGS": -cogs_a
    # So I should check 'cogs_a' which is not directly exposed as attribute 'cogs_arr'? 
    # Ah, I didn't expose cogs_arr.
    # I can calculate from Gross Profit in DataFrame.
    # GP = Rev - COGS. => COGS = Rev - GP.
    
    gp = res2.income_statement["Gross Profit"].values[0]
    cal_cogs = rev2 - gp
    
    expected_gross_prod = 100.0 / 0.90
    expected_cogs = expected_gross_prod * 5.0
    
    assert abs(cal_cogs - expected_cogs) < 1.0

def test_payment_terms_impact():
    p = ProjectModel()
    p.currency_base = "TRY"
    
    # 1M Revenue.
    # Case A: Standard 30 Days.
    # Case B: 50% Advance. 30 Days.
    
    prod = Product(
        name="Standard", unit_price=10.0, initial_volume=100000.0, 
        payment_terms_days=30, advance_payment_pct=0.0
    )
    p.products.append(prod)
    res = calculate_financials(p)
    
    # Receivables A approx = 1M * 30/365 = 82,191.
    rev = res.revenue_arr[0] # 1,000,000
    
    # Check Balance Sheet NWC balance implicitly via Delta NWC or check logic?
    # We can check cash flow? Or debug?
    # Actually, we can check NWC Logic if we could access it?
    # 'delta_nwc' is in cash flow statement.
    # Year 1 Delta NWC = Balance_1 - 0.
    
    delta_nwc_a = -res.cash_flow_statement["Delta NWC"].values[0] # Negative sign in stmt means outflow. So -(-val) = val.
    
    p.products[0].advance_payment_pct = 0.50
    res_b = calculate_financials(p)
    delta_nwc_b = -res_b.cash_flow_statement["Delta NWC"].values[0]
    
    # Expect B to be roughly half of A (since receivables are half).
    # Assuming Payables/Inventory 0? Global defaults are DSO 60, DIO 45, DPO 30.
    # Wait, my logic overrides RECEIVABLES. Inventory/Payables still exist.
    # But Receivables component should drop by 50%.
    
    # Let's set others to 0 to isolate Receivables
    p.nwc_config.dio = 0
    p.nwc_config.dpo = 0
    
    # Recalculate A
    p.products[0].advance_payment_pct = 0.0
    res_a_clean = calculate_financials(p)
    delta_nwc_a_clean = -res_a_clean.cash_flow_statement["Delta NWC"].values[0]
    
    # Recalculate B
    p.products[0].advance_payment_pct = 0.5
    res_b_clean = calculate_financials(p)
    delta_nwc_b_clean = -res_b_clean.cash_flow_statement["Delta NWC"].values[0]
    
    assert delta_nwc_b_clean < delta_nwc_a_clean
    assert abs(delta_nwc_b_clean - (delta_nwc_a_clean * 0.5)) < 1.0 # Should be exactly half

