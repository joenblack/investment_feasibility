from typing import Dict, Any

CURRENT_SCHEMA_VERSION = 1

def migrate_project_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Migrates input dictionary to match the current schema version.
    Input: Dict (from JSON load)
    Output: Dict (ready for ProjectModel.model_validate)
    """
    ver = data.get("schema_version", 0)
    
    if ver < 1:
        # Migration from v0 to v1 (Initial Release with Schema Version)
        # Changes: added schema_version field. 
        # Also maybe some defaults checks?
        data["schema_version"] = 1
        ver = 1
        print("Migrated project data from v0 to v1")
        
    # Future migrations
    # if ver < 2:
    #     data["new_field"] = "default"
    #     data["renamed_field"] = data.pop("old_field", None)
    #     data["schema_version"] = 2
    #     ver = 2
        
    return data
