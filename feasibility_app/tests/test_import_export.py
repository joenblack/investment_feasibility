import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from core.model import ProjectModel, CAPEXItem
from core.reporting import export_to_json, import_from_json

def test_json_round_trip():
    original = ProjectModel(name="Round Trip Project")
    original.capex_items.append(CAPEXItem(name="Test Item", amount=123.45))
    
    json_str = export_to_json(original)
    
    restored = import_from_json(json_str)
    
    assert restored.name == original.name
    assert len(restored.capex_items) == 1
    assert restored.capex_items[0].amount == 123.45
    assert restored.id == original.id
