import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.model import ProjectModel, CAPEXItem, Product, Loan
from core.engine import calculate_financials

def run():
    print("Building Sample Model...")
    model = ProjectModel(name="Smoke Test Project", horizon_years=10)
    
    model.capex_items.append(CAPEXItem(name="Factory", amount=1000000.0, year=1))
    model.products.append(Product(name="Product A", unit_price=200.0, unit_cost=100.0, initial_volume=5000.0, year_growth_rate=0.10))
    model.loans.append(Loan(name="Bank Loan", amount=700000.0, interest_rate=0.15, term_years=5))
    
    print("Running Calculation Engine...")
    results = calculate_financials(model)
    
    print("\n--- KPI ---")
    print(f"NPV: {results.kpi['npv']:,.2f}")
    print(f"IRR: {results.kpi['irr'] * 100:.2f}%")
    print(f"Payback: {results.kpi['payback']:.2f} years")
    
    print("\n--- Income Statement Head ---")
    print(results.income_statement.head())
    
    print("\n--- Cash Flow Head ---")
    print(results.cash_flow_statement.head())
    
    print("\nSmoke Test Passed!")

if __name__ == "__main__":
    run()
