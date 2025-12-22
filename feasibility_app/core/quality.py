from core.model import ProjectModel
from core.engine import FinancialResults
from typing import List, Dict, Tuple
import numpy as np

def calculate_data_health(model: ProjectModel, results: FinancialResults) -> Tuple[int, List[Dict[str, str]]]:
    """
    Analyzes the model and results for logical inconsistencies and risks.
    Returns:
        - Score (0-100)
        - List of warnings [{'severity': 'High/Medium/Low', 'msg': '...'}]
    """
    warnings = []
    score = 100
    
    # 1. Loan > CAPEX (High Severity)
    total_capex = sum(c.amount for c in model.capex_items)
    total_loan = sum(l.amount for l in model.loans)
    if total_loan > total_capex * 1.01: # 1% buffer
        warnings.append({
            "severity": "High",
            "msg": f"Total Loan ({total_loan:,.0f}) exceeds Total CAPEX ({total_capex:,.0f}). verify financing."
        })
        score -= 20

    # 2. Negative EBITDA in Operational Years (Medium)
    # Skip construction years (usually year 1 if no revenue)
    ebitda = results.income_statement["EBITDA"].values
    # Check if we have positive EBITDA eventually
    if np.sum(ebitda > 0) == 0:
        warnings.append({
            "severity": "High",
            "msg": "Project never generates positive EBITDA."
        })
        score -= 25
    elif np.any(ebitda[1:] < 0): # Check from year 2 onwards
        warnings.append({
            "severity": "Medium",
            "msg": "Negative EBITDA detected in operational years."
        })
        score -= 10
        
    # 3. DSCR Covenant (Critical)
    if results.kpi.get("dscr_min", 99.0) < 1.0:
        warnings.append({
            "severity": "Critical",
            "msg": f"Minimum DSCR ({results.kpi.get('dscr_min', 0):.2f}) is below 1.0. Default risk."
        })
        score -= 30
        
    # 4. Extreme Working Capital (Medium)
    if model.nwc_config.dso > 180:
        warnings.append({"severity": "Medium", "msg": "DSO > 180 days seems unrealistic."})
        score -= 5
    if model.nwc_config.dpo > 180:
        warnings.append({"severity": "Medium", "msg": "DPO > 180 days seems unrealistic."})
        score -= 5
        
    # 5. Inflation Consistency
    if model.inflation_rate > 0.50:
         warnings.append({"severity": "Low", "msg": "Inflation rate > 50% is very high."})
         score -= 5
         
    return max(0, score), warnings

def check_product_status(p) -> Tuple[str, str]:
    """
    Returns (Status, Reason) for a product.
    Status: "✅ Included", "⚠️ Inc. (No Rev)", "⛔ Excluded"
    """
    # 1. Exclusion Rules (Technical Constraints)
    if p.production_capacity_per_year <= 0:
        return "⛔ Excluded", "Capacity/Year is 0 or missing."
    if p.oee_percent <= 0:
        return "⛔ Excluded", "OEE % is 0% or missing."
    if p.scrap_rate >= 1.0:
        return "⛔ Excluded", "Scrap Rate >= 100%."
        
    # 2. "Gray Area" / Included but Zero Revenue
    # "Included but revenue = 0"
    if p.initial_volume <= 0:
        return "⚠️ Included (0 Vol)", "Initial Volume is 0. It is set up but produces nothing."
    if p.unit_price <= 0:
        return "⚠️ Included (Free)", "Unit Price is 0. It produces volume but no revenue."
        
    # 3. Minor Warnings (Revenue exists but...)
    if p.unit_cost <= 0:
        return "✅ Included", "Unit Cost is 0 (100% Margin)."
    if p.advance_payment_pct < 0 or p.advance_payment_pct > 1:
        return "✅ Included", "Advance Payment % warning (0-100)."
        
    return "✅ Included", "Fully active."

def check_input_quality(model: ProjectModel) -> List[Dict[str, str]]:
    """
    Checks static inputs for logical missing/invalid values.
    Returns list of dicts: {'context': 'CAPEX', 'item': 'Land', 'issue': '...', 'severity': 'error/warning'}
    """
    issues = []
    
    # 1. Products
    for p in model.products:
        status, reason = check_product_status(p)
        if "⛔" in status:
            issues.append({'context': 'Revenue', 'item': p.name, 'issue': reason, 'severity': 'error'})
        elif "⚠️" in status:
            issues.append({'context': 'Revenue', 'item': p.name, 'issue': reason, 'severity': 'warning'})
            
    # 2. CAPEX
    for c in model.capex_items:
        if c.amount <= 0:
            issues.append({'context': 'CAPEX', 'item': c.name, 'issue': 'Amount is 0.', 'severity': 'warning'})
        if c.year > model.horizon_years:
            issues.append({'context': 'CAPEX', 'item': c.name, 'issue': f'Year {c.year} is outside horizon ({model.horizon_years}).', 'severity': 'error'})
            
    # 3. Personnel
    for p_item in model.personnel:
        if p_item.count <= 0:
             issues.append({'context': 'OPEX', 'item': p_item.role, 'issue': 'Count is 0.', 'severity': 'warning'})
        if p_item.start_year > model.horizon_years:
             issues.append({'context': 'OPEX', 'item': p_item.role, 'issue': 'Start Year outside horizon.', 'severity': 'error'})

    # 4. Loans
    for l in model.loans:
        if l.amount <= 0:
            issues.append({'context': 'Finance', 'item': 'Loan', 'issue': 'Amount is 0.', 'severity': 'warning'})
        if l.start_year > model.horizon_years:
            issues.append({'context': 'Finance', 'item': 'Loan', 'issue': 'Start Year outside horizon.', 'severity': 'error'})
        if l.grace_period_years >= l.term_years:
             issues.append({'context': 'Finance', 'item': 'Loan', 'issue': 'Grace period >= Term.', 'severity': 'error'})
             
    # 5. Global Config
    if model.nwc_config.dso == 0 and model.nwc_config.dpo == 0 and model.nwc_config.dio == 0:
         issues.append({'context': 'Setup', 'item': 'Working Capital', 'issue': 'All NWC days are 0. Logic check needed?', 'severity': 'info'})
         
    return issues
