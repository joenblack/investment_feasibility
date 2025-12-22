import sys
import os
import json
import numpy as np

# Add feasibility_app to path
# Script is in root/scripts/
# We want root/feasibility_app/
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../feasibility_app'))
sys.path.insert(0, root_path)

print(f"DEBUG: Root Path: {root_path}")
print(f"DEBUG: Sys Path: {sys.path}")
print(f"DEBUG: Contents of root: {os.listdir(root_path)}")

from core.model import ProjectModel, Product, CAPEXItem, Loan
from core.engine import calculate_financials

def create_golden_model():
    p = ProjectModel(name="Golden Project")
    p.horizon_years = 5
    p.start_year = 2025
    
    # Add complexities
    p.products.append(Product(name="Widget A", unit_price=100, unit_cost=50, initial_volume=1000, year_growth_rate=0.10))
    p.capex_items.append(CAPEXItem(name="Machine X", amount=50000, year=1))
    p.loans.append(Loan(name="Loan A", amount=40000, interest_rate=0.10, term_years=5))
    
    return p

def generate_golden_data():
    # Ensure tests/data exists
    data_dir = os.path.join(os.path.dirname(__file__), '../feasibility_app/tests/data')
    os.makedirs(data_dir, exist_ok=True)
    
    model = create_golden_model()
    
    # 1. Save Input JSON
    input_path = os.path.join(data_dir, "golden_v1_input.json")
    with open(input_path, "w") as f:
        f.write(model.model_dump_json(indent=2))
        
    print(f"Generated {input_path}")
    
    # 2. Run Engine
    res = calculate_financials(model)
    
    # 3. Capture Results
    # We mainly care about KPIs and Annual Arrays for regression
    results_snapshot = {
        "kpi": res.kpi,
        "years": res.years,
        "revenue": res.revenue_arr.tolist(),
        "ebitda": res.ebitda_arr.tolist(),
        "fcf": res.free_cash_flow.tolist(),
        "dscr": res.dscr_arr.tolist()
    }
    
    output_path = os.path.join(data_dir, "golden_v1_output.json")
    with open(output_path, "w") as f:
        json.dump(results_snapshot, f, indent=2)
        
    print(f"Generated {output_path}")

if __name__ == "__main__":
    generate_golden_data()
