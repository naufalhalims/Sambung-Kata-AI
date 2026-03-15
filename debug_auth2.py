import streamlit_authenticator as sa
import inspect

with open("auth_out.txt", "w", encoding="utf-8") as f:
    f.write(f"HASHER INIT: {inspect.signature(sa.Hasher.__init__)}\n")
    f.write(f"HASHER_HASH: {inspect.signature(sa.Hasher.hash_passwords)}\n")
    f.write(f"AUTH INIT: {inspect.signature(sa.Authenticate.__init__)}\n")
    if hasattr(sa.Authenticate, 'login'):
        f.write(f"LOGIN: {inspect.signature(sa.Authenticate.login)}\n")
    if hasattr(sa.Authenticate, 'logout'):
        f.write(f"LOGOUT: {inspect.signature(sa.Authenticate.logout)}\n")
