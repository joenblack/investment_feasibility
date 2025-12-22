"""
Authentication utilities.
Actual user storage and auth logic is in core/db.py.
"""
import streamlit as st
from core.db import authenticate_user

# Let's define roles constants
ROLE_ADMIN = "Admin"
ROLE_EDITOR = "Editor"
ROLE_VIEWER = "Viewer"

def check_permission(user_role: str, action: str) -> bool:
    """
    actions: 'create_project', 'edit_project', 'delete_project', 'view_project', 'export_data', 'manage_users'
    """
    if user_role == ROLE_ADMIN:
        return True
        
    if user_role == ROLE_EDITOR:
        if action in ['create_project', 'edit_project', 'view_project', 'export_data']:
            return True
        return False
        
    if user_role == ROLE_VIEWER:
        if action in ['view_project']:
            return True
        return False
        
    return False

def login_form():
    """Renders login form and handles session state."""
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        
    if st.session_state.logged_in:
        return True
        
    st.title("Login Required")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        
        if submitted:
            # Authenticate against DB
            user = authenticate_user(username, password)
            
            if user:
                st.session_state.logged_in = True
                st.session_state.user = user
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid username or password")
                
    return False

def logout():
    st.session_state.logged_in = False
    st.session_state.user = None
    st.rerun()
