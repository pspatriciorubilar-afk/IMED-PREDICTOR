import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'functions'))
import firebase_admin
from firebase_admin import credentials, initialize_app, auth

SA_PATH = os.path.join(os.path.dirname(__file__), '..', 'functions', 'serviceAccount.json')
if not firebase_admin._apps:
    firebase_admin.initialize_app(credentials.Certificate(SA_PATH))

email = "ps.patriciorubilar@gmail.com"
user = auth.get_user_by_email(email)
print(f"User disabled? {user.disabled}")
print(f"User email verified? {user.email_verified}")
print(f"User claims: {user.custom_claims}")
