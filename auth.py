import streamlit as st
import os

try:
    import streamlit_authenticator as stauth
    from streamlit_authenticator.utilities.exceptions import LoginError
except ImportError:
    st.error("Modul `streamlit-authenticator` belum diinstal. Jalankan: `pip install streamlit-authenticator`")
    st.stop()

def check_password():
    """Mengembalikan True jika user sudah login via Username & Password."""
    
    # Mengambil kredensial dari secrets.toml (prioritas utama)
    # Jika tidak ada, gunakan nilai default "admin" dan "sambung123"
    try:
        expected_user = st.secrets["APP_USERNAME"]
    except Exception:
        expected_user = os.environ.get("APP_USERNAME", "admin")
        
    try:
        expected_pass = st.secrets["APP_PASSWORD"]
    except Exception:
        expected_pass = os.environ.get("APP_PASSWORD", "sambung123")
        
    @st.cache_data
    def get_credentials(user, pwd):
        # Build the credentials dict with plain password
        credentials = {
            'usernames': {
                user: {
                    'email': f'{user}@example.com',
                    'name': user.capitalize(),
                    'password': pwd
                }
            }
        }
        # Hash it correctly using v0.4.x API
        # hash_passwords modifies the dict or returns the new one
        return stauth.Hasher.hash_passwords(credentials)
        
    credentials = get_credentials(expected_user, expected_pass)
    
    # Inisialisasi authenticator (cookie expiry 30 hari)
    try:
        authenticator = stauth.Authenticate(
            credentials,
            'sambung_kata_v2',          # Changed name forces fresh cookie, avoids stale token
            'sambung_kata_secret_key',
            30,
            auto_hash=False
        )
    except Exception as e:
        st.error(f"Error inisialisasi Authenticator: {e}")
        st.stop()

    st.markdown("""
        <style>
        .login-box {
            background-color: #1a1a2e; padding: 2rem; border-radius: 12px;
            border: 1px solid #2d2d5e; box-shadow: 0 4px 12px #0005;
            text-align: center; max-width: 400px; margin: 40px auto 10px auto;
        }
        </style>
    """, unsafe_allow_html=True)
    
    auth_status = st.session_state.get('authentication_status')
    
    if auth_status:
        st.sidebar.markdown("---")
        st.sidebar.markdown(f"👤 **User:** {st.session_state.get('name', expected_user)}")
        with st.sidebar:
            try:
                authenticator.logout(location='sidebar')
            except Exception:
                try:
                    authenticator.logout('Logout', 'main')
                except Exception:
                    authenticator.logout()
        return True
    else:
        st.markdown('<div class="login-box"><h2>🔒 Login</h2><p>Aplikasi ini dikunci sementara.</p></div>', unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            try:
                authenticator.login()
            except LoginError:
                # Stale / invalid cookie token — reset and let user login fresh
                st.session_state['authentication_status'] = None
                st.rerun()
            except TypeError:
                try:
                    authenticator.login('Login', 'main')
                except LoginError:
                    st.session_state['authentication_status'] = None
                    st.rerun()
                except Exception:
                    pass
                    
        if st.session_state.get('authentication_status') is False:
            with col2:
                st.error('❌ Username atau Password salah')
        elif st.session_state.get('authentication_status') is None:
            with col2:
                st.warning('⚠️ Silakan masukkan Username dan Password Anda')
                
        return False
