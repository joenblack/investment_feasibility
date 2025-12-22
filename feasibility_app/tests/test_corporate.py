import pytest
import os
import sys
import sqlite3

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from core.db import init_db, save_project, load_project, list_projects, DB_PATH
from core.model import ProjectModel
from core.auth import check_permission, ROLE_ADMIN, ROLE_VIEWER

def test_db_lifecycle():
    # Setup clean db
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        
    init_db()
    assert os.path.exists(DB_PATH)
    
    # Create Project
    p = ProjectModel(name="Test Corp")
    save_project(p, user="admin")
    
    # Verify List
    projs = list_projects()
    assert len(projs) == 1
    assert projs[0]['name'] == "Test Corp"
    assert projs[0]['version'] == "v1"
    
    # Verify Load
    p_loaded = load_project(p.id)
    assert p_loaded.name == "Test Corp"
    
    # Verify Update / Versioning
    p.name = "Test Corp Updated"
    save_project(p, user="editor")
    
    projs_v2 = list_projects()
    assert projs_v2[0]['version'] == "v2"
    assert projs_v2[0]['updated_by'] == "editor"
    
def test_authentication():
    # Admin
    assert check_permission(ROLE_ADMIN, 'delete_project') is True
    assert check_permission(ROLE_ADMIN, 'view_project') is True
    
    # Viewer
    assert check_permission(ROLE_VIEWER, 'delete_project') is False
    assert check_permission(ROLE_VIEWER, 'edit_project') is False
    assert check_permission(ROLE_VIEWER, 'view_project') is True
