import pytest
import sys
import os
import numpy as np

# Ensure path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from core.model import ProjectModel, Loan, Product
from core.engine import calculate_financials

def create_base_project():
    p = ProjectModel()
    p.horizon_years = 5
    p.start_year = 2024
    
    # 1 Product
    prod = Product()
    prod.initial_volume = 1000
    prod.unit_price = 100
    prod.unit_cost = 50
    p.products.append(prod)
    
    # Loan: 100k, 10 years (longer than horizon), 10% interest
    l = Loan(
        name="Long Loan",
        amount=100000,
        currency="TRY",
        interest_rate=0.10,
        term_years=10,
        grace_period_years=0,
        payment_method="EqualPayment",
        start_year=1,
        enable_loan=True
    )
    p.loans = [l]
    
    # Levered mode
    p.calculation_mode = "Levered"
    return p

def test_payoff_mode():
    p = create_base_project()
    p.terminal_debt_treatment = "payoff"
    
    res = calculate_financials(p)
    
    # Check endings
    # Ending Debt Balance should be 0 (conceptually cleared for metrics)
    # The ending_debt_balance IS updated in engine to 0.0 if payoff happens
    assert res.kpi["ending_debt_balance"] == 0.0
    
    # Check Cash Flow Year 5
    cf_df = res.cash_flow_statement
    principal_y5 = cf_df.loc[5, "Principal Repayment"]
    
    # Payoff Amount > 50k
    assert principal_y5 < -50000 

def test_refinance_mode():
    p = create_base_project()
    p.terminal_debt_treatment = "refinance"
    
    res = calculate_financials(p)
    
    # Ending Debt Balance should be > 0
    assert res.kpi["ending_debt_balance"] > 0.0
    
    # Year 5 Principal Repayment should be normal
    cf_df = res.cash_flow_statement
    principal_y5 = cf_df.loc[5, "Principal Repayment"]
    
    # Normal payment ~16k total, principal part maybe ~6-10k.
    assert principal_y5 > -30000 
    assert principal_y5 < 0

def test_horizon_ge_term():
    # Test C: Horizon (10) >= Term (10)
    p = create_base_project()
    p.horizon_years = 10
    
    # Levered Payoff
    p.terminal_debt_treatment = "payoff"
    res_payoff = calculate_financials(p)
    
    # Ending debt should be ~0 naturally
    assert abs(res_payoff.kpi["ending_debt_balance"]) < 1.0
    
    # Levered Refinance
    p.terminal_debt_treatment = "refinance"
    res_refi = calculate_financials(p)
    assert abs(res_refi.kpi["ending_debt_balance"]) < 1.0
    
    # Cash flows should be identical
    np.testing.assert_allclose(res_payoff.free_cash_flow, res_refi.free_cash_flow)

def test_unlevered_mode_ignores_treatment():
    # Test D: Unlevered unaffected
    p = create_base_project()
    p.calculation_mode = "Unlevered"
    p.terminal_debt_treatment = "payoff"
    
    res_payoff = calculate_financials(p)
    
    # In Unlevered mode, FCFF is used.
    # We also guard payoff logic with 'if Levered'. 
    # So 'Principal Repayment' line should NOT include payoff even if 'payoff' is selected in UI (but mode is Unlevered).
    
    cf_df_payoff = res_payoff.cash_flow_statement
    principal_y5 = cf_df_payoff.loc[5, "Principal Repayment"]
    
    # Should be normal payment, not payoff
    # (Because Unlevered mode ignores debt payoff logic per spec)
    assert principal_y5 > -30000 
    
    p.terminal_debt_treatment = "refinance"
    res_refi = calculate_financials(p)
    
    # FCFF should be identical
    np.testing.assert_allclose(res_payoff.free_cash_flow, res_refi.free_cash_flow)
