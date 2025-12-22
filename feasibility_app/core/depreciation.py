import pandas as pd
import numpy as np
from typing import List, Dict

def calculate_depreciation(capex_amount: float, useful_life_years: int, start_year: int, horizon_years: int, payments_per_year: int = 1) -> np.ndarray:
    """
    Calculates depreciation using Straight Line method.
    Returns an array of length `horizon_years * payments_per_year`.
    """
    total_periods = horizon_years * payments_per_year
    life_periods = useful_life_years * payments_per_year
    depreciation_stream = np.zeros(total_periods)
    
    if life_periods <= 0:
        return depreciation_stream
    
    period_depreciation = capex_amount / life_periods
    
    # Adjust for start year (1-based index in model, 0-based in array)
    # Start at beginning of start_year
    start_idx = (start_year - 1) * payments_per_year
    
    for i in range(start_idx, min(start_idx + life_periods, total_periods)):
        depreciation_stream[i] += period_depreciation
        
    return depreciation_stream

def aggregate_depreciation(capex_items: List, horizon_years: int, machinery_life: int, building_life: int, payments_per_year: int = 1) -> np.ndarray:
    """
    Aggregates depreciation from all CAPEX items.
    """
    total_periods = horizon_years * payments_per_year
    total_depreciation = np.zeros(total_periods)
    
    for item in capex_items:
        life = machinery_life # Default
        if "building" in item.category.lower() or "construction" in item.category.lower():
            life = building_life
        elif "land" in item.category.lower():
            life = 0 # Land does not depreciate
            
        dep = calculate_depreciation(item.amount, life, item.year, horizon_years, payments_per_year)
        total_depreciation += dep
        
    return total_depreciation
