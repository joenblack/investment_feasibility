import sqlite3
import json
from typing import List, Optional, Dict
from core.model import ProjectModel

DB_PATH = "projects.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def save_project(project: ProjectModel):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Check if exists
    c.execute("SELECT id FROM projects WHERE id = ?", (project.id,))
    exists = c.fetchone()
    
    try:
        json_data = project.model_dump_json()
    except AttributeError:
        json_data = project.json()
    
    if exists:
        c.execute("UPDATE projects SET name = ?, data = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", 
                  (project.name, json_data, project.id))
    else:
        c.execute("INSERT INTO projects (id, name, data) VALUES (?, ?, ?)", 
                  (project.id, project.name, json_data))
        
    conn.commit()
    conn.close()

def load_project(project_id: str) -> Optional[ProjectModel]:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT data FROM projects WHERE id = ?", (project_id,))
    row = c.fetchone()
    conn.close()
    
    if row:
        try:
            return ProjectModel.model_validate_json(row[0])
        except AttributeError:
            return ProjectModel.parse_raw(row[0])
    return None

def list_projects() -> List[Dict[str, str]]:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, name, updated_at FROM projects ORDER BY updated_at DESC")
    rows = c.fetchall()
    conn.close()
    
    return [{"id": r[0], "name": r[1], "updated_at": r[2]} for r in rows]

def delete_project(project_id: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    conn.commit()
    conn.close()
