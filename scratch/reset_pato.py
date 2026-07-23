import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'functions'))
import firebase_admin
from firebase_admin import credentials, initialize_app, auth

SA_PATH = os.path.join(os.path.dirname(__file__), '..', 'functions', 'serviceAccount.json')
if not firebase_admin._apps:
    firebase_admin.initialize_app(credentials.Certificate(SA_PATH))

email = "ps.patriciorubilar@gmail.com"
password = "AdminImed2026!"

try:
    user = auth.create_user(email=email, password=password)
    print(f"User created: {email} / {password}")
except auth.EmailAlreadyExistsError:
    user = auth.get_user_by_email(email)
    auth.update_user(user.uid, password=password)
    print(f"User already existed. Password updated for {email} to {password}")
except Exception as e:
    print(f"Error: {e}")
