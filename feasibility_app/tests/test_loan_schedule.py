import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import numpy as np
from core.finance import calculate_loan_schedule

def test_equal_principal_loan():
    amount = 1000
    rate = 0.10
    term = 5
    start = 1
    horizon = 10
    
    res = calculate_loan_schedule(amount, rate, term, "EqualPrincipal", start, horizon)
    
    # Principal should be 200 each year for 5 years
    expected_principal = np.array([200, 200, 200, 200, 200])
    np.testing.assert_allclose(res["principal"][0:5], expected_principal)
    
    # Interest Year 1: 1000 * 0.10 = 100
    # Interest Year 2: 800 * 0.10 = 80
    assert res["interest"][0] == 100.0
    assert res["interest"][1] == 80.0

def test_grace_period():
    amount = 1000
    rate = 0.10
    term = 5
    start = 1
    horizon = 10
    grace = 2
    
    res = calculate_loan_schedule(amount, rate, term, "EqualPrincipal", start, horizon, grace_period_years=grace)
    
    # First 2 years: 0 principal
    assert res["principal"][0] == 0
    assert res["principal"][1] == 0
    
    # Year 3: Principal starts. Amount 1000 / 5 = 200 per year? 
    # Logic in code: remaining_term = term - (years_elapsed - grace) => term is TOTAL duration usually?
    # Wait, usually term includes grace or excludes?
    # Prompt says: "grace period" as separate param often implies "Total Term = X, of which Y is grace".
    # Or "Term = X (repayment) + Y (grace)".
    # My code: `min(start_idx + term_years + grace_period, horizon_years)` loop implies term_years is the REPAYMENT phase duration effectively?
    # Let's check code: 
    # `remaining_term = term_years - (years_elapsed - grace_period)`
    # If term_years is 5, and grace is 2.
    # Year 0 (elapsed=0): < grace. Prin=0.
    # Year 2 (elapsed=2): >= grace. rem = 5 - (2-2) = 5. Prin = 1000/5 = 200.
    # Code treats term_years as the amortization period length, ADDED to grace.
    # So Total Life = Grace + Term.
    
    assert res["principal"][2] == 200.0
    assert res["interest"][0] == 100.0 # Creates interest during grace
