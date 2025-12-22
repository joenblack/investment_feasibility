import pytest
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from core.migration import migrate_project_data
from core.model import ProjectModel

def test_migration_v0_to_v1():
    # Simulate old data (missing schema_version)
    old_data = {
        "name": "Old Project",
        "horizon_years": 10,
        "projection_years": 10 # Extra field from old version? Pydantic ignores extra by default with Config defaults
    }
    
    migrated = migrate_project_data(old_data)
    
    assert migrated["schema_version"] == 1
    
    # Validation should succeed
    model = ProjectModel.model_validate(migrated)
    assert model.name == "Old Project"
    assert model.schema_version == 1
