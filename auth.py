import streamlit as st
import os

def check_password():
    """Mengembalikan True jika password benar. 
    Akan menghentikan app jika belum login."""
    
    def password_entered():
        # Baca password dari Environment Variable (lokal) atau Streamlit Secrets (Cloud)
        secret_pass = os.environ.get("APP_PASSWORD", "sambung123")
        
        # Jika menggunakan Streamlit Secrets via dashboard (saat di deploy)
        if hasattr(st, "secrets") and "APP_PASSWORD" in st.secrets:
            secret_pass = st.secrets["APP_PASSWORD"]
            
        if st.session_state["password_input"] == secret_pass:
            st.session_state["password_correct"] = True
            del st.session_state["password_input"]  # Hapus dari memori untuk keamanan
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    # Styling sederhana untuk login form
    st.markdown("""
        <style>
        .login-box {
            background-color: #1a1a2e; padding: 2rem; border-radius: 12px;
            border: 1px solid #2d2d5e; box-shadow: 0 4px 12px #0005;
            text-align: center; max-width: 400px; margin: 40px auto;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="login-box"><h2>🔒 Private Access</h2><p>Aplikasi ini dikunci sementara.</p></div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.text_input(
            "Masukkan Password", 
            type="password", 
            on_change=password_entered, 
            key="password_input"
        )
        if "password_correct" in st.session_state and not st.session_state["password_correct"]:
            st.error("❌ Password salah!")
            
    return False
