import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from core.model import ProjectModel, CAPEXItem, Product, Loan
from core.engine import calculate_financials

def test_simple_model_run():
    model = ProjectModel(name="Test Project", horizon_years=5)
    
    # Add CAPEX
    model.capex_items.append(CAPEXItem(name="Machine 1", amount=1000.0, year=1))
    
    # Add Revenue
    model.products.append(Product(name="Widget", unit_price=10.0, unit_cost=5.0, initial_volume=100.0))
    
    # Add Loan
    model.loans.append(Loan(amount=500.0, interest_rate=0.10, term_years=3, start_year=1))
    
    results = calculate_financials(model)
    
    assert len(results.years) == 5
    assert results.kpi["npv"] is not None
    assert results.kpi["irr"] is not None
    
    # Check if P&L dataframe is populated
    assert not results.income_statement.empty
    assert "Revenue" in results.income_statement.columns

def test_unlevered_logic():
    model = ProjectModel(calculation_mode="Unlevered")
    model.capex_items.append(CAPEXItem(amount=1000, year=1))
    # Unlevered ignores loan payments in FCF usually, checking strict FCFF definition in engine
    
    results = calculate_financials(model)
    # FCFF should roughly track EBIT*(1-t) + Dep - CapEx
    # ...
    pass
