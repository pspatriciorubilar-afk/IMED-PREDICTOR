import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'functions'))
import firebase_admin
from firebase_admin import credentials, initialize_app, auth

SA_PATH = os.path.join(os.path.dirname(__file__), '..', 'functions', 'serviceAccount.json')
if not firebase_admin._apps:
    firebase_admin.initialize_app(credentials.Certificate(SA_PATH))

email = "ps.patriciorubilar@gmail.com"
password = "patricio2026"

user = auth.get_user_by_email(email)
auth.update_user(user.uid, password=password)
print(f"Password updated to {password}")
