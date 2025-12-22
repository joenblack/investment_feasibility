import pytest
import sys
import os
import numpy as np

# Ensure path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from core.model import ProjectModel, Product, Loan
from core.engine import calculate_financials

def add_revenue_product(p):
    prod = Product(
        name="Test Prod",
        initial_volume=1000,
        unit_price=100,
        unit_cost=50,
        year_growth_rate=0.0
    )
    p.products.append(prod)
    return p

def test_tv_perpetuity():
    p = ProjectModel()
    p.horizon_years = 5
    p = add_revenue_product(p)
    p.discount_rate_unlevered = 0.10
    p.tv_config.method = "PerpetuityGrowth"
    p.tv_config.growth_rate = 0.02
    
    # Run calculation
    res = calculate_financials(p)
    
    last_fcf = res.free_cash_flow[-1]
    # Simple check: last_fcf should be > 0
    assert last_fcf > 0
    
    expected_tv = last_fcf * 1.02 / (0.10 - 0.02)
    
    assert np.isclose(res.kpi["tv_value"], expected_tv)
    assert res.kpi["tv_pv"] > 0
    
def test_tv_multiple_levered_debt_deduction():
    p = ProjectModel()
    p = add_revenue_product(p)
    p.calculation_mode = "Levered"
    p.tv_config.method = "ExitMultiple"
    p.tv_config.exit_multiple = 5.0
    
    # Add a loan that stays till end
    l = Loan(amount=100000, term_years=10, start_year=1, interest_rate=0.05)
    p.loans.append(l)
    p.terminal_debt_treatment = "refinance" # Keep debt
    
    # We need EBITDA > 0. 1000*(100-50) = 50k/year.
    # Loan interest ~5k.
    
    res = calculate_financials(p)
    
    last_ebitda = res.ebitda_arr[-1]
    ending_debt = res.kpi["ending_debt_balance"]
    
    # TV (Equity) = (EBITDA * M) - Debt
    expected_tv = (last_ebitda * 5.0) - ending_debt
    assert np.isclose(res.kpi["tv_value"], expected_tv)

def test_tv_multiple_unlevered():
    p = ProjectModel()
    p = add_revenue_product(p)
    p.calculation_mode = "Unlevered"
    p.tv_config.method = "ExitMultiple"
    p.tv_config.exit_multiple = 5.0
    
    res = calculate_financials(p)
    
    last_ebitda = res.ebitda_arr[-1]
    expected_tv = last_ebitda * 5.0
    
    assert np.isclose(res.kpi["tv_value"], expected_tv)
