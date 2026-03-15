import streamlit_authenticator as sa
import inspect

# Inspect Hasher
try:
    print('HASHER INIT:', inspect.signature(sa.Hasher.__init__))
except Exception as e:
    print('HASHER INIT ERR:', e)
print('HASHER METHODS:', dir(sa.Hasher))

# Inspect Authenticate
try:
    print('AUTH INIT:', inspect.signature(sa.Authenticate.__init__))
except Exception as e:
    print('AUTH INIT ERR:', e)
