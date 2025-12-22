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
