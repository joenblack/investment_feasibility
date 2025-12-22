import sqlite3
import json
import os
import datetime
import hashlib
from typing import List, Optional, Dict, Any
from core.model import ProjectModel

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../projects.db'))

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Projects Table
    c.execute('''CREATE TABLE IF NOT EXISTS projects (
        id TEXT PRIMARY KEY,
        name TEXT,
        data_json TEXT,
        version TEXT,
        created_at TEXT,
        updated_at TEXT,
        updated_by TEXT
    )''')
    
    # Schema Migration for 'projects'
    # Check if 'version' column exists
    c.execute("PRAGMA table_info(projects)")
    columns = [info[1] for info in c.fetchall()]
    
    if "version" not in columns:
        print("Migrating DB: Adding 'version' column to projects table.")
        c.execute("ALTER TABLE projects ADD COLUMN version TEXT")
        
    if "updated_by" not in columns:
        print("Migrating DB: Adding 'updated_by' column to projects table.")
        c.execute("ALTER TABLE projects ADD COLUMN updated_by TEXT")
        
    if "created_at" not in columns:
        print("Migrating DB: Adding 'created_at' column to projects table.")
        c.execute("ALTER TABLE projects ADD COLUMN created_at TEXT")
        # Backfill with current time or updated_at if available
        now_ts = datetime.datetime.now().isoformat()
        c.execute("UPDATE projects SET created_at = COALESCE(updated_at, ?)", (now_ts,))

    if "data_json" not in columns:
        if "data" in columns:
            print("Migrating DB: Renaming 'data' to 'data_json' in projects table.")
            try:
                c.execute("ALTER TABLE projects RENAME COLUMN data TO data_json")
            except Exception as e:
                print(f"Migration Error (Rename): {e}")
                # Fallback: Add new column and copy
                c.execute("ALTER TABLE projects ADD COLUMN data_json TEXT")
                c.execute("UPDATE projects SET data_json = data")
        else:
             print("Migrating DB: Adding 'data_json' column to projects table.")
             c.execute("ALTER TABLE projects ADD COLUMN data_json TEXT")
        
    # History Table
    c.execute('''CREATE TABLE IF NOT EXISTS project_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id TEXT,
        version_tag TEXT, -- v1, v2 etc.
        data_json TEXT,
        timestamp TEXT,
        user TEXT
    )''')
    
    # Users Table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password_hash TEXT,
        role TEXT
    )''')
    
    # Audit Log
    c.execute('''CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT,
        action TEXT,
        target_id TEXT,
        timestamp TEXT
    )''')
    
    # Seed Default Admin
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        # admin / admin123
        # Use the new hash_password function defined below (need to move definition or call it)
        # Python isn't hoisted like JS for functions defined later? 
        # Actually init_db is defined before hash_password.
        # We should move hash_password usage inside or define it before.
        # Simple fix: Re-implement hash logic here inline for the seed or move function up.
        # Moving function up is better but replacing file content chunk is hard for reordering.
        # Inline the logic for init_db to be safe.
        
        salt = os.urandom(16)
        pw_hash = hashlib.pbkdf2_hmac('sha256', "admin123".encode(), salt, 100000)
        stored_val = f"{salt.hex()}${pw_hash.hex()}"
        
        c.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", 
                  ("admin", stored_val, "Admin"))
        print("\n[SECURITY WARNING] Seeded default admin user (admin/admin123). Please change this in production!\n")
        
    conn.commit()
    conn.close()

# --- Auth ---
def hash_password(password: str) -> str:
    """Hashes password using PBKDF2 with a random salt."""
    salt = os.urandom(16) # 16 bytes salt
    # 100,000 iterations of SHA256
    pw_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
    # Store as salt$hash
    return f"{salt.hex()}${pw_hash.hex()}"

def verify_password(stored_password: str, provided_password: str) -> bool:
    """Verifies a stored password (salt$hash) against provided password."""
    try:
        salt_hex, hash_hex = stored_password.split('$')
        salt = bytes.fromhex(salt_hex)
        pw_hash = hashlib.pbkdf2_hmac('sha256', provided_password.encode(), salt, 100000)
        return pw_hash.hex() == hash_hex
    except Exception:
        # Fallback for legacy simple SHA256 (if any exists from old version)
        # This allows smooth transition for existing dev DBs without wiping
        try:
             legacy_hash = hashlib.sha256(provided_password.encode()).hexdigest()
             return legacy_hash == stored_password
        except:
            return False

def authenticate_user(username, password) -> Optional[Dict]:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("SELECT username, role, password_hash FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    
    if row:
        stored_hash = row[2]
        if verify_password(stored_hash, password):
            return {"username": row[0], "role": row[1]}
    return None

    # Seed Default Admin (Moved logic here to ensure it uses new hash function)
    # Actually init_db calls this. We need to update init_db.


# --- Project CRUD ---
def save_project(project: ProjectModel, user: str, version_tag: str = None) -> bool:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    now = datetime.datetime.now().isoformat()
    data = project.model_dump_json() # Use v2 syntax
    
    # Check if exists
    c.execute("SELECT version FROM projects WHERE id=?", (project.id,))
    row = c.fetchone()
    
    new_version = "v1"
    if row:
        # Increment version logic or just use timestamp
        # If user passed explicit tag, use it. Else auto-increment vX
        current_ver = row[0]
        if current_ver.startswith("v"):
            try:
                ver_num = int(current_ver[1:]) + 1
                new_version = f"v{ver_num}"
            except:
                new_version = "v_" + now
        else:
            new_version = "v2"
            
    if version_tag:
        new_version = version_tag
        
    project.version = new_version
    data = project.model_dump_json() # Re-dump with new version
        
    if row:
        c.execute('''UPDATE projects SET 
            name=?, data_json=?, version=?, updated_at=?, updated_by=? 
            WHERE id=?''', 
            (project.name, data, new_version, now, user, project.id))
    else:
        c.execute('''INSERT INTO projects (id, name, data_json, version, created_at, updated_at, updated_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (project.id, project.name, data, new_version, now, now, user))
            
    # Save History
    c.execute("INSERT INTO project_history (project_id, version_tag, data_json, timestamp, user) VALUES (?, ?, ?, ?, ?)",
              (project.id, new_version, data, now, user))
              
    # Audit
    c.execute("INSERT INTO audit_log (user, action, target_id, timestamp) VALUES (?, ?, ?, ?)",
              (user, "SAVE_PROJECT", project.id, now))
              
    conn.commit()
    conn.close()
    return True

from core.migration import migrate_project_data

def load_project(project_id: str, version_tag: str = None) -> Optional[ProjectModel]:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    if version_tag:
        c.execute("SELECT data_json FROM project_history WHERE project_id=? AND version_tag=?", (project_id, version_tag))
    else:
        c.execute("SELECT data_json FROM projects WHERE id=?", (project_id,))
        
    row = c.fetchone()
    conn.close()
    
    if row:
        data_dict = json.loads(row[0])
        safe_data = migrate_project_data(data_dict)
        return ProjectModel.model_validate(safe_data)
    return None

def list_projects() -> List[Dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT id, name, version, updated_at, updated_by FROM projects ORDER BY updated_at DESC")
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def list_project_history(project_id: str) -> List[Dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT version_tag, timestamp, user FROM project_history WHERE project_id=? ORDER BY id DESC", (project_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def delete_project(project_id: str, user: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM projects WHERE id=?", (project_id,))
    # Keep history? Or delete? Corporate audit Usually keeps history.
    # But let's delete for cleanliness in this app context, or soft delete.
    # Let's keep history but log deletion.
    
    c.execute("INSERT INTO audit_log (user, action, target_id, timestamp) VALUES (?, ?, ?, ?)",
              (user, "DELETE_PROJECT", project_id, datetime.datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
