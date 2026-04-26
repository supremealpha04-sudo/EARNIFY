import streamlit as st
import os
import hashlib
from datetime import datetime, timedelta

def check_password() -> bool:
    """
    Check if user is authenticated
    Returns True if authenticated, False otherwise
    """
    # Check if already authenticated in session
    if st.session_state.get('authenticated', False):
        # Check if session is still valid (8 hours)
        if 'login_time' in st.session_state:
            login_time = st.session_state.login_time
            if datetime.now() - login_time < timedelta(hours=8):
                return True
            else:
                # Session expired
                st.session_state.authenticated = False
                st.session_state.login_time = None
    
    # Show login form
    st.title("🔐 Earnify Admin Login")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("---")
        st.markdown("### Welcome Back")
        
        password = st.text_input("Enter admin password:", type="password", key="login_password")
        remember = st.checkbox("Remember me for 8 hours")
        
        if st.button("Login", use_container_width=True):
            admin_password = os.getenv('ADMIN_PASSWORD', 'EarnifyAdmin2024!')
            
            if password == admin_password:
                st.session_state.authenticated = True
                if remember:
                    st.session_state.login_time = datetime.now()
                st.success("✅ Login successful!")
                st.rerun()
            else:
                st.error("❌ Invalid password!")
        
        st.markdown("---")
        st.caption("Contact system administrator if you forgot the password.")
    
    return False

def logout():
    """Logout user"""
    st.session_state.authenticated = False
    st.session_state.login_time = None
    st.success("Logged out successfully!")
    st.rerun()

def hash_password(password: str) -> str:
    """Hash password for storage"""
    salt = os.getenv('PASSWORD_SALT', 'earnify_salt_2024')
    return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return hash_password(password) == hashed
