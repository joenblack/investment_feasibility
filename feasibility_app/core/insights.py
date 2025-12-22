from typing import List, Dict, Any
import pandas as pd
import numpy as np
from core.model import ProjectModel
from core.engine import FinancialResults

def generate_insights(model: ProjectModel, results: FinancialResults) -> List[Dict[str, str]]:
    """
    Analyzes the financial results and model configuration to generate human-readable insights.
    Returns a list of dicts: {"type": "warning"|"info"|"success", "message_key": "str", "params": {}}
    """
    insights = []
    
    # 1. Terminal Value Dominance
    npv = results.kpi.get('npv', 0)
    tv_pv = results.kpi.get('tv_pv', 0)
    
    if npv > 0 and tv_pv > 0:
        ratio = tv_pv / npv
        if ratio > 0.5:
            insights.append({
                "type": "warning",
                "message_key": "insight_tv_dominance",
                "params": {"ratio": ratio * 100}
            })
            
    # 2. OEE / Efficiency Issues
    low_oee_products = [p.name for p in model.products if p.oee_percent < 0.6]
    if low_oee_products:
        insights.append({
            "type": "info",
            "message_key": "insight_low_oee",
            "params": {"products": ", ".join(low_oee_products)}
        })
        
    # 3. Profitability Structure (High OPEX)
    # Check if Cumulative Gross Profit is positive but Cumulative EBITDA is low/negative
    # Or average margin check
    avg_rev = results.revenue_arr.mean() if len(results.revenue_arr) > 0 else 0
    avg_ebitda = results.ebitda_arr.mean() if len(results.ebitda_arr) > 0 else 0
    
    if avg_rev > 0:
        ebitda_margin = avg_ebitda / avg_rev
        
        # Calculate Gross Margin approx
        # We don't have gross profit array directly in results properties easily without calculating
        # But we have income_statement in results
        is_df = results.income_statement
        if not is_df.empty:
            tot_rev = is_df['Revenue'].sum()
            tot_gp = is_df['Gross Profit'].sum()
            tot_ebitda = is_df['EBITDA'].sum()
            
            if tot_rev > 0:
                gp_margin = tot_gp / tot_rev
                
                # Case: Good Gross Margin (>30%) but Low EBITDA Margin (<5%)
                if gp_margin > 0.30 and (tot_ebitda / tot_rev) < 0.05:
                    insights.append({
                        "type": "warning",
                        "message_key": "insight_high_opex",
                        "params": {}
                    })
                    
    # 4. Cash Flow Squeeze (NWC)
    # Check if NWC increase consumes a large chunk of EBITDA
    cf_df = results.cash_flow_statement
    if not cf_df.empty:
        # Delta NWC column index or name?
        # The dataframe columns are standard.
        # "Delta NWC" is usually negative for increase (cash outflow).
        # We need to check if Sum(Abs(Negative Delta NWC)) is large relative to Sum(EBITDA)
        
        # Wait, results.cash_flow_statement has "Delta NWC" column.
        # In engine: "Delta NWC": -nwc_delta_a
        # So negative value = Cash Outflow (Investment in NWC)
        
        delta_nwc = cf_df["Delta NWC"]
        outflows = delta_nwc[delta_nwc < 0].sum() # Negative number
        
        total_ebitda = results.ebitda_arr.sum()
        
        if total_ebitda > 0 and abs(outflows) > (0.20 * total_ebitda):
             insights.append({
                "type": "warning",
                "message_key": "insight_nwc_squeeze",
                "params": {"pct": abs(outflows)/total_ebitda * 100}
            })
            
    return insights
