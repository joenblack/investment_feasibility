import numpy as np
from typing import Optional, Dict, Any

def calculate_nwc(
    revenue: np.ndarray, 
    cogs: np.ndarray, 
    opex: np.ndarray, 
    dso: float, 
    dio: float, 
    dpo: float, 
    periods_per_year: int = 1,
    receivables_override: Optional[np.ndarray] = None
) -> Dict[str, Any]:
    """
    Calculates Net Working Capital requirements and delta NWC.
    """
    
    annualization_factor = float(periods_per_year)
    
    # 1. Accounts Receivable
    if receivables_override is not None:
        receivables = receivables_override
    else:
        receivables = revenue * annualization_factor * (dso / 365.0)
    inventory = cogs * annualization_factor * (dio / 365.0)
    payables = cogs * annualization_factor * (dpo / 365.0) 
    
    nwc_balance = receivables + inventory - payables
    
    # Change in NWC (Cash Outflow if positive increase)
    # Delta NWC(t) = NWC(t) - NWC(t-1)
    delta_nwc = np.zeros_like(nwc_balance)
    delta_nwc[0] = nwc_balance[0] # Year 1 change is practically the full balance build up
    delta_nwc[1:] = np.diff(nwc_balance)
    
    return {
        "receivables": receivables,
        "inventory": inventory,
        "payables": payables,
        "nwc_balance": nwc_balance,
        "delta_nwc": delta_nwc
    }
