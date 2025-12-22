import streamlit as st
from core.model import ProjectModel
from core.db import save_project
from core.auth import check_permission

from ui.i18n import get_text

from core.db import save_project, load_project

def ensure_state():
    # 1. Try to recover state from URL if not already loaded matching URL
    # Using st.query_params
    query_params = st.query_params
    qp_id = query_params.get("id")
    
    # If we have an ID in URL, and (no project in state OR project in state doesn't match URL)
    if qp_id:
        if 'project' not in st.session_state or st.session_state.project.id != qp_id:
            try:
                loaded = load_project(qp_id)
                if loaded:
                    st.session_state.project = loaded
                    st.session_state.project_active = True
                else:
                    # Invalid ID, maybe clear param?
                    st.warning(f"Project ID {qp_id} not found.")
            except Exception as e:
                print(f"Error loading project from URL: {e}")

    # 2. Default Initialization
    if 'project' not in st.session_state:
        st.session_state.project = ProjectModel()
        st.session_state.project_active = False
        
    if 'language' not in st.session_state:
        st.session_state.language = 'tr' # Default


def bootstrap(require_project=False):
    """
    Centralized initialization:
    1. Initializes DB (if needed)
    2. Initializes Session State
    3. Enforces Login (stops if failed)
    4. Enforces Active Project (stops if failed and requested)
    """
    # 1. Init DB
    from core.db import init_db
    init_db()
    
    # 2. Ensure State
    ensure_state()
    
    # 3. Auth Guard
    from core.auth import login_form
    if not login_form():
        st.stop()
        
    # 4. Project Guard
    if require_project:
        require_active_project()
        
def require_active_project():
    """Guard function to block access if no project is active."""
    if not st.session_state.get("project_active", False):
        st.error("⚠️ No Active Project Selected")
        st.info("Please go to the Dashboard to Load or Create a project.")
        st.page_link("App.py", label="Go to Dashboard", icon="🏠")
        st.stop()


def t(key):
    return get_text(key, st.session_state.language)
        
def save_button():
    # Only show if user has permission
    user = st.session_state.get('user', {'role': 'Viewer', 'username': 'Guest'})
    
    if not check_permission(user['role'], 'edit_project'):
        st.caption("🔒 Read-Only Mode")
        return

    if st.button(t("save_project"), type="primary"):
        if st.session_state.project:
            save_project(st.session_state.project, user=user['username'])
            
            # Auto-activate and update URL
            st.session_state.project_active = True
            st.query_params["id"] = st.session_state.project.id
            
            msg = t('project_saved').format(st.session_state.project.name)
            st.toast(f"{msg} ({st.session_state.project.version})", icon="✅")

def period_selector(key_prefix: str) -> dict:
    c1, c2 = st.columns(2)
    start = c1.number_input("Start Year", min_value=1, max_value=30, value=1, key=f"{key_prefix}_start")
    end = c2.number_input("End Year", min_value=1, max_value=30, value=10, key=f"{key_prefix}_end")
    return {"start": start, "end": end}

def format_currency(amount, currency="TRY"):
    return f"{amount:,.0f} {currency}"

def sidebar_nav():
    st.sidebar.title(t("app_title"))
    
    # Active Project Indicator
    if st.session_state.get("project_active", False):
        st.sidebar.success(f"📂 {st.session_state.project.name}\n\nRunning: {st.session_state.project.version}")
    else:
        st.sidebar.warning("⚠️ No Project Active")

    
    # Language Selector
    lang_map = {"en": "English", "tr": "Türkçe"}
    selected_lang = st.sidebar.selectbox("Language / Dil", options=["en", "tr"], format_func=lambda x: lang_map[x], index=0 if st.session_state.language == "en" else 1)
    if selected_lang != st.session_state.language:
        st.session_state.language = selected_lang
        st.rerun()
        
    st.sidebar.divider()
    
    st.sidebar.page_link("app.py", label=t("home_dashboard"), icon="🏠")
    st.sidebar.divider()
    
    st.sidebar.subheader(t("inputs"))
    st.sidebar.page_link("pages/01_Project_Setup.py", label=t("project_setup_link"))
    st.sidebar.page_link("pages/02_CAPEX.py", label=t("capex_link"))
    st.sidebar.page_link("pages/03_Revenue_OPEX.py", label=t("rev_opex_link"))
    st.sidebar.page_link("pages/04_Finance.py", label=t("finance_link"))
    
    st.sidebar.subheader(t("outputs"), divider=True)
    st.sidebar.page_link("pages/05_Financial_Statements.py", label=t("financial_statements_link"))
    st.sidebar.page_link("pages/06_Charts.py", label=t("charts_link"))
    
    st.sidebar.subheader(t("analysis"), divider=True)
    st.sidebar.page_link("pages/07_Scenarios.py", label=t("scenario_link"))
    st.sidebar.page_link("pages/07_Risk_Analysis.py", label=t("risk_link"))
    st.sidebar.page_link("pages/08_Manual.py", label=t("manual_link"))
