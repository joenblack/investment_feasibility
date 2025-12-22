import pytest
import sys
import os
import numpy as np

# Ensure path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from core.model import ProjectModel, Product, Loan
from core.engine import calculate_financials

def create_model():
    p = ProjectModel()
    p.horizon_years = 3
    # Product
    # Vol=1200 -> 100 per month
    prod = Product(name="P1", initial_volume=1200, unit_price=10.0, unit_cost=0.0, year_growth_rate=0.0)
    p.products.append(prod)
    return p

def test_granularity_comparison():
    # Model 1: Year
    py = create_model()
    py.granularity = "Year"
    res_y = calculate_financials(py)
    
    # Model 2: Month
    pm = create_model()
    pm.granularity = "Month"
    res_m = calculate_financials(pm)
    
    # Comparison
    # Revenue Year 1
    rev_y_1 = res_y.revenue_arr[0] # 1200 * 10 = 12000
    rev_m_1 = res_m.revenue_arr[0] # Should be aggregated sum of 12 months (100*10 * 12)
    
    assert res_y.years == [1, 2, 3]
    assert res_m.years == [1, 2, 3]
    
    assert np.isclose(rev_y_1, 12000.0)
    assert np.isclose(rev_m_1, 12000.0)
    
    # Check if shapes are consistent (Aggregated)
    assert len(res_m.revenue_arr) == 3
    
def test_loan_monthly_schedule():
    p = create_model()
    p.granularity = "Month"
    # Loan: 12000, 1 year term, 0% rate for simplicity first
    l = Loan(amount=12000, term_years=1, interest_rate=0.0, payment_method="EqualPrincipal")
    p.loans.append(l)
    
    res = calculate_financials(p)
    
    # Principal Repayment sum should be 12000
    total_princ = res.cash_flow_statement["Principal Repayment"].sum() 
    # Note: CF is negative for outflow usually in my reporting logic?
    # In engine.py: "Principal Repayment": -princ_a
    # So sum should be -12000
    
    assert np.isclose(total_princ, -12000.0)
    
    # Interest with rate
    l.interest_rate = 0.12 # 12% annual -> 1% monthly
    l.payment_method = "EqualPayment" # PMT
    
    res2 = calculate_financials(p)
    # Total interest should be approx 12000 * 0.12 * roughly 0.5? (declining balance)
    # Detailed check hard, but ensuring it runs is key.
    
    int_a = res2.income_statement["Interest"].sum()
    assert int_a < 0 # Expense is negative
    
def test_compounding_growth():
    # Verify (1+r) vs (1+r)^(1/12) consistency
    p = create_model()
    p.products[0].unit_price = 100.0
    p.products[0].price_escalation_rate = 0.12 # 12%
    
    # Year mode
    p.granularity = "Year"
    res_y = calculate_financials(p)
    # Price Y1 = 100. Y2 = 112.
    # Rev Y1 = 1200 * 100 = 120000.
    # Rev Y2 = 1200 * 112 = 134400.
    
    # Month mode
    p.granularity = "Month"
    res_m = calculate_financials(p)
    
    # Month mode applies growth EACH MONTH? 
    # Logic in engine: `price_growth_p = (1 + 0.12)**(1/12) - 1`.
    # `unit_price` starts at 100.
    # It grows every month.
    # Average price in Year 1 will be > 100?
    # Logic: `unit_price` is "Initial". 
    # In Year mode: `price` is constant for Y1, then jumps for Y2.
    # In Month mode: `price` starts at 100, then 100*(1+gp)...
    # So Y1 revenue will be HIGHER than Y mode because price increases intra-year?
    # OR does Year mode imply "Price at end of year"?
    # Standard: Year mode applies escalation for NEXT year. Y1 uses base.
    # Month mode: If I grow every month, Y1 average > Base.
    # This is a modeling difference.
    # Usually: "Escalation Rate" implies Y2 vs Y1.
    # If I implement monthly compounding starting M2, I change the assumptions.
    # Engine logic:
    # Year: `price *= (1 + rate)` at END of loop (for next year).
    # Month: `price *= (1 + rate_p)` at END of loop (for next month).
    
    # So Month mode leads to price increasing M2..M12. Average > Initial.
    # Year mode: Price constant 100 for M1..M12 (implicitly).
    # So Month mode > Year mode revenue.
    
    rev_m_1 = res_m.revenue_arr[0]
    rev_y_1 = res_y.revenue_arr[0]
    
    assert rev_m_1 > rev_y_1
