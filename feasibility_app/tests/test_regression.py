import pytest
import os
import sys
import json
import numpy as np

# Path Fix
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from core.model import ProjectModel
from core.engine import calculate_financials

GOLDEN_INPUT = os.path.join(os.path.dirname(__file__), 'data/golden_v1_input.json')
GOLDEN_OUTPUT = os.path.join(os.path.dirname(__file__), 'data/golden_v1_output.json')

def test_regression_v1():
    # 1. Load Input
    assert os.path.exists(GOLDEN_INPUT), "Golden Input missing. Run generate_golden.py first."
    with open(GOLDEN_INPUT, "r") as f:
        data = json.load(f)
        
    # Pydantic v2 loading
    model = ProjectModel.model_validate(data)
    
    # 2. Run Engine
    res = calculate_financials(model)
    
    # 3. Load Expected
    assert os.path.exists(GOLDEN_OUTPUT), "Golden Output missing."
    with open(GOLDEN_OUTPUT, "r") as f:
        expected = json.load(f)
        
    # 4. Compare KPIs (Scalar)
    for k, v in expected['kpi'].items():
        curr = res.kpi.get(k)
        assert curr is not None, f"Missing KPI {k}"
        # Float comparison
        if isinstance(v, (int, float)):
            assert np.isclose(curr, v, rtol=1e-5), f"KPI {k} mismatch: {curr} != {v}"
            
    # 5. Compare Arrays
    # EBITDA
    assert len(res.ebitda_arr) == len(expected['ebitda'])
    np.testing.assert_allclose(res.ebitda_arr, expected['ebitda'], rtol=1e-5, err_msg="EBITDA Array Mismatch")
    
    # FCF
    np.testing.assert_allclose(res.free_cash_flow, expected['fcf'], rtol=1e-5, err_msg="FCF Array Mismatch")
