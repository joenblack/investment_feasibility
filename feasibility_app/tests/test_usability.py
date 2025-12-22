import pytest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from core.model import ProjectModel, Loan, CAPEXItem
from core.quality import calculate_data_health
from core.engine import calculate_financials
from core.reporting import export_to_excel

def test_quality_gate_loan_warning():
    p = ProjectModel()
    # Loan > Capex
    p.loans.append(Loan(amount=2000))
    p.capex_items.append(CAPEXItem(amount=1000))
    
    res = calculate_financials(p)
    score, warnings = calculate_data_health(p, res)
    
    # Should have high severity warning
    assert score < 100
    assert any("Total Loan" in w["msg"] for w in warnings)

def test_quality_gate_perfect():
    p = ProjectModel()
    p.loans.append(Loan(amount=500))
    p.capex_items.append(CAPEXItem(amount=1000))
    
    from core.model import Product
    p.products.append(Product(name="P1", unit_price=100, unit_cost=40, initial_volume=1000)) # 60k Margin
    
    # Ensure EBITDA positive
    # ... assuming default model has some margin? 
    # Default Product price 100, cost 60. Volume 1000. => 40k Margin.
    # Fixed exp = ? Default empty.
    
    res = calculate_financials(p)
    score, warnings = calculate_data_health(p, res)
    
    print(f"DEBUG: Score={score}")
    for w in warnings:
        print(f"DEBUG: Warning: {w['msg']}")
        
    # Might still complain about NWC limits if defaults are high?
    # Default DSO=60. OK.
    # Default Inflation=0. OK.
    
    # DSCR might be issue if repayment is high.
    # Loan 500, 5 years. Annual ~100+Interest. EBITDA 40k. DSCR huge.
    
    assert score >= 90 # Allow minor things

def test_excel_export_run():
    p = ProjectModel()
    res = calculate_financials(p)
    
    # Just check it runs and returns bytes
    xlsx_data = export_to_excel(p, res)
    assert len(xlsx_data) > 0
    assert isinstance(xlsx_data, bytes)
