import pytest
import numpy as np
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from core.model import ProjectModel
from core.risk import run_monte_carlo, run_tornado_analysis

def test_monte_carlo_correlation():
    p = ProjectModel()
    p.horizon_years = 3 # Minimum allowed
    # Granularity Year
    p.granularity = "Year"
    
    # Set correlation
    p.risk_config.set_correlation("Price", "Volume", 0.9) # High positive for checking
    p.risk_config.monte_carlo_iterations = 500
    
    df = run_monte_carlo(p, iterations=500)
    
    # Check Price_Factor vs Volume_Factor correlation
    corr = df["Price_Factor"].corr(df["Volume_Factor"])
    print(f"Computed Correlation (Target 0.9): {corr}")
    
    # Should be close to 0.9
    assert corr > 0.8
    assert corr < 1.0

def test_tornado_structure():
    p = ProjectModel()
    p.horizon_years = 3
    
    df = run_tornado_analysis(p)
    
    assert "Variable" in df.columns
    assert "Range" in df.columns
    assert len(df) == 4 # Price, Vol, Capex, Opex
    
    # Check sorting
    assert df.iloc[0]["Range"] >= df.iloc[-1]["Range"]
